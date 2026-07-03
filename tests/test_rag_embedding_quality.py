"""Regression tests for RAG embedding quality.

These pin the property that broke retrieval before: the default local embedding
must be *semantically meaningful* — texts that share tokens must land close in
cosine space — not a whole-text fingerprint that scatters near-identical texts
to near-orthogonal vectors. If someone reverts to whole-text SHA256 hashing,
these fail.
"""
from __future__ import annotations

from backend.embeddings.base import deterministic_hash_embedding
from backend.embeddings.base import embedding_provider_registry
from backend.intelligence.vector import _cosine_similarity
from backend.knowledge import get_local_knowledge_store


def test_shared_tokens_yield_high_cosine() -> None:
    a = deterministic_hash_embedding("money transfer balance consistency regression")
    b = deterministic_hash_embedding("money transfer balance consistency regression checks")
    # One-word delta must stay clearly similar (token bucketing), not orthogonal.
    assert _cosine_similarity(a, b) > 0.8


def test_unrelated_texts_yield_low_cosine() -> None:
    a = deterministic_hash_embedding("money transfer balance regression banking risk")
    b = deterministic_hash_embedding("robot framework keyword library import syntax dryrun")
    assert _cosine_similarity(a, b) < 0.4


def test_embedding_is_deterministic_and_normalized() -> None:
    v1 = deterministic_hash_embedding("money transfer regression", dimensions=32)
    v2 = deterministic_hash_embedding("money transfer regression", dimensions=32)
    assert v1 == v2
    assert len(v1) == 32
    # L2-normalized (unit length) when any token is present.
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-3


def test_empty_text_is_zero_vector() -> None:
    assert deterministic_hash_embedding("", dimensions=16) == tuple([0.0] * 16)
    # Sub-3-char-only text has no usable tokens → zero vector (no signal).
    assert deterministic_hash_embedding("a an", dimensions=16) == tuple([0.0] * 16)


def test_vector_channel_ranks_relevant_chunk_first() -> None:
    # The end-to-end property: for a banking query, the banking chunk must win on
    # the VECTOR score, not merely survive on lexical rerank. This is exactly
    # what was broken — the relevant chunk scored near-lowest on vector before.
    store = get_local_knowledge_store()
    results = store.search(query="money transfer balance regression risk", limit=5)
    assert results, "expected retrieval results"
    top = max(results, key=lambda r: r.vector_score)
    assert top.chunk.chunk_id == "KB-BANK-001"
    # And it should also be the final winner.
    assert results[0].chunk.chunk_id == "KB-BANK-001"


def test_default_provider_uses_semantic_embedding() -> None:
    # The registered default provider must produce the semantic embedding too.
    provider = embedding_provider_registry.create("local_hash_embeddings")
    a = provider.embed("balance regression money transfer").vector
    b = provider.embed("balance regression money transfer audit").vector
    assert _cosine_similarity(a, b) > 0.8
