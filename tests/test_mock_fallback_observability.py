"""Phase 1 hardening — C1 (silent mock fallback made observable) + S10 (fail-closed).

A real provider failing and the output quietly becoming a deterministic mock is
the system's #1 trust risk. These tests prove the fallback is now LOUD:
  - a WARNING log event is emitted at the fallback site,
  - operational_health surfaces a mock_fallback_rate signal,
  - and AEGISQA_ALLOW_MOCK_FALLBACK=false makes the boundary fail closed
    (re-raise) instead of returning fake content as if it were real.
"""
from __future__ import annotations

import logging

import pytest

from backend.config.settings import settings
from backend.governance.context import request_context_scope
from backend.intelligence.context import complete_with_configured_llm
from backend.llm import llm_provider_registry
from backend.llm.base import BaseLLMProvider, LLMResponse
from backend.observability.health import operational_health


_BOOM_PROVIDER = "boom_provider_test"


def _register_boom_provider() -> str:
    """Register (once) a provider whose complete() always raises, simulating a
    real provider being unreachable / erroring."""
    if not llm_provider_registry.has(_BOOM_PROVIDER):

        @llm_provider_registry.register(
            name=_BOOM_PROVIDER,
            mode="external",
            model="boom-1",
            description="Test-only provider that always fails.",
        )
        class _BoomProvider(BaseLLMProvider):
            def complete(self, **_kwargs) -> LLMResponse:  # noqa: ANN003
                raise RuntimeError("simulated provider outage")

    return _BOOM_PROVIDER


def test_fallback_emits_warning_log_and_degrades_by_default(
    monkeypatch, caplog
) -> None:
    provider = _register_boom_provider()
    monkeypatch.setattr(settings, "default_llm_provider", provider)
    monkeypatch.setattr(settings, "allow_mock_fallback", True)

    with caplog.at_level(logging.WARNING, logger="aegisqa.intelligence"):
        response = complete_with_configured_llm(
            prompt_name="coverage_planning_v1",
            prompt_version="1.0.0",
            rendered_prompt="Ticket: trigger the provider outage",
        )

    # Graceful degradation still works by default...
    assert response.provider == "mock_llm"
    assert response.deterministic is True
    assert "fallback from" in response.model
    # ...but it is no longer SILENT: a structured WARNING fired at the site.
    fallback_logs = [
        record
        for record in caplog.records
        if getattr(record, "aegis_event", {}).get("event") == "llm_mock_fallback"
    ]
    assert fallback_logs, "expected an llm_mock_fallback WARNING log event"
    event = fallback_logs[0].aegis_event
    assert event["provider"] == provider
    assert event["error_type"] == "RuntimeError"
    assert event["fail_closed"] is False


def test_fail_closed_reraises_instead_of_returning_mock(monkeypatch) -> None:
    provider = _register_boom_provider()
    monkeypatch.setattr(settings, "default_llm_provider", provider)
    monkeypatch.setattr(settings, "allow_mock_fallback", False)

    # With fail-closed enabled, a failed real call must NOT be silently
    # substituted with mock output — it raises so the caller can react.
    with pytest.raises(RuntimeError, match="simulated provider outage"):
        complete_with_configured_llm(
            prompt_name="coverage_planning_v1",
            prompt_version="1.0.0",
            rendered_prompt="Ticket: trigger the provider outage",
        )


def test_operational_health_flags_mock_fallback(monkeypatch) -> None:
    provider = _register_boom_provider()
    monkeypatch.setattr(settings, "default_llm_provider", provider)
    monkeypatch.setattr(settings, "allow_mock_fallback", True)
    # Any fallback at all should trip the signal (default threshold 0.0).
    monkeypatch.setattr(
        settings, "observability_mock_fallback_rate_threshold", 0.0
    )

    org = "mock-fallback-health-test"
    # Drive a fallback whose model_invocation is attributed to this org.
    with request_context_scope(
        request_id="health-test", actor="pytest", organization_id=org
    ):
        complete_with_configured_llm(
            prompt_name="coverage_planning_v1",
            prompt_version="1.0.0",
            rendered_prompt="Ticket: trigger the provider outage",
        )

    health = operational_health(organization_id=org)
    assert health["mock_fallback_rate"] > 0.0
    assert health["status"] == "degraded"
    signal_names = {signal["name"] for signal in health["signals"]}
    assert "mock_fallback_rate" in signal_names


def test_readiness_reports_model_provider_honestly(monkeypatch) -> None:
    from backend.observability.health import readiness_status

    # mock provider: ready, no external dependency.
    monkeypatch.setattr(settings, "default_llm_provider", "mock_llm")
    payload, code = readiness_status()
    assert code == 200
    assert payload["checks"]["model_provider"]["status"] == "ready"
    assert payload["checks"]["model_provider"]["provider"] == "mock_llm"

    # An unreachable real provider degrades (not_ready only when fail-closed),
    # and the truth is always surfaced in the model_provider check.
    monkeypatch.setattr(settings, "default_llm_provider", "ollama")
    monkeypatch.setattr(settings, "allow_mock_fallback", True)
    monkeypatch.setattr(
        "backend.llm.ollama.ollama_health",
        lambda: {"available": False, "message": "Ollama is not reachable."},
    )
    payload, code = readiness_status()
    provider_check = payload["checks"]["model_provider"]
    assert provider_check["provider"] == "ollama"
    assert provider_check["status"] == "degraded"
    # Degraded still serves (allow_mock_fallback=True) but is no longer a lie.
    assert code == 200

    # With fail-closed, an unreachable real provider is genuinely not ready.
    monkeypatch.setattr(settings, "allow_mock_fallback", False)
    payload, code = readiness_status()
    assert payload["checks"]["model_provider"]["status"] == "not_ready"
    assert code == 503
