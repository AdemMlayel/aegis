from __future__ import annotations

from backend.config.settings import settings
from backend.governance.gateway import circuit_breakers
from backend.storage.database import connect, initialize_database
from backend.storage.observability import observability_summary


def liveness_status() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


def readiness_status() -> tuple[dict[str, object], int]:
    checks: dict[str, dict[str, object]] = {}
    try:
        initialize_database()
        with connect() as connection:
            connection.execute("SELECT 1").fetchone()
        checks["database"] = {"status": "ready"}
    except Exception as exc:  # noqa: BLE001 - readiness must report dependency failures.
        checks["database"] = {
            "status": "not_ready",
            "error": type(exc).__name__,
        }

    configuration_errors: list[str] = []
    if settings.gateway_requests_per_minute <= 0:
        configuration_errors.append(
            "AEGISQA_GATEWAY_REQUESTS_PER_MINUTE must be positive"
        )
    if settings.organization_daily_token_quota <= 0:
        configuration_errors.append(
            "AEGISQA_ORGANIZATION_DAILY_TOKEN_QUOTA must be positive"
        )
    if settings.token_reservation_ttl_seconds <= 0:
        configuration_errors.append(
            "AEGISQA_TOKEN_RESERVATION_TTL_SECONDS must be positive"
        )
    checks["configuration"] = {
        "status": "ready" if not configuration_errors else "not_ready",
        "errors": configuration_errors,
    }

    # Honest model-provider readiness. When a real LLM provider is configured
    # (i.e. not the deterministic mock), probe its reachability so /health/ready
    # doesn't report "ready" while every model call is actually degrading to
    # mock. The probe is REPORTED always; it only blocks readiness (503) when
    # fail-closed is enabled (allow_mock_fallback=False) — otherwise an
    # intentionally-degrading demo stays ready, but the truth is still visible.
    provider = settings.default_llm_provider
    if provider == "mock_llm":
        checks["model_provider"] = {
            "status": "ready",
            "provider": provider,
            "detail": "Deterministic mock provider; no external dependency.",
        }
    else:
        reachable, detail = _probe_model_provider(provider)
        if reachable:
            provider_status = "ready"
        elif settings.allow_mock_fallback:
            # Degrades to mock rather than failing the request, so the service
            # is still "ready" — but we surface the degraded truth explicitly.
            provider_status = "degraded"
        else:
            provider_status = "not_ready"
        checks["model_provider"] = {
            "status": provider_status,
            "provider": provider,
            "fail_closed": not settings.allow_mock_fallback,
            "detail": detail,
        }

    ready = all(
        check["status"] in {"ready", "degraded"}
        for check in checks.values()
    )
    return (
        {
            "status": "ready" if ready else "not_ready",
            "service": settings.app_name,
            "environment": settings.environment,
            "checks": checks,
        },
        200 if ready else 503,
    )


def _probe_model_provider(provider: str) -> tuple[bool, str]:
    """Best-effort reachability probe for a configured real LLM provider.

    Returns (reachable, human-readable detail). Never raises — a probe failure
    is reported as unreachable, not as a server error.
    """
    try:
        if provider == "ollama":
            from backend.llm.ollama import ollama_health

            health = ollama_health()
            return bool(health.get("available")), str(
                health.get("message", "")
            )
        if provider == "openai_compatible":
            # We don't burn a real completion here; reachability of an external
            # endpoint is asserted by configuration presence + circuit state.
            base_url = settings.openai_compatible_base_url
            if not base_url:
                return (
                    False,
                    "openai_compatible selected but "
                    "AEGISQA_OPENAI_COMPATIBLE_BASE_URL is unset.",
                )
            open_providers = {
                item["provider"]
                for item in circuit_breakers.status()
                if item["state"] == "open"
            }
            if provider in open_providers:
                return (
                    False,
                    f"Circuit breaker is open for {provider}.",
                )
            return True, f"Configured external provider at {base_url}."
        # Unknown/custom provider: we can't probe it, so report unknown rather
        # than falsely asserting readiness.
        return (
            False,
            f"No reachability probe implemented for provider {provider!r}.",
        )
    except Exception as exc:  # noqa: BLE001 - readiness probe must never raise.
        return False, f"Provider probe failed: {type(exc).__name__}: {exc}"


def operational_health(
    *,
    organization_id: str | None = None,
) -> dict[str, object]:
    summary = observability_summary(organization_id=organization_id)
    request_total = int(summary["requests"]["total"])
    request_errors = int(summary["requests"]["server_errors"])
    agent_total = int(summary["agents"]["total"])
    agent_failures = int(summary["agents"]["failed"])
    model_total = int(summary["model_calls"]["total"])
    mock_fallbacks = int(summary["model_calls"]["mock_fallbacks"])
    request_error_rate = (
        request_errors / request_total if request_total else 0.0
    )
    agent_failure_rate = (
        agent_failures / agent_total if agent_total else 0.0
    )
    mock_fallback_rate = (
        mock_fallbacks / model_total if model_total else 0.0
    )
    open_circuits = [
        item
        for item in circuit_breakers.status()
        if item["state"] == "open"
    ]
    signals: list[dict[str, object]] = []
    if request_error_rate > settings.observability_error_rate_threshold:
        signals.append(
            {
                "name": "http_error_rate",
                "severity": "warning",
                "value": round(request_error_rate, 4),
                "threshold": settings.observability_error_rate_threshold,
            }
        )
    if (
        agent_failure_rate
        > settings.observability_agent_failure_rate_threshold
    ):
        signals.append(
            {
                "name": "agent_failure_rate",
                "severity": "warning",
                "value": round(agent_failure_rate, 4),
                "threshold": (
                    settings.observability_agent_failure_rate_threshold
                ),
            }
        )
    if open_circuits:
        signals.append(
            {
                "name": "provider_circuits",
                "severity": "warning",
                "open_providers": [
                    item["provider"] for item in open_circuits
                ],
            }
        )
    if mock_fallback_rate > settings.observability_mock_fallback_rate_threshold:
        signals.append(
            {
                "name": "mock_fallback_rate",
                "severity": "warning",
                "value": round(mock_fallback_rate, 4),
                "threshold": (
                    settings.observability_mock_fallback_rate_threshold
                ),
                "mock_fallbacks": mock_fallbacks,
                "model_calls": model_total,
            }
        )
    return {
        "status": "degraded" if signals else "healthy",
        "request_error_rate": round(request_error_rate, 4),
        "agent_failure_rate": round(agent_failure_rate, 4),
        "mock_fallback_rate": round(mock_fallback_rate, 4),
        "open_provider_circuits": len(open_circuits),
        "signals": signals,
    }
