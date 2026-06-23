from __future__ import annotations

from typing import Any

from backend.graph.state import CompletenessChecklist, RequirementAnalysis, TestContext, TicketData
from backend.intelligence.context import (
    format_knowledge_context,
    format_memory_context,
    complete_with_configured_llm,
    prompt_version_ref,
    search_knowledge_for_ticket,
    search_memory_for_ticket,
)
from backend.prompts import prompt_registry
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalRequirementHeuristicTool",
    isolation="process",
    description="Extracts requirement analysis fields with deterministic local heuristics plus local AI/RAG traceability.",
)
class LocalRequirementHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> RequirementAnalysis:
        ticket = kwargs.get("ticket")
        context = kwargs.get("context")
        if not isinstance(ticket, TicketData):
            raise TypeError("LocalRequirementHeuristicTool requires a TicketData ticket")
        if context is not None and not isinstance(context, TestContext):
            raise TypeError("LocalRequirementHeuristicTool requires TestContext or None")
        return analyze_ticket(ticket, context=context)


def analyze_ticket(ticket: TicketData, *, context: TestContext | None = None) -> RequirementAnalysis:
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

    knowledge_results = search_knowledge_for_ticket(ticket, limit=3, context=context)
    memory_results = search_memory_for_ticket(ticket, limit=3, context=context)
    prompt = prompt_registry.get("requirement_analysis_v1")
    rendered_prompt = prompt.render(
        ticket_title=ticket.title,
        priority=ticket.priority,
        labels=", ".join(ticket.labels),
        description=ticket.description,
        acceptance_criteria=ticket.acceptance_criteria or ["No acceptance criteria provided"],
        knowledge_context=format_knowledge_context(knowledge_results),
        memory_context=format_memory_context(memory_results),
    )
    llm_response = complete_with_configured_llm(
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        rendered_prompt=rendered_prompt,
        system_instruction="You are a QA requirement analysis assistant operating in deterministic local mode.",
        context=context,
    )

    knowledge_refs = [result.chunk.chunk_id for result in knowledge_results]
    memory_refs = [result.entry.memory_id for result in memory_results]

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
        memory_refs_used=memory_refs,
        knowledge_refs_used=knowledge_refs,
        prompt_versions_used=[prompt_version_ref("requirement_analysis_v1")],
        llm_summary=llm_response.text,
        confidence=0.82 if has_acceptance_criteria else 0.62,
    )


def _infer_domain(labels: list[str], title: str, description: str) -> str:
    text = " ".join([title, description, *labels]).lower()
    if any(term in text for term in ("payment", "transfer", "banking", "account")):
        return "banking"
    if any(term in text for term in ("api", "endpoint", "request", "response")):
        return "api"
    return "general"


def _infer_actor(description: str) -> str:
    lowered = description.lower()
    if "customer" in lowered:
        return "customer"
    if "admin" in lowered:
        return "admin"
    if "engineer" in lowered:
        return "engineer"
    return "user"
