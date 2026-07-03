from __future__ import annotations

import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
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
from backend.storage.workflow_events import WorkflowEvent, list_workflow_events


router = APIRouter(tags=["workflow-control"])

# G2 (Part B2): live trace streaming bounds. The gateway middleware wraps every
# request in a timeout, and tunnels/proxies kill idle long-lived connections, so
# each SSE response is intentionally short-lived: it streams new events for at
# most _STREAM_MAX_SECONDS, polling the same event store the poll endpoint uses,
# then closes cleanly. The browser's EventSource auto-reconnects and resumes from
# the last sequence (via the standard Last-Event-ID header), so the user sees one
# continuous live ticker. A terminal control event closes the stream early.
_STREAM_MAX_SECONDS = 25.0
_STREAM_POLL_INTERVAL = 1.0
_STREAM_TERMINAL_STATUSES = frozenset({"completed", "failed"})


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


def _sse_pack(event: WorkflowEvent) -> str:
    """Serialize one workflow event as an SSE record.

    The ``id:`` field carries the sequence so the browser sends it back as
    Last-Event-ID on reconnect, letting the stream resume exactly where it left
    off with no gaps or duplicates.
    """
    return (
        f"id: {event.sequence}\n"
        f"event: workflow_event\n"
        f"data: {event.model_dump_json()}\n\n"
    )


async def _workflow_event_stream(context_id: str, request: Request, after_sequence: int):
    cursor = after_sequence
    # Tell the client how long to wait before reconnecting after we close.
    yield "retry: 1500\n\n"
    loop = asyncio.get_event_loop()
    deadline = loop.time() + _STREAM_MAX_SECONDS
    while True:
        if await request.is_disconnected():
            return
        # Same data source as the poll endpoint; run the sync DB read in a
        # thread so we never block the event loop.
        events = await asyncio.to_thread(
            list_workflow_events, context_id=context_id, after_sequence=cursor
        )
        for event in events:
            cursor = event.sequence
            yield _sse_pack(event)
            if event.kind == "control" and event.status in _STREAM_TERMINAL_STATUSES:
                # Workflow reached a terminal state -- close the stream cleanly;
                # the client stops reconnecting once it sees this status.
                yield "event: stream_end\ndata: {}\n\n"
                return
        if loop.time() >= deadline:
            # Bounded lifetime: close so we stay under the gateway timeout and
            # don't hold a tunnel connection open. EventSource reconnects with
            # Last-Event-ID and resumes from `cursor`.
            yield "event: stream_idle\ndata: {}\n\n"
            return
        # Heartbeat comment keeps intermediaries from idling the connection out.
        yield ": keep-alive\n\n"
        await asyncio.sleep(_STREAM_POLL_INTERVAL)


@router.get("/workflows/{context_id}/timeline/stream")
async def stream_timeline(
    context_id: str,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_WORKFLOW)),
    ],
    after_sequence: int = Query(default=0, ge=0),
) -> StreamingResponse:
    """Server-Sent Events stream of workflow trace events (G2 / Part B2).

    A strict enhancement over ``/timeline``: it reads the same event store but
    pushes new events live so the chat shows a real-time execution ticker
    instead of waiting for the next poll. The ``after_sequence`` query param (or
    the ``Last-Event-ID`` header the browser sends on reconnect) resumes the
    stream without gaps. The poll endpoint remains as a fallback for clients
    without EventSource.
    """
    # On reconnect the browser sends the last sequence it saw; prefer it so we
    # never replay or drop events across a reconnect.
    last_event_id = request.headers.get("Last-Event-ID")
    if last_event_id and last_event_id.isdigit():
        after_sequence = int(last_event_id)
    return StreamingResponse(
        _workflow_event_stream(context_id, request, after_sequence),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
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
