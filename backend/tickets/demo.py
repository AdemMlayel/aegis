from __future__ import annotations

from backend.graph.state import TicketData
from backend.tickets.base import BaseTicketConnector, ticket_connector_registry
from backend.tickets.sources import DemoTicketSource


@ticket_connector_registry.register(
    name="demo",
    source="demo",
    description="Structured local demo ticket source backed by sanitized LLD-like tickets.",
    requires_external_api=False,
)
class DemoTicketConnector(BaseTicketConnector):
    """Connector facade for the structured local demo ticket source."""

    def fetch(self, ticket_id: str) -> TicketData | None:
        return DemoTicketSource().fetch(ticket_id)

    def search(self, query: str | None = None) -> list[TicketData]:
        return [record for record in DemoTicketSource().list(query=query)]
