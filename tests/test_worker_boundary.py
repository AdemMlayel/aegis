from __future__ import annotations

from uuid import uuid4

from starlette.testclient import TestClient

from backend.main import app
from backend.workers import dispatch_execution_run, execution_worker_backend_registry


def test_execution_worker_registry_exposes_local_and_celery_backends() -> None:
    specs = {spec.name: spec for spec in execution_worker_backend_registry.list_specs()}

    assert specs["local"].durable is False
    assert specs["local"].requires_broker is False
    assert specs["celery"].durable is True
    assert specs["celery"].requires_broker is True


def test_execution_worker_dispatch_uses_local_fallback_for_unknown_backend() -> None:
    enqueued: list[str] = []

    result = dispatch_execution_run(
        "exec-worker-test",
        backend_name="missing-backend",
        local_enqueue=enqueued.append,
    )

    assert enqueued == ["exec-worker-test"]
    assert result.backend == "local"
    assert result.fallback_used is True
    assert result.durable is False


def test_execute_endpoint_returns_worker_dispatch_metadata() -> None:
    client = TestClient(app)
    ticket_id = f"WORKER-{uuid4().hex[:8]}"

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": ticket_id,
                "title": "Durable Worker Boundary",
                "description": "As a QA lead, I want execution dispatched through a worker boundary.",
                "acceptance_criteria": ["Execution dispatch metadata is exposed"],
                "priority": "medium",
                "labels": ["worker", "execution"],
            },
        },
    )
    assert start_response.status_code == 202

    execute_response = client.post(
        "/api/v1/execute",
        json={
            "suite": ticket_id,
            "adapter": "mock",
            "env": "staging",
            "actor": "ci_runner",
        },
    )

    assert execute_response.status_code == 202
    body = execute_response.json()
    assert body["worker_backend"] == "local"
    assert body["worker_fallback_used"] is False
    assert "local" in body["worker_message"].lower()
