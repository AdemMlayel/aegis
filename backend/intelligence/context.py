from __future__ import annotations

from time import perf_counter

from backend.config.settings import settings
from backend.governance.context import (
    current_agent_execution,
    current_request_context,
)
from backend.governance.gateway import (
    GatewayLimitExceeded,
    circuit_breakers,
)
from backend.governance.policy import (
    AgentPolicyDenied,
    agent_policy_engine,
)
from backend.governance.tokens import (
    release_model_tokens,
    reserve_model_tokens,
    settle_model_tokens,
)
from backend.graph.state import (
    IntelligenceEvidenceRef,
    LLMUsageRef,
    PromptUsageRef,
    TestContext,
    TicketData,
    WorkflowStageName,
)
from backend.knowledge import KnowledgeSearchResult, get_local_knowledge_store
from backend.llm import LLMResponse
from backend.memory import EpisodicMemorySearchResult, get_local_memory_store
from backend.prompts import prompt_registry
from backend.storage.observability import (
    ModelInvocation,
    save_model_invocation,
)


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
    embedding_provider, embedding_model = _embedding_config_for_context(context)
    return get_local_knowledge_store(
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
    ).search(
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
    embedding_provider, embedding_model = _embedding_config_for_context(context)
    return get_local_memory_store(
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
    ).search(
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
    agent_name: str | None = None,
    model_role: str | None = None,
    requested_model: str | None = None,
    duration_ms: int = 0,
    estimated_cost_usd: float = 0.0,
    fallback_from: str | None = None,
) -> None:
    context.intelligence_trace.llm_provider = response.provider
    context.intelligence_trace.llm_calls.append(
        LLMUsageRef(
            provider=response.provider,
            model=response.model,
            prompt_name=response.prompt_name,
            prompt_version=response.prompt_version,
            deterministic=response.deterministic,
            agent_name=agent_name,
            model_role=model_role,
            requested_model=requested_model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            duration_ms=duration_ms,
            estimated_cost_usd=estimated_cost_usd,
            fallback_from=fallback_from,
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


def _embedding_config_for_context(
    context: TestContext | None,
) -> tuple[str | None, str | None]:
    if context is None:
        return None, None
    context.sync_intelligence_trace_config()
    return (
        context.intelligence_config.embedding_provider,
        context.intelligence_config.embedding_model,
    )


def prompt_version_ref(prompt_name: str) -> str:
    prompt = prompt_registry.get(prompt_name)
    return f"{prompt.name}@{prompt.version}"


def consume_stage_feedback(
    context: TestContext | None,
    stage: WorkflowStageName,
) -> list[str]:
    if context is None:
        return []
    comments: list[str] = []
    for item in context.review_feedback:
        if item.status != "open" or item.stage not in {None, stage}:
            continue
        comments.append(item.comment)
        item.status = "applied"
    return comments


def append_feedback_to_prompt(
    rendered_prompt: str,
    comments: list[str],
) -> str:
    if not comments:
        return rendered_prompt
    feedback = "\n".join(f"- {comment}" for comment in comments)
    return f"{rendered_prompt}\n\nReviewer feedback for this revision:\n{feedback}"


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
    from backend.intelligence.routing import agent_name_for_prompt
    from backend.llm import llm_provider_registry
    from backend.llm.ollama_profiles import resolve_chat_model_for_prompt

    agent_name = agent_name_for_prompt(prompt_name)
    agent_route = (
        context.intelligence_config.agent_routes.get(agent_name)
        if context is not None and agent_name is not None
        else None
    )
    if agent_route is not None:
        provider_name = agent_route.provider
        configured_model = agent_route.model
    elif context is not None:
        provider_name = context.intelligence_config.llm_provider
        configured_model = context.intelligence_config.llm_model
    else:
        provider_name = settings.default_llm_provider
        configured_model = None
    resolved_role = None
    model_override = configured_model
    if provider_name == "ollama" and not configured_model:
        resolved_role, model_override = resolve_chat_model_for_prompt(
            prompt_name=prompt_name,
            model_role=model_role,
        )
    execution = current_agent_execution()
    request_context = current_request_context()
    policy = agent_policy_engine.authorize_provider(
        execution,
        provider_name,
    )
    estimated_input_tokens = _estimate_tokens(
        " ".join(
            part
            for part in (system_instruction, rendered_prompt)
            if part
        )
    )
    reservation = reserve_model_tokens(
        request_context=request_context,
        execution=execution,
        policy=policy,
        context_id=context.context_id if context else None,
        agent_name=agent_name,
        provider=provider_name,
        estimated_input_tokens=estimated_input_tokens,
    )
    max_output_tokens = reservation.max_output_tokens
    started = perf_counter()
    fallback_from: str | None = None
    error_type: str | None = None
    try:
        circuit_breakers.before_call(provider_name)
        response = llm_provider_registry.create(provider_name).complete(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            rendered_prompt=rendered_prompt,
            system_instruction=system_instruction,
            model_override=model_override,
            max_output_tokens=max_output_tokens,
        )
        circuit_breakers.record_success(provider_name)
    except (AgentPolicyDenied, GatewayLimitExceeded):
        release_model_tokens(reservation)
        raise
    except Exception as exc:  # noqa: BLE001 - provider boundary must degrade gracefully in local demos.
        circuit_breakers.record_failure(provider_name)
        error_type = type(exc).__name__
        fallback_from = (
            f"{provider_name}:{model_override}"
            if model_override
            else provider_name
        )
        agent_policy_engine.authorize_provider(execution, "mock_llm")
        try:
            fallback = llm_provider_registry.create("mock_llm").complete(
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                rendered_prompt=rendered_prompt,
                system_instruction=system_instruction,
                model_override=(
                    model_override if provider_name == "mock_llm" else None
                ),
                max_output_tokens=max_output_tokens,
            )
        except Exception:
            release_model_tokens(reservation)
            raise
        fallback_origin = (
            f"{provider_name}:{model_override}"
            if model_override and provider_name != "mock_llm"
            else provider_name
        )
        fallback_text = (
            f"{fallback.text} Selected provider {provider_name!r} was "
            f"unavailable: {type(exc).__name__}: {exc}"
        )[: max_output_tokens * 4]
        fallback_output_tokens = _estimate_tokens(fallback_text)
        response = LLMResponse(
            provider="mock_llm",
            model=f"{fallback.model} (fallback from {fallback_origin})",
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=fallback_text,
            deterministic=True,
            input_tokens=fallback.input_tokens,
            output_tokens=fallback_output_tokens,
            total_tokens=fallback.input_tokens + fallback_output_tokens,
        )
    duration_ms = round((perf_counter() - started) * 1000)
    if response.input_tokens <= 0:
        response = LLMResponse(
            **{
                **response.__dict__,
                "input_tokens": estimated_input_tokens,
                "output_tokens": _estimate_tokens(response.text),
                "total_tokens": (
                    estimated_input_tokens
                    + _estimate_tokens(response.text)
                ),
            }
        )
    estimated_cost_usd = _estimate_cost(
        provider=response.provider,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )
    try:
        save_model_invocation(
            ModelInvocation(
                request_id=(
                    request_context.request_id if request_context else None
                ),
                context_id=context.context_id if context else None,
                organization_id=(
                    request_context.organization_id
                    if request_context
                    else "local"
                ),
                actor=request_context.actor if request_context else "system",
                agent_id=execution.agent_id if execution else None,
                agent_name=agent_name,
                provider=response.provider,
                model=response.model,
                prompt_name=prompt_name,
                status="fallback" if fallback_from else "success",
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                duration_ms=duration_ms,
                estimated_cost_usd=estimated_cost_usd,
                fallback_from=fallback_from,
                error_type=error_type,
            )
        )
    except Exception:
        release_model_tokens(reservation)
        raise
    settle_model_tokens(
        reservation,
        actual_tokens=response.total_tokens,
    )
    if context is not None:
        context.sync_intelligence_trace_config()
        record_prompt_usage(context, name=prompt_name, version=prompt_version)
        record_llm_usage(
            context,
            response,
            agent_name=agent_name,
            model_role=resolved_role if not configured_model else "manual_override",
            requested_model=model_override,
            duration_ms=duration_ms,
            estimated_cost_usd=estimated_cost_usd,
            fallback_from=fallback_from,
        )
    return response


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _estimate_cost(
    *,
    provider: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    if provider != "openai_compatible":
        return 0.0
    return round(
        (
            input_tokens * settings.external_input_cost_per_1k
            + output_tokens * settings.external_output_cost_per_1k
        )
        / 1000,
        8,
    )
