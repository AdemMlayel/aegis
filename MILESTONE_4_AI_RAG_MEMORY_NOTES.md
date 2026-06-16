# Milestone 4 — Local AI/RAG/Memory Intelligence Layer

## Goal

Deliver the blueprint's AI-native value path without depending on company data providers or external APIs.

The implementation remains local/mock-first and architecture-focused. It proves that the orchestration can consume LLM output, retrieved knowledge, and episodic memory while keeping provider boundaries swappable.

## Implemented

### LLM provider abstraction

- Added `backend/llm/base.py`.
- Added deterministic `mock_llm` provider in `backend/llm/mock.py`.
- Registered provider through `llm_provider_registry`.
- Added provider catalog visibility.

### Prompt template/versioning

- Added `backend/prompts/base.py`.
- Added versioned templates in `backend/prompts/templates.py`:
  - `requirement_analysis_v1@1.0.0`
  - `coverage_planning_v1@1.0.0`
  - `test_case_generation_v1@1.0.0`
  - `report_generation_v1@1.0.0`

### Knowledge search / RAG

- Added `backend/knowledge/base.py`.
- Added local seeded knowledge chunks in `backend/knowledge/local.py`.
- Search is deterministic keyword/tag retrieval for reproducible tests.
- No external document store is required.

### Episodic memory store

- Added `backend/memory/base.py`.
- Added local seeded memory in `backend/memory/local.py`.
- Memory search supports previous-failure/regression retrieval.
- The memory archiver now indexes workflow snapshots into the local memory store.

### TestContext extension

- Added intelligence trace fields:
  - LLM provider
  - knowledge references
  - memory references
  - prompt versions
  - LLM call summaries
- Added evidence fields to requirement analysis, coverage plan, test cases, report block, and memory archive.

### Agent upgrades

- RequirementAgent now records local RAG/memory evidence and mock LLM summary.
- CoveragePlanner now records RAG/memory rationale and can produce local regression hints.
- TestCaseGenerator now attaches evidence refs and can add regression test cases when coverage requires them.
- ReportGenerator now includes knowledge refs, memory refs, prompt versions, and confidence.

### APIs

Added local intelligence endpoints:

```text
GET /api/v1/intelligence/prompts
GET /api/v1/intelligence/llm-providers
GET /api/v1/intelligence/knowledge/search
GET /api/v1/intelligence/memory/search
```

## Explicitly not implemented yet

The following are intentionally deferred because the project currently lacks company providers:

- Real company Jira/Azure/Confluence retrieval.
- Real internal LLM gateway.
- Real vector database such as pgvector or Qdrant.
- Production-grade memory retention and access-control policies.
- Real prompt-evaluation pipeline.

## Verification

```bash
python -m pytest -q
# 78 passed
```

Frontend build was also verified with:

```bash
cd frontend
npm ci
npm run build
```

## Architectural value

Milestone 4 proves that the blueprint's AI-native flow is now concrete:

```text
Ticket -> RequirementAgent -> RAG + Memory -> CoveragePlanner -> TestCaseGenerator -> Automation -> Validation -> Approval -> Execution -> Investigation -> ArchiveMemory -> Report
```

All intelligence components are swappable and remain safe for local architecture demonstrations.
