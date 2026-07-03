# AegisQA Architecture

## Runtime Flow

```text
ticket
  -> requirement_agent
  -> coverage_planner
  -> test_case_generator
  -> test_data_resolver
  -> automation_generator
  -> validator
  -> validation_retry_gate
  -> human_approval
  -> execution_dispatcher
  -> investigation_coordinator
  -> memory_archiver
  -> report_generator
```

Controlled sessions expose the same nodes through autonomous,
approval-required, and step-by-step modes. Stage services do not duplicate agent
logic; they coordinate persisted state around the graph nodes.

## Contract Boundaries

- Agents declare the skills they may invoke.
- Skills declare the tools they may invoke.
- Tools own provider and external-system access.
- Governance validates agent identity, policy, capability, and model budgets.
- Tool and model calls produce audit and observability records.

Primary contracts:

```text
backend/agents/base.py
backend/skills/base.py
backend/tools/base.py
backend/graph/state.py
backend/graph/workflow.py
backend/services/workflow_control.py
```

## Providers

LLM providers:

- `openai_compatible`: external server-side API integration.
- `ollama`: private local inference with role-specific model routing.
- `mock_llm`: deterministic automated-test and provider-failure fallback.

Embedding providers:

- `ollama_nomic_embed_text`: local model embeddings.
- `local_hash_embeddings`: deterministic test/offline fallback.

Execution providers:

- `robot`: local Robot Framework execution and evidence capture.
- `mock`: deterministic automated-test adapter.

Ticket data is intentionally local and Jira-shaped. The connector contract can
be replaced by a real Jira provider without changing workflow agents.

## Knowledge And Retrieval (RAG)

The knowledge layer grounds assistant answers in a synthetic documentation corpus.

- Source documents live under `fixtures/knowledge/` (`.md`/`.txt`/`.rst`) and are
  ingested automatically at startup by `backend/knowledge/ingestion.py`. Runtime uploads
  are stored as JSON under the generated root.
- Documents are chunked (paragraph-aware, ~900 chars), embedded, and indexed in a local
  in-memory vector store (`backend/intelligence/vector.py`).
- Retrieval combines vector similarity with a deterministic hybrid reranker (lexical
  overlap + tag match), returning scored chunks with source references for citation.
- Embeddings use `ollama_nomic_embed_text` when available, falling back to deterministic
  `local_hash_embeddings` (used by deterministic demo mode and tests).
- The corpus is synthetic and sanitized — placeholders only, no real data. See
  `fixtures/knowledge/README.md`. Verify retrieval with
  `python scripts/verify_rag_corpus.py`.

## Persistence

SQLite migrations own the local schema. Repositories persist:

- workflow contexts and summaries;
- ticket fixtures and comments;
- audit and workflow timeline events;
- artifact revisions;
- execution queue, results, and logs;
- request, agent, and model telemetry;
- token reservations and usage.

Generated Robot files, execution evidence, Git handoff payloads, and memory
archives live under the configurable generated root. Tests use
`generated/test-runtime`, so they cannot pollute the live dashboard.

The local worker polls the durable execution queue. The Celery worker uses Redis
and the same execution service contract. Multi-instance production deployment
still requires PostgreSQL and shared governance/circuit state.

## Review And Evidence

Artifact edits create immutable revisions and invalidate downstream validation
and approval. Validation retries are traced explicitly. Final report packages
contain typed context, tests, validation, decisions, Robot files, execution
evidence, memory references, and a SHA-256 manifest.

Filesystem reads are constrained to the configured generated root.

## Security And Operations

Local permissive auth supports demos. Strict mode requires the configured
development identity headers or token. Capabilities protect ticket, workflow,
approval, execution, artifact, and audit routes.

Middleware provides request IDs, structured logs, rate limits, timeouts,
provider circuit breakers, token reservations, cost accounting, health probes,
and Prometheus-compatible metrics. Enterprise identity, distributed limit
state, OpenTelemetry export, and alert delivery remain production work.

The decision to keep this native governance layer rather than adopt an external
agent-governance framework (e.g. NVIDIA NeMo Agent Toolkit) is recorded in
`docs/adr/0001-agent-governance-approach.md`.

## Source Packaging

`scripts/package_clean.py` excludes Git metadata, virtual environments,
dependency directories, caches, generated output, environment secrets, build
artifacts, and package metadata.
