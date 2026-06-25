from __future__ import annotations

import backend.tools.reporting  # noqa: F401 - registers LocalReportGenerationTool
from backend.graph.state import PromptUsageRef, ReportBlock, TestContext
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

        result = self.tool_registry.execute(
            "LocalReportGenerationTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            coverage_plan=context.coverage_plan,
            ticket=context.ticket,
            test_cases=context.test_cases,
            automation=context.automation,
            approval=context.approval,
            execution=context.execution,
            investigation=context.investigation,
            memory_archive=context.memory_archive,
            intelligence_trace=context.intelligence_trace,
            context=context,
        )
        report = result.value
        if not isinstance(report, ReportBlock):
            raise TypeError("Report generation tools must return ReportBlock")

        context.reports = report
        prompt_key = ("report_generation_v1", "1.0.0")
        if prompt_key not in {(item.name, item.version) for item in context.intelligence_trace.prompt_versions}:
            context.intelligence_trace.prompt_versions.append(
                PromptUsageRef(name=prompt_key[0], version=prompt_key[1])
            )
        context.mark("report_generated")
        return context
