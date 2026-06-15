from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.routes.workflows import (
    StartWorkflowResponse,
    run_and_persist_workflow_start,
)
from backend.graph.state import TestContext, TicketData
from backend.storage.mock_tickets import get_mock_ticket, list_mock_tickets


router = APIRouter(tags=["tickets"])
TicketPriority = Literal["low", "medium", "high", "critical"]


class MockTicketsResponse(BaseModel):
    tickets: list[TicketData]


class MockTicketResponse(BaseModel):
    ticket: TicketData


class StartMockTicketWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket_id: str = Field(min_length=1)


@router.get("/tickets/mock", response_model=MockTicketsResponse)
def read_mock_tickets(
    q: str | None = Query(default=None, min_length=1),
    priority: TicketPriority | None = None,
) -> MockTicketsResponse:
    return MockTicketsResponse(tickets=list_mock_tickets(query=q, priority=priority))


@router.get("/tickets/mock/{ticket_id}", response_model=MockTicketResponse)
def read_mock_ticket(ticket_id: str) -> MockTicketResponse:
    ticket = get_mock_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return MockTicketResponse(ticket=ticket)


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
