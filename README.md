# AegisQA - Local AI-Native QA Orchestration Demo

AegisQA is a local/demo-ready architecture proof for the approved AegisQA v3 blueprint. It demonstrates an AI-native QA orchestration lifecycle from ticket intake to requirement analysis, coverage planning, test case generation, Robot Framework artifact generation, validation, human approval, execution, investigation, reporting, and memory archive.

This repository is intentionally safe for local testing: company systems are not contacted unless explicit providers and credentials are later added.

## Current status

Implemented and verified locally:

- FastAPI backend.
- React three-panel agent operations workspace.
- Agent -> Skill -> Tool architecture.
- Typed workflow context schema `0.15.0`.
- Full local workflow graph with validation retry, approval, execution, investigation, memory archive, and reporting.
- Local/mock Jira-style ticket provider.
- Toolized Git handoff boundary.
- Local artifact store.
- Mock Vault-style secret reference provider.
- Deterministic mock LLM provider.
- Optional Ollama local LLM provider.
- Deterministic local hash embedding provider.
- Optional Ollama embedding provider with Qwen/Nomic local model profiles.
- Local seeded knowledge store for RAG.
- Local seeded episodic memory store.
- Mock and local Robot execution adapters.
- API endpoints for providers, intelligence, workflows, tickets, execution, security, and artifacts.
- Clean package script.
- Controlled workflow sessions with autonomous, approval-required, and step-by-step modes.
- Pollable workflow timeline, stage review/regeneration, artifact revision history, and execution logs.
- Deterministic validation summary with traceability, quality scoring, risk areas, and retry evidence.
- Final technical/executive reports with a hashed ZIP evidence package and export manifest.
- Registered agent identities with centralized skill, tool, and model-provider policies.
- Durable request, agent, and model telemetry with token, latency, fallback, and cost fields.
- Atomic token reservations with organization, workflow, call, and concurrency-safe quota enforcement.
- Structured JSON logs, liveness/readiness probes, operational health, and Prometheus-compatible metrics.
- Gateway request limits, daily quotas, request timeouts, model-token budgets, and provider circuit breakers.
- Backend tests and frontend production build verified.

Verification result during hardening:

```bash
python -m pytest -q
# 121 passed

cd frontend
npm install
npm audit
npm run build
# 0 vulnerabilities, build successful
```

## Architecture

```text
Frontend Dashboard
  -> FastAPI API routes/controllers
      -> Workflow services and graph
          -> Agents
              -> Skills
                  -> Tools
                      -> Local/demo providers now
                      -> Real company providers later
```

The intended AegisQA boundary is preserved:

```text
Agent -> Skill -> Tool -> External System or Local Provider
```

Agents do not directly call company systems. Tools are isolated, typed, auditable boundaries.

## Repository layout

```text
backend/
  api/routes/          FastAPI controllers
  config/              Central settings
  agents/              Workflow agent wrappers
  skills/              Skill orchestration layer
  tools/               Typed tool implementations
  tickets/             Ticket connector interfaces and local Jira mock
  llm/                 LLM provider abstraction: mock, Ollama, OpenAI-compatible
  embeddings/          Embedding provider abstraction: local hash, Ollama nomic
  knowledge/           Local RAG knowledge store
  memory/              Local episodic memory store
  artifacts/           Artifact-store abstraction
  secrets/             Mock Vault-compatible secret references
  execution/           Mock and Robot execution adapters
  graph/               Workflow state, graph, and nodes
  storage/             Local persistence repositories
frontend/
  src/                 React agent operations workspace
tests/                 Backend unit/API/workflow tests
docs/                  Architecture/supporting docs
scripts/               Clean packaging script
```

## Local setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
uvicorn backend.main:app --reload
```

Backend health check:

```text
GET http://127.0.0.1:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local Vite URL, usually:

```text
http://127.0.0.1:5173
```

### Tests

```bash
python -m pytest -q
```

### Frontend quality gate

```bash
cd frontend
npm install
npm audit
npm run build
```

## Environment variables

Copy `.env.example` and adjust only if needed.

```bash
cp .env.example .env
```

