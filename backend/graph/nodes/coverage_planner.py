import backend.agents.coverage_planner  # Registers CoveragePlannerAgent.
from backend.agents.base import agent_registry
from backend.graph.state import TestContext


def coverage_planner(context: TestContext) -> TestContext:
    return agent_registry.create("CoveragePlannerAgent").run(context)
