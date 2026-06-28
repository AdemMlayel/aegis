from __future__ import annotations

from collections import Counter
from typing import Any

from backend.chat.intent_classifier import ClassifiedIntent
from backend.chat.schemas import ChatAction, ChatSession
from backend.integrations.providers import build_provider_catalog
from backend.reference_corpus.profiles import (
    load_execution_evidence_profile,
    load_report_profile,
    load_robot_keyword_registry,
    load_robot_style_profile,
)
from backend.storage.contexts import load_context
from backend.tickets import get_ticket_source


def build_assistant_response(
    *,
    session: ChatSession,
    classified: ClassifiedIntent,
    message_context_id: str | None = None,
    message_ticket_id: str | None = None,
) -> str:
    context_id = classified.context_id or message_context_id or session.context_id
    ticket_id = classified.ticket_id or message_ticket_id or session.ticket_id

    if classified.intent == "help":
        return _help_response()
    if classified.intent == "system_question":
        return _system_response()
    if classified.intent == "workflow_start":
        if not ticket_id:
            return "I can start a workflow once a ticket is selected or a ticket ID is provided."
        return f"I can start a controlled workflow for ticket `{ticket_id}`. This action requires confirmation."
    if classified.intent == "workflow_step":
        return _workflow_step_response(context_id)
    if classified.intent == "workflow_status":
        return _workflow_status_response(context_id)
    if classified.intent == "ticket_question":
        return _ticket_response(ticket_id, context_id)
    if classified.intent == "artifact_question":
        return _artifact_response(context_id, classified.normalized_message)
    if classified.intent == "validation_question":
        return _validation_response(context_id)
    if classified.intent == "approval_request":
        return _approval_response(context_id)
    if classified.intent == "execution_request":
        return _execution_response(context_id)
    if classified.intent == "investigation_question":
        return _investigation_response(context_id)
    if classified.intent == "report_request":
        return _report_response(context_id)
    if classified.intent == "knowledge_question":
        return _knowledge_response()
    if classified.intent == "action_history":
        return _action_history_response(session)
    return _fallback_response()


def _help_response() -> str:
    return (
        "I can help you inspect tickets, explain workflow status, review generated Robot artifacts, "
        "explain validation and execution results, summarize investigation/report output, list action history, "
        "and propose controlled workflow actions. Workflow start, approval, stage progression, and execution "
        "require explicit confirmation."
    )


def _system_response() -> str:
    catalog = build_provider_catalog().as_dict(include_external=True)
    selected = catalog.get("selected", [])
    selected_lines = [
        f"- {item['kind']}: `{item['selected']}` ({item['status']})"
        for item in selected
    ]
    return _lines(
        "Current AegisQA runtime is local/demo-first.",
        f"- Environment: `{catalog.get('environment')}`",
        f"- Deterministic demo mode: `{catalog.get('deterministic_demo_mode')}`",
        f"- External connectors enabled: `{catalog.get('external_connectors_enabled')}`",
        "Selected providers:",
        *selected_lines,
    )


def _workflow_step_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can run or explain the next stage."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    control = context.workflow_control
    if control.state == "waiting_review":
        pending = _pending_reviews(context)
        stage = pending[0] if pending else "current stage"
        return f"The workflow is waiting for review on `{stage}`. Approve or request changes before resuming."
    if control.next_stage is None:
        return "The workflow has no remaining stage to run."
    return _lines(
        f"The next stage is `{control.next_stage}`. Running it is a controlled action and requires confirmation.",
        f"- Current state: `{control.state}`",
        f"- Completed stages: {_join_or_none(control.completed_stages)}",
    )


def _workflow_status_response(context_id: str | None) -> str:
    if not context_id:
        return "No workflow is currently attached to this chat session."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    control = context.workflow_control
    pending_reviews = _pending_reviews(context)
    last_trace = context.workflow_trace[-1] if context.workflow_trace else None
    next_safe_action = _next_safe_action(context)
    return _lines(
        f"Workflow `{context.context_id}` is `{control.state}`.",
        f"- Ticket: `{context.ticket.id if context.ticket else 'none'}`",
        f"- Workflow status: `{context.workflow_status}`",
        f"- Current stage: `{control.current_stage or 'none'}`",
        f"- Next stage: `{control.next_stage or 'none'}`",
        f"- Completed stages: {_join_or_none(control.completed_stages)}",
        f"- Pending reviews: {_join_or_none(pending_reviews)}",
        f"- Last trace: {_format_trace(last_trace)}",
        f"- Next safe action: {next_safe_action}",
    )


def _ticket_response(ticket_id: str | None, context_id: str | None) -> str:
    ticket = None
    requirement_analysis = None
    coverage_plan = None
    if context_id:
        context = load_context(context_id)
        if context:
            ticket = context.ticket
            requirement_analysis = context.requirement_analysis
            coverage_plan = context.coverage_plan
    if ticket is None and ticket_id:
        ticket = get_ticket_source().fetch(ticket_id)
    if ticket is None:
        return "Select or mention a ticket and I can summarize gaps, risks, and acceptance criteria."

    missing: list[str] = []
    if not ticket.acceptance_criteria:
        missing.append("acceptance criteria")
    if not ticket.test_steps:
        missing.append("explicit test steps")
    if not ticket.input_data:
        missing.append("test data")
    if not ticket.expected_outputs:
        missing.append("expected outputs")
    if not ticket.preconditions:
        missing.append("preconditions")

    risks = list(ticket.risks_or_constraints[:4])
    if coverage_plan:
        risks.extend(coverage_plan.risk_rationale[:2])
    lines = [
        f"Ticket `{ticket.id}` — {ticket.title}",
        f"- Priority: `{ticket.priority}`",
        f"- Scope items: {len(ticket.test_scope)}",
        f"- Acceptance criteria: {len(ticket.acceptance_criteria)}",
        f"- Validation rules: {len(ticket.validation_rules)}",
        f"- Missing/weak areas: {', '.join(missing) if missing else 'no major structural gaps detected'}",
        f"- Key risks: {', '.join(risks) if risks else 'none declared'}",
    ]
    if requirement_analysis:
        lines.append(f"- Requirement confidence: {requirement_analysis.confidence:.2f}")
    return _lines(*lines)


def _artifact_response(context_id: str | None, normalized_message: str) -> str:
    if _asks_about_keywords(normalized_message):
        return _keyword_registry_response()
    if not context_id:
        return (
            "Open or start a workflow first, then I can explain generated Robot artifacts. "
            "You can also ask what Robot keywords are available."
        )
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if not context.automation:
        return "No Robot automation has been generated yet."

    registry = load_robot_keyword_registry()
    style = load_robot_style_profile()
    artifact_lines: list[str] = []
    for test_id, block in list(context.automation.items())[:6]:
        validation = block.validation
        if validation.dry_run_passed is True:
            validation_state = "passed"
        elif validation.dry_run_passed is False:
            validation_state = "failed"
        else:
            validation_state = validation.dry_run_skipped_reason or "not run"
        artifact_lines.append(
            f"- `{test_id}` -> `{block.robot_file}` | rev {block.revision} | dry-run `{validation_state}` | errors {len(validation.errors)}"
        )
    valid = sum(1 for block in context.automation.values() if block.validation.dry_run_passed is True)
    guidance = style.get("generation_guidance", [])[:2]
    lines = [
        f"This workflow has {len(context.automation)} generated Robot artifact(s).",
        f"- Validation dry-run passed: {valid}/{len(context.automation)}",
        f"- Corpus keyword registry size: {len(registry.get('keywords', []))}",
        f"- Robot style source files analyzed: {_profile_count(style, 'files_analyzed')}",
        "Artifacts:",
        *artifact_lines,
    ]
    if guidance:
        lines.append(f"Generation guidance: {'; '.join(guidance)}")
    return _lines(*lines)


def _validation_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can explain validation results."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.validation_summary is None:
        return "Validation has not run yet."
    summary = context.validation_summary
    failed = [
        (test_id, block.validation.errors)
        for test_id, block in context.automation.items()
        if block.validation.dry_run_passed is False
    ]
    failed_lines = [
        f"- `{test_id}`: {errors[0] if errors else 'dry-run failed without a stored error'}"
        for test_id, errors in failed[:5]
    ]
    lines = [
        f"Validation status is `{summary.status}`.",
        f"- Validator mode: `{summary.validator_mode}`",
        f"- Total artifacts: {summary.total_artifacts}",
        f"- Passed artifacts: {summary.passed_artifacts}",
        f"- Failed artifacts: {summary.failed_artifacts}",
        f"- Requirement coverage: {summary.requirement_coverage_percent}%",
        f"- Artifact pass rate: {summary.artifact_pass_percent}%",
        f"- Data reference score: {summary.data_reference_percent}%",
        f"- Quality score: {summary.quality_score}/100",
        f"- Retry count: {summary.retry_count}/{summary.max_retries}",
        f"- Missing requirements: {_join_or_none(summary.missing_requirements)}",
        f"- Risk areas: {_join_or_none(summary.risk_areas)}",
        "Failed artifacts:",
    ]
    lines.extend(failed_lines or ["- none"])
    return _lines(*lines)


