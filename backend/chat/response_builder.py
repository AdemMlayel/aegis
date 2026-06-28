from __future__ import annotations

from collections import Counter

from backend.chat.intent_classifier import ClassifiedIntent
from backend.chat.schemas import ChatSession
from backend.integrations.providers import build_provider_catalog
from backend.reference_corpus.profiles import load_execution_evidence_profile, load_robot_keyword_registry, load_report_profile, load_robot_style_profile
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
        return _artifact_response(context_id)
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
    return _fallback_response()


def _help_response() -> str:
    return (
        "I can help you inspect tickets, explain workflow status, review generated Robot artifacts, "
        "explain validation and execution results, and propose controlled workflow actions. "
        "Execution, approval, regeneration, and workflow-start actions require confirmation."
    )


def _system_response() -> str:
    catalog = build_provider_catalog().as_dict(include_external=True)
    selected = catalog.get("selected", [])
    selected_lines = [
        f"- {item['kind']}: `{item['selected']}` ({item['status']})"
        for item in selected
    ]
    return (
        "Current AegisQA runtime is local/demo-first.\n"
        f"- Environment: `{catalog.get('environment')}`\n"
        f"- Deterministic demo mode: `{catalog.get('deterministic_demo_mode')}`\n"
        f"- External connectors enabled: `{catalog.get('external_connectors_enabled')}`\n"
        "Selected providers:\n"
        + "\n".join(selected_lines)
    )


def _workflow_step_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can run or explain the next stage."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    control = context.workflow_control
    if control.state == "waiting_review":
        return "The workflow is waiting for a review decision. Approve or request changes before resuming."
    if control.next_stage is None:
        return "The workflow has no remaining stage to run."
    return f"The next stage is `{control.next_stage}`. Running it is a controlled action and requires confirmation."


def _workflow_status_response(context_id: str | None) -> str:
    if not context_id:
        return "No workflow is currently attached to this chat session."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    control = context.workflow_control
    completed = ", ".join(control.completed_stages) or "none yet"
    pending_reviews = [
        stage for stage, review in control.stage_reviews.items() if review.status == "pending"
    ]
    pending_text = ", ".join(pending_reviews) if pending_reviews else "none"
    return (
        f"Workflow `{context.context_id}` is `{control.state}`.\n"
        f"- Ticket: `{context.ticket.id if context.ticket else 'none'}`\n"
        f"- Current workflow status: `{context.workflow_status}`\n"
        f"- Next stage: `{control.next_stage or 'none'}`\n"
        f"- Completed stages: {completed}\n"
        f"- Pending reviews: {pending_text}"
    )


def _ticket_response(ticket_id: str | None, context_id: str | None) -> str:
    ticket = None
    if context_id:
        context = load_context(context_id)
        ticket = context.ticket if context else None
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

    risks = ticket.risks_or_constraints[:4]
    return (
        f"Ticket `{ticket.id}` — {ticket.title}\n"
        f"- Priority: `{ticket.priority}`\n"
        f"- Scope items: {len(ticket.test_scope)}\n"
        f"- Acceptance criteria: {len(ticket.acceptance_criteria)}\n"
        f"- Validation rules: {len(ticket.validation_rules)}\n"
        f"- Missing/weak areas: {', '.join(missing) if missing else 'no major structural gaps detected'}\n"
        f"- Key risks: {', '.join(risks) if risks else 'none declared'}"
    )


