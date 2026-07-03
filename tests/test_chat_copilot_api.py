from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.storage.contexts import load_context
from backend.storage.mock_tickets import get_mock_ticket_record


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


def test_chat_session_explains_system_knowledge_topics() -> None:
    client = TestClient(app)
    created = client.post("/api/v1/chat/sessions", json={"created_by": "chat-tester"})
    session_id = created.json()["session"]["session_id"]

    cases = [
        ("what are the workflow stages", "eight ordered stages"),
        ("what agents are there", "requirement_agent"),
        ("how does governance work", "tool registry"),
        ("explain the architecture", "React dashboard"),
    ]
    for message, expected_fragment in cases:
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"actor": "chat-tester", "message": message},
        )
        assert response.status_code == 200
        body = response.json()["message"]
        assert body["intent"] == "system_knowledge", message
        assert expected_fragment in body["content"], message
        # System-knowledge answers are informational only — never an action.
        assert body["actions"] == [], message


def test_system_knowledge_intent_does_not_shadow_operational_intents() -> None:
    """Adding conceptual answers must not break action routing."""
    from backend.chat.intent_classifier import classify_chat_intent

    assert classify_chat_intent("start analysis").intent == "workflow_start"
    assert classify_chat_intent("where are we").intent == "workflow_status"
    assert classify_chat_intent("run next stage").intent == "workflow_step"
    assert classify_chat_intent("approve").intent == "approval_request"
    assert classify_chat_intent("execute the tests").intent == "execution_request"
    assert classify_chat_intent("create ticket from this manual test scenario").intent == "ticket_intake"


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


def test_chat_ticket_intake_creates_sanitized_ticket_and_start_action() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester"},
    )
    session_id = created.json()["session"]["session_id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/ticket-intake",
        json={
            "actor": "chat-tester",
            "file_name": "manual_scenario.md",
            "content_type": "text/markdown",
            "file_content": """
Ticket ID: INTAKE-AUTO-001
Title: Validate refund approval API
Description: Verify a sanitized refund approval request through http://internal.example.test.
Business objective: reduce manual regression effort.
Test objective: automate the API approval happy path.
System under test: INTERNAL_SERVICE_A
Environment: TEST_ENVIRONMENT at 10.20.30.40
Preconditions:
- Test user exists
- API token: super-secret-token
Test Steps:
1. Submit refund request payload
2. Approve the refund request
3. Read the final status
Expected Outputs:
- Request is accepted
- Final status is approved
Validation Rules:
- Response status must be 200
- Audit event must be written
Required Tools:
- Robot Framework
- REST API client
""",
        },
    )

    assert response.status_code == 200
    body = response.json()
    message = body["message"]
    assert message["intent"] == "ticket_intake"
    assert "Created sanitized ticket `INTAKE-AUTO-001`" in message["content"]
    assert message["metadata"]["assessment"]["automatable"] is True
    assert len(message["actions"]) == 1
    action = message["actions"][0]
    assert action["kind"] == "start_workflow"
    assert action["ticket_id"] == "INTAKE-AUTO-001"

    ticket = get_mock_ticket_record("INTAKE-AUTO-001")
    assert ticket is not None
    ticket_json = ticket.model_dump_json()
    assert "http://internal.example.test" not in ticket_json
    assert "10.20.30.40" not in ticket_json
    assert "super-secret-token" not in ticket_json
    assert "URL_PLACEHOLDER" in ticket_json
    assert "IP_ADDRESS_PLACEHOLDER" in ticket_json
    assert ticket.status == "ready"

    confirmed = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )
    assert confirmed.status_code == 200
    context = load_context(confirmed.json()["session"]["context_id"])
    assert context is not None
    assert context.ticket.id == "INTAKE-AUTO-001"


def test_chat_ticket_intake_blocks_non_automatable_scenario() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester"},
    )
    session_id = created.json()["session"]["session_id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/ticket-intake",
        json={
            "actor": "chat-tester",
            "description": """
Ticket ID: INTAKE-MANUAL-001
Title: Subjective brand quality review
Description: Manual only visual inspection requiring human judgement.
Expected Outputs:
- The page looks good to the reviewer.
""",
        },
    )

    assert response.status_code == 200
    body = response.json()
    message = body["message"]
    assert message["intent"] == "ticket_intake"
    assert message["metadata"]["assessment"]["automatable"] is False
    assert message["metadata"]["assessment"]["readiness"] == "not_automatable"
    assert message["actions"] == []
    assert "not ready for automation" in message["content"]
    ticket = get_mock_ticket_record("INTAKE-MANUAL-001")
    assert ticket is not None
    assert ticket.status == "blocked"


def test_chat_message_can_create_ticket_from_pasted_description() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester"},
    )
    session_id = created.json()["session"]["session_id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": """
Create ticket from this manual test scenario:
Ticket ID: INTAKE-PASTE-001
Title: Validate mobile login event
Test objective: automate the mobile login success path.
Test Steps:
1. Launch the mobile app
2. Enter valid sanitized credentials
3. Tap login
Expected Outputs:
- Home screen is displayed
Validation Rules:
- Login success event is present in logs
Required Tools:
- Robot Framework
- Appium
""",
        },
    )

    assert response.status_code == 200
    message = response.json()["message"]
    assert message["intent"] == "ticket_intake"
    assert message["metadata"]["assessment"]["automatable"] is True
    assert message["actions"][0]["kind"] == "start_workflow"
    ticket = get_mock_ticket_record("INTAKE-PASTE-001")
    assert ticket is not None
    assert ticket.status == "ready"
    assert "Appium" in ticket.required_tools


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


