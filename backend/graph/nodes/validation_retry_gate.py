from __future__ import annotations

from backend.graph.state import ReviewFeedback, TestContext


def validation_retry_gate(context: TestContext) -> TestContext:
    """Route failed automation validation back to generation up to a fixed limit.

    This keeps the local architecture proof aligned with the blueprint's
    generate -> validate -> repair loop without relying on external LLMs or
    company APIs. The actual repair signal is stored as review feedback so the
    automation generator receives a deterministic correction request on retry.
    """
    if not context.automation:
        context.mark("automation_validation_exhausted")
        return context

    all_ready = all(
        block.validation.artifact_exists
        and block.data_reference_check_passed
        and block.validation.dry_run_passed is True
        for block in context.automation.values()
    )
    if all_ready:
        context.mark("automation_validated")
        return context

    failed_files = [
        block.robot_file
        for block in context.automation.values()
        if not (
            block.validation.artifact_exists
            and block.data_reference_check_passed
            and block.validation.dry_run_passed is True
        )
    ]
    if context.validation_retry_count < context.max_validation_retries:
        context.validation_retry_count += 1
        context.graph_iteration += 1
        context.review_feedback.append(
            ReviewFeedback(
                requested_by="validator",
                comment=(
                    f"Validation retry {context.validation_retry_count}/"
                    f"{context.max_validation_retries}: regenerate or repair "
                    f"failed automation artifacts: {', '.join(failed_files)}"
                ),
            )
        )
        context.record_event(
            actor="system",
            event_type="automation_validation_retry",
            summary="Validation failed; automation regeneration was requested.",
            metadata={
                "context_id": context.context_id,
                "retry_count": context.validation_retry_count,
                "max_retries": context.max_validation_retries,
                "failed_files": failed_files,
            },
        )
        context.mark("automation_regeneration_requested")
        context.trace_node(
            node_name="validation_retry_gate",
            status="routed",
            summary="Routing back to automation generation after validation failure.",
            metadata={
                "retry_count": context.validation_retry_count,
                "max_retries": context.max_validation_retries,
            },
        )
        return context

    context.record_event(
        actor="system",
        event_type="automation_validation_retry",
        summary="Validation failed and retry limit was reached.",
        metadata={
            "context_id": context.context_id,
            "retry_count": context.validation_retry_count,
            "max_retries": context.max_validation_retries,
            "failed_files": failed_files,
        },
    )
    context.mark("automation_validation_exhausted")
    return context
