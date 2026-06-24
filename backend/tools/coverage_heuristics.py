from __future__ import annotations

from typing import Any

from backend.graph.state import CoveragePlan, RequirementAnalysis, TestContext, TicketData
from backend.intelligence.context import (
    append_feedback_to_prompt,
    consume_stage_feedback,
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

    required_types = ["functional", "negative"]
    if risk_level in {"high", "critical"}:
        required_types.append("boundary")
    if analysis.completeness_checklist.performance_expectations_set:
        required_types.append("performance")

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

    knowledge_refs = [result.chunk.chunk_id for result in knowledge_results]
    memory_refs = [result.entry.memory_id for result in memory_results]

    regression_tests: list[str] = []
    if any("transfer" in ref.lower() for ref in memory_refs) and ticket.id.startswith("AI-"):
        regression_tests.append("REG-BALANCE-CONSISTENCY")
    if any("authorization" in ref.lower() for ref in memory_refs) and ticket.id.startswith("AI-"):
        regression_tests.append("REG-AUTH-NEGATIVE-PATHS")

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
    if llm_response.provider != "mock_llm" and llm_response.text:
        risk_rationale.append(f"Model guidance: {llm_response.text[:1200]}")

    return CoveragePlan(
        risk_level=risk_level,
        business_criticality=criticality,
        test_types_required=required_types,
        coverage_matrix={
            "REQ-001 primary success path": ["TC001"],
            "REQ-002 invalid or rejected input": ["TC002"],
            "REQ-003 boundary condition": ["TC003"],
        },
        regression_tests_to_rerun=regression_tests,
        estimated_automation_effort="medium" if risk_level != "critical" else "high",
        prioritization_order=["TC001", "TC002", "TC003", *regression_tests],
        memory_refs_used=memory_refs,
        knowledge_refs_used=knowledge_refs,
        risk_rationale=risk_rationale,
    )
