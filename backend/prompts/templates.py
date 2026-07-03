from __future__ import annotations

from backend.prompts.base import prompt_registry

prompt_registry.register(
    name="requirement_analysis_v1",
    version="1.2.0",
    description="Analyze a ticket with retrieved domain context and previous workflow memory, including a structured completeness checklist assessment.",
    template=(
        "Ticket: $ticket_title | Priority: $priority | Labels: $labels\n"
        "Description:\n$description\n\n"
        "Acceptance Criteria:\n$acceptance_criteria\n\n"
        "Knowledge Context:\n$knowledge_context\n\n"
        "Episodic Memory:\n$memory_context\n\n"
        "Analyze this ticket. The 'summary' is your concise requirement "
        "interpretation with risk hints; 'ambiguities' are clarifying questions; "
        "'checklist_assessment' is your independent true/false/null judgement of "
        "whether the ticket satisfies each completeness item (use null when "
        "unsure).\n\n"
        "$json_contract"
    ),
)

prompt_registry.register(
    name="coverage_planning_v1",
    version="2.0.0",
    description="Plan coverage using requirement analysis, retrieved knowledge, and historical memory.",
    template=(
        "Ticket: $ticket_title\nDomain: $domain\nRisk: $risk_level\n"
        "Known requirements:\n$expected_results\n\n"
        "Knowledge Context:\n$knowledge_context\n\n"
        "Memory Context:\n$memory_context\n\n"
        "Plan coverage for this ticket. 'risk_notes' capture business-risk, "
        "negative-path, and boundary concerns; 'suggested_regressions' are "
        "regression test ids worth re-running (e.g. REG-BALANCE-CONSISTENCY) and "
        "must be grounded in the knowledge/memory context above.\n\n"
        "$json_contract"
    ),
)

prompt_registry.register(
    name="test_case_generation_v1",
    version="2.0.0",
    description="Generate evidence-aware test cases from coverage and retrieved context.",
    template=(
        "Ticket: $ticket_title\nBusiness action: $business_action\n"
        "Coverage types: $test_types_required\n"
        "Knowledge Context:\n$knowledge_context\n"
        "Memory Context:\n$memory_context\n\n"
        "Propose test cases spanning functional, negative, boundary, and "
        "regression scenarios. 'generation_notes' explain coverage decisions; "
        "'suggested_test_titles' are concise test case titles.\n\n"
        "$json_contract"
    ),
)

prompt_registry.register(
    name="report_generation_v1",
    version="2.0.0",
    description="Generate a report with AI/RAG/memory traceability.",
    template=(
        "Ticket: $ticket_id - $ticket_title\n"
        "Risk: $risk_level\nTests: $test_count\nExecution: $execution_status\n"
        "Knowledge refs: $knowledge_refs\nMemory refs: $memory_refs\n\n"
        "Summarize the QA workflow evidence. 'executive_summary' is a concise "
        "stakeholder-facing outcome; 'next_actions' are concrete follow-ups.\n\n"
        "$json_contract"
    ),
)
