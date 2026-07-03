from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.chat.schemas import (
    CancelChatActionRequest,
    CancelChatActionResponse,
    ChatActionHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConfirmChatActionRequest,
    ConfirmChatActionResponse,
    ListChatSessionsResponse,
    CreateChatSessionRequest,
    CreateChatSessionResponse,
    ChatSession,
)
from backend.chat.service import (
    ChatActionConflict,
    ChatActionDenied,
    ChatActionNotFound,
    ChatSessionNotFound,
    cancel_chat_action,
    confirm_chat_action,
    create_chat_session,
    handle_chat_message,
    list_recent_chat_sessions,
    read_chat_session,
)
from backend.security import Principal, get_current_principal


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/sessions",
    response_model=CreateChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    request: CreateChatSessionRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> CreateChatSessionResponse:
    return CreateChatSessionResponse(session=create_chat_session(request))


@router.get("/sessions", response_model=ListChatSessionsResponse)
def list_sessions(
    principal: Annotated[Principal, Depends(get_current_principal)],
    limit: int = 50,
    query: str | None = None,
    context_id: str | None = None,
    ticket_id: str | None = None,
) -> ListChatSessionsResponse:
    return ListChatSessionsResponse(
        sessions=list_recent_chat_sessions(
            limit=limit,
            query=query,
            context_id=context_id,
            ticket_id=ticket_id,
        )
    )


@router.get("/sessions/{session_id}", response_model=ChatSession)
def get_session(
    session_id: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ChatSession:
    try:
        return read_chat_session(session_id)
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/actions", response_model=ChatActionHistoryResponse)
def get_session_actions(
    session_id: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ChatActionHistoryResponse:
    try:
        session = read_chat_session(session_id)
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ChatActionHistoryResponse(actions=session.action_history)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def create_message(
    session_id: str,
    request: ChatMessageRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ChatMessageResponse:
    try:
        session, message = handle_chat_message(
            session_id=session_id,
            actor=principal.user_id,
            message=request.message,
            context_id=request.context_id,
            ticket_id=request.ticket_id,
            principal=principal,
        )
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ChatMessageResponse(session=session, message=message)


@router.post(
    "/sessions/{session_id}/actions/{action_id}/confirm",
    response_model=ConfirmChatActionResponse,
)
def confirm_action(
    session_id: str,
    action_id: str,
    request: ConfirmChatActionRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ConfirmChatActionResponse:
    try:
        session, action, message = confirm_chat_action(
            session_id=session_id,
            action_id=action_id,
            actor=principal.user_id,
            principal=principal,
        )
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ChatActionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ChatActionDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ChatActionConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ConfirmChatActionResponse(session=session, action=action, message=message)

@router.post(
    "/sessions/{session_id}/actions/{action_id}/cancel",
    response_model=CancelChatActionResponse,
)
def cancel_action(
    session_id: str,
    action_id: str,
    request: CancelChatActionRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> CancelChatActionResponse:
    try:
        session, action, message = cancel_chat_action(
            session_id=session_id,
            action_id=action_id,
            actor=principal.user_id,
        )
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ChatActionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ChatActionConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CancelChatActionResponse(session=session, action=action, message=message)

