from __future__ import annotations

from time import perf_counter
from typing import Literal
from uuid import uuid4

from backend.graph.artifacts import GENERATED_ROBOT_ROOT, PROJECT_ROOT
from backend.graph.state import (
    AutomationValidation,
    IntelligenceConfigBlock,
    ReviewFeedback,
    StageReviewBlock,
    TestContext,
    TicketData,
    WorkflowControlBlock,
    WorkflowStageName,
    utc_now,
)
from backend.graph.workflow import (
    REVIEWABLE_WORKFLOW_STAGES,
    WORKFLOW_STAGE_SEQUENCE,
    create_initial_context,
    next_workflow_stage,
    run_workflow_stage,
)
from backend.storage.artifact_revisions import (
    ArtifactRevision,
    list_artifact_revisions,
    save_artifact_revision,
)
from backend.storage.audit import append_audit_event
from backend.storage.contexts import load_context, save_context
from backend.storage.workflow_events import (
    WorkflowEvent,
    append_workflow_event,
    list_workflow_events,
)


WorkflowMode = Literal["autonomous", "approval_required", "step_by_step"]
StageDecision = Literal["approve", "request_changes"]


class WorkflowControlError(Exception):
    pass


class WorkflowSessionNotFound(WorkflowControlError):
    pass


class WorkflowControlConflict(WorkflowControlError):
    pass


class WorkflowControlBadRequest(WorkflowControlError):
    pass


def create_workflow_session(
    *,
    created_by: str,
    ticket: TicketData | None,
    intelligence_config: IntelligenceConfigBlock,
    mode: WorkflowMode,
) -> TestContext:
    context = create_initial_context(
        created_by=created_by,
        ticket=ticket,
        intelligence_config=intelligence_config,
    )
    context.workflow_control = WorkflowControlBlock(
        mode=mode,
        state="initialized",
        next_stage="ticket",
    )
    context.mark("session_initialized")
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="session",
        actor=created_by,
        status=context.workflow_control.state,
        message=f"Workflow session created in {mode} mode.",
        metadata={
            "ticket_id": context.ticket.id if context.ticket else None,
            "mode": mode,
        },
    )
    _append_control_audit(
        context=context,
        actor=created_by,
        summary=f"Workflow session created in {mode} mode.",
        metadata={"mode": mode},
    )
    return context


def resume_workflow_session(
    *,
    context_id: str,
    actor: str,
    single_step: bool = False,
) -> TestContext:
    context = _load_context(context_id)
    control = context.workflow_control
    if control.state == "waiting_review":
        raise WorkflowControlConflict(
            "The current stage requires a review decision before the workflow can resume"
        )
    if control.state == "completed":
        return context
    if control.state == "running":
        raise WorkflowControlConflict("The workflow session is already running")

    control.pause_requested = False
    control.state = "running"
    control.last_error = None
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="control",
        actor=actor,
        status="running",
        message="Workflow session resumed.",
        metadata={"single_step": single_step, "mode": control.mode},
    )

    while control.next_stage is not None:
        context = _run_stage(context=context, stage=control.next_stage, actor=actor)
        control = context.workflow_control
        if control.state in {"waiting_review", "completed", "failed"}:
            break
        if control.pause_requested:
            control.state = "paused"
            break
        if single_step or control.mode == "step_by_step":
            control.state = "paused"
            append_workflow_event(
                context_id=context.context_id,
                kind="control",
                actor=actor,
                status="paused",
                message="Workflow paused at the next stage boundary.",
                metadata={"next_stage": control.next_stage},
            )
            break

    save_context(context)
    return context


def pause_workflow_session(*, context_id: str, actor: str) -> TestContext:
    context = _load_context(context_id)
    control = context.workflow_control
    if control.state == "completed":
        raise WorkflowControlConflict("Completed workflow sessions cannot be paused")
    control.pause_requested = True
    if control.state in {"initialized", "running"}:
        control.state = "paused"
    context.mark("workflow_paused")
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="control",
        actor=actor,
        status=control.state,
        message="Pause requested. The workflow will remain stopped at a stage boundary.",
        metadata={
            "current_stage": control.current_stage,
            "next_stage": control.next_stage,
        },
    )
    _append_control_audit(
        context=context,
        actor=actor,
        summary="Workflow pause requested.",
    )
    return context


