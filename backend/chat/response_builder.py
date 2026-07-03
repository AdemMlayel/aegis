from __future__ import annotations

from collections import Counter
from typing import Any

from backend.chat.intent_classifier import ClassifiedIntent
from backend.chat.llm_responder import answer_with_llm
from backend.chat.schemas import ChatAction, ChatSession
from backend.chat.system_knowledge import (
    resolve_system_topic,
    system_knowledge_lines,
    system_topics,
)
from backend.integrations.providers import build_provider_catalog
from backend.reference_corpus.profiles import (
    load_execution_evidence_profile,
    load_report_profile,
    load_robot_keyword_registry,
    load_robot_style_profile,
)
from backend.storage.contexts import list_contexts, load_context
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
    if classified.intent == "system_knowledge":
        return _system_knowledge_response(classified.normalized_message)
    if classified.intent == "workflow_start":
        if not ticket_id:
            return "I can start a workflow once a ticket is selected or a ticket ID is provided."
        return f"I can start a controlled workflow for ticket `{ticket_id}`. This action requires confirmation."
    if classified.intent == "workflow_step":
        return _workflow_step_response(context_id)
    if classified.intent == "workflow_status":
        return _workflow_status_response(context_id)
    if classified.intent == "show_stage_output":
        return _show_stage_output_response(context_id, classified.normalized_message)
    if classified.intent == "ticket_question":
        return _ticket_response(ticket_id, context_id)
    if classified.intent == "test_case_suggestion":
        return _test_case_suggestion_response(ticket_id, context_id)
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
    if classified.intent == "self_healing_question":
        return _self_healing_response(context_id)
    if classified.intent == "report_request":
        return _report_response(context_id)
    if classified.intent == "knowledge_question":
        return _knowledge_response(classified.normalized_message)
    if classified.intent == "action_history":
        return _action_history_response(session)
    return _unknown_response(session, classified)


def _help_response() -> str:
    return (
        "I can help you inspect tickets, explain workflow status, review generated Robot artifacts, "
        "explain validation and execution results, summarize investigation/report output, list action history, "
        "check for broken locators / unknown keywords and propose self-healing repairs, "
        "and propose controlled workflow actions. I can also explain the system itself — architecture, "
        "agents, workflow stages, governance, knowledge/RAG, providers, and demo mode. Workflow start, "
        "approval, stage progression, and execution require explicit confirmation."
    )


def _system_knowledge_response(normalized_message: str) -> str:
    topic = resolve_system_topic(normalized_message)
    lines = list(system_knowledge_lines(topic))
    if topic == "overview":
        lines.append(
            f"Topics I can detail: {', '.join(system_topics())}."
        )
    return _lines(*lines)


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
        return _no_active_workflow_response()
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


def _no_active_workflow_response() -> str:
    """Helpful response when no workflow is attached to the chat.

    Looks up the most recent resumable workflow via ``list_contexts`` (ordered
    by ``updated_at DESC``) and, if one exists, tells the user how to resume it.
    Falls back to an actionable static message otherwise.
    """
    try:
        contexts = list_contexts()
    except Exception:
        contexts = []
    resumable = next(
        (
            context
            for context in contexts
            if context.workflow_control.state not in {"completed", "failed"}
        ),
        None,
    )
    if resumable is not None:
        control = resumable.workflow_control
        ticket_id = resumable.ticket.id if resumable.ticket else "unknown"
        return _lines(
            "There's no active workflow in this chat.",
            (
                f"The most recent resumable workflow is `{resumable.context_id}` "
                f"(ticket `{ticket_id}`, state `{control.state}`, "
                f"next stage `{control.next_stage or 'none'}`)."
            ),
            f"Ask me to resume it, e.g. 'resume {resumable.context_id}'.",
            "Or start a new one by selecting a ticket and saying 'analyze <TICKET-ID>'.",
        )
    return (
        "There's no active workflow in this chat. Start one by selecting a ticket "
        "and saying 'analyze <TICKET-ID>', or open an existing workflow from the left panel."
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


_STAGE_ARTIFACTS: tuple[str, ...] = (
    "requirements",
    "coverage",
    "tests",
)

# Map natural keywords in the user's message to the stage whose artifact they
# want rendered. Checked against the normalized (accent/apostrophe-stripped)
# message.
_STAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "requirements": ("requirement", "exigence", "anforderung", "requisito"),
    "coverage": ("coverage", "couverture", "abdeckung", "cobertura"),
    "tests": ("test case", "test cases", "test scenario", "cas de test", "casos"),
}