def _artifact_response(context_id: str | None) -> str:
    if not context_id:
        return "Open or start a workflow first, then I can explain generated Robot artifacts."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if not context.automation:
        return "No Robot automation has been generated yet."
    registry = load_robot_keyword_registry()
    style = load_robot_style_profile()
    files = [block.robot_file for block in context.automation.values()]
    valid = sum(1 for block in context.automation.values() if block.validation.dry_run_passed is True)
    return (
        f"This workflow has {len(context.automation)} generated Robot artifact(s).\n"
        f"- Files: {', '.join(files[:5])}\n"
        f"- Validation dry-run passed: {valid}/{len(context.automation)}\n"
        f"- Corpus keyword registry size: {len(registry.get('keywords', []))}\n"
        f"- Robot style source files analyzed: {style.get('files_analyzed', 'unknown')}"
    )


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
        test_id for test_id, block in context.automation.items()
        if block.validation.dry_run_passed is False
    ]
    return (
        f"Validation status is `{summary.status}`.\n"
        f"- Total checks: {summary.total_checks}\n"
        f"- Passed checks: {summary.passed_checks}\n"
        f"- Failed checks: {summary.failed_checks}\n"
        f"- Failed artifacts: {', '.join(failed) if failed else 'none'}"
    )


def _approval_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can inspect approval state."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    pending = [
        stage for stage, review in context.workflow_control.stage_reviews.items()
        if review.status == "pending"
    ]
    if pending:
        return f"The workflow is waiting for review on `{pending[0]}`. Approval requires confirmation."
    if context.approval:
        return f"Package approval status is `{context.approval.status}`."
    return "No approval package exists yet. Continue the workflow until the approval stage."


def _execution_response(context_id: str | None) -> str:
    if not context_id:
        return "Select a workflow first, then I can inspect or request execution."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.execution:
        summary = context.execution.summary
        return (
            f"Execution status is `{context.execution.status}`.\n"
            f"- Passed: {summary.passed}\n"
            f"- Failed: {summary.failed}\n"
            f"- Skipped: {summary.skipped}"
        )
    if context.approval is None or context.approval.status != "approved":
        return "Execution is not available yet. The workflow package must be approved first."
    return "The workflow is approved and can be executed through the configured adapter after confirmation."


def _investigation_response(context_id: str | None) -> str:
    if not context_id:
        return "Select an executed workflow first, then I can explain investigation findings."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    profile = load_execution_evidence_profile()
    if context.investigation is None:
        return (
            "No investigation is available yet. Execute the workflow first.\n"
            f"- Failed execution example available in corpus: {profile.get('has_failed_example', False)}"
        )
    findings = context.investigation.findings
    categories = Counter(finding.category for finding in findings)
    return (
        f"Investigation status is `{context.investigation.status}` with confidence {context.investigation.confidence:.2f}.\n"
        f"- Findings: {len(findings)}\n"
        f"- Categories: {dict(categories)}\n"
        f"- Root cause summary: {context.investigation.root_cause_summary or 'not available'}"
    )


def _report_response(context_id: str | None) -> str:
    profile = load_report_profile()
    if not context_id:
        return "Select a workflow first, then I can summarize its report."
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."
    if context.reports is None:
        return "The report has not been generated yet."
    return (
        f"Report is available for workflow `{context.context_id}`.\n"
        f"- Highest risk: `{context.reports.highest_risk}`\n"
        f"- Executive summary: {context.reports.executive_summary}\n"
        f"- Report corpus files analyzed: {profile.get('files_analyzed', 'unknown')}"
    )


def _knowledge_response() -> str:
    registry = load_robot_keyword_registry()
    style = load_robot_style_profile()
    report = load_report_profile()
    evidence = load_execution_evidence_profile()
    return (
        "Current safe knowledge grounding uses normalized sanitized profiles only.\n"
        f"- Robot keywords: {len(registry.get('keywords', []))}\n"
        f"- Robot style files analyzed: {style.get('files_analyzed', 'unknown')}\n"
        f"- Report files analyzed: {report.get('files_analyzed', 'unknown')}\n"
        f"- Successful execution example: {evidence.get('has_successful_example', False)}\n"
        f"- Failed execution example: {evidence.get('has_failed_example', False)}"
    )


def _fallback_response() -> str:
    return (
        "I did not map that to a safe workflow action yet. I can answer questions about tickets, "
        "workflow status, Robot artifacts, validation, execution, investigation, reports, providers, and safe corpus grounding."
    )
