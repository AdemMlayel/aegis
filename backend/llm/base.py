from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LLMProviderSpec:
    name: str
    mode: Literal["mock", "local", "external"] = "mock"
    model: str = "deterministic-mock"
    requires_external_api: bool = False
    description: str = ""


@dataclass(frozen=True)
class LLMResponse:
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    text: str
    deterministic: bool = True
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class BaseLLMProvider(ABC):
    spec: LLMProviderSpec = LLMProviderSpec(name="base")

    @abstractmethod
    def complete(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        rendered_prompt: str,
        system_instruction: str | None = None,
        model_override: str | None = None,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        raise NotImplementedError


class LLMProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[BaseLLMProvider]] = {}

    def register(
        self,
        *,
        name: str,
        mode: Literal["mock", "local", "external"] = "mock",
        model: str = "deterministic-mock",
        requires_external_api: bool = False,
        description: str = "",
    ):
        normalized_name = _require_name(name)
        spec = LLMProviderSpec(
            name=normalized_name,
            mode=mode,
            model=model,
            requires_external_api=requires_external_api,
            description=description,
        )

        def decorator(provider_cls: type[BaseLLMProvider]) -> type[BaseLLMProvider]:
            if not issubclass(provider_cls, BaseLLMProvider):
                raise TypeError("LLM providers must inherit from BaseLLMProvider")
            if normalized_name in self._providers:
                raise ValueError(f"LLM provider '{normalized_name}' is already registered")
            provider_cls.spec = spec
            self._providers[normalized_name] = provider_cls
            return provider_cls

        return decorator

    def get(self, name: str) -> type[BaseLLMProvider]:
        normalized_name = _require_name(name)
        try:
            return self._providers[normalized_name]
        except KeyError as exc:
            raise KeyError(f"LLM provider '{normalized_name}' is not registered") from exc

    def create(self, name: str) -> BaseLLMProvider:
        return self.get(name)()

    def has(self, name: str) -> bool:
        return _require_name(name) in self._providers

    def list_specs(self) -> list[LLMProviderSpec]:
        return sorted((provider.spec for provider in self._providers.values()), key=lambda spec: spec.name)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Provider names cannot be empty")
    return normalized_name


llm_provider_registry = LLMProviderRegistry()
