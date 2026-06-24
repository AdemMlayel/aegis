from __future__ import annotations

import hashlib
import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from backend.governance.context import current_agent_execution
from backend.governance.gateway import GatewayLimitExceeded
from backend.governance.policy import agent_policy_engine
from backend.governance.policy import AgentPolicyDenied

@dataclass(frozen=True)
class ToolSpec:
    name: str
    isolation: str = "process"
    description: str = ""
    version: str = "0.1.0"
    timeout_seconds: int = 30
    max_retries: int = 0
    audited: bool = True


@dataclass(frozen=True)
class ToolExecutionRecord:
    tool_name: str
    status: Literal["success", "failed"]
    attempts: int
    duration_ms: int
    input_hash: str
    output_hash: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ToolResult:
    value: Any
    record: ToolExecutionRecord


class BaseTool(ABC):
    """Base boundary for all executable tools.

    Subclasses keep implementing ``invoke`` for backward compatibility.  New
    code should call ``ToolRegistry.execute`` so every call receives retries,
    timeout metadata, hashes, and audit logging through a single path.
    """

    spec: ClassVar[ToolSpec] = ToolSpec(name="base")

    @abstractmethod
    def invoke(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class ToolRegistrationError(ValueError):
    pass


class ToolExecutionError(RuntimeError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, type[BaseTool]] = {}

    def register(
        self,
        *,
        name: str,
        isolation: str = "process",
        description: str = "",
        version: str = "0.1.0",
        timeout_seconds: int = 30,
        max_retries: int = 0,
        audited: bool = True,
    ):
        normalized_name = _require_name(name)
        spec = ToolSpec(
            name=normalized_name,
            isolation=isolation,
            description=description,
            version=version,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            audited=audited,
        )

        def decorator(tool_cls: type[BaseTool]) -> type[BaseTool]:
            if not issubclass(tool_cls, BaseTool):
                raise TypeError("Registered tools must inherit from BaseTool")
            if normalized_name in self._tools:
                raise ToolRegistrationError(
                    f"Tool '{normalized_name}' is already registered"
                )
            tool_cls.spec = spec
            self._tools[normalized_name] = tool_cls
            return tool_cls

        return decorator

    def get(self, name: str) -> type[BaseTool]:
        normalized_name = _require_name(name)
        try:
            return self._tools[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Tool '{normalized_name}' is not registered") from exc

    def create(self, name: str, **kwargs: object) -> BaseTool:
        return self.get(name)(**kwargs)

    def execute(
        self,
        name: str,
        *,
        actor: str = "system",
        context_id: str | None = None,
        audit_sink: Callable[..., object] | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        agent_policy_engine.authorize_tool(
            current_agent_execution(),
            name,
        )
        tool = self.create(name)
        return execute_tool(
            tool,
            actor=actor,
            context_id=context_id,
            audit_sink=audit_sink,
            **kwargs,
        )

    def has(self, name: str) -> bool:
        return _require_name(name) in self._tools

    def list_specs(self) -> list[ToolSpec]:
        return sorted(
            (tool_cls.spec for tool_cls in self._tools.values()),
            key=lambda spec: spec.name,
        )


def execute_tool(
    tool: BaseTool,
    *,
    actor: str = "system",
    context_id: str | None = None,
    audit_sink: Callable[..., object] | None = None,
    **kwargs: Any,
) -> ToolResult:
    spec = tool.spec
    attempts = 0
    start = time.perf_counter()
    input_hash = _stable_hash(kwargs)
    last_error: Exception | None = None

    for attempts in range(1, spec.max_retries + 2):
        try:
            value = tool.invoke(**kwargs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            record = ToolExecutionRecord(
                tool_name=spec.name,
                status="success",
                attempts=attempts,
                duration_ms=duration_ms,
                input_hash=input_hash,
                output_hash=_stable_hash(value),
            )
            _audit_tool_record(record, actor=actor, context_id=context_id, sink=audit_sink)
            return ToolResult(value=value, record=record)
        except (AgentPolicyDenied, GatewayLimitExceeded):
            raise
        except Exception as exc:  # noqa: BLE001 - contract records tool failures.
            last_error = exc
            if attempts > spec.max_retries:
                break

    duration_ms = int((time.perf_counter() - start) * 1000)
    error_text = "".join(
        traceback.format_exception_only(type(last_error), last_error)
    ).strip()
    record = ToolExecutionRecord(
        tool_name=spec.name,
        status="failed",
        attempts=attempts,
        duration_ms=duration_ms,
        input_hash=input_hash,
        error=error_text,
    )
    _audit_tool_record(record, actor=actor, context_id=context_id, sink=audit_sink)
    raise ToolExecutionError(f"Tool '{spec.name}' failed: {error_text}") from last_error


def _stable_hash(value: Any) -> str:
    try:
        if hasattr(value, "model_dump_json"):
            payload = value.model_dump_json()
        elif isinstance(value, dict):
            payload = repr(_hashable_mapping(value))
        else:
            payload = repr(value)
    except Exception:  # noqa: BLE001 - hashing must not break tool execution.
        payload = f"<{type(value).__name__}>"
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def _hashable_mapping(value: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, item in sorted(value.items(), key=lambda pair: pair[0]):
        if hasattr(item, "model_dump_json"):
            safe[key] = item.model_dump_json()
        elif isinstance(item, dict):
            safe[key] = _hashable_mapping(item)
        elif isinstance(item, list):
            safe[key] = [repr(part) for part in item]
        else:
            safe[key] = repr(item)
    return safe


def _audit_tool_record(
    record: ToolExecutionRecord,
    *,
    actor: str,
    context_id: str | None,
    sink: Callable[..., object] | None,
) -> None:
    if sink is None:
        return
    sink(
        actor=actor,
        event_type="tool_invoked",
        summary=f"Tool {record.tool_name} {record.status}.",
        metadata={
            "context_id": context_id,
            "tool_name": record.tool_name,
            "status": record.status,
            "attempts": record.attempts,
            "duration_ms": record.duration_ms,
            "input_hash": record.input_hash,
            "output_hash": record.output_hash,
            "error": record.error,
        },
    )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ToolRegistrationError("Registry names cannot be empty")
    return normalized_name


tool_registry = ToolRegistry()
