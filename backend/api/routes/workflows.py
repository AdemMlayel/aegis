from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

import backend.tools.git_handoff  # Registers LocalGitHandoffTool.
from backend.tools.git_handoff import GitExecutionResult
from backend.tools.base import tool_registry
from backend.graph.artifacts import relative_to_project, resolve_robot_file
from backend.graph.regeneration import regenerate_after_changes
from backend.graph.state import ReviewFeedback, TestContext, TicketData, utc_now
from backend.graph.workflow import create_initial_context, run_post_approval_workflow, run_workflow
from backend.storage.audit import append_audit_event
from backend.storage.contexts import list_contexts, load_context, save_context
from backend.security import Capability, Principal, require_capability


router = APIRouter(tags=["workflows"])
ApprovalStatus = Literal[
    "not_ready",
    "pending_review",
    "approved",
    "changes_requested",
]


class StartWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket: TicketData | None = None


class StartWorkflowResponse(BaseModel):
    context: TestContext


class WorkflowContextResponse(BaseModel):
    context: TestContext


class WorkflowSummary(BaseModel):
    context_id: str
    ticket_id: str | None
    ticket_title: str | None
    workflow_status: str
    approval_status: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    test_count: int
    automation_revision: int
    highest_risk: str | None
    git_status: str | None
    execution_status: str | None
    execution_passed: int
    execution_failed: int
    execution_skipped: int
    executed_at: datetime | None


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowSummary]


class AutomationFileResponse(BaseModel):
    ticket_id: str
    file_name: str
    path: str
    content: str


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approve", "request_changes"]
    reviewed_by: str = Field(min_length=1)
    comment: str | None = None


class ApprovalDecisionResponse(BaseModel):
    context: TestContext


class ExecuteWorkflowRequest(BaseModel):
    run_by: str = Field(default="local-user", min_length=1)


class ExecuteWorkflowResponse(BaseModel):
    context: TestContext


def run_and_persist_workflow_start(
    *, created_by: str, ticket: TicketData | None
) -> TestContext:
    context = create_initial_context(created_by=created_by, ticket=ticket)
    completed_context = run_workflow(context)
    summary = "Workflow started and completed the current synchronous pipeline."
    metadata = {
        "context_id": completed_context.context_id,
        "ticket_id": completed_context.ticket.id if completed_context.ticket else None,
        "workflow_status": completed_context.workflow_status,
    }
    completed_context.record_event(
        actor=created_by,
        event_type="workflow_started",
        summary=summary,
        metadata=metadata,
    )
    append_audit_event(
        actor=created_by,
        event_type="workflow_started",
        summary=summary,
        metadata=metadata,
    )
    save_context(completed_context)
    return completed_context


@router.post(
    "/workflows/start",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow(
    request: StartWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.START_WORKFLOW))],
) -> StartWorkflowResponse:
    completed_context = run_and_persist_workflow_start(
        created_by=request.created_by,
        ticket=request.ticket,
    )
    return StartWorkflowResponse(context=completed_context)


def _workflow_summary(context: TestContext) -> WorkflowSummary:
    return WorkflowSummary(
        context_id=context.context_id,
        ticket_id=context.ticket.id if context.ticket else None,
        ticket_title=context.ticket.title if context.ticket else None,
        workflow_status=context.workflow_status,
        approval_status=context.approval.status if context.approval else None,
        created_by=context.created_by,
        created_at=context.created_at,
        updated_at=context.updated_at,
        test_count=len(context.test_cases),
        automation_revision=context.automation_revision,
        highest_risk=context.reports.highest_risk if context.reports else None,
        git_status=context.approval.git_status if context.approval else None,
        execution_status=context.execution.status if context.execution else None,
        execution_passed=context.execution.summary.passed if context.execution else 0,
        execution_failed=context.execution.summary.failed if context.execution else 0,
        execution_skipped=context.execution.summary.skipped if context.execution else 0,
        executed_at=context.execution.finished_at if context.execution else None,
    )


