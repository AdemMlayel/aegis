from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EmbeddingProviderSpec:
    name: str
    mode: Literal["mock", "local", "external"] = "local"
    model: str = "local-hash"
    dimensions: int = 32
    requires_external_api: bool = False
    description: str = ""


@dataclass(frozen=True)
class EmbeddingResponse:
    provider: str
    model: str
    vector: tuple[float, ...]
    deterministic: bool = True


class BaseEmbeddingProvider(ABC):
    spec: EmbeddingProviderSpec = EmbeddingProviderSpec(name="base")

    @abstractmethod
    def embed(self, text: str) -> EmbeddingResponse:
        raise NotImplementedError


class EmbeddingProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[BaseEmbeddingProvider]] = {}

    def register(
        self,
        *,
        name: str,
        mode: Literal["mock", "local", "external"] = "local",
        model: str = "local-hash",
        dimensions: int = 32,
        requires_external_api: bool = False,
        description: str = "",
    ):
        normalized_name = _require_name(name)
        spec = EmbeddingProviderSpec(
            name=normalized_name,
            mode=mode,
            model=model,
            dimensions=dimensions,
            requires_external_api=requires_external_api,
            description=description,
        )

        def decorator(provider_cls: type[BaseEmbeddingProvider]) -> type[BaseEmbeddingProvider]:
            if not issubclass(provider_cls, BaseEmbeddingProvider):
                raise TypeError("Embedding providers must inherit from BaseEmbeddingProvider")
            if normalized_name in self._providers:
                raise ValueError(f"Embedding provider '{normalized_name}' is already registered")
            provider_cls.spec = spec
            self._providers[normalized_name] = provider_cls
            return provider_cls

        return decorator

    def create(self, name: str) -> BaseEmbeddingProvider:
        return self.get(name)()

    def get(self, name: str) -> type[BaseEmbeddingProvider]:
        normalized_name = _require_name(name)
        try:
            return self._providers[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Embedding provider '{normalized_name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return _require_name(name) in self._providers

    def list_specs(self) -> list[EmbeddingProviderSpec]:
        return sorted((provider.spec for provider in self._providers.values()), key=lambda spec: spec.name)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Provider names cannot be empty")
    return normalized_name


def deterministic_hash_embedding(text: str, *, dimensions: int = 32) -> tuple[float, ...]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = list(digest)
    while len(raw) < dimensions:
        raw.extend(hashlib.sha256(bytes(raw)).digest())
    values = [(byte / 127.5) - 1.0 for byte in raw[:dimensions]]
    magnitude = sum(value * value for value in values) ** 0.5 or 1.0
    return tuple(round(value / magnitude, 6) for value in values)


embedding_provider_registry = EmbeddingProviderRegistry()
