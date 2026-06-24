from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.governance.gateway import circuit_breakers
from backend.governance.policy import agent_policy_engine
from backend.governance.tokens import token_budget_status
from backend.observability import operational_health
from backend.security import Capability, Principal, require_capability
from backend.storage.observability import (
    AgentInvocation,
    ModelInvocation,
    list_agent_invocations,
    list_model_invocations,
    observability_summary,
    token_usage,
)


router = APIRouter(tags=["governance"])


class AgentGovernanceCatalogResponse(BaseModel):
    agents: list[dict[str, object]]


class ObservabilitySummaryResponse(BaseModel):
    date: str
    requests: dict[str, int | float]
    models: dict[str, int | float]
    agents: dict[str, int | float]
    provider_circuits: list[dict[str, object]]


class ModelInvocationListResponse(BaseModel):
    invocations: list[ModelInvocation]


class AgentInvocationListResponse(BaseModel):
    invocations: list[AgentInvocation]


class TokenBudgetStatusResponse(BaseModel):
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


@router.get(
    "/governance/agents",
    response_model=AgentGovernanceCatalogResponse,
)
def read_agent_governance_catalog(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
) -> AgentGovernanceCatalogResponse:
    return AgentGovernanceCatalogResponse(
        agents=agent_policy_engine.catalog()
    )


@router.get(
    "/observability/summary",
    response_model=ObservabilitySummaryResponse,
)
def read_observability_summary(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
) -> ObservabilitySummaryResponse:
    summary = observability_summary(
        organization_id=principal.organization_id,
    )
    return ObservabilitySummaryResponse(
        **summary,
        provider_circuits=circuit_breakers.status(),
    )


@router.get(
    "/observability/model-invocations",
    response_model=ModelInvocationListResponse,
)
def read_model_invocations(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
    context_id: str | None = None,
    agent_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> ModelInvocationListResponse:
    return ModelInvocationListResponse(
        invocations=list_model_invocations(
            organization_id=principal.organization_id,
            context_id=context_id,
            agent_name=agent_name,
            limit=limit,
        )
    )


@router.get(
    "/observability/agent-invocations",
    response_model=AgentInvocationListResponse,
)
def read_agent_invocations(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
    context_id: str | None = None,
    agent_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> AgentInvocationListResponse:
    return AgentInvocationListResponse(
        invocations=list_agent_invocations(
            organization_id=principal.organization_id,
            context_id=context_id,
            agent_name=agent_name,
            limit=limit,
        )
    )


@router.get("/observability/token-usage")
def read_token_usage(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
    context_id: str | None = None,
    agent_name: str | None = None,
) -> dict[str, int | float]:
    return token_usage(
        organization_id=principal.organization_id,
        context_id=context_id,
        agent_name=agent_name,
    )


@router.get(
    "/observability/token-budget",
    response_model=TokenBudgetStatusResponse,
)
def read_token_budget(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
    context_id: str | None = None,
    agent_name: str | None = None,
) -> TokenBudgetStatusResponse:
    policy = (
        agent_policy_engine.policy_for(agent_name)
        if agent_name is not None
        else None
    )
    status = token_budget_status(
        organization_id=principal.organization_id,
        context_id=context_id,
        agent_name=agent_name,
        policy=policy,
    )
    return TokenBudgetStatusResponse(**status.as_dict())


@router.get("/observability/health")
def read_operational_health(
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_AUDIT)),
    ],
) -> dict[str, object]:
    return operational_health(
        organization_id=principal.organization_id,
    )
