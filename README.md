# AegisQA — Local AI-Native QA Orchestration Demo

AegisQA is a local/demo-ready architecture proof for the approved AegisQA v3 blueprint. It demonstrates an AI-native QA orchestration lifecycle from ticket intake to requirement analysis, coverage planning, test case generation, Robot Framework artifact generation, validation, human approval, execution, investigation, reporting, and memory archive.

This repository is intentionally safe for local testing: company systems are not contacted unless explicit providers and credentials are later added.

## Current status

Implemented and verified locally:

- FastAPI backend.
- React PM-facing dashboard.
- Agent -> Skill -> Tool architecture.
- Typed workflow context schema `0.11.0`.
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
- Backend tests and frontend build verified.

Verification result during hardening:

```bash
python -m pytest -q
# 88 passed

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
  src/                 PM-facing React dashboard
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

Workflow starts can override the local AI selection per run without changing
global environment defaults:

```json
{
  "created_by": "pm-demo",
  "ticket_id": "MOCK-101",
  "intelligence": {
    "llm_provider": "ollama",
    "embedding_provider": "ollama_nomic_embed_text",
    "llm_model": "qwen3:3b",
    "embedding_model": "qwen3-embedding:0.6b"
  }
}
```

The selected providers and model overrides are persisted on
`TestContext.intelligence_config` and mirrored into
`TestContext.intelligence_trace`.

When the workflow LLM provider is `ollama` and no explicit `llm_model` override
is provided, prompt stages route automatically to local model roles:
requirements/reporting use `main_rag`, coverage uses `reasoning`, and test case
generation uses `stable_baseline`. A manual `llm_model` override still takes
precedence for the full run.

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

The frontend exposes this flow in readable PM-facing sections:

- Demo Ticket
- Local AI Providers
- Workflow Progress
- Requirement Analysis
- Coverage Plan
- Generated Test Cases
- Automation Output
- Execution Result
- Report & Memory
- Investigation & Events

## API highlights

```text
GET  /health
GET  /api/v1/security/me
GET  /api/v1/integrations/providers
GET  /api/v1/intelligence/llm-providers
GET  /api/v1/intelligence/embedding-providers
GET  /api/v1/intelligence/ollama/health
GET  /api/v1/tickets/mock
POST /api/v1/workflows/start-from-mock-ticket
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
- Docker-isolated execution against real test environments.

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
