from __future__ import annotations

from dataclasses import dataclass

from backend.intelligence.vector import (
    InMemoryVectorStore,
    LocalHybridReranker,
    VectorDocument,
    create_embedding_model,
)


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    title: str
    source: str
    text: str
    tags: tuple[str, ...] = ()


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
    def __init__(
        self,
        chunks: list[KnowledgeChunk],
        *,
        embedding_provider: str | None = None,
    ) -> None:
        self._chunks = list(chunks)
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in self._chunks}
        self._embedding_model = create_embedding_model(embedding_provider)
        self._vector_store = InMemoryVectorStore()
        self._reranker = LocalHybridReranker()
        self._index_chunks()

    def search(
        self,
        *,
        query: str,
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> list[KnowledgeSearchResult]:
        query_text = query.strip()
        if not query_text or limit <= 0:
            return []

        query_embedding = self._embedding_model.embed(query_text)
        candidate_limit = max(limit * 4, limit, len(self._chunks))
        hits = self._vector_store.search(
            query_embedding=query_embedding,
            namespace="knowledge",
            limit=candidate_limit,
        )
        reranked_hits = self._reranker.rerank(
            query=query_text,
            hits=hits,
            tags=tags,
            limit=candidate_limit,
        )
        results: list[KnowledgeSearchResult] = []
        for hit in reranked_hits:
            chunk = self._chunk_by_id.get(hit.document.document_id)
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
        return results[:limit]

    def list_chunks(self) -> list[KnowledgeChunk]:
        return list(self._chunks)

    def retrieval_profile(self) -> dict[str, object]:
        return {
            "name": "local_knowledge",
            "chunks": len(self._chunks),
            "embedding_model": self._embedding_model.spec.name,
            "embedding_dimension": self._embedding_model.spec.dimension,
            "vector_store": InMemoryVectorStore.spec["name"],
            "reranker": LocalHybridReranker.spec["name"],
        }

    def _index_chunks(self) -> None:
        for chunk in self._chunks:
            document = VectorDocument(
                document_id=chunk.chunk_id,
                namespace="knowledge",
                text=" ".join([chunk.title, chunk.text, " ".join(chunk.tags)]),
                metadata={
                    "title": chunk.title,
                    "source": chunk.source,
                },
                tags=chunk.tags,
            )
            self._vector_store.upsert(
                document=document,
                embedding=self._embedding_model.embed(document.text),
            )