def review_workflow_stage(
    *,
    context_id: str,
    stage: WorkflowStageName,
    decision: StageDecision,
    reviewed_by: str,
    comment: str | None = None,
) -> TestContext:
    context = _load_context(context_id)
    control = context.workflow_control
    if stage not in control.completed_stages:
        raise WorkflowControlConflict(
            f"Stage '{stage}' has not completed and cannot be reviewed"
        )
    if decision == "request_changes" and not comment:
        raise WorkflowControlBadRequest(
            "request_changes decisions require a comment"
        )
    if (
        stage == "validation"
        and decision == "approve"
        and context.validation_summary is not None
        and context.validation_summary.status == "failed"
    ):
        raise WorkflowControlConflict(
            "Failed validation cannot be approved; request changes and rerun validation"
        )
    pending_stages = {
        name
        for name, item in control.stage_reviews.items()
        if item.status == "pending"
    }
    if (
        control.state == "waiting_review"
        and pending_stages
        and stage not in pending_stages
    ):
        raise WorkflowControlConflict(
            f"Stage '{stage}' is not the stage currently waiting for review"
        )

    revision = control.stage_revisions.get(stage, 1)
    review = control.stage_reviews.get(stage) or StageReviewBlock(
        stage=stage,
        revision=revision,
    )
    review.revision = revision
    review.decided_at = utc_now()
    review.decided_by = reviewed_by
    if comment:
        review.comments.append(comment)

    if decision == "approve":
        review.status = "approved"
        control.stage_reviews[stage] = review
        if control.state == "waiting_review":
            control.state = (
                "completed" if control.next_stage is None else "paused"
            )
        context.mark(f"{stage}_approved")
        message = f"{stage.replace('_', ' ').title()} stage approved."
    else:
        review.status = "changes_requested"
        control.stage_reviews[stage] = review
        context.review_feedback.append(
            ReviewFeedback(
                requested_by=reviewed_by,
                comment=comment or "",
                stage=stage,
            )
        )
        restart_stage = _invalidate_from_stage(context, stage)
        control.state = "paused"
        control.next_stage = restart_stage
        context.mark(f"{stage}_changes_requested")
        message = (
            f"Changes requested for {stage.replace('_', ' ')}. "
            f"Restart queued from {restart_stage.replace('_', ' ')}."
        )

    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="review",
        actor=reviewed_by,
        stage=stage,
        status=review.status,
        message=message,
        metadata={
            "decision": decision,
            "comment": comment,
            "revision": revision,
            "next_stage": control.next_stage,
        },
    )
    append_audit_event(
        actor=reviewed_by,
        event_type="stage_review",
        summary=message,
        metadata={
            "context_id": context.context_id,
            "stage": stage,
            "decision": decision,
            "comment": comment,
            "revision": revision,
        },
    )
    return context


def regenerate_workflow_stage(
    *,
    context_id: str,
    stage: WorkflowStageName,
    actor: str,
    comment: str,
) -> TestContext:
    context = review_workflow_stage(
        context_id=context_id,
        stage=stage,
        decision="request_changes",
        reviewed_by=actor,
        comment=comment,
    )
    return resume_workflow_session(
        context_id=context.context_id,
        actor=actor,
        single_step=True,
    )


def get_workflow_timeline(
    *,
    context_id: str,
    after_sequence: int = 0,
    limit: int = 200,
) -> list[WorkflowEvent]:
    _load_context(context_id)
    return list_workflow_events(
        context_id=context_id,
        after_sequence=after_sequence,
        limit=limit,
    )


def append_workflow_message(
    *,
    context_id: str,
    actor: str,
    message: str,
) -> WorkflowEvent:
    context = _load_context(context_id)
    event = append_workflow_event(
        context_id=context.context_id,
        kind="message",
        actor=actor,
        status="recorded",
        message=message,
        metadata={"role": "user"},
    )
    _append_control_audit(
        context=context,
        actor=actor,
        summary="Workflow operator message recorded.",
        metadata={"event_id": event.id},
    )
    return event


