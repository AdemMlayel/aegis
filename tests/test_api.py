from pathlib import Path
from uuid import uuid4

from starlette.testclient import TestClient

from backend.main import app
from backend.storage.audit import list_audit_events


def test_mock_ticket_endpoints_return_seed_data() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/tickets/mock")

    assert response.status_code == 200
    tickets = response.json()["tickets"]
    assert len(tickets) >= 5
    assert {ticket["id"] for ticket in tickets} >= {"MOCK-101", "MOCK-103"}

    filtered_response = client.get("/api/v1/tickets/mock?q=refund&priority=critical")

    assert filtered_response.status_code == 200
    filtered_tickets = filtered_response.json()["tickets"]
    assert [ticket["id"] for ticket in filtered_tickets] == ["MOCK-103"]

    ticket_response = client.get("/api/v1/tickets/mock/MOCK-101")

    assert ticket_response.status_code == 200
    ticket = ticket_response.json()["ticket"]
    assert ticket["title"] == "Money Transfer Feature"
    assert ticket["source"] == "fake"


def test_start_workflow_from_mock_ticket_endpoint(monkeypatch) -> None:
    monkeypatch.setattr("backend.integrations.git_handoff._is_git_repo", lambda: False)

    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start-from-mock-ticket",
        json={"created_by": "pytest", "ticket_id": "MOCK-101"},
    )

    assert response.status_code == 202
    context = response.json()["context"]
    assert context["workflow_status"] == "report_generated"
    assert context["ticket"]["id"] == "MOCK-101"
    assert context["ticket"]["assignee"] == "qa_engineer_001"
    assert context["approval"]["status"] == "pending_review"
    assert context["automation"]["TC001"]["validation"]["artifact_exists"] is True


def test_start_workflow_from_mock_ticket_accepts_intelligence_config(monkeypatch) -> None:
    monkeypatch.setattr("backend.integrations.git_handoff._is_git_repo", lambda: False)

    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start-from-mock-ticket",
        json={
            "created_by": "pytest",
            "ticket_id": "MOCK-101",
            "intelligence": {
                "llm_provider": "mock_llm",
                "embedding_provider": "local_hash_embeddings",
                "llm_model": "pytest-model-override",
            },
        },
    )

    assert response.status_code == 202
    context = response.json()["context"]
    assert context["intelligence_config"]["llm_provider"] == "mock_llm"
    assert context["intelligence_config"]["embedding_provider"] == "local_hash_embeddings"
    assert context["intelligence_config"]["llm_model"] == "pytest-model-override"
    assert context["intelligence_trace"]["configured_llm_provider"] == "mock_llm"
    assert context["intelligence_trace"]["configured_embedding_provider"] == "local_hash_embeddings"
    assert context["intelligence_trace"]["configured_llm_model"] == "pytest-model-override"
    assert context["intelligence_trace"]["llm_calls"]
    assert all(
        call["model"] == "pytest-model-override"
        for call in context["intelligence_trace"]["llm_calls"]
    )
    assert context["integration_profile"]["llm_provider"]["name"] == "mock_llm"
    assert context["integration_profile"]["embedding_provider"]["name"] == "local_hash_embeddings"


def test_start_workflow_from_missing_mock_ticket_returns_404() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start-from-mock-ticket",
        json={"created_by": "pytest", "ticket_id": "NOPE-404"},
    )

    assert response.status_code == 404


def test_workflow_list_endpoint_returns_recent_summaries() -> None:
    client = TestClient(app)
    ticket_id = f"QUEUE-{uuid4().hex[:8]}"

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": ticket_id,
                "title": "Queue History Feature",
                "description": "As a reviewer, I want to see workflow history.",
                "acceptance_criteria": ["Recent workflows are listed"],
                "priority": "medium",
                "labels": ["queue", "review"],
            },
        },
    )
    context = start_response.json()["context"]

    response = client.get(
        f"/api/v1/workflows?q={ticket_id}&approval_status=pending_review"
    )

    assert response.status_code == 200
    workflows = response.json()["workflows"]
    assert len(workflows) == 1
    assert workflows[0]["context_id"] == context["context_id"]
    assert workflows[0]["ticket_id"] == ticket_id
    assert workflows[0]["ticket_title"] == "Queue History Feature"
    assert workflows[0]["workflow_status"] == "report_generated"
    assert workflows[0]["approval_status"] == "pending_review"
    assert workflows[0]["execution_status"] == "skipped"
    assert workflows[0]["test_count"] == 3
    assert workflows[0]["automation_revision"] == 1


