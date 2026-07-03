"""Ad-hoc verification: confirm AegisQA agents run on the real Nemotron endpoint.

Runs the requirement + coverage stages through complete_with_configured_llm
(exactly what the workflow agents call) and inspects the intelligence trace to
prove the call landed on the self-hosted Nemotron vLLM server and did NOT
silently fall back to the mock provider.
"""
from __future__ import annotations

from backend.config.settings import settings
from backend.graph.state import TestContext as WorkflowContext, TicketData
from backend.intelligence.context import complete_with_configured_llm

print("default_llm_provider :", settings.default_llm_provider)
print("base_url             :", settings.openai_compatible_base_url)
print("chat_model           :", settings.openai_compatible_chat_model)
print("context_window       :", settings.openai_compatible_context_window)
print("agent_max_tokens     :", settings.agent_max_tokens_per_call)
print("-" * 60)

ctx = WorkflowContext(
    created_by="verify",
    ticket=TicketData(
        id="VERIFY-NEMOTRON-1",
        title="High-value refund approval",
        description="As an approver, I want to approve or reject high-value refunds with an immutable audit trail.",
        acceptance_criteria=[
            "High-value refund requires approval by a designated approver",
            "Requester cannot approve their own refund",
            "Approve and reject outcomes write immutable audit events",
        ],
        priority="high",
        labels=["api", "payments", "audit"],
    ),
)

resp = complete_with_configured_llm(
    prompt_name="requirement_analysis_v1",
    prompt_version="1.0.0",
    rendered_prompt="Analyze the refund approval requirement and list 3 ambiguities.",
    context=ctx,
)

print("LLMResponse.provider      :", resp.provider)
print("LLMResponse.model         :", resp.model)
print("LLMResponse.deterministic :", resp.deterministic)
print("usage(in/out/total)       :",
      getattr(resp, "input_tokens", "?"),
      getattr(resp, "output_tokens", "?"),
      getattr(resp, "total_tokens", "?"))
print("text[:240]                :", (resp.text or "")[:240].replace("\n", " "))
print("-" * 60)

calls = ctx.intelligence_trace.llm_calls
print("trace llm_calls           :", len(calls))
if calls:
    last = calls[-1]
    print("  provider                :", last.provider)
    print("  model                   :", last.model)
    print("  status                  :", getattr(last, "status", "?"))
    print("  fallback_from           :", getattr(last, "fallback_from", "MISSING"))
    print("  total_tokens            :", getattr(last, "total_tokens", "?"))

real = (
    resp.provider == "openai_compatible"
    and "Nemotron" in resp.model
    and resp.deterministic is False
    and (not calls or getattr(calls[-1], "fallback_from", None) is None)
)
print("=" * 60)
print("VERDICT:", "REAL NEMOTRON (no fallback) ✅" if real else "NOT REAL / FELL BACK ❌")
