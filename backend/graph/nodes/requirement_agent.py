import backend.agents.requirement_agent  # noqa: F401 - registers RequirementAgent
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def requirement_agent(context: TestContext) -> TestContext:
    return agent_registry.create("RequirementAgent").run(context)
