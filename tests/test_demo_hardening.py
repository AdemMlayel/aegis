from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import settings as settings_module
from backend.config.settings import settings
from backend.execution import DockerRobotExecutionAdapter, execution_adapter_registry
from backend.knowledge import get_local_knowledge_store, ingest_local_document
from backend.knowledge.local import reset_local_knowledge_store
from backend.llm.base import LLMResponse
from backend.intelligence.structured_outputs import (
    RequirementLLMOutput,
    parse_structured_llm_response,
)
from backend.main import app
from backend.storage.adapters import PostgresStorageAdapter, SQLiteStorageAdapter, storage_adapter_registry


def test_deterministic_demo_mode_is_explicit_and_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("AEGISQA_DETERMINISTIC_DEMO_MODE", "true")
    monkeypatch.setenv("AEGISQA_DEFAULT_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("AEGISQA_DEFAULT_EMBEDDING_PROVIDER", "ollama_nomic_embed_text")
    settings_module.get_settings.cache_clear()
    demo_settings = settings_module.get_settings()
    try:
        assert demo_settings.deterministic_demo_mode is True
        assert demo_settings.default_llm_provider == "mock_llm"
        assert demo_settings.default_embedding_provider == "local_hash_embeddings"
        assert demo_settings.default_execution_adapter == "mock"
    finally:
        settings_module.get_settings.cache_clear()


def test_knowledge_ingestion_indexes_local_document(monkeypatch, tmp_path: Path) -> None:
    import backend.knowledge.ingestion as ingestion

    monkeypatch.setattr(ingestion, "GENERATED_KNOWLEDGE_ROOT", tmp_path)
    reset_local_knowledge_store()
    result = ingest_local_document(
        title="Demo IMS Regression Notes",
        text="IMS registration testing must validate SIP trace correlation and rejected registration paths.",
        source="local://demo/ims-regression.md",
        tags=["telecom", "ims", "regression"],
    )
    try:
        assert result.chunk_count == 1
        hits = get_local_knowledge_store().search(query="SIP trace rejected registration", limit=3)
        assert any(hit.chunk.chunk_id in result.chunk_ids for hit in hits)
    finally:
        reset_local_knowledge_store()


def test_structured_llm_parser_records_success_and_fallback() -> None:
    response = LLMResponse(
        provider="mock_llm",
        model="test",
        prompt_name="requirement_analysis_v1",
        prompt_version="1.0.0",
        text='{"summary":"Parsed summary","ambiguities":["Need error path"],"confidence":0.91}',
    )
    parsed = parse_structured_llm_response(response=response, schema=RequirementLLMOutput)
    assert parsed is not None
    assert parsed.summary == "Parsed summary"
    assert parsed.confidence == pytest.approx(0.91)

    bad_response = LLMResponse(
        provider="mock_llm",
        model="test",
        prompt_name="requirement_analysis_v1",
        prompt_version="1.0.0",
        text="plain text only",
    )
    assert parse_structured_llm_response(response=bad_response, schema=RequirementLLMOutput) is None


def test_storage_adapter_catalog_keeps_postgres_as_future_boundary() -> None:
    assert storage_adapter_registry.create("sqlite").spec == SQLiteStorageAdapter.spec
    specs = {spec.name: spec for spec in storage_adapter_registry.list_specs()}
    assert specs["postgres"].requires_external_service is True
    with pytest.raises(NotImplementedError):
        PostgresStorageAdapter().initialize()


def test_docker_robot_adapter_is_registered_but_not_default() -> None:
    assert execution_adapter_registry.has("robot_docker") is True
    assert execution_adapter_registry.get("robot_docker") is DockerRobotExecutionAdapter
    spec = execution_adapter_registry.get("robot_docker").spec
    assert "docker-isolation" in spec.capabilities
    assert settings.default_execution_adapter in {"robot", "mock", "robot_docker"}


def test_provider_catalog_exposes_deterministic_demo_flag(monkeypatch) -> None:
    monkeypatch.setattr(settings, "deterministic_demo_mode", True)
    client = TestClient(app)
    response = client.get("/api/v1/integrations/providers")
    assert response.status_code == 200
    assert response.json()["deterministic_demo_mode"] is True
