# AegisQA

Executable spine for the AegisQA AI-powered test automation orchestrator.

This milestone proves the local product loop from ticket intake through starter
Robot Framework file generation, validation, mock execution, and review before
adding real Jira/Azure integrations, LLM calls, memory, Docker isolation, or a
real execution adapter.

## What Exists

- Typed `TestContext` and related Pydantic models.
- Base Agent, Skill, and Tool registries for the blueprint runtime boundary.
- SQLite-backed mock ticket database seeded from `backend/mock_data/tickets.json`.
- Stub workflow nodes:
  `load_ticket -> requirement_agent -> coverage_planner -> test_case_generator -> test_data_resolver -> automation_generator -> validator -> human_approval -> report_generator`.
- Deterministic test-data resolution for generated test cases.
- Minimal `.robot` files written to `generated/robot/<ticket-id>/`.
- Robot Framework dry-run validation in a dedicated validator node.
- Mock execution results saved on workflow contexts.
- SQLite-backed CI execution runs with JSON, JUnit XML, and HTML result views.
- Pending-review approval state with approve/request-changes decisions.
- Automatic regeneration after `request_changes`, including reviewer feedback in regenerated Robot files.
- SQLite-backed workflow context persistence under `generated/storage/aegisqa.sqlite3`.
- Git branch/commit/PR execution on approval when the project is inside a Git repo.
- Git execution result payloads under `generated/git_handoff/`.
- SQLite audit events under `generated/storage/aegisqa.sqlite3`.
- FastAPI endpoint: `GET /api/v1/tickets/mock`.
- FastAPI endpoint: `GET /api/v1/tickets/mock/{ticket_id}`.
- FastAPI endpoint: `POST /api/v1/tickets/mock`.
- FastAPI endpoint: `PATCH /api/v1/tickets/mock/{ticket_id}`.
- FastAPI endpoint: `POST /api/v1/tickets/mock/{ticket_id}/comments`.
- FastAPI endpoint: `DELETE /api/v1/tickets/mock/{ticket_id}`.
- FastAPI endpoint: `GET /api/v1/workflows`.
- FastAPI endpoint: `POST /api/v1/workflows/start`.
- FastAPI endpoint: `POST /api/v1/workflows/start-from-mock-ticket`.
- FastAPI endpoint: `GET /api/v1/workflows/{context_id}`.
- FastAPI endpoint: `POST /api/v1/workflows/{context_id}/execute`.
- FastAPI endpoint: `POST /api/v1/workflows/{context_id}/approval`.
- FastAPI endpoint: `POST /api/v1/execute`.
- FastAPI endpoint: `GET /api/v1/results`.
- FastAPI endpoint: `GET /api/v1/results/{run_id}`.
- FastAPI endpoint: `GET /api/v1/results/{run_id}/summary.json`.
- FastAPI endpoint: `GET /api/v1/results/{run_id}/junit.xml`.
- FastAPI endpoint: `GET /api/v1/results/{run_id}/report.html`.
- FastAPI endpoint: `GET /api/v1/automation/files/{ticket_id}/{file_name}`.
- React review dashboard under `frontend/`, including workflow queue and execution result history.
- Unit tests for workflow state flow, architecture boundaries, persistence, and API endpoints.

## Run Tests

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

## Run API

```powershell
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

## Run Dashboard

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The dashboard proxies `/api` requests to the
FastAPI server on `http://127.0.0.1:8000` and includes a mock-ticket browser
for starting workflows without Jira/Azure access, plus persisted execution
history with JSON, JUnit, and HTML result links.

Then call:

```http
GET http://127.0.0.1:8000/api/v1/tickets/mock
```

Filter mock tickets by text, priority, status, assignee, or label:

```http
GET http://127.0.0.1:8000/api/v1/tickets/mock?q=refund&priority=critical&status=in_progress
```

Create or update local mock tickets while real Jira/Azure access is unavailable:

```http
POST http://127.0.0.1:8000/api/v1/tickets/mock
Content-Type: application/json

{
  "id": "MOCK-900",
  "title": "Local Experiment Ticket",
  "description": "As a QA engineer, I want a mutable local ticket.",
  "acceptance_criteria": ["Local tickets can be filtered and used to start workflows"],
  "priority": "medium",
  "labels": ["local", "experiment"],
  "assignee": "qa_engineer_001",
  "source": "fake",
  "status": "backlog"
}
```

Start from a seeded mock ticket:

```http
POST http://127.0.0.1:8000/api/v1/workflows/start-from-mock-ticket
Content-Type: application/json

{
  "created_by": "engineer_001",
  "ticket_id": "MOCK-101"
}
```

List saved workflow summaries:

```http
GET http://127.0.0.1:8000/api/v1/workflows?approval_status=pending_review
```

Run mock execution for a workflow:

```http
POST http://127.0.0.1:8000/api/v1/workflows/{context_id}/execute
Content-Type: application/json

{
  "run_by": "qa_engineer_001"
}
```

Trigger the CI-style execution boundary by workflow `context_id` or ticket id:

```http
POST http://127.0.0.1:8000/api/v1/execute
Content-Type: application/json

{
  "suite": "MOCK-101",
  "branch": "feature/generated-tests",
  "env": "staging",
  "tags": ["smoke", "generated"],
  "actor": "ci_runner"
}
```

Inspect saved execution results:

```http
GET http://127.0.0.1:8000/api/v1/results/{run_id}
GET http://127.0.0.1:8000/api/v1/results/{run_id}/summary.json
GET http://127.0.0.1:8000/api/v1/results/{run_id}/junit.xml
GET http://127.0.0.1:8000/api/v1/results/{run_id}/report.html
```

Or start from an inline ticket:

```http
POST http://127.0.0.1:8000/api/v1/workflows/start
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

Read a generated Robot file:

```http
GET http://127.0.0.1:8000/api/v1/automation/files/FAKE-001/TC001_money_transfer_feature_happy_path.robot
```

Approve or request changes:

```http
POST http://127.0.0.1:8000/api/v1/workflows/{context_id}/approval
Content-Type: application/json

{
  "decision": "approve",
  "reviewed_by": "qa_engineer_001",
  "comment": "Ready for Git handoff."
}
```

To request changes and immediately regenerate:

```http
POST http://127.0.0.1:8000/api/v1/workflows/{context_id}/approval
Content-Type: application/json

{
  "decision": "request_changes",
  "reviewed_by": "qa_engineer_001",
  "comment": "Please add an insufficient-funds assertion."
}
```

When approved inside a Git work tree, AegisQA creates or switches to the
`aegis/<ticket-id>` branch, stages the generated Robot files, commits them, and
attempts `gh pr create` when the GitHub CLI is available. Outside a Git work
tree, approval still succeeds and records `git_status: "blocked"` with the
reason in the approval block and handoff payload.
