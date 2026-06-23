# AegisQA Architecture Hardening Report

## Scope

This pass cleaned and hardened the local/demo AegisQA repository so it can be tested locally and presented to a PM without relying on company APIs or credentials.

The work intentionally keeps external systems disabled. Jira, Git, Vault, execution infrastructure, LLMs, embeddings, RAG, and memory are exposed through provider boundaries with local/demo implementations.

## Audit findings before cleanup

| Finding | Classification | Action |
|---|---|---|
| Raw archives included `.venv`, `.tools`, `frontend/node_modules`, `frontend/dist`, `generated`, `.pytest_cache`, `__pycache__`, and egg-info | Redundant runtime/generated material | Kept clean package script and verified clean packaging excludes these files |
| Frontend source was a single large dashboard component | Maintainability gap | Rebuilt the UI into clearer PM-facing sections while keeping a simple source footprint |
| Model provider abstraction existed only for deterministic mock behavior | Local model integration gap | Added Ollama chat and embedding provider boundaries with clear health messages and deterministic fallback behavior |
| Embeddings/RAG did not expose provider selection | Architecture gap | Added embedding provider registry and provider catalog integration |
| Dependency versions were loose | Reproducibility gap | Stabilized Python version ranges and pinned frontend package versions through package-lock |
| Tests passed for the existing architecture but did not verify local model endpoints | Missing tests | Added local model/provider tests |
| External provider behavior could fail the demo if selected but unavailable | Demo-readiness issue | Added graceful LLM fallback helper and Ollama health endpoint |

## Cleaned architecture overview

```text
Frontend Dashboard
  -> FastAPI routes/controllers
      -> Services / workflow graph
          -> Agents
              -> Skills
                  -> Tools
                      -> Local/demo providers or future external systems
```

Current local providers:

| Provider area | Local/demo provider | Purpose |
|---|---|---|
| Ticket connector | `jira_mock` | Realistic local ticket fixture adapter |
| LLM | `mock_llm`, optional `ollama` | Deterministic AI traces by default, local model support when available |
| Embeddings | `local_hash_embeddings`, optional `ollama_nomic_embed_text` | Reproducible retrieval by default, local `nomic-embed-text` support when available |
| Knowledge | `local_knowledge` | Seeded RAG knowledge chunks |
| Memory | `local_episodic_memory` | Seeded previous-failure memory and archive placeholder |
| Secrets | `mock_vault` | Secret-reference architecture without real secrets |
| Execution | `mock`, `robot` | Deterministic execution and optional local Robot runner |
| Artifacts | `local_fs` | Local artifact persistence |
| Git handoff | `LocalGitHandoffTool` | Toolized local Git handoff boundary |

## Removed or merged duplicated components

This pass does not blindly delete business features. It removes runtime/package artifacts only during clean packaging:

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

No useful source modules were deleted. Existing Agent -> Skill -> Tool boundaries were preserved.

## Intentional mocks that remain

| Mock/local element | Why it remains |
|---|---|
| `jira_mock` ticket connector | Company Jira/Azure/GitLab credentials and URLs are not available |
| `mock_vault` | Real Vault/secrets provider is not available and should not be faked with hardcoded secrets |
| `mock` execution adapter | Allows deterministic local demo even when Robot or target environments are unavailable |
| `mock_llm` | Keeps tests stable and demos available without cloud/local model dependencies |
| `local_hash_embeddings` | Keeps RAG/memory retrieval reproducible without Ollama |
| `local_knowledge` and `local_episodic_memory` | Company docs and historical execution data are not available yet |

## Local model configuration

Supported providers:

- `mock_llm`: default deterministic provider.
- `ollama`: local Ollama chat provider.
- `openai_compatible`: optional future cloud/internal gateway provider, disabled in local mode.
- `local_hash_embeddings`: default deterministic embedding provider.
- `ollama_nomic_embed_text`: local Ollama embedding provider.

Recommended local models:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Relevant environment variables:

```bash
AEGISQA_DEFAULT_LLM_PROVIDER=mock_llm
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=local_hash_embeddings
AEGISQA_OLLAMA_BASE_URL=http://127.0.0.1:11434
AEGISQA_OLLAMA_CHAT_MODEL=llama3.1:8b
AEGISQA_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

To use Ollama:

```bash
AEGISQA_DEFAULT_LLM_PROVIDER=ollama
AEGISQA_DEFAULT_EMBEDDING_PROVIDER=ollama_nomic_embed_text
```

If Ollama is not running or models are missing, the API reports this through:

```text
GET /api/v1/intelligence/ollama/health
```

The workflow uses a safe mock fallback for PM demos rather than silently crashing.

## Verification results

```bash
python -m pytest -q
# 79 passed

cd frontend
npm install
npm audit
npm run build
# build successful; 0 npm vulnerabilities
```

## Known limitations

- Real Jira, Azure DevOps, GitLab, Vault, company docs, and company execution environments are not connected.
- PostgreSQL/pgvector are not yet active production storage layers; local persistence remains simple and demo-oriented.
- Robot execution is available through a local adapter, but the deterministic mock adapter remains the safest PM demo default.
- The RAG pipeline uses seeded local chunks. There is no document upload/chunking UI yet.
- Real LLM output should later be constrained through strict JSON/Pydantic output parsing before production use.
- RBAC is local-demo mode and not integrated with enterprise identity.

## Recommended next milestones

1. Add a storage adapter layer with SQLite now and PostgreSQL later.
2. Add local document ingestion for RAG.
3. Add strict structured LLM output parsing and validation.
4. Add Docker-isolated Robot execution.
5. Add request ID, structured logs, and rate limiting middleware.
6. Add enterprise identity integration only when company provider details are available.
