from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.intelligence.vector import (
    InMemoryVectorStore,
    LocalHashEmbeddingModel,
    LocalHybridReranker,
    VectorDocument,
)


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    title: str
    source: str
    text: str
    tags: tuple[str, ...] = ()
    created_at: str | None = None
    expires_at: str | None = None


@dataclass(frozen=True)
class KnowledgeSearchResult:
    chunk: KnowledgeChunk
    score: float
    matched_terms: tuple[str, ...] = ()
    vector_score: float = 0.0
    rerank_score: float = 0.0
    retention_status: str = "active"

    @property
    def ref(self) -> str:
        return self.chunk.chunk_id

    @property
    def excerpt(self) -> str:
        text = " ".join(self.chunk.text.split())
        return text if len(text) <= 220 else f"{text[:217]}..."


class KnowledgeStore:
    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        self._chunks = chunks
        self._embedding_model = LocalHashEmbeddingModel()
        self._vector_store = InMemoryVectorStore()
        self._reranker = LocalHybridReranker()
        self._chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        for chunk in chunks:
            self._vector_store.upsert(
                document=VectorDocument(
                    document_id=chunk.chunk_id,
                    namespace="knowledge",
                    text=" ".join([chunk.title, chunk.text]),
                    tags=chunk.tags,
                    expires_at=chunk.expires_at,
                    metadata={
                        "title": chunk.title,
                        "source": chunk.source,
                        "created_at": chunk.created_at,
                    },
                ),
                embedding=self._embedding_model.embed(" ".join([chunk.title, chunk.text, " ".join(chunk.tags)])),
            )

    def search(self, *, query: str, tags: list[str] | None = None, limit: int = 3) -> list[KnowledgeSearchResult]:
        results: list[KnowledgeSearchResult] = []
        hits = self._vector_store.search(
            query_embedding=self._embedding_model.embed(query),
            namespace="knowledge",
            limit=max(limit * 4, limit),
        )
        reranked_hits = self._reranker.rerank(query=query, hits=hits, tags=tags, limit=limit)
        for hit in reranked_hits:
            chunk = self._chunks_by_id.get(hit.document.document_id)
            if chunk is None:
                continue
            results.append(
                KnowledgeSearchResult(
                    chunk=chunk,
                    score=hit.rerank_score,
                    matched_terms=hit.matched_terms,
                    vector_score=hit.vector_score,
                    rerank_score=hit.rerank_score,
                    retention_status=hit.retention_status,
                )
            )
        return results

    def list_chunks(self) -> list[KnowledgeChunk]:
        active_ids = {document.document_id for document in self._vector_store.list_documents()}
        return [chunk for chunk in self._chunks if chunk.chunk_id in active_ids]

    def invalidate(self, chunk_id: str) -> bool:
        return self._vector_store.invalidate(chunk_id)

    def retrieval_profile(self) -> dict[str, object]:
        return {
            "chunk_count": len(self._chunks),
            "active_chunk_count": len(self.list_chunks()),
            "embedding_model": self._embedding_model.spec.name,
            "vector_store": self._vector_store.spec["name"],
            "reranker": self._reranker.spec["name"],
        }


def _tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(term) > 2}
