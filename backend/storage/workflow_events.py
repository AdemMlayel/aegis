from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import StrictModel, WorkflowStageName, utc_now
from backend.storage.database import connect, initialize_database


WorkflowEventKind = Literal[
    "session",
    "control",
    "stage",
    "review",
    "artifact",
    "message",
    "error",
]


class WorkflowEvent(StrictModel):
    sequence: int = Field(ge=1)
    id: str
    context_id: str
    kind: WorkflowEventKind
    stage: WorkflowStageName | None = None
    status: str | None = None
    actor: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


def append_workflow_event(
    *,
    context_id: str,
    kind: WorkflowEventKind,
    actor: str,
    message: str,
    stage: WorkflowStageName | None = None,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowEvent:
    event_id = str(uuid4())
    created_at = utc_now()
    payload = metadata or {}
    initialize_database()
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO workflow_events (
                id,
                context_id,
                kind,
                stage,
                status,
                actor,
                message,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                context_id,
                kind,
                stage,
                status,
                actor,
                message,
                json.dumps(payload, sort_keys=True),
                created_at.isoformat(),
            ),
        )
        sequence = int(cursor.lastrowid)
    return WorkflowEvent(
        sequence=sequence,
        id=event_id,
        context_id=context_id,
        kind=kind,
        stage=stage,
        status=status,
        actor=actor,
        message=message,
        metadata=payload,
        created_at=created_at,
    )


def list_workflow_events(
    *,
    context_id: str,
    after_sequence: int = 0,
    limit: int = 200,
) -> list[WorkflowEvent]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                sequence,
                id,
                context_id,
                kind,
                stage,
                status,
                actor,
                message,
                metadata_json,
                created_at
            FROM workflow_events
            WHERE context_id = ? AND sequence > ?
            ORDER BY sequence ASC
            LIMIT ?
            """,
            (context_id, after_sequence, limit),
        ).fetchall()
    return [
        WorkflowEvent(
            sequence=row["sequence"],
            id=row["id"],
            context_id=row["context_id"],
            kind=row["kind"],
            stage=row["stage"],
            status=row["status"],
            actor=row["actor"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]
