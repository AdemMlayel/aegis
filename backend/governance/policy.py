from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from backend.config.settings import settings
from backend.governance.context import AgentExecutionContext


RiskTier = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    name: str
    version: str
    owner: str
    service_account: str
    trust_domain: str = "aegisqa.local"
    risk_tier: RiskTier = "medium"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AgentPolicy:
    agent_id: str
    allowed_skills: tuple[str, ...]
    allowed_providers: tuple[str, ...]
    max_model_calls_per_workflow: int
    max_tokens_per_call: int
    max_tokens_per_workflow: int
    require_human_approval: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class AgentPolicyDenied(PermissionError):
    pass


class AgentPolicyEngine:
    def __init__(self) -> None:
        self._identities: dict[str, AgentIdentity] = {}
        self._policies: dict[str, AgentPolicy] = {}

    def register(
        self,
        *,
        name: str,
        version: str,
        skills: tuple[str, ...],
        owner: str,
        risk_tier: RiskTier,
        uses_llm: bool,
        require_human_approval: bool,
    ) -> AgentIdentity:
        agent_id = f"aegisqa.agent.{name}"
        identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            version=version,
            owner=owner,
            service_account=f"svc:{name}",
            risk_tier=risk_tier,
        )
        providers = (
            ("mock_llm", "ollama", "openai_compatible")
            if uses_llm
            else ()
        )
        policy = AgentPolicy(
            agent_id=agent_id,
            allowed_skills=skills,
            allowed_providers=providers,
            max_model_calls_per_workflow=settings.agent_max_model_calls_per_workflow,
            max_tokens_per_call=settings.agent_max_tokens_per_call,
            max_tokens_per_workflow=settings.agent_max_tokens_per_workflow,
            require_human_approval=require_human_approval,
        )
        self._identities[name] = identity
        self._policies[name] = policy
        return identity

    def identity_for(self, agent_name: str) -> AgentIdentity:
        try:
            return self._identities[agent_name]
        except KeyError as exc:
            raise AgentPolicyDenied(
                f"Agent identity is not registered for '{agent_name}'"
            ) from exc

    def policy_for(self, agent_name: str) -> AgentPolicy:
        try:
            return self._policies[agent_name]
        except KeyError as exc:
            raise AgentPolicyDenied(
                f"Agent policy is not registered for '{agent_name}'"
            ) from exc

    def authorize_skill(
        self,
        execution: AgentExecutionContext | None,
        skill_name: str,
    ) -> None:
        if execution is None:
            return
        policy = self.policy_for(execution.agent_name)
        if skill_name not in policy.allowed_skills:
            raise AgentPolicyDenied(
                f"Agent '{execution.agent_name}' cannot execute skill "
                f"'{skill_name}'"
            )

    def authorize_tool(
        self,
        execution: AgentExecutionContext | None,
        tool_name: str,
    ) -> None:
        if execution is None:
            return
        if execution.skill_name is None:
            raise AgentPolicyDenied(
                f"Agent '{execution.agent_name}' attempted tool '{tool_name}' "
                "outside a governed skill"
            )
        self.authorize_skill(execution, execution.skill_name)
        if tool_name not in execution.allowed_tools:
            raise AgentPolicyDenied(
                f"Skill '{execution.skill_name}' cannot execute tool "
                f"'{tool_name}'"
            )

    def authorize_provider(
        self,
        execution: AgentExecutionContext | None,
        provider: str,
    ) -> AgentPolicy | None:
        if execution is None:
            return None
        policy = self.policy_for(execution.agent_name)
        if provider not in policy.allowed_providers:
            raise AgentPolicyDenied(
                f"Agent '{execution.agent_name}' cannot use provider "
                f"'{provider}'"
            )
        return policy

    def catalog(self) -> list[dict[str, object]]:
        return [
            {
                "identity": self._identities[name].as_dict(),
                "policy": self._policies[name].as_dict(),
            }
            for name in sorted(self._identities)
        ]


agent_policy_engine = AgentPolicyEngine()
