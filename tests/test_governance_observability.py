from __future__ import annotations

import asyncio
import sqlite3
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agents import AgentRegistry, BaseAgent
from backend.config.settings import settings
from backend.governance.context import AgentExecutionContext
from backend.governance.gateway import (
    CircuitBreakerRegistry,
    CircuitOpenError,
    gateway_limiter,
)
from backend.governance.policy import (
    AgentPolicyDenied,
    AgentPolicyEngine,
)
from backend.graph.state import TestContext as WorkflowContext
from backend.main import app
from backend.observability import install_gateway_middleware
from backend.skills import BaseSkill, SkillRegistry
from backend.storage.observability import (
    list_agent_invocations,
    list_model_invocations,
)
from backend.storage.database import SQLITE_DB_PATH
from backend.storage.token_governance import (
    TokenBudgetReservationDenied,
    active_token_reservations,
    release_token_reservation,
    reserve_token_budget,
)
from backend.tools import BaseTool, ToolRegistry


def test_governance_catalog_exposes_agent_identity_and_policy() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/governance/agents")

    assert response.status_code == 200
    catalog = {
        item["identity"]["name"]: item
        for item in response.json()["agents"]
    }
    requirement = catalog["RequirementAgent"]
    assert requirement["identity"]["agent_id"] == (
        "aegisqa.agent.RequirementAgent"
    )
    assert requirement["identity"]["service_account"] == (
        "svc:RequirementAgent"
    )
    assert requirement["policy"]["allowed_skills"] == [
        "AnalyzeRequirementSkill"
    ]
    assert "openai_compatible" in requirement["policy"]["allowed_providers"]
    assert catalog["ValidatorAgent"]["policy"]["allowed_providers"] == []
    assert (
        catalog["ValidatorAgent"]["policy"]["require_human_approval"]
        is True
    )


def test_agent_policy_blocks_undeclared_skill() -> None:
    agent_registry = AgentRegistry()
    skill_registry = SkillRegistry()
    suffix = uuid4().hex[:8]
    allowed_skill_name = f"AllowedSkill{suffix}"
    denied_skill_name = f"DeniedSkill{suffix}"
    agent_name = f"PolicyAgent{suffix}"

    @skill_registry.register(name=allowed_skill_name)
    class AllowedSkill(BaseSkill):
        def execute(self, context: WorkflowContext) -> WorkflowContext:
            return context

    @skill_registry.register(name=denied_skill_name)
    class DeniedSkill(BaseSkill):
        def execute(self, context: WorkflowContext) -> WorkflowContext:
            return context

    @agent_registry.register(
        name=agent_name,
        skills=[allowed_skill_name],
    )
    class PolicyAgent(BaseAgent):
        def run(self, context: WorkflowContext) -> WorkflowContext:
            skill = self.skill_registry.create(denied_skill_name)
            return skill.execute(context)

    agent = agent_registry.create(
        agent_name,
        skill_registry=skill_registry,
    )

    with pytest.raises(
        AgentPolicyDenied,
        match="cannot execute skill",
    ):
        agent.run(WorkflowContext(created_by="pytest"))


def test_deterministic_agent_policy_blocks_model_provider() -> None:
    engine = AgentPolicyEngine()
    suffix = uuid4().hex[:8]
    agent_name = f"DeterministicAgent{suffix}"
    identity = engine.register(
        name=agent_name,
        version="1.0.0",
        skills=("DeterministicSkill",),
        owner="pytest",
        risk_tier="high",
        uses_llm=False,
        require_human_approval=True,
    )
    execution = AgentExecutionContext(
        agent_id=identity.agent_id,
        agent_name=agent_name,
        context_id="test-context",
    )

    with pytest.raises(
        AgentPolicyDenied,
        match="cannot use provider",
    ):
        engine.authorize_provider(execution, "ollama")


