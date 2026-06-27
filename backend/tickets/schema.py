from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.graph.state import StrictModel, TicketData, TicketStatus, utc_now


TicketPriority = Literal["low", "medium", "high", "critical"]
RequirementStatus = Literal["draft", "approved", "needs_clarification"]


def now_iso() -> str:
    return utc_now().isoformat()


class TicketComment(StrictModel):
    author: str
    body: str
    created_at: str = Field(default_factory=now_iso)


class LinkedRequirement(StrictModel):
    id: str
    title: str
    status: RequirementStatus = "draft"
    source: str = "demo"


class StructuredTicketRecord(TicketData):
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    comments: list[TicketComment] = Field(default_factory=list)
    linked_requirements: list[LinkedRequirement] = Field(default_factory=list)


class StructuredTicketUpdate(StrictModel):
    title: str | None = None
    description: str | None = None
    business_objective: str | None = None
    test_objective: str | None = None
    system_under_test: str | None = None
    feature_or_service_name: str | None = None
    test_scope: list[str] | None = None
    out_of_scope: list[str] | None = None
    preconditions: list[str] | None = None
    assumptions: list[str] | None = None
    environment: str | None = None
    interfaces_involved: list[str] | None = None
    input_data: list[dict[str, str]] | None = None
    expected_outputs: list[str] | None = None
    validation_rules: list[dict[str, object]] | None = None
    test_steps: list[dict[str, object]] | None = None
    acceptance_criteria: list[str] | None = None
    risks_or_constraints: list[str] | None = None
    dependencies: list[str] | None = None
    required_tools: list[str] | None = None
    priority: TicketPriority | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    status: TicketStatus | None = None
    raw_url: str | None = None
    technical: dict[str, object] | None = None
    comments: list[TicketComment] | None = None
    linked_requirements: list[LinkedRequirement] | None = None


class NewTicketComment(StrictModel):
    author: str
    body: str


# Backward-compatible names while older local endpoints still exist.
MockTicketComment = TicketComment
MockLinkedRequirement = LinkedRequirement
MockTicketRecord = StructuredTicketRecord
MockTicketUpdate = StructuredTicketUpdate
NewMockTicketComment = NewTicketComment
MockTicketStatus = TicketStatus
