# AegisQA

Executable architecture spine for the AegisQA AI-powered test automation orchestrator.

This package is intentionally local-first.  It proves the concrete architecture,
workflow, security boundaries, ticket connector boundary, tool contract, and
execution adapter boundary with mock data before connecting to company Jira,
Azure DevOps, identity, Vault, or CI infrastructure.

## Current Scope

Implemented and test-covered locally:

- Typed `TestContext` schema `0.10.0` with integration-profile metadata.
- Agent, Skill, Tool, Execution Adapter, Ticket Connector, Artifact Store, Secret Provider, and Provider Catalog registries.
- Contract-based tool execution with retries, duration, input/output hashes, and audit records.
- Local RBAC/auth scaffold with permissive mode by default and strict mode available.
- SQLite-backed mock ticket database seeded from `backend/mock_data/tickets.json`.
- Versioned SQLite migration runner for the local schema and future Postgres path.
- Service-layer boundary for workflow, execution, integration, and intelligence orchestration.
- Jira-shaped mock connector: `jira_mock`, plus generic connector start/search endpoints.
- Workflow lifecycle:
  `load_ticket -> requirement_agent -> coverage_planner -> test_case_generator -> test_data_resolver -> automation_generator -> validator -> human_approval -> execution_dispatcher -> investigation_coordinator -> memory_archiver -> report_generator`.
- Deterministic requirement analysis, coverage planning, test-case generation, test-data resolution, and Robot generation.
- Robot validation with real `robot --dryrun` when available and deterministic structural validation when Robot is absent.
- Human approval gate with approve/request-changes flow.
- Local Git handoff attempt after approval when the repo and GitHub CLI are available.
- Mock execution adapter and CI-style execution result APIs.
- Real local Robot execution adapter behind the execution adapter interface.
- Execution result history, event logs, JSON, JUnit XML, HTML report, and WebSocket stream.
- Investigation and local memory archive placeholders in the workflow graph.
- Local filesystem artifact store: `local_fs`.
- Mock Vault-compatible secret provider: `mock_vault`, returning references only.
- Provider catalog endpoints that show selected local/mock providers and keep external connectors disabled.
- React review dashboard under `frontend/`, including provider catalog and intelligence metadata panels.
- 78 passing Python tests.

## What Is Deliberately Mocked

The following remain mocked or local-only until company access and security approval are available:

- Jira/Azure DevOps/GitLab external APIs.
- Company identity provider.
- Vault/secret store.
- Real CI runners.
- Browser/device farms.
- Vector memory and production database.
- LLM/RAG providers.

## Install and Test

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
```

Linux/macOS:

```bash
python -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```

Robot Framework is declared as a dependency, but tests remain green even when a
global `robot` CLI is unavailable because the local validator falls back to
structural Robot validation.

## Run API

```bash
python -m uvicorn backend.main:app --reload
```

Health check:

```http
GET http://127.0.0.1:8000/health
```

## Local Security / RBAC

Default mode is permissive for local mock-data demos.

```bash
AEGISQA_AUTH_MODE=permissive
```

Strict local mode:

```bash
AEGISQA_AUTH_MODE=strict
AEGISQA_DEV_TOKEN=change-me-local-only
```

Then call protected APIs with either:

```http
Authorization: Bearer change-me-local-only
```

or local development headers:

```http
X-Aegis-User: qa-lead
X-Aegis-Role: qa_lead
```

RBAC endpoints:

```http
GET /api/v1/security/me
GET /api/v1/security/rbac
```

## Ticket Connectors

Mock tickets:

```http
GET /api/v1/tickets/mock
GET /api/v1/tickets/mock/{ticket_id}
```

Jira-shaped local connector with no external API call:

```http
GET /api/v1/tickets/connectors
GET /api/v1/tickets/connectors/jira_mock/health
GET /api/v1/tickets/connectors/jira_mock/tickets
GET /api/v1/tickets/jira/mock
GET /api/v1/tickets/jira/mock/{ticket_id}
```

## Start a Workflow

Start from a selected ticket connector, defaulting to `jira_mock`:

```http
POST /api/v1/workflows/start-from-ticket-connector
Content-Type: application/json

{
  "created_by": "engineer_001",
  "connector": "jira_mock",
  "ticket_id": "MOCK-101"
}
```

Start from a seeded mock ticket:

```http
POST /api/v1/workflows/start-from-mock-ticket
Content-Type: application/json

{
  "created_by": "engineer_001",
  "ticket_id": "MOCK-101"
}
```

Start from an inline ticket:

```http
POST /api/v1/workflows/start
Content-Type: application/json

