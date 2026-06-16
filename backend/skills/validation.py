from __future__ import annotations

import backend.tools.robot_validation  # Registers LocalRobotValidationTool.
from backend.graph.state import AutomationBlock, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="ValidateAutomationSkill",
    tools=["LocalRobotValidationTool"],
    description="Validates generated automation artifacts before human approval.",
)
class ValidateAutomationSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if not context.automation:
            raise ValueError("Validator requires context.automation")

        result = self.tool_registry.execute(
            "LocalRobotValidationTool",
            actor="system",
            context_id=context.context_id,
            audit_sink=context.record_event,
            automation=context.automation,
            test_data=context.test_data,
        )
        automation = result.value
        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "Automation validation tools must return dict[str, AutomationBlock]"
            )

        context.automation = automation
        all_ready = all(
            block.validation.artifact_exists
            and block.data_reference_check_passed
            and block.validation.dry_run_passed is True
            for block in context.automation.values()
        )
        context.mark(
            "automation_validated" if all_ready else "automation_validation_failed"
        )
        return context
