"""Phase 3 orchestration-integrity regressions for the workflow-control service.

Covers W5 (validation retry-count reset on invalidation) and S2 (honest manual
stage completion -- a validation stage that exhausts its retries without passing
must be reported failed, not completed).
"""
from __future__ import annotations

from backend.graph.state import (
    AutomationBlock,
    AutomationValidation,
    TestContext,
    TicketData,
)
from backend.services.workflow_control import (
    _invalidate_after_artifact_edit,
    _invalidate_from_stage,
    _stage_completion_failure,
)


def _context_with_automation(*, dry_run_passed: bool | None) -> TestContext:
    context = TestContext(
        created_by="pytest",
        ticket=TicketData(id="W5-1", title="retry reset", labels=["phase3"]),
    )
    context.automation = {
        "TC001": AutomationBlock(
            test_case_id="TC001",
            robot_file="generated/TC001.robot",
            validation=AutomationValidation(
                artifact_exists=True,
                dry_run_passed=dry_run_passed,
            ),
            data_reference_check_passed=True,
        )
    }
    return context


def test_invalidate_from_stage_resets_validation_retry_count() -> None:
    """W5: re-running from a stage that invalidates automation must reset the
    retry bookkeeping so the fresh validation loop gets its full retry budget."""
    context = _context_with_automation(dry_run_passed=False)
    context.validation_retry_count = 2  # previously exhausted
    context.graph_iteration = 4
    context.workflow_control.completed_stages = [
        "ticket",
        "requirements",
        "coverage",
        "tests",
        "automation",
        "validation",
    ]

    _invalidate_from_stage(context, "validation")

    assert context.validation_retry_count == 0
    assert context.graph_iteration == 1


def test_invalidate_after_artifact_edit_resets_validation_retry_count() -> None:
    """W5: a manual artifact edit re-runs validation; the retry budget must be
    reset rather than inherited from a prior exhausted run."""
    context = _context_with_automation(dry_run_passed=True)
    context.validation_retry_count = 2
    context.graph_iteration = 3

    _invalidate_after_artifact_edit(context, actor="editor")

    assert context.validation_retry_count == 0
    assert context.graph_iteration == 1


def test_stage_completion_failure_flags_unvalidated_automation() -> None:
    """S2: when validation runs to exhaustion with artifacts that never passed
    dry-run, the stage must be reported as failed (returns a reason), not
    silently marked completed."""
    context = _context_with_automation(dry_run_passed=False)
    reason = _stage_completion_failure(context, "validation")
    assert reason is not None
    assert "TC001" in reason


def test_stage_completion_failure_flags_never_validated_automation() -> None:
    """S2: dry_run_passed is None (never validated) must NOT count as a pass
    (mirrors N1's `is True` predicate)."""
    context = _context_with_automation(dry_run_passed=None)
    assert _stage_completion_failure(context, "validation") is not None


def test_stage_completion_failure_passes_when_all_validated() -> None:
    context = _context_with_automation(dry_run_passed=True)
    assert _stage_completion_failure(context, "validation") is None


def test_stage_completion_failure_ignores_non_validation_stages() -> None:
    """Only the validation loop can finish-without-raising-yet-fail; other stages
    raise on real failure and must not be second-guessed here."""
    context = _context_with_automation(dry_run_passed=False)
    for stage in ("ticket", "requirements", "coverage", "tests", "automation"):
        assert _stage_completion_failure(context, stage) is None
