from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from backend.graph import nodes
from backend.graph.state import (
    ExecutionRequestBlock,
    IntelligenceConfigBlock,
    TestContext,
    TicketData,
    WorkflowStageName,
)

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # LangGraph is declared but not required for local skeleton tests.
    END = None
    StateGraph = None


WorkflowNode = Callable[[TestContext], TestContext]

PRE_VALIDATION_NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    ("load_ticket", nodes.load_ticket),
    ("requirement_agent", nodes.requirement_agent),
    ("coverage_planner", nodes.coverage_planner),
    ("test_case_generator", nodes.test_case_generator),
    ("test_data_resolver", nodes.test_data_resolver),
)

VALIDATION_LOOP_NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    ("automation_generator", nodes.automation_generator),
    ("validator", nodes.validator),
    ("validation_retry_gate", nodes.validation_retry_gate),
)

POST_VALIDATION_NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    ("human_approval", nodes.human_approval),
    ("execution_dispatcher", nodes.execution_dispatcher),
    ("investigation_coordinator", nodes.investigation_coordinator),
    ("memory_archiver", nodes.memory_archiver),
    ("report_generator", nodes.report_generator),
)

POST_APPROVAL_NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    ("execution_dispatcher", nodes.execution_dispatcher),
    ("investigation_coordinator", nodes.investigation_coordinator),
    ("memory_archiver", nodes.memory_archiver),
    ("report_generator", nodes.report_generator),
)

NODE_SEQUENCE: tuple[tuple[str, WorkflowNode], ...] = (
    *PRE_VALIDATION_NODE_SEQUENCE,
    *VALIDATION_LOOP_NODE_SEQUENCE,
    *POST_VALIDATION_NODE_SEQUENCE,
)

WORKFLOW_STAGE_SEQUENCE: tuple[WorkflowStageName, ...] = (
    "ticket",
    "requirements",
    "coverage",
    "tests",
    "automation",
    "validation",
    "approval",
    "report",
)

REVIEWABLE_WORKFLOW_STAGES: frozenset[WorkflowStageName] = frozenset(
    {
        "requirements",
        "coverage",
        "tests",
        "automation",
        "validation",
        "report",
    }
)


def _coerce_context(initial_state: TestContext | dict[str, Any]) -> TestContext:
    return (
        initial_state
        if isinstance(initial_state, TestContext)
        else TestContext.model_validate(initial_state)
    )


def _invoke_node(name: str, node: WorkflowNode, context: TestContext) -> TestContext:
    context.trace_node(node_name=name, status="started")
    try:
        updated = node(context)
    except Exception as exc:  # noqa: BLE001 - graph traces failures for audit/debug.
        context.trace_node(
            node_name=name,
            status="failed",
            summary=str(exc),
            metadata={"exception_type": type(exc).__name__},
        )
        raise
    updated.trace_node(
        node_name=name,
        status="completed",
        summary=f"Node completed with workflow status {updated.workflow_status}.",
    )
    return updated


def _run_nodes(
    context: TestContext,
    sequence: Iterable[tuple[str, WorkflowNode]],
) -> TestContext:
    for name, node in sequence:
        context = _invoke_node(name, node, context)
    return context


class SequentialWorkflow:
    def invoke(self, initial_state: TestContext | dict[str, Any]) -> TestContext:
        context = _coerce_context(initial_state)
        context = _run_nodes(context, PRE_VALIDATION_NODE_SEQUENCE)

        while True:
            context = _run_nodes(context, VALIDATION_LOOP_NODE_SEQUENCE)
            if context.workflow_status != "automation_regeneration_requested":
                break
            context.trace_node(
                node_name="validation_retry_gate",
                status="routed",
                summary="Routing back to automation generation after validation failure.",
                metadata={
                    "retry_count": context.validation_retry_count,
                    "max_retries": context.max_validation_retries,
                },
            )

        return _run_nodes(context, POST_VALIDATION_NODE_SEQUENCE)


def _route_after_validation_gate(context: TestContext) -> str:
    if context.workflow_status == "automation_regeneration_requested":
        context.trace_node(
            node_name="validation_retry_gate",
            status="routed",
            summary="Routing back to automation generation after validation failure.",
            metadata={
                "retry_count": context.validation_retry_count,
                "max_retries": context.max_validation_retries,
            },
        )
        return "automation_generator"
    return "human_approval"


def build_langgraph_workflow() -> Any:
    if StateGraph is None or END is None:
        raise RuntimeError("LangGraph is not installed")

    workflow = StateGraph(TestContext)
    for name, node in NODE_SEQUENCE:
        workflow.add_node(name, _wrap_langgraph_node(name, node))

    workflow.set_entry_point("load_ticket")
    workflow.add_edge("load_ticket", "requirement_agent")
    workflow.add_edge("requirement_agent", "coverage_planner")
    workflow.add_edge("coverage_planner", "test_case_generator")
    workflow.add_edge("test_case_generator", "test_data_resolver")
    workflow.add_edge("test_data_resolver", "automation_generator")
    workflow.add_edge("automation_generator", "validator")
    workflow.add_edge("validator", "validation_retry_gate")
    workflow.add_conditional_edges(
        "validation_retry_gate",
        _route_after_validation_gate,
        {
            "automation_generator": "automation_generator",
            "human_approval": "human_approval",
        },
    )
    workflow.add_edge("human_approval", "execution_dispatcher")
    workflow.add_edge("execution_dispatcher", "investigation_coordinator")
    workflow.add_edge("investigation_coordinator", "memory_archiver")
    workflow.add_edge("memory_archiver", "report_generator")
    workflow.add_edge("report_generator", END)
    return workflow.compile()


