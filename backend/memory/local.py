from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal, cast

from backend.config.settings import settings
from backend.graph.artifacts import memory_output_dir
from backend.memory.base import EpisodicMemoryEntry, EpisodicMemoryStore

_memory_stores: dict[tuple[str, str | None], EpisodicMemoryStore] = {}


def _load_archived_entries() -> list[EpisodicMemoryEntry]:
    root = memory_output_dir()
    if not root.is_dir():
        return []

    entries: list[EpisodicMemoryEntry] = []
    seen_ids: set[str] = set()
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            memory_id = str(payload["memory_id"]).strip()
            if not memory_id or memory_id in seen_ids:
                continue
            outcome_value = str(
                payload.get("outcome") or payload.get("execution_status") or "unknown"
            )
            if outcome_value not in {"passed", "failed", "skipped", "unknown"}:
                outcome_value = "unknown"
            ticket_id = str(payload.get("ticket_id") or payload.get("context_id") or memory_id)
            summary = str(payload.get("summary") or "").strip()
            if not summary:
                summary = (
                    f"Workflow {ticket_id} archived with "
                    f"{int(payload.get('test_case_count') or 0)} generated tests and "
                    f"execution status {payload.get('execution_status') or 'n/a'}."
                )
            entries.append(
                EpisodicMemoryEntry(
                    memory_id=memory_id,
                    title=str(payload.get("title") or f"Workflow memory for {ticket_id}"),
                    summary=summary,
                    tags=tuple(str(tag) for tag in payload.get("tags", []) if str(tag)),
                    source_refs=tuple(
                        str(ref) for ref in payload.get("source_refs", []) if str(ref)
                    )
                    or (path.as_posix(),),
                    outcome=cast(
                        Literal["passed", "failed", "skipped", "unknown"],
                        outcome_value,
                    ),
                    created_at=str(
                        payload.get("archived_at")
                        or datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
                    ),
                )
            )
            seen_ids.add(memory_id)
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            continue
    return entries


def get_local_memory_store(
    *,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> EpisodicMemoryStore:
    selected_provider = embedding_provider or settings.default_embedding_provider
    key = (selected_provider, embedding_model)
    if key not in _memory_stores:
        _memory_stores[key] = EpisodicMemoryStore(
            entries=_load_archived_entries(),
            embedding_provider=selected_provider,
            embedding_model=embedding_model,
        )
    return _memory_stores[key]


def reset_local_memory_stores() -> None:
    _memory_stores.clear()
