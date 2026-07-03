from __future__ import annotations

import sqlite3
from uuid import uuid4

from backend.graph.state import (
    ApprovalBlock,
    AuditEventType,
    ExecutionBlock,
    ExecutionCaseResult,
    ExecutionSummary,
    ReportBlock,
    TestContext as WorkflowContext,
    TicketData,
    utc_now,
)
from backend.storage.audit import append_audit_event, list_audit_events
from backend.storage.contexts import (
    OptimisticConcurrencyError,
    list_contexts,
    load_context,
    save_context,
)
from backend.storage.database import SQLITE_DB_PATH, initialize_database
from backend.storage.migrations import list_applied_migrations
from backend.storage.execution_events import (
    append_execution_event,
    list_execution_events,
)


def _workflow_context(ticket_id: str) -> WorkflowContext:
    return WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id=ticket_id,
            title=f"SQLite Persistence {ticket_id}",
            labels=["sqlite", "queue"],
        ),
        approval=ApprovalBlock(status="pending_review", git_status="not_started"),
        reports=ReportBlock(
            summary="SQLite persistence summary.",
            total_test_cases=0,
            highest_risk="medium",
        ),
    )


def test_save_and_load_context_uses_sqlite() -> None:
    ticket_id = f"SQL-{uuid4().hex[:8]}"
    context = _workflow_context(ticket_id)
    context.mark("report_generated")

    path = save_context(context)
    loaded = load_context(context.context_id)

    assert path == SQLITE_DB_PATH
    assert SQLITE_DB_PATH.is_file()
    assert loaded is not None
    assert loaded.context_id == context.context_id
    assert loaded.ticket is not None
    assert loaded.ticket.id == ticket_id
    assert loaded.workflow_status == "report_generated"


def test_workflow_queue_history_is_backed_by_sqlite_summary_columns() -> None:
    first = _workflow_context(f"QUEUE-SQL-1-{uuid4().hex[:6]}")
    first.mark("queued_first")
    save_context(first)

    second = _workflow_context(f"QUEUE-SQL-2-{uuid4().hex[:6]}")
    second.automation_revision = 3
    second.execution = ExecutionBlock(
        status="failed",
        run_by="pytest",
        started_at=utc_now(),
        finished_at=utc_now(),
        summary=ExecutionSummary(total=2, passed=1, failed=1),
        results=[
            ExecutionCaseResult(
                test_case_id="TC001",
                title="Passing case",
                status="passed",
                message="Passed",
            ),
            ExecutionCaseResult(
                test_case_id="TC002",
                title="Failing case",
                status="failed",
                message="Failed",
            ),
        ],
    )
    second.mark("queued_second")
    save_context(second)

    context_ids = [context.context_id for context in list_contexts()]
    assert context_ids.index(second.context_id) < context_ids.index(first.context_id)

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT
                ticket_id,
                workflow_status,
                approval_status,
                automation_revision,
                highest_risk,
                execution_status,
                execution_passed,
                execution_failed,
                execution_skipped
            FROM workflow_contexts
            WHERE context_id = ?
            """,
            (second.context_id,),
        ).fetchone()

    assert row == (
        second.ticket.id,
        "queued_second",
        "pending_review",
        3,
        "medium",
        "failed",
        1,
        1,
        0,
    )


def test_audit_events_are_persisted_to_sqlite() -> None:
    initialize_database()
    context_id = f"AUDIT-SQL-{uuid4().hex[:8]}"
    event_type: AuditEventType = "workflow_started"

    event = append_audit_event(
        actor="pytest",
        event_type=event_type,
        summary="SQLite audit event.",
        metadata={"context_id": context_id, "kind": "unit-test"},
    )

    events = list_audit_events(context_id=context_id, limit=5)

    assert events[0].id == event.id
    assert events[0].metadata == {"context_id": context_id, "kind": "unit-test"}

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT context_id, actor, event_type, summary
            FROM audit_events
            WHERE id = ?
            """,
            (event.id,),
        ).fetchone()

    assert row == (context_id, "pytest", event_type, "SQLite audit event.")


def test_execution_events_are_persisted_to_sqlite() -> None:
    initialize_database()
    run_id = f"exec-{uuid4()}"
    context_id = f"CTX-{uuid4().hex[:8]}"

    event = append_execution_event(
        run_id=run_id,
        context_id=context_id,
        phase="case_finished",
        status="failed",
        test_case_id="TC002",
        message="Negative case failed.",
        level="error",
        metadata={"duration_ms": 1234},
    )

    events = list_execution_events(run_id=run_id)

    assert events == [event]
    assert events[0].metadata == {"duration_ms": 1234}

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT run_id, context_id, level, phase, status, test_case_id, message
            FROM execution_events
            WHERE id = ?
            """,
            (event.id,),
        ).fetchone()

    assert row == (
        run_id,
        context_id,
        "error",
        "case_finished",
        "failed",
        "TC002",
        "Negative case failed.",
    )


def test_workflow_control_migration_is_recorded() -> None:
    initialize_database()
    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        migrations = list_applied_migrations(connection)

    applied = {(version, name) for version, name, _ in migrations}
    assert {
        (1, "initial_local_schema"),
        (2, "workflow_control_and_artifact_revisions"),
        (3, "governance_observability"),
        (4, "agent_invocation_observability"),
        (5, "token_budget_reservations"),
        (6, "request_observation_identity"),
        (7, "workflow_context_row_version"),
    } <= applied


def test_first_save_starts_at_row_version_one() -> None:
    context = _workflow_context(f"VER-{uuid4().hex[:8]}")
    save_context(context)
    assert context.row_version == 1
    reloaded = load_context(context.context_id)
    assert reloaded is not None
    assert reloaded.row_version == 1


def test_serial_load_mutate_save_advances_version_without_conflict() -> None:
    """The common single-writer path must never raise a false conflict; each
    load -> mutate -> save advances the row_version by one (W1)."""
    context = _workflow_context(f"VER-SERIAL-{uuid4().hex[:8]}")
    save_context(context)  # row_version 1

    for expected in (2, 3, 4):
        reloaded = load_context(context.context_id)
        assert reloaded is not None
        reloaded.mark(f"step_{expected}")
        save_context(reloaded)
        assert reloaded.row_version == expected


def test_concurrent_stale_write_is_rejected_without_data_loss() -> None:
    """W1: two writers load the same context; the first commits and the second
    (still holding the stale version) must be rejected rather than silently
    overwriting the first writer's change (last-writer-wins)."""
    context = _workflow_context(f"VER-RACE-{uuid4().hex[:8]}")
    save_context(context)  # row_version 1

    writer_a = load_context(context.context_id)
    writer_b = load_context(context.context_id)
    assert writer_a is not None and writer_b is not None
    assert writer_a.row_version == writer_b.row_version == 1

    writer_a.mark("a_committed")
    save_context(writer_a)
    assert writer_a.row_version == 2

    writer_b.mark("b_should_be_rejected")
    try:
        save_context(writer_b)
    except OptimisticConcurrencyError as exc:
        assert exc.context_id == context.context_id
        assert exc.expected == 1
        assert exc.actual == 2
    else:  # pragma: no cover - the save must raise
        raise AssertionError("stale concurrent write was not rejected")

    # Writer A's change survived; writer B did not clobber it.
    final = load_context(context.context_id)
    assert final is not None
    assert final.workflow_status == "a_committed"
    assert final.row_version == 2
