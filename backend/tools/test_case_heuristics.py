from __future__ import annotations

from typing import Any, Literal

from backend.graph.state import CoveragePlan, RequirementAnalysis, TestCase, TestContext, TicketData
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
    TestCaseLLMOutput,
    build_json_contract,
    parse_structured_llm_response,
)
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalTestCaseHeuristicTool",
    isolation="process",
    description="Generates deterministic evidence-aware test cases from requirement, coverage, RAG, and memory data.",
)
class LocalTestCaseHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> list[TestCase]:
        analysis = kwargs.get("requirement_analysis")
        coverage_plan = kwargs.get("coverage_plan")
        ticket = kwargs.get("ticket")
        context = kwargs.get("context")
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError(
                "LocalTestCaseHeuristicTool requires RequirementAnalysis"
            )
        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("LocalTestCaseHeuristicTool requires CoveragePlan")
        if ticket is not None and not isinstance(ticket, TicketData):
            raise TypeError("LocalTestCaseHeuristicTool requires TicketData or None")
        if context is not None and not isinstance(context, TestContext):
            raise TypeError("LocalTestCaseHeuristicTool requires TestContext or None")
        return generate_test_cases(
            analysis=analysis,
            coverage_plan=coverage_plan,
            ticket=ticket,
            context=context,
        )


def _refs_for(coverage_plan: CoveragePlan, test_case_id: str, fallback: str) -> list[str]:
    """Resolve a test case's requirement_refs from the derived coverage matrix.

    The matrix keys are 'REQ-00N <description>'; values are the planned TC slots.
    We invert it so each test case is tagged to the real requirement(s) covering
    it, instead of the old hardcoded REQ-001/2/3. Falls back to the given default
    when (legacy/empty matrix) nothing maps to this slot.
    """
    refs: list[str] = []
    for key, tc_ids in coverage_plan.coverage_matrix.items():
        if test_case_id in tc_ids:
            req_id = key.split(" ", 1)[0]
            if req_id and req_id not in refs:
                refs.append(req_id)
    return refs or [fallback]


def _requirement_test_type(
    requirement: Any,
) -> Literal["functional", "negative", "boundary", "regression", "edge"]:
    """Pick a TestCase type for a derived requirement from its declared test_types.

    Falls back to the origin: checklist-origin error requirements lean negative,
    everything else functional. Always returns a valid TestCase.type literal.
    """
    valid: tuple[Literal["functional", "negative", "boundary", "regression", "edge"], ...] = (
        "functional",
        "negative",
        "boundary",
        "regression",
        "edge",
    )
    for candidate in requirement.test_types:
        if candidate in valid:
            return candidate
    if requirement.origin == "checklist":
        return "negative"
    return "functional"


