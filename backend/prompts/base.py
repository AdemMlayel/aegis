from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Any


@dataclass(frozen=True)
class PromptTemplateSpec:
    name: str
    version: str
    description: str
    template: str

    def render(self, **values: Any) -> str:
        safe_values = {key: _stringify(value) for key, value in values.items()}
        return Template(self.template).safe_substitute(safe_values)


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplateSpec] = {}

    def register(self, *, name: str, version: str, description: str, template: str) -> PromptTemplateSpec:
        normalized_name = _require_name(name)
        spec = PromptTemplateSpec(
            name=normalized_name,
            version=version,
            description=description,
            template=template,
        )
        if normalized_name in self._templates:
            raise ValueError(f"Prompt template '{normalized_name}' is already registered")
        self._templates[normalized_name] = spec
        return spec

    def get(self, name: str) -> PromptTemplateSpec:
        normalized_name = _require_name(name)
        try:
            return self._templates[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Prompt template '{normalized_name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return _require_name(name) in self._templates

    def list_specs(self) -> list[PromptTemplateSpec]:
        return sorted(self._templates.values(), key=lambda spec: spec.name)


def _stringify(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(_stringify(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {_stringify(item)}" for key, item in value.items())
    return str(value)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Prompt names cannot be empty")
    return normalized_name


prompt_registry = PromptRegistry()