Important defaults:

```bash
AEGISQA_DEFAULT_TICKET_CONNECTOR=jira_mock
AEGISQA_DEFAULT_EXECUTION_ADAPTER=mock
AEGISQA_DEFAULT_LLM_PROVIDER=mock_llm
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=local_hash_embeddings
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=false
```

The default mode is fully local and requires no company API credentials.

## Local model configuration

Default AI mode is deterministic:

```bash
AEGISQA_DEFAULT_LLM_PROVIDER=mock_llm
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=local_hash_embeddings
```

Optional Ollama mode:

```bash
ollama pull qwen3:3b
ollama pull llama3.1:8b
ollama pull qwen3-coder
ollama pull phi4-mini
ollama pull gemma3:4b
ollama pull deepseek-r1:8b
ollama pull deepseek-r1:7b
ollama pull qwen3-embedding:0.6b
ollama pull nomic-embed-text
```

Then configure:

```bash
AEGISQA_DEFAULT_LLM_PROVIDER=ollama
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=ollama_nomic_embed_text
AEGISQA_OLLAMA_BASE_URL=http://127.0.0.1:11434
AEGISQA_OLLAMA_CHAT_MODEL=qwen3:3b
AEGISQA_OLLAMA_RAG_MODEL=qwen3:3b
AEGISQA_OLLAMA_BASELINE_MODEL=llama3.1:8b
AEGISQA_OLLAMA_CODING_MODEL=qwen3-coder
AEGISQA_OLLAMA_FAST_MODEL=phi4-mini
AEGISQA_OLLAMA_FAST_FALLBACK_MODEL=gemma3:4b
AEGISQA_OLLAMA_REASONING_MODEL=deepseek-r1:8b
AEGISQA_OLLAMA_REASONING_FALLBACK_MODEL=deepseek-r1:7b
AEGISQA_OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b
AEGISQA_OLLAMA_EMBEDDING_FALLBACK_MODEL=nomic-embed-text
```

Ollama health endpoint:

```text
GET /api/v1/intelligence/ollama/health
GET /api/v1/intelligence/ollama/profiles
POST /api/v1/intelligence/ollama/profiles/smoke-test
```

If Ollama is not running or the selected model is missing, the API returns a clear status message. Workflow generation and RAG/memory retrieval use deterministic fallbacks so PM demos do not fail silently.

Workflow starts can override AI routing per run without changing global
environment defaults. Each LLM-backed agent can use a different provider and
model:

```json
{
  "created_by": "pm-demo",
  "ticket_id": "MOCK-101",
  "intelligence": {
    "llm_provider": "ollama",
    "embedding_provider": "ollama_nomic_embed_text",
    "embedding_model": "nomic-embed-text",
    "agent_routes": {
      "RequirementAgent": {
        "provider": "openai_compatible",
        "model": "your-requirement-model"
      },
      "CoveragePlannerAgent": {
        "provider": "openai_compatible",
        "model": "your-reasoning-model"
      },
      "TestCaseGeneratorAgent": {
        "provider": "openai_compatible",
        "model": "your-generation-model"
      },
      "ReportGeneratorAgent": {
        "provider": "ollama",
        "model": "qwen3:3b"
      }
    }
  }
}
```

The selected providers, embedding model, and agent routes are persisted on
`TestContext.intelligence_config` and mirrored into
`TestContext.intelligence_trace`.

The streamlined dashboard provides two presets:

- `External live`: the configured OpenAI-compatible model for every LLM-backed
  agent, with local embeddings.
- `Private local`: Ollama role routing. When Ollama embeddings are unavailable,
  the dashboard keeps deterministic local embeddings so workflow startup remains
  reliable.

The deterministic mock provider remains registered for automated tests and
provider-failure fallback, but it is no longer shown as a primary dashboard
configuration.

Agent selections always override the workflow-level LLM fallback. For Ollama,
an empty agent model uses the built-in role mapping: requirements/reporting use
`main_rag`, coverage uses `reasoning`, and test generation uses
`stable_baseline`.

External credentials are server-side only. Enable and configure an
OpenAI-compatible endpoint before it becomes selectable:

