from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class ToolSpec:
    name: str
    isolation: str = "process"
    description: str = ""
    version: str = "0.1.0"


class BaseTool(ABC):
    spec: ClassVar[ToolSpec] = ToolSpec(name="base")

    @abstractmethod
    def invoke(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class ToolRegistrationError(ValueError):
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
    ):
        normalized_name = _require_name(name)
        spec = ToolSpec(
            name=normalized_name,
            isolation=isolation,
            description=description,
            version=version,
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

    def has(self, name: str) -> bool:
        return _require_name(name) in self._tools

    def list_specs(self) -> list[ToolSpec]:
        return sorted(
            (tool_cls.spec for tool_cls in self._tools.values()),
            key=lambda spec: spec.name,
        )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ToolRegistrationError("Registry names cannot be empty")
    return normalized_name


tool_registry = ToolRegistry()
