from __future__ import annotations

from typing import Any

from backend.graph.artifacts import GENERATED_AUDIT_ROOT
from backend.graph.state import AuditEvent, AuditEventType


def append_audit_event(
    *,
    actor: str,
    event_type: AuditEventType,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    GENERATED_AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    event = AuditEvent(
        actor=actor,
        event_type=event_type,
        summary=summary,
        metadata=metadata or {},
    )
    audit_file = GENERATED_AUDIT_ROOT / "events.jsonl"
    with audit_file.open("a", encoding="utf-8") as stream:
        stream.write(event.model_dump_json())
        stream.write("\n")
    return event