```bash
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true
AEGISQA_OPENAI_COMPATIBLE_BASE_URL=https://your-provider.example/v1
AEGISQA_OPENAI_COMPATIBLE_API_KEY=server-side-secret
AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL=your-default-model
```

The API returns provider readiness and required environment-variable names but
never returns credential values.

## Clean real-LLM demo state

The source fixture set contains two representative tickets. Reset accumulated
local workflow history before a team demo with:

```bash
python scripts/reset_demo_state.py
```

The command backs up `generated/storage/aegisqa.sqlite3`, creates a fresh
runtime database, and reseeds the two tickets. Pytest uses a separate
`generated/storage/aegisqa-test.sqlite3`, so regression runs no longer populate
the live dashboard.

For a live external workflow, configure:

```bash
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true
AEGISQA_DEFAULT_LLM_PROVIDER=openai_compatible
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=local_hash_embeddings
AEGISQA_OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
AEGISQA_OPENAI_COMPATIBLE_API_KEY=your-server-side-key
AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL=gpt-4o-mini
```

Current model responses enrich requirement analysis, coverage rationale, test
generation notes, and the final report. The typed test-case structure and Robot
generation remain deterministic pending the structured-output upgrade.

## Controlled workflow sessions

The original workflow start APIs remain backward compatible and complete the
current demo pipeline synchronously. A separate controlled-session API supports
the future agent workspace:

- `autonomous`: continue through all stages.
- `approval_required`: pause after each reviewable deliverable.
- `step_by_step`: execute one logical stage per request.

Logical stages are:

```text
ticket -> requirements -> coverage -> tests -> automation
       -> validation -> approval -> report
```

Core controls:

```http
POST /api/v1/workflows/sessions
POST /api/v1/workflows/{context_id}/resume
POST /api/v1/workflows/{context_id}/next
POST /api/v1/workflows/{context_id}/pause
POST /api/v1/workflows/{context_id}/stages/{stage}/review
POST /api/v1/workflows/{context_id}/stages/{stage}/regenerate
```

Pause requests are honored at stage boundaries. Individual synchronous Python
functions are not interrupted mid-call.

Operational events and operator messages share a durable cursor-based timeline:

```http
GET  /api/v1/workflows/{context_id}/timeline?after_sequence=0
POST /api/v1/workflows/{context_id}/timeline/messages
```

Generated Robot artifacts support immutable revision history. Manual edits
invalidate downstream validation and approval state:

```http
PUT /api/v1/workflows/{context_id}/artifacts/{test_case_id}
GET /api/v1/workflows/{context_id}/artifacts/{test_case_id}/revisions
```

## Main demo workflow

1. Load a local ticket from the `jira_mock` provider.
2. Run requirement analysis with local RAG and memory evidence.
3. Generate coverage plan and risk rationale.
4. Generate test cases.
5. Generate Robot Framework automation artifacts.
6. Validate artifacts.
7. Present human approval state.
8. Approve workflow.
9. Execute locally through mock or Robot adapter.
10. Generate investigation/report output.
11. Archive a local memory entry.

The frontend exposes this flow as one operational workspace:

- Left workspace queue with ticket search and run-state filters.
- Central activity timeline with eight workflow stages and approval controls.
- Dedicated test, automation artifact, and evidence views.
- Validation and final-report workspaces with approval and export controls.
- Editable Robot artifact with revision history and downstream invalidation.
- Right-side execution mode, provider routing, embedding, knowledge, and health controls.

## API highlights

