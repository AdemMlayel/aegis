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
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        if not settings.openai_compatible_base_url or not settings.openai_compatible_api_key:
            raise RuntimeError(
                "OpenAI-compatible provider is not configured. Set AEGISQA_OPENAI_COMPATIBLE_BASE_URL "
                "and AEGISQA_OPENAI_COMPATIBLE_API_KEY, or use a configured Ollama provider."
            )
        model = model_override or settings.openai_compatible_chat_model
        max_output_tokens = self._clamp_output_tokens(
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            rendered_prompt=rendered_prompt,
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction or "You are AegisQA."},
                {"role": "user", "content": rendered_prompt},
            ],
            "temperature": 0.1,
            **(
                {"max_tokens": max_output_tokens}
                if max_output_tokens is not None
                else {}
            ),
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
            with urllib.request.urlopen(
                request,
                timeout=settings.llm_http_timeout_seconds,
            ) as response:  # noqa: S310 - configured external endpoint.
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI-compatible provider request failed: {exc}") from exc
        text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        return LLMResponse(
            provider=self.spec.name,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=str(text).strip(),
            deterministic=False,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=int(
                usage.get("total_tokens")
                or input_tokens + output_tokens
            ),
        )

    @staticmethod
    def _clamp_output_tokens(
        *,
        max_output_tokens: int | None,
        system_instruction: str | None,
        rendered_prompt: str,
    ) -> int | None:
        """Clamp requested output tokens to fit the served model's context window.

        Servers like vLLM reject a request when ``prompt_tokens + max_tokens``
        exceeds ``max_model_len`` (HTTP 400), which would silently degrade the
        whole workflow to the mock provider. When a context window is configured,
        we leave room for the estimated prompt and never request more output than
        the window allows, down to a configured minimum.
        """
        window = settings.openai_compatible_context_window
        if window <= 0:
            return max_output_tokens

        # Rough token estimate (~4 chars/token), with headroom for chat framing.
        prompt_chars = len(system_instruction or "") + len(rendered_prompt)
        estimated_prompt_tokens = (prompt_chars // 4) + 32
        budget = window - estimated_prompt_tokens
        floor = settings.openai_compatible_min_output_tokens
        # Always leave at least the floor available, even if the estimate is tight.
        allowed = max(floor, budget)
        if max_output_tokens is None:
            return allowed
        return max(1, min(max_output_tokens, allowed))
