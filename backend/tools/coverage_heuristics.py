from __future__ import annotations

from typing import Any

from backend.graph.state import CoveragePlan, RequirementAnalysis, TestContext, TicketData
from backend.intelligence.coverage_derivation import (
    build_coverage_matrix,
    derive_coverage,
)
from backend.intelligence.coverage_adjudication import adjudicate_coverage_plan
from backend.intelligence.context import (
    append_feedback_to_prompt,
    consume_stage_feedback,
    format_knowledge_context,
    format_memory_context,
    complete_with_configured_llm,
    search_knowledge_for_ticket,
    search_memory_for_ticket,
)
from backend.prompts import prompt_registry
from backend.intelligence.structured_outputs import (
    CoverageLLMOutput,
    build_json_contract,
    parse_structured_llm_response,
)
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalCoverageHeuristicTool",
    isolation="process",
    description="Plans coverage with deterministic local risk, RAG, and episodic-memory heuristics.",
)
class LocalCoverageHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> CoveragePlan:
        ticket = kwargs.get("ticket")
        analysis = kwargs.get("requirement_analysis")
        context = kwargs.get("context")
        if not isinstance(ticket, TicketData):
            raise TypeError("LocalCoverageHeuristicTool requires a TicketData ticket")
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError(
                "LocalCoverageHeuristicTool requires RequirementAnalysis"
            )
        if context is not None and not isinstance(context, TestContext):
            raise TypeError("LocalCoverageHeuristicTool requires TestContext or None")
        return plan_coverage(ticket=ticket, analysis=analysis, context=context)


def plan_coverage(
    *,
    ticket: TicketData,
    analysis: RequirementAnalysis,
    context: TestContext | None = None,
) -> CoveragePlan:
    if ticket.priority == "critical":
        risk_level = "critical"
        criticality = 10
    elif ticket.priority == "high" or analysis.domain == "banking":
        risk_level = "high"
        criticality = 8
    elif ticket.priority == "low":
        risk_level = "low"
        criticality = 3
    else:
        risk_level = "medium"
        criticality = 5

    # Derive requirements, required test types, and propagated confidence from the
    # ADJUDICATED requirement analysis (not just domain + one boolean). Risk level
    # stays priority/domain-driven above; the checklist now shapes coverage types.
    derivation = derive_coverage(analysis, risk_level=risk_level)
    required_types = derivation.test_types_required

    knowledge_results = search_knowledge_for_ticket(ticket, limit=3, context=context)
    memory_results = search_memory_for_ticket(ticket, limit=3, context=context)
    prompt = prompt_registry.get("coverage_planning_v1")
    rendered_prompt = prompt.render(
        ticket_title=ticket.title,
        domain=analysis.domain,
        risk_level=risk_level,
        expected_results=analysis.expected_results,
        knowledge_context=format_knowledge_context(knowledge_results),
        memory_context=format_memory_context(memory_results),
        json_contract=build_json_contract(CoverageLLMOutput),
    )
    reviewer_feedback = consume_stage_feedback(context, "coverage")
    rendered_prompt = append_feedback_to_prompt(
        rendered_prompt,
        reviewer_feedback,
    )
    llm_response = complete_with_configured_llm(
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        rendered_prompt=rendered_prompt,
        system_instruction=(
            "You are an evidence-grounded QA coverage planner. Focus on business risk, "
            "negative paths, boundaries, and regression scope."
        ),
        context=context,
        model_role="reasoning",
    )

    structured_output = parse_structured_llm_response(
        response=llm_response,
        schema=CoverageLLMOutput,
        context=context,
    )
    knowledge_refs = [result.chunk.chunk_id for result in knowledge_results]
    memory_refs = [result.entry.memory_id for result in memory_results]
    memory_evidence = [
        " ".join(
            [
                result.entry.title,
                result.entry.summary,
                *result.entry.tags,
            ]
        ).lower()
        for result in memory_results
    ]

    # Deterministic, episodic-memory-EVIDENCED regression detection. These are
    # grounded in retrieved memory and always survive adjudication below.
    deterministic_regressions: list[str] = []
    if any(
        "transfer" in evidence and "balance" in evidence
        for evidence in memory_evidence
    ) and ticket.id.startswith("AI-"):
        deterministic_regressions.append("REG-BALANCE-CONSISTENCY")
    if any("authorization" in evidence for evidence in memory_evidence) and ticket.id.startswith(
        "AI-"
    ):
        deterministic_regressions.append("REG-AUTH-NEGATIVE-PATHS")

    # Deterministic rationale built first; the LLM reading is reconciled against
    # it (labelled, evidence-gated) rather than stapled on. See
    # backend.intelligence.coverage_adjudication.
    risk_rationale = [
        f"Priority '{ticket.priority}' and domain '{analysis.domain}' produce {risk_level} risk.",
    ]
    if knowledge_refs:
        risk_rationale.append(f"Knowledge evidence considered: {', '.join(knowledge_refs)}.")
    if memory_refs:
        risk_rationale.append(f"Episodic memory considered: {', '.join(memory_refs)}.")
    risk_rationale.extend(
        f"Reviewer direction applied: {comment}"
        for comment in reviewer_feedback
    )
    risk_rationale.extend(derivation.rationale)

    adjudication = adjudicate_coverage_plan(
        derivation_confidence=derivation.confidence,
        deterministic_regressions=deterministic_regressions,
        deterministic_rationale=risk_rationale,
        llm=structured_output,
        knowledge_refs=len(knowledge_refs),
        memory_refs=len(memory_refs),
        llm_unparsed_text=llm_response.text,
        llm_provider=llm_response.provider,
    )
    regression_tests = adjudication.regressions
    risk_rationale.extend(adjudication.risk_rationale_additions)
    risk_rationale.extend(adjudication.notes)

    # Build a requirement→test-case matrix from the DERIVED requirements (not the
    # old hardcoded REQ-001/2/3). Coverage runs before test-case generation, so we
    # assign planned TC slots by requirement order; test-case generation honors
    # these ids when tagging requirement_refs.
    planned_assignment: dict[str, list[str]] = {}
    for slot, req in enumerate(derivation.requirements, start=1):
        planned_assignment[req.requirement_id] = [f"TC{slot:03d}"]
    coverage_matrix = build_coverage_matrix(derivation.requirements, planned_assignment)
    planned_test_ids = [tc for ids in planned_assignment.values() for tc in ids]

    return CoveragePlan(
        risk_level=risk_level,
        business_criticality=criticality,
        test_types_required=required_types,
        coverage_matrix=coverage_matrix,
        regression_tests_to_rerun=regression_tests,
        estimated_automation_effort="medium" if risk_level != "critical" else "high",
        prioritization_order=[*planned_test_ids, *regression_tests],
        memory_refs_used=memory_refs,
        knowledge_refs_used=knowledge_refs,
        risk_rationale=risk_rationale,
        confidence=adjudication.confidence,
        requirement_items=derivation.requirements,
    )
