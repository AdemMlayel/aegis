from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.graph.state import TestContext, TicketData
from backend.security import Capability, Principal, require_capability
from backend.services.workflows import (
    ApprovalStatus,
    AutomationFile,
    WorkflowBadRequest,
    WorkflowConflict,
    WorkflowNotFound,
    WorkflowSummary,
    decide_workflow_approval as decide_workflow_approval_service,
    execute_approved_workflow,
    get_workflow,
    list_workflow_summaries,
    read_automation_file as read_automation_file_service,
    start_workflow as start_workflow_service,
)


router = APIRouter(tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket: TicketData | None = None


class StartWorkflowResponse(BaseModel):
    context: TestContext


class WorkflowContextResponse(BaseModel):
    context: TestContext


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowSummary]


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


@router.post(
    "/workflows/start",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow(
    request: StartWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.START_WORKFLOW))],
) -> StartWorkflowResponse:
    completed_context = start_workflow_service(
        created_by=request.created_by,
        ticket=request.ticket,
    )
    return StartWorkflowResponse(context=completed_context)


@router.get("/workflows", response_model=WorkflowListResponse)
def list_workflow_contexts(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    q: str | None = Query(default=None, min_length=1),
    workflow_status: str | None = None,
    approval_status: ApprovalStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkflowListResponse:
    return WorkflowListResponse(
        workflows=list_workflow_summaries(
            q=q,
            workflow_status=workflow_status,
            approval_status=approval_status,
            limit=limit,
        )
    )


@router.get(
    "/workflows/{context_id}",
    response_model=WorkflowContextResponse,
)
def get_workflow_context(
    context_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> WorkflowContextResponse:
    try:
        return WorkflowContextResponse(context=get_workflow(context_id))
    except WorkflowNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/workflows/{context_id}/execute",
    response_model=ExecuteWorkflowResponse,
)
def execute_workflow(
    context_id: str,
    request: ExecuteWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.EXECUTE_WORKFLOW))],
) -> ExecuteWorkflowResponse:
    try:
        context = execute_approved_workflow(
            context_id=context_id,
            run_by=request.run_by,
        )
    except WorkflowNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkflowConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
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
    try:
        context = decide_workflow_approval_service(
            context_id=context_id,
            decision=request.decision,
            reviewed_by=request.reviewed_by,
            comment=request.comment,
        )
    except WorkflowNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkflowBadRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except WorkflowConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ApprovalDecisionResponse(context=context)


@router.get(
    "/automation/files/{ticket_id}/{file_name}",
    response_model=AutomationFile,
)
def read_automation_file(
    ticket_id: str,
    file_name: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
) -> AutomationFile:
    try:
        return read_automation_file_service(ticket_id=ticket_id, file_name=file_name)
    except WorkflowBadRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except WorkflowNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
