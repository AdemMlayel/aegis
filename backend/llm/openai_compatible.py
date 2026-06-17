from __future__ import annotations

from typing import Any

from backend.config.settings import settings
from backend.llm.base import BaseLLMProvider, LLMResponse, llm_provider_registry
from backend.llm.http_json import post_json


@llm_provider_registry.register(
    name="openai_compatible",
    mode="external",
    model=settings.openai_compatible_model,
    requires_external_api=True,
    description=(
        "OpenAI-compatible chat completions provider. Configure base URL, API key, and model through environment variables."
    ),
    configuration_status="configured" if settings.openai_compatible_api_key else "missing_api_key",
    configuration_keys=(
        "AEGISQA_OPENAI_COMPATIBLE_BASE_URL",
        "AEGISQA_OPENAI_COMPATIBLE_API_KEY",
        "AEGISQA_OPENAI_COMPATIBLE_MODEL",
    ),
)
class OpenAICompatibleLLMProvider(BaseLLMProvider):
    def complete(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        rendered_prompt: str,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        if not settings.openai_compatible_api_key:
            raise RuntimeError(
                "OpenAI-compatible LLM provider requires AEGISQA_OPENAI_COMPATIBLE_API_KEY."
            )
        base_url = settings.openai_compatible_base_url.rstrip("/")
        payload: dict[str, Any] = {
            "model": settings.openai_compatible_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_instruction or "You are AegisQA's QA automation intelligence provider.",
                },
                {
                    "role": "user",
                    "content": rendered_prompt,
                },
            ],
            "temperature": settings.openai_compatible_temperature,
        }
        response = post_json(
            url=f"{base_url}/chat/completions",
            payload=payload,
            headers={"Authorization": f"Bearer {settings.openai_compatible_api_key}"},
            timeout_seconds=settings.llm_http_timeout_seconds,
        )
        text = _extract_chat_completion_text(response)
        return LLMResponse(
            provider=self.spec.name,
            model=settings.openai_compatible_model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=text,
            deterministic=False,
        )


def _extract_chat_completion_text(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenAI-compatible response did not include choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("OpenAI-compatible response choice was invalid.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenAI-compatible response choice did not include a message.")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise RuntimeError("OpenAI-compatible response message content was empty.")
