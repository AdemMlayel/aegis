from uuid import uuid4

from starlette.testclient import TestClient

from backend.main import app


def test_seeded_mock_tickets_include_database_metadata() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/tickets/demo/DEMO-TELCO-IMS-001")

    assert response.status_code == 200
    ticket = response.json()["ticket"]
    assert ticket["status"] == "ready"
    assert ticket["comments"]
    assert ticket["comments"][0]["author"] == "domain_expert"
    assert {requirement["id"] for requirement in ticket["linked_requirements"]} >= {
        "REQ-DEMO-TELCO-001",
        "REQ-DEMO-TELCO-002",
    }
    assert ticket["technical"]["architecture_summary"]
    assert ticket["required_tools"]


def test_mock_ticket_database_supports_crud_filters_and_comments() -> None:
    client = TestClient(app)
    ticket_id = f"MOCK-CRUD-{uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/tickets/mock",
        json={
            "id": ticket_id,
            "title": "Mock CRUD Ticket",
            "description": "As a QA engineer, I want mutable mock tickets.",
            "acceptance_criteria": ["Mock ticket can be created and updated"],
            "priority": "low",
            "labels": ["crud", "mockdb"],
            "assignee": "qa_mock",
            "source": "fake",
            "status": "backlog",
            "linked_requirements": [
                {
                    "id": f"REQ-{ticket_id}-1",
                    "title": "Mock tickets can carry linked requirements",
                    "status": "draft",
                }
            ],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()["ticket"]
    assert created["id"] == ticket_id
    assert created["status"] == "backlog"
    assert created["created_at"]
    assert created["updated_at"]

    duplicate_response = client.post("/api/v1/tickets/mock", json=created)
    assert duplicate_response.status_code == 409

    filtered_response = client.get(
        "/api/v1/tickets/mock",
        params={
            "q": "mutable",
            "status": "backlog",
            "assignee": "qa_mock",
            "label": "crud",
        },
    )
    assert filtered_response.status_code == 200
    assert [ticket["id"] for ticket in filtered_response.json()["tickets"]] == [
        ticket_id
    ]

    update_response = client.patch(
        f"/api/v1/tickets/mock/{ticket_id}",
        json={
            "status": "in_progress",
            "priority": "high",
            "labels": ["crud", "updated"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()["ticket"]
    assert updated["status"] == "in_progress"
    assert updated["priority"] == "high"
    assert updated["labels"] == ["crud", "updated"]

    comment_response = client.post(
        f"/api/v1/tickets/mock/{ticket_id}/comments",
        json={
            "author": "qa_lead",
            "body": "Exercise the local mock database before connector work.",
        },
    )
    assert comment_response.status_code == 200
    commented = comment_response.json()["ticket"]
    assert commented["comments"][-1]["author"] == "qa_lead"
    assert "local mock database" in commented["comments"][-1]["body"]

    start_response = client.post(
        "/api/v1/workflows/start-from-mock-ticket",
        json={"created_by": "pytest", "ticket_id": ticket_id},
    )
    assert start_response.status_code == 202
    assert start_response.json()["context"]["ticket"]["id"] == ticket_id

    delete_response = client.delete(f"/api/v1/tickets/mock/{ticket_id}")
    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/api/v1/tickets/mock/{ticket_id}")
    assert get_deleted_response.status_code == 404
