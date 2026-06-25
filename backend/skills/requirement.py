from __future__ import annotations

import backend.tools.requirement_heuristics  # noqa: F401 - registers LocalRequirementHeuristicTool
from backend.graph.state import PromptUsageRef, RequirementAnalysis, TestContext
from backend.intelligence.context import record_knowledge_refs, record_memory_refs, search_knowledge_for_ticket, search_memory_for_ticket
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

        result = self.tool_registry.execute(
            "LocalRequirementHeuristicTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            ticket=context.ticket,
            context=context,
        )
        analysis = result.value
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError("Requirement analysis tools must return RequirementAnalysis")

        context.requirement_analysis = analysis
        if context.ticket is not None:
            record_knowledge_refs(
                context,
                search_knowledge_for_ticket(context.ticket, limit=3, context=context),
            )
            record_memory_refs(
                context,
                search_memory_for_ticket(context.ticket, limit=3, context=context),
            )
        for prompt_ref in analysis.prompt_versions_used:
            name, version = prompt_ref.split("@", 1)
            if (name, version) not in {(item.name, item.version) for item in context.intelligence_trace.prompt_versions}:
                context.intelligence_trace.prompt_versions.append(PromptUsageRef(name=name, version=version))
        context.mark("requirements_analyzed")
        return context
