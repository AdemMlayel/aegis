from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.api.routes.workflows import (
    IntelligenceConfigRequest,
    StartWorkflowResponse,
    run_and_persist_workflow_start,
)
from backend.graph.state import TestContext, TicketData
from backend.security import Capability, Principal, require_capability
from backend.tickets import get_ticket_source, ticket_connector_registry
from backend.storage.mock_tickets import (
    MockTicketRecord,
    MockTicketStatus,
    MockTicketUpdate,
    NewMockTicketComment,
    add_mock_ticket_comment,
    create_mock_ticket,
    delete_mock_ticket,
    update_mock_ticket,
)


router = APIRouter(tags=["tickets"])
TicketPriority = Literal["low", "medium", "high", "critical"]


class MockTicketsResponse(BaseModel):
    tickets: list[MockTicketRecord]


class MockTicketResponse(BaseModel):
    ticket: MockTicketRecord


class DemoTicketsResponse(BaseModel):
    tickets: list[MockTicketRecord]


class DemoTicketResponse(BaseModel):
    ticket: MockTicketRecord




class TicketConnectorSpecsResponse(BaseModel):
    connectors: list[dict[str, object]]


class JiraMockTicketsResponse(BaseModel):
    tickets: list[TicketData]


class JiraMockTicketResponse(BaseModel):
    ticket: TicketData


class TicketConnectorHealthResponse(BaseModel):
    connector: str
    health: dict[str, object]


class StartConnectorTicketWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket_id: str = Field(min_length=1)
    connector: str = Field(default_factory=lambda: settings.default_ticket_connector, min_length=1)
    intelligence: IntelligenceConfigRequest | None = None


class StartMockTicketWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket_id: str = Field(min_length=1)
    intelligence: IntelligenceConfigRequest | None = None


class StartDemoTicketWorkflowRequest(BaseModel):
    created_by: str = Field(default="local-user", min_length=1)
    ticket_id: str = Field(min_length=1)
    intelligence: IntelligenceConfigRequest | None = None




@router.get("/tickets/connectors", response_model=TicketConnectorSpecsResponse)
def read_ticket_connectors(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
) -> TicketConnectorSpecsResponse:
    return TicketConnectorSpecsResponse(
        connectors=[spec.__dict__ for spec in ticket_connector_registry.list_specs()]
    )


@router.get("/tickets/connectors/{connector_name}/health", response_model=TicketConnectorHealthResponse)
def read_ticket_connector_health(
    connector_name: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
) -> TicketConnectorHealthResponse:
    if not ticket_connector_registry.has(connector_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket connector '{connector_name}' is not registered",
        )
    connector = ticket_connector_registry.create(connector_name)
    return TicketConnectorHealthResponse(
        connector=connector_name,
        health=connector.health().__dict__,
    )


@router.get("/tickets/connectors/{connector_name}/tickets", response_model=JiraMockTicketsResponse)
def read_connector_tickets(
    connector_name: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
    q: str | None = Query(default=None, min_length=1),
) -> JiraMockTicketsResponse:
    if not ticket_connector_registry.has(connector_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket connector '{connector_name}' is not registered",
        )
    connector = ticket_connector_registry.create(connector_name)
    if connector.spec.requires_external_api and not settings.external_connectors_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External ticket connectors are disabled in local architecture mode",
        )
    return JiraMockTicketsResponse(tickets=connector.search(q))


@router.get("/tickets/jira/mock", response_model=JiraMockTicketsResponse)
def read_jira_mock_tickets(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
    q: str | None = Query(default=None, min_length=1),
) -> JiraMockTicketsResponse:
    connector = ticket_connector_registry.create("jira_mock")
    return JiraMockTicketsResponse(tickets=connector.search(q))


@router.get("/tickets/jira/mock/{ticket_id}", response_model=JiraMockTicketResponse)
def read_jira_mock_ticket(
    ticket_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
) -> JiraMockTicketResponse:
    connector = ticket_connector_registry.create("jira_mock")
    ticket = connector.fetch(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock Jira ticket was not found",
        )
    return JiraMockTicketResponse(ticket=ticket)

