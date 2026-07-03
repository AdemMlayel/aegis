"""Optional LLM-backed intent classification for the chat copilot.

The deterministic ``classify_chat_intent`` is fast, free, and handles the vast
majority of phrasings via scored keyword/phrase matching. This module adds an
LLM adjudication layer for the genuinely ambiguous cases — natural phrasings the
rules score weakly or miss entirely.

Design constraints (mirror llm_responder):
- Activates ONLY when a real LLM is configured and chat fallback is enabled;
  it is off by default and forced off in deterministic demo mode. With the mock
  provider it never runs, so behavior in demo mode is unchanged.
- Classification ONLY. It maps free-form text to one of the known intents; it
  never proposes or triggers actions. Action planning stays on the deterministic,
  confirmation-gated path keyed off the returned intent.
- Degrades safely: any provider error, malformed output, or unrecognized label
  returns ``None`` so the caller keeps the deterministic result. Chat must never
  hard-fail on classification.
"""
from __future__ import annotations

import json
import re
from typing import get_args

from backend.chat.schemas import ChatIntent
from backend.config.settings import settings

_VALID_INTENTS: frozenset[str] = frozenset(get_args(ChatIntent))

_SYSTEM_INSTRUCTION = (
    "You are an intent classifier for the AegisQA QA-orchestration copilot. "
    "Read the user's message and choose the single best intent label from the "
    "allowed list. Respond with ONLY a compact JSON object of the form "
    '{\"intent\": \"<label>\", \"confidence\": <0..1>}. Do not add prose, '
    "markdown, or explanation. If nothing fits, use \"unknown\"."
)

# Short, model-friendly description of what each intent means.
_INTENT_GUIDE = """Allowed intents and meaning:
- help: greetings, thanks, or asking what the copilot can do.
- system_question: what providers/models are configured, mocked vs real, runtime mode.
- system_knowledge: how the system/architecture/agents/workflow/governance work conceptually.
- ticket_question: gaps, risks, acceptance criteria, or details of a ticket.
- test_case_suggestion: asking the copilot to suggest/propose/draft test cases or scenarios.
- workflow_start: begin/kick off analysis or a new workflow for a ticket.
- workflow_status: where are we, current stage, progress of a workflow.
- workflow_step: continue/resume/run the next stage; keep going.
- artifact_question: about generated Robot files, keywords, automation artifacts.
- validation_question: about validation / dry-run results or why validation failed.
- approval_request: approve a stage or the package; sign off.
- execution_request: run/execute the tests.
- investigation_question: why something failed, root cause, debugging, troubleshooting.
- report_request: produce or summarize a report / executive summary.
- knowledge_question: the RAG corpus, knowledge base, sanitized grounding.
- action_history: list of proposed/confirmed/cancelled chat actions.
- unknown: anything that does not fit the above."""


def _llm_enabled() -> bool:
    if not settings.chat_llm_fallback_enabled:
        return False
    provider = (settings.default_llm_provider or "").strip().lower()
    # The mock provider cannot classify; treat it as disabled.
    return bool(provider) and provider != "mock_llm"


def classify_intent_with_llm(message: str) -> tuple[str, float] | None:
    """Return (intent, confidence) from the configured LLM, or None.

    None means "unavailable or could not decide" — the caller keeps the
    deterministic classification.
    """
    if not _llm_enabled():
        return None
    cleaned = (message or "").strip()
    if not cleaned:
        return None

    rendered_prompt = (
        f"{_INTENT_GUIDE}\n\n"
        f"User message: {cleaned}\n\n"
        'Return only JSON: {"intent": "<label>", "confidence": <0..1>}.'
    )

    try:
        from backend.llm import llm_provider_registry

        provider = llm_provider_registry.create(settings.default_llm_provider)
        response = provider.complete(
            prompt_name="chat_intent_v1",
            prompt_version="v1",
            rendered_prompt=rendered_prompt,
            system_instruction=_SYSTEM_INSTRUCTION,
            max_output_tokens=64,
        )
    except Exception:  # noqa: BLE001 - classification must never hard-fail chat.
        return None

    return _parse_intent(getattr(response, "text", "") or "")


def _parse_intent(text: str) -> tuple[str, float] | None:
    """Strictly parse the model output into (intent, confidence) or None."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None

    intent = str(data.get("intent", "")).strip()
    if intent not in _VALID_INTENTS:
        return None

    raw_conf = data.get("confidence", 0.7)
    try:
        confidence = float(raw_conf)
    except (ValueError, TypeError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))
    return intent, confidence
