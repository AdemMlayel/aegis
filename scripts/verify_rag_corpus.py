#!/usr/bin/env python3
"""Verify the local RAG knowledge corpus ingests and retrieves correctly.

This is a deterministic check intended for CI and demos. It forces the local
hash embedding provider (no Ollama required), rebuilds the local knowledge
store from ``fixtures/knowledge``, prints the corpus size and retrieval profile,
and runs a small set of probe queries, asserting each returns at least one hit.

Usage:
    python scripts/verify_rag_corpus.py

Reset / rebuild:
    The store is in-memory and rebuilt on every process start, so there is no
    persistent index to clear. To rebuild after editing fixtures/knowledge,
    simply re-run this script (or restart the backend). Generated documents
    ingested at runtime live under ``generated/`` (gitignored); remove that
    directory to drop them.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Force deterministic local embeddings so the check needs no external service.
os.environ.setdefault("AEGISQA_DETERMINISTIC_DEMO_MODE", "true")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.knowledge.local import (  # noqa: E402
    get_local_knowledge_store,
    reset_local_knowledge_store,
)

PROBE_QUERIES = (
    "requirement completeness checklist",
    "investigate a failed robot execution",
    "governance rules for tool execution",
    "synthetic test data teardown",
    "read robot framework output results",
    "low level design interpretation",
    "report generation traceability",
    "known failure session id mismatch",
)


def main() -> int:
    reset_local_knowledge_store()
    store = get_local_knowledge_store()
    chunks = store.list_chunks()
    profile = store.retrieval_profile()

    print(f"Ingested chunks : {len(chunks)}")
    print(f"Embedding model : {profile['embedding_model']} (dim {profile['embedding_dimension']})")
    print(f"Vector store    : {profile['vector_store']}")
    print(f"Reranker        : {profile['reranker']}")
    print()

    failures = 0
    for query in PROBE_QUERIES:
        results = store.search(query=query, limit=2)
        if not results:
            failures += 1
            print(f"  MISS  {query!r} -> no results")
            continue
        top = results[0]
        print(f"  HIT   {query!r} -> [{top.score:.3f}] {top.chunk.chunk_id}")

    print()
    if len(chunks) < 20:
        print(f"FAIL: expected a populated corpus (>=20 chunks), found {len(chunks)}")
        return 1
    if failures:
        print(f"FAIL: {failures} probe query/queries returned no results")
        return 1
    print(f"OK: corpus populated ({len(chunks)} chunks) and all {len(PROBE_QUERIES)} probes retrieved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
