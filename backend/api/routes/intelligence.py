from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.knowledge import get_local_knowledge_store
from backend.llm import llm_provider_registry
from backend.embeddings import embedding_provider_registry
from backend.llm.ollama import ollama_health
from backend.memory import get_local_memory_store
from backend.prompts import prompt_registry
from backend.security import Capability, Principal, require_capability

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


class EmbeddingProviderResponse(BaseModel):
    name: str
    mode: str
    model: str
    dimensions: int
    requires_external_api: bool
    description: str


class OllamaHealthResponse(BaseModel):
    available: bool
    base_url: str
    chat_model: str
    embedding_model: str
    installed_models: list[str]
    chat_model_ready: bool
    embedding_model_ready: bool
    message: str


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
    return [
        LLMProviderResponse(
            name=spec.name,
            mode=spec.mode,
            model=spec.model,
            requires_external_api=spec.requires_external_api,
            description=spec.description,
        )
        for spec in llm_provider_registry.list_specs()
    ]




@router.get("/intelligence/embedding-providers", response_model=list[EmbeddingProviderResponse])
def list_embedding_providers(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> list[EmbeddingProviderResponse]:
    return [
        EmbeddingProviderResponse(
            name=spec.name,
            mode=spec.mode,
            model=spec.model,
            dimensions=spec.dimensions,
            requires_external_api=spec.requires_external_api,
            description=spec.description,
        )
        for spec in embedding_provider_registry.list_specs()
    ]


@router.get("/intelligence/ollama/health", response_model=OllamaHealthResponse)
def get_ollama_health(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> OllamaHealthResponse:
    return OllamaHealthResponse(**ollama_health())

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
