from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from backend.config.settings import settings
from backend.graph import nodes
from backend.graph.state import (
    ExecutionRequestBlock,
    IntelligenceConfigBlock,
    TestContext,
    TicketData,
    WorkflowStageName,
)

try:
    from langgraph.errors import GraphRecursionError
    from langgraph.graph import END, StateGraph
except ImportError:  # LangGraph is declared but not required for local skeleton tests.
    END = None
    StateGraph = None

    class GraphRecursionError(Exception):  # type: ignore[no-redef]
        """Fallback when LangGraph is absent; never raised on the sequential path."""


# Hard ceiling for the validate -> regenerate loop, independent of the mutable
# ``validation_retry_count``. A logic bug that wedges ``workflow_status`` on
# ``automation_regeneration_requested`` must terminate the loop rather than spin
# forever; the ceiling is generous (retries can be edited up to le=5).
_MAX_VALIDATION_LOOP_ITERATIONS = 16


WorkflowNode = Callable[[TestContext], TestContext]


class _LatestContextCarrier:
    """Captures the most recently completed node output during a graph run.

    LangGraph copies state per super-step, so when a node raises, the outer
    ``context`` reference in :func:`run_workflow` never observes the artifacts
    that *earlier* nodes produced -- the failed run would then persist with zero
    requirements/coverage/tests even though several stages genuinely succeeded
    (W4). Each successful node records its output here so the failure handler can
    copy real pre-crash artifacts back onto the outer context before persisting.

    A fresh carrier is created per :func:`run_workflow` invocation and threaded
    via closure, so there is no shared mutable state between concurrent runs.
    """

    __slots__ = ("latest",)

    def __init__(self) -> None:
        self.latest: TestContext | None = None


# Fields produced by workflow nodes that should survive a mid-run crash. The
# workflow-control block and ``workflow_status`` are deliberately excluded: the
# failure handler owns those and must not have them overwritten by recovery.
_RECOVERABLE_ARTIFACT_FIELDS: tuple[str, ...] = (
    "requirement_analysis",
    "coverage_plan",
    "test_cases",
    "test_data",
    "automation",
    "automation_revision",
    "validation_summary",
    "execution_request",
    "execution",
    "investigation",
    "self_healing",
    "memory_archive",
    "approval",
    "reports",
    "review_feedback",
    "workflow_trace",
    "audit_log",
    "graph_iteration",
    "validation_retry_count",
    "current_node",
)


def _recover_pre_crash_artifacts(
    context: TestContext,
    recovered: TestContext | None,
) -> None:
    """Copy pre-crash artifacts from the carrier onto the outer context.

    No-op when nothing was captured or when the captured object *is* the outer
    context (the sequential path mutates by reference, so there is nothing to
    recover). Only the curated artifact allowlist is copied; the control block
    and workflow status are left for the failure handler to set authoritatively.
    """
    if recovered is None or recovered is context:
        return
    for field in _RECOVERABLE_ARTIFACT_FIELDS:
        setattr(context, field, getattr(recovered, field))

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