def _wrap_langgraph_node(name: str, node: WorkflowNode) -> WorkflowNode:
    def wrapped(context: TestContext) -> TestContext:
        return _invoke_node(name, node, context)

    return wrapped


def build_workflow() -> Any:
    if StateGraph is not None:
        return build_langgraph_workflow()
    return SequentialWorkflow()


def create_initial_context(
    *,
    created_by: str = "local-user",
    ticket: TicketData | None = None,
    intelligence_config: IntelligenceConfigBlock | None = None,
) -> TestContext:
    context = TestContext(
        created_by=created_by,
        ticket=ticket,
        intelligence_config=intelligence_config or IntelligenceConfigBlock(),
    )
    context.sync_intelligence_trace_config()
    return context


def run_workflow(context: TestContext) -> TestContext:
    context.workflow_control.mode = "autonomous"
    context.workflow_control.state = "running"
    context.workflow_control.current_stage = "ticket"
    result = build_workflow().invoke(context)
    completed = (
        result
        if isinstance(result, TestContext)
        else TestContext.model_validate(result)
    )
    completed.workflow_control.state = "completed"
    completed.workflow_control.current_stage = None
    completed.workflow_control.next_stage = None
    completed.workflow_control.completed_stages = list(WORKFLOW_STAGE_SEQUENCE)
    completed.workflow_control.stage_revisions = {
        stage: 1 for stage in WORKFLOW_STAGE_SEQUENCE
    }
    return completed


def run_workflow_stage(
    context: TestContext,
    stage: WorkflowStageName,
) -> TestContext:
    if stage == "ticket":
        return _run_nodes(context, (("load_ticket", nodes.load_ticket),))
    if stage == "requirements":
        return _run_nodes(
            context,
            (("requirement_agent", nodes.requirement_agent),),
        )
    if stage == "coverage":
        return _run_nodes(
            context,
            (("coverage_planner", nodes.coverage_planner),),
        )
    if stage == "tests":
        return _run_nodes(
            context,
            (
                ("test_case_generator", nodes.test_case_generator),
                ("test_data_resolver", nodes.test_data_resolver),
            ),
        )
    if stage == "automation":
        return _run_nodes(
            context,
            (("automation_generator", nodes.automation_generator),),
        )
    if stage == "validation":
        return _run_validation_stage(context)
    if stage == "approval":
        return _run_nodes(
            context,
            (("human_approval", nodes.human_approval),),
        )
    if stage == "report":
        sequence: list[tuple[str, WorkflowNode]] = []
        if context.execution is None:
            sequence.append(("execution_dispatcher", nodes.execution_dispatcher))
        if context.investigation is None:
            sequence.append(
                ("investigation_coordinator", nodes.investigation_coordinator)
            )
        if context.memory_archive is None:
            sequence.append(("memory_archiver", nodes.memory_archiver))
        sequence.append(("report_generator", nodes.report_generator))
        return _run_nodes(context, sequence)
    raise ValueError(f"Unsupported workflow stage '{stage}'")


def next_workflow_stage(
    stage: WorkflowStageName,
) -> WorkflowStageName | None:
    index = WORKFLOW_STAGE_SEQUENCE.index(stage)
    if index + 1 >= len(WORKFLOW_STAGE_SEQUENCE):
        return None
    return WORKFLOW_STAGE_SEQUENCE[index + 1]


def _run_validation_stage(context: TestContext) -> TestContext:
    while True:
        context = _run_nodes(
            context,
            (
                ("validator", nodes.validator),
                ("validation_retry_gate", nodes.validation_retry_gate),
            ),
        )
        if context.workflow_status != "automation_regeneration_requested":
            return context
        context = _run_nodes(
            context,
            (("automation_generator", nodes.automation_generator),),
        )


def run_post_approval_workflow(
    context: TestContext,
    *,
    requested_by: str,
    adapter: str = "mock",
    env: str = "local",
    branch: str | None = None,
    tags: Iterable[str] = (),
) -> TestContext:
    """Run the blueprint nodes that occur after human approval.

    The initial synchronous workflow defers execution until approval. This helper
    resumes the graph locally with mock or local Robot adapters, then continues
    investigation, memory archive, and report generation so the orchestration can
    be demonstrated without company APIs.
    """
    context.execution_request = ExecutionRequestBlock(
        requested_by=requested_by,
        adapter=adapter,
        env=env,
        branch=branch,
        tags=list(tags),
    )
    return _run_nodes(context, POST_APPROVAL_NODE_SEQUENCE)


def run_after_execution_analysis(context: TestContext) -> TestContext:
    """Run investigation, memory archive, and reporting after an execution adapter."""
    return _run_nodes(
        context,
        (
            ("investigation_coordinator", nodes.investigation_coordinator),
            ("memory_archiver", nodes.memory_archiver),
            ("report_generator", nodes.report_generator),
        ),
    )
