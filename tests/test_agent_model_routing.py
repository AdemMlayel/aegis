from __future__ import annotations

from fastapi.testclient import TestClient

from backend.config.settings import settings
from backend.embeddings import embedding_provider_registry
from backend.graph.state import (
    AgentModelRouteBlock,
    IntelligenceConfigBlock,
    TestContext as WorkflowContext,
    TicketData,
)
from backend.graph.workflow import run_workflow
from backend.intelligence.context import search_knowledge_for_ticket
from backend.llm.base import LLMResponse
from backend.llm.ollama import OllamaLLMProvider
from backend.main import app


def test_agent_model_catalog_exposes_recommendations_and_deterministic_boundaries() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/intelligence/agent-model-profiles")

    assert response.status_code == 200
    body = response.json()
    agents = {item["agent_name"]: item for item in body["agents"]}
    assert agents["RequirementAgent"]["recommended_mode"] == "external"
    assert agents["CoveragePlannerAgent"]["recommended_mode"] == "external"
    assert agents["TestCaseGeneratorAgent"]["recommended_mode"] == "external"
    assert agents["ReportGeneratorAgent"]["recommended_mode"] == "local"
    assert agents["AutomationGeneratorAgent"]["uses_llm"] is False
    assert agents["ValidatorAgent"]["uses_llm"] is False
    assert body["embedding"] == {
        "recommended_mode": "local",
        "recommended_provider": "ollama_nomic_embed_text",
        "recommended_model": "nomic-embed-text",
        "fallback_provider": "local_hash_embeddings",
        "rationale": body["embedding"]["rationale"],
    }


def test_workflow_routes_each_llm_agent_independently() -> None:
    client = TestClient(app)
    routes = {
        "RequirementAgent": {
            "provider": "mock_llm",
            "model": "requirement-specialist",
        },
        "CoveragePlannerAgent": {
            "provider": "mock_llm",
            "model": "reasoning-specialist",
        },
        "TestCaseGeneratorAgent": {
            "provider": "mock_llm",
            "model": "generation-specialist",
        },
        "ReportGeneratorAgent": {
            "provider": "mock_llm",
            "model": "report-specialist",
        },
    }

    response = client.post(
        "/api/v1/workflows/start-from-demo-ticket",
        json={
            "created_by": "routing-test",
            "ticket_id": "DEMO-TELCO-IMS-001",
            "intelligence": {
                "llm_provider": "mock_llm",
                "embedding_provider": "local_hash_embeddings",
                "agent_routes": routes,
            },
        },
    )

    assert response.status_code == 202
    context = response.json()["context"]
    assert context["intelligence_config"]["agent_routes"] == routes
    assert context["intelligence_trace"]["configured_agent_routes"] == routes
    calls = {
        call["agent_name"]: call
        for call in context["intelligence_trace"]["llm_calls"]
    }
    assert calls["RequirementAgent"]["model"] == "requirement-specialist"
    assert calls["CoveragePlannerAgent"]["model"] == "reasoning-specialist"
    assert calls["TestCaseGeneratorAgent"]["model"] == "generation-specialist"
    assert calls["ReportGeneratorAgent"]["model"] == "report-specialist"
    assert all(call["model_role"] == "manual_override" for call in calls.values())


def test_workflow_rejects_model_route_for_deterministic_agent() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start-from-demo-ticket",
        json={
            "created_by": "routing-test",
            "ticket_id": "DEMO-TELCO-IMS-001",
            "intelligence": {
                "agent_routes": {
                    "ValidatorAgent": {
                        "provider": "mock_llm",
                    }
                }
            },
        },
    )

    assert response.status_code == 400
    assert "ValidatorAgent" in response.json()["detail"]


