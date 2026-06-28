from __future__ import annotations

from backend.chat.intent_classifier import ClassifiedIntent
from backend.chat.schemas import ChatAction, ChatSession
from backend.storage.contexts import load_context


def plan_actions(
    *,
    session: ChatSession,
    classified: ClassifiedIntent,
    message_context_id: str | None = None,
    message_ticket_id: str | None = None,
) -> list[ChatAction]:
    context_id = classified.context_id or message_context_id or session.context_id
    ticket_id = classified.ticket_id or message_ticket_id or session.ticket_id

    if classified.intent == "workflow_start" and ticket_id:
        return [
            ChatAction(
                kind="start_workflow",
                label="Start analysis",
                description=f"Create an approval-required workflow session for ticket {ticket_id}.",
                ticket_id=ticket_id,
                payload={"mode": "approval_required"},
            )
        ]

    if classified.intent == "workflow_step" and context_id:
        return [
            ChatAction(
                kind="run_next_stage",
                label="Run next stage",
                description="Run the next deterministic workflow stage and pause again at the stage boundary.",
                context_id=context_id,
            )
        ]

    if classified.intent == "approval_request" and context_id:
        context = load_context(context_id)
        pending = []
        if context is not None:
            pending = [
                stage
                for stage, review in context.workflow_control.stage_reviews.items()
                if review.status == "pending"
            ]
        if pending:
            stage = pending[0]
            return [
                ChatAction(
                    kind="approve_pending_stage",
                    label=f"Approve {stage}",
                    description=f"Approve the currently pending {stage} stage review.",
                    context_id=context_id,
                    payload={"stage": stage},
                )
            ]

    if classified.intent == "execution_request" and context_id:
        return [
            ChatAction(
                kind="execute_workflow",
                label="Execute tests",
                description="Execute the approved workflow through the configured execution adapter.",
                context_id=context_id,
            )
        ]

    return []
