from uuid import uuid4

from starlette.testclient import TestClient

from backend.main import app


def test_ci_execute_endpoint_persists_results_and_artifacts() -> None:
    client = TestClient(app)
    ticket_id = f"CI-EXEC-{uuid4().hex[:8]}"

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": ticket_id,
                "title": "CI Execution Boundary",
                "description": "As a QA lead, I want CI to run generated automation.",
                "acceptance_criteria": ["Execution results are published"],
                "priority": "high",
                "labels": ["ci", "execution"],
            },
        },
    )
    assert start_response.status_code == 202
    context_id = start_response.json()["context"]["context_id"]

    execute_response = client.post(
        "/api/v1/execute",
        json={
            "suite": ticket_id,
            "branch": "feature/ci-boundary",
            "env": "staging",
            "tags": ["smoke", "generated"],
            "actor": "ci_runner",
        },
    )

    assert execute_response.status_code == 202
    body = execute_response.json()
    run_id = body["run_id"]
    assert body["context_id"] == context_id
    assert body["status"] == "queued"
    assert body["status_url"] == f"/api/v1/results/{run_id}"
    assert body["summary_url"] == f"/api/v1/results/{run_id}/summary.json"
    assert body["junit_url"] == f"/api/v1/results/{run_id}/junit.xml"
    assert body["report_url"] == f"/api/v1/results/{run_id}/report.html"
    assert body["websocket_url"] == f"/api/v1/ws/exec/{run_id}"

    result_response = client.get(body["status_url"])
    assert result_response.status_code == 200
    result_body = result_response.json()
    assert result_body["websocket_url"] == f"/api/v1/ws/exec/{run_id}"
    run = result_body["run"]
    assert run["run_id"] == run_id
    assert run["context_id"] == context_id
    assert run["status"] == "failed"
    assert run["request"] == {
        "suite": ticket_id,
        "branch": "feature/ci-boundary",
        "env": "staging",
        "tags": ["smoke", "generated"],
        "actor": "ci_runner",
    }
    assert run["execution"]["run_by"] == "ci_runner"
    assert run["execution"]["summary"]["total"] == 3
    assert run["execution"]["summary"]["passed"] == 2
    assert run["execution"]["summary"]["failed"] == 1

    summary_response = client.get(body["summary_url"])
    assert summary_response.status_code == 200
    assert summary_response.json()["run"]["run_id"] == run_id

    junit_response = client.get(body["junit_url"])
    assert junit_response.status_code == 200
    assert junit_response.headers["content-type"].startswith("application/xml")
    assert "<testsuite" in junit_response.text
    assert 'failures="1"' in junit_response.text
    assert "<failure" in junit_response.text

    report_response = client.get(body["report_url"])
    assert report_response.status_code == 200
    assert report_response.headers["content-type"].startswith("text/html")
    assert "CI Execution Boundary" in report_response.text

    history_response = client.get(
        f"/api/v1/results?context_id={context_id}&status=failed"
    )
    assert history_response.status_code == 200
    runs = history_response.json()["runs"]
    assert runs[0]["run_id"] == run_id

    saved_context_response = client.get(f"/api/v1/workflows/{context_id}")
    assert saved_context_response.status_code == 200
    saved_context = saved_context_response.json()["context"]
    assert saved_context["execution"]["status"] == "failed"
    assert saved_context["workflow_status"] == "mock_execution_failed"


def test_execution_websocket_streams_run_status() -> None:
    client = TestClient(app)
    ticket_id = f"CI-WS-{uuid4().hex[:8]}"

    start_response = client.post(
        "/api/v1/workflows/start",
        json={
            "created_by": "pytest",
            "ticket": {
                "id": ticket_id,
                "title": "CI Websocket Boundary",
                "description": "As a QA lead, I want live execution status.",
                "acceptance_criteria": ["Execution status is streamed"],
                "priority": "high",
                "labels": ["ci", "websocket"],
            },
        },
    )
    assert start_response.status_code == 202

    execute_response = client.post(
        "/api/v1/execute",
        json={
            "suite": ticket_id,
            "env": "staging",
            "actor": "ci_runner",
        },
    )
    assert execute_response.status_code == 202
    websocket_url = execute_response.json()["websocket_url"]

    with client.websocket_connect(websocket_url) as websocket:
        payload = websocket.receive_json()

    assert payload["run"]["run_id"] == execute_response.json()["run_id"]
    assert payload["run"]["status"] == "failed"
    assert payload["websocket_url"] == websocket_url


def test_ci_execute_endpoint_returns_404_for_unknown_suite() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/execute",
        json={
            "suite": f"UNKNOWN-{uuid4().hex[:8]}",
            "env": "staging",
            "actor": "ci_runner",
        },
    )

    assert response.status_code == 404


def test_result_artifacts_return_404_for_unknown_run() -> None:
    client = TestClient(app)

    response = client.get(f"/api/v1/results/exec-{uuid4()}")

    assert response.status_code == 404
