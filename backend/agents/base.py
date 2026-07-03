from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
from typing import ClassVar

from backend.config.settings import settings
from backend.governance.context import (
    agent_execution_scope,
    current_request_context,
)
from backend.governance.policy import (
    AgentPolicyDenied,
    RiskTier,
    agent_policy_engine,
)
from backend.graph.state import TestContext
from backend.storage.observability import (
    AgentInvocation,
    save_agent_invocation,
)


@dataclass(frozen=True)
class AgentSpec:
    name: str
    skills: tuple[str, ...] = ()
    description: str = ""
    version: str = "0.1.0"
    owner: str = "qa-platform"
    risk_tier: RiskTier = "medium"
    uses_llm: bool = False
    require_human_approval: bool = False
    agent_id: str = ""


class BaseAgent(ABC):
    spec: ClassVar[AgentSpec] = AgentSpec(name="base")

    def __init__(self, *, skill_registry: object | None = None) -> None:
        self.skill_registry = skill_registry

    @abstractmethod
    def run(self, context: TestContext) -> TestContext:
        raise NotImplementedError


class AgentRegistrationError(ValueError):
    pass


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(
        self,
        *,
        name: str,
        skills: Iterable[str] = (),
        description: str = "",
        version: str = "0.1.0",
        owner: str = "qa-platform",
        risk_tier: RiskTier = "medium",
        uses_llm: bool = False,
        require_human_approval: bool = False,
    ):
        normalized_name = _require_name(name)
        normalized_skills = tuple(skills)
        identity = agent_policy_engine.register(
            name=normalized_name,
            version=version,
            skills=normalized_skills,
            owner=owner,
            risk_tier=risk_tier,
            uses_llm=uses_llm,
            require_human_approval=require_human_approval,
        )
        spec = AgentSpec(
            name=normalized_name,
            skills=normalized_skills,
            description=description,
            version=version,
            owner=owner,
            risk_tier=risk_tier,
            uses_llm=uses_llm,
            require_human_approval=require_human_approval,
            agent_id=identity.agent_id,
        )

        def decorator(agent_cls: type[BaseAgent]) -> type[BaseAgent]:
            if not issubclass(agent_cls, BaseAgent):
                raise TypeError("Registered agents must inherit from BaseAgent")
            if normalized_name in self._agents:
                raise AgentRegistrationError(
                    f"Agent '{normalized_name}' is already registered"
                )
            agent_cls.spec = spec
            original_run = agent_cls.run

            @wraps(original_run)
            def governed_run(
                self: BaseAgent,
                context: TestContext,
            ) -> TestContext:
                started = perf_counter()
                request_context = current_request_context()
                # W7: enforce the previously-inert require_human_approval flag
                # when the operator opts in. An approval-required agent may then
                # only run once the workflow context carries a granted approval.
                if (
                    settings.enforce_agent_human_approval
                    and spec.require_human_approval
                    and (context.approval is None or context.approval.status != "approved")
                ):
                    raise AgentPolicyDenied(
                        f"Agent '{normalized_name}' requires human approval; "
                        "the workflow context has no granted approval "
                        f"(status="
                        f"{context.approval.status if context.approval else 'none'})"
                    )
                with agent_execution_scope(
                    agent_id=identity.agent_id,
                    agent_name=normalized_name,
                    context_id=context.context_id,
                ):
                    try:
                        result = original_run(self, context)
                    except Exception as exc:
                        save_agent_invocation(
                            AgentInvocation(
                                request_id=(
                                    request_context.request_id
                                    if request_context
                                    else None
                                ),
                                context_id=context.context_id,
                                organization_id=(
                                    request_context.organization_id
                                    if request_context
                                    else "local"
                                ),
                                actor=(
                                    request_context.actor
                                    if request_context
                                    else "system"
                                ),
                                agent_id=identity.agent_id,
                                agent_name=normalized_name,
                                status="failed",
                                duration_ms=round(
                                    (perf_counter() - started) * 1000
                                ),
                                error_type=type(exc).__name__,
                            )
                        )
                        raise
                    save_agent_invocation(
                        AgentInvocation(
                            request_id=(
                                request_context.request_id
                                if request_context
                                else None
                            ),
                            context_id=context.context_id,
                            organization_id=(
                                request_context.organization_id
                                if request_context
                                else "local"
                            ),
                            actor=(
                                request_context.actor
                                if request_context
                                else "system"
                            ),
                            agent_id=identity.agent_id,
                            agent_name=normalized_name,
                            status="success",
                            duration_ms=round(
                                (perf_counter() - started) * 1000
                            ),
                        )
                    )
                    return result

            agent_cls.run = governed_run
            self._agents[normalized_name] = agent_cls
            return agent_cls

        return decorator

    def get(self, name: str) -> type[BaseAgent]:
        normalized_name = _require_name(name)
        try:
            return self._agents[normalized_name]
        except KeyError as exc:
            # N4: raise the typed registration error, not a bare KeyError.
            raise AgentRegistrationError(
                f"Agent '{normalized_name}' is not registered"
            ) from exc

    def create(self, name: str, **kwargs: object) -> BaseAgent:
        return self.get(name)(**kwargs)

    def has(self, name: str) -> bool:
        return _require_name(name) in self._agents

    def list_specs(self) -> list[AgentSpec]:
        return sorted(
            (agent_cls.spec for agent_cls in self._agents.values()),
            key=lambda spec: spec.name,
        )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise AgentRegistrationError("Registry names cannot be empty")
    return normalized_name


agent_registry = AgentRegistry()