def _resolve_requested_stage(context: Any, normalized_message: str) -> str | None:
    """Pick which stage's output the user wants to see.

    Priority: an explicit stage keyword in the message wins; otherwise fall back
    to the stage currently pending review (the one they'd be approving); else the
    most recently completed artifact-bearing stage.
    """
    for stage, keywords in _STAGE_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return stage
    pending = _pending_reviews(context)
    for stage in pending:
        if stage in _STAGE_ARTIFACTS:
            return stage
    completed = list(context.workflow_control.completed_stages)
    for stage in reversed(completed):
        if stage in _STAGE_ARTIFACTS:
            return stage
    return None


def _show_stage_output_response(context_id: str | None, normalized_message: str) -> str:
    if not context_id:
        return (
            "Open or start a workflow first, then I can show you a stage's output — "
            "the requirements, coverage plan, or generated test cases."
        )
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."

    stage = _resolve_requested_stage(context, normalized_message)
    if stage is None:
        return _lines(
            "No completed stage output is available to show yet.",
            f"- Current state: `{context.workflow_control.state}`",
            f"- Completed stages: {_join_or_none(context.workflow_control.completed_stages)}",
            "Run a stage first, then ask me to show its output.",
        )

    if stage == "requirements":
        return _render_requirements_output(context)
    if stage == "coverage":
        return _render_coverage_output(context)
    if stage == "tests":
        return _render_test_cases_output(context)
    return f"I don't have a renderer for the `{stage}` stage output yet."


def _render_requirements_output(context: Any) -> str:
    analysis = context.requirement_analysis
    if analysis is None:
        return "The requirements stage has not produced output yet. Run it first."
    checklist = analysis.completeness_checklist
    checklist_items = [
        ("actor identified", checklist.actor_identified),
        ("preconditions defined", checklist.preconditions_defined),
        ("expected outcome specified", checklist.expected_outcome_specified),
        ("error scenarios mentioned", checklist.error_scenarios_mentioned),
        ("data constraints defined", checklist.data_constraints_defined),
        ("performance expectations set", checklist.performance_expectations_set),
    ]
    precondition_lines = [f"  - {item}" for item in analysis.preconditions] or ["  - none"]
    result_lines = [f"  - {item}" for item in analysis.expected_results] or ["  - none"]
    lines = [
        "Requirements stage output:",
        f"- Business action: {analysis.business_action}",
        f"- Domain: `{analysis.domain}` | Actor: `{analysis.actor}`",
        f"- Confidence: {analysis.confidence:.2f}",
        "Preconditions:",
        *precondition_lines,
        "Expected results:",
        *result_lines,
        "Completeness checklist:",
        *(f"  - {label}: {'yes' if ok else 'no'}" for label, ok in checklist_items),
        f"- Missing fields: {_join_or_none(analysis.missing_fields)}",
    ]
    if analysis.clarification_questions:
        lines.append("Clarification questions:")
        lines.extend(f"  - {q}" for q in analysis.clarification_questions)
    if analysis.llm_summary:
        lines.append(f"- LLM summary: {analysis.llm_summary}")
    if analysis.adjudication_notes:
        lines.append("Adjudication (how heuristic + LLM signals were reconciled):")
        lines.extend(f"  - {note}" for note in analysis.adjudication_notes)
    lines.append(
        "If this looks right, approve the requirements stage (approval requires confirmation)."
    )
    return _lines(*lines)


def _render_coverage_output(context: Any) -> str:
    plan = context.coverage_plan
    if plan is None:
        return "The coverage stage has not produced output yet. Run it first."
    matrix_lines = [
        f"  - {req}: {', '.join(cases) if cases else 'no cases mapped'}"
        for req, cases in list(plan.coverage_matrix.items())[:10]
    ]
    lines = [
        "Coverage stage output:",
        f"- Risk level: `{plan.risk_level}` | Business criticality: {plan.business_criticality}/10",
        f"- Estimated automation effort: `{plan.estimated_automation_effort}`",
        f"- Test types required: {_join_or_none(plan.test_types_required)}",
        f"- Prioritization order: {_join_or_none(plan.prioritization_order)}",
        f"- Regression tests to rerun: {_join_or_none(plan.regression_tests_to_rerun)}",
        "Coverage matrix (requirement -> cases):",
        *(matrix_lines or ["  - none"]),
    ]
    if plan.risk_rationale:
        lines.append("Risk rationale:")
        lines.extend(f"  - {item}" for item in plan.risk_rationale[:5])
    lines.append(
        "If this looks right, approve the coverage stage (approval requires confirmation)."
    )
    return _lines(*lines)