{
  "created_by": "engineer_001",
  "ticket": {
    "id": "FAKE-001",
    "title": "Money Transfer Feature",
    "description": "As a customer, I want to transfer money to another account.",
    "acceptance_criteria": [
      "Transfer completes within 3 seconds",
      "Balance updates immediately"
    ],
    "priority": "high",
    "labels": ["banking", "payments"]
  }
}
```

List workflow summaries:

```http
GET /api/v1/workflows?approval_status=pending_review
```

Read a workflow:

```http
GET /api/v1/workflows/{context_id}
```

Read a generated Robot file:

```http
GET /api/v1/automation/files/{ticket_id}/{file_name}
```

## Approval

Request changes:

```http
POST /api/v1/workflows/{context_id}/approval
Content-Type: application/json

{
  "decision": "request_changes",
  "reviewed_by": "qa_reviewer",
  "comment": "Please add an insufficient-funds assertion."
}
```

Approve:

```http
POST /api/v1/workflows/{context_id}/approval
Content-Type: application/json

{
  "decision": "approve",
  "reviewed_by": "qa_reviewer",
  "comment": "Ready for local Git handoff."
}
```

## Execute Generated Automation

Mock adapter:

```http
POST /api/v1/execute
Content-Type: application/json

{
  "suite": "MOCK-101",
  "adapter": "mock",
  "branch": "feature/generated-tests",
  "env": "staging",
  "tags": ["smoke", "generated"],
  "actor": "ci_runner"
}
```

Robot adapter, local CLI only:

```http
POST /api/v1/execute
Content-Type: application/json

{
  "suite": "MOCK-101",
  "adapter": "robot",
  "env": "local",
  "actor": "qa_runner"
}
```

Inspect results:

```http
GET /api/v1/results/{run_id}
GET /api/v1/results/{run_id}/summary.json
GET /api/v1/results/{run_id}/logs
GET /api/v1/results/{run_id}/junit.xml
GET /api/v1/results/{run_id}/report.html
```

Live status stream:

```text
ws://127.0.0.1:8000/api/v1/ws/exec/{run_id}
```

## Integration Provider Catalog

Milestone 3 Lite keeps company/external APIs disabled and proves the swappable boundaries locally.

```http
GET /api/v1/integrations/providers
GET /api/v1/integrations/profile
GET /api/v1/integrations/secrets/references
GET /api/v1/integrations/artifacts
```

Selected local/mock providers by default:

```text
ticket_connector: jira_mock
execution_adapter: mock
artifact_store: local_fs
secret_provider: mock_vault
git_handoff: LocalGitHandoffTool
```

`AEGISQA_EXTERNAL_CONNECTORS_ENABLED=false` is the default and prevents accidental external-provider usage during architecture demos.

## Run Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Clean Package

The source package should not include local runtime artifacts, virtual
environments, dependency directories, or generated files.  To create a clean copy:

```bash
python scripts/package_clean.py
```

The generated clean copy excludes `.venv/`, `.tools/`, `.pytest_cache/`, `.git/`,
`node_modules/`, `frontend/dist/`, `generated/`, `__pycache__/`, `*.pyc`, and
`aegisqa.egg-info/`.

## Milestone 4 — Local AI/RAG/Memory Intelligence Layer

Milestone 4 adds the blueprint's AI-native architecture while keeping the project fully local and mock-data driven. No company Jira, Azure DevOps, Confluence, Vault, LLM API, or internal execution environment is required.

Implemented local intelligence boundaries:

- `mock_llm`: deterministic LLM provider abstraction for repeatable tests.
- Prompt registry and versioned prompt templates.
- `local_knowledge`: seeded local knowledge/RAG store.
- `local_episodic_memory`: seeded local previous-failure memory store.
- Intelligence trace on `TestContext` with knowledge refs, memory refs, prompt versions, and mock LLM usage.
- RequirementAgent enrichment with local RAG + memory context.
- CoveragePlanner enrichment with memory-backed regression hints.
- TestCaseGenerator enrichment with evidence and memory references.
- ReportGenerator enrichment with AI/RAG/memory traceability.

Useful local endpoints:

```text
GET /api/v1/intelligence/prompts
GET /api/v1/intelligence/llm-providers
GET /api/v1/intelligence/knowledge/search?query=banking%20transfer%20risk
GET /api/v1/intelligence/memory/search?query=transfer%20balance%20regression
GET /api/v1/integrations/providers
```

Default local AI profile:

```text
llm_provider: mock_llm
knowledge_store: local_knowledge
memory_store: local_episodic_memory
external_connectors_enabled: false
```

The mock provider and stores are intentionally deterministic. They prove the architecture and workflow wiring now, while allowing real providers such as Ollama, OpenAI, internal LLM gateways, Confluence/RAG indexes, pgvector, or Qdrant to be added later behind the same boundaries.
