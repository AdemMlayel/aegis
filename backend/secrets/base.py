from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from pydantic import Field

from backend.graph.state import StrictModel


class SecretProviderMode(StrEnum):
    MOCK = "mock"
    LOCAL = "local"
    EXTERNAL = "external"


class SecretReference(StrictModel):
    provider: str
    name: str = Field(min_length=1)
    uri: str
    masked_value: str = "********"
    external_resolution_required: bool = False


@dataclass(frozen=True)
class SecretProviderSpec:
    name: str
    mode: SecretProviderMode = SecretProviderMode.MOCK
    description: str = ""
    version: str = "0.1.0"
    requires_external_api: bool = False
    resolves_values: bool = False


class BaseSecretProvider(ABC):
    spec: ClassVar[SecretProviderSpec] = SecretProviderSpec(name="base")

    @abstractmethod
    def reference(self, name: str) -> SecretReference:
        raise NotImplementedError

    @abstractmethod
    def list_references(self) -> list[SecretReference]:
        raise NotImplementedError


class SecretProviderRegistrationError(ValueError):
    pass


class SecretProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[BaseSecretProvider]] = {}

    def register(
        self,
        *,
        name: str,
        mode: SecretProviderMode = SecretProviderMode.MOCK,
        description: str = "",
        version: str = "0.1.0",
        requires_external_api: bool = False,
        resolves_values: bool = False,
    ):
        normalized_name = _require_name(name)
        spec = SecretProviderSpec(
            name=normalized_name,
            mode=mode,
            description=description,
            version=version,
            requires_external_api=requires_external_api,
            resolves_values=resolves_values,
        )

        def decorator(provider_cls: type[BaseSecretProvider]) -> type[BaseSecretProvider]:
            if not issubclass(provider_cls, BaseSecretProvider):
                raise TypeError("Registered secret providers must inherit from BaseSecretProvider")
            if normalized_name in self._providers:
                raise SecretProviderRegistrationError(
                    f"Secret provider '{normalized_name}' is already registered"
                )
            provider_cls.spec = spec
            self._providers[normalized_name] = provider_cls
            return provider_cls

        return decorator

    def create(self, name: str, **kwargs: object) -> BaseSecretProvider:
        return self.get(name)(**kwargs)

    def get(self, name: str) -> type[BaseSecretProvider]:
        normalized_name = _require_name(name)
        try:
            return self._providers[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Secret provider '{normalized_name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return _require_name(name) in self._providers

    def list_specs(self) -> list[SecretProviderSpec]:
        return sorted((provider_cls.spec for provider_cls in self._providers.values()), key=lambda spec: spec.name)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise SecretProviderRegistrationError("Secret provider names cannot be empty")
    return normalized_name


secret_provider_registry = SecretProviderRegistry()
