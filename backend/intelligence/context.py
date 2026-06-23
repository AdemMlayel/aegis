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


def search_knowledge_for_ticket(
    ticket: TicketData,
    *,
    limit: int = 3,
    context: TestContext | None = None,
) -> list[KnowledgeSearchResult]:
    embedding_provider = _embedding_provider_for_context(context)
    return get_local_knowledge_store(embedding_provider=embedding_provider).search(
        query=build_ticket_query(ticket),
        tags=ticket.labels,
        limit=limit,
    )


def search_memory_for_ticket(
    ticket: TicketData,
    *,
    limit: int = 3,
    context: TestContext | None = None,
) -> list[EpisodicMemorySearchResult]:
    embedding_provider = _embedding_provider_for_context(context)
    return get_local_memory_store(embedding_provider=embedding_provider).search(
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


def record_llm_usage(
    context: TestContext,
    response: LLMResponse,
    *,
    model_role: str | None = None,
    requested_model: str | None = None,
) -> None:
    context.intelligence_trace.llm_provider = response.provider
    context.intelligence_trace.llm_calls.append(
        LLMUsageRef(
            provider=response.provider,
            model=response.model,
            prompt_name=response.prompt_name,
            prompt_version=response.prompt_version,
            deterministic=response.deterministic,
            model_role=model_role,
            requested_model=requested_model,
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


def _embedding_provider_for_context(context: TestContext | None) -> str | None:
    if context is None:
        return None
    context.sync_intelligence_trace_config()
    return context.intelligence_config.embedding_provider


def prompt_version_ref(prompt_name: str) -> str:
    prompt = prompt_registry.get(prompt_name)
    return f"{prompt.name}@{prompt.version}"


def complete_with_configured_llm(
    *,
    prompt_name: str,
    prompt_version: str,
    rendered_prompt: str,
    system_instruction: str | None = None,
    context: TestContext | None = None,
    model_role: str | None = None,
) -> LLMResponse:
    """Call the selected LLM provider with a safe deterministic fallback.

    Local demos should not fail just because Ollama is not running. When a
    selected local/cloud provider is unavailable, the response explicitly states
    the fallback reason so the UI and report remain honest.
    """
    from backend.config.settings import settings
    from backend.llm import llm_provider_registry
    from backend.llm.ollama_profiles import resolve_chat_model_for_prompt

    provider_name = context.intelligence_config.llm_provider if context else settings.default_llm_provider
    configured_model = context.intelligence_config.llm_model if context else None
    resolved_role = None
    model_override = configured_model
    if provider_name == "ollama" and not configured_model:
        resolved_role, model_override = resolve_chat_model_for_prompt(
            prompt_name=prompt_name,
            model_role=model_role,
        )
    try:
        response = llm_provider_registry.create(provider_name).complete(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            rendered_prompt=rendered_prompt,
            system_instruction=system_instruction,
            model_override=model_override,
        )
    except Exception as exc:  # noqa: BLE001 - provider boundary must degrade gracefully in local demos.
        fallback = llm_provider_registry.create("mock_llm").complete(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            rendered_prompt=rendered_prompt,
            system_instruction=system_instruction,
            model_override=model_override if provider_name == "mock_llm" else None,
        )
        fallback_origin = (
            f"{provider_name}:{model_override}"
            if model_override and provider_name != "mock_llm"
            else provider_name
        )
        response = LLMResponse(
            provider="mock_llm",
            model=f"{fallback.model} (fallback from {fallback_origin})",
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=(
                f"{fallback.text} Selected provider {provider_name!r} was unavailable: "
                f"{type(exc).__name__}: {exc}"
            ),
            deterministic=True,
        )
    if context is not None:
        context.sync_intelligence_trace_config()
        record_prompt_usage(context, name=prompt_name, version=prompt_version)
        record_llm_usage(
            context,
            response,
            model_role=resolved_role if not configured_model else "manual_override",
            requested_model=model_override,
        )
    return response
