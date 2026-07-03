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

WORKFLOW_CONTROL_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflow_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    context_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    stage TEXT,
    status TEXT,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workflow_events_context_sequence
    ON workflow_events(context_id, sequence ASC);
CREATE INDEX IF NOT EXISTS idx_workflow_events_kind
    ON workflow_events(kind);

CREATE TABLE IF NOT EXISTS artifact_revisions (
    id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    test_case_id TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    version INTEGER NOT NULL,
    source TEXT NOT NULL,
    actor TEXT NOT NULL,
    comment TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(context_id, test_case_id, version)
);

CREATE INDEX IF NOT EXISTS idx_artifact_revisions_context_case
    ON artifact_revisions(context_id, test_case_id, version ASC);
"""

GOVERNANCE_OBSERVABILITY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS request_observations (
    request_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    error_type TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_request_observations_created_at
    ON request_observations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_observations_actor
    ON request_observations(actor, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_observations_organization
    ON request_observations(organization_id, created_at DESC);

CREATE TABLE IF NOT EXISTS model_invocations (
    id TEXT PRIMARY KEY,
    request_id TEXT,
    context_id TEXT,
    organization_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    agent_id TEXT,
    agent_name TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_name TEXT NOT NULL,
    status TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    estimated_cost_usd REAL NOT NULL,
    fallback_from TEXT,
    error_type TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_invocations_created_at
    ON model_invocations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_invocations_context
    ON model_invocations(context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_invocations_agent
    ON model_invocations(agent_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_invocations_organization
    ON model_invocations(organization_id, created_at DESC);
"""

AGENT_INVOCATION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agent_invocations (
    id TEXT PRIMARY KEY,
    request_id TEXT,
    context_id TEXT,
    organization_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    error_type TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_invocations_created_at
    ON agent_invocations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_invocations_context
    ON agent_invocations(context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_invocations_agent
    ON agent_invocations(agent_name, created_at DESC);
"""

TOKEN_GOVERNANCE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS token_reservations (
    id TEXT PRIMARY KEY,
    request_id TEXT,
    context_id TEXT,
    organization_id TEXT NOT NULL,
    agent_id TEXT,
    agent_name TEXT,
    provider TEXT NOT NULL,
    estimated_input_tokens INTEGER NOT NULL,
    reserved_tokens INTEGER NOT NULL,
    actual_tokens INTEGER,
    status TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_token_reservations_active_organization
    ON token_reservations(organization_id, status, expires_at);
CREATE INDEX IF NOT EXISTS idx_token_reservations_active_workflow
    ON token_reservations(context_id, agent_name, status, expires_at);
CREATE INDEX IF NOT EXISTS idx_token_reservations_created_at
    ON token_reservations(created_at DESC);
"""

REQUEST_OBSERVATION_ID_SCHEMA_SQL = """
CREATE TABLE request_observations_v2 (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    error_type TEXT,
    created_at TEXT NOT NULL
);

INSERT INTO request_observations_v2 (
    id, request_id, actor, organization_id, method, path, status_code,
    duration_ms, error_type, created_at
)
SELECT
    request_id, request_id, actor, organization_id, method, path, status_code,
    duration_ms, error_type, created_at
FROM request_observations;

DROP TABLE request_observations;
ALTER TABLE request_observations_v2 RENAME TO request_observations;

CREATE INDEX IF NOT EXISTS idx_request_observations_request_id
    ON request_observations(request_id);
CREATE INDEX IF NOT EXISTS idx_request_observations_created_at
    ON request_observations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_observations_actor
    ON request_observations(actor, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_observations_organization
    ON request_observations(organization_id, created_at DESC);
"""


WORKFLOW_CONTEXT_ROW_VERSION_SCHEMA_SQL = """
ALTER TABLE workflow_contexts
    ADD COLUMN row_version INTEGER NOT NULL DEFAULT 1;
"""


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="initial_local_schema",
        sql=INITIAL_LOCAL_SCHEMA_SQL,
    ),
    Migration(
        version=2,
        name="workflow_control_and_artifact_revisions",
        sql=WORKFLOW_CONTROL_SCHEMA_SQL,
    ),
    Migration(
        version=3,
        name="governance_observability",
        sql=GOVERNANCE_OBSERVABILITY_SCHEMA_SQL,
    ),
    Migration(
        version=4,
        name="agent_invocation_observability",
        sql=AGENT_INVOCATION_SCHEMA_SQL,
    ),
    Migration(
        version=5,
        name="token_budget_reservations",
        sql=TOKEN_GOVERNANCE_SCHEMA_SQL,
    ),
    Migration(
        version=6,
        name="request_observation_identity",
        sql=REQUEST_OBSERVATION_ID_SCHEMA_SQL,
    ),
    Migration(
        version=7,
        name="workflow_context_row_version",
        sql=WORKFLOW_CONTEXT_ROW_VERSION_SCHEMA_SQL,
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
