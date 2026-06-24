from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app
from backend.graph.state import StageReviewBlock, ValidationSummary, utc_now
from backend.security import Capability, Role
from backend.security.rbac import ROLE_CAPABILITIES
from backend.storage.contexts import load_context, save_context


def _session_payload(*, mode: str) -> dict[str, object]:
    ticket_id = f"CONTROL-{uuid4().hex[:8]}"
    return {
        "created_by": "workflow-operator",
        "mode": mode,
        "ticket": {
            "id": ticket_id,
            "title": "Controlled Workflow Session",
            "description": (
                "As a QA lead, I want to inspect and approve each workflow stage."
            ),
            "acceptance_criteria": [
                "Stages can pause and resume",
                "Operational events are pollable",
            ],
            "priority": "high",
            "labels": ["workflow", "approval"],
        },
    }


def test_step_by_step_session_runs_one_stage_and_exposes_timeline() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="step_by_step"),
    )

    assert created.status_code == 201
    context = created.json()["context"]
    context_id = context["context_id"]
    assert context["workflow_control"]["state"] == "initialized"
    assert context["workflow_control"]["next_stage"] == "ticket"

    first = client.post(
        f"/api/v1/workflows/{context_id}/next",
        json={"actor": "workflow-operator"},
    )

    assert first.status_code == 200
    first_context = first.json()["context"]
    assert first_context["workflow_control"]["state"] == "paused"
    assert first_context["workflow_control"]["completed_stages"] == ["ticket"]
    assert first_context["workflow_control"]["next_stage"] == "requirements"
    assert first_context["ticket"]["id"].startswith("CONTROL-")

    second = client.post(
        f"/api/v1/workflows/{context_id}/next",
        json={"actor": "workflow-operator"},
    )

    assert second.status_code == 200
    second_context = second.json()["context"]
    assert second_context["workflow_control"]["state"] == "paused"
    assert second_context["workflow_control"]["completed_stages"] == [
        "ticket",
        "requirements",
    ]
    assert second_context["requirement_analysis"] is not None

    timeline = client.get(f"/api/v1/workflows/{context_id}/timeline")

    assert timeline.status_code == 200
    events = timeline.json()["events"]
    sequences = [event["sequence"] for event in events]
    assert sequences == sorted(sequences)
    assert events[0]["kind"] == "session"
    assert any(
        event["stage"] == "requirements" and event["status"] == "completed"
        for event in events
    )
    cursor = timeline.json()["next_sequence"]
    empty_poll = client.get(
        f"/api/v1/workflows/{context_id}/timeline",
        params={"after_sequence": cursor},
    )
    assert empty_poll.status_code == 200
    assert empty_poll.json() == {"events": [], "next_sequence": cursor}

    message = client.post(
        f"/api/v1/workflows/{context_id}/timeline/messages",
        json={
            "actor": "workflow-operator",
            "message": "Focus the next stage on authentication edge cases.",
        },
    )
    assert message.status_code == 201
    assert message.json()["event"]["kind"] == "message"
    assert message.json()["event"]["metadata"]["role"] == "user"

    next_poll = client.get(
        f"/api/v1/workflows/{context_id}/timeline",
        params={"after_sequence": cursor},
    )
    assert [event["kind"] for event in next_poll.json()["events"]] == ["message"]


