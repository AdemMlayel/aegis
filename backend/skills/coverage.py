from __future__ import annotations

import backend.tools.coverage_heuristics  # noqa: F401 - registers LocalCoverageHeuristicTool
from backend.graph.state import CoveragePlan, PromptUsageRef, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="PlanCoverageSkill",
    tools=["LocalCoverageHeuristicTool"],
    description="Plans risk, coverage matrix, and execution priority.",
)
class PlanCoverageSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if context.requirement_analysis is None:
            raise ValueError("CoveragePlanner requires context.requirement_analysis")
        if context.ticket is None:
            raise ValueError("CoveragePlanner requires context.ticket")

        result = self.tool_registry.execute(
            "LocalCoverageHeuristicTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            ticket=context.ticket,
            requirement_analysis=context.requirement_analysis,
            context=context,
        )
        coverage_plan = result.value
        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("Coverage planning tools must return CoveragePlan")

        context.coverage_plan = coverage_plan
        prompt_key = ("coverage_planning_v1", "1.0.0")
        if prompt_key not in {(item.name, item.version) for item in context.intelligence_trace.prompt_versions}:
            context.intelligence_trace.prompt_versions.append(
                PromptUsageRef(name=prompt_key[0], version=prompt_key[1])
            )
        context.mark("coverage_planned")
        return context
