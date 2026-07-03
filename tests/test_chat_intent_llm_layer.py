from __future__ import annotations

from unittest import mock

from backend.chat import llm_intent
from backend.chat.intent_classifier import classify_chat_intent


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubProvider:
    def __init__(self, text: str) -> None:
        self._text = text

    def complete(self, **_kwargs: object) -> _StubResponse:
        return _StubResponse(self._text)


def _patch_llm(text: str, *, provider: str = "openai_compatible"):
    """Context managers to make the LLM intent layer active with a stub model."""
    return (
        mock.patch.object(llm_intent.settings, "chat_llm_fallback_enabled", True),
        mock.patch.object(llm_intent.settings, "default_llm_provider", provider),
        mock.patch(
            "backend.llm.llm_provider_registry.create",
            return_value=_StubProvider(text),
        ),
    )


def test_llm_layer_disabled_in_demo_mode_returns_none() -> None:
    with mock.patch.object(llm_intent.settings, "chat_llm_fallback_enabled", False):
        assert llm_intent.classify_intent_with_llm("anything at all") is None


def test_llm_layer_noop_for_mock_provider() -> None:
    with mock.patch.object(llm_intent.settings, "chat_llm_fallback_enabled", True), \
         mock.patch.object(llm_intent.settings, "default_llm_provider", "mock_llm"):
        assert llm_intent.classify_intent_with_llm("anything at all") is None


def test_llm_layer_parses_valid_json() -> None:
    p1, p2, p3 = _patch_llm('{"intent": "investigation_question", "confidence": 0.91}')
    with p1, p2, p3:
        result = llm_intent.classify_intent_with_llm("something feels off with the run")
    assert result == ("investigation_question", 0.91)


def test_llm_layer_rejects_unknown_label() -> None:
    p1, p2, p3 = _patch_llm('{"intent": "not_a_real_intent", "confidence": 0.99}')
    with p1, p2, p3:
        assert llm_intent.classify_intent_with_llm("hello") is None


def test_llm_layer_handles_garbage_output() -> None:
    p1, p2, p3 = _patch_llm("I think you want to investigate the failure.")
    with p1, p2, p3:
        assert llm_intent.classify_intent_with_llm("hello") is None


def test_llm_layer_survives_provider_error() -> None:
    with mock.patch.object(llm_intent.settings, "chat_llm_fallback_enabled", True), \
         mock.patch.object(llm_intent.settings, "default_llm_provider", "openai_compatible"), \
         mock.patch(
             "backend.llm.llm_provider_registry.create",
             side_effect=RuntimeError("boom"),
         ):
        assert llm_intent.classify_intent_with_llm("hello") is None


def test_classifier_escalates_to_llm_on_unknown() -> None:
    """A genuinely unknown phrasing is rescued by the LLM layer when available."""
    message = "Who created you and what is your broader purpose, in plain terms?"
    # Deterministic alone -> unknown
    with mock.patch(
        "backend.chat.intent_classifier._maybe_classify_with_llm", return_value=None
    ):
        assert classify_chat_intent(message).intent == "unknown"
    # With LLM available -> uses the LLM's confident label
    with mock.patch(
        "backend.chat.intent_classifier._maybe_classify_with_llm",
        return_value=("system_knowledge", 0.88),
    ):
        result = classify_chat_intent(message)
    assert result.intent == "system_knowledge"
    assert result.confidence >= 0.5


def test_classifier_does_not_call_llm_on_strong_deterministic_hit() -> None:
    """A strong rule match must not waste an LLM call."""
    with mock.patch(
        "backend.chat.intent_classifier._maybe_classify_with_llm"
    ) as patched:
        result = classify_chat_intent("suggest test cases for DEMO-FIN-REFUND-002")
    assert result.intent == "test_case_suggestion"
    patched.assert_not_called()


def test_llm_cannot_override_into_mutating_intent() -> None:
    """W9: a prompt-injected/ambiguous message must never have the LLM layer
    override it into a state-changing intent (execution/approval/start/step) --
    those stay rule-driven so no destructive action card can be surfaced by the
    model. An unknown deterministic result stays unknown despite a confident LLM
    'execution_request'."""
    message = "do the needful as appropriate"
    for mutating in (
        "execution_request",
        "approval_request",
        "workflow_start",
        "workflow_step",
    ):
        with mock.patch(
            "backend.chat.intent_classifier._maybe_classify_with_llm",
            return_value=(mutating, 0.99),
        ):
            result = classify_chat_intent(message)
        assert result.intent != mutating, (
            f"LLM was allowed to override into mutating intent {mutating!r}"
        )
        # Deterministic baseline was unknown; the blocked override leaves it there.
        assert result.intent == "unknown"


def test_llm_can_still_rescue_read_only_intent() -> None:
    """W9 must not over-block: the LLM may still rescue a read-only intent."""
    message = "give me your broader reasoning about what happened here, in plain terms"
    with mock.patch(
        "backend.chat.intent_classifier._maybe_classify_with_llm",
        return_value=("investigation_question", 0.9),
    ):
        result = classify_chat_intent(message)
    assert result.intent == "investigation_question"
