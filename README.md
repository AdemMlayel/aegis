# AegisQA

AegisQA is a local/demo-ready AI-native QA orchestration proof aligned with the approved AegisQA blueprint. It demonstrates the full lifecycle from a structured ticket to requirements, coverage, test cases, Robot Framework automation, validation, approval, execution, investigation, report generation, and memory archival.

The project intentionally avoids real company APIs by default. Company integrations are represented through provider interfaces and local/demo adapters.

## Verified state

```bash
python -m pytest -q
# 300 passed

ruff check backend scripts
# All checks passed!

python scripts/verify_rag_corpus.py
# OK: corpus populated (43 chunks) and all 8 probes retrieved.

python scripts/check_lockfile_registry.py
# OK: frontend/package-lock.json resolved URLs all public

cd frontend
npm ci
npm run build
# tsc + vite build -> dist/ emitted
```

> Frontend build notes:
> - `frontend/package-lock.json` must resolve dependencies from the **public**
>   npm registry. A lockfile regenerated inside a private network rewrites every
>   `resolved` URL to an internal mirror, which makes a clean `npm ci` hang or
>   fail. `scripts/check_lockfile_registry.py` (run in CI) guards against this;
>   if it fails, regenerate with
>   `cd frontend && rm package-lock.json && npm install --registry=https://registry.npmjs.org/`.
> - `frontend/tsconfig.json` uses `moduleResolution: "Bundler"`. An earlier
>   `"Node"` (node10) value caused a hard `TS5107` error under newer TypeScript;
>   the bundler setting is the correct value for this Vite project.

## Architecture

```text
React dashboard
  -> FastAPI API routes
    -> Services
      -> Workflow graph
        -> Agents
          -> Skills
            -> Tools
              -> Local provider / future external provider
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev,worker]"
cp .env.example .env
```

Start backend:

```bash
uvicorn backend.main:app --reload
```

Start frontend:

```bash
cd frontend
npm ci
npm run dev
```

## Deterministic PM demo mode

Use this when Ollama is not installed or not ready:

```env
AEGISQA_DETERMINISTIC_DEMO_MODE=true
```

This explicitly selects safe local/demo providers:

```text
LLM: mock_llm
Embeddings: local_hash_embeddings
Execution: mock
Ticket source: demo
```

## Local Ollama mode

Use this for local model testing:

```bash
ollama pull qwen3:3b
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Recommended environment:

```env
AEGISQA_DETERMINISTIC_DEMO_MODE=false
AEGISQA_DEFAULT_LLM_PROVIDER=ollama
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=ollama_nomic_embed_text
```

Check model readiness:

```text
GET /api/v1/intelligence/ollama/health
GET /api/v1/intelligence/ollama/profiles
```

## OpenAI-compatible / vLLM mode (real external model)

Point AegisQA at any OpenAI-compatible server (e.g. a local vLLM serving an open model):

```env
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true
AEGISQA_DEFAULT_LLM_PROVIDER=openai_compatible
AEGISQA_OPENAI_COMPATIBLE_BASE_URL=http://<host>:8000/v1
AEGISQA_OPENAI_COMPATIBLE_API_KEY=<any-non-empty-value>
AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL=<model-id-from-/v1/models>
# Set this to the served model's context window (prompt + output). Required for
# small-context models: without it the agent's default 16000-token request can
# exceed the window, the server returns HTTP 400, and the call silently falls
# back to the mock provider.
AEGISQA_OPENAI_COMPATIBLE_CONTEXT_WINDOW=8192
# Large local models can be slow; raise the HTTP timeout so heavier stages
# (coverage, test generation, report) do not time out and fall back to mock.
AEGISQA_LLM_HTTP_TIMEOUT_SECONDS=180
```

Verify a stage actually used the real model (not a silent fallback) by checking
that `context.intelligence_trace.llm_calls[-1].fallback_from` is `None`.

Note: very large prompts (e.g. the final report stage, which includes all prior
artifacts) can still exceed a small context window even after output clamping —
use a larger-context model for full end-to-end real-model runs.

## RAG knowledge ingestion

The local RAG layer reads:

- built-in seeded knowledge chunks,
- the synthetic knowledge corpus under `fixtures/knowledge` (see
  `fixtures/knowledge/README.md`) — procedures, Robot/execution notes, governance rules,
  known failures, and demo usage, all sanitized,
- optional files from `AEGISQA_KNOWLEDGE_DOCUMENTS_DIR`,
- manual document ingestion through `POST /api/v1/intelligence/knowledge/ingest`.

Verify ingestion and retrieval (deterministic, no Ollama required):

```bash
python scripts/verify_rag_corpus.py
```

Manual ingestion example body:

```json
{
  "title": "Demo API QA Rules",
  "source": "local://demo/api-rules.md",
  "tags": ["api", "qa"],
  "text": "Validate authorization, schema compatibility, idempotency, and rollback behavior."
}
```


## Sanitized reference corpus grounding

The current Milestone 8A grounding flow treats `aegis-sensitive-data/` as a quarantined input folder. Raw files are never consumed directly by agents.

Safe flow:

```text
aegis-sensitive-data/
  -> scripts/intake_reference_corpus.py
  -> sanitize + safety scan
  -> fixtures/reference_corpus/raw_sanitized/
  -> fixtures/reference_corpus/normalized/
  -> agents/tools use normalized profiles only
