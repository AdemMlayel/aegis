# AegisQA Current Hardening Report

## Current verification

- Backend tests: `300 passed`
- Python compile check: `python -m compileall -q backend scripts tests` passes
- Frontend clean build: `npm ci && npm run build` succeeds
- External company providers: intentionally disabled in local/demo mode

## Hardening changes in this pass

1. Clean packaging exclusions were tightened: `.env`, `lld.docx`, generated artifacts, virtual environments, tool downloads, frontend dependencies, build output, and caches are excluded from clean packages.
2. Deterministic demo mode was made explicit through `AEGISQA_DETERMINISTIC_DEMO_MODE`.
3. Local document ingestion was added for RAG using `.md`, `.txt`, and `.rst` sources from `fixtures/knowledge`, `AEGISQA_KNOWLEDGE_DOCUMENTS_DIR`, or manual API ingestion.
4. LLM output handling now includes strict Pydantic parsing. Invalid model JSON is recorded and deterministic heuristics remain the safe fallback.
5. The frontend workspace was split with shared primitives and workflow utility modules.
6. Docker-isolated Robot execution was added as an optional adapter: `robot_docker`.
7. A storage adapter boundary was introduced with `sqlite` active and `postgres` present as a future disabled boundary.
8. Investigation now records evidence items across Robot results, artifacts, model traces, RAG references, and memory references.

## Intentional local/demo boundaries

The following remain local or mock because company systems and credentials are not available:

- Jira/Azure/GitLab real APIs
- Enterprise SSO/JWT identity provider
- Vault
- Company Git repositories and PR automation
- Company test environments
- Production PostgreSQL migrations
- Production vector database
- CI/CD/CT enterprise pipeline

## Current architecture

```text
React dashboard
  -> FastAPI gateway
    -> Services
      -> Workflow graph
        -> Agents
          -> Skills
            -> Tools
              -> Local providers / future external providers
```

## Remaining recommended work

1. Commit and tag this hardened state in the project repository.
2. Validate Docker Compose on a Docker-enabled machine.
3. Build or select the `aegisqa-robot-runner:local` image before using `robot_docker`.
4. Add production PostgreSQL migrations before enabling `AEGISQA_STORAGE_BACKEND=postgres`.
5. Add richer UI panels for document ingestion and investigation evidence review.
