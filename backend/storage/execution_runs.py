from __future__ import annotations

import json
from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import ExecutionBlock, StrictModel, utc_now
from backend.storage.database import connect, initialize_database


ExecutionRunStatus = Literal[
    "queued",
    "running",
    "passed",
    "failed",
    "skipped",
    "blocked",
]


class ExecutionRunRequest(StrictModel):
    suite: str = Field(min_length=1)
    adapter: str = Field(default="mock", min_length=1)
    branch: str | None = None
    env: str = Field(default="staging", min_length=1)
    tags: list[str] = Field(default_factory=list)
    actor: str = Field(default="ci", min_length=1)


class ExecutionRunRecord(StrictModel):
    run_id: str = Field(default_factory=lambda: f"exec-{uuid4()}")
    context_id: str
    request: ExecutionRunRequest
    status: ExecutionRunStatus = "queued"
    execution: ExecutionBlock | None = None
    junit_xml: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


def save_execution_run(record: ExecutionRunRecord) -> ExecutionRunRecord:
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO execution_runs (
                run_id,
                context_id,
                request_json,
                status,
                suite,
                branch,
                env,
                tags_json,
                actor,
                result_json,
                junit_xml,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                context_id = excluded.context_id,
                request_json = excluded.request_json,
                status = excluded.status,
                suite = excluded.suite,
                branch = excluded.branch,
                env = excluded.env,
                tags_json = excluded.tags_json,
                actor = excluded.actor,
                result_json = excluded.result_json,
                junit_xml = excluded.junit_xml,
                updated_at = excluded.updated_at
            """,
            (
                record.run_id,
                record.context_id,
                record.request.model_dump_json(),
                record.status,
                record.request.suite,
                record.request.branch,
                record.request.env,
                json.dumps(record.request.tags, sort_keys=True),
                record.request.actor,
                record.execution.model_dump_json() if record.execution else None,
                record.junit_xml,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )
    return record


def create_execution_run(
    *,
    context_id: str,
    request: ExecutionRunRequest,
    status: ExecutionRunStatus = "queued",
) -> ExecutionRunRecord:
    record = ExecutionRunRecord(
        context_id=context_id,
        request=request,
        status=status,
    )
    return save_execution_run(record)


def load_execution_run(run_id: str) -> ExecutionRunRecord | None:
    initialize_database()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    if row is None:
        return None
    return _row_to_record(row)


def list_execution_runs(
    *,
    context_id: str | None = None,
    status: ExecutionRunStatus | None = None,
    limit: int = 50,
) -> list[ExecutionRunRecord]:
    initialize_database()
    clauses: list[str] = []
    parameters: list[object] = []
    if context_id:
        clauses.append("context_id = ?")
        parameters.append(context_id)
    if status:
        clauses.append("status = ?")
        parameters.append(status)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    parameters.append(limit)
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM execution_runs
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def _row_to_record(row) -> ExecutionRunRecord:
    return ExecutionRunRecord(
        run_id=row["run_id"],
        context_id=row["context_id"],
        request=ExecutionRunRequest.model_validate_json(row["request_json"]),
        status=row["status"],
        execution=(
            ExecutionBlock.model_validate_json(row["result_json"])
            if row["result_json"]
            else None
        ),
        junit_xml=row["junit_xml"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
