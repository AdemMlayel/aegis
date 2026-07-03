from __future__ import annotations

from backend.chat.action_planner import plan_actions
from backend.chat.intent_classifier import classify_chat_intent
from backend.chat.intent_preamble import interpreted_intent_preamble
from backend.chat.response_builder import build_assistant_response
from backend.chat.safety import ensure_action_allowed
from backend.chat.schemas import (
    ChatAction,
    ChatMessage,
    ChatSession,
    ChatTicketIntakeRequest,
    CreateChatSessionRequest,
)
from backend.chat.ticket_intake import TicketIntakeResult, intake_ticket_from_chat
from backend.config.settings import settings
from backend.graph.state import IntelligenceConfigBlock, utc_now
from backend.graph.workflow import run_post_approval_workflow
from backend.security import Capability, Principal
from backend.storage.audit import append_audit_event
from backend.storage.contexts import load_context, save_context
from backend.tickets import get_ticket_source
from backend.services.workflow_control import (
    WorkflowControlError,
    create_workflow_session,
    resume_workflow_session,
    review_workflow_stage,
)
from backend.chat.session_store import list_chat_sessions, load_chat_session, save_chat_session


class ChatSessionNotFound(Exception):
    pass


class ChatActionNotFound(Exception):
    pass


class ChatActionConflict(Exception):
    pass


class ChatActionDenied(Exception):
    pass


def create_chat_session(request: CreateChatSessionRequest) -> ChatSession:
    session = ChatSession(
        created_by=request.created_by,
        title=request.title or "AegisQA Copilot Session",
        context_id=request.context_id,
        ticket_id=request.ticket_id,
    )
    greeting = ChatMessage(
        role="assistant",
        content=(
            "AegisQA Copilot is ready. I can answer questions about the system, "
            "tickets, workflow status, generated Robot artifacts, validation, execution, "
            "investigation, reports, and safe corpus grounding. Controlled actions will ask for confirmation."
        ),
        intent="help",
        metadata={"source": "chat_session_created"},
    )
    session.append_message(greeting)
    return save_chat_session(session)




def list_recent_chat_sessions(
    *,
    limit: int = 50,
    query: str | None = None,
    context_id: str | None = None,
    ticket_id: str | None = None,
) -> list[ChatSession]:
    return list_chat_sessions(
        limit=max(1, min(limit, 100)),
        query=query,
        context_id=context_id,
        ticket_id=ticket_id,
    )

def read_chat_session(session_id: str) -> ChatSession:
    session = load_chat_session(session_id)
    if session is None:
        raise ChatSessionNotFound("Chat session was not found")
    return session


