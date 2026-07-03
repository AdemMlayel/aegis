"""Optional LLM-backed answering for free-form chat questions.

The copilot is deterministic first: ``classify_chat_intent`` handles known
intents and ``build_assistant_response`` returns templated, data-grounded
answers. Only when a message maps to ``unknown`` — and only when explicitly
enabled — do we fall through to the configured LLM here, grounded with system
knowledge and retrieved RAG context.

Design constraints:
- LLM is used for ANSWERS only. It never proposes or triggers actions; those
  stay on the deterministic, confirmation-gated path.
- It degrades safely: any provider error returns ``None`` so the caller uses
  the deterministic fallback text. The copilot must never hard-fail on chat.
- It is off by default and forced off in deterministic demo mode.
"""
from __future__ import annotations

from backend.chat.system_knowledge import system_knowledge_lines
from backend.config.settings import settings

_SYSTEM_INSTRUCTION = (
    "You are the AegisQA Copilot, embedded in a local QA orchestration system. "
    "Answer the user's question concisely and accurately using ONLY the AegisQA "
    "context provided below. If the context does not contain the answer, say so "
    "plainly and suggest what the user could ask instead. Do not invent system "
    "behavior, endpoints, or data. Never claim to have performed an action — you "
    "only provide information; controlled actions require separate confirmation."
)


def _retrieve_context(message: str, *, limit: int = 4) -> tuple[str, list[str]]:
    """Return a grounding context block and the list of cited chunk ids.

    S6: apply the same ``_KNOWLEDGE_RELEVANCE_FLOOR`` (0.33) the deterministic
    path uses, so the LLM is grounded ONLY on chunks with real lexical overlap.
    Without the floor, every chunk gets a small non-zero cosine and an unrelated
    question would inject low-relevance noise as if it were authoritative
    context — inviting a confidently-wrong grounded answer.
    """
    try:
        from backend.chat.response_builder import _KNOWLEDGE_RELEVANCE_FLOOR
        from backend.knowledge.local import get_local_knowledge_store

        store = get_local_knowledge_store()
        results = store.search(query=message, limit=limit)
    except Exception:  # noqa: BLE001 - retrieval is best-effort grounding.
        return "", []
    lines: list[str] = []
    citations: list[str] = []
    for result in results:
        if result.score < _KNOWLEDGE_RELEVANCE_FLOOR:
            continue
        citations.append(result.chunk.chunk_id)
        lines.append(f"[{result.chunk.chunk_id}] {result.chunk.title}: {result.excerpt}")
    return "\n".join(lines), citations


def answer_with_llm(message: str) -> str | None:
    """Answer a free-form question with the configured LLM, or None on failure.

    Returns the answer text (with a citations footer when RAG context was used),
    or None if the LLM is disabled/unavailable so the caller can fall back to the
    deterministic response.
    """
    if not settings.chat_llm_fallback_enabled:
        return None

    overview = "\n".join(system_knowledge_lines("overview"))
    rag_context, citations = _retrieve_context(message)
    grounding = f"System overview:\n{overview}"
    if rag_context:
        grounding += f"\n\nRetrieved documentation:\n{rag_context}"

    rendered_prompt = (
        f"{grounding}\n\n"
        f"User question: {message}\n\n"
        "Answer using only the AegisQA context above."
    )

    try:
        from backend.llm import llm_provider_registry

        provider = llm_provider_registry.create(settings.default_llm_provider)
        response = provider.complete(
            prompt_name="chat_freeform_v1",
            prompt_version="v1",
            rendered_prompt=rendered_prompt,
            system_instruction=_SYSTEM_INSTRUCTION,
            max_output_tokens=settings.chat_llm_max_output_tokens,
        )
    except Exception:  # noqa: BLE001 - chat must never hard-fail; fall back deterministically.
        return None

    text = (response.text or "").strip()
    if not text:
        return None
    if citations:
        text = f"{text}\n\nSources: {', '.join(citations)}"
    return text
