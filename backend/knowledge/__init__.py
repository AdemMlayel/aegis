from __future__ import annotations

from backend.knowledge.base import KnowledgeChunk, KnowledgeSearchResult, KnowledgeStore
from backend.knowledge.ingestion import IngestionResult, ingest_local_document
from backend.knowledge.local import get_local_knowledge_store, reset_local_knowledge_store

__all__ = [
    "KnowledgeChunk",
    "KnowledgeSearchResult",
    "KnowledgeStore",
    "get_local_knowledge_store",
    "reset_local_knowledge_store",
    "ingest_local_document",
    "IngestionResult",
]
