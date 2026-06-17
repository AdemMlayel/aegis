from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from backend.config.settings import settings
from backend.intelligence.vector import (
    InMemoryVectorStore,
    LocalHashEmbeddingModel,
    LocalHybridReranker,
    VectorDocument,
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
    expires_at: str | None = None


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
    def __init__(self, entries: list[EpisodicMemoryEntry] | None = None) -> None:
        self._entries = entries or []
        self._embedding_model = LocalHashEmbeddingModel()
        self._vector_store = InMemoryVectorStore()
        self._reranker = LocalHybridReranker()
        self._entries_by_id: dict[str, EpisodicMemoryEntry] = {}
        for entry in self._entries:
            self._index_entry(entry)

    def search(self, *, query: str, tags: list[str] | None = None, limit: int = 3) -> list[EpisodicMemorySearchResult]:
        results: list[EpisodicMemorySearchResult] = []
        hits = self._vector_store.search(
            query_embedding=self._embedding_model.embed(query),
            namespace="memory",
            limit=max(limit * 4, limit),
        )
        reranked_hits = self._reranker.rerank(query=query, hits=hits, tags=tags, limit=limit)
        for hit in reranked_hits:
            entry = self._entries_by_id.get(hit.document.document_id)
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
        return results

    def archive(
        self,
        *,
        title: str,
        summary: str,
        tags: list[str],
        source_refs: list[str],
        outcome: Literal["passed", "failed", "skipped", "unknown"] = "unknown",
        retention_days: int | None = None,
    ) -> EpisodicMemoryEntry:
        retention = settings.memory_retention_days if retention_days is None else retention_days
        expires_at = None
        if retention > 0:
            expires_at = (datetime.now(UTC) + timedelta(days=retention)).isoformat()
        entry = EpisodicMemoryEntry(
            memory_id=f"mem-{uuid4().hex[:12]}",
            title=title,
            summary=summary,
            tags=tuple(tags),
            source_refs=tuple(source_refs),
            outcome=outcome,
            expires_at=expires_at,
        )
        self._entries.append(entry)
        self._index_entry(entry)
        return entry

    def list_entries(self) -> list[EpisodicMemoryEntry]:
        active_ids = {document.document_id for document in self._vector_store.list_documents()}
        return [entry for entry in self._entries if entry.memory_id in active_ids]

    def invalidate(self, memory_id: str) -> bool:
        return self._vector_store.invalidate(memory_id)

    def prune_expired(self) -> list[str]:
        return self._vector_store.prune_expired()

    def retrieval_profile(self) -> dict[str, object]:
        return {
            "entry_count": len(self._entries),
            "active_entry_count": len(self.list_entries()),
            "retention_days": settings.memory_retention_days,
            "embedding_model": self._embedding_model.spec.name,
            "vector_store": self._vector_store.spec["name"],
            "reranker": self._reranker.spec["name"],
        }

    def _index_entry(self, entry: EpisodicMemoryEntry) -> None:
        self._entries_by_id[entry.memory_id] = entry
        self._vector_store.upsert(
            document=VectorDocument(
                document_id=entry.memory_id,
                namespace="memory",
                text=" ".join([entry.title, entry.summary]),
                tags=entry.tags,
                expires_at=entry.expires_at,
                metadata={
                    "title": entry.title,
                    "outcome": entry.outcome,
                    "source_refs": list(entry.source_refs),
                    "created_at": entry.created_at,
                },
            ),
            embedding=self._embedding_model.embed(" ".join([entry.title, entry.summary, " ".join(entry.tags)])),
        )


def _tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(term) > 2}
