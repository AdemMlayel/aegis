from __future__ import annotations

from backend.prompts.base import prompt_registry

prompt_registry.register(
    name="requirement_analysis_v1",
    version="1.0.0",
    description="Analyze a ticket with retrieved domain context and previous workflow memory.",
    template=(
        "Ticket: $ticket_title | Priority: $priority | Labels: $labels\n"
        "Description:\n$description\n\n"
        "Acceptance Criteria:\n$acceptance_criteria\n\n"
        "Knowledge Context:\n$knowledge_context\n\n"
        "Episodic Memory:\n$memory_context\n\n"
        "Return a concise requirement interpretation and risk hints."
    ),
)

prompt_registry.register(
    name="coverage_planning_v1",
    version="1.0.0",
    description="Plan coverage using requirement analysis, retrieved knowledge, and historical memory.",
    template=(
        "Ticket: $ticket_title\nDomain: $domain\nRisk: $risk_level\n"
        "Known requirements:\n$expected_results\n\n"
        "Knowledge Context:\n$knowledge_context\n\n"
        "Memory Context:\n$memory_context\n\n"
        "Return coverage priorities and regression hints."
    ),
)

prompt_registry.register(
    name="test_case_generation_v1",
    version="1.0.0",
    description="Generate evidence-aware test cases from coverage and retrieved context.",
    template=(
        "Ticket: $ticket_title\nBusiness action: $business_action\n"
        "Coverage types: $test_types_required\n"
        "Knowledge Context:\n$knowledge_context\n"
        "Memory Context:\n$memory_context\n"
        "Return functional, negative, boundary, and regression test ideas."
    ),
)

prompt_registry.register(
    name="report_generation_v1",
    version="1.0.0",
    description="Generate a report with AI/RAG/memory traceability.",
    template=(
        "Ticket: $ticket_id - $ticket_title\n"
        "Risk: $risk_level\nTests: $test_count\nExecution: $execution_status\n"
        "Knowledge refs: $knowledge_refs\nMemory refs: $memory_refs\n"
        "Summarize the QA workflow evidence."
    ),
)