def edit_robot_artifact(
    *,
    context_id: str,
    test_case_id: str,
    actor: str,
    content: str,
    comment: str | None = None,
) -> tuple[TestContext, ArtifactRevision]:
    context = _load_context(context_id)
    if context.ticket is None:
        raise WorkflowControlConflict("Workflow has no ticket")
    block = context.automation.get(test_case_id)
    if block is None:
        raise WorkflowControlConflict(
            f"No generated automation exists for test case '{test_case_id}'"
        )
    artifact_path = (PROJECT_ROOT / block.robot_file).resolve()
    generated_root = GENERATED_ROBOT_ROOT.resolve()
    try:
        artifact_path.relative_to(generated_root)
    except ValueError as exc:
        raise WorkflowControlBadRequest(
            "Artifact path escapes the generated Robot root"
        ) from exc
    if artifact_path.suffix != ".robot" or not artifact_path.is_file():
        raise WorkflowControlConflict("Generated Robot artifact was not found")

    revisions = list_artifact_revisions(
        context_id=context.context_id,
        test_case_id=test_case_id,
    )
    existing_content = artifact_path.read_text(encoding="utf-8")
    if not revisions:
        save_artifact_revision(
            ArtifactRevision(
                context_id=context.context_id,
                test_case_id=test_case_id,
                artifact_path=block.robot_file,
                version=1,
                source="generated",
                actor="system",
                comment="Original generated artifact.",
                content=existing_content,
            )
        )
        next_version = 2
    else:
        next_version = revisions[-1].version + 1

    temp_path = artifact_path.with_name(
        f".{artifact_path.name}.{uuid4().hex}.tmp"
    )
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(artifact_path)
        try:
            revision = save_artifact_revision(
                ArtifactRevision(
                    context_id=context.context_id,
                    test_case_id=test_case_id,
                    artifact_path=block.robot_file,
                    version=next_version,
                    source="manual",
                    actor=actor,
                    comment=comment,
                    content=content,
                )
            )
        except Exception:
            artifact_path.write_text(existing_content, encoding="utf-8")
            raise
    finally:
        if temp_path.exists():
            temp_path.unlink()

    context.automation_revision += 1
    block.revision = context.automation_revision
    block.generated_at = utc_now()
    block.data_reference_check_passed = False
    block.validation = AutomationValidation()
    _invalidate_after_artifact_edit(context, actor=actor)
    context.mark("artifact_edited")
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="artifact",
        actor=actor,
        stage="automation",
        status="edited",
        message=f"Robot artifact for {test_case_id} was edited.",
        metadata={
            "test_case_id": test_case_id,
            "artifact_path": block.robot_file,
            "version": next_version,
            "comment": comment,
            "next_stage": context.workflow_control.next_stage,
        },
    )
    append_audit_event(
        actor=actor,
        event_type="artifact_revision",
        summary=f"Robot artifact for {test_case_id} was edited.",
        metadata={
            "context_id": context.context_id,
            "test_case_id": test_case_id,
            "artifact_path": block.robot_file,
            "version": next_version,
            "comment": comment,
        },
    )
    return context, revision


def get_artifact_revisions(
    *,
    context_id: str,
    test_case_id: str,
) -> list[ArtifactRevision]:
    _load_context(context_id)
    return list_artifact_revisions(
        context_id=context_id,
        test_case_id=test_case_id,
    )


def _stage_completion_failure(
    context: TestContext,
    stage: WorkflowStageName,
) -> str | None:
    """Return a failure reason when a stage finished without raising but lacks
    real success evidence, else ``None``.

    The validation loop is the key case: ``_run_validation_stage`` returns
    normally after exhausting its retries even when artifacts never passed
    dry-run (``workflow_status == 'automation_validation_exhausted'``). Marking
    that stage completed would misreport a failed gate as passed. Evidence: every
    automation block must exist and have ``dry_run_passed is True`` (mirrors the
    autonomous path's ``_apply_honest_completion`` validation predicate, N1).
    """
    if stage != "validation":
        return None
    if not context.automation:
        return "Validation produced no automation artifacts to validate."
    unvalidated = [
        block.robot_file
        for block in context.automation.values()
        if block.validation.dry_run_passed is not True
    ]
    if unvalidated:
        return (
            "Validation did not pass for all automation artifacts "
            f"(retries exhausted at {context.validation_retry_count}/"
            f"{context.max_validation_retries}); unvalidated: "
            f"{', '.join(unvalidated)}"
        )
    return None