@router.get("/tickets/mock", response_model=MockTicketsResponse)
def read_mock_tickets(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
    q: str | None = Query(default=None, min_length=1),
    priority: TicketPriority | None = None,
    status: MockTicketStatus | None = None,
    assignee: str | None = Query(default=None, min_length=1),
    label: str | None = Query(default=None, min_length=1),
) -> MockTicketsResponse:
    return MockTicketsResponse(
        tickets=get_ticket_source().list(
            query=q,
            priority=priority,
            status=status,
            assignee=assignee,
            label=label,
        )
    )


@router.get("/tickets/demo", response_model=DemoTicketsResponse)
def read_demo_tickets(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
    q: str | None = Query(default=None, min_length=1),
    priority: TicketPriority | None = None,
    status: MockTicketStatus | None = None,
    assignee: str | None = Query(default=None, min_length=1),
    label: str | None = Query(default=None, min_length=1),
) -> DemoTicketsResponse:
    return DemoTicketsResponse(
        tickets=get_ticket_source().list(
            query=q,
            priority=priority,
            status=status,
            assignee=assignee,
            label=label,
        )
    )


@router.get("/tickets/mock/{ticket_id}", response_model=MockTicketResponse)
def read_mock_ticket(
    ticket_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
) -> MockTicketResponse:
    ticket = get_ticket_source().fetch_record(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return MockTicketResponse(ticket=ticket)


@router.get("/tickets/demo/{ticket_id}", response_model=DemoTicketResponse)
def read_demo_ticket(
    ticket_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_TICKETS))],
) -> DemoTicketResponse:
    ticket = get_ticket_source().fetch_record(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo ticket was not found",
        )
    return DemoTicketResponse(ticket=ticket)


@router.post(
    "/tickets/mock",
    response_model=MockTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mock_ticket_endpoint(
    ticket: MockTicketRecord,
    principal: Annotated[Principal, Depends(require_capability(Capability.WRITE_TICKETS))],
) -> MockTicketResponse:
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
    principal: Annotated[Principal, Depends(require_capability(Capability.WRITE_TICKETS))],
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
    principal: Annotated[Principal, Depends(require_capability(Capability.WRITE_TICKETS))],
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
def delete_mock_ticket_endpoint(
    ticket_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.WRITE_TICKETS))],
) -> Response:
    deleted = delete_mock_ticket(ticket_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/workflows/start-from-ticket-connector",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow_from_ticket_connector(
    request: StartConnectorTicketWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.START_WORKFLOW))],
) -> StartWorkflowResponse:
    if not ticket_connector_registry.has(request.connector):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket connector '{request.connector}' is not registered",
        )
    connector = ticket_connector_registry.create(request.connector)
    if connector.spec.requires_external_api and not settings.external_connectors_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External ticket connectors are disabled in local architecture mode",
        )
    ticket = connector.fetch(request.ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector ticket was not found",
        )
    context: TestContext = run_and_persist_workflow_start(
        created_by=request.created_by,
        ticket=ticket,
        intelligence=request.intelligence,
    )
    return StartWorkflowResponse(context=context)


@router.post(
    "/workflows/start-from-mock-ticket",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow_from_mock_ticket(
    request: StartMockTicketWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.START_WORKFLOW))],
) -> StartWorkflowResponse:
    ticket = get_ticket_source().fetch(request.ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock ticket was not found",
        )
    context: TestContext = run_and_persist_workflow_start(
        created_by=request.created_by,
        ticket=ticket,
        intelligence=request.intelligence,
    )
    return StartWorkflowResponse(context=context)


@router.post(
    "/workflows/start-from-demo-ticket",
    response_model=StartWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_workflow_from_demo_ticket(
    request: StartDemoTicketWorkflowRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.START_WORKFLOW))],
) -> StartWorkflowResponse:
    ticket = get_ticket_source().fetch(request.ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo ticket was not found",
        )
    context: TestContext = run_and_persist_workflow_start(
        created_by=request.created_by,
        ticket=ticket,
        intelligence=request.intelligence,
    )
    return StartWorkflowResponse(context=context)
