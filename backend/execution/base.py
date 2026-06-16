from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from backend.graph.state import TestContext


@dataclass(frozen=True)
class ExecutionAdapterSpec:
    name: str
    engine: str = "local"
    capabilities: tuple[str, ...] = ()
    description: str = ""
    version: str = "0.1.0"


class BaseExecutionAdapter(ABC):
    spec: ClassVar[ExecutionAdapterSpec] = ExecutionAdapterSpec(name="base")

    @abstractmethod
    def execute(
        self,
        context: TestContext,
        *,
        actor: str,
        env: str,
        branch: str | None = None,
        tags: Iterable[str] = (),
    ) -> TestContext:
        raise NotImplementedError


class ExecutionAdapterRegistrationError(ValueError):
    pass


class ExecutionAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, type[BaseExecutionAdapter]] = {}

    def register(
        self,
        *,
        name: str,
        engine: str = "local",
        capabilities: Iterable[str] = (),
        description: str = "",
        version: str = "0.1.0",
    ):
        normalized_name = _require_name(name)
        spec = ExecutionAdapterSpec(
            name=normalized_name,
            engine=engine,
            capabilities=tuple(capabilities),
            description=description,
            version=version,
        )

        def decorator(
            adapter_cls: type[BaseExecutionAdapter],
        ) -> type[BaseExecutionAdapter]:
            if not issubclass(adapter_cls, BaseExecutionAdapter):
                raise TypeError(
                    "Registered execution adapters must inherit from BaseExecutionAdapter"
                )
            if normalized_name in self._adapters:
                raise ExecutionAdapterRegistrationError(
                    f"Execution adapter '{normalized_name}' is already registered"
                )
            adapter_cls.spec = spec
            self._adapters[normalized_name] = adapter_cls
            return adapter_cls

        return decorator

    def get(self, name: str) -> type[BaseExecutionAdapter]:
        normalized_name = _require_name(name)
        try:
            return self._adapters[normalized_name]
        except KeyError as exc:
            raise KeyError(
                f"Execution adapter '{normalized_name}' is not registered"
            ) from exc

    def create(self, name: str, **kwargs: object) -> BaseExecutionAdapter:
        return self.get(name)(**kwargs)

    def has(self, name: str) -> bool:
        return _require_name(name) in self._adapters

    def list_specs(self) -> list[ExecutionAdapterSpec]:
        return sorted(
            (adapter_cls.spec for adapter_cls in self._adapters.values()),
            key=lambda spec: spec.name,
        )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ExecutionAdapterRegistrationError(
            "Execution adapter registry names cannot be empty"
        )
    return normalized_name


execution_adapter_registry = ExecutionAdapterRegistry()
