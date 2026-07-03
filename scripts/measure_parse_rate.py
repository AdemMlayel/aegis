"""Measure live structured-parse rate across all four LLM stages.

Runs each stage's real prompt through the configured provider (live Nemotron via
openai_compatible) and reports whether the response parsed into its schema. This
is the honest before/after metric for the prompt-contract fix.
"""
from __future__ import annotations

from backend.graph.state import TestContext, TicketData
from backend.intelligence.context import complete_with_configured_llm
from backend.intelligence.structured_outputs import (
    CoverageLLMOutput,
    ReportLLMOutput,
    RequirementLLMOutput,
    TestCaseLLMOutput,
    build_json_contract,
    parse_structured_llm_response,
)
from backend.prompts import prompt_registry

STAGES = [
    ("requirement_analysis_v1", RequirementLLMOutput, "reasoning"),
    ("coverage_planning_v1", CoverageLLMOutput, "reasoning"),
    ("test_case_generation_v1", TestCaseLLMOutput, "stable_baseline"),
    ("report_generation_v1", ReportLLMOutput, "main_rag"),
]

# Minimal realistic render values per prompt (only fields each template uses).
RENDER = {
    "requirement_analysis_v1": dict(
        ticket_title="Transfer funds with insufficient balance",
        priority="high",
        labels="banking, transfer",
        description="Customer transfers funds; insufficient balance must be rejected with no state change. Min 1 USD, max 50000 USD.",
        acceptance_criteria="Transfer completes within 2s for valid input.",
        knowledge_context="KB-BANK-001: balance consistency rules.",
        memory_context="MEMORY[prior transfer/balance incident].",
    ),
    "coverage_planning_v1": dict(
        ticket_title="Transfer funds with insufficient balance",
        domain="banking",
        risk_level="high",
        expected_results="Reject insufficient-funds transfer; no money moves.",
        knowledge_context="KB-BANK-001: balance consistency rules.",
        memory_context="MEMORY[prior transfer/balance incident].",
    ),
    "test_case_generation_v1": dict(
        ticket_title="Transfer funds with insufficient balance",
        business_action="Transfer funds between accounts",
        test_types_required="functional, negative, boundary",
        knowledge_context="KB-BANK-001: balance consistency rules.",
        memory_context="MEMORY[prior transfer/balance incident].",
    ),
    "report_generation_v1": dict(
        ticket_id="AI-777",
        ticket_title="Transfer funds with insufficient balance",
        risk_level="high",
        test_count=4,
        execution_status="passed",
        knowledge_refs="KB-BANK-001",
        memory_refs="MEM-001",
    ),
}

SCHEMA_FOR = {name: schema for name, schema, _ in STAGES}


def main() -> None:
    ctx = TestContext(
        ticket=TicketData(id="AI-777", title="probe", description="probe"),
        created_by="parse-rate-probe",
    )
    results = []
    for name, schema, role in STAGES:
        prompt = prompt_registry.get(name)
        rendered = prompt.render(
            json_contract=build_json_contract(schema),
            **RENDER[name],
        )
        resp = complete_with_configured_llm(
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            rendered_prompt=rendered,
            system_instruction="You are AegisQA. Follow the JSON contract exactly.",
            context=ctx,
            model_role=role,
        )
        parsed = parse_structured_llm_response(response=resp, schema=schema, context=ctx)
        ok = parsed is not None
        fallback = resp.provider == "mock_llm"
        results.append((name, ok, fallback, resp.provider))
        print(f"[{name}]")
        print(f"  provider     : {resp.provider}")
        print(f"  parsed_ok    : {ok}")
        if not ok:
            print(f"  raw_text[:300]: {resp.text[:300]!r}")
        print()

    passed = sum(1 for _, ok, fb, _ in results if ok and not fb)
    real = sum(1 for _, _, fb, _ in results if not fb)
    print(f"=== parse rate: {passed}/{len(results)} parsed on a REAL provider "
          f"({real}/{len(results)} stages hit a real provider, rest fell back to mock) ===")


if __name__ == "__main__":
    main()
