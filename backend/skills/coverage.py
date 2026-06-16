from __future__ import annotations

import backend.tools.coverage_heuristics  # Registers LocalCoverageHeuristicTool.
from backend.graph.state import CoveragePlan, TestContext
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

        tool = self.tool_registry.create("LocalCoverageHeuristicTool")
        coverage_plan = tool.invoke(
            ticket=context.ticket,
            requirement_analysis=context.requirement_analysis,
        )
        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("Coverage planning tools must return CoveragePlan")

        context.coverage_plan = coverage_plan
        context.mark("coverage_planned")
        return context
