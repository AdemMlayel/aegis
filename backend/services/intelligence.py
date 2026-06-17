from __future__ import annotations

from backend.knowledge import get_local_knowledge_store
from backend.intelligence.vector import retrieval_profile
from backend.llm import llm_provider_registry
from backend.memory import get_local_memory_store
from backend.prompts import prompt_registry


def list_prompt_templates() -> list[dict[str, object]]:
    return [
        {
            "name": prompt.name,
            "version": prompt.version,
            "description": prompt.description,
        }
        for prompt in prompt_registry.list_specs()
    ]


def list_llm_providers() -> list[dict[str, object]]:
    return [
        {
            "name": spec.name,
            "mode": spec.mode,
            "model": spec.model,
            "requires_external_api": spec.requires_external_api,
            "description": spec.description,
        }
        for spec in llm_provider_registry.list_specs()
    ]


def search_knowledge(*, query: str, limit: int = 3) -> list[dict[str, object]]:
    return [
        {
            "ref_id": result.chunk.chunk_id,
            "title": result.chunk.title,
            "source": result.chunk.source,
            "score": result.score,
            "vector_score": result.vector_score,
            "rerank_score": result.rerank_score,
            "retention_status": result.retention_status,
            "excerpt": result.excerpt,
            "matched_terms": list(result.matched_terms),
        }
        for result in get_local_knowledge_store().search(query=query, limit=limit)
    ]


def search_memory(*, query: str, limit: int = 3) -> list[dict[str, object]]:
    return [
        {
            "ref_id": result.entry.memory_id,
            "title": result.entry.title,
            "score": result.score,
            "vector_score": result.vector_score,
            "rerank_score": result.rerank_score,
            "retention_status": result.retention_status,
            "summary": result.entry.summary,
            "tags": list(result.entry.tags),
            "source_refs": list(result.entry.source_refs),
            "matched_terms": list(result.matched_terms),
        }
        for result in get_local_memory_store().search(query=query, limit=limit)
    ]


def read_retrieval_profile() -> dict[str, object]:
    return {
        **retrieval_profile(),
        "knowledge_store": get_local_knowledge_store().retrieval_profile(),
        "memory_store": get_local_memory_store().retrieval_profile(),
    }
