from __future__ import annotations

from backend.knowledge.base import KnowledgeChunk, KnowledgeSearchResult, KnowledgeStore
from backend.knowledge.local import get_local_knowledge_store

__all__ = [
    "KnowledgeChunk",
    "KnowledgeSearchResult",
    "KnowledgeStore",
    "get_local_knowledge_store",
]
