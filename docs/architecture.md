# AegisQA Architecture Notes

## Current Milestone

This package is an architecture-first local implementation of AegisQA.  It is
intentionally designed to prove the complete orchestration model with mock data
before connecting to company Jira/Azure, identity, Vault, databases, browsers, or
CI infrastructure.

The current synchronous workflow is:

```text
load_ticket
  -> requirement_agent
  -> coverage_planner
  -> test_case_generator
  -> test_data_resolver
  -> automation_generator
  -> validator
  -> human_approval
  -> execution_dispatcher
  -> investigation_coordinator
  -> memory_archiver
  -> report_generator
```

The graph now includes the approved lifecycle stages even when execution is
intentionally deferred until human approval.  On a normal mock workflow start,
execution is recorded as `skipped`, investigation is recorded as `skipped`, and a
local memory snapshot is archived under `generated/memory/`.  Approved workflows
can then be executed through the execution boundary.

## Runtime Boundaries

The core runtime still uses the blueprint separation:

- Agent boundary: `backend/agents/base.py`
- Skill boundary: `backend/skills/base.py`
- Tool boundary: `backend/tools/base.py`
- Workflow context: `backend/graph/state.py`
- Workflow graph: `backend/graph/workflow.py`
- Service orchestration: `backend/services/`
- Execution adapters: `backend/execution/base.py`
- Execution workers: `backend/workers/`
- Ticket connectors: `backend/tickets/base.py`
- Local security/RBAC: `backend/security/rbac.py`

The current deterministic slices are:

- `RequirementAgent -> AnalyzeRequirementSkill -> LocalRequirementHeuristicTool`
- `CoveragePlannerAgent -> PlanCoverageSkill -> LocalCoverageHeuristicTool`
- `TestCaseGeneratorAgent -> GenerateTestCasesSkill -> LocalTestCaseHeuristicTool`
- `TestDataResolverAgent -> ResolveTestDataSkill -> LocalTestDataHeuristicTool`
- `AutomationGeneratorAgent -> GenerateAutomationSkill -> LocalRobotAutomationTool`
- `ValidatorAgent -> ValidateAutomationSkill -> LocalRobotValidationTool`
- `HumanApprovalAgent -> RequestHumanApprovalSkill -> LocalHumanApprovalPolicyTool`
- `ReportGeneratorAgent -> GenerateReportSkill -> LocalReportGenerationTool`

## Tool Contract

`ToolRegistry.execute(...)` is the preferred call path.  It wraps every tool
invocation with:

- a typed `ToolResult`,
- retry metadata,
- duration metadata,
- input/output hashes,
- failure capture,
- context audit events.

Direct `tool.invoke(...)` remains available for tests and backward-compatible
low-level use, but workflow skills call tools through the contract wrapper.

## Security and RBAC

The API now has a local RBAC scaffold under `backend/security/rbac.py`.

Default local behavior is permissive so developers can prove the architecture
without a company identity provider.  Set `AEGISQA_AUTH_MODE=strict` to require
local headers or a development bearer token.

Supported roles:

- `viewer`
- `qa_engineer`
- `qa_lead`
- `admin`

Supported capabilities include ticket read/write, workflow start/read/approve,
workflow execution, artifact read, and audit read.  Routes are protected through
FastAPI dependencies while keeping local mock workflows easy to run.

## Ticket Connectors

The first ticket connector is `jira_mock`, registered in `backend/tickets/`.  It
returns Jira-shaped `TicketData` from the local mock ticket database and never
calls external APIs.  This proves the future Jira boundary while respecting the
current constraint to avoid company systems.

Useful endpoints:

```text
GET /api/v1/tickets/connectors
GET /api/v1/tickets/jira/mock
GET /api/v1/tickets/jira/mock/{ticket_id}
```

## Execution Adapters

Two adapters are registered:

- `mock`: deterministic execution with predictable pass/fail/skip behavior.
- `robot`: local Robot Framework CLI execution with artifact capture.

The `robot` adapter does not call external services.  It requires a local Robot
Framework installation and stores artifacts under `generated/execution/`.
When Robot is unavailable, the validator falls back to deterministic structural
validation so tests and local architecture demos remain reproducible.

Execution dispatch now goes through `backend/workers/`.  The default backend is
`local`, which preserves the FastAPI background-task fallback.  The `celery`
backend dispatches the same persisted execution run id to a Redis/Celery worker
when `AEGISQA_EXECUTION_WORKER_BACKEND=celery`.

## Intelligence Retrieval

Local RAG and episodic memory now use deterministic retrieval infrastructure:

- Embedding model: `local_hash_embedding`
- Vector store: `local_in_memory_vector`
- Reranker: `local_hybrid_reranker`
- Retention/invalidation: exposed on local knowledge and memory stores

This proves the vector retrieval shape while keeping local tests independent of
external embedding APIs or a production vector database.

## LLM Providers

`mock_llm` remains the default for deterministic tests.  Two real provider
boundaries are registered behind the same `BaseLLMProvider` contract:

- `openai_compatible`: external OpenAI-style `/v1/chat/completions` endpoint.
- `ollama`: local Ollama `/api/chat` endpoint with role-based model routing
  for RAG, coding, and reasoning prompts.

Switching providers is configuration-driven through `AEGISQA_DEFAULT_LLM_PROVIDER`.
The OpenAI-compatible provider also requires `AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true`
and `AEGISQA_OPENAI_COMPATIBLE_API_KEY`.  Provider configuration status is exposed
through `/api/v1/intelligence/llm-providers` and the provider catalog.
Local Ollama model availability and smoke tests are exposed through
`/api/v1/intelligence/ollama/models`.

## Persistence

Local SQLite persistence remains under `generated/storage/aegisqa.sqlite3`.
Generated runtime artifacts remain under `generated/` and are excluded from clean
packages.

`docker-compose.yml` provisions Postgres for the production database path, plus
Redis for Celery-compatible execution dispatch.  The current storage adapter is
still SQLite-backed until the Postgres adapter is implemented.

## Packaging Rule

Source packages must exclude local/generated material:

- `.venv/`
- `.tools/`
- `.pytest_cache/`
- `.git/`
- `node_modules/`
- `frontend/dist/`
- `generated/`
- `__pycache__/`
- `*.pyc`
- `aegisqa.egg-info/`

Use `python scripts/package_clean.py` to create a clean local source copy.


## Milestone 3 Lite Integration Architecture

The project now includes an explicit provider catalog under `backend/integrations/providers.py` and a local integration profile builder under `backend/integrations/profile.py`.

The selected local/mock providers are written into `TestContext.integration_profile` when a workflow starts. This lets reviewers see which integration boundaries were used without connecting to company APIs.

Default providers:

- Ticket connector: `jira_mock`
- Execution adapter: `mock`
- Artifact store: `local_fs`
- Secret provider: `mock_vault`
- Git handoff tool: `LocalGitHandoffTool`

New boundaries:

- Artifact store: `backend/artifacts/base.py`, `backend/artifacts/local.py`
- Secret provider: `backend/secrets/base.py`, `backend/secrets/mock_vault.py`
- Provider catalog: `backend/integrations/providers.py`
- Integration profile: `backend/integrations/profile.py`
- Integration APIs: `backend/api/routes/integrations.py`

The mock Vault provider returns secret references such as `mock-vault://jira/api-token` and never resolves real secret values. The local filesystem artifact store writes only to `generated/artifacts/`, which remains excluded from clean packages.

External providers are intentionally disabled by default with `AEGISQA_EXTERNAL_CONNECTORS_ENABLED=false`.
