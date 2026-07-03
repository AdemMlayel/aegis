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
    # When True this scope represents a trusted, RBAC-gated system caller (e.g.
    # the approval endpoint driving the Git handoff) rather than an LLM agent.
    # Such a scope may run high-risk tools without an agent skill graph, but it
    # is an explicit, audited authorization -- never the implicit ungoverned
    # ``None`` path that W6 denies.
    system_authorized_tools: tuple[str, ...] = ()


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
    system_authorized_tools: tuple[str, ...] = (),
) -> Iterator[AgentExecutionContext]:
    context = AgentExecutionContext(
        agent_id=agent_id,
        agent_name=agent_name,
        context_id=context_id,
        skill_name=skill_name,
        allowed_tools=allowed_tools,
        system_authorized_tools=system_authorized_tools,
    )
    token = _agent_execution.set(context)
    try:
        yield context
    finally:
        _agent_execution.reset(token)


@contextmanager
def system_tool_scope(
    *,
    tool_names: tuple[str, ...],
    context_id: str | None = None,
    caller: str = "system",
) -> Iterator[AgentExecutionContext]:
    """Open an explicit, audited authorization scope for a trusted system caller.

    Use this when a non-agent, RBAC-gated endpoint must run a high-risk tool
    (e.g. the approval endpoint driving the Git handoff). It authorizes only the
    named tools and nothing else, so it is far narrower than the old ungoverned
    ``execution is None`` path that W6 now denies for high-risk tools.
    """
    context = AgentExecutionContext(
        agent_id=f"aegisqa.system.{caller}",
        agent_name=caller,
        context_id=context_id,
        skill_name=None,
        allowed_tools=tool_names,
        system_authorized_tools=tool_names,
    )
    token = _agent_execution.set(context)
    try:
        yield context
    finally:
        _agent_execution.reset(token)