def _render_test_cases_output(context: Any) -> str:
    cases = context.test_cases
    if not cases:
        return "The tests stage has not produced test cases yet. Run it first."
    type_counts = Counter(case.type for case in cases)
    lines = [
        f"Tests stage output — {len(cases)} generated test case(s).",
        f"- By type: {dict(type_counts)}",
    ]
    for case in cases[:8]:
        refs = ", ".join(case.requirement_refs) if case.requirement_refs else "none"
        lines.append(
            f"- `{case.id}` [{case.type}/{case.priority}] {case.title} "
            f"(reqs: {refs}, {len(case.steps)} step(s))"
        )
    if len(cases) > 8:
        lines.append(f"- ...and {len(cases) - 8} more.")
    lines.append(
        "If this looks right, approve the tests stage (approval requires confirmation)."
    )
    return _lines(*lines)


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


def _test_case_suggestion_response(ticket_id: str | None, context_id: str | None) -> str:
    ticket = None
    if context_id:
        context = load_context(context_id)
        if context:
            ticket = context.ticket
    if ticket is None and ticket_id:
        ticket = get_ticket_source().fetch(ticket_id)
    if ticket is None:
        return (
            "Select or mention a ticket (e.g. its ID) and I'll suggest functional, "
            "negative, and boundary test cases for it."
        )

    lines = [f"Suggested test cases for `{ticket.id}` — {ticket.title}"]

    # Functional (happy-path) cases — one per acceptance criterion (cap 4).
    if ticket.acceptance_criteria:
        for criterion in ticket.acceptance_criteria[:4]:
            lines.append(f"- [functional] Verify acceptance criterion: {criterion}")
    else:
        lines.append(
            f"- [functional] Verify the happy path for: {ticket.title}"
        )

    # Negative cases — one per validation rule (cap 3).
    if ticket.validation_rules:
        for rule in ticket.validation_rules[:3]:
            lines.append(
                f"- [negative] Exercise invalid/violated rule `{rule.id}`: {rule.description}"
            )
    else:
        lines.append(
            "- [negative] Submit missing/invalid input data and confirm the system "
            "rejects it with a clear error."
        )

    # Boundary cases — derived from input_data / expected_outputs field names.
    if ticket.input_data:
        input_names = ", ".join(datum.name for datum in ticket.input_data[:3])
        lines.append(
            f"- [boundary] Test min/max, empty, and max-length values for input "
            f"field(s): {input_names}"
        )
    if ticket.expected_outputs:
        output_names = ", ".join(ticket.expected_outputs[:3])
        lines.append(
            f"- [boundary] Verify boundary/empty conditions for expected "
            f"output(s): {output_names}"
        )

    lines.append(
        "These are deterministic suggestions derived from the ticket's fields. "
        "Running the real test-generation stage requires starting a workflow."
    )
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
    investigation = context.investigation
    lines = [
        f"Investigation status is `{investigation.status}` with confidence "
        f"{investigation.confidence:.2f} "
        f"(weighted evidence score {investigation.evidence_score:.1f}/100).",
        f"- Evidence items: {len(investigation.evidence_items)}",
        f"- Findings: {len(findings)}",
        f"- Categories: {dict(categories)}",
        f"- Root cause summary: {investigation.root_cause_summary or 'not available'}",
    ]
    if investigation.matched_signals:
        signal_summary = ", ".join(
            f"{hit.signal}({hit.weight})" for hit in investigation.matched_signals[:8]
        )
        lines.append(f"- Weighted signals that fired: {signal_summary}")
    if findings:
        lines.append("Findings (each confidence is Σ weighted signals / budget × 100):")
        for finding in findings[:5]:
            lines.append(
                f"- `{finding.category}`/{finding.severity} "
                f"(score {finding.evidence_score:.1f}/100): {finding.summary}"
            )
            if finding.score_basis:
                lines.append(f"    basis: {finding.score_basis}")
            if finding.matched_signals:
                detail = "; ".join(
                    f"{hit.signal} — {hit.detail}" for hit in finding.matched_signals[:4]
                )
                lines.append(f"    evidence: {detail}")
    return _lines(*lines)


