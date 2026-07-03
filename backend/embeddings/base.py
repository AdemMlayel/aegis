from __future__ import annotations

import hashlib
import re
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

    def __init__(self, *, model_override: str | None = None) -> None:
        self.model_override = model_override

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

    def create(
        self,
        name: str,
        *,
        model_override: str | None = None,
    ) -> BaseEmbeddingProvider:
        return self.get(name)(model_override=model_override)

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
    """Deterministic, semantically-meaningful local embedding.

    Hashes each TOKEN into a bucket and accumulates a signed count, rather than
    hashing the whole string into one fingerprint. This matters: a whole-text
    SHA256 fingerprint gives two texts that differ by a single word nearly
    orthogonal vectors (cosine ~0.09), so cosine similarity carries no semantic
    signal and RAG retrieval silently degrades to lexical-overlap-only. Token
    bucketing makes texts that share words land close together (cosine ~0.91 for
    a one-word delta) while staying fully deterministic and dependency-free.

    Empty / token-less text returns a zero vector (cosine 0 against anything),
    which is the correct "no signal" behaviour.
    """
    values = [0.0] * dimensions
    for token in _embedding_tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        values[bucket] += sign
    magnitude = sum(value * value for value in values) ** 0.5
    if magnitude == 0:
        return tuple(values)
    return tuple(round(value / magnitude, 6) for value in values)


def _embedding_tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokens of length > 2 (drops noise stopwords)."""
    return [
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) > 2
    ]


embedding_provider_registry = EmbeddingProviderRegistry()
