import backend.agents.automation_generator  # Registers AutomationGeneratorAgent.
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def automation_generator(context: TestContext) -> TestContext:
    return agent_registry.create("AutomationGeneratorAgent").run(context)
