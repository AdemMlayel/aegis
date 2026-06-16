import backend.agents.validator  # Registers ValidatorAgent.
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def validator(context: TestContext) -> TestContext:
    return agent_registry.create("ValidatorAgent").run(context)