```text
GET  /health
GET  /health/live
GET  /health/ready
GET  /metrics
GET  /api/v1/security/me
GET  /api/v1/integrations/providers
GET  /api/v1/intelligence/llm-providers
GET  /api/v1/intelligence/embedding-providers
GET  /api/v1/intelligence/agent-model-profiles
GET  /api/v1/intelligence/ollama/health
GET  /api/v1/governance/agents
GET  /api/v1/observability/summary
GET  /api/v1/observability/agent-invocations
GET  /api/v1/observability/model-invocations
GET  /api/v1/observability/token-usage
GET  /api/v1/observability/token-budget
GET  /api/v1/observability/health
GET  /api/v1/tickets/mock
POST /api/v1/workflows/start-from-mock-ticket
POST /api/v1/workflows/sessions
POST /api/v1/workflows/{context_id}/resume
POST /api/v1/workflows/{context_id}/next
GET  /api/v1/workflows/{context_id}/timeline
GET  /api/v1/workflows/{context_id}/package/manifest
GET  /api/v1/workflows/{context_id}/package/technical.md
GET  /api/v1/workflows/{context_id}/package/executive.md
GET  /api/v1/workflows/{context_id}/package.zip
POST /api/v1/workflows/{context_id}/approval
POST /api/v1/workflows/{context_id}/execute
POST /api/v1/execute
GET  /api/v1/results/{run_id}
```

## What is real today

- Backend API and workflow orchestration.
- Frontend dashboard.
- Agent/Skill/Tool separation.
- Local provider catalog.
- Local ticket fixture provider.
- Local RAG and memory stores.
- Local model provider abstraction.
- Optional Ollama model integration.
- Generated Robot files.
- Validation gate.
- Approval gate.
- Agent identity and policy enforcement.
- Request/agent/model observability and token accounting.
- Gateway limits and provider circuit breakers.
- Local/mock execution and report generation.
- Tests and clean packaging.

## What remains local/demo-only

- Jira/Azure/GitLab integrations.
- Vault integration.
- Enterprise identity provider.
- Real Git PR creation against company repositories.
- Company internal documentation ingestion.
- Production vector database.
- Production PostgreSQL persistence.
- Multi-instance distributed rate limits and circuit state.
- OpenTelemetry export, managed metrics storage, dashboards, and alerting integration.
- Docker-isolated execution against real test environments.

## Governance settings

The local defaults are intentionally generous for demos. Production deployments
should set organization-specific values:

```text
AEGISQA_GATEWAY_REQUESTS_PER_MINUTE=240
AEGISQA_GATEWAY_DAILY_REQUEST_QUOTA=10000
AEGISQA_GATEWAY_REQUEST_TIMEOUT_SECONDS=60
AEGISQA_PROVIDER_CIRCUIT_FAILURE_THRESHOLD=3
AEGISQA_PROVIDER_CIRCUIT_RESET_SECONDS=30
AEGISQA_AGENT_MAX_MODEL_CALLS_PER_WORKFLOW=24
AEGISQA_AGENT_MAX_TOKENS_PER_CALL=16000
AEGISQA_AGENT_MAX_TOKENS_PER_WORKFLOW=120000
AEGISQA_ORGANIZATION_DAILY_TOKEN_QUOTA=1000000
AEGISQA_TOKEN_RESERVATION_TTL_SECONDS=300
AEGISQA_EXTERNAL_INPUT_COST_PER_1K=0.00015
AEGISQA_EXTERNAL_OUTPUT_COST_PER_1K=0.0006
AEGISQA_OBSERVABILITY_ERROR_RATE_THRESHOLD=0.05
AEGISQA_OBSERVABILITY_AGENT_FAILURE_RATE_THRESHOLD=0.10
```

## Clean packaging

Do not share raw working tree archives. They may include runtime/dependency folders.

Use:

```bash
python scripts/package_clean.py /path/to/aegisqa-clean
```

Excluded from clean packages:

- `.git/`
- `.venv/`
- `.tools/`
- `frontend/node_modules/`
- `frontend/dist/`
- `generated/`
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `aegisqa.egg-info/`

## PM demo script

See:

```text
DEMO_SCRIPT_PM.md
```

## Hardening report

See:

```text
ARCHITECTURE_HARDENING_REPORT.md
```

## Recommended next milestones

1. Add storage adapter layer with SQLite now and PostgreSQL later.
2. Add local document ingestion pipeline for RAG.
3. Add strict structured LLM output parsing with Pydantic validation.
4. Add Docker-isolated Robot execution adapter.
5. Add request ID, structured JSON logs, and rate limiting.
6. Add enterprise identity and real ticket/document providers only after company details are available.
