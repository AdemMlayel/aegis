from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from backend.graph.artifacts import PROJECT_ROOT
from backend.graph.state import TicketData


MOCK_TICKETS_PATH = PROJECT_ROOT / "backend" / "mock_data" / "tickets.json"
TicketPriority = Literal["low", "medium", "high", "critical"]


@lru_cache(maxsize=1)
def _load_mock_tickets() -> tuple[TicketData, ...]:
    payload = json.loads(MOCK_TICKETS_PATH.read_text(encoding="utf-8"))
    tickets = [TicketData.model_validate(item) for item in payload]
    return tuple(sorted(tickets, key=lambda ticket: ticket.id))


def list_mock_tickets(
    *, query: str | None = None, priority: TicketPriority | None = None
) -> list[TicketData]:
    tickets = list(_load_mock_tickets())
    if priority:
        tickets = [ticket for ticket in tickets if ticket.priority == priority]
    if query:
        needle = query.casefold()
        tickets = [
            ticket
            for ticket in tickets
            if needle in _search_blob(ticket)
        ]
    return tickets


def get_mock_ticket(ticket_id: str) -> TicketData | None:
    normalized_id = ticket_id.casefold()
    return next(
        (
            ticket
            for ticket in _load_mock_tickets()
            if ticket.id.casefold() == normalized_id
        ),
        None,
    )


def _search_blob(ticket: TicketData) -> str:
    return " ".join(
        [
            ticket.id,
            ticket.title,
            ticket.description,
            " ".join(ticket.acceptance_criteria),
            " ".join(ticket.labels),
            ticket.assignee or "",
        ]
    ).casefold()