def test_agent_policy_blocks_tool_not_declared_by_skill() -> None:
    agent_registry = AgentRegistry()
    skill_registry = SkillRegistry()
    tool_registry = ToolRegistry()
    suffix = uuid4().hex[:8]
    allowed_tool_name = f"AllowedTool{suffix}"
    denied_tool_name = f"DeniedTool{suffix}"
    skill_name = f"GovernedSkill{suffix}"
    agent_name = f"GovernedAgent{suffix}"

    @tool_registry.register(name=allowed_tool_name)
    class AllowedTool(BaseTool):
        def invoke(self, **kwargs: object) -> object:
            return kwargs

    @tool_registry.register(name=denied_tool_name)
    class DeniedTool(BaseTool):
        def invoke(self, **kwargs: object) -> object:
            return kwargs

    @skill_registry.register(
        name=skill_name,
        tools=[allowed_tool_name],
    )
    class GovernedSkill(BaseSkill):
        def __init__(self) -> None:
            super().__init__(tool_registry=tool_registry)

        def execute(self, context: WorkflowContext) -> WorkflowContext:
            self.tool_registry.execute(denied_tool_name)
            return context

    @agent_registry.register(name=agent_name, skills=[skill_name])
    class GovernedAgent(BaseAgent):
        def run(self, context: WorkflowContext) -> WorkflowContext:
            skill = self.skill_registry.create(skill_name)
            return skill.execute(context)

    agent = agent_registry.create(
        agent_name,
        skill_registry=skill_registry,
    )

    with pytest.raises(
        AgentPolicyDenied,
        match="cannot execute tool",
    ):
        agent.run(WorkflowContext(created_by="pytest"))


def test_workflow_telemetry_correlates_request_agent_and_model() -> None:
    client = TestClient(app)
    request_id = f"req-{uuid4()}"
    organization = f"org-{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/workflows/start",
        headers={
            "X-Request-ID": request_id,
            "X-Aegis-User": "telemetry-tester",
            "X-Aegis-Role": "qa_lead",
            "X-Aegis-Organization": organization,
        },
        json={
            "created_by": "telemetry-tester",
            "ticket": {
                "id": f"TELEMETRY-{uuid4().hex[:8]}",
                "title": "Governed model telemetry",
                "description": "Record every governed execution boundary.",
                "acceptance_criteria": ["Telemetry is correlated"],
                "priority": "high",
                "labels": ["governance"],
            },
        },
    )

    assert response.status_code == 202
    assert response.headers["X-Request-ID"] == request_id
    context_id = response.json()["context"]["context_id"]
    agents = list_agent_invocations(context_id=context_id)
    models = list_model_invocations(context_id=context_id)
    assert agents
    assert models
    assert {item.request_id for item in agents} == {request_id}
    assert {item.request_id for item in models} == {request_id}
    assert all(item.organization_id == organization for item in models)
    assert all(item.total_tokens > 0 for item in models)
    assert {item.agent_name for item in models} >= {
        "RequirementAgent",
        "CoveragePlannerAgent",
        "TestCaseGeneratorAgent",
        "ReportGeneratorAgent",
    }

    summary = client.get(
        "/api/v1/observability/summary",
        headers={
            "X-Aegis-User": "telemetry-tester",
            "X-Aegis-Role": "qa_lead",
            "X-Aegis-Organization": organization,
        },
    )
    assert summary.status_code == 200
    assert summary.json()["agents"]["total"] >= len(agents)
    assert summary.json()["models"]["total_tokens"] >= sum(
        item.total_tokens for item in models
    )


def test_gateway_rate_limit_and_daily_quota(monkeypatch) -> None:
    gateway_limiter.reset()
    test_app = FastAPI()
    install_gateway_middleware(test_app)

    @test_app.get("/limited")
    def limited() -> dict[str, bool]:
        return {"ok": True}

    organization = f"rate-{uuid4().hex[:8]}"
    headers = {
        "X-Aegis-User": "rate-user",
        "X-Aegis-Organization": organization,
    }
    monkeypatch.setattr(settings, "gateway_requests_per_minute", 1)
    monkeypatch.setattr(settings, "gateway_daily_request_quota", 100)
    client = TestClient(test_app)

    assert client.get("/limited", headers=headers).status_code == 200
    assert client.get("/limited", headers=headers).status_code == 429

    gateway_limiter.reset()
    monkeypatch.setattr(settings, "gateway_daily_request_quota", 0)
    quota_response = client.get(
        "/limited",
        headers={
            "X-Aegis-User": "quota-user",
            "X-Aegis-Organization": f"quota-{uuid4().hex[:8]}",
        },
    )
    assert quota_response.status_code == 429
    assert "daily request quota" in quota_response.json()["detail"]