def test_execute_workflow_endpoint_records_mock_results(monkeypatch) -> None:
    client = TestClient(app)
    ticket_id = f"EXEC-{uuid4().hex[:8]}"

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": ticket_id,
                "title": "Execution Results Feature",
                "description": "As a reviewer, I want to run generated automation.",
                "acceptance_criteria": ["Mock execution results are saved"],
                "priority": "high",
                "labels": ["execution", "review"],
            },
        },
    )
    context_id = start_response.json()["context"]["context_id"]
    monkeypatch.setattr("backend.integrations.git_handoff._is_git_repo", lambda: False)
    approval_response = client.post(
        f"/api/v1/workflows/{context_id}/approval",
        json={
            "decision": "approve",
            "reviewed_by": "qa_reviewer",
            "comment": "Approved for local mock execution.",
        },
    )
    assert approval_response.status_code == 200

    response = client.post(
        f"/api/v1/workflows/{context_id}/execute",
        json={"run_by": "qa_runner"},
    )

    assert response.status_code == 200
    context = response.json()["context"]
    execution = context["execution"]
    summary = execution["summary"]
    assert context["workflow_status"] == "report_generated"
    assert context["investigation"]["status"] == "completed"
    assert context["memory_archive"]["status"] == "archived"
    assert context["execution_request"]["status"] == "completed"
    assert execution["status"] == "failed"
    assert execution["run_by"] == "qa_runner"
    assert summary["duration_ms"] > 0
    assert summary == {
        "total": 3,
        "passed": 2,
        "failed": 1,
        "skipped": 0,
        "duration_ms": summary["duration_ms"],
    }
    assert [result["status"] for result in execution["results"]] == [
        "passed",
        "failed",
        "passed",
    ]
    assert any(
        event["event_type"] == "execution_completed"
        for event in context["audit_log"]
    )

    saved_response = client.get(f"/api/v1/workflows/{context_id}")
    assert saved_response.status_code == 200
    assert saved_response.json()["context"]["execution"]["status"] == "failed"

    queue_response = client.get(f"/api/v1/workflows?q={ticket_id}")
    assert queue_response.status_code == 200
    workflow = queue_response.json()["workflows"][0]
    assert workflow["execution_status"] == "failed"
    assert workflow["execution_passed"] == 2
    assert workflow["execution_failed"] == 1
    assert workflow["execution_skipped"] == 0


def test_start_workflow_endpoint_returns_completed_context(monkeypatch) -> None:
    monkeypatch.setattr("backend.integrations.git_handoff._is_git_repo", lambda: False)

    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": "FAKE-API-1",
                "title": "Money Transfer Feature",
                "description": (
                    "As an authenticated customer, I want to transfer money."
                ),
                "acceptance_criteria": ["Transfer completes within 3 seconds"],
                "priority": "high",
                "labels": ["banking"],
            },
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["context"]["workflow_status"] == "report_generated"
    context_id = body["context"]["context_id"]
    assert body["context"]["ticket"]["id"] == "FAKE-API-1"
    assert set(body["context"]["test_data"]) == {"TC001", "TC002", "TC003"}
    assert set(body["context"]["automation"]) == {"TC001", "TC002", "TC003"}
    robot_path = body["context"]["automation"]["TC001"]["robot_file"]
    assert robot_path.endswith(".robot")
    assert body["context"]["automation"]["TC001"]["validation"]["artifact_exists"] is True
    assert body["context"]["approval"]["status"] == "pending_review"
    assert body["context"]["reports"]["total_test_cases"] == 3

    file_response = client.get(
        f"/api/v1/automation/files/FAKE-API-1/{Path(robot_path).name}"
    )

    assert file_response.status_code == 200
    file_body = file_response.json()
    assert file_body["path"] == robot_path
    assert "Money Transfer Feature - Happy Path" in file_body["content"]

    context_response = client.get(f"/api/v1/workflows/{context_id}")
    assert context_response.status_code == 200
    assert context_response.json()["context"]["context_id"] == context_id

    approval_response = client.post(
        f"/api/v1/workflows/{context_id}/approval",
        json={
            "decision": "approve",
            "reviewed_by": "qa_reviewer",
            "comment": "Looks ready for handoff.",
        },
    )

    assert approval_response.status_code == 200
    approval_body = approval_response.json()
    approval = approval_body["context"]["approval"]
    assert approval["status"] == "approved"
    assert approval["decided_by"] == "qa_reviewer"
    assert approval["comments"] == ["Looks ready for handoff."]
    assert approval["git_status"] in {"completed", "blocked"}
    assert approval["git_branch"] == "aegis/fake_api_1"
    assert approval["git_pr_url"] is None
    assert approval["git_handoff_path"].endswith(".json")
    assert Path(approval["git_handoff_path"]).is_file()
    if approval["git_status"] == "blocked":
        assert approval["git_error"]
        assert approval_body["context"]["workflow_status"] == "approved_git_blocked"
    else:
        assert approval_body["context"]["workflow_status"] == "approved_git_complete"
    assert any(
        event["event_type"] == "git_execution"
        for event in approval_body["context"]["audit_log"]
    )
    assert any(
        event["event_type"] == "tool_invoked"
        and event["metadata"]["tool_name"] == "LocalGitHandoffTool"
        for event in approval_body["context"]["audit_log"]
    )

    saved_response = client.get(f"/api/v1/workflows/{context_id}")
    assert saved_response.status_code == 200
    assert saved_response.json()["context"]["approval"]["status"] == "approved"
    context_audit_events = list_audit_events(context_id=context_id, limit=20)
    assert any(
        event.event_type == "approval_decision" for event in context_audit_events
    )
    assert any(
        event.event_type == "automation_file_read"
        for event in list_audit_events(limit=20)
    )


