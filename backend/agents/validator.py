from __future__ import annotations

import backend.skills.validation  # noqa: F401 - registers ValidateAutomationSkill
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="ValidatorAgent",
    skills=["ValidateAutomationSkill"],
    description="Coordinates validation for generated automation artifacts.",
    risk_tier="critical",
    require_human_approval=True,
)
class ValidatorAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("ValidateAutomationSkill")
        return skill.execute(context)
