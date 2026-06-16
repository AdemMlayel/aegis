from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


INITIAL_LOCAL_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflow_contexts (
    context_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    ticket_id TEXT,
    ticket_title TEXT,
    workflow_status TEXT NOT NULL,
    approval_status TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    test_count INTEGER NOT NULL DEFAULT 0,
    automation_revision INTEGER NOT NULL DEFAULT 0,
    highest_risk TEXT,
    git_status TEXT,
    execution_status TEXT,
    execution_passed INTEGER NOT NULL DEFAULT 0,
    execution_failed INTEGER NOT NULL DEFAULT 0,
    execution_skipped INTEGER NOT NULL DEFAULT 0,
    executed_at TEXT,
    search_blob TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_workflow_contexts_updated_at
    ON workflow_contexts(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_contexts_ticket_id
    ON workflow_contexts(ticket_id);
CREATE INDEX IF NOT EXISTS idx_workflow_contexts_workflow_status
    ON workflow_contexts(workflow_status);
CREATE INDEX IF NOT EXISTS idx_workflow_contexts_approval_status
    ON workflow_contexts(approval_status);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    context_id TEXT,
    actor TEXT NOT NULL,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
    ON audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_context_id
    ON audit_events(context_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type
    ON audit_events(event_type);

CREATE TABLE IF NOT EXISTS mock_tickets (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    assignee TEXT,
    labels_json TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    search_blob TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_mock_tickets_priority
    ON mock_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_mock_tickets_status
    ON mock_tickets(status);
CREATE INDEX IF NOT EXISTS idx_mock_tickets_assignee
    ON mock_tickets(assignee);

CREATE TABLE IF NOT EXISTS execution_runs (
    run_id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    request_json TEXT NOT NULL,
    status TEXT NOT NULL,
    suite TEXT NOT NULL,
    branch TEXT,
    env TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    actor TEXT NOT NULL,
    result_json TEXT,
    junit_xml TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_runs_context_id
    ON execution_runs(context_id);
CREATE INDEX IF NOT EXISTS idx_execution_runs_status
    ON execution_runs(status);
CREATE INDEX IF NOT EXISTS idx_execution_runs_updated_at
    ON execution_runs(updated_at DESC);

CREATE TABLE IF NOT EXISTS execution_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    level TEXT NOT NULL,
    phase TEXT NOT NULL,
    status TEXT,
    test_case_id TEXT,
    message TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_events_run_id_created_at
    ON execution_events(run_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_execution_events_context_id
    ON execution_events(context_id);
CREATE INDEX IF NOT EXISTS idx_execution_events_phase
    ON execution_events(phase);
"""


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="initial_local_schema",
        sql=INITIAL_LOCAL_SCHEMA_SQL,
    ),
)


def run_migrations(connection: sqlite3.Connection) -> None:
    """Apply all known local SQLite migrations idempotently."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    applied = {
        row[0]
        for row in connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    }
    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        connection.executescript(migration.sql)
        connection.execute(
            """
            INSERT INTO schema_migrations (version, name, applied_at)
            VALUES (?, ?, ?)
            """,
            (
                migration.version,
                migration.name,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def list_applied_migrations(
    connection: sqlite3.Connection,
) -> list[tuple[int, str, str]]:
    run_migrations(connection)
    rows = connection.execute(
        """
        SELECT version, name, applied_at
        FROM schema_migrations
        ORDER BY version
        """
    ).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]
