from __future__ import annotations

from typing import Any

from backend.graph.state import CoveragePlan, RequirementAnalysis, TestCase, TestContext, TicketData
from backend.intelligence.context import (
    format_knowledge_context,
    format_memory_context,
    complete_with_configured_llm,
    search_knowledge_for_ticket,
    search_memory_for_ticket,
)
from backend.prompts import prompt_registry
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


def generate_test_cases(
    *,
    analysis: RequirementAnalysis,
    coverage_plan: CoveragePlan,
    ticket: TicketData | None = None,
    context: TestContext | None = None,
) -> list[TestCase]:
    evidence_refs = list(coverage_plan.knowledge_refs_used or analysis.knowledge_refs_used)
    memory_refs = list(coverage_plan.memory_refs_used or analysis.memory_refs_used)
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
        )
        complete_with_configured_llm(
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            rendered_prompt=rendered_prompt,
            system_instruction="You are a QA test case generator operating in deterministic local mode.",
            context=context,
        )

    test_cases = [
        TestCase(
            id="TC001",
            title=f"{analysis.business_action} - Happy Path",
            type="functional",
            priority="critical" if coverage_plan.risk_level == "critical" else "high",
            requirement_refs=["REQ-001"],
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                f"Start {analysis.business_action}",
                "Submit valid data",
                "Verify the success response",
            ],
            expected_outcome="Primary user journey completes successfully",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["valid_record"],
            },
            evidence_refs=evidence_refs,
            memory_refs=memory_refs,
            generation_notes=["Generated from local deterministic AI/RAG architecture path."],
        ),
        TestCase(
            id="TC002",
            title=f"{analysis.business_action} - Rejected Input",
            type="negative",
            priority="high",
            requirement_refs=["REQ-002"],
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
            requirement_refs=["REQ-003"],
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

    for index, regression_ref in enumerate(coverage_plan.regression_tests_to_rerun, start=4):
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

    return test_cases
