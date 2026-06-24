from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import StrictModel, utc_now
from backend.storage.database import connect, initialize_database


class RequestObservation(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    actor: str
    organization_id: str
    method: str
    path: str
    status_code: int
    duration_ms: int = Field(ge=0)
    error_type: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ModelInvocation(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str | None = None
    context_id: str | None = None
    organization_id: str = "local"
    actor: str = "system"
    agent_id: str | None = None
    agent_name: str | None = None
    provider: str
    model: str
    prompt_name: str
    status: Literal["success", "fallback", "failed"] = "success"
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    fallback_from: str | None = None
    error_type: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AgentInvocation(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str | None = None
    context_id: str | None = None
    organization_id: str = "local"
    actor: str = "system"
    agent_id: str
    agent_name: str
    status: Literal["success", "failed"] = "success"
    duration_ms: int = Field(default=0, ge=0)
    error_type: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


def save_request_observation(
    observation: RequestObservation,
) -> RequestObservation:
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO request_observations (
                id, request_id, actor, organization_id, method, path,
                status_code, duration_ms, error_type, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation.id,
                observation.request_id,
                observation.actor,
                observation.organization_id,
                observation.method,
                observation.path,
                observation.status_code,
                observation.duration_ms,
                observation.error_type,
                observation.created_at.isoformat(),
            ),
        )
    return observation


def save_model_invocation(invocation: ModelInvocation) -> ModelInvocation:
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO model_invocations (
                id, request_id, context_id, organization_id, actor, agent_id,
                agent_name, provider, model, prompt_name, status, input_tokens,
                output_tokens, total_tokens, duration_ms, estimated_cost_usd,
                fallback_from, error_type, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invocation.id,
                invocation.request_id,
                invocation.context_id,
                invocation.organization_id,
                invocation.actor,
                invocation.agent_id,
                invocation.agent_name,
                invocation.provider,
                invocation.model,
                invocation.prompt_name,
                invocation.status,
                invocation.input_tokens,
                invocation.output_tokens,
                invocation.total_tokens,
                invocation.duration_ms,
                invocation.estimated_cost_usd,
                invocation.fallback_from,
                invocation.error_type,
                invocation.created_at.isoformat(),
            ),
        )
    return invocation


def save_agent_invocation(invocation: AgentInvocation) -> AgentInvocation:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO agent_invocations (
                id, request_id, context_id, organization_id, actor, agent_id,
                agent_name, status, duration_ms, error_type, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invocation.id,
                invocation.request_id,
                invocation.context_id,
                invocation.organization_id,
                invocation.actor,
                invocation.agent_id,
                invocation.agent_name,
                invocation.status,
                invocation.duration_ms,
                invocation.error_type,
                invocation.created_at.isoformat(),
            ),
        )
    return invocation


