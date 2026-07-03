from __future__ import annotations

from unittest import mock

from backend.llm.openai_compatible import OpenAICompatibleLLMProvider


def _clamp(max_tokens, prompt, window, floor=256):
    with mock.patch.multiple(
        "backend.llm.openai_compatible.settings",
        openai_compatible_context_window=window,
        openai_compatible_min_output_tokens=floor,
    ):
        return OpenAICompatibleLLMProvider._clamp_output_tokens(
            max_output_tokens=max_tokens,
            system_instruction="You are AegisQA.",
            rendered_prompt=prompt,
        )


def test_clamp_disabled_when_window_zero() -> None:
    assert _clamp(16000, "short prompt", window=0) == 16000


def test_clamp_caps_to_window_minus_prompt() -> None:
    clamped = _clamp(16000, "x" * 40, window=8192)
    assert clamped is not None
    assert clamped <= 8192
    assert clamped < 16000


def test_clamp_never_below_floor() -> None:
    # Huge prompt eats the window; output must still be at least the floor.
    assert _clamp(16000, "x" * 40000, window=8192, floor=256) == 256


def test_clamp_respects_smaller_requested_max() -> None:
    # If the caller asks for fewer tokens than the window allows, keep theirs.
    assert _clamp(100, "short", window=8192) == 100


def test_clamp_handles_none_request() -> None:
    # No requested cap -> provider supplies the window-derived allowance.
    allowed = _clamp(None, "x" * 40, window=8192)
    assert allowed is not None and allowed > 0
