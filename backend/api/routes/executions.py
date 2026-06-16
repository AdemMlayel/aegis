from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel

from backend.security import Capability, Principal, require_capability
from backend.services.executions import (
    FINAL_EXECUTION_STATUSES,
    ExecutionBadRequest,
    ExecutionNotFound,
    get_result as get_result_service,
    get_result_logs as get_result_logs_service,
    list_results as list_results_service,
    process_execution_run,
    queue_execution_run,
    render_html_report,
    run_stream_payload,
    run_urls,
)
from backend.storage.execution_events import ExecutionEvent, list_execution_events
from backend.storage.execution_runs import (
    ExecutionRunRecord,
    ExecutionRunRequest,
    ExecutionRunStatus,
    load_execution_run,
)


router = APIRouter(tags=["executions"])


class ExecuteRunResponse(BaseModel):
    run_id: str
    context_id: str
    status: ExecutionRunStatus
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
    try:
        record = queue_execution_run(request)
    except ExecutionBadRequest as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ExecutionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    background_tasks.add_task(process_execution_run, record.run_id)
    return ExecuteRunResponse(
        run_id=record.run_id,
        context_id=record.context_id,
        status=record.status,
        **run_urls(record.run_id),
    )


@router.get("/results", response_model=ExecutionRunListResponse)
def list_results(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    context_id: str | None = None,
    run_status: ExecutionRunStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> ExecutionRunListResponse:
    return ExecutionRunListResponse(
        runs=list_results_service(
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
    return ExecutionRunDetailResponse(run=record, **run_urls(run_id))


@router.get("/results/{run_id}/summary.json", response_model=ExecutionRunDetailResponse)
def get_result_summary(
    run_id: str,
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> ExecutionRunDetailResponse:
    record = _load_run_or_404(run_id)
    return ExecutionRunDetailResponse(run=record, **run_urls(run_id))


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
    try:
        events = get_result_logs_service(run_id=run_id, limit=limit)
    except ExecutionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ExecutionEventListResponse(events=events)


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
                await websocket.send_json(run_stream_payload(record, events))
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
    try:
        return get_result_service(run_id)
    except ExecutionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
