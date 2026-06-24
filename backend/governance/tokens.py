from __future__ import annotations

from dataclasses import dataclass

from backend.config.settings import settings
from backend.governance.context import (
    AgentExecutionContext,
    RequestContext,
)
from backend.governance.gateway import GatewayLimitExceeded
from backend.governance.policy import AgentPolicy, AgentPolicyDenied
from backend.storage.observability import token_usage
from backend.storage.token_governance import (
    TokenBudgetReservationDenied,
    TokenReservation,
    active_token_reservations,
    release_token_reservation,
    reserve_token_budget,
    settle_token_reservation,
)


@dataclass(frozen=True)
class TokenBudgetStatus:
    organization_id: str
    context_id: str | None
    agent_name: str | None
    used_tokens: int
    reserved_tokens: int
    limit_tokens: int
    remaining_tokens: int
    used_calls: int
    reserved_calls: int
    limit_calls: int | None

    def as_dict(self) -> dict[str, int | str | None]:
        return {
            "organization_id": self.organization_id,
            "context_id": self.context_id,
            "agent_name": self.agent_name,
            "used_tokens": self.used_tokens,
            "reserved_tokens": self.reserved_tokens,
            "limit_tokens": self.limit_tokens,
            "remaining_tokens": self.remaining_tokens,
            "used_calls": self.used_calls,
            "reserved_calls": self.reserved_calls,
            "limit_calls": self.limit_calls,
        }


def reserve_model_tokens(
    *,
    request_context: RequestContext | None,
    execution: AgentExecutionContext | None,
    policy: AgentPolicy | None,
    context_id: str | None,
    agent_name: str | None,
    provider: str,
    estimated_input_tokens: int,
) -> TokenReservation:
    organization_id = (
        request_context.organization_id if request_context else "local"
    )
    try:
        return reserve_token_budget(
            request_id=(
                request_context.request_id if request_context else None
            ),
            context_id=context_id,
            organization_id=organization_id,
            agent_id=execution.agent_id if execution else None,
            agent_name=agent_name,
            provider=provider,
            estimated_input_tokens=estimated_input_tokens,
            organization_daily_limit=settings.organization_daily_token_quota,
            max_calls_per_workflow=(
                policy.max_model_calls_per_workflow if policy else None
            ),
            max_tokens_per_call=(
                policy.max_tokens_per_call
                if policy
                else settings.agent_max_tokens_per_call
            ),
            max_tokens_per_workflow=(
                policy.max_tokens_per_workflow if policy else None
            ),
            ttl_seconds=settings.token_reservation_ttl_seconds,
        )
    except TokenBudgetReservationDenied as exc:
        if exc.scope == "organization":
            raise GatewayLimitExceeded(
                "Organization daily model-token quota exceeded"
            ) from exc
        if exc.scope == "workflow_calls":
            raise AgentPolicyDenied(
                f"Agent '{agent_name}' exceeded its workflow model-call budget"
            ) from exc
        if exc.scope == "per_call":
            raise AgentPolicyDenied(
                f"Agent '{agent_name}' prompt exceeds its per-call token budget"
            ) from exc
        raise AgentPolicyDenied(
            f"Agent '{agent_name}' exceeded its workflow token budget"
        ) from exc


def settle_model_tokens(
    reservation: TokenReservation,
    *,
    actual_tokens: int,
) -> None:
    settle_token_reservation(
        reservation.id,
        actual_tokens=actual_tokens,
    )


def release_model_tokens(reservation: TokenReservation) -> None:
    release_token_reservation(reservation.id)


def token_budget_status(
    *,
    organization_id: str,
    context_id: str | None = None,
    agent_name: str | None = None,
    policy: AgentPolicy | None = None,
) -> TokenBudgetStatus:
    usage = token_usage(
        organization_id=organization_id,
        context_id=context_id,
        agent_name=agent_name,
        today_only=context_id is None,
    )
    reservations = active_token_reservations(
        organization_id=organization_id,
        context_id=context_id,
        agent_name=agent_name,
    )
    limit_tokens = (
        policy.max_tokens_per_workflow
        if context_id is not None and policy is not None
        else settings.organization_daily_token_quota
    )
    committed = (
        int(usage["total_tokens"]) + reservations["reserved_tokens"]
    )
    return TokenBudgetStatus(
        organization_id=organization_id,
        context_id=context_id,
        agent_name=agent_name,
        used_tokens=int(usage["total_tokens"]),
        reserved_tokens=reservations["reserved_tokens"],
        limit_tokens=limit_tokens,
        remaining_tokens=max(0, limit_tokens - committed),
        used_calls=int(usage["calls"]),
        reserved_calls=reservations["calls"],
        limit_calls=(
            policy.max_model_calls_per_workflow if policy else None
        ),
    )
