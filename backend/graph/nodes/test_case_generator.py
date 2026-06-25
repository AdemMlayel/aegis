import backend.agents.test_case_generator  # noqa: F401 - registers TestCaseGeneratorAgent
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def test_case_generator(context: TestContext) -> TestContext:
    return agent_registry.create("TestCaseGeneratorAgent").run(context)
