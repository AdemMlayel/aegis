import pytest
from starlette.testclient import TestClient

from backend.graph.state import TestContext as WorkflowContext, TicketData
from backend.graph.workflow import run_workflow
from backend.knowledge import get_local_knowledge_store
from backend.llm import llm_provider_registry
from backend.main import app
from backend.memory import get_local_memory_store, reset_local_memory_stores
from backend.prompts import prompt_registry


@pytest.fixture(scope="module")
def archived_transfer_memory_id() -> str:
    reset_local_memory_stores()
    entry = get_local_memory_store().archive(
        title="Previous money transfer regression failure",
        summary=(
            "A completed transfer workflow found that balance consistency, audit records, "
            "and duplicate submission handling require regression coverage."
        ),
        tags=["banking", "payments", "transfer", "regression", "balance"],
        source_refs=["test://workflow/previous-transfer-run"],
        outcome="failed",
    )
    return entry.memory_id


def test_milestone4_intelligence_components_are_registered(
    archived_transfer_memory_id: str,
) -> None:
    assert llm_provider_registry.has("mock_llm") is True
    assert prompt_registry.has("requirement_analysis_v1") is True
    assert prompt_registry.has("coverage_planning_v1") is True
    assert prompt_registry.has("test_case_generation_v1") is True
    assert prompt_registry.has("report_generation_v1") is True
    assert get_local_knowledge_store().search(query="money transfer balance", limit=2)
    assert get_local_memory_store().search(query="money transfer balance regression", limit=2)


def test_workflow_records_ai_rag_and_memory_trace(
    archived_transfer_memory_id: str,
) -> None:
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
    assert any(
        ref.ref_id == archived_transfer_memory_id
        for ref in result.intelligence_trace.memory_refs
    )
    assert result.memory_archive is not None
    assert result.memory_archive.indexed_refs


def test_intelligence_api_exposes_local_mock_providers_and_search(
    archived_transfer_memory_id: str,
) -> None:
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

    memory = client.get("/api/v1/intelligence/memory/search", params={"query": "transfer balance regression"})
    assert memory.status_code == 200
    assert any(item["ref_id"] == archived_transfer_memory_id for item in memory.json())


def test_provider_catalog_includes_milestone4_local_intelligence_boundaries() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/providers")
    assert response.status_code == 200
    providers = response.json()["providers"]
    provider_keys = {(provider["kind"], provider["name"]) for provider in providers}

    assert ("llm_provider", "mock_llm") in provider_keys
    assert ("knowledge_store", "local_knowledge") in provider_keys
    assert ("memory_store", "local_episodic_memory") in provider_keys
