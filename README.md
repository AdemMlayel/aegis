# AegisQA

Executable spine for the AegisQA AI-powered test automation orchestrator.

This milestone proves the core state flow from ticket intake through starter
Robot Framework file generation and validation before adding real Jira/Azure
integrations, LLM calls, memory, Docker isolation, execution, or the dashboard.

## What Exists

- Typed `TestContext` and related Pydantic models.
- Stub workflow nodes:
  `load_ticket -> requirement_agent -> coverage_planner -> test_case_generator -> test_data_resolver -> automation_generator -> validator -> human_approval -> report_generator`.
- Deterministic test-data resolution for generated test cases.
- Minimal `.robot` files written to `generated/robot/<ticket-id>/`.
- Robot Framework dry-run validation in a dedicated validator node.
- Pending-review approval state with approve/request-changes decisions.
- Automatic regeneration after `request_changes`, including reviewer feedback in regenerated Robot files.
- File-backed workflow context persistence under `generated/contexts/`.
- Git branch/commit/PR execution on approval when the project is inside a Git repo.
- Git execution result payloads under `generated/git_handoff/`.
- JSONL audit events under `generated/audit/events.jsonl`.
- FastAPI endpoint: `POST /api/v1/workflows/start`.
- FastAPI endpoint: `GET /api/v1/workflows/{context_id}`.
- FastAPI endpoint: `POST /api/v1/workflows/{context_id}/approval`.
- FastAPI endpoint: `GET /api/v1/automation/files/{ticket_id}/{file_name}`.
- Unit tests for workflow state flow and the API endpoint.

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

Then call:

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
