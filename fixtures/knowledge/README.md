# Synthetic Knowledge Corpus (RAG)

This directory holds the synthetic documentation that populates the local RAG knowledge
store. The backend ingests every `.md`, `.txt`, and `.rst` file under this tree
automatically at startup (see `backend/knowledge/ingestion.py`), chunks it, embeds it, and
makes it retrievable by the assistant with source citations.

## Why synthetic

These documents are **synthetic**. They are modeled on the structure, behavior, and
complexity of the real QA workflow but contain no real hostnames, addresses, credentials,
tokens, customer names, internal identifiers, or proprietary content. All component and
identity references are neutral placeholders such as `INTERNAL_SERVICE_A`,
`TEST_SUBSCRIBER_A`, `AUTH_PROVIDER_PLACEHOLDER`, and `THRESHOLD_PLACEHOLDER`.

## Layout

- `procedures/` — ticket analysis, failure investigation, LLD interpretation, report
  generation, and synthetic test-data resolution procedures.
- `robot/` — Robot Framework usage notes and execution-result interpretation.
- `governance/` — governance and safety rules the backend enforces.
- `failures/` — known failure signatures and troubleshooting evidence patterns for
  historical cross-reference during investigation.
- `usage/` — assistant usage and demo scenario walkthrough.
- `qa/` — general local-demo testing guidelines.

## How it maps to the real workflow

Each document corresponds to a stage or concern in the real pipeline (ticket
understanding, coverage, automation, execution, investigation, reporting, governance) and
to the sanitized reference corpus under `fixtures/reference_corpus/`. The mapping lets the
assistant ground its answers in the same concepts the agents use, without exposing any
sensitive source material.

## Adding documents

Drop a new `.md` file in the appropriate subfolder. The title is taken from the first
`#` heading; tags are derived from the folder path and filename. Re-run the verification
script (below) or restart the backend to pick it up.

## Verify retrieval

```bash
python scripts/verify_rag_corpus.py
```

This forces deterministic local embeddings (no Ollama required), rebuilds the store,
prints the corpus size and retrieval profile, and asserts that a set of probe queries each
return at least one hit.

## Reset / rebuild

The store is in-memory and rebuilt on every process start — there is no persistent index
to clear. Documents ingested at runtime via the API are written under `generated/`
(gitignored); delete that directory to drop them.
