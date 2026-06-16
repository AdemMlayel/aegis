from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from backend.api.routes.workflows import (
    StartWorkflowResponse,
    run_and_persist_workflow_start,
)
from backend.graph.state import TestContext, TicketData
from backend.storage.mock_tickets import (
    MockTicketRecord,
    MockTicketStatus,
    MockTicketUpdate,
    NewMockTicketComment,
    add_mock_ticket_comment,
    create_mock_ticket,
    delete_mock_ticket,
    get_mock_ticket,
    get_mock_ticket_record,
    list_mock_tickets,
    update_mock_ticket,
)


router = APIRouter(tags=["tickets"])
TicketPriority = Literal["low", "medium", "high", "critical"]


class MockTicketsResponse(BaseModel):
    tickets: list[MockTicketRecord]


class MockTicketResponse(BaseModel):
    ticket: MockTicketRecord


class StartMockTicketWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket_id: str = Field(min_length=1)


@router.get("/tickets/mock", response_model=MockTicketsResponse)
def read_mock_tickets(
    q: str | None = Query(default=None, min_length=1),
    priority: TicketPriority | None = None,
    status: MockTicketStatus | None = None,
    assignee: str | None = Query(default=None, min_length=1),
    label: str | None = Query(default=None, min_length=1),
) -> MockTicketsResponse:
    return MockTicketsResponse(
        tickets=list_mock_tickets(
            query=q,
            priority=priority,
            status=status,
            assignee=assignee,
            label=label,
        )
    )


@router.get("/tickets/mock/{ticket_id}", response_model=MockTicketResponse)
def read_mock_ticket(ticket_id: str) -> MockTicketResponse:
    ticket = get_mock_ticket_record(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return MockTicketResponse(ticket=ticket)


@router.post(
    "/tickets/mock",
    response_model=MockTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mock_ticket_endpoint(ticket: MockTicketRecord) -> MockTicketResponse:
    try:
        created = create_mock_ticket(ticket)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return MockTicketResponse(ticket=created)


@router.patch("/tickets/mock/{ticket_id}", response_model=MockTicketResponse)
def update_mock_ticket_endpoint(
    ticket_id: str,
    update: MockTicketUpdate,
) -> MockTicketResponse:
    ticket = update_mock_ticket(ticket_id, update)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return MockTicketResponse(ticket=ticket)


@router.post(
    "/tickets/mock/{ticket_id}/comments",
    response_model=MockTicketResponse,
)
def add_mock_ticket_comment_endpoint(
    ticket_id: str,
    comment: NewMockTicketComment,
) -> MockTicketResponse:
    ticket = add_mock_ticket_comment(ticket_id, comment)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return MockTicketResponse(ticket=ticket)


@router.delete(
    "/tickets/mock/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mock_ticket_endpoint(ticket_id: str) -> Response:
    deleted = delete_mock_ticket(ticket_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/workflows/start-from-mock-ticket",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow_from_mock_ticket(
    request: StartMockTicketWorkflowRequest,
) -> StartWorkflowResponse:
    ticket = get_mock_ticket(request.ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    context: TestContext = run_and_persist_workflow_start(
        created_by=request.created_by,
        ticket=ticket,
    )
    return StartWorkflowResponse(context=context)
