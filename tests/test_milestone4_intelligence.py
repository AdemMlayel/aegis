from datetime import UTC, datetime, timedelta

import pytest
from starlette.testclient import TestClient

from backend.graph.state import TestContext as WorkflowContext, TicketData
from backend.graph.workflow import run_workflow
from backend.knowledge.base import KnowledgeChunk, KnowledgeStore
from backend.knowledge import get_local_knowledge_store
from backend.llm import llm_provider_registry
from backend.memory.base import EpisodicMemoryEntry, EpisodicMemoryStore
from backend.main import app
from backend.memory import get_local_memory_store
from backend.prompts import prompt_registry


def test_milestone4_intelligence_components_are_registered() -> None:
    assert llm_provider_registry.has("mock_llm") is True
    assert llm_provider_registry.has("openai_compatible") is True
    assert llm_provider_registry.has("ollama") is True
    assert prompt_registry.has("requirement_analysis_v1") is True
    assert prompt_registry.has("coverage_planning_v1") is True
    assert prompt_registry.has("test_case_generation_v1") is True
    assert prompt_registry.has("report_generation_v1") is True
    assert get_local_knowledge_store().search(query="money transfer balance", limit=2)
    assert get_local_memory_store().search(query="money transfer balance regression", limit=2)


def test_workflow_records_ai_rag_and_memory_trace() -> None:
    result = run_workflow(
        WorkflowContext(
            created_by="pytest",
            ticket=TicketData(
                id="AI-TRANSFER-001",
                title="Money Transfer Balance Consistency",
                description="As an authenticated customer, I want to transfer money and see both balances updated.",
                acceptance_criteria=["Transfer completes within 3 seconds", "Both balances are consistent"],
                priority="high",
                labels=["banking", "payments", "transfer"],
            ),
        )
    )

    assert result.requirement_analysis is not None
    assert result.requirement_analysis.llm_summary is not None
    assert result.requirement_analysis.knowledge_refs_used
    assert result.requirement_analysis.memory_refs_used
    assert result.coverage_plan is not None
    assert result.coverage_plan.regression_tests_to_rerun == ["REG-BALANCE-CONSISTENCY"]
    assert result.reports is not None
    assert result.reports.knowledge_refs_used
    assert result.reports.memory_refs_used
    assert result.intelligence_trace.llm_provider == "mock_llm"
    assert {prompt.name for prompt in result.intelligence_trace.prompt_versions} >= {
        "requirement_analysis_v1",
        "coverage_planning_v1",
        "test_case_generation_v1",
        "report_generation_v1",
    }
    assert any(ref.ref_id == "KB-BANK-001" for ref in result.intelligence_trace.knowledge_refs)
    assert any(ref.ref_id == "MEM-BANK-TRANSFER-001" for ref in result.intelligence_trace.memory_refs)
    assert result.memory_archive is not None
    assert result.memory_archive.indexed_refs


def test_intelligence_api_exposes_local_mock_providers_and_search() -> None:
    client = TestClient(app)

    prompts = client.get("/api/v1/intelligence/prompts")
    assert prompts.status_code == 200
    assert {prompt["name"] for prompt in prompts.json()} >= {
        "requirement_analysis_v1",
        "report_generation_v1",
    }

    providers = client.get("/api/v1/intelligence/llm-providers")
    assert providers.status_code == 200
    provider_map = {provider["name"]: provider for provider in providers.json()}
    assert provider_map["mock_llm"]["requires_external_api"] is False
    assert provider_map["openai_compatible"]["requires_external_api"] is True
    assert provider_map["openai_compatible"]["configuration_status"] in {
        "configured",
        "missing_api_key",
    }
    assert provider_map["ollama"]["mode"] == "local"

    knowledge = client.get("/api/v1/intelligence/knowledge/search", params={"query": "banking transfer risk"})
    assert knowledge.status_code == 200
    assert any(item["ref_id"] == "KB-BANK-001" for item in knowledge.json())
    assert knowledge.json()[0]["rerank_score"] >= 0

    memory = client.get("/api/v1/intelligence/memory/search", params={"query": "transfer balance regression"})
    assert memory.status_code == 200
    assert any(item["ref_id"] == "MEM-BANK-TRANSFER-001" for item in memory.json())
    assert memory.json()[0]["vector_score"] >= 0

    profile = client.get("/api/v1/intelligence/retrieval-profile")
    assert profile.status_code == 200
    assert profile.json()["embedding_model"]["name"] == "local_hash_embedding"
    assert profile.json()["vector_store"]["name"] == "local_in_memory_vector"
    assert profile.json()["reranker"]["name"] == "local_hybrid_reranker"