def _run_stage(
    *,
    context: TestContext,
    stage: WorkflowStageName,
    actor: str,
) -> TestContext:
    control = context.workflow_control
    control.state = "running"
    control.current_stage = stage
    context.mark(f"{stage}_running")
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="stage",
        actor=actor,
        stage=stage,
        status="running",
        message=f"{stage.replace('_', ' ').title()} stage started.",
        metadata={"revision": control.stage_revisions.get(stage, 0) + 1},
    )
    started = perf_counter()
    try:
        context = run_workflow_stage(context, stage)
    except Exception as exc:
        control = context.workflow_control
        control.state = "failed"
        control.current_stage = stage
        control.last_error = f"{type(exc).__name__}: {exc}"
        context.mark(f"{stage}_failed")
        save_context(context)
        append_workflow_event(
            context_id=context.context_id,
            kind="error",
            actor=actor,
            stage=stage,
            status="failed",
            message=f"{stage.replace('_', ' ').title()} stage failed: {exc}",
            metadata={"exception_type": type(exc).__name__},
        )
        raise

    # S2: a stage can finish without raising yet still have genuinely failed --
    # most importantly the validation loop, which returns normally after
    # exhausting its retries with artifacts that never passed dry-run. Marking
    # such a stage "completed" would misreport a failed gate as passed (the same
    # honesty principle as _apply_honest_completion on the autonomous path). Gate
    # the completion bookkeeping on real evidence and fail honestly otherwise.
    stage_failure = _stage_completion_failure(context, stage)
    if stage_failure is not None:
        control = context.workflow_control
        control.state = "failed"
        control.current_stage = stage
        control.last_error = stage_failure
        context.mark(f"{stage}_failed")
        save_context(context)
        append_workflow_event(
            context_id=context.context_id,
            kind="error",
            actor=actor,
            stage=stage,
            status="failed",
            message=f"{stage.replace('_', ' ').title()} stage failed: {stage_failure}",
            metadata={"evidence_gate": True},
        )
        return context

    control = context.workflow_control
    persisted = load_context(context.context_id)
    if persisted is not None and persisted.workflow_control.pause_requested:
        control.pause_requested = True
    revision = control.stage_revisions.get(stage, 0) + 1
    control.stage_revisions[stage] = revision
    if stage not in control.completed_stages:
        control.completed_stages.append(stage)
    control.current_stage = None
    control.next_stage = next_workflow_stage(stage)
    control.last_error = None

    if (
        control.mode == "approval_required"
        and stage in REVIEWABLE_WORKFLOW_STAGES
    ):
        control.stage_reviews[stage] = StageReviewBlock(
            stage=stage,
            revision=revision,
            status="pending",
            requested_at=utc_now(),
            requested_by=actor,
        )
        control.state = "waiting_review"
    elif control.next_stage is None:
        control.state = "completed"
    else:
        control.state = "running"

    duration_ms = round((perf_counter() - started) * 1000)
    context.mark(
        "workflow_session_completed"
        if control.state == "completed"
        else context.workflow_status
    )
    save_context(context)
    append_workflow_event(
        context_id=context.context_id,
        kind="stage",
        actor=actor,
        stage=stage,
        status="completed",
        message=_stage_summary(context, stage),
        metadata={
            "revision": revision,
            "duration_ms": duration_ms,
            "next_stage": control.next_stage,
            "control_state": control.state,
        },
    )
    return context


