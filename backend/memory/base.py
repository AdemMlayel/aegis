from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from backend.intelligence.vector import (
    InMemoryVectorStore,
    LocalHybridReranker,
    VectorDocument,
    create_embedding_model,
)


@dataclass(frozen=True)
class EpisodicMemoryEntry:
    memory_id: str
    title: str
    summary: str
    tags: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    outcome: Literal["passed", "failed", "skipped", "unknown"] = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class EpisodicMemorySearchResult:
    entry: EpisodicMemoryEntry
    score: float
    matched_terms: tuple[str, ...] = ()
    vector_score: float = 0.0
    rerank_score: float = 0.0
    retention_status: str = "active"

    @property
    def ref(self) -> str:
        return self.entry.memory_id


class EpisodicMemoryStore:
    def __init__(
        self,
        entries: list[EpisodicMemoryEntry] | None = None,
        *,
        embedding_provider: str | None = None,
    ) -> None:
        self._entries = list(entries or [])
        self._entry_by_id = {entry.memory_id: entry for entry in self._entries}
        self._embedding_model = create_embedding_model(embedding_provider)
        self._vector_store = InMemoryVectorStore()
        self._reranker = LocalHybridReranker()
        for entry in self._entries:
            self._index_entry(entry)

    def search(
        self,
        *,
        query: str,
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> list[EpisodicMemorySearchResult]:
        query_text = query.strip()
        if not query_text or limit <= 0:
            return []

        query_embedding = self._embedding_model.embed(query_text)
        candidate_limit = max(limit * 4, limit, len(self._entries))
        hits = self._vector_store.search(
            query_embedding=query_embedding,
            namespace="episodic_memory",
            limit=candidate_limit,
        )
        reranked_hits = self._reranker.rerank(
            query=query_text,
            hits=hits,
            tags=tags,
            limit=candidate_limit,
        )
        results: list[EpisodicMemorySearchResult] = []
        for hit in reranked_hits:
            entry = self._entry_by_id.get(hit.document.document_id)
            if entry is None:
                continue
            results.append(
                EpisodicMemorySearchResult(
                    entry=entry,
                    score=hit.rerank_score,
                    matched_terms=hit.matched_terms,
                    vector_score=hit.vector_score,
                    rerank_score=hit.rerank_score,
                    retention_status=hit.retention_status,
                )
            )
        return results[:limit]

    def archive(
        self,
        *,
        title: str,
        summary: str,
        tags: list[str],
        source_refs: list[str],
        outcome: Literal["passed", "failed", "skipped", "unknown"] = "unknown",
    ) -> EpisodicMemoryEntry:
        entry = EpisodicMemoryEntry(
            memory_id=f"mem-{uuid4().hex[:12]}",
            title=title,
            summary=summary,
            tags=tuple(tags),
            source_refs=tuple(source_refs),
            outcome=outcome,
        )
        self._entries.append(entry)
        self._entry_by_id[entry.memory_id] = entry
        self._index_entry(entry)
        return entry

    def list_entries(self) -> list[EpisodicMemoryEntry]:
        return list(self._entries)

    def retrieval_profile(self) -> dict[str, object]:
        return {
            "name": "local_episodic_memory",
            "entries": len(self._entries),
            "embedding_model": self._embedding_model.spec.name,
            "embedding_dimension": self._embedding_model.spec.dimension,
            "vector_store": InMemoryVectorStore.spec["name"],
            "reranker": LocalHybridReranker.spec["name"],
        }

    def _index_entry(self, entry: EpisodicMemoryEntry) -> None:
        document = VectorDocument(
            document_id=entry.memory_id,
            namespace="episodic_memory",
            text=" ".join([entry.title, entry.summary, " ".join(entry.tags)]),
            metadata={
                "title": entry.title,
                "outcome": entry.outcome,
                "source_refs": list(entry.source_refs),
            },
            tags=entry.tags,
            created_at=entry.created_at,
        )
        self._vector_store.upsert(
            document=document,
            embedding=self._embedding_model.embed(document.text),
        )