```

Generated normalized profiles:

- `fixtures/reference_corpus/normalized/robot_keywords/keyword_registry.json`
- `fixtures/reference_corpus/normalized/robot_style_profile/profile.json`
- `fixtures/reference_corpus/normalized/report_profile/profile.json`
- `fixtures/reference_corpus/normalized/execution_evidence_profile/profile.json`
- `fixtures/reference_corpus/normalized/ticket_profile/profile.json`
- `fixtures/reference_corpus/INTAKE_SUMMARY.json`

Current corpus state:

```text
Sanitized files: 61
Redactions applied: 15073
Robot test/support files: 14
Custom library/reference files: 42
Report examples: 0 currently provided
Successful execution artifacts: 3
Failed execution artifacts: 0 currently provided
Ticket/semi-structured input files: 2
Extracted normalized Robot keywords: 238
```

Run the safe grounding pipeline manually:

```bash
python scripts/intake_reference_corpus.py --clean
python -m pytest -q
```

## Execution adapters

| Adapter | Purpose |
|---|---|
| `mock` | Deterministic demo/test execution |
| `robot` | Local Robot Framework CLI execution |
| `robot_docker` | Optional Docker-isolated Robot execution |

`robot_docker` requires Docker and the configured image:

```env
AEGISQA_DEFAULT_EXECUTION_ADAPTER=robot_docker
AEGISQA_ROBOT_DOCKER_IMAGE=aegisqa-robot-runner:local
```

If Docker is unavailable, the adapter fails clearly instead of silently pretending execution worked.

## Storage

```env
AEGISQA_STORAGE_BACKEND=sqlite
```

SQLite is the active local storage backend. A PostgreSQL adapter boundary exists for future work, but it is intentionally disabled until real migrations and runtime configuration are implemented.

## Demo script

1. Start backend and frontend.
2. Open the dashboard.
3. Select a demo ticket.
4. Start the workflow.
5. Show requirement analysis, coverage, test cases, automation, validation, and approval.
6. Approve the workflow.
7. Execute using `mock`, `robot`, or `robot_docker` depending on the environment.
8. Show execution result, investigation evidence, report, and memory archive.

## Clean package generation

Never share the raw working tree. Generate a clean source package:

```bash
python scripts/package_clean.py ../aegisqa-clean
```

The package excludes `.env`, `.git`, `.venv`, `.tools`, `node_modules`, build output, generated artifacts, caches, `lld.docx`, `data/`, and the quarantined `aegis-sensitive-data/` folder. It keeps only sanitized reference-corpus material and normalized profiles under `fixtures/reference_corpus/`.

## Current limitations

- Real Jira/Azure/GitLab APIs are not connected.
- Enterprise SSO/JWT is not connected.
- Vault is represented by a mock provider.
- PostgreSQL is a future adapter boundary only.
- Production vector DB is not connected.
- Docker Robot execution requires a local Docker image.
- Agent simulation/optimizer and A2A protocol are future milestones.


## Milestone 8B — Conversational QA Copilot

AegisQA now includes a governed chat layer over the workflow cockpit. The copilot can answer system, ticket, workflow, artifact, validation, execution, investigation, report, and safe-corpus questions. Controlled actions such as workflow start, running a stage, approving a pending stage, and execution are represented as confirmation-required chat actions.

It can also **explain the system itself**. The `system_knowledge` intent answers conceptual questions — architecture, the eight workflow stages, the agent roster, the governance model, the knowledge/RAG layer, providers, and demo mode — from a curated, code-accurate knowledge module (`backend/chat/system_knowledge.py`). Examples: "explain the architecture", "what agents are there", "what are the workflow stages", "how does governance work". These answers are informational only and never trigger an action. Intent routing is ordered so operational commands (start/status/approve/execute) are not shadowed.

Main endpoints:

```text
POST /api/v1/chat/sessions
GET  /api/v1/chat/sessions/{session_id}
POST /api/v1/chat/sessions/{session_id}/messages
POST /api/v1/chat/sessions/{session_id}/actions/{action_id}/confirm
```

The copilot does not replace the deterministic workflow engine. It routes safe user intent into existing workflow services and preserves the model-drafts/system-validates/human-confirms architecture.

### Optional LLM-backed free-form answers

By default the copilot is fully deterministic. Set `AEGISQA_CHAT_LLM_FALLBACK_ENABLED=true` (with a real LLM provider configured) to let questions the deterministic classifier maps to `unknown` be answered by the configured model, grounded with the system-knowledge overview and retrieved RAG chunks (answers include source citations). This path is informational only — it never proposes or triggers actions — degrades to the deterministic fallback on any error, and is forced off in deterministic demo mode. Known intents and confirmation-gated actions remain on the deterministic path.
