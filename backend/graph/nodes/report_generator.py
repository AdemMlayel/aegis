import backend.agents.report_generator  # Registers ReportGeneratorAgent.
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def report_generator(context: TestContext) -> TestContext:
    return agent_registry.create("ReportGeneratorAgent").run(context)