def test_provider_catalog_includes_milestone4_local_intelligence_boundaries() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/providers")
    assert response.status_code == 200
    providers = response.json()["providers"]
    provider_keys = {(provider["kind"], provider["name"]) for provider in providers}

    assert ("llm_provider", "mock_llm") in provider_keys
    assert ("llm_provider", "ollama") in provider_keys
    assert ("knowledge_store", "local_knowledge") in provider_keys
    assert ("memory_store", "local_episodic_memory") in provider_keys
    assert ("embedding_model", "local_hash_embedding") in provider_keys
    assert ("embedding_model", "ollama_embedding") in provider_keys
    assert ("vector_store", "local_in_memory_vector") in provider_keys
    assert ("reranker", "local_hybrid_reranker") in provider_keys


def test_openai_compatible_provider_builds_chat_completion_request(monkeypatch) -> None:
    import backend.llm.openai_compatible as provider_module
    from backend.llm.openai_compatible import OpenAICompatibleLLMProvider, settings

    captured: dict[str, object] = {}

    def fake_post_json(**kwargs):
        captured.update(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": "Real-model style requirement analysis.",
                    }
                }
            ]
        }

    monkeypatch.setattr(settings, "openai_compatible_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_compatible_base_url", "https://llm.example/v1")
    monkeypatch.setattr(settings, "openai_compatible_model", "real-model")
    monkeypatch.setattr(provider_module, "post_json", fake_post_json)

    response = OpenAICompatibleLLMProvider().complete(
        prompt_name="requirement_analysis_v1",
        prompt_version="1.0.0",
        rendered_prompt="Ticket: Configure real model",
    )

    assert response.provider == "openai_compatible"
    assert response.model == "real-model"
    assert response.deterministic is False
    assert response.text == "Real-model style requirement analysis."
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    payload = captured["payload"]
    assert payload["model"] == "real-model"
    assert payload["messages"][-1]["content"] == "Ticket: Configure real model"


def test_openai_compatible_provider_requires_api_key(monkeypatch) -> None:
    from backend.llm.openai_compatible import OpenAICompatibleLLMProvider, settings

    monkeypatch.setattr(settings, "openai_compatible_api_key", None)

    with pytest.raises(RuntimeError, match="AEGISQA_OPENAI_COMPATIBLE_API_KEY"):
        OpenAICompatibleLLMProvider().complete(
            prompt_name="requirement_analysis_v1",
            prompt_version="1.0.0",
            rendered_prompt="Ticket: Missing key",
        )


def test_ollama_provider_builds_local_chat_request(monkeypatch) -> None:
    import backend.llm.ollama as provider_module
    from backend.llm.ollama import OllamaLLMProvider, settings

    captured: dict[str, object] = {}

    def fake_post_json(**kwargs):
        captured.update(kwargs)
        return {"message": {"content": "Local model analysis."}}

    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.local:11434")
    monkeypatch.setattr(settings, "ollama_model", "llama-local")
    monkeypatch.setattr(settings, "ollama_reasoning_model", "deepseek-local")
    monkeypatch.setattr(provider_module, "post_json", fake_post_json)

    response = OllamaLLMProvider().complete(
        prompt_name="coverage_planning_v1",
        prompt_version="1.0.0",
        rendered_prompt="Plan coverage",
        system_instruction="QA system",
    )

    assert response.provider == "ollama"
    assert response.model == "deepseek-local"
    assert response.text == "Local model analysis."
    assert captured["url"] == "http://ollama.local:11434/api/chat"
    payload = captured["payload"]
    assert payload["model"] == "deepseek-local"
    assert payload["messages"][0] == {"role": "system", "content": "QA system"}
    assert payload["messages"][1] == {"role": "user", "content": "Plan coverage"}


def test_ollama_model_profiles_report_requested_roles(monkeypatch) -> None:
    import backend.llm.ollama_profiles as profiles

    def fake_get_json(**kwargs):
        return {
            "models": [
                {"name": "qwen3:3b"},
                {"name": "nomic-embed-text"},
            ]
        }

    monkeypatch.setattr(profiles, "get_json", fake_get_json)

    status = profiles.model_profile_status()
    profile_map = {profile["role"]: profile for profile in status["profiles"]}

    assert status["service_available"] is True
    assert profile_map["main_rag"]["model"] == "qwen3:3b"
    assert profile_map["stable_baseline"]["model"] == "llama3.1:8b"
    assert profile_map["coding_repo_analysis"]["model"] == "qwen3-coder:latest"
    assert profile_map["main_rag"]["installed"] is True
    assert profile_map["rag_embedding"]["fallback_installed"] is True
    assert profile_map["reasoning"]["pull_command"] == "ollama pull deepseek-r1:7b"


