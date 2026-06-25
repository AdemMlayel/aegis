# AegisQA

AegisQA is a demo-ready QA orchestration workspace that turns a ticket into
reviewable requirements, coverage, test cases, Robot Framework automation,
validation evidence, approval, execution results, reports, and reusable workflow
memory.

The application supports real OpenAI-compatible models and local Ollama models.
Deterministic model and execution adapters remain available only as explicit
test/failure fallbacks. The two centralized ticket fixtures are the only seeded
demo records.

## What Works

- Three-panel React operations dashboard with ticket queue, workflow timeline,
  review controls, artifacts, evidence, logs, reports, and model routing.
- FastAPI API with typed workflow sessions and autonomous, review, or step modes.
- `Agent -> Skill -> Tool` boundaries with registered identities and policies.
- Per-agent external/local model selection and local embedding selection.
- OpenAI-compatible and Ollama LLM providers.
- Ollama and deterministic fallback embedding providers.
- Robot Framework generation, validation, local execution, and artifact capture.
- SQLite persistence for tickets, contexts, audit events, workflow events,
  execution queue/history, revisions, telemetry, and token governance.
- Local and Celery/Redis execution workers.
- Request, agent, model, token, latency, cost, health, and metrics telemetry.
- Human approval, regeneration, artifact editing, report packaging, and Git
  handoff boundaries.
- Episodic memory rebuilt from completed workflow archives rather than fake
  seeded failures.

## Architecture

```text
React dashboard
  -> FastAPI routes
      -> workflow/execution/intelligence services
          -> workflow graph
              -> agents
                  -> skills
                      -> tools
                          -> local or external providers
```

Key directories:

```text
backend/api/routes/     HTTP controllers
backend/services/       Application orchestration
backend/graph/          Workflow state, graph, and nodes
backend/agents/         Agent contracts and implementations
backend/skills/         Skill contracts and implementations
backend/tools/          Audited tool boundaries
backend/storage/        SQLite repositories and migrations
backend/llm/            Mock, Ollama, and OpenAI-compatible providers
backend/embeddings/     Local and Ollama embedding providers
backend/workers/        Local/Celery execution dispatch
frontend/src/           React operations workspace
tests/                  Backend unit, boundary, API, and workflow tests
scripts/                Demo reset and clean packaging utilities
```

See [docs/architecture.md](docs/architecture.md) for boundary details and
[AegisQA_v3_Full_Blueprint.md](AegisQA_v3_Full_Blueprint.md) for the approved
target architecture.

## Setup

Python 3.11+ and Node.js 20+ are required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,worker]"
Copy-Item .env.example .env

cd frontend
npm ci
cd ..
```

Keep credentials only in `.env`, which is ignored by Git. Never put a provider
key in frontend environment variables.

## Model Configuration

For an external OpenAI-compatible provider:

```text
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true
AEGISQA_OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
AEGISQA_OPENAI_COMPATIBLE_API_KEY=your-server-side-key
AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL=gpt-4o-mini
```

For private local inference:

```powershell
ollama pull qwen3:3b
ollama pull llama3.1:8b
ollama pull qwen3-coder
ollama pull phi4-mini
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
```

```text
AEGISQA_DEFAULT_LLM_PROVIDER=ollama
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=ollama_nomic_embed_text
AEGISQA_OLLAMA_CHAT_MODEL=qwen3:3b
AEGISQA_OLLAMA_BASELINE_MODEL=llama3.1:8b
AEGISQA_OLLAMA_CODING_MODEL=qwen3-coder
AEGISQA_OLLAMA_FAST_MODEL=phi4-mini
AEGISQA_OLLAMA_REASONING_MODEL=deepseek-r1:8b
AEGISQA_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

The dashboard recommends external models for requirements, coverage, and test
generation, while local inference is suitable for grounded reporting and local
embeddings. A workflow cannot be started from the dashboard until a real LLM
provider is ready.

## Run

Backend:

```powershell
python -m uvicorn backend.main:app --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. API health is available at
`http://127.0.0.1:8000/health/ready`.

Optional local queue worker:

```powershell
python -m backend.worker
```

Complete container stack:

```powershell
docker compose up --build
```

## Demo Flow

1. Select one of the two ticket fixtures in the left queue.
2. Choose external or local models per agent in the right panel.
3. Start the workflow in review or step mode.
4. Review requirements, coverage, tests, generated Robot files, and validation.
5. Request changes or approve at checkpoints.
6. Execute approved automation with the Robot adapter.
7. Inspect live execution logs, reports, evidence, and archived memory.

Reset accumulated runtime output before a clean demo:

```powershell
python scripts/reset_demo_state.py
```

This deletes generated workflows, logs, artifacts, memory, and history, then
creates a fresh SQLite database containing only the two ticket fixtures. Add
`--keep-backup` only when an old local database is intentionally needed.

## Quality Gates

```powershell
python -m ruff check backend scripts tests
python -m pytest -q
python -m compileall -q backend scripts tests

cd frontend
npx tsc --noEmit --noUnusedLocals --noUnusedParameters
npm audit
npm run build
```

Create a source-only package outside the repository:

```powershell
python scripts/package_clean.py ..\aegisqa-clean
```

## Current Limits

- Ticket data is local; Jira/Azure DevOps/GitLab connectors are not implemented.
- Authentication is a local RBAC scaffold, not enterprise SSO.
- SQLite and in-process governance state are intended for one application
  instance; production needs shared PostgreSQL/Redis state.
- Vector retrieval is in memory; there is no production vector database.
- Robot execution runs on the local host unless separately container-isolated.
- OpenTelemetry export, managed dashboards, and alert delivery are not wired.
- LLM output enriches deterministic typed workflow artifacts; strict structured
  model-output parsing is the next major quality upgrade.

The detailed cleanup evidence and remaining risks are recorded in
[CODEBASE_HARDENING_REPORT.md](CODEBASE_HARDENING_REPORT.md).
