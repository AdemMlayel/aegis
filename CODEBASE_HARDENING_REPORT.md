# AegisQA Codebase Hardening Report

Date: June 25, 2026

## A. What Was Found

### Extra and obsolete files

- Generated runtime output had grown to about 41.5 MB and 3,267 files.
- The live SQLite database contained 168 workflows, mostly imported from old
  test JSON contexts.
- `generated/storage` contained nine migration-test databases and a 33 MB reset
  backup.
- Runtime folders contained 1,166 memory files, 1,574 Robot files, 166 context
  files, logs, and Git handoff payloads from earlier tests.
- `ARCHITECTURE_HARDENING_REPORT.md` and `DEMO_SCRIPT_PM.md` described an older
  mock-first milestone and obsolete test counts.
- `requirements-dev.txt` duplicated the dependencies owned by `pyproject.toml`.
- Build output, Python caches, test caches, Ruff caches, and package metadata
  were present locally.

### Duplicate or inconsistent logic

- `backend/storage/database.py` duplicated the complete schema already owned by
  the migration module.
- Test output and live output shared the same generated root, allowing tests to
  repopulate the dashboard.
- Generated-root configuration was only partially honored by artifact and
  report-package code.
- The provider profile described all non-external operation as `mock_only`,
  even when real local providers were selected.

### Unused code

- Ruff found 36 unused-import findings. Most were intentional registry imports
  that were not declared as side effects; the remainder were genuinely unused.
- TypeScript strict unused checks found unused React/icon imports.
- The frontend API exposed unused workflow/execution helpers and a dead response
  type.

### Hardcoded values

- Frontend API root, Vite host/port/proxy, and operator identity were embedded in
  source.
- Workflow execution defaulted to the mock adapter in several models and routes.
- The workflow route recorded mock-specific execution language.
- Worker settings referenced by code were missing from central configuration.
- Docker Compose declared PostgreSQL even though the application had no
  PostgreSQL storage adapter.

### Mock and unrealistic behavior

- Runtime episodic memory was preloaded with invented regression failures.
- Mock execution was the default, despite Robot Framework being available.
- The dashboard could silently select the hidden mock LLM when no real provider
  was ready.
- Old test workflows made the live queue and memory appear populated.

### Errors and risks

- The Celery Docker install target referenced a nonexistent `worker` extra.
- Celery worker configuration fields were missing.
- Vite environment types were missing after environment-based configuration was
  introduced.
- Two tests depended on hardcoded generated paths and fake memory IDs.
- The clean-package script copied the root `.env` file, creating a credential
  disclosure risk.
- The OpenAI credential previously shared in chat must be treated as compromised.

## B. What Was Changed

### Frontend

- Added typed runtime configuration for API root and operator identity.
- Made Vite host, port, and proxy target environment-configurable.
- Removed unused API functions, response types, imports, and variables.
- Stopped automatic hidden-mock selection; a real external or Ollama provider
  must be ready before the dashboard starts a workflow.
- Preserved per-agent external/local routing and local embedding selection.
- Kept ticket-to-workflow payload normalization at the API boundary.
- Updated the frontend runbook and verified the production build.

### Backend

- Consolidated schema ownership in `backend/storage/migrations.py`.
- Added SQLite foreign keys, busy timeout, and WAL configuration.
- Added missing local/Celery worker settings and a real `worker` dependency extra.
- Changed default execution behavior to Robot Framework.
- Made execution audit messages adapter-neutral.
- Rebuilt episodic memory from completed workflow archives and removed all
  synthetic runtime memory fixtures.
- Made regression planning use memory content and tags instead of magic IDs.
- Applied configured generated roots consistently to artifacts and report
  packages.
- Clarified registry side-effect imports and removed genuinely unused imports.
- Updated local/external provider language and `local_only` integration policy.

### Configuration

- Removed the unused PostgreSQL service from Compose.
- Added a Redis-backed Celery worker and corrected API/worker environment fields.
- Added Ruff and Celery/Redis extras to `pyproject.toml`.
- Removed the duplicate requirements file.
- Added generated-root, worker, broker, and frontend Vite environment examples.
- Changed source defaults toward real Ollama inference; tests explicitly select
  deterministic providers.

### Data