# Maps each graph node to the workflow stage it belongs to. Kept in lockstep
# with the frontend `nodeStage` helper (WorkspaceUtils.ts) so backend control
# bookkeeping and the UI agree on which stage a node failure/completion lands in.
_NODE_TO_STAGE: dict[str, WorkflowStageName] = {
    "load_ticket": "ticket",
    "requirement_agent": "requirements",
    "coverage_planner": "coverage",
    "test_case_generator": "tests",
    "test_data_resolver": "tests",
    "automation_generator": "automation",
    "validator": "validation",
    "validation_retry_gate": "validation",
    "human_approval": "approval",
    "execution_dispatcher": "report",
    "investigation_coordinator": "report",
    "memory_archiver": "report",
    "report_generator": "report",
}


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
        # Tag the failing node/stage onto the exception itself. LangGraph copies
        # node state, so the outer context reference may not observe the failed
        # node's trace — but the exception object propagates unchanged, making
        # this the reliable carrier for failure attribution in run_workflow.
        exc.aegis_failed_node = name  # type: ignore[attr-defined]
        exc.aegis_failed_stage = _NODE_TO_STAGE.get(name)  # type: ignore[attr-defined]
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
    def invoke(
        self,
        initial_state: TestContext | dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> TestContext:
        # ``config`` (e.g. recursion_limit) is a LangGraph concept; the
        # sequential fallback has its own per-loop ceiling and ignores it.
        context = _coerce_context(initial_state)
        context = _run_nodes(context, PRE_VALIDATION_NODE_SEQUENCE)

        iterations = 0
        while True:
            context = _run_nodes(context, VALIDATION_LOOP_NODE_SEQUENCE)
            if context.workflow_status != "automation_regeneration_requested":
                break
            iterations += 1
            if iterations >= _MAX_VALIDATION_LOOP_ITERATIONS:
                raise RuntimeError(
                    "Validation regeneration loop exceeded "
                    f"{_MAX_VALIDATION_LOOP_ITERATIONS} iterations "
                    f"(retry_count={context.validation_retry_count}, "
                    f"max={context.max_validation_retries}); aborting to avoid a "
                    "non-terminating workflow."
                )
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


def build_langgraph_workflow(
    carrier: _LatestContextCarrier | None = None,
) -> Any:
    if StateGraph is None or END is None:
        raise RuntimeError("LangGraph is not installed")

    workflow = StateGraph(TestContext)
    for name, node in NODE_SEQUENCE:
        workflow.add_node(name, _wrap_langgraph_node(name, node, carrier))

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


def _wrap_langgraph_node(
    name: str,
    node: WorkflowNode,
    carrier: _LatestContextCarrier | None = None,
) -> WorkflowNode:
    def wrapped(context: TestContext) -> TestContext:
        updated = _invoke_node(name, node, context)
        if carrier is not None:
            # Record the freshest successful node output so a later node's crash
            # can still persist these real, pre-crash artifacts (W4).
            carrier.latest = updated
        return updated

    return wrapped


def build_workflow(carrier: _LatestContextCarrier | None = None) -> Any:
    if StateGraph is not None:
        return build_langgraph_workflow(carrier)
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


def _apply_honest_completion(context: TestContext) -> TestContext:
    """Derive workflow-control bookkeeping from real artifacts, not assumptions.

    The autonomous pipeline runs every node, but ``execution_dispatcher`` always
    defers when approval is not granted -- and autonomous ``human_approval`` only
    ever produces ``pending_review``. So an autonomous run structurally stops at
    the approval gate: execution is skipped and the human approval decision is
    still outstanding. Stamping all eight stages "completed" (as the prior code
    did unconditionally) misreports that gate as passed.

    Each stage is marked completed only when its own evidence predicate holds, so
    every entry in ``completed_stages`` is traceable to an actual artifact.

    ``state`` describes the *autonomous control session*, not the workflow
    lifecycle: it reaches ``completed`` because the autonomous run executed to its
    natural stopping point (the approval gate) and will not advance further on its
    own. The outstanding human-approval gate is represented honestly elsewhere --
    ``approval`` is absent from ``completed_stages`` and ``approval.status`` stays
    ``pending_review`` until a human decides. (The frontend approval panel keys on
    ``approval.status == 'pending_review' && state == 'completed'``, so this
    terminal state preserves that verified flow.) A genuinely approved + executed
    run additionally marks the approval and report stages completed.
    """
    control = context.workflow_control
    approval_status = context.approval.status if context.approval else None
    approved = approval_status == "approved"
    execution_status = context.execution.status if context.execution else None
    execution_ran = execution_status in {"passed", "failed"}

    # (stage, evidence predicate) -- order matches WORKFLOW_STAGE_SEQUENCE.
    stage_evidence: list[tuple[WorkflowStageName, bool]] = [
        ("ticket", context.ticket is not None),
        ("requirements", context.requirement_analysis is not None),
        ("coverage", context.coverage_plan is not None),
        ("tests", bool(context.test_cases) and bool(context.test_data)),
        ("automation", bool(context.automation)),
        (
            "validation",
            bool(context.automation)
            and all(
                block.validation.dry_run_passed is True
                for block in context.automation.values()
            ),
        ),
        # Approval is "completed" only when genuinely granted -- never on the
        # autonomous deferral where status is still pending_review.
        ("approval", approved),
        # Report stage is genuinely done only when a report exists AND real
        # execution happened. On the autonomous deferral execution is skipped,
        # so the generated report is a pre-execution draft, not a final report.
        ("report", context.reports is not None and execution_ran),
    ]
    completed: list[WorkflowStageName] = [
        stage for stage, ok in stage_evidence if ok
    ]
    control.completed_stages = completed
    control.stage_revisions = {stage: 1 for stage in completed}

    # The autonomous control session has run to its natural end either way; the
    # difference between a deferred run and a fully-executed one is carried by
    # completed_stages (above) + approval.status, not by faking extra stages.
    control.state = "completed"
    control.current_stage = None
    control.next_stage = None
    control.last_error = None
    return context


def run_workflow(context: TestContext) -> TestContext:
    context.workflow_control.mode = "autonomous"
    context.workflow_control.state = "running"
    context.workflow_control.current_stage = "ticket"
    carrier = _LatestContextCarrier()
    try:
        workflow = build_workflow(carrier)
        result = workflow.invoke(context, config=_graph_invoke_config(context))
    except GraphRecursionError as exc:
        # The validate -> regenerate loop hit LangGraph's recursion ceiling. This
        # is raised *outside* _invoke_node so it carries no stage attribution;
        # attribute it to validation (the only loop in the graph) explicitly.
        _recover_pre_crash_artifacts(context, carrier.latest)
        control = context.workflow_control
        control.state = "failed"
        control.current_stage = "validation"
        control.next_stage = None
        control.last_error = f"{type(exc).__name__}: {exc}"
        context.mark("validation_failed")
        raise
    except Exception as exc:  # noqa: BLE001 - contain failure, record diagnostics, re-raise.
        # LangGraph copies state per super-step, so the outer context never saw
        # the artifacts earlier nodes produced; recover them from the carrier
        # before persisting so the failed run is inspectable (W4).
        _recover_pre_crash_artifacts(context, carrier.latest)
        control = context.workflow_control
        failed_stage = getattr(exc, "aegis_failed_stage", None)
        failed_node = getattr(exc, "aegis_failed_node", None)
        control.state = "failed"
        control.current_stage = failed_stage
        control.next_stage = None
        control.last_error = f"{type(exc).__name__}: {exc}"
        context.mark(f"{failed_stage or failed_node or 'workflow'}_failed")
        raise
    completed = (
        result
        if isinstance(result, TestContext)
        else TestContext.model_validate(result)
    )
    return _apply_honest_completion(completed)


def _graph_invoke_config(context: TestContext) -> dict[str, Any]:
    """Recursion limit sized to the real worst-case graph traversal.

    LangGraph defaults to ``recursion_limit=25``, but the validate -> regenerate
    loop adds up to ``max_validation_retries`` extra passes through the
    3-node validation block (validator, retry gate, automation generator). With
    13 nodes + 5 retries x 3 nodes = 28 > 25, the default would raise
    ``GraphRecursionError`` mid-loop on a heavily-retried run. Size the limit to
    the worst case plus a small safety margin so a legitimate retry sequence
    completes, while the per-loop ceiling in ``_run_validation_stage`` /
    ``SequentialWorkflow`` still guards against a genuine non-terminating loop.
    """
    worst_case = (
        len(NODE_SEQUENCE)
        + context.max_validation_retries * len(VALIDATION_LOOP_NODE_SEQUENCE)
        + 5
    )
    return {"recursion_limit": worst_case}


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
    iterations = 0
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
        iterations += 1
        if iterations >= _MAX_VALIDATION_LOOP_ITERATIONS:
            raise RuntimeError(
                "Validation regeneration loop exceeded "
                f"{_MAX_VALIDATION_LOOP_ITERATIONS} iterations "
                f"(retry_count={context.validation_retry_count}, "
                f"max={context.max_validation_retries}); aborting to avoid a "
                "non-terminating workflow."
            )
        context = _run_nodes(
            context,
            (("automation_generator", nodes.automation_generator),),
        )


def run_post_approval_workflow(
    context: TestContext,
    *,
    requested_by: str,
    adapter: str | None = None,
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
        adapter=adapter or settings.default_execution_adapter,
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
