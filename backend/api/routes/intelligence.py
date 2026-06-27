from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.knowledge import get_local_knowledge_store, ingest_local_document
from backend.intelligence.providers import (
    embedding_provider_metadata,
    llm_provider_metadata,
)
from backend.intelligence.routing import (
    embedding_recommendation,
    list_agent_model_profiles,
)
from backend.llm import llm_provider_registry
from backend.embeddings import embedding_provider_registry
from backend.llm.ollama import ollama_health
from backend.memory import get_local_memory_store
from backend.prompts import prompt_registry
from backend.security import Capability, Principal, require_capability
from backend.services.intelligence import (
    read_ollama_model_profiles,
    smoke_test_ollama_model_profiles,
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
    configuration_status: str
    configuration_keys: list[str]
    selectable: bool


class EmbeddingProviderResponse(BaseModel):
    name: str
    mode: str
    model: str
    dimensions: int
    requires_external_api: bool
    description: str
    configuration_status: str
    configuration_keys: list[str]
    selectable: bool


class AgentModelProfileResponse(BaseModel):
    agent_name: str
    label: str
    purpose: str
    uses_llm: bool
    prompt_names: list[str]
    local_role: str | None
    recommended_mode: str
    rationale: str
    local_provider: str | None
    local_model: str | None
    external_provider: str | None
    external_model: str | None
    recommended_provider: str | None
    recommended_model: str | None


class EmbeddingRecommendationResponse(BaseModel):
    recommended_mode: str
    recommended_provider: str
    recommended_model: str
    fallback_provider: str
    rationale: str


class AgentRoutingCatalogResponse(BaseModel):
    agents: list[AgentModelProfileResponse]
    embedding: EmbeddingRecommendationResponse


class OllamaHealthResponse(BaseModel):
    available: bool
    base_url: str
    chat_model: str
    embedding_model: str
    installed_models: list[str]
    chat_model_ready: bool
    embedding_model_ready: bool
    message: str


class OllamaModelProfileResponse(BaseModel):
    role: str
    model: str
    kind: str
    purpose: str
    env_key: str
    fallback_model: str | None
    installed: bool
    fallback_installed: bool
    pull_command: str
    fallback_pull_command: str | None


class OllamaPromptRouteResponse(BaseModel):
    prompt_name: str
    role: str
    model: str


class OllamaModelProfilesResponse(BaseModel):
    base_url: str
    service_available: bool
    service_error: str | None
    installed_models: list[str]
    profiles: list[OllamaModelProfileResponse]
    prompt_routes: list[OllamaPromptRouteResponse]


class OllamaSmokeTestRequest(BaseModel):
    roles: list[str] | None = None
    prompt: str = "Return only OK if this model is ready for AegisQA."


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


class KnowledgeSearchItem(BaseModel):
    ref_id: str
    title: str
    source: str
    score: float
    excerpt: str
    matched_terms: list[str]


class MemorySearchItem(BaseModel):
    ref_id: str
    title: str
    score: float
    summary: str
    tags: list[str]
    source_refs: list[str]
    matched_terms: list[str]


class KnowledgeIngestRequest(BaseModel):
    title: str
    text: str
    source: str = "local://manual-ingest"
    tags: list[str] = []


class KnowledgeIngestResponse(BaseModel):
    document_id: str
    title: str
    source: str
    chunk_ids: list[str]
    chunk_count: int
    tags: list[str]
    stored_path: str | None = None


@router.get("/intelligence/prompts", response_model=list[PromptTemplateResponse])
def list_prompt_templates(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[PromptTemplateResponse]:
    return [
        PromptTemplateResponse(
            name=prompt.name,
            version=prompt.version,
            description=prompt.description,
        )
        for prompt in prompt_registry.list_specs()
    ]


@router.get("/intelligence/llm-providers", response_model=list[LLMProviderResponse])
def list_llm_providers(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[LLMProviderResponse]:
    providers = []
    for spec in llm_provider_registry.list_specs():
        providers.append(
            LLMProviderResponse(
                name=spec.name,
                mode=spec.mode,
                model=spec.model,
                requires_external_api=spec.requires_external_api,
                description=spec.description,
                **llm_provider_metadata(spec.name),
            )
        )
    return providers




@router.get("/intelligence/embedding-providers", response_model=list[EmbeddingProviderResponse])
def list_embedding_providers(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[EmbeddingProviderResponse]:
    providers = []
    for spec in embedding_provider_registry.list_specs():
        providers.append(
            EmbeddingProviderResponse(
                name=spec.name,
                mode=spec.mode,
                model=spec.model,
                dimensions=spec.dimensions,
                requires_external_api=spec.requires_external_api,
                description=spec.description,
                **embedding_provider_metadata(spec.name),
            )
        )
    return providers


@router.get(
    "/intelligence/agent-model-profiles",
    response_model=AgentRoutingCatalogResponse,
)
def get_agent_model_profiles(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> AgentRoutingCatalogResponse:
    return AgentRoutingCatalogResponse(
        agents=list_agent_model_profiles(),
        embedding=embedding_recommendation(),
    )


@router.get("/intelligence/ollama/health", response_model=OllamaHealthResponse)
def get_ollama_health(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaHealthResponse:
    return OllamaHealthResponse(**ollama_health())


@router.get("/intelligence/ollama/profiles", response_model=OllamaModelProfilesResponse)
def get_ollama_model_profiles(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaModelProfilesResponse:
    return OllamaModelProfilesResponse(**read_ollama_model_profiles())


@router.post("/intelligence/ollama/profiles/smoke-test", response_model=OllamaSmokeTestResponse)
def smoke_test_ollama_profiles(
    request: OllamaSmokeTestRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaSmokeTestResponse:
    return OllamaSmokeTestResponse(
        results=smoke_test_ollama_model_profiles(
            roles=request.roles,
            prompt=request.prompt,
        )
    )


@router.get("/intelligence/knowledge/search", response_model=list[KnowledgeSearchItem])
def search_knowledge(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    query: str = Query(min_length=1),
    limit: int = Query(default=3, ge=1, le=10),
) -> list[KnowledgeSearchItem]:
    return [
        KnowledgeSearchItem(
            ref_id=result.chunk.chunk_id,
            title=result.chunk.title,
            source=result.chunk.source,
            score=result.score,
            excerpt=result.excerpt,
            matched_terms=list(result.matched_terms),
        )
        for result in get_local_knowledge_store().search(query=query, limit=limit)
    ]


@router.post("/intelligence/knowledge/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge_document(
    request: KnowledgeIngestRequest,
    principal: Annotated[Principal, Depends(require_capability(Capability.EDIT_ARTIFACTS))],
) -> KnowledgeIngestResponse:
    result = ingest_local_document(
        title=request.title,
        text=request.text,
        source=request.source,
        tags=request.tags,
    )
    return KnowledgeIngestResponse(**result.__dict__)


@router.get("/intelligence/memory/search", response_model=list[MemorySearchItem])
def search_memory(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    query: str = Query(min_length=1),
    limit: int = Query(default=3, ge=1, le=10),
) -> list[MemorySearchItem]:
    return [
        MemorySearchItem(
            ref_id=result.entry.memory_id,
            title=result.entry.title,
            score=result.score,
            summary=result.entry.summary,
            tags=list(result.entry.tags),
            source_refs=list(result.entry.source_refs),
            matched_terms=list(result.matched_terms),
        )
        for result in get_local_memory_store().search(query=query, limit=limit)
    ]
