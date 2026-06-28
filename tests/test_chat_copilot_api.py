from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.storage.contexts import load_context


def test_chat_session_can_answer_system_questions() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester"},
    )

    assert created.status_code == 201
    session_id = created.json()["session"]["session_id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "What is mocked and what is real in the current system?",
        },
    )

    assert response.status_code == 200
    message = response.json()["message"]
    assert message["intent"] == "system_question"
    assert "Selected providers" in message["content"]
    assert message["actions"] == []


def test_chat_workflow_start_action_requires_confirmation_and_creates_context() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/chat/sessions",
        json={
            "created_by": "chat-tester",
            "ticket_id": "DEMO-TELCO-IMS-001",
        },
    )
    session_id = created.json()["session"]["session_id"]

    planned = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Analyze this ticket",
            "ticket_id": "DEMO-TELCO-IMS-001",
        },
    )

    assert planned.status_code == 200
    assistant = planned.json()["message"]
    assert assistant["intent"] == "workflow_start"
    assert len(assistant["actions"]) == 1
    action = assistant["actions"][0]
    assert action["kind"] == "start_workflow"
    assert action["status"] == "pending_confirmation"
    assert action["requires_confirmation"] is True

    confirmed = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )

    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["action"]["status"] == "completed"
    context_id = body["session"]["context_id"]
    context = load_context(context_id)
    assert context is not None
    assert context.ticket.id == "DEMO-TELCO-IMS-001"
    assert context.workflow_control.state == "initialized"
    assert "Workflow session" in body["message"]["content"]


def test_chat_can_report_workflow_status_and_plan_next_stage() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={
            "created_by": "chat-tester",
            "ticket_id": "DEMO-TELCO-IMS-001",
        },
    )
    session_id = created.json()["session"]["session_id"]
    planned = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Analyze DEMO-TELCO-IMS-001"},
    )
    start_action = planned.json()["message"]["actions"][0]
    confirmed = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{start_action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )
    context_id = confirmed.json()["session"]["context_id"]

    status_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Where are we in the workflow?",
            "context_id": context_id,
        },
    )
    assert status_response.status_code == 200
    assert status_response.json()["message"]["intent"] == "workflow_status"
    assert "Next stage" in status_response.json()["message"]["content"]

    next_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Run next stage",
            "context_id": context_id,
        },
    )
    assert next_response.status_code == 200
    next_action = next_response.json()["message"]["actions"][0]
    assert next_action["kind"] == "run_next_stage"

    run_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{next_action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )
    assert run_response.status_code == 200
    assert run_response.json()["action"]["status"] == "completed"
    assert load_context(context_id).workflow_control.completed_stages == ["ticket"]
