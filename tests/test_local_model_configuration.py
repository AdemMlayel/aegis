from __future__ import annotations

from fastapi.testclient import TestClient

from backend.config.settings import settings
from backend.embeddings import embedding_provider_registry
from backend.graph.state import (
    IntelligenceConfigBlock,
    TestContext as WorkflowContext,
    TicketData,
)
from backend.graph.workflow import run_workflow
from backend.intelligence.context import complete_with_configured_llm
from backend.llm.base import LLMResponse
from backend.llm.ollama import OllamaLLMProvider
from backend.llm.ollama_profiles import list_ollama_profiles
from backend.llm import llm_provider_registry
from backend.main import app


def test_local_model_providers_are_registered() -> None:
    assert llm_provider_registry.has("mock_llm")
    assert llm_provider_registry.has("ollama")
    assert llm_provider_registry.has("openai_compatible")
    assert embedding_provider_registry.has("local_hash_embeddings")
    assert embedding_provider_registry.has("ollama_nomic_embed_text")
    assert settings.default_llm_provider in {spec.name for spec in llm_provider_registry.list_specs()}
    assert settings.default_embedding_provider in {spec.name for spec in embedding_provider_registry.list_specs()}


def test_local_hash_embedding_is_deterministic() -> None:
    provider = embedding_provider_registry.create("local_hash_embeddings")
    first = provider.embed("money transfer regression")
    second = provider.embed("money transfer regression")
    assert first.vector == second.vector
    assert first.provider == "local_hash_embeddings"
    assert len(first.vector) == 32


def test_intelligence_model_endpoints_are_demo_safe() -> None:
    client = TestClient(app)

    llm_response = client.get("/api/v1/intelligence/llm-providers")
    assert llm_response.status_code == 200
    llm_names = {item["name"] for item in llm_response.json()}
    assert {"mock_llm", "ollama", "openai_compatible"} <= llm_names

    embedding_response = client.get("/api/v1/intelligence/embedding-providers")
    assert embedding_response.status_code == 200
    embedding_names = {item["name"] for item in embedding_response.json()}
    assert {"local_hash_embeddings", "ollama_nomic_embed_text"} <= embedding_names

    health_response = client.get("/api/v1/intelligence/ollama/health")
    assert health_response.status_code == 200
    body = health_response.json()
    assert "available" in body
    assert "message" in body
    assert "chat_model" in body
    assert "embedding_model" in body


def test_ollama_role_profiles_match_planned_local_stack() -> None:
    profiles = {profile.role: profile for profile in list_ollama_profiles()}

    assert profiles["main_rag"].model == "qwen3:3b"
    assert profiles["stable_baseline"].model == "llama3.1:8b"
    assert profiles["coding_repo_analysis"].model == "qwen3-coder"
    assert profiles["fast_testing"].model == "phi4-mini"
    assert profiles["fast_testing"].fallback_model == "gemma3:4b"
    assert profiles["reasoning"].model == "deepseek-r1:8b"
    assert profiles["reasoning"].fallback_model == "deepseek-r1:7b"
    assert profiles["rag_embedding"].model == "qwen3-embedding:0.6b"
    assert profiles["rag_embedding"].fallback_model == "nomic-embed-text"


def test_ollama_profile_endpoints_are_demo_safe(monkeypatch) -> None:
    client = TestClient(app)

    monkeypatch.setattr(
        "backend.llm.ollama_profiles.list_installed_ollama_models",
        lambda: (
            True,
            ["qwen3:3b", "llama3.1:8b", "qwen3-embedding:0.6b"],
            None,
        ),
    )

    profiles_response = client.get("/api/v1/intelligence/ollama/profiles")
    assert profiles_response.status_code == 200
    profiles_body = profiles_response.json()
    assert profiles_body["service_available"] is True
    assert {profile["role"] for profile in profiles_body["profiles"]} >= {
        "main_rag",
        "stable_baseline",
        "coding_repo_analysis",
        "fast_testing",
        "reasoning",
        "rag_embedding",
    }
    assert any(
        profile["role"] == "main_rag" and profile["installed"] is True
        for profile in profiles_body["profiles"]
    )
    assert any(
        route["prompt_name"] == "coverage_planning_v1"
        and route["role"] == "reasoning"
        for route in profiles_body["prompt_routes"]
    )

    monkeypatch.setattr(
        "backend.api.routes.intelligence.smoke_test_ollama_model_profiles",
        lambda roles=None, prompt="": [
            {
                "role": "main_rag",
                "model": "qwen3:3b",
                "kind": "chat",
                "available": True,
                "ok": True,
                "response_excerpt": "OK",
                "error": None,
            }
        ],
    )
    smoke_response = client.post(
        "/api/v1/intelligence/ollama/profiles/smoke-test",
        json={"roles": ["main_rag"]},
    )
    assert smoke_response.status_code == 200
    assert smoke_response.json()["results"][0]["ok"] is True