def _invalidate_from_stage(
    context: TestContext,
    stage: WorkflowStageName,
) -> WorkflowStageName:
    restart_stage = "automation" if stage == "validation" else stage
    restart_index = WORKFLOW_STAGE_SEQUENCE.index(restart_stage)
    control = context.workflow_control
    control.completed_stages = [
        item
        for item in control.completed_stages
        if WORKFLOW_STAGE_SEQUENCE.index(item) < restart_index
    ]
    control.stage_reviews = {
        name: review
        for name, review in control.stage_reviews.items()
        if WORKFLOW_STAGE_SEQUENCE.index(name) < restart_index or name == stage
    }

    if restart_index <= WORKFLOW_STAGE_SEQUENCE.index("requirements"):
        context.requirement_analysis = None
    if restart_index <= WORKFLOW_STAGE_SEQUENCE.index("coverage"):
        context.coverage_plan = None
    if restart_index <= WORKFLOW_STAGE_SEQUENCE.index("tests"):
        context.test_cases = []
        context.test_data = {}
    if restart_index <= WORKFLOW_STAGE_SEQUENCE.index("automation"):
        context.automation = {}
        context.validation_summary = None
        # The validation loop is about to run fresh from regenerated automation.
        # Reset the retry bookkeeping so a context that previously exhausted its
        # retries does not enter validation already maxed-out and skip repair
        # while still being marked completed (W5).
        context.validation_retry_count = 0
        context.graph_iteration = 1
    if restart_index <= WORKFLOW_STAGE_SEQUENCE.index("approval"):
        context.approval = None
    if restart_stage != "report":
        context.execution_request = None
        context.execution = None
        context.investigation = None
        context.memory_archive = None
    context.reports = None
    return restart_stage


def _invalidate_after_artifact_edit(
    context: TestContext,
    *,
    actor: str,
) -> None:
    control = context.workflow_control
    validation_index = WORKFLOW_STAGE_SEQUENCE.index("validation")
    control.completed_stages = [
        stage
        for stage in control.completed_stages
        if WORKFLOW_STAGE_SEQUENCE.index(stage) < validation_index
    ]
    control.stage_reviews = {
        name: review
        for name, review in control.stage_reviews.items()
        if WORKFLOW_STAGE_SEQUENCE.index(name) < validation_index
    }
    control.stage_revisions["automation"] = (
        control.stage_revisions.get("automation", 0) + 1
    )
    control.next_stage = "validation"
    control.current_stage = None
    # A manual artifact edit re-runs validation from regenerated automation.
    # Reset retry bookkeeping so the re-validation gets its full retry budget
    # instead of inheriting an exhausted count from a prior run (W5).
    context.validation_retry_count = 0
    context.graph_iteration = 1
    if control.mode == "approval_required":
        control.stage_reviews["automation"] = StageReviewBlock(
            stage="automation",
            revision=control.stage_revisions["automation"],
            status="pending",
            requested_at=utc_now(),
            requested_by=actor,
        )
        control.state = "waiting_review"
    else:
        control.state = "paused"
    control.pause_requested = False
    context.approval = None
    context.validation_summary = None
    context.execution_request = None
    context.execution = None
    context.investigation = None
    context.memory_archive = None
    context.reports = None


def _stage_summary(context: TestContext, stage: WorkflowStageName) -> str:
    if stage == "ticket":
        return f"Ticket {context.ticket.id if context.ticket else 'unknown'} loaded."
    if stage == "requirements":
        analysis = context.requirement_analysis
        return (
            f"Requirement analysis completed with "
            f"{len(analysis.clarification_questions) if analysis else 0} clarification question(s)."
        )
    if stage == "coverage":
        plan = context.coverage_plan
        return (
            f"Coverage planned at {plan.risk_level if plan else 'unknown'} risk "
            f"with {len(plan.test_types_required) if plan else 0} test type(s)."
        )
    if stage == "tests":
        return f"Generated {len(context.test_cases)} test case(s) with resolved data."
    if stage == "automation":
        return (
            f"Generated {len(context.automation)} Robot artifact(s), "
            f"revision {context.automation_revision}."
        )
    if stage == "validation":
        passed = sum(
            1
            for block in context.automation.values()
            if block.validation.dry_run_passed is True
        )
        return f"Validated {passed}/{len(context.automation)} Robot artifact(s)."
    if stage == "approval":
        return (
            f"Approval package is "
            f"{context.approval.status if context.approval else 'not ready'}."
        )
    return "Workflow report and supporting evidence are available."


def _load_context(context_id: str) -> TestContext:
    context = load_context(context_id)
    if context is None:
        raise WorkflowSessionNotFound("Workflow context was not found")
    return context


def _append_control_audit(
    *,
    context: TestContext,
    actor: str,
    summary: str,
    metadata: dict[str, object] | None = None,
) -> None:
    append_audit_event(
        actor=actor,
        event_type="workflow_control",
        summary=summary,
        metadata={
            "context_id": context.context_id,
            **(metadata or {}),
        },
    )
