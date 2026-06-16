from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from backend.graph.state import TestContext


@dataclass(frozen=True)
class AgentSpec:
    name: str
    skills: tuple[str, ...] = ()
    description: str = ""
    version: str = "0.1.0"


class BaseAgent(ABC):
    spec: ClassVar[AgentSpec] = AgentSpec(name="base")

    def __init__(self, *, skill_registry: object | None = None) -> None:
        self.skill_registry = skill_registry

    @abstractmethod
    def run(self, context: TestContext) -> TestContext:
        raise NotImplementedError


class AgentRegistrationError(ValueError):
    pass


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(
        self,
        *,
        name: str,
        skills: Iterable[str] = (),
        description: str = "",
        version: str = "0.1.0",
    ):
        normalized_name = _require_name(name)
        spec = AgentSpec(
            name=normalized_name,
            skills=tuple(skills),
            description=description,
            version=version,
        )

        def decorator(agent_cls: type[BaseAgent]) -> type[BaseAgent]:
            if not issubclass(agent_cls, BaseAgent):
                raise TypeError("Registered agents must inherit from BaseAgent")
            if normalized_name in self._agents:
                raise AgentRegistrationError(
                    f"Agent '{normalized_name}' is already registered"
                )
            agent_cls.spec = spec
            self._agents[normalized_name] = agent_cls
            return agent_cls

        return decorator

    def get(self, name: str) -> type[BaseAgent]:
        normalized_name = _require_name(name)
        try:
            return self._agents[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Agent '{normalized_name}' is not registered") from exc

    def create(self, name: str, **kwargs: object) -> BaseAgent:
        return self.get(name)(**kwargs)

    def has(self, name: str) -> bool:
        return _require_name(name) in self._agents

    def list_specs(self) -> list[AgentSpec]:
        return sorted(
            (agent_cls.spec for agent_cls in self._agents.values()),
            key=lambda spec: spec.name,
        )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise AgentRegistrationError("Registry names cannot be empty")
    return normalized_name


agent_registry = AgentRegistry()