def test_ollama_smoke_test_profiles_supports_chat_and_embeddings(monkeypatch) -> None:
    import backend.llm.ollama_profiles as profiles

    installed = [profile.model for profile in profiles.list_ollama_profiles()]
    calls: list[tuple[str, str]] = []

    def fake_chat_with_ollama(*, model: str, prompt: str) -> str:
        calls.append(("chat", model))
        return f"OK {model}"

    def fake_embed_with_ollama(*, model: str, text: str) -> tuple[float, ...]:
        calls.append(("embedding", model))
        return (0.1, 0.2, 0.3)

    monkeypatch.setattr(profiles, "list_installed_ollama_models", lambda: (True, installed, None))
    monkeypatch.setattr(profiles, "chat_with_ollama", fake_chat_with_ollama)
    monkeypatch.setattr(profiles, "embed_with_ollama", fake_embed_with_ollama)

    results = profiles.smoke_test_profiles(
        roles=["coding_repo_analysis", "rag_embedding"],
        prompt="ping",
    )
    result_map = {result.role: result for result in results}

    assert result_map["coding_repo_analysis"].ok is True
    assert result_map["rag_embedding"].ok is True
    assert result_map["rag_embedding"].response_excerpt == "embedding_dimensions=3"
    assert ("chat", "qwen3-coder:latest") in calls
    assert ("embedding", "qwen3-embedding:0.6b") in calls


def test_ollama_model_profile_api(monkeypatch) -> None:
    import backend.api.routes.intelligence as route_module

    client = TestClient(app)

    monkeypatch.setattr(
        route_module,
        "read_ollama_model_profiles_service",
        lambda: {
            "base_url": "http://ollama.local:11434",
            "service_available": True,
            "service_error": None,
            "installed_models": ["qwen3:3b"],
            "profiles": [
                {
                    "role": "main_rag",
                    "model": "qwen3:3b",
                    "kind": "chat",
                    "purpose": "Main model.",
                    "env_key": "AEGISQA_OLLAMA_RAG_MODEL",
                    "fallback_model": None,
                    "installed": True,
                    "fallback_installed": False,
                    "pull_command": "ollama pull qwen3:3b",
                    "fallback_pull_command": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        route_module,
        "smoke_test_ollama_model_profiles_service",
        lambda *, roles, prompt: [
            {
                "role": roles[0],
                "model": "qwen3:3b",
                "kind": "chat",
                "available": True,
                "ok": True,
                "response_excerpt": "OK",
                "error": None,
            }
        ],
    )

    catalog = client.get("/api/v1/intelligence/ollama/models")
    assert catalog.status_code == 200
    assert catalog.json()["profiles"][0]["role"] == "main_rag"

    smoke = client.post(
        "/api/v1/intelligence/ollama/models/smoke-test",
        json={"roles": ["main_rag"], "prompt": "ping"},
    )
    assert smoke.status_code == 200
    assert smoke.json()["results"][0]["ok"] is True


def test_ollama_embedding_model_can_back_retrieval_profile(monkeypatch) -> None:
    import backend.intelligence.vector as vector_module
    import backend.llm.ollama_profiles as profiles

    monkeypatch.setattr(vector_module.settings, "default_embedding_model", "ollama_embedding")
    monkeypatch.setattr(vector_module.settings, "ollama_embedding_model", "nomic-embed-text")
    monkeypatch.setattr(
        profiles,
        "embed_with_ollama",
        lambda *, model, text: (0.7, 0.2, 0.1),
    )

    embedding_model = vector_module.create_embedding_model()

    assert embedding_model.spec.name == "ollama_embedding"
    assert embedding_model.spec.deterministic is False
    assert embedding_model.embed("transfer risk") == (0.7, 0.2, 0.1)
    assert vector_module.retrieval_profile()["embedding_model"]["name"] == "ollama_embedding"


def test_knowledge_vector_store_supports_rerank_and_invalidation() -> None:
    store = KnowledgeStore(
        [
            KnowledgeChunk(
                chunk_id="KB-A",
                title="Transfer risk",
                source="local://kb/a",
                text="Money transfer balance consistency and duplicate submission risk.",
                tags=("banking", "transfer"),
            ),
            KnowledgeChunk(
                chunk_id="KB-B",
                title="Profile settings",
                source="local://kb/b",
                text="Profile color preferences and avatar settings.",
                tags=("profile",),
            ),
        ]
    )

    results = store.search(query="transfer balance risk", limit=2)

    assert results[0].chunk.chunk_id == "KB-A"
    assert results[0].vector_score >= 0
    assert results[0].rerank_score == results[0].score
    assert store.invalidate("KB-A") is True
    assert all(result.chunk.chunk_id != "KB-A" for result in store.search(query="transfer balance risk", limit=2))


def test_memory_vector_store_prunes_expired_entries() -> None:
    expired_at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    store = EpisodicMemoryStore(
        [
            EpisodicMemoryEntry(
                memory_id="MEM-EXPIRED",
                title="Expired transfer lesson",
                summary="Old transfer balance lesson.",
                tags=("transfer",),
                expires_at=expired_at,
            ),
            EpisodicMemoryEntry(
                memory_id="MEM-ACTIVE",
                title="Active transfer lesson",
                summary="Current transfer balance lesson.",
                tags=("transfer", "balance"),
            ),
        ]
    )

    assert store.prune_expired() == ["MEM-EXPIRED"]
    results = store.search(query="transfer balance", limit=5)

    assert [result.entry.memory_id for result in results] == ["MEM-ACTIVE"]
    assert store.retrieval_profile()["active_entry_count"] == 1
