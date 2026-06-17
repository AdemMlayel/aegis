from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.security import Capability, Principal, require_capability
from backend.services.intelligence import (
    list_llm_providers as list_llm_providers_service,
    list_prompt_templates as list_prompt_templates_service,
    read_ollama_model_profiles as read_ollama_model_profiles_service,
    read_retrieval_profile as read_retrieval_profile_service,
    search_knowledge as search_knowledge_service,
    search_memory as search_memory_service,
    smoke_test_ollama_model_profiles as smoke_test_ollama_model_profiles_service,
)

router = APIRouter(tags=["intelligence"])


class PromptTemplateResponse(BaseModel):
    name: str
    version: str
    description: str


class LLMProviderResponse(BaseModel):
    name: str
    mode: str
    model: str
    requires_external_api: bool
    description: str
    configuration_status: str = "ready"
    configuration_keys: list[str] = []


class KnowledgeSearchItem(BaseModel):
    ref_id: str
    title: str
    source: str
    score: float
    vector_score: float = 0.0
    rerank_score: float = 0.0
    retention_status: str = "active"
    excerpt: str
    matched_terms: list[str]


class MemorySearchItem(BaseModel):
    ref_id: str
    title: str
    score: float
    vector_score: float = 0.0
    rerank_score: float = 0.0
    retention_status: str = "active"
    summary: str
    tags: list[str]
    source_refs: list[str]
    matched_terms: list[str]


class RetrievalProfileResponse(BaseModel):
    embedding_model: dict[str, object]
    vector_store: dict[str, object]
    reranker: dict[str, object]
    knowledge_store: dict[str, object]
    memory_store: dict[str, object]


class OllamaModelProfileResponse(BaseModel):
    role: str
    model: str
    kind: str
    purpose: str
    env_key: str
    fallback_model: str | None = None
    installed: bool
    fallback_installed: bool = False
    pull_command: str
    fallback_pull_command: str | None = None


class OllamaModelCatalogResponse(BaseModel):
    base_url: str
    service_available: bool
    service_error: str | None = None
    installed_models: list[str]
    profiles: list[OllamaModelProfileResponse]


class OllamaSmokeTestRequest(BaseModel):
    roles: list[str] | None = None
    prompt: str = Field(default="Return only OK if this model is ready for AegisQA.", min_length=1)


class OllamaSmokeTestItem(BaseModel):
    role: str
    model: str
    kind: str
    available: bool
    ok: bool
    response_excerpt: str = ""
    error: str | None = None


class OllamaSmokeTestResponse(BaseModel):
    results: list[OllamaSmokeTestItem]


@router.get("/intelligence/prompts", response_model=list[PromptTemplateResponse])
def list_prompt_templates(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[PromptTemplateResponse]:
    return [
        PromptTemplateResponse(**prompt)
        for prompt in list_prompt_templates_service()
    ]


@router.get("/intelligence/llm-providers", response_model=list[LLMProviderResponse])
def list_llm_providers(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[LLMProviderResponse]:
    return [
        LLMProviderResponse(**provider)
        for provider in list_llm_providers_service()
    ]


@router.get("/intelligence/knowledge/search", response_model=list[KnowledgeSearchItem])
def search_knowledge(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    query: str = Query(min_length=1),
    limit: int = Query(default=3, ge=1, le=10),
) -> list[KnowledgeSearchItem]:
    return [
        KnowledgeSearchItem(**result)
        for result in search_knowledge_service(query=query, limit=limit)
    ]


@router.get("/intelligence/memory/search", response_model=list[MemorySearchItem])
def search_memory(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    query: str = Query(min_length=1),
    limit: int = Query(default=3, ge=1, le=10),
) -> list[MemorySearchItem]:
    return [
        MemorySearchItem(**result)
        for result in search_memory_service(query=query, limit=limit)
    ]


@router.get("/intelligence/retrieval-profile", response_model=RetrievalProfileResponse)
def read_retrieval_profile(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> RetrievalProfileResponse:
    return RetrievalProfileResponse(**read_retrieval_profile_service())


@router.get("/intelligence/ollama/models", response_model=OllamaModelCatalogResponse)
def read_ollama_model_profiles(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaModelCatalogResponse:
    return OllamaModelCatalogResponse(**read_ollama_model_profiles_service())


@router.post("/intelligence/ollama/models/smoke-test", response_model=OllamaSmokeTestResponse)
def smoke_test_ollama_model_profiles(
    payload: OllamaSmokeTestRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaSmokeTestResponse:
    return OllamaSmokeTestResponse(
        results=[
            OllamaSmokeTestItem(**result)
            for result in smoke_test_ollama_model_profiles_service(
                roles=payload.roles,
                prompt=payload.prompt,
            )
        ]
    )
