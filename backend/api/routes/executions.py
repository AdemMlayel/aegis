from __future__ import annotations

import asyncio
from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
    Depends,
)
from pydantic import BaseModel

from backend.execution import execution_adapter_registry
from backend.graph.state import ExecutionBlock, TestContext, utc_now
from backend.graph.workflow import run_after_execution_analysis
from backend.storage.audit import append_audit_event
from backend.storage.contexts import list_contexts, load_context, save_context
from backend.storage.execution_events import (
    ExecutionEvent,
    append_execution_event,
    list_execution_events,
)
from backend.security import Capability, Principal, require_capability
from backend.storage.execution_runs import (
    ExecutionRunRecord,
    ExecutionRunRequest,
    ExecutionRunStatus,
    create_execution_run,
    list_execution_runs,
    load_execution_run,
    save_execution_run,
)
from backend.workers import dispatch_execution_run


router = APIRouter(tags=["executions"])
FINAL_EXECUTION_STATUSES = {"passed", "failed", "skipped", "blocked"}


class ExecuteRunResponse(BaseModel):
    run_id: str
    context_id: str
    status: ExecutionRunStatus
    worker_backend: str
    worker_durable: bool
    worker_task_id: str | None = None
    worker_fallback_used: bool = False
    worker_message: str
    status_url: str
    summary_url: str
    junit_url: str
    report_url: str
    logs_url: str
    websocket_url: str | None = None


class ExecutionRunDetailResponse(BaseModel):
    run: ExecutionRunRecord
    status_url: str
    summary_url: str
    junit_url: str
    report_url: str
    logs_url: str
    websocket_url: str | None = None


class ExecutionRunListResponse(BaseModel):
    runs: list[ExecutionRunRecord]


class ExecutionEventListResponse(BaseModel):
    events: list[ExecutionEvent]


def _run_urls(run_id: str) -> dict[str, str]:
    return {
        "status_url": f"/api/v1/results/{run_id}",
        "summary_url": f"/api/v1/results/{run_id}/summary.json",
        "junit_url": f"/api/v1/results/{run_id}/junit.xml",
        "report_url": f"/api/v1/results/{run_id}/report.html",
        "logs_url": f"/api/v1/results/{run_id}/logs",
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
    principal: Annotated[Principal, Depends(require_capability(Capability.EXECUTE_WORKFLOW))],
) -> ExecuteRunResponse:
    if not execution_adapter_registry.has(request.adapter):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execution adapter '{request.adapter}' is not registered",
        )

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
    append_execution_event(
        run_id=record.run_id,
        context_id=context.context_id,
        phase="queued",
        status=record.status,
        message="Execution run was queued.",
        metadata={
            "suite": request.suite,
            "adapter": request.adapter,
            "env": request.env,
            "branch": request.branch,
            "tags": request.tags,
        },
    )
    dispatch = dispatch_execution_run(
        record.run_id,
        local_enqueue=lambda run_id: background_tasks.add_task(process_execution_run, run_id),
    )

    return ExecuteRunResponse(
        run_id=record.run_id,
        context_id=context.context_id,
        status=record.status,
        worker_backend=dispatch.backend,
        worker_durable=dispatch.durable,
        worker_task_id=dispatch.task_id,
        worker_fallback_used=dispatch.fallback_used,
        worker_message=dispatch.message,
        **_run_urls(record.run_id),
    )


