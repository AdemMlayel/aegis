from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import StrictModel, utc_now
from backend.storage.database import connect, initialize_database


ExecutionEventLevel = Literal["debug", "info", "warning", "error"]
ExecutionEventPhase = Literal[
    "queued",
    "running",
    "case_started",
    "case_finished",
    "artifact",
    "completed",
    "blocked",
]


class ExecutionEvent(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    level: ExecutionEventLevel = "info"
    phase: ExecutionEventPhase
    status: str | None = None
    test_case_id: str | None = None
    message: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


def append_execution_event(
    *,
    run_id: str,
    context_id: str,
    phase: ExecutionEventPhase,
    message: str,
    level: ExecutionEventLevel = "info",
    status: str | None = None,
    test_case_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExecutionEvent:
    event = ExecutionEvent(
        run_id=run_id,
        context_id=context_id,
        level=level,
        phase=phase,
        status=status,
        test_case_id=test_case_id,
        message=message,
        metadata=metadata or {},
    )
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO execution_events (
                id,
                run_id,
                context_id,
                level,
                phase,
                status,
                test_case_id,
                message,
                metadata_json,
                payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.run_id,
                event.context_id,
                event.level,
                event.phase,
                event.status,
                event.test_case_id,
                event.message,
                json.dumps(event.metadata, sort_keys=True),
                event.model_dump_json(),
                event.created_at.isoformat(),
            ),
        )
    return event


def list_execution_events(*, run_id: str, limit: int = 200) -> list[ExecutionEvent]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM execution_events
            WHERE run_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (run_id, limit),
        ).fetchall()
    return [ExecutionEvent.model_validate_json(row["payload_json"]) for row in rows]
