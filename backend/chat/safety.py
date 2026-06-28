from __future__ import annotations

from backend.chat.schemas import ChatActionKind
from backend.security import Capability, Principal


ACTION_CAPABILITIES: dict[ChatActionKind, Capability] = {
    "start_workflow": Capability.START_WORKFLOW,
    "resume_workflow": Capability.START_WORKFLOW,
    "run_next_stage": Capability.START_WORKFLOW,
    "approve_pending_stage": Capability.APPROVE_WORKFLOW,
    "execute_workflow": Capability.EXECUTE_WORKFLOW,
}

READ_ONLY_INTENTS = {
    "system_question",
    "ticket_question",
    "workflow_status",
    "artifact_question",
    "validation_question",
    "investigation_question",
    "report_request",
    "knowledge_question",
    "help",
    "unknown",
}


def capability_for_action(kind: ChatActionKind) -> Capability:
    return ACTION_CAPABILITIES[kind]


def ensure_action_allowed(kind: ChatActionKind, principal: Principal) -> None:
    capability = capability_for_action(kind)
    if not principal.can(capability):
        raise PermissionError(f"Capability required: {capability}")
