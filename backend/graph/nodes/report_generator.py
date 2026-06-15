from backend.graph.state import ReportBlock, TestContext


def report_generator(context: TestContext) -> TestContext:
    if context.coverage_plan is None:
        raise ValueError("ReportGenerator requires context.coverage_plan")

    automation_count = len(context.automation)
    validated_count = sum(
        1
        for automation in context.automation.values()
        if automation.validation.dry_run_passed is True
    )
    approval_status = context.approval.status if context.approval else "not_ready"
    context.reports = ReportBlock(
        summary=(
            f"Generated {len(context.test_cases)} starter test cases and "
            f"{automation_count} Robot automation files for "
            f"{context.ticket.id if context.ticket else 'unknown ticket'}. "
            f"Validated {validated_count}/{automation_count}; "
            f"approval status is {approval_status}."
        ),
        total_test_cases=len(context.test_cases),
        highest_risk=context.coverage_plan.risk_level,
        next_actions=[
            "Review requirement clarification questions",
            "Review generated Robot files through the automation file endpoint",
            "Replace the Git handoff stub with real branch and PR creation",
            "Add audit records for approval decisions",
        ],
    )
    context.mark("report_generated")
    return context
