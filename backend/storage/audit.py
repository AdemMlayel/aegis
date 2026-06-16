from __future__ import annotations

import json
from typing import Any

from backend.graph.state import AuditEvent, AuditEventType
from backend.storage.database import connect, initialize_database


def append_audit_event(
    *,
    actor: str,
    event_type: AuditEventType,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        event_type=event_type,
        summary=summary,
        metadata=metadata or {},
    )
    context_id = event.metadata.get("context_id")
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (
                id,
                context_id,
                actor,
                event_type,
                summary,
                metadata_json,
                payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                context_id if isinstance(context_id, str) else None,
                event.actor,
                event.event_type,
                event.summary,
                json.dumps(event.metadata, sort_keys=True),
                event.model_dump_json(),
                event.created_at.isoformat(),
            ),
        )
    return event


def list_audit_events(
    *,
    context_id: str | None = None,
    limit: int = 100,
) -> list[AuditEvent]:
    initialize_database()
    if context_id is None:
        query = """
            SELECT payload_json
            FROM audit_events
            ORDER BY created_at DESC
            LIMIT ?
        """
        parameters: tuple[object, ...] = (limit,)
    else:
        query = """
            SELECT payload_json
            FROM audit_events
            WHERE context_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        parameters = (context_id, limit)

    with connect() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [AuditEvent.model_validate_json(row["payload_json"]) for row in rows]
