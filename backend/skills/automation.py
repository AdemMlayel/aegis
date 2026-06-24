from __future__ import annotations

import backend.tools.automation_heuristics  # Registers LocalRobotAutomationTool.
from backend.graph.state import AutomationBlock, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="GenerateAutomationSkill",
    tools=["LocalRobotAutomationTool"],
    description="Generates deterministic Robot Framework automation artifacts.",
)
class GenerateAutomationSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if context.ticket is None:
            raise ValueError("AutomationGenerator requires context.ticket")
        if not context.test_cases:
            raise ValueError("AutomationGenerator requires context.test_cases")
        if not context.test_data:
            raise ValueError("AutomationGenerator requires context.test_data")

        revision = context.automation_revision + 1
        feedback = [
            item
            for item in context.review_feedback
            if item.status == "open"
            and item.stage in {None, "automation", "validation"}
        ]
        result = self.tool_registry.execute(
            "LocalRobotAutomationTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            ticket_id=context.ticket.id,
            test_cases=context.test_cases,
            test_data=context.test_data,
            revision=revision,
            feedback=feedback,
        )
        automation = result.value
        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "Automation generation tools must return dict[str, AutomationBlock]"
            )

        context.automation_revision = revision
        for item in context.review_feedback:
            if (
                item.status == "open"
                and item.stage in {None, "automation", "validation"}
            ):
                item.status = "applied"

        context.automation = automation
        context.validation_summary = None
        context.mark("automation_generated")
        return context
