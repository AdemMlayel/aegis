from __future__ import annotations

from backend.chat.schemas import ChatActionKind, ChatIntent
from backend.security import Capability, Principal


ACTION_CAPABILITIES: dict[ChatActionKind, Capability] = {
    "start_workflow": Capability.START_WORKFLOW,
    "run_next_stage": Capability.START_WORKFLOW,
    "approve_pending_stage": Capability.APPROVE_WORKFLOW,
    "execute_workflow": Capability.EXECUTE_WORKFLOW,
}

READ_ONLY_INTENTS: set[ChatIntent] = {
    "system_question",
    "ticket_question",
    "test_case_suggestion",
    "workflow_status",
    "show_stage_output",
    "artifact_question",
    "validation_question",
    "investigation_question",
    "self_healing_question",
    "report_request",
    "knowledge_question",
    "action_history",
    "help",
    "unknown",
}

MUTATING_INTENTS: set[ChatIntent] = {
    "workflow_start",
    "workflow_step",
    "approval_request",
    "execution_request",
}


def capability_for_action(kind: ChatActionKind) -> Capability:
    return ACTION_CAPABILITIES[kind]


def ensure_action_allowed(kind: ChatActionKind, principal: Principal) -> None:
    capability = capability_for_action(kind)
    if not principal.can(capability):
        raise PermissionError(f"Capability required: {capability}")


def is_read_only_intent(intent: ChatIntent) -> bool:
    return intent in READ_ONLY_INTENTS
