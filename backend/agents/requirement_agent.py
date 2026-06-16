from __future__ import annotations

import backend.skills.requirement  # Registers AnalyzeRequirementSkill.
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="RequirementAgent",
    skills=["AnalyzeRequirementSkill"],
    description="Coordinates requirement analysis for a workflow ticket.",
)
class RequirementAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("AnalyzeRequirementSkill")
        return skill.execute(context)