def test_ollama_prompt_stages_route_to_role_models(monkeypatch) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_complete(self, **kwargs):
        calls.append((kwargs["prompt_name"], kwargs["model_override"]))
        return LLMResponse(
            provider="ollama",
            model=kwargs["model_override"] or "missing-model",
            prompt_name=kwargs["prompt_name"],
            prompt_version=kwargs["prompt_version"],
            text="OK",
            deterministic=False,
        )

    monkeypatch.setattr(OllamaLLMProvider, "complete", fake_complete)
    context = WorkflowContext(
        created_by="pytest",
        intelligence_config=IntelligenceConfigBlock(llm_provider="ollama"),
    )

    for prompt_name in [
        "requirement_analysis_v1",
        "coverage_planning_v1",
        "test_case_generation_v1",
        "report_generation_v1",
    ]:
        complete_with_configured_llm(
            prompt_name=prompt_name,
            prompt_version="1.0.0",
            rendered_prompt="Ticket: model role routing",
            context=context,
        )

    assert calls == [
        ("requirement_analysis_v1", "qwen3:3b"),
        ("coverage_planning_v1", "deepseek-r1:8b"),
        ("test_case_generation_v1", "llama3.1:8b"),
        ("report_generation_v1", "qwen3:3b"),
    ]
    assert [
        call.model_role
        for call in context.intelligence_trace.llm_calls
    ] == ["main_rag", "reasoning", "stable_baseline", "main_rag"]


def test_manual_llm_model_override_bypasses_prompt_role_routing(monkeypatch) -> None:
    calls: list[str | None] = []

    def fake_complete(self, **kwargs):
        calls.append(kwargs["model_override"])
        return LLMResponse(
            provider="ollama",
            model=kwargs["model_override"] or "missing-model",
            prompt_name=kwargs["prompt_name"],
            prompt_version=kwargs["prompt_version"],
            text="OK",
            deterministic=False,
        )

    monkeypatch.setattr(OllamaLLMProvider, "complete", fake_complete)
    context = WorkflowContext(
        created_by="pytest",
        intelligence_config=IntelligenceConfigBlock(
            llm_provider="ollama",
            llm_model="manual-model",
        ),
    )

    complete_with_configured_llm(
        prompt_name="coverage_planning_v1",
        prompt_version="1.0.0",
        rendered_prompt="Ticket: manual override",
        context=context,
    )

    assert calls == ["manual-model"]
    assert context.intelligence_trace.llm_calls[0].model_role == "manual_override"
    assert context.intelligence_trace.llm_calls[0].requested_model == "manual-model"


def test_workflow_uses_selected_embedding_provider_with_local_fallback(monkeypatch) -> None:
    def fail_embedding_request(*args, **kwargs):
        raise RuntimeError("ollama offline in test")

    monkeypatch.setattr("backend.embeddings.ollama._post_json", fail_embedding_request)

    result = run_workflow(
        WorkflowContext(
            created_by="pytest",
            ticket=TicketData(
                id="AI-TRANSFER-FALLBACK",
                title="Money Transfer Balance Consistency",
                description=(
                    "As an authenticated customer, I want to transfer money and "
                    "see both balances updated."
                ),
                acceptance_criteria=[
                    "Transfer completes within 3 seconds",
                    "Both balances are consistent",
                ],
                priority="high",
                labels=["banking", "payments", "transfer"],
            ),
            intelligence_config=IntelligenceConfigBlock(
                llm_provider="mock_llm",
                embedding_provider="ollama_nomic_embed_text",
            ),
        )
    )

    assert (
        result.intelligence_trace.configured_embedding_provider
        == "ollama_nomic_embed_text"
    )
    assert result.requirement_analysis is not None
    assert result.requirement_analysis.knowledge_refs_used
    assert result.requirement_analysis.memory_refs_used
    assert result.intelligence_trace.knowledge_refs
    assert result.intelligence_trace.memory_refs
