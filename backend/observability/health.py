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

    ready = all(
        check["status"] == "ready"
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


def operational_health(
    *,
    organization_id: str | None = None,
) -> dict[str, object]:
    summary = observability_summary(organization_id=organization_id)
    request_total = int(summary["requests"]["total"])
    request_errors = int(summary["requests"]["server_errors"])
    agent_total = int(summary["agents"]["total"])
    agent_failures = int(summary["agents"]["failed"])
    request_error_rate = (
        request_errors / request_total if request_total else 0.0
    )
    agent_failure_rate = (
        agent_failures / agent_total if agent_total else 0.0
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
    return {
        "status": "degraded" if signals else "healthy",
        "request_error_rate": round(request_error_rate, 4),
        "agent_failure_rate": round(agent_failure_rate, 4),
        "open_provider_circuits": len(open_circuits),
        "signals": signals,
    }