def handle_chat_message(
    *,
    session_id: str,
    actor: str,
    message: str,
    principal: Principal,
    context_id: str | None = None,
    ticket_id: str | None = None,
) -> tuple[ChatSession, ChatMessage]:
    session = read_chat_session(session_id)
    if context_id:
        session.context_id = context_id
    if ticket_id:
        session.ticket_id = ticket_id

    user_message = ChatMessage(
        role="user",
        content=message,
        metadata={"actor": actor},
    )
    session.append_message(user_message)

    classified = classify_chat_intent(message)
    if classified.intent == "ticket_intake":
        if not principal.can(Capability.WRITE_TICKETS):
            assistant_message = ChatMessage(
                role="assistant",
                content="I can create a ticket from that scenario, but your current role does not have ticket-write permission.",
                intent="ticket_intake",
                metadata={
                    "confidence": classified.confidence,
                    "detected_language": classified.detected_language,
                    "permission": "write:tickets",
                },
            )
            session.append_message(assistant_message)
            save_chat_session(session)
            return session, assistant_message
        result = intake_ticket_from_chat(
            actor=principal.user_id,
            session_id=session_id,
            description=message,
        )
        actions = _intake_actions(result=result, principal=principal)
        assistant_message = ChatMessage(
            role="assistant",
            content=_ticket_intake_response(result),
            intent="ticket_intake",
            actions=actions,
            metadata={
                "confidence": classified.confidence,
                "detected_language": classified.detected_language,
                "source": "ticket_intake",
                "ticket_id": result.ticket.id,
                "assessment": result.assessment.model_dump(mode="json"),
                "redaction_count": result.redaction_count,
            },
        )
        session.ticket_id = result.ticket.id
        session.append_message(assistant_message)
        _audit_ticket_intake(
            actor=principal.user_id,
            session=session,
            result=result,
        )
        save_chat_session(session)
        return session, assistant_message

    planned_actions = plan_actions(
        session=session,
        classified=classified,
        message_context_id=context_id,
        message_ticket_id=ticket_id,
    )
    for action in planned_actions:
        try:
            ensure_action_allowed(action.kind, principal)
        except PermissionError:
            action.status = "blocked"
            action.result_summary = "Current user does not have permission for this action."

    response_text = build_assistant_response(
        session=session,
        classified=classified,
        message_context_id=context_id,
        message_ticket_id=ticket_id,
    )
    # G1 (Part B1): when a mutating action is queued for confirmation, lead with
    # a plain-language statement of what the copilot understood and what it will
    # ask the orchestrator to do. Only pending (non-blocked) actions get a
    # preamble -- a blocked action already explains itself via result_summary.
    pending_actions = [
        action
        for action in planned_actions
        if action.status == "pending_confirmation"
    ]
    preamble = interpreted_intent_preamble(pending_actions)
    if preamble:
        response_text = f"{preamble}\n\n{response_text}"
    assistant_message = ChatMessage(
        role="assistant",
        content=response_text,
        intent=classified.intent,
        actions=planned_actions,
        metadata={
            "confidence": classified.confidence,
            "detected_language": classified.detected_language,
            "context_id": classified.context_id or context_id or session.context_id,
            "ticket_id": classified.ticket_id or ticket_id or session.ticket_id,
        },
    )
    session.append_message(assistant_message)
    save_chat_session(session)
    return session, assistant_message


def handle_chat_ticket_intake(
    *,
    session_id: str,
    request: ChatTicketIntakeRequest,
    principal: Principal,
) -> tuple[ChatSession, ChatMessage]:
    if not principal.can(Capability.WRITE_TICKETS):
        raise PermissionError("Capability required: write:tickets")

    session = read_chat_session(session_id)
    result = intake_ticket_from_chat(
        actor=principal.user_id,
        session_id=session_id,
        description=request.description,
        file_name=request.file_name,
        file_content=request.file_content,
    )

    source_label = request.file_name or "pasted description"
    user_message = ChatMessage(
        role="user",
        content=f"Uploaded test scenario for intake: {source_label}",
        metadata={
            "actor": principal.user_id,
            "source": "ticket_intake",
            "file_name": request.file_name,
            "content_type": request.content_type,
        },
    )
    session.append_message(user_message)

    actions = _intake_actions(result=result, principal=principal)
    assistant_message = ChatMessage(
        role="assistant",
        content=_ticket_intake_response(result),
        intent="ticket_intake",
        actions=actions,
        metadata={
            "source": "ticket_intake",
            "ticket_id": result.ticket.id,
            "assessment": result.assessment.model_dump(mode="json"),
            "redaction_count": result.redaction_count,
        },
    )
    session.ticket_id = result.ticket.id
    session.append_message(assistant_message)
    _audit_ticket_intake(
        actor=principal.user_id,
        session=session,
        result=result,
    )
    save_chat_session(session)
    return session, assistant_message