def list_agent_invocations(
    *,
    organization_id: str | None = None,
    context_id: str | None = None,
    agent_name: str | None = None,
    limit: int = 100,
) -> list[AgentInvocation]:
    conditions: list[str] = []
    parameters: list[object] = []
    if organization_id is not None:
        conditions.append("organization_id = ?")
        parameters.append(organization_id)
    if context_id is not None:
        conditions.append("context_id = ?")
        parameters.append(context_id)
    if agent_name is not None:
        conditions.append("agent_name = ?")
        parameters.append(agent_name)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    parameters.append(limit)
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM agent_invocations
            {where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
    return [
        AgentInvocation(
            id=row["id"],
            request_id=row["request_id"],
            context_id=row["context_id"],
            organization_id=row["organization_id"],
            actor=row["actor"],
            agent_id=row["agent_id"],
            agent_name=row["agent_name"],
            status=row["status"],
            duration_ms=row["duration_ms"],
            error_type=row["error_type"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def list_model_invocations(
    *,
    organization_id: str | None = None,
    context_id: str | None = None,
    agent_name: str | None = None,
    limit: int = 100,
) -> list[ModelInvocation]:
    conditions: list[str] = []
    parameters: list[object] = []
    if organization_id is not None:
        conditions.append("organization_id = ?")
        parameters.append(organization_id)
    if context_id is not None:
        conditions.append("context_id = ?")
        parameters.append(context_id)
    if agent_name is not None:
        conditions.append("agent_name = ?")
        parameters.append(agent_name)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    parameters.append(limit)
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM model_invocations
            {where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
    return [
        ModelInvocation(
            id=row["id"],
            request_id=row["request_id"],
            context_id=row["context_id"],
            organization_id=row["organization_id"],
            actor=row["actor"],
            agent_id=row["agent_id"],
            agent_name=row["agent_name"],
            provider=row["provider"],
            model=row["model"],
            prompt_name=row["prompt_name"],
            status=row["status"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            total_tokens=row["total_tokens"],
            duration_ms=row["duration_ms"],
            estimated_cost_usd=row["estimated_cost_usd"],
            fallback_from=row["fallback_from"],
            error_type=row["error_type"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def count_requests_today(*, organization_id: str) -> int:
    today = datetime.now(UTC).date().isoformat()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM request_observations
            WHERE organization_id = ?
              AND substr(created_at, 1, 10) = ?
            """,
            (organization_id, today),
        ).fetchone()
    return int(row["count"])


def token_usage(
    *,
    organization_id: str | None = None,
    context_id: str | None = None,
    agent_name: str | None = None,
    today_only: bool = False,
) -> dict[str, int | float]:
    conditions: list[str] = []
    parameters: list[object] = []
    if organization_id is not None:
        conditions.append("organization_id = ?")
        parameters.append(organization_id)
    if context_id is not None:
        conditions.append("context_id = ?")
        parameters.append(context_id)
    if agent_name is not None:
        conditions.append("agent_name = ?")
        parameters.append(agent_name)
    if today_only:
        conditions.append("substr(created_at, 1, 10) = ?")
        parameters.append(datetime.now(UTC).date().isoformat())
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS calls,
                COALESCE(SUM(input_tokens), 0) AS input_tokens,
                COALESCE(SUM(output_tokens), 0) AS output_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd
            FROM model_invocations
            {where}
            """,
            tuple(parameters),
        ).fetchone()
    return {
        "calls": int(row["calls"]),
        "input_tokens": int(row["input_tokens"]),
        "output_tokens": int(row["output_tokens"]),
        "total_tokens": int(row["total_tokens"]),
        "estimated_cost_usd": round(float(row["estimated_cost_usd"]), 8),
    }


def observability_summary(
    *,
    organization_id: str | None = None,
) -> dict[str, object]:
    today = datetime.now(UTC).date().isoformat()
    request_scope = (
        "AND organization_id = ?" if organization_id is not None else ""
    )
    request_parameters: tuple[object, ...] = (
        (today, organization_id)
        if organization_id is not None
        else (today,)
    )
    agent_scope = (
        "AND organization_id = ?" if organization_id is not None else ""
    )
    agent_parameters: tuple[object, ...] = (
        (today, organization_id)
        if organization_id is not None
        else (today,)
    )
    with connect() as connection:
        requests = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END), 0)
                    AS server_errors,
                COALESCE(AVG(duration_ms), 0) AS average_duration_ms,
                COALESCE(MAX(duration_ms), 0) AS max_duration_ms
            FROM request_observations
            WHERE substr(created_at, 1, 10) = ?
            {request_scope}
            """,
            request_parameters,
        ).fetchone()
        agents = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0)
                    AS failed,
                COALESCE(AVG(duration_ms), 0) AS average_duration_ms
            FROM agent_invocations
            WHERE substr(created_at, 1, 10) = ?
            {agent_scope}
            """,
            agent_parameters,
        ).fetchone()
    return {
        "date": today,
        "requests": {
            "total": int(requests["total"]),
            "server_errors": int(requests["server_errors"]),
            "average_duration_ms": round(
                float(requests["average_duration_ms"]),
                2,
            ),
            "max_duration_ms": int(requests["max_duration_ms"]),
        },
        "models": token_usage(
            organization_id=organization_id,
            today_only=True,
        ),
        "agents": {
            "total": int(agents["total"]),
            "failed": int(agents["failed"]),
            "average_duration_ms": round(
                float(agents["average_duration_ms"]),
                2,
            ),
        },
    }


def metrics_snapshot() -> dict[str, list[dict[str, int | float | str]]]:
    with connect() as connection:
        requests = connection.execute(
            """
            SELECT
                method,
                path,
                CASE
                    WHEN status_code < 200 THEN '1xx'
                    WHEN status_code < 300 THEN '2xx'
                    WHEN status_code < 400 THEN '3xx'
                    WHEN status_code < 500 THEN '4xx'
                    ELSE '5xx'
                END AS status_class,
                COUNT(*) AS count,
                COALESCE(SUM(duration_ms), 0) AS duration_ms
            FROM request_observations
            GROUP BY method, path, status_class
            ORDER BY method, path, status_class
            """
        ).fetchall()
        agents = connection.execute(
            """
            SELECT
                agent_name,
                status,
                COUNT(*) AS count,
                COALESCE(SUM(duration_ms), 0) AS duration_ms
            FROM agent_invocations
            GROUP BY agent_name, status
            ORDER BY agent_name, status
            """
        ).fetchall()
        models = connection.execute(
            """
            SELECT
                provider,
                model,
                status,
                COUNT(*) AS count,
                COALESCE(SUM(input_tokens), 0) AS input_tokens,
                COALESCE(SUM(output_tokens), 0) AS output_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(duration_ms), 0) AS duration_ms,
                COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd
            FROM model_invocations
            GROUP BY provider, model, status
            ORDER BY provider, model, status
            """
        ).fetchall()
        reservations = connection.execute(
            """
            SELECT
                provider,
                COUNT(*) AS count,
                COALESCE(SUM(reserved_tokens), 0) AS reserved_tokens
            FROM token_reservations
            WHERE status = 'active' AND expires_at > ?
            GROUP BY provider
            ORDER BY provider
            """,
            (datetime.now(UTC).isoformat(),),
        ).fetchall()
    return {
        "requests": [dict(row) for row in requests],
        "agents": [dict(row) for row in agents],
        "models": [dict(row) for row in models],
        "reservations": [dict(row) for row in reservations],
    }
