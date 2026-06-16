from __future__ import annotations

import json
import sqlite3
from typing import Any, Literal

from pydantic import Field

from backend.graph.artifacts import PROJECT_ROOT
from backend.graph.state import StrictModel, TicketData, utc_now
from backend.storage.database import connect, initialize_database


MOCK_TICKETS_PATH = PROJECT_ROOT / "backend" / "mock_data" / "tickets.json"
TicketPriority = Literal["low", "medium", "high", "critical"]
MockTicketStatus = Literal["backlog", "ready", "in_progress", "blocked", "done"]
RequirementStatus = Literal["draft", "approved", "needs_clarification"]


def _now_iso() -> str:
    return utc_now().isoformat()


class MockTicketComment(StrictModel):
    author: str
    body: str
    created_at: str = Field(default_factory=_now_iso)


class MockLinkedRequirement(StrictModel):
    id: str
    title: str
    status: RequirementStatus = "draft"
    source: str = "mock"


class MockTicketRecord(TicketData):
    status: MockTicketStatus = "ready"
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)
    comments: list[MockTicketComment] = Field(default_factory=list)
    linked_requirements: list[MockLinkedRequirement] = Field(default_factory=list)


class MockTicketUpdate(StrictModel):
    title: str | None = None
    description: str | None = None
    acceptance_criteria: list[str] | None = None
    priority: TicketPriority | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    status: MockTicketStatus | None = None
    raw_url: str | None = None
    comments: list[MockTicketComment] | None = None
    linked_requirements: list[MockLinkedRequirement] | None = None


class NewMockTicketComment(StrictModel):
    author: str
    body: str


_seed_imported = False


def _record_from_seed(item: dict[str, Any]) -> MockTicketRecord:
    now = _now_iso()
    payload = {
        "status": "ready",
        "created_at": now,
        "updated_at": now,
        "comments": [],
        "linked_requirements": [],
        **item,
    }
    return MockTicketRecord.model_validate(payload)


def _record_to_ticket(record: MockTicketRecord) -> TicketData:
    return TicketData(
        id=record.id,
        title=record.title,
        description=record.description,
        acceptance_criteria=record.acceptance_criteria,
        priority=record.priority,
        labels=record.labels,
        assignee=record.assignee,
        source=record.source,
        raw_url=record.raw_url,
    )


def _search_blob(record: MockTicketRecord) -> str:
    return " ".join(
        [
            record.id,
            record.title,
            record.description,
            record.status,
            record.priority,
            " ".join(record.acceptance_criteria),
            " ".join(record.labels),
            record.assignee or "",
            " ".join(comment.body for comment in record.comments),
            " ".join(requirement.id for requirement in record.linked_requirements),
            " ".join(requirement.title for requirement in record.linked_requirements),
        ]
    ).casefold()


def _row_values(record: MockTicketRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "payload_json": record.model_dump_json(),
        "title": record.title,
        "description": record.description,
        "priority": record.priority,
        "status": record.status,
        "assignee": record.assignee,
        "labels_json": json.dumps(record.labels),
        "source": str(record.source),
        "raw_url": record.raw_url,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "search_blob": _search_blob(record),
    }


def _save_record(
    connection: sqlite3.Connection,
    record: MockTicketRecord,
) -> None:
    connection.execute(
        """
        INSERT INTO mock_tickets (
            id,
            payload_json,
            title,
            description,
            priority,
            status,
            assignee,
            labels_json,
            source,
            raw_url,
            created_at,
            updated_at,
            search_blob
        )
        VALUES (
            :id,
            :payload_json,
            :title,
            :description,
            :priority,
            :status,
            :assignee,
            :labels_json,
            :source,
            :raw_url,
            :created_at,
            :updated_at,
            :search_blob
        )
        ON CONFLICT(id) DO UPDATE SET
            payload_json = excluded.payload_json,
            title = excluded.title,
            description = excluded.description,
            priority = excluded.priority,
            status = excluded.status,
            assignee = excluded.assignee,
            labels_json = excluded.labels_json,
            source = excluded.source,
            raw_url = excluded.raw_url,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at,
            search_blob = excluded.search_blob
        """,
        _row_values(record),
    )


def seed_mock_tickets() -> None:
    global _seed_imported
    if _seed_imported:
        return

    initialize_database()
    with connect() as connection:
        existing = connection.execute("SELECT COUNT(*) FROM mock_tickets").fetchone()
        if existing and existing[0] > 0:
            _seed_imported = True
            return

        payload = json.loads(MOCK_TICKETS_PATH.read_text(encoding="utf-8"))
        for item in payload:
            _save_record(connection, _record_from_seed(item))

    _seed_imported = True


def _record_from_row(row: sqlite3.Row) -> MockTicketRecord:
    return MockTicketRecord.model_validate_json(row["payload_json"])


def _all_records() -> list[MockTicketRecord]:
    seed_mock_tickets()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM mock_tickets
            ORDER BY id
            """
        ).fetchall()
    return [MockTicketRecord.model_validate_json(row["payload_json"]) for row in rows]


def list_mock_tickets(
    *,
    query: str | None = None,
    priority: TicketPriority | None = None,
    status: MockTicketStatus | None = None,
    assignee: str | None = None,
    label: str | None = None,
) -> list[MockTicketRecord]:
    tickets = _all_records()
    if priority:
        tickets = [ticket for ticket in tickets if ticket.priority == priority]
    if status:
        tickets = [ticket for ticket in tickets if ticket.status == status]
    if assignee:
        normalized_assignee = assignee.casefold()
        tickets = [
            ticket
            for ticket in tickets
            if ticket.assignee and ticket.assignee.casefold() == normalized_assignee
        ]
    if label:
        normalized_label = label.casefold()
        tickets = [
            ticket
            for ticket in tickets
            if normalized_label in {item.casefold() for item in ticket.labels}
        ]
    if query:
        needle = query.casefold()
        tickets = [
            ticket
            for ticket in tickets
            if needle in _search_blob(ticket)
        ]
    return tickets


def get_mock_ticket(ticket_id: str) -> TicketData | None:
    record = get_mock_ticket_record(ticket_id)
    return _record_to_ticket(record) if record else None


def get_mock_ticket_record(ticket_id: str) -> MockTicketRecord | None:
    seed_mock_tickets()
    normalized_id = ticket_id.casefold()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT payload_json
            FROM mock_tickets
            WHERE lower(id) = ?
            """,
            (normalized_id,),
        ).fetchone()
    return _record_from_row(row) if row else None


def create_mock_ticket(record: MockTicketRecord) -> MockTicketRecord:
    seed_mock_tickets()
    if get_mock_ticket_record(record.id) is not None:
        raise ValueError(f"Mock ticket '{record.id}' already exists")

    now = _now_iso()
    persisted = record.model_copy(update={"created_at": now, "updated_at": now})
    with connect() as connection:
        _save_record(connection, persisted)
    return persisted


def update_mock_ticket(
    ticket_id: str,
    update: MockTicketUpdate,
) -> MockTicketRecord | None:
    record = get_mock_ticket_record(ticket_id)
    if record is None:
        return None

    changes = update.model_dump(exclude_unset=True)
    nullable_fields = {"assignee", "raw_url"}
    changes = {
        key: value
        for key, value in changes.items()
        if value is not None or key in nullable_fields
    }
    if "comments" in changes and changes["comments"] is not None:
        changes["comments"] = [
            MockTicketComment.model_validate(comment)
            for comment in changes["comments"]
        ]
    if "linked_requirements" in changes and changes["linked_requirements"] is not None:
        changes["linked_requirements"] = [
            MockLinkedRequirement.model_validate(requirement)
            for requirement in changes["linked_requirements"]
        ]
    changes["updated_at"] = _now_iso()
    updated = record.model_copy(update=changes)
    with connect() as connection:
        _save_record(connection, updated)
    return updated


def add_mock_ticket_comment(
    ticket_id: str,
    comment: NewMockTicketComment,
) -> MockTicketRecord | None:
    record = get_mock_ticket_record(ticket_id)
    if record is None:
        return None

    comments = [
        *record.comments,
        MockTicketComment(
            author=comment.author,
            body=comment.body,
            created_at=_now_iso(),
        ),
    ]
    updated = record.model_copy(
        update={"comments": comments, "updated_at": _now_iso()}
    )
    with connect() as connection:
        _save_record(connection, updated)
    return updated


def delete_mock_ticket(ticket_id: str) -> bool:
    seed_mock_tickets()
    with connect() as connection:
        result = connection.execute(
            "DELETE FROM mock_tickets WHERE lower(id) = ?",
            (ticket_id.casefold(),),
        )
    return result.rowcount > 0
