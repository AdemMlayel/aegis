from __future__ import annotations

from backend.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse, deterministic_hash_embedding, embedding_provider_registry


@embedding_provider_registry.register(
    name="local_hash_embeddings",
    mode="local",
    model="aegisqa-local-hash-embedding-v1",
    dimensions=32,
    requires_external_api=False,
    description="Deterministic local hash embeddings for reproducible RAG and memory tests.",
)
class LocalHashEmbeddingProvider(BaseEmbeddingProvider):
    def embed(self, text: str) -> EmbeddingResponse:
        return EmbeddingResponse(
            provider=self.spec.name,
            model=self.spec.model,
            vector=deterministic_hash_embedding(text, dimensions=self.spec.dimensions),
            deterministic=True,
        )
