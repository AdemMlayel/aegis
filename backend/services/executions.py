from __future__ import annotations

from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape

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
from backend.storage.execution_runs import (
    ExecutionRunRecord,
    ExecutionRunRequest,
    ExecutionRunStatus,
    create_execution_run,
    list_execution_runs,
    load_execution_run,
    save_execution_run,
)


FINAL_EXECUTION_STATUSES = {"passed", "failed", "skipped", "blocked"}


class ExecutionServiceError(Exception):
    """Base exception for execution service failures."""


class ExecutionNotFound(ExecutionServiceError):
    pass


class ExecutionBadRequest(ExecutionServiceError):
    pass


def run_urls(run_id: str) -> dict[str, str]:
    return {
        "status_url": f"/api/v1/results/{run_id}",
        "summary_url": f"/api/v1/results/{run_id}/summary.json",
        "junit_url": f"/api/v1/results/{run_id}/junit.xml",
        "report_url": f"/api/v1/results/{run_id}/report.html",
        "logs_url": f"/api/v1/results/{run_id}/logs",
        "websocket_url": f"/api/v1/ws/exec/{run_id}",
    }


def queue_execution_run(request: ExecutionRunRequest) -> ExecutionRunRecord:
    if not execution_adapter_registry.has(request.adapter):
        raise ExecutionBadRequest(
            f"Execution adapter '{request.adapter}' is not registered"
        )

    context = _load_context_for_suite(request.suite)
    if context is None:
        raise ExecutionNotFound(
            "No workflow context was found for the requested suite"
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
    return record


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
        _block_run_without_context(record)
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
        _block_run_with_error(record=record, context=context, error=str(exc))
        return

    execution = context.execution
    if execution is None:
        record.status = "blocked"
    else:
        _append_case_events(record=record, context=context, execution=execution)
        record.status = execution.status
        record.execution = execution
        record.junit_xml = render_junit_xml(record.run_id, execution)
    record.updated_at = utc_now()
    save_execution_run(record)
    _append_artifact_event(record, context)
    _append_completion_event(record=record, context=context, execution=execution)
    _append_completion_audit(record=record, context=context, execution=execution)
    save_context(context)


def list_results(
    *,
    context_id: str | None = None,
    status: ExecutionRunStatus | None = None,
    limit: int = 50,
) -> list[ExecutionRunRecord]:
    return list_execution_runs(context_id=context_id, status=status, limit=limit)


def get_result(run_id: str) -> ExecutionRunRecord:
    record = load_execution_run(run_id)
    if record is None:
        raise ExecutionNotFound("Execution run was not found")
    return record


def get_result_logs(*, run_id: str, limit: int = 200) -> list[ExecutionEvent]:
    get_result(run_id)
    return list_execution_events(run_id=run_id, limit=limit)


def run_stream_payload(
    record: ExecutionRunRecord,
    events: list[ExecutionEvent] | None = None,
) -> dict[str, object]:
    return {
        "run": record.model_dump(mode="json"),
        "events": [event.model_dump(mode="json") for event in (events or [])],
        **run_urls(record.run_id),
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


def _load_context_for_suite(suite: str) -> TestContext | None:
    context = load_context(suite)
    if context:
        return context

    needle = suite.casefold()
    for candidate in list_contexts():
        if candidate.ticket and candidate.ticket.id.casefold() == needle:
            return candidate
    return None


def _block_run_without_context(record: ExecutionRunRecord) -> None:
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


def _block_run_with_error(
    *,
    record: ExecutionRunRecord,
    context: TestContext,
    error: str,
) -> None:
    record.status = "blocked"
    record.updated_at = utc_now()
    save_execution_run(record)
    append_execution_event(
        run_id=record.run_id,
        context_id=context.context_id,
        phase="blocked",
        level="error",
        status=record.status,
        message=error,
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
            "error": error,
        },
    )


def _append_case_events(
    *,
    record: ExecutionRunRecord,
    context: TestContext,
    execution: ExecutionBlock,
) -> None:
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


def _append_artifact_event(record: ExecutionRunRecord, context: TestContext) -> None:
    if not record.junit_xml:
        return
    append_execution_event(
        run_id=record.run_id,
        context_id=context.context_id,
        phase="artifact",
        status=record.status,
        message="JUnit and HTML execution artifacts are available.",
        metadata={
            "junit_url": run_urls(record.run_id)["junit_url"],
            "report_url": run_urls(record.run_id)["report_url"],
        },
    )


def _append_completion_event(
    *,
    record: ExecutionRunRecord,
    context: TestContext,
    execution: ExecutionBlock | None,
) -> None:
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


def _append_completion_audit(
    *,
    record: ExecutionRunRecord,
    context: TestContext,
    execution: ExecutionBlock | None,
) -> None:
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
