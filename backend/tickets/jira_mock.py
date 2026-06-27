from __future__ import annotations

from backend.graph.state import TicketData, TicketSource
from backend.tickets.base import BaseTicketConnector, ticket_connector_registry
from backend.tickets.sources import DemoTicketSource


@ticket_connector_registry.register(
    name="jira_mock",
    source="jira",
    description="Jira-shaped local connector backed by the mock ticket store.",
    requires_external_api=False,
)
class MockJiraTicketConnector(BaseTicketConnector):
    """Local Jira connector boundary with zero company API dependency."""

    def fetch(self, ticket_id: str) -> TicketData | None:
        ticket = DemoTicketSource().fetch(ticket_id)
        if ticket is None:
            return None
        return _as_jira_ticket(ticket)

    def search(self, query: str | None = None) -> list[TicketData]:
        return [_as_jira_ticket(ticket) for ticket in DemoTicketSource().list(query=query)]


def _as_jira_ticket(ticket: TicketData) -> TicketData:
    return TicketData(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        business_objective=ticket.business_objective,
        test_objective=ticket.test_objective,
        system_under_test=ticket.system_under_test,
        feature_or_service_name=ticket.feature_or_service_name,
        test_scope=ticket.test_scope,
        out_of_scope=ticket.out_of_scope,
        preconditions=ticket.preconditions,
        assumptions=ticket.assumptions,
        environment=ticket.environment,
        interfaces_involved=ticket.interfaces_involved,
        input_data=ticket.input_data,
        expected_outputs=ticket.expected_outputs,
        validation_rules=ticket.validation_rules,
        test_steps=ticket.test_steps,
        acceptance_criteria=ticket.acceptance_criteria,
        risks_or_constraints=ticket.risks_or_constraints,
        dependencies=ticket.dependencies,
        required_tools=ticket.required_tools,
        priority=ticket.priority,
        status=ticket.status,
        created_date=ticket.created_date,
        last_updated_date=ticket.last_updated_date,
        labels=[*ticket.labels, "jira-mock"],
        assignee=ticket.assignee,
        source=TicketSource.JIRA,
        raw_url=f"mock://jira/{ticket.id}",
        technical=ticket.technical,
    )
