import backend.agents.test_data_resolver  # noqa: F401 - registers TestDataResolverAgent
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def test_data_resolver(context: TestContext) -> TestContext:
    return agent_registry.create("TestDataResolverAgent").run(context)
