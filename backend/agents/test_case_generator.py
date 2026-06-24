from __future__ import annotations

import backend.skills.test_generation  # Registers GenerateTestCasesSkill.
from backend.agents.base import BaseAgent, agent_registry
from backend.graph.state import TestContext
from backend.skills.base import SkillRegistry, skill_registry as default_skill_registry


@agent_registry.register(
    name="TestCaseGeneratorAgent",
    skills=["GenerateTestCasesSkill"],
    description="Coordinates deterministic test case generation for a workflow.",
    uses_llm=True,
    risk_tier="high",
)
class TestCaseGeneratorAgent(BaseAgent):
    def __init__(self, *, skill_registry: SkillRegistry | None = None) -> None:
        super().__init__(skill_registry=skill_registry or default_skill_registry)

    def run(self, context: TestContext) -> TestContext:
        skill = self.skill_registry.create("GenerateTestCasesSkill")
        return skill.execute(context)
