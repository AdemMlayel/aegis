from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.graph.state import StrictModel, utc_now


class ArtifactStoreMode(StrEnum):
    LOCAL = "local"
    MOCK = "mock"
    EXTERNAL = "external"


class ArtifactRecord(StrictModel):
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid4().hex[:12]}")
    context_id: str
    kind: str
    path: str
    content_type: str = "text/plain"
    description: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactStoreSpec:
    name: str
    mode: ArtifactStoreMode = ArtifactStoreMode.LOCAL
    description: str = ""
    root: str = "generated/artifacts"
    version: str = "0.1.0"
    requires_external_api: bool = False


class BaseArtifactStore(ABC):
    spec: ClassVar[ArtifactStoreSpec] = ArtifactStoreSpec(name="base")

    @abstractmethod
    def put_text(
        self,
        *,
        context_id: str,
        kind: str,
        name: str,
        content: str,
        content_type: str = "text/plain",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRecord:
        raise NotImplementedError

    @abstractmethod
    def read_text(self, record: ArtifactRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    def list(self, *, context_id: str | None = None) -> list[ArtifactRecord]:
        raise NotImplementedError


class ArtifactStoreRegistrationError(ValueError):
    pass


class ArtifactStoreRegistry:
    def __init__(self) -> None:
        self._stores: dict[str, type[BaseArtifactStore]] = {}

    def register(
        self,
        *,
        name: str,
        mode: ArtifactStoreMode = ArtifactStoreMode.LOCAL,
        description: str = "",
        root: str = "generated/artifacts",
        version: str = "0.1.0",
        requires_external_api: bool = False,
    ):
        normalized_name = _require_name(name)
        spec = ArtifactStoreSpec(
            name=normalized_name,
            mode=mode,
            description=description,
            root=root,
            version=version,
            requires_external_api=requires_external_api,
        )

        def decorator(store_cls: type[BaseArtifactStore]) -> type[BaseArtifactStore]:
            if not issubclass(store_cls, BaseArtifactStore):
                raise TypeError("Registered artifact stores must inherit from BaseArtifactStore")
            if normalized_name in self._stores:
                raise ArtifactStoreRegistrationError(
                    f"Artifact store '{normalized_name}' is already registered"
                )
            store_cls.spec = spec
            self._stores[normalized_name] = store_cls
            return store_cls

        return decorator

    def create(self, name: str, **kwargs: object) -> BaseArtifactStore:
        return self.get(name)(**kwargs)

    def get(self, name: str) -> type[BaseArtifactStore]:
        normalized_name = _require_name(name)
        try:
            return self._stores[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Artifact store '{normalized_name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return _require_name(name) in self._stores

    def list_specs(self) -> list[ArtifactStoreSpec]:
        return sorted((store_cls.spec for store_cls in self._stores.values()), key=lambda spec: spec.name)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ArtifactStoreRegistrationError("Artifact store names cannot be empty")
    return normalized_name


artifact_store_registry = ArtifactStoreRegistry()