def _workflow_search_blob(context: TestContext) -> str:
    ticket = context.ticket
    return " ".join(
        [
            context.context_id,
            context.created_by,
            context.workflow_status,
            context.approval.status if context.approval else "",
            context.execution.status if context.execution else "",
            ticket.id if ticket else "",
            ticket.title if ticket else "",
            " ".join(ticket.labels) if ticket else "",
        ]
    ).casefold()


@router.get("/workflows", response_model=WorkflowListResponse)
def list_workflow_contexts(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    q: str | None = Query(default=None, min_length=1),
    workflow_status: str | None = None,
    approval_status: ApprovalStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkflowListResponse:
    contexts = list_contexts()
    if workflow_status:
        contexts = [
            context
            for context in contexts
            if context.workflow_status == workflow_status
        ]
    if approval_status:
        contexts = [
            context
            for context in contexts
            if context.approval and context.approval.status == approval_status
        ]
    if q:
        needle = q.casefold()
        contexts = [
            context
            for context in contexts
            if needle in _workflow_search_blob(context)
        ]

    return WorkflowListResponse(
        workflows=[_workflow_summary(context) for context in contexts[:limit]]
    )


@router.get(
    "/workflows/{context_id}",
    response_model=WorkflowContextResponse,
)
def get_workflow_context(
    context_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> WorkflowContextResponse:
    context = load_context(context_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow context was not found",
        )
    return WorkflowContextResponse(context=context)


@router.post(
    "/workflows/{context_id}/execute",
    response_model=ExecuteWorkflowResponse,
)
def execute_workflow(
    context_id: str,
    request: ExecuteWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.EXECUTE_WORKFLOW))],
) -> ExecuteWorkflowResponse:
    context = load_context(context_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow context was not found",
        )

    if context.approval is None or context.approval.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow must be approved before execution",
        )

    context = run_post_approval_workflow(
        context,
        requested_by=request.run_by,
        adapter="mock",
        env="local",
    )
    execution = context.execution
    append_audit_event(
        actor=request.run_by,
        event_type="execution_completed",
        summary=f"Mock execution {execution.status if execution else 'completed'}.",
        metadata={
            "context_id": context.context_id,
            "ticket_id": context.ticket.id if context.ticket else None,
            "execution_status": execution.status if execution else None,
            "passed": execution.summary.passed if execution else 0,
            "failed": execution.summary.failed if execution else 0,
            "skipped": execution.summary.skipped if execution else 0,
        },
    )
    save_context(context)
    return ExecuteWorkflowResponse(context=context)


