from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal

from backend.integrations.git_handoff import create_git_handoff
from backend.graph.artifacts import relative_to_project, resolve_robot_file
from backend.graph.state import TestContext, TicketData, utc_now
from backend.graph.workflow import create_initial_context, run_workflow
from backend.storage.audit import append_audit_event
from backend.storage.contexts import load_context, save_context


router = APIRouter(tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket: TicketData | None = None


class StartWorkflowResponse(BaseModel):
    context: TestContext


class WorkflowContextResponse(BaseModel):
    context: TestContext


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


@router.post(
    "/workflows/start",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow(request: StartWorkflowRequest) -> StartWorkflowResponse:
    context = create_initial_context(created_by=request.created_by, ticket=request.ticket)
    completed_context = run_workflow(context)
    completed_context.record_event(
        actor=request.created_by,
        event_type="workflow_started",
        summary="Workflow started and completed the current synchronous pipeline.",
        metadata={
            "context_id": completed_context.context_id,
            "ticket_id": completed_context.ticket.id if completed_context.ticket else None,
            "workflow_status": completed_context.workflow_status,
        },
    )
    append_audit_event(
        actor=request.created_by,
        event_type="workflow_started",
        summary="Workflow started and completed the current synchronous pipeline.",
        metadata={
            "context_id": completed_context.context_id,
            "ticket_id": completed_context.ticket.id if completed_context.ticket else None,
            "workflow_status": completed_context.workflow_status,
        },
    )
    save_context(completed_context)
    return StartWorkflowResponse(context=completed_context)


@router.get(
    "/workflows/{context_id}",
    response_model=WorkflowContextResponse,
)
def get_workflow_context(context_id: str) -> WorkflowContextResponse:
    context = load_context(context_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow context was not found",
        )
    return WorkflowContextResponse(context=context)


@router.post(
    "/workflows/{context_id}/approval",
    response_model=ApprovalDecisionResponse,
)
def decide_workflow_approval(
    context_id: str, request: ApprovalDecisionRequest
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

    git_result = create_git_handoff(context, request.reviewed_by)
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
def read_automation_file(ticket_id: str, file_name: str) -> AutomationFileResponse:
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
