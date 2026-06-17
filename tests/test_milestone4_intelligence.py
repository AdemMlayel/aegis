from starlette.testclient import TestClient
from datetime import UTC, datetime, timedelta

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
    assert providers.json()[0]["name"] == "mock_llm"
    assert providers.json()[0]["requires_external_api"] is False

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
    assert ("knowledge_store", "local_knowledge") in provider_keys
    assert ("memory_store", "local_episodic_memory") in provider_keys
    assert ("embedding_model", "local_hash_embedding") in provider_keys
    assert ("vector_store", "local_in_memory_vector") in provider_keys
    assert ("reranker", "local_hybrid_reranker") in provider_keys


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
