from __future__ import annotations

import backend.skills.automation  # Registers GenerateAutomationSkill.
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="AutomationGeneratorAgent",
    skills=["GenerateAutomationSkill"],
    description="Coordinates deterministic Robot Framework automation generation.",
)
class AutomationGeneratorAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("GenerateAutomationSkill")
        return skill.execute(context)
