from __future__ import annotations

from backend.graph.state import (
    AutomationBlock,
    ExecutionBlock,
    ExecutionCaseResult,
    ExecutionSummary,
    TestCase,
    TestContext,
    utc_now,
)


def run_mock_execution(context: TestContext, *, actor: str) -> TestContext:
    if not context.test_cases or not context.automation:
        raise ValueError("Workflow has no generated automation to execute")

    started_at = utc_now()
    results = [
        _mock_case_result(
            context=context,
            test_case=test_case,
            automation=context.automation.get(test_case.id),
            index=index,
        )
        for index, test_case in enumerate(context.test_cases)
    ]
    finished_at = utc_now()
    summary = ExecutionSummary(
        total=len(results),
        passed=sum(1 for result in results if result.status == "passed"),
        failed=sum(1 for result in results if result.status == "failed"),
        skipped=sum(1 for result in results if result.status == "skipped"),
        duration_ms=sum(result.duration_ms for result in results),
    )
    execution_status = (
        "failed"
        if summary.failed
        else "skipped"
        if summary.skipped and not summary.passed
        else "passed"
    )

    context.execution = ExecutionBlock(
        status=execution_status,
        run_by=actor,
        started_at=started_at,
        finished_at=finished_at,
        summary=summary,
        results=results,
    )
    context.mark(f"mock_execution_{execution_status}")
    context.record_event(
        actor=actor,
        event_type="execution_completed",
        summary=f"Mock execution {execution_status}.",
        metadata={
            "context_id": context.context_id,
            "execution_status": execution_status,
            "passed": summary.passed,
            "failed": summary.failed,
            "skipped": summary.skipped,
        },
    )
    return context


def _mock_case_result(
    *,
    context: TestContext,
    test_case: TestCase,
    automation: AutomationBlock | None,
    index: int,
) -> ExecutionCaseResult:
    status, message = _mock_status(context, test_case, automation)
    duration_ms = 0 if status == "skipped" else 900 + (index * 173) + len(test_case.steps) * 41
    logs = [
        f"Loaded {automation.robot_file if automation else 'missing Robot artifact'}",
        f"Scenario: {test_case.title}",
        message,
    ]
    return ExecutionCaseResult(
        test_case_id=test_case.id,
        title=test_case.title,
        status=status,
        duration_ms=duration_ms,
        robot_file=automation.robot_file if automation else None,
        message=message,
        logs=logs,
    )


def _mock_status(
    context: TestContext,
    test_case: TestCase,
    automation: AutomationBlock | None,
) -> tuple[str, str]:
    if automation is None:
        return "skipped", "Skipped because no generated automation artifact exists."
    if not (
        automation.validation.artifact_exists
        and automation.data_reference_check_passed
        and automation.validation.dry_run_passed is True
    ):
        return "skipped", "Skipped because dry-run validation is not green."

    ticket_priority = context.ticket.priority if context.ticket else "medium"
    if ticket_priority in {"high", "critical"} and test_case.type == "negative":
        return (
            "failed",
            "Mock assertion failed: rejection behavior did not match the generated oracle.",
        )
    if ticket_priority == "low" and test_case.type == "boundary":
        return "skipped", "Skipped by the low-risk mock execution profile."
    return "passed", "Mock execution completed successfully."
