from __future__ import annotations

import hashlib
import json
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

from fastapi.testclient import TestClient

from backend.main import app
from backend.storage.audit import list_audit_events


def _start_report_ready_workflow(client: TestClient) -> dict[str, object]:
    ticket_id = f"PACKAGE-{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "package-tester",
            "ticket": {
                "id": ticket_id,
                "title": "Exportable QA Package",
                "description": (
                    "As a QA lead, I want a complete downloadable evidence package."
                ),
                "acceptance_criteria": [
                    "Reports are downloadable",
                    "Automation and evidence are included",
                ],
                "priority": "high",
                "labels": ["report", "export"],
            },
        },
    )
    assert response.status_code == 202
    return response.json()["context"]


def test_report_package_manifest_and_markdown_exports() -> None:
    client = TestClient(app)
    context = _start_report_ready_workflow(client)
    context_id = context["context_id"]

    manifest_response = client.get(
        f"/api/v1/workflows/{context_id}/package/manifest"
    )
    technical_response = client.get(
        f"/api/v1/workflows/{context_id}/package/technical.md"
    )
    executive_response = client.get(
        f"/api/v1/workflows/{context_id}/package/executive.md"
    )

    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["context_id"] == context_id
    assert manifest["ticket_id"].startswith("PACKAGE-")
    assert manifest["package_status"] == "draft"
    assert manifest["validation_status"] in {"passed", "warning"}
    assert manifest["quality_score"] is not None
    package_paths = {item["path"] for item in manifest["files"]}
    assert {
        "reports/technical-report.md",
        "reports/executive-summary.md",
        "data/context.json",
        "data/test-cases.json",
        "data/validation-summary.json",
        "data/decision-history.json",
    } <= package_paths
    assert any(
        path.startswith("automation/TC001_") and path.endswith(".robot")
        for path in package_paths
    )
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])

    assert technical_response.status_code == 200
    assert technical_response.headers["content-type"].startswith(
        "text/markdown"
    )
    assert "# Test Automation Report" in technical_response.text
    assert "## Validation" in technical_response.text
    assert "## Decision History" in technical_response.text

    assert executive_response.status_code == 200
    assert executive_response.headers["content-type"].startswith(
        "text/markdown"
    )
    assert "# QA Status" in executive_response.text
    assert "## Quality" in executive_response.text


def test_report_package_zip_contains_manifest_and_verified_files() -> None:
    client = TestClient(app)
    context = _start_report_ready_workflow(client)
    context_id = context["context_id"]

    response = client.get(f"/api/v1/workflows/{context_id}/package.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        manifest = json.loads(archive.read("manifest.json"))
        for item in manifest["files"]:
            assert item["path"] in names
            payload = archive.read(item["path"])
            assert len(payload) == item["size_bytes"]
            assert hashlib.sha256(payload).hexdigest() == item["sha256"]

    events = list_audit_events(context_id=context_id, limit=20)
    assert any(
        event.event_type == "report_package_exported"
        for event in events
    )


def test_report_package_requires_generated_report() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/workflows/sessions",
        json={
            "created_by": "package-tester",
            "mode": "step_by_step",
            "ticket": {
                "id": f"PACKAGE-PENDING-{uuid4().hex[:8]}",
                "title": "Report Not Ready",
                "description": "The workflow has not reached reporting.",
                "acceptance_criteria": ["Package is unavailable before reporting"],
                "priority": "medium",
                "labels": ["report"],
            },
        },
    )
    context_id = created.json()["context"]["context_id"]

    response = client.get(
        f"/api/v1/workflows/{context_id}/package/manifest"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Workflow report has not been generated yet"


def test_report_package_returns_not_found_for_unknown_context() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/workflows/not-a-context/package/manifest"
    )

    assert response.status_code == 404
