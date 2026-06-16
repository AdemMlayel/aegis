from __future__ import annotations

import re
from dataclasses import dataclass, field


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

    def search(self, *, query: str, tags: list[str] | None = None, limit: int = 3) -> list[KnowledgeSearchResult]:
        query_terms = _tokenize(query)
        tag_terms = {tag.lower() for tag in (tags or [])}
        results: list[KnowledgeSearchResult] = []
        for chunk in self._chunks:
            chunk_terms = _tokenize(" ".join([chunk.title, chunk.text, " ".join(chunk.tags)]))
            matched_terms = tuple(sorted(query_terms & chunk_terms))
            tag_matches = tag_terms & {tag.lower() for tag in chunk.tags}
            if not matched_terms and not tag_matches:
                continue
            score = len(matched_terms) + (1.5 * len(tag_matches))
            score = score / max(len(query_terms) or 1, 1)
            results.append(
                KnowledgeSearchResult(
                    chunk=chunk,
                    score=round(min(score, 1.0), 3),
                    matched_terms=matched_terms,
                )
            )
        return sorted(results, key=lambda result: (-result.score, result.chunk.chunk_id))[:limit]

    def list_chunks(self) -> list[KnowledgeChunk]:
        return list(self._chunks)


def _tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(term) > 2}
