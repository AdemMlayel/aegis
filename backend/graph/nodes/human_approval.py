import backend.agents.human_approval  # noqa: F401 - registers HumanApprovalAgent
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def human_approval(context: TestContext) -> TestContext:
    return agent_registry.create("HumanApprovalAgent").run(context)
