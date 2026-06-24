from __future__ import annotations

from backend.config.settings import settings
from backend.governance.gateway import circuit_breakers
from backend.storage.observability import metrics_snapshot


def render_prometheus_metrics() -> str:
    snapshot = metrics_snapshot()
    lines = [
        "# HELP aegisqa_info AegisQA service information.",
        "# TYPE aegisqa_info gauge",
        (
            "aegisqa_info"
            f'{{environment="{_escape(settings.environment)}"}} 1'
        ),
        "# HELP aegisqa_http_requests_total Total observed HTTP requests.",
        "# TYPE aegisqa_http_requests_total counter",
        "# HELP aegisqa_http_request_duration_milliseconds_sum Cumulative HTTP request duration.",
        "# TYPE aegisqa_http_request_duration_milliseconds_sum counter",
    ]
    for row in snapshot["requests"]:
        labels = _labels(
            method=row["method"],
            path=row["path"],
            status_class=row["status_class"],
        )
        lines.append(
            f"aegisqa_http_requests_total{labels} {row['count']}"
        )
        lines.append(
            "aegisqa_http_request_duration_milliseconds_sum"
            f"{labels} {row['duration_ms']}"
        )

    lines.extend(
        [
            "# HELP aegisqa_agent_invocations_total Total governed agent invocations.",
            "# TYPE aegisqa_agent_invocations_total counter",
            "# HELP aegisqa_agent_duration_milliseconds_sum Cumulative agent duration.",
            "# TYPE aegisqa_agent_duration_milliseconds_sum counter",
        ]
    )
    for row in snapshot["agents"]:
        labels = _labels(
            agent=row["agent_name"],
            status=row["status"],
        )
        lines.append(
            f"aegisqa_agent_invocations_total{labels} {row['count']}"
        )
        lines.append(
            f"aegisqa_agent_duration_milliseconds_sum{labels} "
            f"{row['duration_ms']}"
        )

    lines.extend(
        [
            "# HELP aegisqa_model_invocations_total Total governed model invocations.",
            "# TYPE aegisqa_model_invocations_total counter",
            "# HELP aegisqa_model_tokens_total Total model tokens by direction.",
            "# TYPE aegisqa_model_tokens_total counter",
            "# HELP aegisqa_model_duration_milliseconds_sum Cumulative model duration.",
            "# TYPE aegisqa_model_duration_milliseconds_sum counter",
            "# HELP aegisqa_model_estimated_cost_usd_total Estimated external model cost.",
            "# TYPE aegisqa_model_estimated_cost_usd_total counter",
        ]
    )
    for row in snapshot["models"]:
        labels = _labels(
            provider=row["provider"],
            model=row["model"],
            status=row["status"],
        )
        lines.append(
            f"aegisqa_model_invocations_total{labels} {row['count']}"
        )
        for direction in ("input", "output", "total"):
            token_labels = _labels(
                provider=row["provider"],
                model=row["model"],
                direction=direction,
            )
            lines.append(
                f"aegisqa_model_tokens_total{token_labels} "
                f"{row[f'{direction}_tokens']}"
            )
        lines.append(
            f"aegisqa_model_duration_milliseconds_sum{labels} "
            f"{row['duration_ms']}"
        )
        lines.append(
            f"aegisqa_model_estimated_cost_usd_total{labels} "
            f"{row['estimated_cost_usd']}"
        )

    lines.extend(
        [
            "# HELP aegisqa_token_reservations_active Active model token reservations.",
            "# TYPE aegisqa_token_reservations_active gauge",
            "# HELP aegisqa_token_reserved Active reserved model tokens.",
            "# TYPE aegisqa_token_reserved gauge",
        ]
    )
    for row in snapshot["reservations"]:
        labels = _labels(provider=row["provider"])
        lines.append(
            f"aegisqa_token_reservations_active{labels} {row['count']}"
        )
        lines.append(
            f"aegisqa_token_reserved{labels} {row['reserved_tokens']}"
        )

    lines.extend(
        [
            "# HELP aegisqa_provider_circuit_open Whether a provider circuit is open.",
            "# TYPE aegisqa_provider_circuit_open gauge",
        ]
    )
    for item in circuit_breakers.status():
        labels = _labels(provider=item["provider"])
        lines.append(
            f"aegisqa_provider_circuit_open{labels} "
            f"{1 if item['state'] == 'open' else 0}"
        )
    return "\n".join(lines) + "\n"


def _labels(**values: object) -> str:
    rendered = ",".join(
        f'{name}="{_escape(str(value))}"'
        for name, value in values.items()
    )
    return f"{{{rendered}}}"


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )
