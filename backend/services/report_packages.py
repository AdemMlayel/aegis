from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import Field

from backend.graph.artifacts import (
    GENERATED_ROOT,
    GENERATED_ROBOT_ROOT,
    PROJECT_ROOT,
    slug,
)
from backend.graph.state import StrictModel, TestContext, utc_now
from backend.storage.contexts import load_context


class ReportPackageNotFound(Exception):
    pass


class ReportPackageNotReady(Exception):
    pass


class ReportPackageFile(StrictModel):
    path: str
    kind: str
    content_type: str
    description: str
    size_bytes: int = Field(ge=0)
    sha256: str


class ReportPackageManifest(StrictModel):
    context_id: str
    ticket_id: str | None
    ticket_title: str | None
    generated_at: str
    package_name: str
    package_status: Literal[
        "draft",
        "ready_for_approval",
        "approved",
        "executed",
    ]
    approval_status: str
    execution_status: str
    validation_status: str
    quality_score: int | None
    files: list[ReportPackageFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReportPackage(StrictModel):
    file_name: str
    content: bytes
    manifest: ReportPackageManifest


def get_report_package_manifest(context_id: str) -> ReportPackageManifest:
    context = _load_report_context(context_id)
    _, manifest = _package_entries(context)
    return manifest


def render_technical_report(context_id: str) -> str:
    return _render_technical_report(_load_report_context(context_id))


def render_executive_report(context_id: str) -> str:
    return _render_executive_report(_load_report_context(context_id))


def build_report_package(context_id: str) -> ReportPackage:
    context = _load_report_context(context_id)
    entries, manifest = _package_entries(context)
    manifest_bytes = _json_bytes(manifest.model_dump(mode="json"))
    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        for path, content in entries.items():
            archive.writestr(path, content)
    return ReportPackage(
        file_name=f"{manifest.package_name}.zip",
        content=buffer.getvalue(),
        manifest=manifest,
    )


def _load_report_context(context_id: str) -> TestContext:
    context = load_context(context_id)
    if context is None:
        raise ReportPackageNotFound("Workflow context was not found")
    if context.reports is None:
        raise ReportPackageNotReady(
            "Workflow report has not been generated yet"
        )
    return context


def _package_entries(
    context: TestContext,
) -> tuple[dict[str, bytes], ReportPackageManifest]:
    entries: dict[str, bytes] = {}
    descriptions: dict[str, tuple[str, str, str]] = {}
    warnings: list[str] = []

    def add(
        path: str,
        content: bytes | str,
        *,
        kind: str,
        content_type: str,
        description: str,
    ) -> None:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        entries[path] = payload
        descriptions[path] = (kind, content_type, description)

    add(
        "reports/technical-report.md",
        _render_technical_report(context),
        kind="report",
        content_type="text/markdown",
        description="Detailed QA engineering report.",
    )
    add(
        "reports/executive-summary.md",
        _render_executive_report(context),
        kind="report",
        content_type="text/markdown",
        description="Stakeholder-facing QA status summary.",
    )
    add(
        "data/context.json",
        _json_bytes(context.model_dump(mode="json")),
        kind="evidence",
        content_type="application/json",
        description="Complete typed workflow context snapshot.",
    )
    add(
        "data/test-cases.json",
        _json_bytes(
            [test_case.model_dump(mode="json") for test_case in context.test_cases]
        ),
        kind="test-cases",
        content_type="application/json",
        description="Generated test case definitions.",
    )
    if context.validation_summary is not None:
        add(
            "data/validation-summary.json",
            _json_bytes(context.validation_summary.model_dump(mode="json")),
            kind="validation",
            content_type="application/json",
            description="Deterministic validation quality and traceability summary.",
        )
    add(
        "data/decision-history.json",
        _json_bytes(_decision_history(context)),
        kind="audit",
        content_type="application/json",
        description="Stage reviews, final approval, and workflow audit decisions.",
    )
    if context.execution is not None and context.execution.status != "skipped":
        add(
            "data/execution.json",
            _json_bytes(context.execution.model_dump(mode="json")),
            kind="execution",
            content_type="application/json",
            description="Latest workflow execution results.",
        )
    if (
        context.investigation is not None
        and context.investigation.status == "completed"
    ):
        add(
            "data/investigation.json",
            _json_bytes(context.investigation.model_dump(mode="json")),
            kind="investigation",
            content_type="application/json",
            description="Evidence-based failure investigation.",
        )

    for test_case_id, block in sorted(context.automation.items()):
        artifact_path = (PROJECT_ROOT / block.robot_file).resolve()
        if not _is_within(artifact_path, GENERATED_ROBOT_ROOT.resolve()):
            warnings.append(
                f"Skipped automation artifact outside generated Robot root: "
                f"{block.robot_file}"
            )
            continue
        if not artifact_path.is_file():
            warnings.append(f"Automation artifact was not found: {block.robot_file}")
            continue
        add(
            f"automation/{test_case_id}_{artifact_path.name}",
            artifact_path.read_bytes(),
            kind="automation",
            content_type="text/x-robotframework",
            description=f"Robot Framework automation for {test_case_id}.",
        )

    _add_optional_file(
        context.approval.git_handoff_path if context.approval else None,
        package_path="git/handoff.json",
        entries=entries,
        descriptions=descriptions,
        warnings=warnings,
        kind="git-handoff",
        content_type="application/json",
        description="Local Git handoff payload.",
    )
    if context.memory_archive is not None and context.memory_archive.status == "archived":
        add(
            "data/memory-archive.json",
            _json_bytes(context.memory_archive.model_dump(mode="json")),
            kind="memory",
            content_type="application/json",
            description="Archived episodic memory record for this workflow.",
        )

    execution_artifacts = (
        context.execution.artifacts
        if context.execution and context.execution.status != "skipped"
        else []
    )
    for artifact in execution_artifacts:
        if not artifact.path:
            continue
        safe_name = Path(artifact.path).name
        _add_optional_file(
            artifact.path,
            package_path=f"execution/artifacts/{safe_name}",
            entries=entries,
            descriptions=descriptions,
            warnings=warnings,
            kind=artifact.kind,
            content_type=artifact.content_type,
            description=artifact.description,
        )

    files = [
        ReportPackageFile(
            path=path,
            kind=descriptions[path][0],
            content_type=descriptions[path][1],
            description=descriptions[path][2],
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        for path, content in sorted(entries.items())
    ]
    ticket_id = context.ticket.id if context.ticket else None
    manifest = ReportPackageManifest(
        context_id=context.context_id,
        ticket_id=ticket_id,
        ticket_title=context.ticket.title if context.ticket else None,
        generated_at=utc_now().isoformat(),
        package_name=f"aegisqa_{slug(ticket_id or context.context_id)}",
        package_status=_package_status(context),
        approval_status=(
            context.approval.status if context.approval else "not_ready"
        ),
        execution_status=(
            context.execution.status if context.execution else "not_started"
        ),
        validation_status=(
            context.validation_summary.status
            if context.validation_summary
            else "not_run"
        ),
        quality_score=(
            context.validation_summary.quality_score
            if context.validation_summary
            else None
        ),
        files=files,
        warnings=warnings,
    )
    return entries, manifest


def _render_technical_report(context: TestContext) -> str:
    ticket = context.ticket
    report = context.reports
    validation = context.validation_summary
    execution = context.execution
    investigation = context.investigation
    approval = context.approval
    lines = [
        f"# Test Automation Report - {ticket.id if ticket else context.context_id}",
        "",
        f"**Ticket:** {ticket.title if ticket else 'Untitled workflow'}",
        f"**Context ID:** `{context.context_id}`",
        f"**Risk:** {report.highest_risk if report else 'unknown'}",
        f"**Workflow status:** {context.workflow_status}",
        f"**Approval:** {approval.status if approval else 'not ready'}",
        "",
        "## Summary",
        "",
        report.summary if report else "No report summary is available.",
        "",
        "## Validation",
        "",
    ]
    if validation:
        lines.extend(
            [
                f"- Quality score: {validation.quality_score}/100",
                (
                    f"- Requirement coverage: "
                    f"{validation.requirement_coverage_percent}%"
                ),
                (
                    f"- Artifacts passed: {validation.passed_artifacts}/"
                    f"{validation.total_artifacts}"
                ),
                f"- Validator mode: {validation.validator_mode}",
                (
                    f"- Workflow retries: {validation.retry_count}/"
                    f"{validation.max_retries}"
                ),
            ]
        )
        if validation.risk_areas:
            lines.extend(["", "### Validation risks", ""])
            lines.extend(f"- {risk}" for risk in validation.risk_areas)
    else:
        lines.append("- Validation has not run.")

    lines.extend(["", "## Test Cases", ""])
    for test_case in context.test_cases:
        lines.extend(
            [
                f"### {test_case.id} - {test_case.title}",
                f"- Type: {test_case.type}",
                f"- Priority: {test_case.priority}",
                (
                    f"- Requirement references: "
                    f"{', '.join(test_case.requirement_refs) or 'none'}"
                ),
                f"- Expected outcome: {test_case.expected_outcome}",
                "",
            ]
        )

    lines.extend(["## Automation Artifacts", ""])
    for test_case_id, block in sorted(context.automation.items()):
        lines.append(
            f"- `{test_case_id}`: `{block.robot_file}` - "
            f"{'passed' if block.validation.dry_run_passed is True else 'failed'}"
        )

    lines.extend(["", "## Execution", ""])
    if execution and execution.status != "skipped":
        lines.extend(
            [
                f"- Status: {execution.status}",
                f"- Environment: {execution.env}",
                f"- Adapter: {execution.adapter}",
                (
                    f"- Results: {execution.summary.passed} passed, "
                    f"{execution.summary.failed} failed, "
                    f"{execution.summary.skipped} skipped"
                ),
                f"- Duration: {execution.summary.duration_ms} ms",
            ]
        )
        for result in execution.results:
            lines.append(
                f"- {result.test_case_id} - {result.status}: {result.message}"
            )
    else:
        lines.append("- Execution has not run.")

    lines.extend(["", "## Investigation", ""])
    if investigation and investigation.status == "completed" and investigation.findings:
        lines.append(investigation.root_cause_summary or "Findings recorded.")
        lines.append("")
        for finding in investigation.findings:
            lines.append(
                f"- **{finding.severity} / {finding.category}:** "
                f"{finding.summary} (confidence {round(finding.confidence * 100)}%)"
            )
    else:
        lines.append("- No investigation findings recorded.")

    lines.extend(["", "## Decision History", ""])
    for item in _decision_history(context)["stage_reviews"]:
        lines.append(
            f"- {item['stage']}: {item['status']} by "
            f"{item['decided_by'] or 'pending reviewer'}"
        )
    if approval:
        lines.append(
            f"- Final package: {approval.status} by "
            f"{approval.decided_by or 'pending reviewer'}"
        )

    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in (report.next_actions if report else []))
    return "\n".join(lines).rstrip() + "\n"


def _render_executive_report(context: TestContext) -> str:
    ticket = context.ticket
    report = context.reports
    validation = context.validation_summary
    execution = context.execution
    approval = context.approval
    passed = execution.summary.passed if execution else 0
    failed = execution.summary.failed if execution else 0
    total = execution.summary.total if execution else len(context.test_cases)
    status = (
        "Approved"
        if approval and approval.status == "approved"
        else "Awaiting final approval"
        if approval and approval.status == "pending_review"
        else "In progress"
    )
    lines = [
        f"# QA Status - {ticket.title if ticket else 'Untitled workflow'}",
        "",
        f"**Ticket:** {ticket.id if ticket else context.context_id}",
        f"**Package status:** {status}",
        f"**Risk assessment:** {report.highest_risk if report else 'unknown'}",
        "",
        "## Outcome",
        "",
        report.summary if report else "The QA workflow report is not available.",
        "",
        "## Quality",
        "",
        (
            f"- Validation score: {validation.quality_score}/100"
            if validation
            else "- Validation has not run."
        ),
        (
            f"- Requirement coverage: {validation.requirement_coverage_percent}%"
            if validation
            else "- Requirement coverage is not available."
        ),
        f"- Generated test cases: {len(context.test_cases)}",
        f"- Automation artifacts: {len(context.automation)}",
        "",
        "## Execution Status",
        "",
    ]
    if execution and execution.status != "skipped":
        lines.extend(
            [
                f"- Tests run: {total}",
                f"- Passed: {passed}",
                f"- Failed: {failed}",
                f"- Overall status: {execution.status}",
            ]
        )
    else:
        lines.append("- Execution is awaiting package approval.")
    lines.extend(["", "## Recommendation", ""])
    lines.extend(
        f"- {action}" for action in (report.next_actions[:3] if report else [])
    )
    return "\n".join(lines).rstrip() + "\n"


def _decision_history(context: TestContext) -> dict[str, object]:
    stage_reviews = [
        review.model_dump(mode="json")
        for _, review in sorted(context.workflow_control.stage_reviews.items())
    ]
    return {
        "stage_reviews": stage_reviews,
        "final_approval": (
            context.approval.model_dump(mode="json") if context.approval else None
        ),
        "audit_log": [
            event.model_dump(mode="json") for event in context.audit_log
        ],
    }


def _package_status(context: TestContext) -> str:
    if context.execution is not None and context.execution.status != "skipped":
        return "executed"
    if context.approval and context.approval.status == "approved":
        return "approved"
    report_review = context.workflow_control.stage_reviews.get("report")
    if report_review and report_review.status == "approved":
        return "ready_for_approval"
    return "draft"


def _add_optional_file(
    source_path: str | None,
    *,
    package_path: str,
    entries: dict[str, bytes],
    descriptions: dict[str, tuple[str, str, str]],
    warnings: list[str],
    kind: str,
    content_type: str,
    description: str,
) -> None:
    if not source_path:
        return
    path = (PROJECT_ROOT / source_path).resolve()
    if not _is_within(path, GENERATED_ROOT.resolve()):
        warnings.append(f"Skipped file outside generated root: {source_path}")
        return
    if not path.is_file():
        warnings.append(f"Package artifact was not found: {source_path}")
        return
    entries[package_path] = path.read_bytes()
    descriptions[package_path] = (kind, content_type, description)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
