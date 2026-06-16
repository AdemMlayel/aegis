# Milestone 2 — Orchestration Alignment Notes

Goal: align the local architecture proof with the approved AegisQA v3 orchestration blueprint while keeping all company/external API dependencies mocked or local.

## Scope completed

- Extended `TestContext` to schema version `0.9.0` with workflow tracing, graph iteration, validation retry controls, execution request metadata, execution evidence, investigation, and local memory archive metadata.
- Added a validation retry gate in the orchestration loop.
- Added conditional LangGraph routing from validation back to automation generation when validation fails and retry capacity remains.
- Added sequential fallback routing with the same retry semantics when LangGraph is unavailable.
- Added post-approval orchestration helper for execution, investigation, memory archive, and reporting.
- Updated execution dispatcher to use local execution adapters through the adapter registry.
- Kept default execution deferred until human approval.
- Kept company/external APIs out of scope; execution remains local through `mock` or local Robot CLI adapter.
- Added local investigation coordinator behavior based on execution results.
- Added local memory archive placeholder that writes JSON snapshots under generated memory output.
- Moved Git handoff behind the tool registry through `LocalGitHandoffTool`.
- Added tests for validation retry routing, workflow tracing, post-execution analysis, and Git tool invocation audit evidence.

## External dependency policy

This milestone intentionally does **not** call Jira, Azure DevOps, GitLab, company Git, company identity providers, Vault, Redis, Celery, LLM APIs, or vector databases. The implementation proves the architecture and workflow boundaries with mock/local adapters only.

## Verification

```bash
python -m pytest -q
# 68 passed

cd frontend
npm ci
npm run build
# build successful
```
