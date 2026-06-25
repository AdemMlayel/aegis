from __future__ import annotations

import backend.execution  # noqa: F401 - registers local execution adapters
from backend.config.settings import settings
from backend.execution import execution_adapter_registry
from backend.graph.state import (
    ExecutionBlock,
    ExecutionRequestBlock,
    ExecutionSummary,
    TestContext,
    utc_now,
)


def execution_dispatcher(context: TestContext) -> TestContext:
    """Dispatch approved workflows to a local execution adapter.

    Company execution infrastructure is intentionally out of scope for this
    milestone. The node proves the orchestration contract with local adapters:
    ``mock`` for deterministic architecture demos and ``robot`` for local Robot
    CLI execution when available.
    """
    if context.approval is None or context.approval.status != "approved":
        now = utc_now()
        if context.execution_request is None:
            context.execution_request = ExecutionRequestBlock(
                requested_by="system",
                adapter="deferred",
                env="local",
                status="deferred",
                blocked_reason="Execution requires human approval.",
            )
        else:
            context.execution_request.status = "deferred"
            context.execution_request.blocked_reason = "Execution requires human approval."
        context.execution = ExecutionBlock(
            status="skipped",
            run_by=context.execution_request.requested_by,
            started_at=now,
            finished_at=now,
            summary=ExecutionSummary(
                total=len(context.test_cases),
                passed=0,
                failed=0,
                skipped=len(context.test_cases),
                duration_ms=0,
            ),
            results=[],
            adapter=context.execution_request.adapter,
            env=context.execution_request.env,
        )
        context.record_event(
            actor="system",
            event_type="execution_completed",
            summary="Execution was deferred until human approval.",
            metadata={
                "context_id": context.context_id,
                "approval_status": context.approval.status if context.approval else None,
            },
        )
        context.mark("execution_deferred")
        return context

    request = context.execution_request or ExecutionRequestBlock(
        requested_by="system",
        adapter=settings.default_execution_adapter,
        env="local",
    )
    context.execution_request = request
    request.status = "running"

    if not execution_adapter_registry.has(request.adapter):
        now = utc_now()
        request.status = "blocked"
        request.blocked_reason = f"Execution adapter '{request.adapter}' is not registered."
        context.execution = ExecutionBlock(
            status="blocked",
            run_by=request.requested_by,
            started_at=now,
            finished_at=now,
            summary=ExecutionSummary(total=len(context.test_cases)),
            results=[],
            adapter=request.adapter,
            env=request.env,
        )
        context.record_event(
            actor=request.requested_by,
            event_type="execution_completed",
            summary="Execution was blocked before adapter start.",
            metadata={"reason": request.blocked_reason},
        )
        context.mark("execution_blocked")
        return context

    try:
        adapter = execution_adapter_registry.create(request.adapter)
        context = adapter.execute(
            context,
            actor=request.requested_by,
            env=request.env,
            branch=request.branch,
            tags=request.tags,
        )
    except ValueError as exc:
        now = utc_now()
        request.status = "blocked"
        request.blocked_reason = str(exc)
        context.execution = ExecutionBlock(
            status="blocked",
            run_by=request.requested_by,
            started_at=now,
            finished_at=now,
            summary=ExecutionSummary(total=len(context.test_cases)),
            results=[],
            adapter=request.adapter,
            env=request.env,
        )
        context.record_event(
            actor=request.requested_by,
            event_type="execution_completed",
            summary="Execution adapter was blocked.",
            metadata={
                "context_id": context.context_id,
                "adapter": request.adapter,
                "error": str(exc),
            },
        )
        context.mark("execution_blocked")
        return context

    request.status = "completed"
    context.execution_request = request
    return context
