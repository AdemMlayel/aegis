"""Run the full 8-stage AegisQA workflow on the configured (Nemotron) LLM and
report per-stage provenance from the intelligence trace."""
from __future__ import annotations

import time

from backend.graph.state import TestContext as WorkflowContext, TicketData
from backend.graph.workflow import run_workflow

t0 = time.time()
ctx = run_workflow(
    WorkflowContext(
        created_by="nemotron-fullrun",
        ticket=TicketData(
            id="REFUND-AUDIT-7",
            title="High-value refund approval with immutable audit",
            description=(
                "As an approver, I want to approve or reject high-value refunds, "
                "with every outcome writing an immutable audit event, so that the "
                "settlement state stays consistent and reviewable."
            ),
            acceptance_criteria=[
                "High-value refund requires approval by a designated approver",
                "Requester cannot approve their own refund",
                "Approve and reject outcomes write immutable audit events",
                "Rejected refunds do not mutate settlement state",
            ],
            priority="high",
            labels=["api", "payments", "audit"],
        ),
    )
)
dt = time.time() - t0

print(f"workflow_status : {ctx.workflow_status}")
print(f"elapsed         : {dt:.1f}s")
print(f"requirement     : {'ok' if ctx.requirement_analysis else 'MISSING'}")
print(f"coverage_plan   : {'ok' if ctx.coverage_plan else 'MISSING'}")
print(f"test_cases      : {len(ctx.test_cases)}")
print(f"automation      : {len(ctx.automation or {})}")
print(f"reports         : {'ok' if ctx.reports else 'MISSING'}")
print("-" * 64)

calls = ctx.intelligence_trace.llm_calls
print(f"LLM calls       : {len(calls)}")
providers = {c.provider for c in calls}
models = {c.model for c in calls}
fallbacks = [c for c in calls if getattr(c, "fallback_from", None) is not None]
total_tokens = sum(getattr(c, "total_tokens", 0) or 0 for c in calls)
print(f"providers used  : {providers}")
print(f"models used     : {models}")
print(f"fallback calls  : {len(fallbacks)}")
print(f"total tokens    : {total_tokens}")
for c in calls:
    print(f"  - {getattr(c,'prompt_name','?'):28} {c.provider:18} "
          f"{getattr(c,'total_tokens',0)} tok  fallback_from={getattr(c,'fallback_from',None)}")

all_real = (
    providers == {"openai_compatible"}
    and not fallbacks
    and all("Nemotron" in m for m in models)
)
print("=" * 64)
print("VERDICT:", "FULL PIPELINE ON NEMOTRON, ZERO FALLBACK ✅" if all_real
      else "MIXED / FALLBACK DETECTED ⚠️")
