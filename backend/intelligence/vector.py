from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.config.settings import settings
from backend.embeddings import embedding_provider_registry


def tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(term) > 2}


@dataclass(frozen=True)
class EmbeddingSpec:
    name: str = "local_hash_embedding"
    dimension: int = 64
    deterministic: bool = True
    description: str = "Deterministic local hashing embeddings for architecture tests."


class LocalHashEmbeddingModel:
    spec = EmbeddingSpec()

    def embed(self, text: str) -> tuple[float, ...]:
        values = [0.0] * self.spec.dimension
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.spec.dimension
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            values[index] += sign
        length = math.sqrt(sum(value * value for value in values))
        if length == 0:
            return tuple(values)
        return tuple(round(value / length, 6) for value in values)


class EmbeddingProviderModel:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        self.provider = embedding_provider_registry.create(provider_name)
        self._fallback_provider = embedding_provider_registry.create(
            "local_hash_embeddings"
        )
        provider_spec = self.provider.spec
        self.spec = EmbeddingSpec(
            name=provider_spec.name,
            dimension=provider_spec.dimensions,
            deterministic=provider_spec.name == "local_hash_embeddings",
            description=provider_spec.description,
        )

    def embed(self, text: str) -> tuple[float, ...]:
        try:
            return self.provider.embed(text).vector
        except Exception:  # noqa: BLE001 - retrieval must degrade safely for local demos.
            if self.provider_name == "local_hash_embeddings":
                raise
            return self._fallback_provider.embed(text).vector


def create_embedding_model(
    provider_name: str | None = None,
) -> LocalHashEmbeddingModel | EmbeddingProviderModel:
    selected_provider = provider_name or settings.default_embedding_provider
    if embedding_provider_registry.has(selected_provider):
        return EmbeddingProviderModel(selected_provider)
    return LocalHashEmbeddingModel()


@dataclass(frozen=True)
class VectorDocument:
    document_id: str
    namespace: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str | None = None


@dataclass(frozen=True)
class VectorSearchHit:
    document: VectorDocument
    vector_score: float


@dataclass(frozen=True)
class RerankedVectorHit:
    document: VectorDocument
    vector_score: float
    lexical_score: float
    rerank_score: float
    matched_terms: tuple[str, ...]
    retention_status: str


class InMemoryVectorStore:
    spec = {
        "name": "local_in_memory_vector",
        "mode": "local",
        "description": "Local in-memory vector index used for deterministic RAG and memory retrieval.",
    }

    def __init__(self) -> None:
        self._documents: dict[str, VectorDocument] = {}
        self._embeddings: dict[str, tuple[float, ...]] = {}
        self._invalidated: set[str] = set()

    def upsert(self, *, document: VectorDocument, embedding: tuple[float, ...]) -> None:
        self._documents[document.document_id] = document
        self._embeddings[document.document_id] = embedding
        self._invalidated.discard(document.document_id)

    def invalidate(self, document_id: str) -> bool:
        if document_id not in self._documents:
            return False
        self._invalidated.add(document_id)
        return True

    def prune_expired(self, *, now: datetime | None = None) -> list[str]:
        current = now or datetime.now(UTC)
        expired: list[str] = []
        for document_id, document in self._documents.items():
            if not document.expires_at:
                continue
            expires_at = datetime.fromisoformat(document.expires_at)
            if expires_at <= current:
                self._invalidated.add(document_id)
                expired.append(document_id)
        return expired

    def search(
        self,
        *,
        query_embedding: tuple[float, ...],
        namespace: str | None = None,
        limit: int = 10,
    ) -> list[VectorSearchHit]:
        self.prune_expired()
        hits: list[VectorSearchHit] = []
        for document_id, document in self._documents.items():
            if document_id in self._invalidated:
                continue
            if namespace and document.namespace != namespace:
                continue
            embedding = self._embeddings.get(document_id)
            if embedding is None:
                continue
            hits.append(
                VectorSearchHit(
                    document=document,
                    vector_score=round(_cosine_similarity(query_embedding, embedding), 3),
                )
            )
        return sorted(hits, key=lambda hit: (-hit.vector_score, hit.document.document_id))[:limit]

    def list_documents(self) -> list[VectorDocument]:
        return [
            document
            for document_id, document in self._documents.items()
            if document_id not in self._invalidated
        ]


class LocalHybridReranker:
    spec = {
        "name": "local_hybrid_reranker",
        "mode": "local",
        "description": "Combines vector similarity, lexical overlap, and tag matches deterministically.",
    }

    def rerank(
        self,
        *,
        query: str,
        hits: list[VectorSearchHit],
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> list[RerankedVectorHit]:
        query_terms = tokenize(query)
        tag_terms = {tag.lower() for tag in (tags or [])}
        reranked: list[RerankedVectorHit] = []
        for hit in hits:
            document_terms = tokenize(
                " ".join(
                    [
                        hit.document.text,
                        str(hit.document.metadata.get("title", "")),
                        " ".join(hit.document.tags),
                    ]
                )
            )
            matched_terms = tuple(sorted(query_terms & document_terms))
            tag_matches = tag_terms & {tag.lower() for tag in hit.document.tags}
            lexical_score = len(matched_terms) / max(len(query_terms) or 1, 1)
            tag_score = min(0.2, 0.08 * len(tag_matches))
            rerank_score = min(
                1.0,
                (0.46 * max(hit.vector_score, 0.0)) + (0.46 * lexical_score) + tag_score,
            )
            reranked.append(
                RerankedVectorHit(
                    document=hit.document,
                    vector_score=hit.vector_score,
                    lexical_score=round(lexical_score, 3),
                    rerank_score=round(rerank_score, 3),
                    matched_terms=matched_terms,
                    retention_status="active",
                )
            )
        return sorted(
            reranked,
            key=lambda hit: (-hit.rerank_score, -hit.lexical_score, hit.document.document_id),
        )[:limit]


def retrieval_profile() -> dict[str, object]:
    embedding = create_embedding_model().spec
    return {
        "embedding_model": {
            "name": embedding.name,
            "dimension": embedding.dimension,
            "deterministic": embedding.deterministic,
            "description": embedding.description,
        },
        "vector_store": InMemoryVectorStore.spec,
        "reranker": LocalHybridReranker.spec,
    }


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
