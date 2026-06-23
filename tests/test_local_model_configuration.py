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
