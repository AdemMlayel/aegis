from __future__ import annotations

import backend.tools.test_case_heuristics  # Registers LocalTestCaseHeuristicTool.
from backend.graph.state import PromptUsageRef, TestCase, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="GenerateTestCasesSkill",
    tools=["LocalTestCaseHeuristicTool"],
    description="Generates test cases from analyzed requirements and coverage.",
)
class GenerateTestCasesSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if context.requirement_analysis is None:
            raise ValueError("TestCaseGenerator requires context.requirement_analysis")
        if context.coverage_plan is None:
            raise ValueError("TestCaseGenerator requires context.coverage_plan")

        result = self.tool_registry.execute(
            "LocalTestCaseHeuristicTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            requirement_analysis=context.requirement_analysis,
            coverage_plan=context.coverage_plan,
            ticket=context.ticket,
            context=context,
        )
        test_cases = result.value
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("Test case generation tools must return list[TestCase]")

        context.test_cases = test_cases
        prompt_key = ("test_case_generation_v1", "1.0.0")
        if prompt_key not in {(item.name, item.version) for item in context.intelligence_trace.prompt_versions}:
            context.intelligence_trace.prompt_versions.append(
                PromptUsageRef(name=prompt_key[0], version=prompt_key[1])
            )
        context.mark("test_cases_generated")
        return context