def test_automation_file_endpoint_rejects_non_robot_file() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/automation/files/FAKE-API-1/output.txt")

    assert response.status_code == 400


def test_approval_endpoint_records_requested_changes() -> None:
    client = TestClient(app)

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": "FAKE-CHANGES-1",
                "title": "Money Transfer Feature",
                "description": "As an authenticated customer, I want to transfer money.",
                "acceptance_criteria": ["Transfer completes within 3 seconds"],
                "priority": "high",
                "labels": ["banking"],
            },
        },
    )
    context_id = start_response.json()["context"]["context_id"]

    approval_response = client.post(
        f"/api/v1/workflows/{context_id}/approval",
        json={
            "decision": "request_changes",
            "reviewed_by": "qa_reviewer",
            "comment": "Please add an insufficient-funds assertion.",
        },
    )

    assert approval_response.status_code == 200
    context = approval_response.json()["context"]
    assert context["workflow_status"] == "pending_human_review"
    assert context["approval"]["status"] == "pending_review"
    assert context["approval"]["decided_by"] is None
    assert context["approval"]["comments"] == [
        "Please add an insufficient-funds assertion."
    ]
    assert context["automation_revision"] == 2
    assert context["automation"]["TC001"]["revision"] == 2
    assert context["review_feedback"] == [
        {
            "requested_at": context["review_feedback"][0]["requested_at"],
            "requested_by": "qa_reviewer",
            "comment": "Please add an insufficient-funds assertion.",
            "status": "applied",
        }
    ]
    assert any(
        event["event_type"] == "automation_regenerated"
        for event in context["audit_log"]
    )

    robot_path = context["automation"]["TC001"]["robot_file"]
    file_response = client.get(
        f"/api/v1/automation/files/FAKE-CHANGES-1/{Path(robot_path).name}"
    )

    assert file_response.status_code == 200
    assert (
        "Reviewer feedback applied: Please add an insufficient-funds assertion."
        in file_response.json()["content"]
    )


def test_request_changes_requires_comment() -> None:
    client = TestClient(app)

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": "FAKE-NO-COMMENT-1",
                "title": "Money Transfer Feature",
                "description": "As an authenticated customer, I want to transfer money.",
                "acceptance_criteria": ["Transfer completes within 3 seconds"],
                "priority": "high",
                "labels": ["banking"],
            },
        },
    )
    context_id = start_response.json()["context"]["context_id"]

    approval_response = client.post(
        f"/api/v1/workflows/{context_id}/approval",
        json={
            "decision": "request_changes",
            "reviewed_by": "qa_reviewer",
        },
    )

    assert approval_response.status_code == 400
