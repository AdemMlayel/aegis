from __future__ import annotations

from backend.graph.state import (
    IntelligenceEvidenceRef,
    LLMUsageRef,
    PromptUsageRef,
    TestContext,
    TicketData,
)
from backend.knowledge import KnowledgeSearchResult, get_local_knowledge_store
from backend.llm import LLMResponse
from backend.memory import EpisodicMemorySearchResult, get_local_memory_store
from backend.prompts import prompt_registry


def build_ticket_query(ticket: TicketData) -> str:
    return " ".join(
        [
            ticket.id,
            ticket.title,
            ticket.description,
            " ".join(ticket.acceptance_criteria),
            " ".join(ticket.labels),
            ticket.priority,
        ]
    )


def search_knowledge_for_ticket(ticket: TicketData, *, limit: int = 3) -> list[KnowledgeSearchResult]:
    return get_local_knowledge_store().search(
        query=build_ticket_query(ticket),
        tags=ticket.labels,
        limit=limit,
    )


def search_memory_for_ticket(ticket: TicketData, *, limit: int = 3) -> list[EpisodicMemorySearchResult]:
    return get_local_memory_store().search(
        query=build_ticket_query(ticket),
        tags=ticket.labels,
        limit=limit,
    )


def format_knowledge_context(results: list[KnowledgeSearchResult]) -> str:
    if not results:
        return "No local knowledge chunks matched."
    return "\n".join(
        f"KNOWLEDGE[{result.chunk.chunk_id}] {result.chunk.title}: {result.excerpt}"
        for result in results
    )


def format_memory_context(results: list[EpisodicMemorySearchResult]) -> str:
    if not results:
        return "No episodic memories matched."
    return "\n".join(
        f"MEMORY[{result.entry.memory_id}] {result.entry.title}: {result.entry.summary}"
        for result in results
    )


def record_prompt_usage(context: TestContext, *, name: str, version: str) -> None:
    key = (name, version)
    existing = {(item.name, item.version) for item in context.intelligence_trace.prompt_versions}
    if key not in existing:
        context.intelligence_trace.prompt_versions.append(PromptUsageRef(name=name, version=version))


def record_llm_usage(context: TestContext, response: LLMResponse) -> None:
    context.intelligence_trace.llm_provider = response.provider
    context.intelligence_trace.llm_calls.append(
        LLMUsageRef(
            provider=response.provider,
            model=response.model,
            prompt_name=response.prompt_name,
            prompt_version=response.prompt_version,
            deterministic=response.deterministic,
            summary=response.text,
        )
    )


def record_knowledge_refs(context: TestContext, results: list[KnowledgeSearchResult]) -> list[str]:
    existing = {item.ref_id for item in context.intelligence_trace.knowledge_refs}
    refs: list[str] = []
    for result in results:
        refs.append(result.chunk.chunk_id)
        if result.chunk.chunk_id in existing:
            continue
        context.intelligence_trace.knowledge_refs.append(
            IntelligenceEvidenceRef(
                ref_id=result.chunk.chunk_id,
                source=result.chunk.source,
                title=result.chunk.title,
                score=result.score,
                excerpt=result.excerpt,
            )
        )
    return refs


def record_memory_refs(context: TestContext, results: list[EpisodicMemorySearchResult]) -> list[str]:
    existing = {item.ref_id for item in context.intelligence_trace.memory_refs}
    refs: list[str] = []
    for result in results:
        refs.append(result.entry.memory_id)
        if result.entry.memory_id in existing:
            continue
        context.intelligence_trace.memory_refs.append(
            IntelligenceEvidenceRef(
                ref_id=result.entry.memory_id,
                source=result.entry.source_refs[0] if result.entry.source_refs else "local://memory",
                title=result.entry.title,
                score=result.score,
                excerpt=result.entry.summary,
            )
        )
    return refs


def prompt_version_ref(prompt_name: str) -> str:
    prompt = prompt_registry.get(prompt_name)
    return f"{prompt.name}@{prompt.version}"
