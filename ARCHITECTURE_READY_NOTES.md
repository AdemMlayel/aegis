# Architecture-Ready Stabilization Notes

## Scope Applied

This revision focuses on a concrete local architecture proof while deliberately
avoiding company/external APIs.  All Jira behavior is represented through a
mock Jira connector backed by local mock tickets.

## Main Changes

- Clean packaging support through `scripts/package_clean.py`.
- Reproducibility cleanup: removed invalid `httpx2` dev dependency.
- Python tests green: `86 passed`.
- Frontend build verified after fresh `npm ci`.
- Local RBAC/auth scaffold added with permissive and strict modes.
- Workflow graph extended with execution dispatch, investigation, and memory archive stages.
- Tool contract formalized through `ToolRegistry.execute`, `ToolResult`, hashes, retries, duration, and audit events.
- Mock Jira connector added under `backend/tickets/`.
- Real local Robot execution adapter added under `backend/execution/robot.py`.
- Robot validation now supports deterministic structural fallback when the Robot CLI is unavailable.

## External Systems

Not connected by design:

- Company Jira/Azure/GitLab APIs.
- Company identity provider.
- Vault or production secrets.
- Production CI runners.
- LLM/RAG/vector memory providers.

## Verification

Commands run successfully:

```bash
python -m pytest -q
# 86 passed

cd frontend
npm ci
npm run build
# vite build completed successfully
```
