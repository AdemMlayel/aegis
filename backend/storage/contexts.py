from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.graph.artifacts import GENERATED_CONTEXT_ROOT
from backend.graph.state import TestContext
from backend.storage.database import SQLITE_DB_PATH, connect, initialize_database


def _workflow_search_blob(context: TestContext) -> str:
    ticket = context.ticket
    return " ".join(
        [
            context.context_id,
            context.created_by,
            context.workflow_status,
            context.approval.status if context.approval else "",
            context.execution.status if context.execution else "",
            ticket.id if ticket else "",
            ticket.title if ticket else "",
            " ".join(ticket.labels) if ticket else "",
        ]
    ).casefold()


def _context_row_values(context: TestContext) -> dict[str, object]:
    execution = context.execution
    execution_summary = execution.summary if execution else None
    return {
        "context_id": context.context_id,
        "payload_json": context.model_dump_json(),
        "ticket_id": context.ticket.id if context.ticket else None,
        "ticket_title": context.ticket.title if context.ticket else None,
        "workflow_status": context.workflow_status,
        "approval_status": context.approval.status if context.approval else None,
        "created_by": context.created_by,
        "created_at": context.created_at.isoformat(),
        "updated_at": context.updated_at.isoformat(),
        "test_count": len(context.test_cases),
        "automation_revision": context.automation_revision,
        "highest_risk": context.reports.highest_risk if context.reports else None,
        "git_status": context.approval.git_status if context.approval else None,
        "execution_status": execution.status if execution else None,
        "execution_passed": execution_summary.passed if execution_summary else 0,
        "execution_failed": execution_summary.failed if execution_summary else 0,
        "execution_skipped": execution_summary.skipped if execution_summary else 0,
        "executed_at": execution.finished_at.isoformat() if execution else None,
        "search_blob": _workflow_search_blob(context),
    }


def _save_context_row(
    connection: sqlite3.Connection,
    context: TestContext,
) -> None:
    values = _context_row_values(context)
    connection.execute(
        """
        INSERT INTO workflow_contexts (
            context_id,
            payload_json,
            ticket_id,
            ticket_title,
            workflow_status,
            approval_status,
            created_by,
            created_at,
            updated_at,
            test_count,
            automation_revision,
            highest_risk,
            git_status,
            execution_status,
            execution_passed,
            execution_failed,
            execution_skipped,
            executed_at,
            search_blob
        )
        VALUES (
            :context_id,
            :payload_json,
            :ticket_id,
            :ticket_title,
            :workflow_status,
            :approval_status,
            :created_by,
            :created_at,
            :updated_at,
            :test_count,
            :automation_revision,
            :highest_risk,
            :git_status,
            :execution_status,
            :execution_passed,
            :execution_failed,
            :execution_skipped,
            :executed_at,
            :search_blob
        )
        ON CONFLICT(context_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            ticket_id = excluded.ticket_id,
            ticket_title = excluded.ticket_title,
            workflow_status = excluded.workflow_status,
            approval_status = excluded.approval_status,
            created_by = excluded.created_by,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at,
            test_count = excluded.test_count,
            automation_revision = excluded.automation_revision,
            highest_risk = excluded.highest_risk,
            git_status = excluded.git_status,
            execution_status = excluded.execution_status,
            execution_passed = excluded.execution_passed,
            execution_failed = excluded.execution_failed,
            execution_skipped = excluded.execution_skipped,
            executed_at = excluded.executed_at,
            search_blob = excluded.search_blob
        """,
        values,
    )


_legacy_contexts_migrated = False


def _migrate_legacy_context_files() -> None:
    global _legacy_contexts_migrated
    if _legacy_contexts_migrated or not GENERATED_CONTEXT_ROOT.is_dir():
        _legacy_contexts_migrated = True
        return

    with connect() as connection:
        for path in GENERATED_CONTEXT_ROOT.glob("*.json"):
            try:
                context = TestContext.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
            except ValueError:
                continue
            exists = connection.execute(
                "SELECT 1 FROM workflow_contexts WHERE context_id = ?",
                (context.context_id,),
            ).fetchone()
            if exists is None:
                _save_context_row(connection, context)

    _legacy_contexts_migrated = True


def save_context(context: TestContext) -> Path:
    initialize_database()
    with connect() as connection:
        _save_context_row(connection, context)
    return SQLITE_DB_PATH


def load_context(context_id: str) -> TestContext | None:
    _migrate_legacy_context_files()
    with connect() as connection:
        row = connection.execute(
            "SELECT payload_json FROM workflow_contexts WHERE context_id = ?",
            (context_id,),
        ).fetchone()
    if row is None:
        return None
    return TestContext.model_validate_json(row["payload_json"])


def list_contexts() -> list[TestContext]:
    _migrate_legacy_context_files()
    contexts: list[TestContext] = []
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM workflow_contexts
            ORDER BY updated_at DESC
            """
        ).fetchall()

    for row in rows:
        try:
            contexts.append(TestContext.model_validate_json(row["payload_json"]))
        except ValueError:
            continue
    return contexts