def _approval_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can inspect approval state."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    pending = _pending_reviews(context)
    if pending:
        return _lines(
            f"The workflow is waiting for review on `{pending[0]}`. Approval requires confirmation.",
            "A human reviewer should inspect the stage output before approving.",
        )
    if context.approval:
        return _lines(
            f"Package approval status is `{context.approval.status}`.",
            f"- Review items: {len(context.approval.review_items)}",
            f"- Git handoff: `{context.approval.git_status}`",
        )
    return "No approval package exists yet. Continue the workflow until the approval stage."


def _execution_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can inspect or request execution."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.execution:
        summary = context.execution.summary
        failed = [result for result in context.execution.results if result.status == "failed"]
        failed_lines = [
            f"- `{result.test_case_id}`: {result.message}" for result in failed[:5]
        ]
        lines = [
            f"Execution status is `{context.execution.status}`.",
            f"- Adapter: `{context.execution.adapter}`",
            f"- Environment: `{context.execution.env}`",
            f"- Total: {summary.total}",
            f"- Passed: {summary.passed}",
            f"- Failed: {summary.failed}",
            f"- Skipped: {summary.skipped}",
            f"- Artifacts: {len(context.execution.artifacts)}",
        ]
        if failed_lines:
            lines.append("Failed cases:")
            lines.extend(failed_lines)
        return _lines(*lines)
    if context.approval is None or context.approval.status != "approved":
        return "Execution is not available yet. The workflow package must be approved first."
    return "The workflow is approved and can be executed through the configured adapter after confirmation."


def _investigation_response(context_id: str | None) -> str:
    profile = load_execution_evidence_profile()
    if not context_id:
        return "Select an executed workflow first, then I can explain investigation findings."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.investigation is None:
        failed_profile = profile.get("profiles", {}).get("failed", {})
        guidance = profile.get("investigation_guidance", [])[:2]
        return _lines(
            "No investigation is available yet. Execute the workflow first.",
            f"- Failed execution examples in corpus: {failed_profile.get('artifact_count', 0)} artifact(s)",
            f"- Investigation guidance: {'; '.join(guidance) if guidance else 'none'}",
        )
    findings = context.investigation.findings
    categories = Counter(finding.category for finding in findings)
    top_findings = [
        f"- `{finding.category}`/{finding.severity}: {finding.summary}"
        for finding in findings[:5]
    ]
    lines = [
        f"Investigation status is `{context.investigation.status}` with confidence {context.investigation.confidence:.2f}.",
        f"- Evidence items: {len(context.investigation.evidence_items)}",
        f"- Findings: {len(findings)}",
        f"- Categories: {dict(categories)}",
        f"- Root cause summary: {context.investigation.root_cause_summary or 'not available'}",
    ]
    if top_findings:
        lines.append("Findings:")
        lines.extend(top_findings)
    return _lines(*lines)


def _report_response(context_id: str | None) -> str:
    profile = load_report_profile()
    if not context_id:
        return "Select a workflow first, then I can summarize its report."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.reports is None:
        return "The report has not been generated yet."
    return _lines(
        f"Report is available for workflow `{context.context_id}`.",
        f"- Highest risk: `{context.reports.highest_risk}`",
        f"- Total test cases: {context.reports.total_test_cases}",
        f"- Confidence: {context.reports.confidence:.2f}",
        f"- Summary: {context.reports.summary}",
        f"- Next actions: {_join_or_none(context.reports.next_actions)}",
        f"- Report corpus style sections: {_join_or_none(profile.get('profile', {}).get('preferred_sections', []))}",
    )


