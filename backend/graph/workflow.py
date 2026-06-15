from collections.abc import Callable
from typing import Any

from backend.graph import nodes
from backend.graph.state import TestContext, TicketData

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # LangGraph is declared but not required for local skeleton tests.
    END = None
    StateGraph = None


WorkflowNode = Callable[[TestContext], TestContext]

NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    ("load_ticket", nodes.load_ticket),
    ("requirement_agent", nodes.requirement_agent),
    ("coverage_planner", nodes.coverage_planner),
    ("test_case_generator", nodes.test_case_generator),
    ("test_data_resolver", nodes.test_data_resolver),
    ("automation_generator", nodes.automation_generator),
    ("validator", nodes.validator),
    ("human_approval", nodes.human_approval),
    ("report_generator", nodes.report_generator),
)


class SequentialWorkflow:
    def invoke(self, initial_state: TestContext | dict[str, Any]) -> TestContext:
        context = (
            initial_state
            if isinstance(initial_state, TestContext)
            else TestContext.model_validate(initial_state)
        )
        for _, node in NODE_SEQUENCE:
            context = node(context)
        return context


def build_langgraph_workflow() -> Any:
    if StateGraph is None or END is None:
        raise RuntimeError("LangGraph is not installed")

    workflow = StateGraph(TestContext)
    for name, node in NODE_SEQUENCE:
        workflow.add_node(name, node)

    workflow.set_entry_point("load_ticket")
    workflow.add_edge("load_ticket", "requirement_agent")
    workflow.add_edge("requirement_agent", "coverage_planner")
    workflow.add_edge("coverage_planner", "test_case_generator")
    workflow.add_edge("test_case_generator", "test_data_resolver")
    workflow.add_edge("test_data_resolver", "automation_generator")
    workflow.add_edge("automation_generator", "validator")
    workflow.add_edge("validator", "human_approval")
    workflow.add_edge("human_approval", "report_generator")
    workflow.add_edge("report_generator", END)
    return workflow.compile()


def build_workflow() -> Any:
    if StateGraph is not None:
        return build_langgraph_workflow()
    return SequentialWorkflow()


def create_initial_context(
    *, created_by: str = "local-user", ticket: TicketData | None = None
) -> TestContext:
    return TestContext(created_by=created_by, ticket=ticket)


def run_workflow(context: TestContext) -> TestContext:
    result = build_workflow().invoke(context)
    return result if isinstance(result, TestContext) else TestContext.model_validate(result)