def process_execution_run(run_id: str) -> None:
    record = load_execution_run(run_id)
    if record is None:
        return

    record.status = "running"
    record.updated_at = utc_now()
    save_execution_run(record)
    append_execution_event(
        run_id=record.run_id,
        context_id=record.context_id,
        phase="running",
        status=record.status,
        message="Execution worker started.",
        metadata={
            "suite": record.request.suite,
            "adapter": record.request.adapter,
            "env": record.request.env,
            "branch": record.request.branch,
            "tags": record.request.tags,
        },
    )

    context = load_context(record.context_id)
    if context is None:
        record.status = "blocked"
        record.updated_at = utc_now()
        save_execution_run(record)
        append_execution_event(
            run_id=record.run_id,
            context_id=record.context_id,
            phase="blocked",
            level="error",
            status=record.status,
            message="Workflow context was not found.",
        )
        append_audit_event(
            actor=record.request.actor,
            event_type="execution_completed",
            summary="CI execution blocked.",
            metadata={
                "run_id": record.run_id,
                "context_id": record.context_id,
                "suite": record.request.suite,
                "adapter": record.request.adapter,
                "env": record.request.env,
                "branch": record.request.branch,
                "tags": record.request.tags,
                "execution_status": record.status,
                "error": "Workflow context was not found",
            },
        )
        return

    try:
        adapter = execution_adapter_registry.create(record.request.adapter)
        context = adapter.execute(
            context,
            actor=record.request.actor,
            env=record.request.env,
            branch=record.request.branch,
            tags=record.request.tags,
        )
        context = run_after_execution_analysis(context)
    except ValueError as exc:
        record.status = "blocked"
        record.updated_at = utc_now()
        save_execution_run(record)
        append_execution_event(
            run_id=record.run_id,
            context_id=context.context_id,
            phase="blocked",
            level="error",
            status=record.status,
            message=str(exc),
            metadata={
                "adapter": record.request.adapter,
                "ticket_id": context.ticket.id if context.ticket else None,
            },
        )
        append_audit_event(
            actor=record.request.actor,
            event_type="execution_completed",
            summary="CI execution blocked.",
            metadata={
                "run_id": record.run_id,
                "context_id": context.context_id,
                "ticket_id": context.ticket.id if context.ticket else None,
                "suite": record.request.suite,
                "adapter": record.request.adapter,
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
        for result in execution.results:
            append_execution_event(
                run_id=record.run_id,
                context_id=context.context_id,
                phase="case_started",
                status="running",
                test_case_id=result.test_case_id,
                message=f"Started {result.title}.",
                metadata={"robot_file": result.robot_file},
            )
            append_execution_event(
                run_id=record.run_id,
                context_id=context.context_id,
                phase="case_finished",
                level="error" if result.status == "failed" else "info",
                status=result.status,
                test_case_id=result.test_case_id,
                message=result.message,
                metadata={
                    "title": result.title,
                    "duration_ms": result.duration_ms,
                    "robot_file": result.robot_file,
                    "logs": result.logs,
                },
            )
        record.status = execution.status
        record.execution = execution
        record.junit_xml = render_junit_xml(record.run_id, execution)
    record.updated_at = utc_now()
    save_execution_run(record)
    if record.junit_xml:
        append_execution_event(
            run_id=record.run_id,
            context_id=context.context_id,
            phase="artifact",
            status=record.status,
            message="JUnit and HTML execution artifacts are available.",
            metadata={
                "junit_url": _run_urls(record.run_id)["junit_url"],
                "report_url": _run_urls(record.run_id)["report_url"],
            },
        )
    append_execution_event(
        run_id=record.run_id,
        context_id=context.context_id,
        phase="completed" if record.status != "blocked" else "blocked",
        level="error" if record.status in {"failed", "blocked"} else "info",
        status=record.status,
        message=f"Execution run finished with status {record.status}.",
        metadata={
            "passed": execution.summary.passed if execution else 0,
            "failed": execution.summary.failed if execution else 0,
            "skipped": execution.summary.skipped if execution else 0,
        },
    )

    append_audit_event(
        actor=record.request.actor,
        event_type="execution_completed",
        summary=f"CI execution {record.status}.",
        metadata={
            "run_id": record.run_id,
            "context_id": context.context_id,
            "ticket_id": context.ticket.id if context.ticket else None,
            "suite": record.request.suite,
            "adapter": record.request.adapter,
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
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
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
def get_result(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> ExecutionRunDetailResponse:
    record = _load_run_or_404(run_id)
    return ExecutionRunDetailResponse(run=record, **_run_urls(run_id))


@router.get("/results/{run_id}/summary.json", response_model=ExecutionRunDetailResponse)
def get_result_summary(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> ExecutionRunDetailResponse:
    record = _load_run_or_404(run_id)
    return ExecutionRunDetailResponse(run=record, **_run_urls(run_id))


@router.get("/results/{run_id}/junit.xml")
def get_result_junit(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
) -> Response:
    record = _load_run_or_404(run_id)
    if record.junit_xml is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JUnit artifact is not available for this run",
        )
    return Response(content=record.junit_xml, media_type="application/xml")


@router.get("/results/{run_id}/report.html")
def get_result_report(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
) -> Response:
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


@router.get("/results/{run_id}/logs", response_model=ExecutionEventListResponse)
def get_result_logs(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
    limit: int = Query(default=200, ge=1, le=1000),
) -> ExecutionEventListResponse:
    _load_run_or_404(run_id)
    return ExecutionEventListResponse(
        events=list_execution_events(run_id=run_id, limit=limit)
    )


@router.websocket("/ws/exec/{run_id}")
async def stream_execution_run(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    last_status: str | None = None
    last_event_count = -1
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

            events = list_execution_events(run_id=run_id, limit=200)
            event_count = len(events)
            if (
                record.status != last_status
                or event_count != last_event_count
                or record.status in FINAL_EXECUTION_STATUSES
            ):
                await websocket.send_json(_run_stream_payload(record, events))
                last_status = record.status
                last_event_count = event_count

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


def _run_stream_payload(
    record: ExecutionRunRecord,
    events: list[ExecutionEvent] | None = None,
) -> dict[str, object]:
    return {
        "run": record.model_dump(mode="json"),
        "events": [event.model_dump(mode="json") for event in (events or [])],
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
  <p>Suite: {html_escape(record.request.suite)} | Adapter: {html_escape(record.request.adapter)} | Env: {html_escape(record.request.env)}</p>
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
