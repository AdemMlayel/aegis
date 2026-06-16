from __future__ import annotations

from typing import Any

from backend.graph.state import CompletenessChecklist, RequirementAnalysis, TicketData
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalRequirementHeuristicTool",
    isolation="process",
    description="Extracts requirement analysis fields with deterministic local heuristics.",
)
class LocalRequirementHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> RequirementAnalysis:
        ticket = kwargs.get("ticket")
        if not isinstance(ticket, TicketData):
            raise TypeError("LocalRequirementHeuristicTool requires a TicketData ticket")
        return analyze_ticket(ticket)


def analyze_ticket(ticket: TicketData) -> RequirementAnalysis:
    actor = _infer_actor(ticket.description)
    domain = _infer_domain(ticket.labels, ticket.title, ticket.description)
    has_acceptance_criteria = bool(ticket.acceptance_criteria)
    mentions_performance = any(
        term in criterion.lower()
        for criterion in ticket.acceptance_criteria
        for term in ("second", "minute", "latency", "within")
    )

    checklist = CompletenessChecklist(
        actor_identified=actor != "user",
        preconditions_defined="auth" in ticket.description.lower()
        or "login" in ticket.description.lower(),
        expected_outcome_specified=has_acceptance_criteria,
        error_scenarios_mentioned=any(
            term in ticket.description.lower()
            for term in ("error", "invalid", "fail", "insufficient")
        ),
        data_constraints_defined=any(
            term in ticket.description.lower()
            for term in ("limit", "minimum", "maximum", "currency")
        ),
        performance_expectations_set=mentions_performance,
    )

    missing_fields: list[str] = []
    clarification_questions: list[str] = []
    if not checklist.preconditions_defined:
        missing_fields.append("Preconditions are not explicit")
        clarification_questions.append("What setup or authentication state is required?")
    if not checklist.error_scenarios_mentioned:
        missing_fields.append("Error scenarios are not described")
        clarification_questions.append("Which error states should be tested?")
    if not checklist.data_constraints_defined:
        missing_fields.append("Data constraints are not described")
        clarification_questions.append("What input limits, formats, or currencies apply?")

    return RequirementAnalysis(
        business_action=ticket.title,
        domain=domain,
        actor=actor,
        preconditions=["User can access the target environment"],
        expected_results=ticket.acceptance_criteria
        or ["Requested business action completes successfully"],
        completeness_checklist=checklist,
        missing_fields=missing_fields,
        clarification_questions=clarification_questions,
    )


def _infer_domain(labels: list[str], title: str, description: str) -> str:
    text = " ".join([title, description, *labels]).lower()
    if any(term in text for term in ("payment", "transfer", "banking", "account")):
        return "banking"
    return "general"


def _infer_actor(description: str) -> str:
    lowered = description.lower()
    if "customer" in lowered:
        return "customer"
    if "admin" in lowered:
        return "admin"
    return "user"
