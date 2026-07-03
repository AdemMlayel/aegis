from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.graph.artifacts import GENERATED_CONTEXT_ROOT
from backend.graph.state import TestContext
from backend.storage.database import SQLITE_DB_PATH, connect, initialize_database


class OptimisticConcurrencyError(RuntimeError):
    """Raised when a context save loses an optimistic-concurrency check (W1).

    A context loaded at ``row_version = N`` is saved back, but the row has since
    advanced past ``N`` -- another writer (e.g. a concurrent resume + approve)
    committed in between. Surfacing this instead of silently overwriting
    prevents last-writer-wins data loss on a shared ``context_id``.
    """

    def __init__(self, context_id: str, expected: int, actual: int | None) -> None:
        self.context_id = context_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Concurrent modification of context '{context_id}': expected "
            f"row_version {expected}, found {actual}. Reload and retry."
        )


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


# Column bookkeeping shared by the insert/upsert and conditional-update paths so
# the two SQL statements never drift. ``row_version`` is handled separately.
_CONTEXT_FIELD_NAMES: tuple[str, ...] = (
    "context_id",
    "payload_json",
    "ticket_id",
    "ticket_title",
    "workflow_status",
    "approval_status",
    "created_by",
    "created_at",
    "updated_at",
    "test_count",
    "automation_revision",
    "highest_risk",
    "git_status",
    "execution_status",
    "execution_passed",
    "execution_failed",
    "execution_skipped",
    "executed_at",
    "search_blob",
)
_CONTEXT_COLUMNS = ",\n                ".join(_CONTEXT_FIELD_NAMES)
_CONTEXT_VALUE_PLACEHOLDERS = ",\n                ".join(
    f":{name}" for name in _CONTEXT_FIELD_NAMES
)
# For ON CONFLICT ... DO UPDATE (context_id is the conflict key, never updated).
_CONTEXT_UPDATE_ASSIGNMENTS = ",\n                ".join(
    f"{name} = excluded.{name}"
    for name in _CONTEXT_FIELD_NAMES
    if name != "context_id"
)
# For a direct UPDATE ... WHERE (named params bound from the values dict).
_CONTEXT_UPDATE_ASSIGNMENTS_SELF = ",\n            ".join(
    f"{name} = :{name}"
    for name in _CONTEXT_FIELD_NAMES
    if name != "context_id"
)


def _save_context_row(
    connection: sqlite3.Connection,
    context: TestContext,
) -> None:
    existing = connection.execute(
        "SELECT row_version FROM workflow_contexts WHERE context_id = ?",
        (context.context_id,),
    ).fetchone()

    if existing is None:
        # First write for this context_id: plain insert at row_version 1.
        context.row_version = 1
        values = _context_row_values(context)
        values["row_version"] = 1
        connection.execute(
            f"""
            INSERT INTO workflow_contexts (
                {_CONTEXT_COLUMNS}, row_version
            )
            VALUES (
                {_CONTEXT_VALUE_PLACEHOLDERS}, :row_version
            )
            """,
            values,
        )
        return

    # The row exists. ``context.row_version`` is the version this in-memory copy
    # believes it holds; do a conditional UPDATE and bump. If the row has since
    # advanced (a concurrent writer committed between our load and this save),
    # the WHERE clause matches nothing and we surface the conflict (W1) rather
    # than silently overwriting the other writer's changes.
    expected_version = context.row_version
    next_version = expected_version + 1
    context.row_version = next_version
    values = _context_row_values(context)  # payload reflects the bumped version
    values["expected_version"] = expected_version
    values["next_version"] = next_version
    cursor = connection.execute(
        f"""
        UPDATE workflow_contexts SET
            {_CONTEXT_UPDATE_ASSIGNMENTS_SELF},
            row_version = :next_version
        WHERE context_id = :context_id AND row_version = :expected_version
        """,
        values,
    )
    if cursor.rowcount == 0:
        context.row_version = expected_version  # roll back the in-memory bump
        raise OptimisticConcurrencyError(
            context.context_id,
            expected_version,
            existing["row_version"],
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
            "SELECT payload_json, row_version FROM workflow_contexts "
            "WHERE context_id = ?",
            (context_id,),
        ).fetchone()
    if row is None:
        return None
    context = _normalize_legacy_workflow_control(
        TestContext.model_validate_json(row["payload_json"])
    )
    # The DB column is the authoritative concurrency token; reconcile the
    # in-memory copy to it in case the persisted payload ever lags (W1).
    context.row_version = row["row_version"]
    return context


def list_contexts() -> list[TestContext]:
    _migrate_legacy_context_files()
    contexts: list[TestContext] = []
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json, row_version
            FROM workflow_contexts
            ORDER BY updated_at DESC
            """
        ).fetchall()

    for row in rows:
        try:
            context = _normalize_legacy_workflow_control(
                TestContext.model_validate_json(row["payload_json"])
            )
        except ValueError:
            continue
        context.row_version = row["row_version"]
        contexts.append(context)
    return contexts


def _normalize_legacy_workflow_control(context: TestContext) -> TestContext:
    control = context.workflow_control
    if (
        context.reports is not None
        and control.state == "initialized"
        and control.next_stage == "ticket"
        and not control.completed_stages
    ):
        stages = [
            "ticket",
            "requirements",
            "coverage",
            "tests",
            "automation",
            "validation",
            "approval",
            "report",
        ]
        control.mode = "autonomous"
        control.state = "completed"
        control.current_stage = None
        control.next_stage = None
        control.completed_stages = stages  # type: ignore[assignment]
        control.stage_revisions = {stage: 1 for stage in stages}
    return context