def test_approval_required_session_waits_for_review_and_regenerates() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="approval_required"),
    )
    context_id = created.json()["context"]["context_id"]

    requirements = client.post(
        f"/api/v1/workflows/{context_id}/resume",
        json={"actor": "workflow-operator"},
    )

    assert requirements.status_code == 200
    context = requirements.json()["context"]
    assert context["workflow_control"]["state"] == "waiting_review"
    assert context["workflow_control"]["next_stage"] == "coverage"
    assert context["workflow_control"]["stage_reviews"]["requirements"]["status"] == "pending"

    wrong_stage = client.post(
        f"/api/v1/workflows/{context_id}/stages/ticket/review",
        json={
            "decision": "approve",
            "reviewed_by": "qa-lead",
        },
    )
    assert wrong_stage.status_code == 409

    blocked_resume = client.post(
        f"/api/v1/workflows/{context_id}/resume",
        json={"actor": "workflow-operator"},
    )
    assert blocked_resume.status_code == 409

    approved = client.post(
        f"/api/v1/workflows/{context_id}/stages/requirements/review",
        json={
            "decision": "approve",
            "reviewed_by": "qa-lead",
            "comment": "Requirement extraction is ready.",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["context"]["workflow_control"]["state"] == "paused"

    coverage = client.post(
        f"/api/v1/workflows/{context_id}/resume",
        json={"actor": "workflow-operator"},
    )
    assert coverage.status_code == 200
    assert coverage.json()["context"]["workflow_control"]["stage_revisions"]["coverage"] == 1

    regenerated = client.post(
        f"/api/v1/workflows/{context_id}/stages/coverage/regenerate",
        json={
            "actor": "qa-lead",
            "comment": "Add more explicit authorization and rollback risk coverage.",
        },
    )

    assert regenerated.status_code == 200
    context = regenerated.json()["context"]
    assert context["workflow_control"]["state"] == "waiting_review"
    assert context["workflow_control"]["stage_revisions"]["coverage"] == 2
    assert context["workflow_control"]["stage_reviews"]["coverage"]["status"] == "pending"
    assert context["coverage_plan"] is not None
    assert context["review_feedback"][-1]["comment"].startswith(
        "Add more explicit authorization"
    )
    assert context["review_feedback"][-1]["stage"] == "coverage"
    assert context["review_feedback"][-1]["status"] == "applied"
    assert any(
        item.startswith("Reviewer direction applied:")
        for item in context["coverage_plan"]["risk_rationale"]
    )


def test_autonomous_controlled_session_completes_all_stages() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="autonomous"),
    )
    context_id = created.json()["context"]["context_id"]

    response = client.post(
        f"/api/v1/workflows/{context_id}/resume",
        json={"actor": "workflow-operator"},
    )

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["workflow_control"]["state"] == "completed"
    assert context["workflow_control"]["next_stage"] is None
    assert context["workflow_control"]["completed_stages"] == [
        "ticket",
        "requirements",
        "coverage",
        "tests",
        "automation",
        "validation",
        "approval",
        "report",
    ]
    assert context["approval"]["status"] == "pending_review"
    assert context["reports"] is not None


def test_approval_required_session_completes_after_final_stage_review() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="approval_required"),
    )
    context_id = created.json()["context"]["context_id"]

    while True:
        resumed = client.post(
            f"/api/v1/workflows/{context_id}/resume",
            json={"actor": "workflow-operator"},
        )
        assert resumed.status_code == 200
        context = resumed.json()["context"]
        pending = [
            stage
            for stage, review in context["workflow_control"]["stage_reviews"].items()
            if review["status"] == "pending"
        ]
        assert len(pending) == 1

        reviewed = client.post(
            f"/api/v1/workflows/{context_id}/stages/{pending[0]}/review",
            json={
                "decision": "approve",
                "reviewed_by": "qa-lead",
            },
        )
        assert reviewed.status_code == 200
        context = reviewed.json()["context"]
        if context["workflow_control"]["state"] == "completed":
            break

    assert pending == ["report"]
    assert context["workflow_control"]["next_stage"] is None
    assert context["workflow_control"]["completed_stages"][-1] == "report"
    assert context["workflow_control"]["stage_reviews"]["report"]["status"] == "approved"


def test_pause_is_persisted_at_stage_boundaries() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="autonomous"),
    )
    context_id = created.json()["context"]["context_id"]

    paused = client.post(
        f"/api/v1/workflows/{context_id}/pause",
        json={"actor": "workflow-operator"},
    )

    assert paused.status_code == 200
    control = paused.json()["context"]["workflow_control"]
    assert control["state"] == "paused"
    assert control["pause_requested"] is True
    assert control["next_stage"] == "ticket"


