from __future__ import annotations

from typing import Any

from backend.graph.state import (
    ApprovalBlock,
    AutomationBlock,
    CoveragePlan,
    ReportBlock,
    TestCase,
    TicketData,
)
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalReportGenerationTool",
    isolation="process",
    description="Builds deterministic workflow reports from generated artifacts.",
)
class LocalReportGenerationTool(BaseTool):
    def invoke(self, **kwargs: Any) -> ReportBlock:
        coverage_plan = kwargs.get("coverage_plan")
        ticket = kwargs.get("ticket")
        test_cases = kwargs.get("test_cases")
        automation = kwargs.get("automation")
        approval = kwargs.get("approval")

        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("LocalReportGenerationTool requires CoveragePlan")
        if ticket is not None and not isinstance(ticket, TicketData):
            raise TypeError("LocalReportGenerationTool requires TicketData or None")
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("LocalReportGenerationTool requires list[TestCase]")
        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "LocalReportGenerationTool requires dict[str, AutomationBlock]"
            )
        if approval is not None and not isinstance(approval, ApprovalBlock):
            raise TypeError("LocalReportGenerationTool requires ApprovalBlock or None")

        return generate_report(
            coverage_plan=coverage_plan,
            ticket=ticket,
            test_cases=test_cases,
            automation=automation,
            approval=approval,
        )


def generate_report(
    *,
    coverage_plan: CoveragePlan,
    ticket: TicketData | None,
    test_cases: list[TestCase],
    automation: dict[str, AutomationBlock],
    approval: ApprovalBlock | None,
) -> ReportBlock:
    automation_count = len(automation)
    validated_count = sum(
        1
        for automation_block in automation.values()
        if automation_block.validation.dry_run_passed is True
    )
    approval_status = approval.status if approval else "not_ready"

    return ReportBlock(
        summary=(
            f"Generated {len(test_cases)} starter test cases and "
            f"{automation_count} Robot automation files for "
            f"{ticket.id if ticket else 'unknown ticket'}. "
            f"Validated {validated_count}/{automation_count}; "
            f"approval status is {approval_status}."
        ),
        total_test_cases=len(test_cases),
        highest_risk=coverage_plan.risk_level,
        next_actions=[
            "Review requirement clarification questions",
            "Review generated Robot files through the automation file endpoint",
            "Replace the Git handoff stub with real branch and PR creation",
            "Add audit records for approval decisions",
        ],
    )
