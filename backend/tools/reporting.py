from __future__ import annotations

from typing import Any

from backend.graph.state import (
    ApprovalBlock,
    AutomationBlock,
    CoveragePlan,
    ExecutionBlock,
    IntelligenceTraceBlock,
    InvestigationBlock,
    MemoryArchiveBlock,
    ReportBlock,
    TestContext,
    TestCase,
    TicketData,
)
from backend.intelligence.context import (
    append_feedback_to_prompt,
    complete_with_configured_llm,
    consume_stage_feedback,
)
from backend.prompts import prompt_registry
from backend.intelligence.structured_outputs import (
    ReportLLMOutput,
    parse_structured_llm_response,
)
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalReportGenerationTool",
    isolation="process",
    description="Builds deterministic workflow reports with AI/RAG/memory traceability.",
)
class LocalReportGenerationTool(BaseTool):
    def invoke(self, **kwargs: Any) -> ReportBlock:
        coverage_plan = kwargs.get("coverage_plan")
        ticket = kwargs.get("ticket")
        test_cases = kwargs.get("test_cases")
        automation = kwargs.get("automation")
        approval = kwargs.get("approval")
        execution = kwargs.get("execution")
        investigation = kwargs.get("investigation")
        memory_archive = kwargs.get("memory_archive")
        intelligence_trace = kwargs.get("intelligence_trace")
        context = kwargs.get("context")

        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("LocalReportGenerationTool requires CoveragePlan")
        if ticket is not None and not isinstance(ticket, TicketData):
            raise TypeError("LocalReportGenerationTool requires TicketData or None")
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("LocalReportGenerationTool requires list[TestCase]")
        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "LocalReportGenerationTool requires dict[str, AutomationBlock]"
            )
        if approval is not None and not isinstance(approval, ApprovalBlock):
            raise TypeError("LocalReportGenerationTool requires ApprovalBlock or None")
        if execution is not None and not isinstance(execution, ExecutionBlock):
            raise TypeError("LocalReportGenerationTool requires ExecutionBlock or None")
        if investigation is not None and not isinstance(investigation, InvestigationBlock):
            raise TypeError("LocalReportGenerationTool requires InvestigationBlock or None")
        if memory_archive is not None and not isinstance(memory_archive, MemoryArchiveBlock):
            raise TypeError("LocalReportGenerationTool requires MemoryArchiveBlock or None")
        if intelligence_trace is not None and not isinstance(intelligence_trace, IntelligenceTraceBlock):
            raise TypeError("LocalReportGenerationTool requires IntelligenceTraceBlock or None")
        if context is not None and not isinstance(context, TestContext):
            raise TypeError("LocalReportGenerationTool requires TestContext or None")

        return generate_report(
            coverage_plan=coverage_plan,
            ticket=ticket,
            test_cases=test_cases,
            automation=automation,
            approval=approval,
            execution=execution,
            investigation=investigation,
            memory_archive=memory_archive,
            intelligence_trace=intelligence_trace,
            context=context,
        )


def generate_report(
    *,
    coverage_plan: CoveragePlan,
    ticket: TicketData | None,
    test_cases: list[TestCase],
    automation: dict[str, AutomationBlock],
    approval: ApprovalBlock | None,
    execution: ExecutionBlock | None = None,
    investigation: InvestigationBlock | None = None,
    memory_archive: MemoryArchiveBlock | None = None,
    intelligence_trace: IntelligenceTraceBlock | None = None,
    context: TestContext | None = None,
) -> ReportBlock:
    automation_count = len(automation)
    validated_count = sum(
        1
        for automation_block in automation.values()
        if automation_block.validation.dry_run_passed is True
    )
    approval_status = approval.status if approval else "not_ready"
    execution_status = execution.status if execution else "not_started"
    investigation_status = investigation.status if investigation else "not_started"
    memory_status = memory_archive.status if memory_archive else "not_started"

    knowledge_refs = [ref.ref_id for ref in intelligence_trace.knowledge_refs] if intelligence_trace else []
    memory_refs = [ref.ref_id for ref in intelligence_trace.memory_refs] if intelligence_trace else []
    prompt_refs = [f"{ref.name}@{ref.version}" for ref in intelligence_trace.prompt_versions] if intelligence_trace else []
    model_summary: str | None = None
    model_next_actions: list[str] = []
    model_confidence: float | None = None
    reviewer_feedback: list[str] = []

    if ticket is not None:
        prompt = prompt_registry.get("report_generation_v1")
        rendered_prompt = prompt.render(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            risk_level=coverage_plan.risk_level,
            test_count=len(test_cases),
            execution_status=execution_status,
            knowledge_refs=knowledge_refs,
            memory_refs=memory_refs,
        )
        reviewer_feedback = consume_stage_feedback(context, "report")
        rendered_prompt = append_feedback_to_prompt(
            rendered_prompt,
            reviewer_feedback,
        )
        llm_response = complete_with_configured_llm(
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            rendered_prompt=rendered_prompt,
            system_instruction=(
                "You are an evidence-grounded QA report generator. Summarize outcomes, "
                "risk, confidence, and practical next actions."
            ),
            context=context,
            model_role="main_rag",
        )
        structured_output = parse_structured_llm_response(
            response=llm_response,
            schema=ReportLLMOutput,
            context=context,
        )
        if structured_output is not None and llm_response.provider != "mock_llm":
            model_summary = structured_output.executive_summary[:2000]
            model_next_actions = structured_output.next_actions
            model_confidence = structured_output.confidence
        elif llm_response.provider != "mock_llm" and llm_response.text:
            model_summary = llm_response.text[:2000]
        if "report_generation_v1@1.0.0" not in prompt_refs:
            prompt_refs.append("report_generation_v1@1.0.0")

    return ReportBlock(
        summary=model_summary or (
            f"Generated {len(test_cases)} starter test cases and "
            f"{automation_count} Robot automation files for "
            f"{ticket.id if ticket else 'unknown ticket'}. "
            f"Validated {validated_count}/{automation_count}; "
            f"approval status is {approval_status}; "
            f"execution status is {execution_status}; "
            f"investigation status is {investigation_status}; "
            f"memory status is {memory_status}."
        ),
        total_test_cases=len(test_cases),
        highest_risk=coverage_plan.risk_level,
        next_actions=[
            "Review requirement clarification questions",
            "Review generated Robot files through the automation file endpoint",
            "Execute approved automation through the mock or Robot execution adapter",
            "Review investigation and archived-memory payloads before promoting to external systems",
            *model_next_actions,
            *[
                f"Reviewer direction applied: {comment}"
                for comment in reviewer_feedback
            ],
        ],
        knowledge_refs_used=knowledge_refs,
        memory_refs_used=memory_refs,
        prompt_versions_used=prompt_refs,
        confidence=model_confidence if model_confidence is not None else 0.82 if knowledge_refs or memory_refs else 0.68,
    )
