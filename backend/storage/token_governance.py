from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from backend.storage.database import connect


BudgetScope = Literal[
    "organization",
    "workflow_calls",
    "per_call",
    "workflow_tokens",
]


class TokenBudgetReservationDenied(RuntimeError):
    def __init__(self, scope: BudgetScope) -> None:
        self.scope = scope
        super().__init__(scope)


@dataclass(frozen=True)
class TokenReservation:
    id: str
    request_id: str | None
    context_id: str | None
    organization_id: str
    agent_id: str | None
    agent_name: str | None
    provider: str
    estimated_input_tokens: int
    reserved_tokens: int
    expires_at: datetime
    created_at: datetime

    @property
    def max_output_tokens(self) -> int:
        return self.reserved_tokens - self.estimated_input_tokens


def reserve_token_budget(
    *,
    request_id: str | None,
    context_id: str | None,
    organization_id: str,
    agent_id: str | None,
    agent_name: str | None,
    provider: str,
    estimated_input_tokens: int,
    organization_daily_limit: int,
    max_calls_per_workflow: int | None,
    max_tokens_per_call: int | None,
    max_tokens_per_workflow: int | None,
    ttl_seconds: int,
) -> TokenReservation:
    now = datetime.now(UTC)
    now_iso = now.isoformat()
    today = now.date().isoformat()
    expires_at = now + timedelta(seconds=max(1, ttl_seconds))

    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            UPDATE token_reservations
            SET status = 'expired', updated_at = ?
            WHERE status = 'active' AND expires_at <= ?
            """,
            (now_iso, now_iso),
        )
        organization_row = connection.execute(
            """
            SELECT
                (
                    SELECT COALESCE(SUM(total_tokens), 0)
                    FROM model_invocations
                    WHERE organization_id = ?
                      AND substr(created_at, 1, 10) = ?
                ) + (
                    SELECT COALESCE(SUM(reserved_tokens), 0)
                    FROM token_reservations
                    WHERE organization_id = ?
                      AND status = 'active'
                      AND expires_at > ?
                ) AS committed_tokens
            """,
            (organization_id, today, organization_id, now_iso),
        ).fetchone()
        organization_used = int(organization_row["committed_tokens"])
        organization_remaining = organization_daily_limit - organization_used
        if organization_remaining <= estimated_input_tokens:
            raise TokenBudgetReservationDenied("organization")

        workflow_used = 0
        workflow_calls = 0
        if context_id is not None and agent_name is not None:
            workflow_row = connection.execute(
                """
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM model_invocations
                        WHERE context_id = ? AND agent_name = ?
                    ) + (
                        SELECT COUNT(*)
                        FROM token_reservations
                        WHERE context_id = ?
                          AND agent_name = ?
                          AND status = 'active'
                          AND expires_at > ?
                    ) AS committed_calls,
                    (
                        SELECT COALESCE(SUM(total_tokens), 0)
                        FROM model_invocations
                        WHERE context_id = ? AND agent_name = ?
                    ) + (
                        SELECT COALESCE(SUM(reserved_tokens), 0)
                        FROM token_reservations
                        WHERE context_id = ?
                          AND agent_name = ?
                          AND status = 'active'
                          AND expires_at > ?
                    ) AS committed_tokens
                """,
                (
                    context_id,
                    agent_name,
                    context_id,
                    agent_name,
                    now_iso,
                    context_id,
                    agent_name,
                    context_id,
                    agent_name,
                    now_iso,
                ),
            ).fetchone()
            workflow_calls = int(workflow_row["committed_calls"])
            workflow_used = int(workflow_row["committed_tokens"])

        if (
            max_calls_per_workflow is not None
            and workflow_calls >= max_calls_per_workflow
        ):
            raise TokenBudgetReservationDenied("workflow_calls")
        if (
            max_tokens_per_call is not None
            and estimated_input_tokens >= max_tokens_per_call
        ):
            raise TokenBudgetReservationDenied("per_call")

        limits = [organization_remaining]
        if max_tokens_per_call is not None:
            limits.append(max_tokens_per_call)
        if max_tokens_per_workflow is not None:
            workflow_remaining = max_tokens_per_workflow - workflow_used
            if workflow_remaining <= estimated_input_tokens:
                raise TokenBudgetReservationDenied("workflow_tokens")
            limits.append(workflow_remaining)

        reserved_tokens = min(limits)
        if reserved_tokens <= estimated_input_tokens:
            raise TokenBudgetReservationDenied("organization")

        reservation = TokenReservation(
            id=str(uuid4()),
            request_id=request_id,
            context_id=context_id,
            organization_id=organization_id,
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            estimated_input_tokens=estimated_input_tokens,
            reserved_tokens=reserved_tokens,
            expires_at=expires_at,
            created_at=now,
        )
        connection.execute(
            """
            INSERT INTO token_reservations (
                id, request_id, context_id, organization_id, agent_id,
                agent_name, provider, estimated_input_tokens, reserved_tokens,
                actual_tokens, status, expires_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', ?, ?, ?)
            """,
            (
                reservation.id,
                reservation.request_id,
                reservation.context_id,
                reservation.organization_id,
                reservation.agent_id,
                reservation.agent_name,
                reservation.provider,
                reservation.estimated_input_tokens,
                reservation.reserved_tokens,
                reservation.expires_at.isoformat(),
                reservation.created_at.isoformat(),
                reservation.created_at.isoformat(),
            ),
        )
    return reservation


def settle_token_reservation(
    reservation_id: str,
    *,
    actual_tokens: int,
) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as connection:
        connection.execute(
            """
            UPDATE token_reservations
            SET actual_tokens = ?, status = 'settled', updated_at = ?
            WHERE id = ? AND status = 'active'
            """,
            (max(0, actual_tokens), now, reservation_id),
        )


def release_token_reservation(reservation_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as connection:
        connection.execute(
            """
            UPDATE token_reservations
            SET status = 'released', updated_at = ?
            WHERE id = ? AND status = 'active'
            """,
            (now, reservation_id),
        )


def active_token_reservations(
    *,
    organization_id: str,
    context_id: str | None = None,
    agent_name: str | None = None,
) -> dict[str, int]:
    now = datetime.now(UTC).isoformat()
    conditions = [
        "organization_id = ?",
        "status = 'active'",
        "expires_at > ?",
    ]
    parameters: list[object] = [organization_id, now]
    if context_id is not None:
        conditions.append("context_id = ?")
        parameters.append(context_id)
    if agent_name is not None:
        conditions.append("agent_name = ?")
        parameters.append(agent_name)
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS calls,
                COALESCE(SUM(reserved_tokens), 0) AS reserved_tokens
            FROM token_reservations
            WHERE {' AND '.join(conditions)}
            """,
            tuple(parameters),
        ).fetchone()
    return {
        "calls": int(row["calls"]),
        "reserved_tokens": int(row["reserved_tokens"]),
    }