def test_failed_validation_stage_cannot_be_approved() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json=_session_payload(mode="approval_required"),
    )
    context_id = created.json()["context"]["context_id"]
    context = load_context(context_id)
    assert context is not None
    context.workflow_control.state = "waiting_review"
    context.workflow_control.completed_stages = [
        "ticket",
        "requirements",
        "coverage",
        "tests",
        "automation",
        "validation",
    ]
    context.workflow_control.next_stage = "approval"
    context.workflow_control.stage_reviews["validation"] = StageReviewBlock(
        stage="validation",
        status="pending",
        requested_at=utc_now(),
        requested_by="workflow-operator",
    )
    context.validation_summary = ValidationSummary(
        status="failed",
        total_artifacts=1,
        failed_artifacts=1,
        risk_areas=["One automation artifact failed validation."],
    )
    save_context(context)

    response = client.post(
        f"/api/v1/workflows/{context_id}/stages/validation/review",
        json={
            "decision": "approve",
            "reviewed_by": "qa-lead",
        },
    )

    assert response.status_code == 409
    assert "Failed validation cannot be approved" in response.json()["detail"]


def test_robot_artifact_edits_are_versioned_and_require_revalidation() -> None:
    client = TestClient(app)
    ticket_id = f"ARTIFACT-{uuid4().hex[:8]}"
    start = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "artifact-editor",
            "ticket": {
                "id": ticket_id,
                "title": "Editable Robot Artifact",
                "description": "Allow safe manual review edits.",
                "acceptance_criteria": ["Artifact revisions are retained"],
                "priority": "medium",
                "labels": ["artifact", "revision"],
            },
        },
    )
    assert start.status_code == 202
    context = start.json()["context"]
    context_id = context["context_id"]
    robot_path = Path(context["automation"]["TC001"]["robot_file"])
    original = robot_path.read_text(encoding="utf-8")
    edited = f"{original}\n# Manual reviewer note\n"

    update = client.put(
        f"/api/v1/workflows/{context_id}/artifacts/TC001",
        json={
            "actor": "artifact-editor",
            "content": edited,
            "comment": "Clarified the generated artifact.",
        },
    )

    assert update.status_code == 200
    body = update.json()
    assert body["revision"]["version"] == 2
    assert body["revision"]["source"] == "manual"
    assert body["context"]["workflow_control"]["state"] == "paused"
    assert body["context"]["workflow_control"]["next_stage"] == "validation"
    assert (
        body["context"]["automation"]["TC001"]["validation"]["dry_run_passed"]
        is None
    )
    assert robot_path.read_text(encoding="utf-8") == edited

    history = client.get(
        f"/api/v1/workflows/{context_id}/artifacts/TC001/revisions"
    )

    assert history.status_code == 200
    revisions = history.json()["revisions"]
    assert [item["version"] for item in revisions] == [1, 2]
    assert revisions[0]["source"] == "generated"
    assert revisions[0]["content"] == original
    assert revisions[1]["content"] == edited

    validation = client.post(
        f"/api/v1/workflows/{context_id}/next",
        json={"actor": "artifact-editor"},
    )
    assert validation.status_code == 200
    validated_context = validation.json()["context"]
    assert validated_context["workflow_control"]["next_stage"] == "approval"
    assert (
        validated_context["automation"]["TC001"]["validation"]["dry_run_passed"]
        is True
    )


def test_artifact_edit_capability_is_available_to_engineers_and_leads() -> None:
    assert Capability.EDIT_ARTIFACTS in ROLE_CAPABILITIES[Role.QA_ENGINEER]
    assert Capability.EDIT_ARTIFACTS in ROLE_CAPABILITIES[Role.QA_LEAD]
    assert Capability.EDIT_ARTIFACTS not in ROLE_CAPABILITIES[Role.VIEWER]
