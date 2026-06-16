from __future__ import annotations

import backend.skills.human_approval  # Registers RequestHumanApprovalSkill.
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="HumanApprovalAgent",
    skills=["RequestHumanApprovalSkill"],
    description="Coordinates human approval request creation for validated automation.",
)
class HumanApprovalAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("RequestHumanApprovalSkill")
        return skill.execute(context)
