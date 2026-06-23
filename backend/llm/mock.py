from __future__ import annotations

import re

from backend.llm.base import BaseLLMProvider, LLMResponse, llm_provider_registry


@llm_provider_registry.register(
    name="mock_llm",
    mode="mock",
    model="aegisqa-deterministic-mock-v1",
    requires_external_api=False,
    description="Deterministic local LLM provider used for architecture validation and tests.",
)
class MockLLMProvider(BaseLLMProvider):
    def complete(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        rendered_prompt: str,
        system_instruction: str | None = None,
        model_override: str | None = None,
    ) -> LLMResponse:
        compact = " ".join(rendered_prompt.split())
        ticket_match = re.search(r"Ticket:\s*([^|]+)", compact)
        ticket_title = ticket_match.group(1).strip() if ticket_match else "the ticket"
        knowledge_count = rendered_prompt.count("KNOWLEDGE[")
        memory_count = rendered_prompt.count("MEMORY[")
        text = (
            f"Mock AI analysis for {ticket_title}: used {knowledge_count} knowledge "
            f"chunk(s) and {memory_count} episodic memory item(s)."
        )
        return LLMResponse(
            provider=self.spec.name,
            model=model_override or self.spec.model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=text,
            deterministic=True,
        )
