from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    actor: str
    organization_id: str


@dataclass(frozen=True)
class AgentExecutionContext:
    agent_id: str
    agent_name: str
    context_id: str | None
    skill_name: str | None = None
    allowed_tools: tuple[str, ...] = ()


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "aegisqa_request_context",
    default=None,
)
_agent_execution: ContextVar[AgentExecutionContext | None] = ContextVar(
    "aegisqa_agent_execution",
    default=None,
)


def current_request_context() -> RequestContext | None:
    return _request_context.get()


def current_agent_execution() -> AgentExecutionContext | None:
    return _agent_execution.get()


@contextmanager
def request_context_scope(
    *,
    request_id: str,
    actor: str,
    organization_id: str,
) -> Iterator[RequestContext]:
    context = RequestContext(
        request_id=request_id,
        actor=actor,
        organization_id=organization_id,
    )
    token = _request_context.set(context)
    try:
        yield context
    finally:
        _request_context.reset(token)


@contextmanager
def agent_execution_scope(
    *,
    agent_id: str,
    agent_name: str,
    context_id: str | None,
    skill_name: str | None = None,
    allowed_tools: tuple[str, ...] = (),
) -> Iterator[AgentExecutionContext]:
    context = AgentExecutionContext(
        agent_id=agent_id,
        agent_name=agent_name,
        context_id=context_id,
        skill_name=skill_name,
        allowed_tools=allowed_tools,
    )
    token = _agent_execution.set(context)
    try:
        yield context
    finally:
        _agent_execution.reset(token)
