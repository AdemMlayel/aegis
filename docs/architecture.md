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
- Execution adapters: `backend/execution/base.py`
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

## Controlled Workflow Sessions

`backend/services/workflow_control.py` adds a persisted logical-stage layer over
the existing graph nodes. It does not replace the graph or duplicate agent
logic. Each stage delegates to the same node functions used by the synchronous
workflow.

The supported modes are autonomous, approval-required, and step-by-step.
Control state, stage revisions, and review decisions live in
`TestContext.workflow_control`. Operational events are stored separately in
SQLite with a monotonic sequence cursor so dashboards can poll incrementally.

Pause requests take effect between logical stages. Long-running provider or
tool calls finish before the pause is observed.

Robot artifact edits are versioned in `artifact_revisions`. Editing an artifact
clears its validation result and invalidates downstream approval/report state,
so manually changed code cannot retain an earlier green status.

Validation produces a deterministic summary in the workflow context. Its
quality score combines requirement traceability, artifact dry-run results,
resolved test-data references, and requirement completeness. The dashboard
shows every score component, validator mode, retry history, missing requirement
references, and per-artifact errors. Failed validation cannot be approved.

Final report exports are assembled by `backend/services/report_packages.py`.
The controller exposes a manifest, technical Markdown, executive Markdown, and
an in-memory ZIP. The package includes the typed context, test cases, validation
summary, decision history, Robot files, and any real execution, investigation,
memory, or Git handoff evidence. Every manifest entry records its byte size and
SHA-256 hash, and all filesystem inputs are restricted to generated roots.

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
workflow execution, artifact read/edit, and audit read. Routes are protected through
FastAPI dependencies while keeping local mock workflows easy to run.

## Agent Governance and Observability

Every registered agent now receives a stable identity under the
`aegisqa.agent.*` trust domain, a service-account label, owner, version, and risk
tier. `backend/governance/policy.py` derives an enforceable policy for each
identity. Skill creation, tool execution, and model-provider calls all consult
that policy. An agent cannot execute undeclared skills, a skill cannot execute
undeclared tools, and deterministic agents cannot acquire model access.

The gateway middleware assigns or propagates `X-Request-ID`, records structured
JSON request logs, persists request latency/status, enforces per-actor rate
limits and organization daily quotas, and applies a request timeout. Model calls
atomically reserve their maximum token allowance before provider execution.
Reservations enforce organization, per-call, per-workflow, model-call, and
concurrent-request limits, then settle against the provider's actual usage.
Provider failures feed circuit breakers; unavailable or open providers use the
explicit deterministic fallback where policy permits.

SQLite migrations persist request, agent, and model invocation records.
Model telemetry includes prompt/output tokens, latency, estimated external cost,
fallback origin, agent identity, request ID, workflow context, and organization.
The `/api/v1/observability/*` endpoints expose summaries, quota status,
operational health, and invocation details. `/health/live` and `/health/ready`
support orchestrator probes, while `/metrics` emits Prometheus-compatible
request, agent, model, token, cost, reservation, and circuit metrics.
This is a production-shaped local implementation; multi-instance deployments
still need shared Redis/PostgreSQL rate-limit and circuit state, an
OpenTelemetry exporter, managed metrics storage, and alert delivery.

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

## Persistence

Local SQLite persistence remains under `generated/storage/aegisqa.sqlite3`.
Generated runtime artifacts remain under `generated/` and are excluded from clean
packages.

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
