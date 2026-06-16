from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4


@dataclass(frozen=True)
class EpisodicMemoryEntry:
    memory_id: str
    title: str
    summary: str
    tags: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    outcome: Literal["passed", "failed", "skipped", "unknown"] = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class EpisodicMemorySearchResult:
    entry: EpisodicMemoryEntry
    score: float
    matched_terms: tuple[str, ...] = ()

    @property
    def ref(self) -> str:
        return self.entry.memory_id


class EpisodicMemoryStore:
    def __init__(self, entries: list[EpisodicMemoryEntry] | None = None) -> None:
        self._entries = entries or []

    def search(self, *, query: str, tags: list[str] | None = None, limit: int = 3) -> list[EpisodicMemorySearchResult]:
        query_terms = _tokenize(query)
        tag_terms = {tag.lower() for tag in (tags or [])}
        results: list[EpisodicMemorySearchResult] = []
        for entry in self._entries:
            entry_terms = _tokenize(" ".join([entry.title, entry.summary, " ".join(entry.tags)]))
            matched_terms = tuple(sorted(query_terms & entry_terms))
            tag_matches = tag_terms & {tag.lower() for tag in entry.tags}
            if not matched_terms and not tag_matches:
                continue
            score = len(matched_terms) + (1.25 * len(tag_matches))
            score = score / max(len(query_terms) or 1, 1)
            results.append(
                EpisodicMemorySearchResult(
                    entry=entry,
                    score=round(min(score, 1.0), 3),
                    matched_terms=matched_terms,
                )
            )
        return sorted(results, key=lambda result: (-result.score, result.entry.memory_id))[:limit]

    def archive(
        self,
        *,
        title: str,
        summary: str,
        tags: list[str],
        source_refs: list[str],
        outcome: Literal["passed", "failed", "skipped", "unknown"] = "unknown",
    ) -> EpisodicMemoryEntry:
        entry = EpisodicMemoryEntry(
            memory_id=f"mem-{uuid4().hex[:12]}",
            title=title,
            summary=summary,
            tags=tuple(tags),
            source_refs=tuple(source_refs),
            outcome=outcome,
        )
        self._entries.append(entry)
        return entry

    def list_entries(self) -> list[EpisodicMemoryEntry]:
        return list(self._entries)


def _tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(term) > 2}