- Replaced the reset script with a full generated-runtime reset.
- Removed old contexts, memory, Robot files, logs, migration databases, backups,
  execution output, and handoff payloads.
- Left a fresh 256 KB SQLite database with exactly two ticket fixtures and zero
  workflow contexts.
- Isolated all pytest output under `generated/test-runtime`.
- Kept ticket data centralized in `backend/mock_data/tickets.json`.

### Tests

- Made tests independent of the production generated path.
- Replaced fake seeded-memory assumptions with explicit test-only memory setup.
- Added deterministic cleanup of the test runtime at session start.
- Updated integration-policy expectations from `mock_only` to `local_only`.
- Final result: 121 passed.

### Documentation

- Replaced the oversized, stale README with a current setup, model, demo, and
  quality-gate runbook.
- Rewrote the architecture notes around the implemented service, graph,
  provider, persistence, worker, governance, and evidence boundaries.
- Removed obsolete milestone/demo documents.
- Added this evidence-based hardening report.

## C. What Was Kept Intentionally

- Two realistic mock tickets, because ticket selection is required for the demo.
- Mock LLM and execution adapters, only for automated tests and explicit failure
  fallback.
- Deterministic hash embeddings as an offline/test fallback.
- Built-in QA knowledge chunks as product guidance, not fake runtime history.
- `.env.example` without credentials.
- The approved blueprint and current architecture documentation.
- `.tools/gh-extract`, because Git handoff uses the bundled GitHub CLI fallback.
- Local SQLite, Robot Framework, Redis/Celery, and package utilities required by
  the current demo architecture.

## D. Remaining Risks

### Critical before sharing the demo

- Rotate the OpenAI API key that was pasted into chat, update `.env`, and revoke
  the old key. It must be considered exposed.

### Production gaps

- Jira/Azure DevOps/GitLab connectors are not implemented.
- Authentication is local RBAC, not enterprise SSO.
- SQLite is suitable for a single demo instance; production needs PostgreSQL and
  shared transactional state.
- Vector retrieval is in memory; there is no durable production vector database.
- Rate limits and provider circuit state are not distributed across instances.
- Robot execution is local rather than isolated in a hardened execution sandbox.
- OpenTelemetry export, managed dashboards, and alert delivery are not wired.
- Strict Pydantic parsing of model-generated structured artifacts remains a
  recommended next quality milestone.

### Local environment

- Ollama was not reachable during verification. The configured external provider
  was reported ready, but no new billable model call was made with the exposed
  credential.
- LangGraph emits one pending-deprecation warning from its installed dependency.
- Docker Compose validation succeeded, with a host-only warning that Docker
  could not read the user's global `config.json` in the sandbox.
- `ConversationWorkspace.tsx` remains large; it is cohesive but should be split
  by workspace view before substantial UI expansion.

## E. How To Run

Install:

```powershell
python -m pip install -e ".[dev,worker]"
cd frontend
npm ci
cd ..
```

Backend and frontend:

```powershell
python -m uvicorn backend.main:app --reload
cd frontend
npm run dev
```

Optional worker or full stack:

```powershell
python -m backend.worker
docker compose up --build
```

Reset the demo:

```powershell
python scripts/reset_demo_state.py
```

Quality gates:

```powershell
python -m ruff check backend scripts tests
python -m pytest -q
python -m compileall -q backend scripts tests
cd frontend
npx tsc --noEmit --noUnusedLocals --noUnusedParameters
npm audit
npm run build
```

Verified on June 25, 2026:

- Ruff: passed.
- Python compile: passed.
- Pytest: 121 passed, one dependency deprecation warning.
- TypeScript strict unused check: passed.
- Frontend production build: passed.
- npm audit: zero vulnerabilities.
- pip dependency check: passed.
- Local and Celery worker imports/tasks: passed.
- Docker Compose configuration: passed.
- Backend and frontend startup: passed.
- Health, tickets, providers, empty workflow queue, and session creation API
  smoke checks: passed.
- Clean source package: 197 files, no `.env`, generated output, dependencies,
  caches, or build output.

## F. Demo Readiness Status

**Almost ready.**

The application is clean, executable, correctly wired, and suitable for a team
demo after one mandatory action: rotate the exposed external API key and perform
one short external-provider smoke workflow with the replacement credential.
Ollama can be installed later as the private local alternative.
