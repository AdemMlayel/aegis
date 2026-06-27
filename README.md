# AegisQA

AegisQA is a local/demo-ready AI-native QA orchestration proof aligned with the approved AegisQA blueprint. It demonstrates the full lifecycle from a structured ticket to requirements, coverage, test cases, Robot Framework automation, validation, approval, execution, investigation, report generation, and memory archival.

The project intentionally avoids real company APIs by default. Company integrations are represented through provider interfaces and local/demo adapters.

## Verified state

```bash
python -m pytest -q
# 140 passed

cd frontend
npm ci
npm run build
# build successful
```

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

## RAG knowledge ingestion

The local RAG layer reads:

- built-in seeded knowledge chunks,
- markdown/text files from `fixtures/knowledge`,
- optional files from `AEGISQA_KNOWLEDGE_DOCUMENTS_DIR`,
- manual document ingestion through `POST /api/v1/intelligence/knowledge/ingest`.

Manual ingestion example body:

```json
{
  "title": "Demo API QA Rules",
  "source": "local://demo/api-rules.md",
  "tags": ["api", "qa"],
  "text": "Validate authorization, schema compatibility, idempotency, and rollback behavior."
}
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

The package excludes `.env`, `.git`, `.venv`, `.tools`, `node_modules`, build output, generated artifacts, caches, and `lld.docx`.

## Current limitations

- Real Jira/Azure/GitLab APIs are not connected.
- Enterprise SSO/JWT is not connected.
- Vault is represented by a mock provider.
- PostgreSQL is a future adapter boundary only.
- Production vector DB is not connected.
- Docker Robot execution requires a local Docker image.
- Agent simulation/optimizer and A2A protocol are future milestones.
