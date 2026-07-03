"""Triage-engine live test against the external GPU server (Nemotron-70B).

Creates a real autonomous workflow session for a demo ticket using the
openai_compatible provider, runs the LangGraph pipeline end-to-end, and then
proves the agents used the REAL model rather than silently degrading to the
deterministic mock — by inspecting intelligence_trace.llm_calls for any
fallback_from marker. Exits non-zero if any real-intent call fell back to mock.
"""
from __future__ import annotations

import os
from pathlib import Path

# Faithfully load the same .env the server uses.
ENV = Path("/root/work/aegis/.env")
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def _resolve_ticket():
    # Use the same ticket source the API uses, so the TicketData is schema-valid.
    from backend.tickets import get_ticket_source

    ticket = get_ticket_source().fetch("DEMO-FIN-REFUND-002")
    if ticket is None:
        raise SystemExit("FAIL: demo ticket DEMO-FIN-REFUND-002 not found")
    return ticket


def main() -> int:
    from backend.api.routes.workflows import build_intelligence_config
    from backend.config.settings import settings
    from backend.services.workflow_control import (
        create_workflow_session,
        resume_workflow_session,
    )

    print(f"default_llm_provider     = {settings.default_llm_provider}")
    print(f"allow_mock_fallback      = {settings.allow_mock_fallback}")
    print(f"agent_max_tokens_per_call= {os.environ.get('AEGISQA_AGENT_MAX_TOKENS_PER_CALL')}")
    print(f"base_url                 = {os.environ.get('AEGISQA_OPENAI_COMPATIBLE_BASE_URL')}")
    print("-" * 64)

    ticket = _resolve_ticket()
    intelligence = build_intelligence_config(None)  # uses configured defaults
    print(f"intelligence.llm_provider = {intelligence.llm_provider}")

    context = create_workflow_session(
        created_by="triage-test",
        ticket=ticket,
        intelligence_config=intelligence,
        mode="autonomous",
    )
    print(f"created session {context.context_id} (mode=autonomous)")

    context = resume_workflow_session(
        context_id=context.context_id,
        actor="triage-test",
    )

    calls = context.intelligence_trace.llm_calls
    print("-" * 64)
    print(f"workflow_status = {context.workflow_status}")
    print(f"llm_calls       = {len(calls)}")
    if not calls:
        print("FAIL: no LLM calls recorded — engine did not invoke the model.")
        return 2

    fell_back = [c for c in calls if getattr(c, "fallback_from", None)]
    for i, c in enumerate(calls, 1):
        provider = getattr(c, "provider", "?")
        model = getattr(c, "model", "?")
        fb = getattr(c, "fallback_from", None)
        flag = f"  <-- FALLBACK from {fb}" if fb else ""
        print(f"  [{i}] {provider} | {model}{flag}")

    print("-" * 64)
    last = calls[-1]
    real_provider = getattr(last, "provider", "")
    print(f"last call provider   = {real_provider}")
    print(f"last call fallback   = {getattr(last, 'fallback_from', None)}")
    print(f"calls that fell back = {len(fell_back)}/{len(calls)}")

    if fell_back:
        print("FAIL: at least one call silently degraded to mock.")
        return 1
    if "mock" in str(getattr(last, "model", "")).lower():
        print("FAIL: last call model looks like the deterministic mock.")
        return 1

    print("PASS: real model used end-to-end, zero mock fallbacks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
