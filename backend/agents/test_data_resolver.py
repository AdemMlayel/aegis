from __future__ import annotations

import backend.skills.test_data  # noqa: F401 - registers ResolveTestDataSkill
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="TestDataResolverAgent",
    skills=["ResolveTestDataSkill"],
    description="Coordinates deterministic test data resolution for generated cases.",
)
class TestDataResolverAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("ResolveTestDataSkill")
        return skill.execute(context)