def test_chat_sessions_can_be_listed_and_pending_actions_cancelled() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
    )
    assert created.status_code == 201
    session_id = created.json()["session"]["session_id"]

    planned = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Analyze DEMO-TELCO-IMS-001",
        },
    )
    assert planned.status_code == 200
    action = planned.json()["message"]["actions"][0]

    listed = client.get("/api/v1/chat/sessions", params={"limit": 10})
    assert listed.status_code == 200
    assert any(
        session["session_id"] == session_id for session in listed.json()["sessions"]
    )

    cancelled = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{action['action_id']}/cancel",
        json={"actor": "chat-tester"},
    )
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["action"]["status"] == "cancelled"
    assert "cancelled" in body["message"]["content"].lower()

    blocked_confirm = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )
    assert blocked_confirm.status_code == 409


def test_chat_validation_and_report_answers_match_current_context_schema() -> None:
    from backend.graph.state import TestContext, TicketData
    from backend.graph.workflow import run_workflow
    from backend.storage.contexts import save_context

    context = run_workflow(
        TestContext(
            created_by="chat-tester",
            ticket=TicketData(
                id="CHAT-SCHEMA-001",
                title="Chat schema compatibility",
                description="Validate chat answers against the current workflow schema.",
                acceptance_criteria=["Chat reports validation and report data."],
                priority="medium",
                labels=["chat", "schema"],
            ),
        )
    )
    save_context(context)

    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={
            "created_by": "chat-tester",
            "context_id": context.context_id,
            "ticket_id": "CHAT-SCHEMA-001",
        },
    )
    assert created.status_code == 201
    session_id = created.json()["session"]["session_id"]

    validation = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Explain validation results",
            "context_id": context.context_id,
        },
    )
    assert validation.status_code == 200
    validation_message = validation.json()["message"]
    assert validation_message["intent"] == "validation_question"
    assert "Total artifacts" in validation_message["content"]
    assert "Quality score" in validation_message["content"]

    report = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Generate a PM summary",
            "context_id": context.context_id,
        },
    )
    assert report.status_code == 200
    report_message = report.json()["message"]
    assert report_message["intent"] == "report_request"
    assert "Summary" in report_message["content"]


def test_chat_action_history_endpoint_tracks_terminal_statuses() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
    )
    session_id = created.json()["session"]["session_id"]

    planned = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Analyze DEMO-TELCO-IMS-001"},
    )
    action = planned.json()["message"]["actions"][0]
    confirmed = client.post(
        f"/api/v1/chat/sessions/{session_id}/actions/{action['action_id']}/confirm",
        json={"actor": "chat-tester"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["session"]["pending_actions"] == []

    history = client.get(f"/api/v1/chat/sessions/{session_id}/actions")
    assert history.status_code == 200
    actions = history.json()["actions"]
    assert len(actions) == 1
    assert actions[0]["action_id"] == action["action_id"]
    assert actions[0]["status"] == "completed"

    answer = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Show action history"},
    )
    assert answer.status_code == 200
    message = answer.json()["message"]
    assert message["intent"] == "action_history"
    assert "Completed: 1" in message["content"]


def test_chat_session_list_can_be_filtered_by_ticket_and_query() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={
            "created_by": "chat-tester",
            "ticket_id": "DEMO-TELCO-IMS-001",
            "title": "IMS demo chat",
        },
    )
    session_id = created.json()["session"]["session_id"]

    by_ticket = client.get(
        "/api/v1/chat/sessions",
        params={"ticket_id": "DEMO-TELCO-IMS-001", "limit": 20},
    )
    assert by_ticket.status_code == 200
    assert any(session["session_id"] == session_id for session in by_ticket.json()["sessions"])

    by_query = client.get(
        "/api/v1/chat/sessions",
        params={"query": "IMS demo", "limit": 20},
    )
    assert by_query.status_code == 200
    assert any(session["session_id"] == session_id for session in by_query.json()["sessions"])


def test_chat_multilingual_deterministic_intents_are_supported() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
    )
    session_id = created.json()["session"]["session_id"]

    french_status = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Où en sommes nous dans le workflow ?"},
    )
    assert french_status.status_code == 200
    assert french_status.json()["message"]["intent"] == "workflow_status"
    assert french_status.json()["message"]["metadata"]["detected_language"] == "fr"

    spanish_report = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Genera un resumen PM"},
    )
    assert spanish_report.status_code == 200
    assert spanish_report.json()["message"]["intent"] == "report_request"

    german_keywords = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "Welche Robot Schlusselworter sind verfugbar?"},
    )
    assert german_keywords.status_code == 200
    assert german_keywords.json()["message"]["intent"] == "artifact_question"
    assert "Robot keyword registry" in german_keywords.json()["message"]["content"]


def test_chat_execution_request_does_not_plan_action_before_approval() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
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

    execution_request = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Run the tests",
            "context_id": context_id,
        },
    )
    assert execution_request.status_code == 200
    message = execution_request.json()["message"]
    assert message["intent"] == "execution_request"
    assert message["actions"] == []
    assert "must be approved first" in message["content"]


def test_chat_read_only_intents_do_not_create_pending_actions() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
    )
    session_id = created.json()["session"]["session_id"]

    for text in [
        "What is mocked and what is real?",
        "Explain Robot keywords",
        "Show action history",
        "Explain safe corpus grounding",
    ]:
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"actor": "chat-tester", "message": text},
        )
        assert response.status_code == 200
        assert response.json()["message"]["actions"] == []
        assert response.json()["session"]["pending_actions"] == []