def _self_healing_response(context_id: str | None) -> str:
    if not context_id:
        return (
            "Open or run a workflow first, then I can check for broken locators "
            "and unknown keyword references and propose human-gated repairs."
        )
    context = load_context(context_id)
    if context is None:
        return "I could not find that workflow context."

    healing = context.self_healing
    # If the self-healing stage hasn't been recorded on the context yet, run the
    # detector live against the current automation/execution state so the chat is
    # always answerable. This never modifies a file.
    if healing is None or healing.status == "not_started":
        from backend.tools.self_healing import detect_self_healing

        healing = detect_self_healing(context)

    if not healing.suggestions:
        return _lines(
            "Self-healing scan found no broken locators or unknown keyword references.",
            f"- {healing.summary or 'All keyword references resolve against the registry.'}",
            "Every generated keyword is either a BuiltIn keyword or present in the "
            "sanitized keyword registry.",
        )

    locator = [s for s in healing.suggestions if s.kind == "locator"]
    keyword = [s for s in healing.suggestions if s.kind == "keyword"]
    lines = [
        f"Self-healing detected {len(healing.suggestions)} broken reference(s) "
        f"({len(locator)} locator, {len(keyword)} keyword). "
        "All repairs are suggestions awaiting human approval — no file has been modified.",
    ]
    for suggestion in healing.suggestions[:6]:
        where = ""
        if suggestion.robot_file:
            where = f" in `{suggestion.robot_file}`"
            if suggestion.line:
                where += f":{suggestion.line}"
        lines.append(
            f"- [{suggestion.kind}] broken `{suggestion.broken_reference}`{where}"
        )
        rec = suggestion.recommended
        if rec is not None:
            lines.append(
                f"    -> recommended: `{rec.value}` "
                f"(score {rec.score:.2f}, {rec.stability_label} stability)"
            )
        others = [c for c in suggestion.candidates if c is not rec][:2]
        for cand in others:
            lines.append(f"       alt: `{cand.value}` (score {cand.score:.2f})")
        if suggestion.memory_match:
            lines.append(f"    similar approved fix: {suggestion.memory_match}")
    if len(healing.suggestions) > 6:
        lines.append(f"- ...and {len(healing.suggestions) - 6} more.")
    lines.append(
        "Approving a repair is a separate, confirmation-gated action; the system "
        "suggests, you decide."
    )
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


def _knowledge_response(normalized_message: str = "") -> str:
    """Answer a knowledge/RAG question.

    If the message carries a substantive query (beyond the bare RAG meta-words),
    actually RETRIEVE from the knowledge store and surface the real chunks —
    this is the whole point of having a RAG engine. Only when the message is a
    bare "what's in the knowledge base?" do we fall back to the corpus census.
    """
    query_terms = _knowledge_query_terms(normalized_message)
    if query_terms:
        retrieved = _retrieve_knowledge_chunks(" ".join(query_terms))
        if retrieved:
            return retrieved
        # A real query that retrieved nothing is itself useful information.
        return _lines(
            f"Nothing in the sanitized knowledge corpus matched '{' '.join(query_terms)}'.",
            "The corpus covers requirements completeness, banking/payment risk, Robot "
            "structure, approval governance, and API workflow QA. Try one of those topics, "
            "or ask 'what's in the knowledge base?' for an inventory.",
        )
    return _knowledge_inventory_response()


# RAG meta-words that signal the knowledge intent but carry no query content of
# their own — stripped so only the real subject terms drive retrieval.
_KNOWLEDGE_STOPWORDS: frozenset[str] = frozenset(
    {
        "knowledge", "rag", "corpus", "memory", "sanitized", "base", "vector",
        "what", "whats", "does", "say", "about", "tell", "show", "the", "is",
        "in", "do", "we", "have", "any", "on", "for", "of", "me", "explain",
        "know", "anything", "there", "stored", "store", "retrieve", "search",
        "find", "look", "up", "from", "and", "a", "an", "to", "que", "qui",
    }
)


