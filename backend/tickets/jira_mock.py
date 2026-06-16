from __future__ import annotations

from backend.graph.state import TicketData, TicketSource
from backend.storage.mock_tickets import get_mock_ticket, list_mock_tickets
from backend.tickets.base import BaseTicketConnector, ticket_connector_registry


@ticket_connector_registry.register(
    name="jira_mock",
    source="jira",
    description="Jira-shaped local connector backed by the mock ticket store.",
    requires_external_api=False,
)
class MockJiraTicketConnector(BaseTicketConnector):
    """Local Jira connector boundary with zero company API dependency."""

    def fetch(self, ticket_id: str) -> TicketData | None:
        ticket = get_mock_ticket(ticket_id)
        if ticket is None:
            return None
        return _as_jira_ticket(ticket)

    def search(self, query: str | None = None) -> list[TicketData]:
        return [_as_jira_ticket(ticket) for ticket in list_mock_tickets(query=query)]


def _as_jira_ticket(ticket: TicketData) -> TicketData:
    return TicketData(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        acceptance_criteria=ticket.acceptance_criteria,
        priority=ticket.priority,
        labels=[*ticket.labels, "jira-mock"],
        assignee=ticket.assignee,
        source=TicketSource.JIRA,
        raw_url=ticket.raw_url or f"mock://jira/{ticket.id}",
    )
