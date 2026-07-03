from __future__ import annotations

from unittest import mock

from backend.chat.intent_classifier import classify_chat_intent
from backend.chat.response_builder import build_assistant_response
from backend.chat.schemas import ChatSession

UNKNOWN_QUESTION = "Who created you and what is your broader purpose, in plain terms?"


def test_unknown_returns_deterministic_fallback_when_llm_disabled() -> None:
    session = ChatSession(created_by="t")
    classified = classify_chat_intent(UNKNOWN_QUESTION)
    assert classified.intent == "unknown"
    with mock.patch(
        "backend.chat.response_builder.answer_with_llm", return_value=None
    ) as patched:
        answer = build_assistant_response(session=session, classified=classified)
    patched.assert_called_once()
    assert "did not map that to a safe" in answer


def test_unknown_uses_llm_answer_when_available() -> None:
    session = ChatSession(created_by="t")
    classified = classify_chat_intent(UNKNOWN_QUESTION)
    assert classified.intent == "unknown"
    with mock.patch(
        "backend.chat.response_builder.answer_with_llm",
        return_value="A grounded answer.\n\nSources: KB-QA-001",
    ):
        answer = build_assistant_response(session=session, classified=classified)
    assert answer == "A grounded answer.\n\nSources: KB-QA-001"


def test_known_intents_never_invoke_llm_responder() -> None:
    """Deterministic intents must answer without touching the LLM path."""
    session = ChatSession(created_by="t")
    with mock.patch(
        "backend.chat.response_builder.answer_with_llm"
    ) as patched:
        for message in [
            "what are the workflow stages",
            "explain the architecture",
            "what is mocked and what is real",
            "help",
        ]:
            classified = classify_chat_intent(message)
            build_assistant_response(session=session, classified=classified)
    patched.assert_not_called()


def test_llm_responder_returns_none_when_disabled() -> None:
    from backend.chat.llm_responder import answer_with_llm

    with mock.patch(
        "backend.chat.llm_responder.settings.chat_llm_fallback_enabled", False
    ):
        assert answer_with_llm("anything") is None