def confirm_chat_action(
    *,
    session_id: str,
    action_id: str,
    actor: str,
    principal: Principal,
) -> tuple[ChatSession, ChatAction, ChatMessage]:
    session = read_chat_session(session_id)
    action = session.find_action(action_id)
    if action is None:
        raise ChatActionNotFound("Chat action was not found")
    if action.status != "pending_confirmation":
        raise ChatActionConflict(f"Chat action is {action.status}")

    try:
        ensure_action_allowed(action.kind, principal)
    except PermissionError as exc:
        raise ChatActionDenied(str(exc)) from exc

    try:
        result_summary = _execute_action(action=action, session=session, actor=actor)
    except WorkflowControlError as exc:
        action.status = "blocked"
        action.completed_at = utc_now()
        action.result_summary = str(exc)
        session.replace_action(action)
        message = ChatMessage(
            role="assistant",
            content=f"Action could not be completed: {exc}",
            metadata={"action_id": action.action_id, "action_kind": action.kind},
        )
        session.append_message(message)
        save_chat_session(session)
        return session, action, message

    action.status = "completed"
    action.completed_at = utc_now()
    action.result_summary = result_summary
    session.replace_action(action)
    message = ChatMessage(
        role="assistant",
        content=result_summary,
        metadata={"action_id": action.action_id, "action_kind": action.kind},
    )
    session.append_message(message)
    save_chat_session(session)
    return session, action, message


def _intake_actions(
    *,
    result: TicketIntakeResult,
    principal: Principal,
) -> list[ChatAction]:
    if not result.assessment.automatable:
        return []
    action = ChatAction(
        kind="start_workflow",
        label="Start workflow from uploaded ticket",
        description=(
            f"Create an approval-required workflow session for sanitized ticket "
            f"{result.ticket.id}."
        ),
        ticket_id=result.ticket.id,
        payload={
            "mode": "approval_required",
            "source": "chat_ticket_intake",
            "assessment": result.assessment.model_dump(mode="json"),
        },
    )
    try:
        ensure_action_allowed(action.kind, principal)
    except PermissionError:
        action.status = "blocked"
        action.result_summary = "Current user does not have permission to start workflows."
    return [action]


def _audit_ticket_intake(
    *,
    actor: str,
    session: ChatSession,
    result: TicketIntakeResult,
) -> None:
    append_audit_event(
        actor=actor,
        event_type="chat_ticket_intake",
        summary="Chat copilot created a sanitized ticket from scenario input.",
        metadata={
            "session_id": session.session_id,
            "ticket_id": result.ticket.id,
            "automatable": result.assessment.automatable,
            "readiness": result.assessment.readiness,
            "redaction_count": result.redaction_count,
        },
    )


def _ticket_intake_response(result: TicketIntakeResult) -> str:
    assessment = result.assessment
    status_line = (
        "I can automate this scenario."
        if assessment.automatable
        else "This scenario is not ready for automation yet."
    )
    lines = [
        f"Created sanitized ticket `{result.ticket.id}` from the uploaded scenario.",
        f"- Title: {result.ticket.title}",
        f"- Automation readiness: `{assessment.readiness}`",
        f"- Confidence: {assessment.confidence:.2f}",
        f"- Redactions applied before storage: {result.redaction_count}",
        f"- Recommended tools: {_join_or_none(assessment.recommended_tools)}",
        status_line,
    ]
    if assessment.reasons:
        lines.append("Signals found:")
        lines.extend(f"- {reason}" for reason in assessment.reasons[:6])
    if assessment.missing_information:
        lines.append("Missing or weak information:")
        lines.extend(f"- {item}" for item in assessment.missing_information[:6])
    if assessment.blockers:
        lines.append("Automation blockers:")
        lines.extend(f"- {item}" for item in assessment.blockers[:6])
    if assessment.automatable:
        lines.append("Confirm the proposed action to create the workflow session.")
    else:
        lines.append(
            "Add the missing details, then upload or paste the refined scenario again."
        )
    return "\n".join(lines)


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def cancel_chat_action(
    *,
    session_id: str,
    action_id: str,
    actor: str,
) -> tuple[ChatSession, ChatAction, ChatMessage]:
    session = read_chat_session(session_id)
    action = session.find_action(action_id)
    if action is None:
        raise ChatActionNotFound("Chat action was not found")
    if action.status != "pending_confirmation":
        raise ChatActionConflict(f"Chat action is {action.status}")

    action.status = "cancelled"
    action.completed_at = utc_now()
    action.result_summary = f"Cancelled by {actor}."
    session.replace_action(action)
    message = ChatMessage(
        role="assistant",
        content=f"Action `{action.label}` was cancelled. No workflow change was applied.",
        metadata={"action_id": action.action_id, "action_kind": action.kind},
    )
    session.append_message(message)
    save_chat_session(session)
    return session, action, message


