from __future__ import annotations

import json
import urllib.error
import urllib.request

from backend.config.settings import settings
from backend.llm.base import BaseLLMProvider, LLMResponse, llm_provider_registry


@llm_provider_registry.register(
    name="openai_compatible",
    mode="external",
    model=settings.openai_compatible_chat_model,
    requires_external_api=True,
    description="Optional OpenAI-compatible provider for future cloud/internal model gateways. Disabled unless external connectors are explicitly enabled.",
)
class OpenAICompatibleLLMProvider(BaseLLMProvider):
    def complete(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        rendered_prompt: str,
        system_instruction: str | None = None,
        model_override: str | None = None,
    ) -> LLMResponse:
        if not settings.openai_compatible_base_url or not settings.openai_compatible_api_key:
            raise RuntimeError(
                "OpenAI-compatible provider is not configured. Set AEGISQA_OPENAI_COMPATIBLE_BASE_URL "
                "and AEGISQA_OPENAI_COMPATIBLE_API_KEY, or use mock_llm/ollama."
            )
        model = model_override or settings.openai_compatible_chat_model
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction or "You are AegisQA."},
                {"role": "user", "content": rendered_prompt},
            ],
            "temperature": 0.1,
        }
        url = f"{settings.openai_compatible_base_url.rstrip('/')}/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.openai_compatible_api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - configured external endpoint.
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI-compatible provider request failed: {exc}") from exc
        text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(
            provider=self.spec.name,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=str(text).strip(),
            deterministic=False,
        )
