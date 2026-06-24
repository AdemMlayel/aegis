from __future__ import annotations

from backend.config.settings import settings
from backend.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse, embedding_provider_registry
from backend.llm.ollama import OllamaUnavailableError, _post_json


@embedding_provider_registry.register(
    name="ollama_nomic_embed_text",
    mode="local",
    model=settings.ollama_embedding_model,
    dimensions=768,
    requires_external_api=False,
    description="Local Ollama embedding provider using Qwen, Nomic, or another configured embedding model.",
)
class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def embed(self, text: str) -> EmbeddingResponse:
        model = self.model_override or settings.ollama_embedding_model
        try:
            raw = _post_json(
                "/api/embeddings",
                {"model": model, "prompt": text},
                timeout=settings.ollama_timeout_seconds,
            )
        except OllamaUnavailableError as exc:
            raise OllamaUnavailableError(
                "Ollama embeddings are not available. Start Ollama, pull the configured embedding model, "
                "or set AEGISQA_DEFAULT_EMBEDDING_PROVIDER=local_hash_embeddings. "
                f"Details: {exc}"
            ) from exc
        vector = raw.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise OllamaUnavailableError(
                f"Ollama returned no embedding for model {model!r}."
            )
        return EmbeddingResponse(
            provider=self.spec.name,
            model=model,
            vector=tuple(float(value) for value in vector),
            deterministic=False,
        )
