from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.security import Capability, Principal, require_capability
from backend.services.intelligence import (
    list_llm_providers as list_llm_providers_service,
    list_prompt_templates as list_prompt_templates_service,
    read_retrieval_profile as read_retrieval_profile_service,
    search_knowledge as search_knowledge_service,
    search_memory as search_memory_service,
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
