from __future__ import annotations

import asyncio
from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel

from backend.graph.execution import run_mock_execution
from backend.graph.state import ExecutionBlock, TestContext, utc_now
from backend.storage.audit import append_audit_event
from backend.storage.contexts import list_contexts, load_context, save_context
from backend.storage.execution_runs import (
    ExecutionRunRecord,
    ExecutionRunRequest,
    ExecutionRunStatus,
    create_execution_run,
    list_execution_runs,
    load_execution_run,
    save_execution_run,
)


router = APIRouter(tags=["executions"])
FINAL_EXECUTION_STATUSES = {"passed", "failed", "skipped", "blocked"}


class ExecuteRunResponse(BaseModel):
    run_id: str
    context_id: str
    status: ExecutionRunStatus
    status_url: str
    summary_url: str
    junit_url: str
    report_url: str
    websocket_url: str | None = None


class ExecutionRunDetailResponse(BaseModel):
    run: ExecutionRunRecord
    status_url: str
    summary_url: str
    junit_url: str
    report_url: str
    websocket_url: str | None = None


class ExecutionRunListResponse(BaseModel):
    runs: list[ExecutionRunRecord]


def _run_urls(run_id: str) -> dict[str, str]:
    return {
        "status_url": f"/api/v1/results/{run_id}",
        "summary_url": f"/api/v1/results/{run_id}/summary.json",
        "junit_url": f"/api/v1/results/{run_id}/junit.xml",
        "report_url": f"/api/v1/results/{run_id}/report.html",
        "websocket_url": f"/api/v1/ws/exec/{run_id}",
    }


def _load_context_for_suite(suite: str) -> TestContext | None:
    context = load_context(suite)
    if context:
        return context

    needle = suite.casefold()
    for candidate in list_contexts():
        if candidate.ticket and candidate.ticket.id.casefold() == needle:
            return candidate
    return None


@router.post(
    "/execute",
    response_model=ExecuteRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def execute_suite(
    request: ExecutionRunRequest,
    background_tasks: BackgroundTasks,
) -> ExecuteRunResponse:
    context = _load_context_for_suite(request.suite)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workflow context was found for the requested suite",
        )

    record = create_execution_run(
        context_id=context.context_id,
        request=request,
        status="queued",
    )
    background_tasks.add_task(process_execution_run, record.run_id)

    return ExecuteRunResponse(
        run_id=record.run_id,
        context_id=context.context_id,
        status=record.status,
        **_run_urls(record.run_id),
    )


def process_execution_run(run_id: str) -> None:
    record = load_execution_run(run_id)
    if record is None:
        return

    record.status = "running"
    record.updated_at = utc_now()
    save_execution_run(record)

    context = load_context(record.context_id)
    if context is None:
        record.status = "blocked"
        record.updated_at = utc_now()
        save_execution_run(record)
        append_audit_event(
            actor=record.request.actor,
            event_type="execution_completed",
            summary="CI execution blocked.",
            metadata={
                "run_id": record.run_id,
                "context_id": record.context_id,
                "suite": record.request.suite,
                "env": record.request.env,
                "branch": record.request.branch,
                "tags": record.request.tags,
                "execution_status": record.status,
                "error": "Workflow context was not found",
            },
        )
        return

    try:
        context = run_mock_execution(context, actor=record.request.actor)
    except ValueError as exc:
        record.status = "blocked"
        record.updated_at = utc_now()
        save_execution_run(record)
        append_audit_event(
            actor=record.request.actor,
            event_type="execution_completed",
            summary="CI execution blocked.",
            metadata={
                "run_id": record.run_id,
                "context_id": context.context_id,
                "ticket_id": context.ticket.id if context.ticket else None,
                "suite": record.request.suite,
                "env": record.request.env,
                "branch": record.request.branch,
                "tags": record.request.tags,
                "execution_status": record.status,
                "error": str(exc),
            },
        )
        return

    execution = context.execution
    if execution is None:
        record.status = "blocked"
    else:
        record.status = execution.status
        record.execution = execution
        record.junit_xml = render_junit_xml(record.run_id, execution)
    record.updated_at = utc_now()
    save_execution_run(record)

    append_audit_event(
        actor=record.request.actor,
        event_type="execution_completed",
        summary=f"CI execution {record.status}.",
        metadata={
            "run_id": record.run_id,
            "context_id": context.context_id,
            "ticket_id": context.ticket.id if context.ticket else None,
            "suite": record.request.suite,
            "env": record.request.env,
            "branch": record.request.branch,
            "tags": record.request.tags,
            "execution_status": record.status,
            "passed": execution.summary.passed if execution else 0,
            "failed": execution.summary.failed if execution else 0,
            "skipped": execution.summary.skipped if execution else 0,
        },
    )
    save_context(context)