def _knowledge_query_terms(normalized_message: str) -> list[str]:
    """Extract substantive subject terms from a knowledge question."""
    if not normalized_message:
        return []
    return [
        token
        for token in normalized_message.split()
        if len(token) > 2 and token not in _KNOWLEDGE_STOPWORDS
    ]


def _retrieve_knowledge_chunks(query: str, *, limit: int = 3) -> str | None:
    """Retrieve and format real knowledge chunks for a query, or None.

    Applies a relevance floor: a query with no lexical overlap still gets a
    small non-zero cosine against every chunk, so without a floor an unrelated
    query ('quantum blockchain') would surface low-relevance noise as if it were
    an answer. Below the floor we report 'nothing matched' honestly.
    """
    try:
        from backend.knowledge.local import get_local_knowledge_store

        results = get_local_knowledge_store().search(query=query, limit=limit)
    except Exception:  # noqa: BLE001 - retrieval is best-effort; fall back to inventory.
        return None
    # Keep only results that clear the relevance floor; a query with real lexical
    # overlap scores well above it, pure-cosine-noise sits below.
    results = [r for r in results if r.score >= _KNOWLEDGE_RELEVANCE_FLOOR]
    if not results:
        return None
    lines = [f"From the sanitized knowledge corpus (top {len(results)} for your query):"]
    for result in results:
        matched = ", ".join(result.matched_terms[:5]) if result.matched_terms else "semantic match"
        lines.append(
            f"- [{result.chunk.chunk_id}] {result.chunk.title} "
            f"(relevance {result.score:.2f}; {matched})"
        )
        lines.append(f"    {result.excerpt}")
    lines.append("These are sanitized normalized chunks; raw sensitive input stays quarantined.")
    return _lines(*lines)


# Minimum rerank relevance for a chunk to count as a genuine match. Real
# lexical-overlap hits score ~0.4-0.7; pure cosine-floor noise sits ~0.3 and
# below. Tuned against the seeded corpus (see scripts/probe_rag_vector_quality.py).
_KNOWLEDGE_RELEVANCE_FLOOR = 0.33


def _knowledge_inventory_response() -> str:
    registry = load_robot_keyword_registry()
    style = load_robot_style_profile()
    report = load_report_profile()
    evidence = load_execution_evidence_profile()
    failed_profile = evidence.get("profiles", {}).get("failed", {})
    successful_profile = evidence.get("profiles", {}).get("successful", {})
    knowledge_chunks = _knowledge_chunk_count()
    return _lines(
        "Current safe knowledge grounding uses normalized sanitized profiles only.",
        f"- Knowledge chunks (RAG-retrievable): {knowledge_chunks}",
        f"- Robot keywords: {len(registry.get('keywords', []))}",
        f"- Robot style files analyzed: {_profile_count(style, 'files_analyzed')}",
        f"- Report files analyzed: {_profile_count(report, 'files_analyzed')}",
        f"- Successful execution artifacts: {successful_profile.get('artifact_count', 0)}",
        f"- Failed execution artifacts: {failed_profile.get('artifact_count', 0)}",
        "Ask about a topic (e.g. 'what does the corpus say about banking risk?') to "
        "retrieve the actual chunks. Raw sensitive input remains quarantined.",
    )


def _knowledge_chunk_count() -> int:
    try:
        from backend.knowledge.local import get_local_knowledge_store

        return len(get_local_knowledge_store().list_chunks())
    except Exception:  # noqa: BLE001 - inventory is best-effort.
        return 0


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


def _unknown_response(session: ChatSession, classified: ClassifiedIntent) -> str:
    """Answer an unrecognized question.

    Tries the optional LLM responder first (grounded with system knowledge + RAG)
    when enabled; otherwise — or on any LLM failure — returns the deterministic
    fallback. The LLM path is informational only and never proposes actions.
    """
    llm_answer = answer_with_llm(classified.normalized_message or "")
    if llm_answer:
        return llm_answer
    return _fallback_response()


def _fallback_response() -> str:
    return (
        "I did not map that to a safe workflow action yet. I can answer questions about tickets, "
        "workflow status, Robot artifacts, validation, execution, investigation, reports, providers, "
        "action history, and safe corpus grounding. I can also explain the system itself — try "
        "\"explain the architecture\", \"what agents are there\", \"what are the workflow stages\", "
        "or \"how does governance work\"."
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
