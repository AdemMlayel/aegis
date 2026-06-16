from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from backend.graph.state import TestContext


@dataclass(frozen=True)
class SkillSpec:
    name: str
    tools: tuple[str, ...] = ()
    description: str = ""
    version: str = "0.1.0"


class BaseSkill(ABC):
    spec: ClassVar[SkillSpec] = SkillSpec(name="base")

    def __init__(self, *, tool_registry: object | None = None) -> None:
        self.tool_registry = tool_registry

    @abstractmethod
    def execute(self, context: TestContext) -> TestContext:
        raise NotImplementedError


class SkillRegistrationError(ValueError):
    pass


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, type[BaseSkill]] = {}

    def register(
        self,
        *,
        name: str,
        tools: Iterable[str] = (),
        description: str = "",
        version: str = "0.1.0",
    ):
        normalized_name = _require_name(name)
        spec = SkillSpec(
            name=normalized_name,
            tools=tuple(tools),
            description=description,
            version=version,
        )

        def decorator(skill_cls: type[BaseSkill]) -> type[BaseSkill]:
            if not issubclass(skill_cls, BaseSkill):
                raise TypeError("Registered skills must inherit from BaseSkill")
            if normalized_name in self._skills:
                raise SkillRegistrationError(
                    f"Skill '{normalized_name}' is already registered"
                )
            skill_cls.spec = spec
            self._skills[normalized_name] = skill_cls
            return skill_cls

        return decorator

    def get(self, name: str) -> type[BaseSkill]:
        normalized_name = _require_name(name)
        try:
            return self._skills[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Skill '{normalized_name}' is not registered") from exc

    def create(self, name: str, **kwargs: object) -> BaseSkill:
        return self.get(name)(**kwargs)

    def has(self, name: str) -> bool:
        return _require_name(name) in self._skills

    def list_specs(self) -> list[SkillSpec]:
        return sorted(
            (skill_cls.spec for skill_cls in self._skills.values()),
            key=lambda spec: spec.name,
        )


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise SkillRegistrationError("Registry names cannot be empty")
    return normalized_name


skill_registry = SkillRegistry()
