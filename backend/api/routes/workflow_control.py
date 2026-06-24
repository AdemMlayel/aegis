from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.routes.workflows import (
    IntelligenceConfigRequest,
    build_intelligence_config,
)
from backend.graph.state import TestContext, TicketData, WorkflowStageName
from backend.security import Capability, Principal, require_capability
from backend.services.workflow_control import (
    WorkflowControlBadRequest,
    WorkflowControlConflict,
    WorkflowSessionNotFound,
    append_workflow_message,
    create_workflow_session,
    edit_robot_artifact,
    get_artifact_revisions,
    get_workflow_timeline,
    pause_workflow_session,
    regenerate_workflow_stage,
    resume_workflow_session,
    review_workflow_stage,
)
from backend.storage.artifact_revisions import ArtifactRevision
from backend.storage.workflow_events import WorkflowEvent


router = APIRouter(tags=["workflow-control"])


class CreateWorkflowSessionRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket: TicketData | None = None
    intelligence: IntelligenceConfigRequest | None = None
    mode: Literal[
        "autonomous",
        "approval_required",
        "step_by_step",
    ] = "approval_required"


class WorkflowControlActionRequest(BaseModel):
    actor: str = Field(default="local-user", min_length=1)


class StageReviewRequest(BaseModel):
    decision: Literal["approve", "request_changes"]
    reviewed_by: str = Field(min_length=1)
    comment: str | None = None


class StageRegenerationRequest(BaseModel):
    actor: str = Field(min_length=1)
    comment: str = Field(min_length=1)


class EditArtifactRequest(BaseModel):
    actor: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=500_000)
    comment: str | None = None


class WorkflowMessageRequest(BaseModel):
    actor: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=10_000)


class WorkflowMessageResponse(BaseModel):
    event: WorkflowEvent


class WorkflowControlResponse(BaseModel):
    context: TestContext


class WorkflowTimelineResponse(BaseModel):
    events: list[WorkflowEvent]
    next_sequence: int


class ArtifactRevisionResponse(BaseModel):
    context: TestContext
    revision: ArtifactRevision


class ArtifactRevisionListResponse(BaseModel):
    revisions: list[ArtifactRevision]


@router.post(
    "/workflows/sessions",
    response_model=WorkflowControlResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    request: CreateWorkflowSessionRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.START_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    context = create_workflow_session(
        created_by=request.created_by,
        ticket=request.ticket,
        intelligence_config=build_intelligence_config(request.intelligence),
        mode=request.mode,
    )
    return WorkflowControlResponse(context=context)


@router.post(
    "/workflows/{context_id}/resume",
    response_model=WorkflowControlResponse,
)
def resume_session(
    context_id: str,
    request: WorkflowControlActionRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.START_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    return WorkflowControlResponse(
        context=_translate_control_errors(
            lambda: resume_workflow_session(
                context_id=context_id,
                actor=request.actor,
            )
        )
    )


@router.post(
    "/workflows/{context_id}/next",
    response_model=WorkflowControlResponse,
)
def run_next_stage(
    context_id: str,
    request: WorkflowControlActionRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.START_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    return WorkflowControlResponse(
        context=_translate_control_errors(
            lambda: resume_workflow_session(
                context_id=context_id,
                actor=request.actor,
                single_step=True,
            )
        )
    )


@router.post(
    "/workflows/{context_id}/pause",
    response_model=WorkflowControlResponse,
)
def pause_session(
    context_id: str,
    request: WorkflowControlActionRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.START_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    return WorkflowControlResponse(
        context=_translate_control_errors(
            lambda: pause_workflow_session(
                context_id=context_id,
                actor=request.actor,
            )
        )
    )


@router.post(
    "/workflows/{context_id}/stages/{stage}/review",
    response_model=WorkflowControlResponse,
)
def review_stage(
    context_id: str,
    stage: WorkflowStageName,
    request: StageReviewRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.APPROVE_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    return WorkflowControlResponse(
        context=_translate_control_errors(
            lambda: review_workflow_stage(
                context_id=context_id,
                stage=stage,
                decision=request.decision,
                reviewed_by=request.reviewed_by,
                comment=request.comment,
            )
        )
    )


@router.post(
    "/workflows/{context_id}/stages/{stage}/regenerate",
    response_model=WorkflowControlResponse,
)
def regenerate_stage(
    context_id: str,
    stage: WorkflowStageName,
    request: StageRegenerationRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.APPROVE_WORKFLOW)),
    ],
) -> WorkflowControlResponse:
    return WorkflowControlResponse(
        context=_translate_control_errors(
            lambda: regenerate_workflow_stage(
                context_id=context_id,
                stage=stage,
                actor=request.actor,
                comment=request.comment,
            )
        )
    )


@router.get(
    "/workflows/{context_id}/timeline",
    response_model=WorkflowTimelineResponse,
)
def read_timeline(
    context_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_WORKFLOW)),
    ],
    after_sequence: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
) -> WorkflowTimelineResponse:
    events = _translate_control_errors(
        lambda: get_workflow_timeline(
            context_id=context_id,
            after_sequence=after_sequence,
            limit=limit,
        )
    )
    return WorkflowTimelineResponse(
        events=events,
        next_sequence=events[-1].sequence if events else after_sequence,
    )


@router.post(
    "/workflows/{context_id}/timeline/messages",
    response_model=WorkflowMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_timeline_message(
    context_id: str,
    request: WorkflowMessageRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.START_WORKFLOW)),
    ],
) -> WorkflowMessageResponse:
    return WorkflowMessageResponse(
        event=_translate_control_errors(
            lambda: append_workflow_message(
                context_id=context_id,
                actor=request.actor,
                message=request.message,
            )
        )
    )


@router.put(
    "/workflows/{context_id}/artifacts/{test_case_id}",
    response_model=ArtifactRevisionResponse,
)
def update_robot_artifact(
    context_id: str,
    test_case_id: str,
    request: EditArtifactRequest,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.EDIT_ARTIFACTS)),
    ],
) -> ArtifactRevisionResponse:
    context, revision = _translate_control_errors(
        lambda: edit_robot_artifact(
            context_id=context_id,
            test_case_id=test_case_id,
            actor=request.actor,
            content=request.content,
            comment=request.comment,
        )
    )
    return ArtifactRevisionResponse(context=context, revision=revision)


@router.get(
    "/workflows/{context_id}/artifacts/{test_case_id}/revisions",
    response_model=ArtifactRevisionListResponse,
)
def read_artifact_revisions(
    context_id: str,
    test_case_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_ARTIFACTS)),
    ],
) -> ArtifactRevisionListResponse:
    return ArtifactRevisionListResponse(
        revisions=_translate_control_errors(
            lambda: get_artifact_revisions(
                context_id=context_id,
                test_case_id=test_case_id,
            )
        )
    )


def _translate_control_errors(action):
    try:
        return action()
    except WorkflowSessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkflowControlBadRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except WorkflowControlConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