@router.post(
    "/workflows/{context_id}/approval",
    response_model=ApprovalDecisionResponse,
)
def decide_workflow_approval(
    context_id: str,
    request: ApprovalDecisionRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.APPROVE_WORKFLOW))],
) -> ApprovalDecisionResponse:
    context = load_context(context_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow context was not found",
        )
    if context.approval is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow has not reached the approval step",
        )
    if context.approval.status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow approval is {context.approval.status}",
        )

    context.approval.decided_at = utc_now()
    context.approval.decided_by = request.reviewed_by
    if request.comment:
        context.approval.comments.append(request.comment)

    if request.decision == "request_changes":
        if not request.comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="request_changes decisions require a comment",
            )
        context.review_feedback.append(
            ReviewFeedback(
                requested_by=request.reviewed_by,
                comment=request.comment,
            )
        )
        context.approval.status = "changes_requested"
        context.approval.notes.append("Reviewer requested changes before Git handoff.")
        context.record_event(
            actor=request.reviewed_by,
            event_type="approval_decision",
            summary="Reviewer requested changes.",
            metadata={
                "context_id": context.context_id,
                "decision": request.decision,
                "comment": request.comment,
            },
        )
        append_audit_event(
            actor=request.reviewed_by,
            event_type="approval_decision",
            summary="Reviewer requested changes.",
            metadata={
                "context_id": context.context_id,
                "decision": request.decision,
                "comment": request.comment,
            },
        )
        context.mark("changes_requested")
        context = regenerate_after_changes(context, actor=request.reviewed_by)
        append_audit_event(
            actor=request.reviewed_by,
            event_type="automation_regenerated",
            summary="Automation was regenerated after reviewer feedback.",
            metadata={
                "context_id": context.context_id,
                "automation_revision": context.automation_revision,
            },
        )
        save_context(context)
        return ApprovalDecisionResponse(context=context)

    validation_ready = all(
        automation.validation.dry_run_passed is True
        for automation in context.automation.values()
    )
    if not validation_ready:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow cannot be approved until all automation passes validation",
        )

    git_tool_result = tool_registry.execute(
        "LocalGitHandoffTool",
        actor="system",
        context_id=context.context_id,
        audit_sink=context.record_event,
        context=context,
        reviewed_by=request.reviewed_by,
    )
    git_result = git_tool_result.value
    if not isinstance(git_result, GitExecutionResult):
        raise TypeError("LocalGitHandoffTool must return GitExecutionResult")
    context.approval.status = "approved"
    context.approval.git_branch = git_result.branch
    context.approval.git_commit_sha = git_result.commit_sha
    context.approval.git_pr_url = git_result.pr_url
    context.approval.git_status = "completed" if git_result.status == "completed" else "blocked"
    context.approval.git_error = "\n".join(git_result.errors) if git_result.errors else None
    context.approval.git_handoff_path = git_result.handoff_path.as_posix()
    context.approval.notes.append(
        "Git branch/commit/PR execution completed."
        if git_result.status == "completed"
        else "Git execution was blocked; see git_error and handoff payload."
    )
    context.record_event(
        actor=request.reviewed_by,
        event_type="approval_decision",
        summary="Reviewer approved generated automation.",
        metadata={
            "context_id": context.context_id,
            "decision": request.decision,
            "comment": request.comment,
        },
    )
    context.record_event(
        actor="system",
        event_type="git_execution",
        summary=f"Git execution {git_result.status}.",
        metadata={
            "context_id": context.context_id,
            "branch": git_result.branch,
            "commit_sha": git_result.commit_sha,
            "pr_url": git_result.pr_url,
            "errors": git_result.errors,
        },
    )
    append_audit_event(
        actor=request.reviewed_by,
        event_type="approval_decision",
        summary="Reviewer approved generated automation.",
        metadata={
            "context_id": context.context_id,
            "decision": request.decision,
            "comment": request.comment,
        },
    )
    append_audit_event(
        actor="system",
        event_type="git_execution",
        summary=f"Git execution {git_result.status}.",
        metadata={
            "context_id": context.context_id,
            "branch": git_result.branch,
            "commit_sha": git_result.commit_sha,
            "pr_url": git_result.pr_url,
            "errors": git_result.errors,
        },
    )
    context.mark(
        "approved_git_complete"
        if git_result.status == "completed"
        else "approved_git_blocked"
    )
    save_context(context)
    return ApprovalDecisionResponse(context=context)


@router.get(
    "/automation/files/{ticket_id}/{file_name}",
    response_model=AutomationFileResponse,
)
def read_automation_file(
    ticket_id: str,
    file_name: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
) -> AutomationFileResponse:
    try:
        robot_file = resolve_robot_file(ticket_id, file_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not robot_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated Robot file was not found",
        )

    append_audit_event(
        actor="api",
        event_type="automation_file_read",
        summary="Generated Robot file was read through the API.",
        metadata={
            "ticket_id": ticket_id,
            "file_name": file_name,
            "path": relative_to_project(robot_file),
        },
    )
    return AutomationFileResponse(
        ticket_id=ticket_id,
        file_name=file_name,
        path=relative_to_project(robot_file),
        content=robot_file.read_text(encoding="utf-8"),
    )
