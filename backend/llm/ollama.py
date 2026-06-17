from __future__ import annotations

from typing import Any

from backend.config.settings import settings
from backend.llm.base import BaseLLMProvider, LLMResponse, llm_provider_registry
from backend.llm.http_json import post_json


@llm_provider_registry.register(
    name="ollama",
    mode="local",
    model=settings.ollama_model,
    requires_external_api=False,
    description="Local Ollama chat provider. Configure base URL and model through environment variables.",
    configuration_status="configured",
    configuration_keys=("AEGISQA_OLLAMA_BASE_URL", "AEGISQA_OLLAMA_MODEL"),
)
class OllamaLLMProvider(BaseLLMProvider):
    def complete(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        rendered_prompt: str,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": rendered_prompt})
        payload: dict[str, Any] = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": settings.ollama_temperature},
        }
        response = post_json(
            url=f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            payload=payload,
            timeout_seconds=settings.llm_http_timeout_seconds,
        )
        text = _extract_ollama_text(response)
        return LLMResponse(
            provider=self.spec.name,
            model=settings.ollama_model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=text,
            deterministic=False,
        )


def _extract_ollama_text(response: dict[str, Any]) -> str:
    message = response.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    response_text = response.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()
    raise RuntimeError("Ollama response did not include message content.")