def _knowledge_response() -> str:
    registry = load_robot_keyword_registry()
    style = load_robot_style_profile()
    report = load_report_profile()
    evidence = load_execution_evidence_profile()
    failed_profile = evidence.get("profiles", {}).get("failed", {})
    successful_profile = evidence.get("profiles", {}).get("successful", {})
    return _lines(
        "Current safe knowledge grounding uses normalized sanitized profiles only.",
        f"- Robot keywords: {len(registry.get('keywords', []))}",
        f"- Robot style files analyzed: {_profile_count(style, 'files_analyzed')}",
        f"- Report files analyzed: {_profile_count(report, 'files_analyzed')}",
        f"- Successful execution artifacts: {successful_profile.get('artifact_count', 0)}",
        f"- Failed execution artifacts: {failed_profile.get('artifact_count', 0)}",
        "Raw sensitive input remains quarantined; agents consume only sanitized normalized outputs.",
    )


def _keyword_registry_response() -> str:
    registry = load_robot_keyword_registry()
    keywords: list[dict[str, Any]] = registry.get("keywords", [])
    domain_counts = Counter(str(item.get("domain", "unknown")) for item in keywords)
    approved = sum(1 for item in keywords if item.get("approved_for_generation") is True)
    samples = [
        f"- `{item.get('name')}` ({item.get('domain', 'unknown')}, risk `{item.get('risk_level', 'unknown')}`)"
        for item in keywords[:8]
    ]
    return _lines(
        "Robot keyword registry is available from sanitized normalized corpus output only.",
        f"- Total keywords: {len(keywords)}",
        f"- Approved for generation: {approved}",
        f"- Domains: {dict(domain_counts)}",
        "Sample keywords:",
        *(samples or ["- none"]),
    )


def _action_history_response(session: ChatSession) -> str:
    actions = session.action_history
    if not actions:
        return "No controlled chat actions have been proposed in this session yet."
    counts = Counter(action.status for action in actions)
    recent = [
        _format_action(action)
        for action in sorted(actions, key=lambda item: item.created_at, reverse=True)[:8]
    ]
    return _lines(
        "Controlled action history for this chat session:",
        f"- Pending: {counts.get('pending_confirmation', 0)}",
        f"- Completed: {counts.get('completed', 0)}",
        f"- Cancelled: {counts.get('cancelled', 0)}",
        f"- Blocked: {counts.get('blocked', 0)}",
        "Recent actions:",
        *recent,
    )


def _fallback_response() -> str:
    return (
        "I did not map that to a safe workflow action yet. I can answer questions about tickets, "
        "workflow status, Robot artifacts, validation, execution, investigation, reports, providers, "
        "action history, and safe corpus grounding."
    )


def _asks_about_keywords(normalized_message: str) -> bool:
    return any(
        token in normalized_message
        for token in [
            "keyword",
            "keywords",
            "mot cle",
            "mots cles",
            "schlusselwort",
            "palabra clave",
            "palavra chave",
        ]
    )


def _pending_reviews(context: Any) -> list[str]:
    return [
        stage
        for stage, review in context.workflow_control.stage_reviews.items()
        if review.status == "pending"
    ]


def _next_safe_action(context: Any) -> str:
    control = context.workflow_control
    pending = _pending_reviews(context)
    if pending:
        return f"review `{pending[0]}` before continuing"
    if control.next_stage:
        return f"run `{control.next_stage}` after confirmation"
    if context.approval is not None and context.approval.status == "approved" and context.execution is None:
        return "execute approved tests after confirmation"
    if control.state == "completed":
        return "inspect final report and archive memory"
    return "inspect current artifacts or workflow status"


def _format_trace(trace: Any | None) -> str:
    if trace is None:
        return "none"
    summary = f" — {trace.summary}" if trace.summary else ""
    return f"`{trace.node_name}` {trace.status}{summary}"


def _format_action(action: ChatAction) -> str:
    target = action.context_id or action.ticket_id or "no target"
    suffix = f" — {action.result_summary}" if action.result_summary else ""
    return f"- `{action.kind}` / `{action.status}` / {target}{suffix}"


def _profile_count(profile: dict[str, Any], key: str) -> Any:
    if key in profile:
        return profile[key]
    summary = profile.get("summary")
    if isinstance(summary, dict) and key in summary:
        return summary[key]
    nested_profile = profile.get("profile")
    if isinstance(nested_profile, dict) and key in nested_profile:
        return nested_profile[key]
    return "unknown"


def _join_or_none(values: list[str] | tuple[str, ...]) -> str:
    return ", ".join(values) if values else "none"


def _lines(*values: str) -> str:
    return chr(10).join(values)