def generate_test_cases(
    *,
    analysis: RequirementAnalysis,
    coverage_plan: CoveragePlan,
    ticket: TicketData | None = None,
    context: TestContext | None = None,
) -> list[TestCase]:
    evidence_refs = list(coverage_plan.knowledge_refs_used or analysis.knowledge_refs_used)
    memory_refs = list(coverage_plan.memory_refs_used or analysis.memory_refs_used)
    model_guidance: str | None = None
    structured_notes: list[str] = []
    reviewer_feedback: list[str] = []
    if ticket is not None:
        knowledge_results = search_knowledge_for_ticket(ticket, limit=3, context=context)
        memory_results = search_memory_for_ticket(ticket, limit=3, context=context)
        prompt = prompt_registry.get("test_case_generation_v1")
        rendered_prompt = prompt.render(
            ticket_title=ticket.title,
            business_action=analysis.business_action,
            test_types_required=coverage_plan.test_types_required,
            knowledge_context=format_knowledge_context(knowledge_results),
            memory_context=format_memory_context(memory_results),
            json_contract=build_json_contract(TestCaseLLMOutput),
        )
        reviewer_feedback = consume_stage_feedback(context, "tests")
        rendered_prompt = append_feedback_to_prompt(
            rendered_prompt,
            reviewer_feedback,
        )
        llm_response = complete_with_configured_llm(
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            rendered_prompt=rendered_prompt,
            system_instruction=(
                "You are an evidence-grounded QA test case generator. Identify complete "
                "positive, negative, boundary, and regression scenarios."
            ),
            context=context,
            model_role="stable_baseline",
        )
        structured_output = parse_structured_llm_response(
            response=llm_response,
            schema=TestCaseLLMOutput,
            context=context,
        )
        if structured_output is not None:
            structured_notes = structured_output.generation_notes
        elif llm_response.provider != "mock_llm" and llm_response.text:
            model_guidance = f"Model guidance: {llm_response.text[:1200]}"

    test_cases = [
        TestCase(
            id="TC001",
            title=f"{analysis.business_action} - Happy Path",
            type="functional",
            priority="critical" if coverage_plan.risk_level == "critical" else "high",
            requirement_refs=_refs_for(coverage_plan, "TC001", "REQ-001"),
            preconditions=analysis.preconditions,
            steps=_primary_steps(ticket, analysis),
            expected_outcome=_primary_expected_outcome(ticket),
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["valid_record"],
                **_structured_data_requirements(ticket),
            },
            evidence_refs=evidence_refs,
            memory_refs=memory_refs,
            generation_notes=[
                "Generated from local deterministic AI/RAG architecture path.",
                *_structured_generation_notes(ticket),
            ],
        ),
        TestCase(
            id="TC002",
            title=f"{analysis.business_action} - Rejected Input",
            type="negative",
            priority="high",
            requirement_refs=_refs_for(coverage_plan, "TC002", "REQ-002"),
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                f"Start {analysis.business_action}",
                "Submit invalid or incomplete data",
                "Verify that the action is rejected clearly",
            ],
            expected_outcome="Invalid action is rejected without changing system state",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["invalid_record"],
            },
            evidence_refs=evidence_refs,
            memory_refs=memory_refs,
            generation_notes=["Negative path is required by the coverage plan."],
        ),
        TestCase(
            id="TC003",
            title=f"{analysis.business_action} - Boundary Condition",
            type="boundary",
            priority="medium",
            requirement_refs=_refs_for(coverage_plan, "TC003", "REQ-003"),
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                "Prepare boundary-value data",
                f"Run {analysis.business_action}",
                "Verify boundary behavior",
            ],
            expected_outcome="Boundary values are handled according to requirements",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["boundary_record"],
            },
            evidence_refs=evidence_refs,
            memory_refs=memory_refs,
            generation_notes=["Boundary path is included for high-risk or memory-supported flows."],
        ),
    ]

    # One covering test case per DERIVED requirement beyond the first three (which
    # the functional/negative/boundary archetypes above already cover). This closes
    # the matrix↔generator gap: every requirement the coverage plan derived now has
    # a covering case, instead of REQ-004+ having planned slots with no test.
    base_count = len(test_cases)
    extra_requirements = coverage_plan.requirement_items[base_count:]
    for offset, requirement in enumerate(extra_requirements):
        index = base_count + offset + 1
        tc_id = f"TC{index:03d}"
        req_type = _requirement_test_type(requirement)
        test_cases.append(
            TestCase(
                id=tc_id,
                title=f"{analysis.business_action} - {requirement.description[:60]}",
                type=req_type,
                priority="high" if req_type in {"negative", "functional"} else "medium",
                requirement_refs=_refs_for(coverage_plan, tc_id, requirement.requirement_id),
                preconditions=analysis.preconditions,
                steps=[
                    f"Sign in as {analysis.actor}",
                    f"Exercise: {requirement.description}",
                    f"Run {analysis.business_action}",
                    "Verify the requirement holds",
                ],
                expected_outcome=requirement.description,
                test_data_requirements={
                    "users": ["valid_user"],
                    "records": [f"{req_type}_record"],
                },
                evidence_refs=evidence_refs,
                memory_refs=memory_refs,
                generation_notes=[
                    f"Derived from coverage requirement {requirement.requirement_id} "
                    f"(origin: {requirement.origin}).",
                ],
            )
        )

    for index, regression_ref in enumerate(
        coverage_plan.regression_tests_to_rerun, start=len(test_cases) + 1
    ):
        test_cases.append(
            TestCase(
                id=f"TC{index:03d}",
                title=f"{analysis.business_action} - {regression_ref}",
                type="regression",
                priority="high",
                requirement_refs=[regression_ref],
                preconditions=analysis.preconditions,
                steps=[
                    f"Sign in as {analysis.actor}",
                    "Replay the historical regression condition",
                    f"Run {analysis.business_action}",
                    "Verify the previous failure condition does not reappear",
                ],
                expected_outcome=f"Historical regression {regression_ref} remains fixed",
                test_data_requirements={"users": ["valid_user"], "records": ["regression_record"]},
                evidence_refs=evidence_refs,
                memory_refs=memory_refs,
                generation_notes=["Generated from episodic memory regression hint."],
            )
        )

    if structured_notes:
        for test_case in test_cases:
            test_case.generation_notes.extend(structured_notes)
    if model_guidance:
        for test_case in test_cases:
            test_case.generation_notes.append(model_guidance)
    for comment in reviewer_feedback:
        for test_case in test_cases:
            test_case.generation_notes.append(
                f"Reviewer direction applied: {comment}"
            )

    return test_cases


def _primary_steps(
    ticket: TicketData | None,
    analysis: RequirementAnalysis,
) -> list[str]:
    if ticket and ticket.test_steps:
        return [
            f"{step.order}. {step.action} Expected: {step.expected_result}"
            for step in sorted(ticket.test_steps, key=lambda item: item.order)
        ]
    return [
        f"Sign in as {analysis.actor}",
        f"Start {analysis.business_action}",
        "Submit valid data",
        "Verify the success response",
    ]


def _primary_expected_outcome(ticket: TicketData | None) -> str:
    if ticket and ticket.expected_outputs:
        return "; ".join(ticket.expected_outputs[:3])
    return "Primary user journey completes successfully"


def _structured_data_requirements(ticket: TicketData | None) -> dict[str, list[str]]:
    if ticket is None or not ticket.input_data:
        return {}
    return {
        "structured_ticket_inputs": [item.value for item in ticket.input_data],
    }


def _structured_generation_notes(ticket: TicketData | None) -> list[str]:
    if ticket is None:
        return []
    notes: list[str] = []
    if ticket.required_tools:
        notes.append(f"Required tools: {', '.join(ticket.required_tools)}")
    if ticket.validation_rules:
        notes.append(
            "Validation rules: "
            + ", ".join(rule.id for rule in ticket.validation_rules)
        )
    if ticket.interfaces_involved:
        notes.append(
            "Interfaces involved: "
            + ", ".join(ticket.interfaces_involved)
        )
    return notes