def _execute_action(*, action: ChatAction, session: ChatSession, actor: str) -> str:
    if action.kind == "start_workflow":
        if not action.ticket_id:
            raise ChatActionConflict("No ticket is attached to this action")
        ticket = get_ticket_source().fetch(action.ticket_id)
        if ticket is None:
            raise ChatActionConflict("Ticket was not found")
        context = create_workflow_session(
            created_by=actor,
            ticket=ticket,
            intelligence_config=IntelligenceConfigBlock(
                llm_provider=settings.default_llm_provider,
                embedding_provider=settings.default_embedding_provider,
            ),
            mode=action.payload.get("mode", "approval_required"),
        )
        session.context_id = context.context_id
        session.ticket_id = ticket.id
        action.context_id = context.context_id
        append_audit_event(
            actor=actor,
            event_type="workflow_control",
            summary="Chat copilot created workflow session.",
            metadata={
                "session_id": session.session_id,
                "action_id": action.action_id,
                "context_id": context.context_id,
                "ticket_id": ticket.id,
            },
        )
        return (
            f"Workflow session `{context.context_id}` was created for ticket `{ticket.id}`. "
            f"The next stage is `{context.workflow_control.next_stage}`."
        )

    if action.kind == "run_next_stage":
        context_id = _require_context_id(action, session)
        context = resume_workflow_session(
            context_id=context_id,
            actor=actor,
            single_step=True,
        )
        session.context_id = context.context_id
        return (
            f"Workflow `{context.context_id}` advanced. "
            f"State: `{context.workflow_control.state}`. "
            f"Next stage: `{context.workflow_control.next_stage or 'none'}`."
        )

    if action.kind == "approve_pending_stage":
        context_id = _require_context_id(action, session)
        stage = action.payload.get("stage")
        if not isinstance(stage, str):
            raise ChatActionConflict("No stage is attached to this approval action")
        context = review_workflow_stage(
            context_id=context_id,
            stage=stage,  # type: ignore[arg-type]
            decision="approve",
            reviewed_by=actor,
            comment="Approved through AegisQA Copilot confirmation.",
        )
        session.context_id = context.context_id
        return (
            f"Stage `{stage}` was approved. "
            f"Workflow state is `{context.workflow_control.state}` and next stage is `{context.workflow_control.next_stage or 'none'}`."
        )

    if action.kind == "execute_workflow":
        context_id = _require_context_id(action, session)
        context = load_context(context_id)
        if context is None:
            raise ChatActionConflict("Workflow context was not found")
        if context.approval is None or context.approval.status != "approved":
            raise ChatActionConflict("Workflow must be package-approved before execution")
        context = run_post_approval_workflow(
            context,
            requested_by=actor,
            adapter=settings.default_execution_adapter,
            env="local",
        )
        save_context(context)
        session.context_id = context.context_id
        execution = context.execution
        append_audit_event(
            actor=actor,
            event_type="execution_completed",
            summary="Chat copilot executed approved workflow.",
            metadata={
                "session_id": session.session_id,
                "action_id": action.action_id,
                "context_id": context.context_id,
                "execution_status": execution.status if execution else None,
            },
        )
        return (
            f"Workflow `{context.context_id}` was executed through `{settings.default_execution_adapter}`. "
            f"Execution status: `{execution.status if execution else 'unknown'}`."
        )

    raise ChatActionConflict(f"Unsupported chat action: {action.kind}")


def _require_context_id(action: ChatAction, session: ChatSession) -> str:
    context_id = action.context_id or session.context_id
    if not context_id:
        raise ChatActionConflict("No workflow context is attached to this action")
    return context_id
