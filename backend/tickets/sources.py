from __future__ import annotations

from abc import ABC, abstractmethod

from backend.graph.state import TicketData
from backend.storage.mock_tickets import (
    MockTicketStatus,
    TicketPriority,
    get_mock_ticket,
    get_mock_ticket_record,
    list_mock_tickets,
)
from backend.tickets.schema import StructuredTicketRecord


class TicketSource(ABC):
    """Boundary for ticket retrieval.

    The dashboard and workflow should depend on this interface instead of the
    current local demo storage. A future API-backed source can replace the demo
    source without changing the UI workflow.
    """

    @abstractmethod
    def list(
        self,
        *,
        query: str | None = None,
        priority: TicketPriority | None = None,
        status: MockTicketStatus | None = None,
        assignee: str | None = None,
        label: str | None = None,
    ) -> list[StructuredTicketRecord]:
        raise NotImplementedError

    @abstractmethod
    def fetch_record(self, ticket_id: str) -> StructuredTicketRecord | None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, ticket_id: str) -> TicketData | None:
        raise NotImplementedError


class DemoTicketSource(TicketSource):
    def list(
        self,
        *,
        query: str | None = None,
        priority: TicketPriority | None = None,
        status: MockTicketStatus | None = None,
        assignee: str | None = None,
        label: str | None = None,
    ) -> list[StructuredTicketRecord]:
        return list_mock_tickets(
            query=query,
            priority=priority,
            status=status,
            assignee=assignee,
            label=label,
        )

    def fetch_record(self, ticket_id: str) -> StructuredTicketRecord | None:
        return get_mock_ticket_record(ticket_id)

    def fetch(self, ticket_id: str) -> TicketData | None:
        return get_mock_ticket(ticket_id)


class ApiTicketSource(TicketSource):
    def list(
        self,
        *,
        query: str | None = None,
        priority: TicketPriority | None = None,
        status: MockTicketStatus | None = None,
        assignee: str | None = None,
        label: str | None = None,
    ) -> list[StructuredTicketRecord]:
        raise NotImplementedError("API ticket source is not configured in local demo mode")

    def fetch_record(self, ticket_id: str) -> StructuredTicketRecord | None:
        raise NotImplementedError("API ticket source is not configured in local demo mode")

    def fetch(self, ticket_id: str) -> TicketData | None:
        raise NotImplementedError("API ticket source is not configured in local demo mode")


def get_ticket_source() -> TicketSource:
    return DemoTicketSource()
