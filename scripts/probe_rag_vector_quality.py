"""Empirical probe: is the default RAG vector channel semantically meaningful?

Hypothesis: the registered default embedding (local_hash_embeddings) hashes the
WHOLE text via SHA256, so two texts that share most words still get
uncorrelated vectors — making cosine similarity ~noise. Retrieval would then be
carried entirely by the reranker's lexical overlap, not the vector channel.

This prints, for a banking query against the seeded chunks:
  - the vector_score the default embedding assigns each chunk
  - whether the most lexically-relevant chunk actually wins on vector score
"""
from __future__ import annotations

from backend.config.settings import settings
from backend.embeddings.base import deterministic_hash_embedding
from backend.intelligence.vector import LocalHashEmbeddingModel, _cosine_similarity
from backend.knowledge import get_local_knowledge_store

print("default_embedding_provider:", settings.default_embedding_provider)
print()

# 1) Direct demonstration: near-identical texts, whole-text hash vs token hash.
a = "money transfer balance consistency regression"
b = "money transfer balance consistency regression checks"  # +1 word
whole_a = deterministic_hash_embedding(a, dimensions=32)
whole_b = deterministic_hash_embedding(b, dimensions=32)
tok = LocalHashEmbeddingModel()
tok_a, tok_b = tok.embed(a), tok.embed(b)
print("Near-identical texts (differ by ONE word):")
print(f"  whole-text SHA256 cosine : {_cosine_similarity(whole_a, whole_b):.3f}")
print(f"  token-bucket   cosine    : {_cosine_similarity(tok_a, tok_b):.3f}")
print()

# 2) Real retrieval: vector_score per chunk for a banking query.
store = get_local_knowledge_store()
results = store.search(query="money transfer balance regression risk", limit=5)
print("Query: 'money transfer balance regression risk'")
print("Per-chunk vector_score (default embedding) vs final rerank:")
for r in results:
    print(f"  {r.chunk.chunk_id:14} vector={r.vector_score:+.3f}  rerank={r.rerank_score:.3f}  matched={list(r.matched_terms)[:5]}")
print()
print("If vector scores are ~0 / unordered while the right chunk still wins on")
print("rerank, the vector channel is dead weight and lexical overlap is doing the work.")