@router.get("/results", response_model=ExecutionRunListResponse)
def list_results(
    context_id: str | None = None,
    run_status: ExecutionRunStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> ExecutionRunListResponse:
    return ExecutionRunListResponse(
        runs=list_execution_runs(
            context_id=context_id,
            status=run_status,
            limit=limit,
        )
    )


@router.get("/results/{run_id}", response_model=ExecutionRunDetailResponse)
def get_result(run_id: str) -> ExecutionRunDetailResponse:
    record = _load_run_or_404(run_id)
    return ExecutionRunDetailResponse(run=record, **_run_urls(run_id))


@router.get("/results/{run_id}/summary.json", response_model=ExecutionRunDetailResponse)
def get_result_summary(run_id: str) -> ExecutionRunDetailResponse:
    record = _load_run_or_404(run_id)
    return ExecutionRunDetailResponse(run=record, **_run_urls(run_id))


@router.get("/results/{run_id}/junit.xml")
def get_result_junit(run_id: str) -> Response:
    record = _load_run_or_404(run_id)
    if record.junit_xml is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JUnit artifact is not available for this run",
        )
    return Response(content=record.junit_xml, media_type="application/xml")


@router.get("/results/{run_id}/report.html")
def get_result_report(run_id: str) -> Response:
    record = _load_run_or_404(run_id)
    if record.execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HTML report is not available for this run",
        )
    return Response(
        content=render_html_report(record),
        media_type="text/html",
    )


@router.websocket("/ws/exec/{run_id}")
async def stream_execution_run(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    last_status: str | None = None
    try:
        for _ in range(120):
            record = load_execution_run(run_id)
            if record is None:
                await websocket.send_json(
                    {
                        "run_id": run_id,
                        "status": "not_found",
                        "error": "Execution run was not found",
                    }
                )
                await websocket.close(code=1008)
                return

            if record.status != last_status or record.status in FINAL_EXECUTION_STATUSES:
                await websocket.send_json(_run_stream_payload(record))
                last_status = record.status

            if record.status in FINAL_EXECUTION_STATUSES:
                await websocket.close(code=1000)
                return

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return

    await websocket.close(code=1000)


def _load_run_or_404(run_id: str) -> ExecutionRunRecord:
    record = load_execution_run(run_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution run was not found",
        )
    return record


def _run_stream_payload(record: ExecutionRunRecord) -> dict[str, object]:
    return {
        "run": record.model_dump(mode="json"),
        **_run_urls(record.run_id),
    }


def render_junit_xml(run_id: str, execution: ExecutionBlock) -> str:
    summary = execution.summary
    testcases = "\n".join(
        _render_junit_testcase(result) for result in execution.results
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="AegisQA {xml_escape(run_id)}" '
        f'tests="{summary.total}" failures="{summary.failed}" '
        f'skipped="{summary.skipped}" time="{summary.duration_ms / 1000:.3f}">\n'
        f"{testcases}\n"
        "</testsuite>\n"
    )


def _render_junit_testcase(result) -> str:
    name = xml_escape(result.title)
    classname = xml_escape(result.test_case_id)
    time_seconds = result.duration_ms / 1000
    if result.status == "failed":
        logs = xml_escape("\n".join(result.logs))
        message = xml_escape(result.message)
        return (
            f'  <testcase classname="{classname}" name="{name}" '
            f'time="{time_seconds:.3f}">\n'
            f'    <failure message="{message}">{logs}</failure>\n'
            "  </testcase>"
        )
    if result.status == "skipped":
        message = xml_escape(result.message)
        return (
            f'  <testcase classname="{classname}" name="{name}" '
            f'time="{time_seconds:.3f}">\n'
            f'    <skipped message="{message}" />\n'
            "  </testcase>"
        )
    return (
        f'  <testcase classname="{classname}" name="{name}" '
        f'time="{time_seconds:.3f}" />'
    )


def render_html_report(record: ExecutionRunRecord) -> str:
    execution = record.execution
    if execution is None:
        return ""

    rows = "\n".join(
        (
            "<tr>"
            f"<td>{html_escape(result.test_case_id)}</td>"
            f"<td>{html_escape(result.title)}</td>"
            f"<td>{html_escape(result.status)}</td>"
            f"<td>{result.duration_ms}</td>"
            f"<td>{html_escape(result.message)}</td>"
            "</tr>"
        )
        for result in execution.results
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AegisQA Execution {html_escape(record.run_id)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; text-align: left; }}
    th {{ background: #f0f4f8; }}
  </style>
</head>
<body>
  <h1>AegisQA Execution {html_escape(record.run_id)}</h1>
  <p>Status: {html_escape(record.status)}</p>
  <p>Suite: {html_escape(record.request.suite)} | Env: {html_escape(record.request.env)}</p>
  <table>
    <thead>
      <tr><th>Case</th><th>Title</th><th>Status</th><th>Duration ms</th><th>Message</th></tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
"""
