from __future__ import annotations

import backend.tools.reporting  # Registers LocalReportGenerationTool.
from backend.graph.state import ReportBlock, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="GenerateReportSkill",
    tools=["LocalReportGenerationTool"],
    description="Generates deterministic workflow reports for review dashboards.",
)
class GenerateReportSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if context.coverage_plan is None:
            raise ValueError("ReportGenerator requires context.coverage_plan")

        tool = self.tool_registry.create("LocalReportGenerationTool")
        report = tool.invoke(
            coverage_plan=context.coverage_plan,
            ticket=context.ticket,
            test_cases=context.test_cases,
            automation=context.automation,
            approval=context.approval,
        )
        if not isinstance(report, ReportBlock):
            raise TypeError("Report generation tools must return ReportBlock")

        context.reports = report
        context.mark("report_generated")
        return context