def test_external_provider_metadata_requires_server_side_configuration(
    monkeypatch,
) -> None:
    client = TestClient(app)
    monkeypatch.setattr(settings, "external_connectors_enabled", False)

    disabled = client.get("/api/v1/intelligence/llm-providers")

    external = next(
        item for item in disabled.json() if item["name"] == "openai_compatible"
    )
    assert external["selectable"] is False
    assert external["configuration_status"] == "disabled"
    assert "AEGISQA_OPENAI_COMPATIBLE_API_KEY" in external["configuration_keys"]

    monkeypatch.setattr(settings, "external_connectors_enabled", True)
    monkeypatch.setattr(
        settings,
        "openai_compatible_base_url",
        "https://models.example.test/v1",
    )
    monkeypatch.setattr(settings, "openai_compatible_api_key", "test-key")

    ready = client.get("/api/v1/intelligence/llm-providers")

    external = next(
        item for item in ready.json() if item["name"] == "openai_compatible"
    )
    assert external["selectable"] is True
    assert external["configuration_status"] == "ready"


def test_ollama_embedding_model_override_is_used(monkeypatch) -> None:
    requests: list[dict[str, object]] = []

    def fake_post_json(path, payload, *, timeout):
        requests.append(payload)
        return {"embedding": [0.1, 0.2, 0.3]}

    monkeypatch.setattr("backend.embeddings.ollama._post_json", fake_post_json)
    provider = embedding_provider_registry.create(
        "ollama_nomic_embed_text",
        model_override="nomic-embed-text",
    )

    response = provider.embed("private ticket text")

    assert requests == [
        {"model": "nomic-embed-text", "prompt": "private ticket text"}
    ]
    assert response.model == "nomic-embed-text"


def test_workflow_retrieval_uses_selected_embedding_model(monkeypatch) -> None:
    requests: list[dict[str, object]] = []

    def fake_post_json(path, payload, *, timeout):
        requests.append(payload)
        return {"embedding": [0.1, 0.2, 0.3]}

    monkeypatch.setattr("backend.embeddings.ollama._post_json", fake_post_json)
    context = WorkflowContext(
        created_by="routing-test",
        intelligence_config=IntelligenceConfigBlock(
            embedding_provider="ollama_nomic_embed_text",
            embedding_model="nomic-embed-text",
        ),
    )
    ticket = TicketData(
        id="ROUTING-EMBED-1",
        title="Private retrieval",
        description="Keep ticket text in local embeddings.",
        labels=["privacy", "rag"],
    )

    results = search_knowledge_for_ticket(ticket, context=context)

    assert results
    assert requests
    assert {
        request["model"]
        for request in requests
    } == {"nomic-embed-text"}


def test_successful_selected_models_contribute_visible_agent_guidance(
    monkeypatch,
) -> None:
    def fake_complete(self, **kwargs):
        return LLMResponse(
            provider="ollama",
            model=kwargs["model_override"] or "local-role-model",
            prompt_name=kwargs["prompt_name"],
            prompt_version=kwargs["prompt_version"],
            text=f"Guidance from {kwargs['prompt_name']}",
            deterministic=False,
        )

    monkeypatch.setattr(OllamaLLMProvider, "complete", fake_complete)
    routes = {
        agent_name: AgentModelRouteBlock(provider="ollama")
        for agent_name in (
            "RequirementAgent",
            "CoveragePlannerAgent",
            "TestCaseGeneratorAgent",
            "ReportGeneratorAgent",
        )
    }
    result = run_workflow(
        WorkflowContext(
            created_by="routing-test",
            intelligence_config=IntelligenceConfigBlock(
                llm_provider="mock_llm",
                agent_routes=routes,
            ),
            ticket=TicketData(
                id="ROUTING-GUIDANCE-1",
                title="Use routed model guidance",
                description="Generate evidence-backed QA output.",
                acceptance_criteria=["Visible outputs include selected model guidance"],
                priority="high",
                labels=["routing", "ai"],
            ),
        )
    )

    assert result.requirement_analysis is not None
    assert result.requirement_analysis.llm_summary == (
        "Guidance from requirement_analysis_v1"
    )
    assert result.coverage_plan is not None
    assert "Guidance from coverage_planning_v1" in result.coverage_plan.risk_rationale[-1]
    assert result.test_cases
    assert "Guidance from test_case_generation_v1" in result.test_cases[0].generation_notes[-1]
    assert result.reports is not None
    assert result.reports.summary == "Guidance from report_generation_v1"