def test_gateway_timeout(monkeypatch) -> None:
    gateway_limiter.reset()
    test_app = FastAPI()
    install_gateway_middleware(test_app)

    @test_app.get("/slow")
    async def slow() -> dict[str, bool]:
        await asyncio.sleep(0.05)
        return {"ok": True}

    monkeypatch.setattr(settings, "gateway_request_timeout_seconds", 0.001)
    monkeypatch.setattr(settings, "gateway_requests_per_minute", 100)
    monkeypatch.setattr(settings, "gateway_daily_request_quota", 100)
    response = TestClient(test_app).get(
        "/slow",
        headers={
            "X-Aegis-Organization": f"timeout-{uuid4().hex[:8]}"
        },
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "Gateway request timed out"


def test_model_token_quota_blocks_workflow_before_provider_call(
    monkeypatch,
) -> None:
    gateway_limiter.reset()
    monkeypatch.setattr(settings, "organization_daily_token_quota", 0)
    response = TestClient(app).post(
        "/api/v1/workflows/start",
        headers={
            "X-Aegis-User": "quota-model-user",
            "X-Aegis-Role": "qa_lead",
            "X-Aegis-Organization": f"model-quota-{uuid4().hex[:8]}",
        },
        json={
            "created_by": "quota-model-user",
            "ticket": {
                "id": f"MODEL-QUOTA-{uuid4().hex[:8]}",
                "title": "Model quota enforcement",
                "description": "The model call must not exceed its quota.",
                "acceptance_criteria": ["Quota is enforced"],
                "priority": "medium",
                "labels": ["governance"],
            },
        },
    )

    assert response.status_code == 429
    assert "model-token quota" in response.json()["detail"]


def test_provider_circuit_breaker_opens_and_resets(monkeypatch) -> None:
    registry = CircuitBreakerRegistry()
    monkeypatch.setattr(settings, "provider_circuit_failure_threshold", 2)
    monkeypatch.setattr(settings, "provider_circuit_reset_seconds", 60)

    registry.record_failure("provider-a")
    registry.before_call("provider-a")
    registry.record_failure("provider-a")

    with pytest.raises(CircuitOpenError):
        registry.before_call("provider-a")

    assert registry.status()[0]["state"] == "open"
    registry.reset()
    registry.before_call("provider-a")


def test_token_reservation_prevents_concurrent_overspend() -> None:
    organization = f"reservation-{uuid4().hex}"
    first = reserve_token_budget(
        request_id="request-1",
        context_id="context-1",
        organization_id=organization,
        agent_id="agent-1",
        agent_name="RequirementAgent",
        provider="mock_llm",
        estimated_input_tokens=10,
        organization_daily_limit=50,
        max_calls_per_workflow=3,
        max_tokens_per_call=50,
        max_tokens_per_workflow=50,
        ttl_seconds=60,
    )

    with pytest.raises(TokenBudgetReservationDenied) as exc_info:
        reserve_token_budget(
            request_id="request-2",
            context_id="context-1",
            organization_id=organization,
            agent_id="agent-1",
            agent_name="RequirementAgent",
            provider="mock_llm",
            estimated_input_tokens=10,
            organization_daily_limit=50,
            max_calls_per_workflow=3,
            max_tokens_per_call=50,
            max_tokens_per_workflow=50,
            ttl_seconds=60,
        )

    assert exc_info.value.scope == "organization"
    active = active_token_reservations(organization_id=organization)
    assert active == {"calls": 1, "reserved_tokens": 50}
    release_token_reservation(first.id)


def test_health_metrics_and_token_budget_endpoints() -> None:
    client = TestClient(app)

    assert client.get("/health/live").json()["status"] == "ok"
    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "ready"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "aegisqa_http_requests_total" in metrics.text
    assert "aegisqa_model_tokens_total" in metrics.text

    budget = client.get("/api/v1/observability/token-budget")
    assert budget.status_code == 200
    assert budget.json()["limit_tokens"] == (
        settings.organization_daily_token_quota
    )
    assert budget.json()["remaining_tokens"] >= 0

    health = client.get("/api/v1/observability/health")
    assert health.status_code == 200
    assert health.json()["status"] in {"healthy", "degraded"}


def test_duplicate_correlation_ids_do_not_overwrite_request_telemetry() -> None:
    request_id = f"duplicate-{uuid4()}"
    client = TestClient(app)

    client.get("/health/live", headers={"X-Request-ID": request_id})
    client.get("/health/live", headers={"X-Request-ID": request_id})

    with sqlite3.connect(SQLITE_DB_PATH) as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM request_observations
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()[0]

    assert count == 2
