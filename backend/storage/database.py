from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.graph.artifacts import GENERATED_STORAGE_ROOT


SQLITE_DB_PATH = GENERATED_STORAGE_ROOT / "aegisqa.sqlite3"


def initialize_database(db_path: Path = SQLITE_DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
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
            """
        )
    return db_path


def connect(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
