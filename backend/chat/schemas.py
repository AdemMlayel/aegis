from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import StrictModel, utc_now


ChatIntent = Literal[
    "system_question",
    "system_knowledge",
    "ticket_question",
    "test_case_suggestion",
    "workflow_start",
    "workflow_status",
    "workflow_step",
    "show_stage_output",
    "artifact_question",
    "validation_question",
    "approval_request",
    "execution_request",
    "investigation_question",
    "self_healing_question",
    "report_request",
    "knowledge_question",
    "action_history",
    "ticket_intake",
    "help",
    "unknown",
]

ChatActionKind = Literal[
    "start_workflow",
    "run_next_stage",
    "approve_pending_stage",
    "execute_workflow",
]

ChatActionStatus = Literal["pending_confirmation", "completed", "cancelled", "blocked"]
ChatMessageRole = Literal["user", "assistant", "system"]


class ChatAction(StrictModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: ChatActionKind
    label: str
    description: str
    requires_confirmation: bool = True
    status: ChatActionStatus = "pending_confirmation"
    context_id: str | None = None
    ticket_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    result_summary: str | None = None


class ChatMessage(StrictModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: ChatMessageRole
    content: str
    intent: ChatIntent | None = None
    actions: list[ChatAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ChatSession(StrictModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_by: str = "local-user"
    title: str = "AegisQA Copilot Session"
    context_id: str | None = None
    ticket_id: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    pending_actions: list[ChatAction] = Field(default_factory=list)
    action_history: list[ChatAction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def append_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        for action in message.actions:
            self._record_action(action)
        self.updated_at = utc_now()

    def replace_action(self, action: ChatAction) -> None:
        self.action_history = [
            action if item.action_id == action.action_id else item
            for item in self.action_history
        ]
        for message in self.messages:
            message.actions = [
                action if item.action_id == action.action_id else item
                for item in message.actions
            ]
        self.pending_actions = [
            item for item in self.action_history if item.status == "pending_confirmation"
        ]
        self.updated_at = utc_now()

    def find_action(self, action_id: str) -> ChatAction | None:
        for action in self.action_history:
            if action.action_id == action_id:
                return action
        # Backward compatibility for old persisted sessions created before
        # action_history existed.
        for action in self.pending_actions:
            if action.action_id == action_id:
                return action
        for message in self.messages:
            for action in message.actions:
                if action.action_id == action_id:
                    return action
        return None

    def _record_action(self, action: ChatAction) -> None:
        existing_index = next(
            (
                index
                for index, item in enumerate(self.action_history)
                if item.action_id == action.action_id
            ),
            None,
        )
        if existing_index is None:
            self.action_history.append(action)
        else:
            self.action_history[existing_index] = action
        self.pending_actions = [
            item for item in self.action_history if item.status == "pending_confirmation"
        ]


class CreateChatSessionRequest(StrictModel):
    created_by: str = Field(default="local-user", min_length=1)
    context_id: str | None = None
    ticket_id: str | None = None
    title: str | None = None


class CreateChatSessionResponse(StrictModel):
    session: ChatSession


class ChatMessageRequest(StrictModel):
    actor: str = Field(default="local-user", min_length=1)
    message: str = Field(min_length=1, max_length=10_000)
    context_id: str | None = None
    ticket_id: str | None = None


class ChatTicketIntakeRequest(StrictModel):
    actor: str = Field(default="local-user", min_length=1)
    description: str | None = Field(default=None, max_length=100_000)
    file_name: str | None = Field(default=None, max_length=255)
    file_content: str | None = Field(default=None, max_length=100_000)
    content_type: str | None = Field(default=None, max_length=120)


class ChatMessageResponse(StrictModel):
    session: ChatSession
    message: ChatMessage


class ListChatSessionsResponse(StrictModel):
    sessions: list[ChatSession]


class ChatActionHistoryResponse(StrictModel):
    actions: list[ChatAction]


class ConfirmChatActionRequest(StrictModel):
    actor: str = Field(default="local-user", min_length=1)


class ConfirmChatActionResponse(StrictModel):
    session: ChatSession
    action: ChatAction
    message: ChatMessage


class CancelChatActionRequest(StrictModel):
    actor: str = Field(default="local-user", min_length=1)


class CancelChatActionResponse(StrictModel):
    session: ChatSession
    action: ChatAction
    message: ChatMessage
