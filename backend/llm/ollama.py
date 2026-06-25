from __future__ import annotations

import json
import urllib.error
import urllib.request

from backend.config.settings import settings
from backend.llm.base import BaseLLMProvider, LLMResponse, llm_provider_registry


class OllamaUnavailableError(RuntimeError):
    pass


@llm_provider_registry.register(
    name="ollama",
    mode="local",
    model=settings.ollama_chat_model,
    requires_external_api=False,
    description="Local Ollama chat provider for developer/PM demos. Requires Ollama running locally and the configured model pulled.",
)
class OllamaLLMProvider(BaseLLMProvider):
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
        model = model_override or settings.ollama_chat_model
        prompt = rendered_prompt if not system_instruction else f"{system_instruction}\n\n{rendered_prompt}"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                **(
                    {"num_predict": max_output_tokens}
                    if max_output_tokens is not None
                    else {}
                ),
            },
        }
        try:
            raw = _post_json("/api/generate", payload, timeout=settings.ollama_timeout_seconds)
        except OllamaUnavailableError as exc:
            raise OllamaUnavailableError(
                "Ollama is not available. Start Ollama, pull the configured chat model, "
                f"or select a configured external provider. Details: {exc}"
            ) from exc
        text = str(raw.get("response") or "").strip()
        if not text:
            raise OllamaUnavailableError(
                f"Ollama returned an empty response for model {model!r}."
            )
        return LLMResponse(
            provider=self.spec.name,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            text=text,
            deterministic=False,
            input_tokens=int(raw.get("prompt_eval_count") or 0),
            output_tokens=int(raw.get("eval_count") or 0),
            total_tokens=(
                int(raw.get("prompt_eval_count") or 0)
                + int(raw.get("eval_count") or 0)
            ),
        )


def list_ollama_models() -> list[str]:
    try:
        raw = _get_json("/api/tags", timeout=5)
    except OllamaUnavailableError:
        return []
    models = raw.get("models", [])
    return sorted(str(item.get("name")) for item in models if item.get("name"))


def ollama_health() -> dict[str, object]:
    models = list_ollama_models()
    chat_model = settings.ollama_chat_model
    embedding_model = settings.ollama_embedding_model
    return {
        "available": bool(models),
        "base_url": settings.ollama_base_url,
        "chat_model": chat_model,
        "embedding_model": embedding_model,
        "installed_models": models,
        "chat_model_ready": chat_model in models,
        "embedding_model_ready": embedding_model in models,
        "message": _health_message(models, chat_model, embedding_model),
    }


def _health_message(models: list[str], chat_model: str, embedding_model: str) -> str:
    if not models:
        return "Ollama is not reachable. Start Ollama or use a configured external LLM provider."
    missing = [model for model in (chat_model, embedding_model) if model not in models]
    if missing:
        return "Ollama is reachable, but missing model(s): " + ", ".join(missing)
    return "Ollama is reachable and configured models are available."


def _extract_ollama_text(payload: dict[str, object]) -> str:
    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    response = payload.get("response")
    if isinstance(response, str) and response.strip():
        return response.strip()
    raise OllamaUnavailableError("Ollama returned an empty text response.")


def _post_json(path: str, payload: dict[str, object], *, timeout: int) -> dict[str, object]:
    url = f"{settings.ollama_base_url.rstrip('/')}{path}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - local configurable dev endpoint.
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaUnavailableError(str(exc)) from exc


def _get_json(path: str, *, timeout: int) -> dict[str, object]:
    url = f"{settings.ollama_base_url.rstrip('/')}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - local configurable dev endpoint.
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaUnavailableError(str(exc)) from exc
