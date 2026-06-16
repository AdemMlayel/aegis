from __future__ import annotations

import backend.tools.test_data_heuristics  # Registers LocalTestDataHeuristicTool.
from backend.graph.state import TestContext, TestDataBlock
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="ResolveTestDataSkill",
    tools=["LocalTestDataHeuristicTool"],
    description="Resolves deterministic test data blocks for generated test cases.",
)
class ResolveTestDataSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if not context.test_cases:
            raise ValueError("TestDataResolver requires context.test_cases")

        result = self.tool_registry.execute(
            "LocalTestDataHeuristicTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            test_cases=context.test_cases,
        )
        test_data = result.value
        if not isinstance(test_data, dict) or not all(
            isinstance(block, TestDataBlock) for block in test_data.values()
        ):
            raise TypeError(
                "Test data resolution tools must return dict[str, TestDataBlock]"
            )

        context.test_data = test_data
        context.mark("test_data_resolved")
        return context
