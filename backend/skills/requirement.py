from __future__ import annotations

import backend.tools.requirement_heuristics  # Registers LocalRequirementHeuristicTool.
from backend.graph.state import RequirementAnalysis, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="AnalyzeRequirementSkill",
    tools=["LocalRequirementHeuristicTool"],
    description="Analyzes ticket requirements through the configured requirement tool.",
)
class AnalyzeRequirementSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if context.ticket is None:
            raise ValueError("RequirementAgent requires context.ticket")

        tool = self.tool_registry.create("LocalRequirementHeuristicTool")
        analysis = tool.invoke(ticket=context.ticket)
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError("Requirement analysis tools must return RequirementAnalysis")

        context.requirement_analysis = analysis
        context.mark("requirements_analyzed")
        return context
