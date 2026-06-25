from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from backend.graph.state import TicketData


@dataclass(frozen=True)
class TicketConnectorSpec:
    name: str
    source: str
    description: str = ""
    version: str = "0.1.0"
    requires_external_api: bool = False


@dataclass(frozen=True)
class TicketConnectorHealth:
    name: str
    status: str
    requires_external_api: bool
    detail: str = ""


class BaseTicketConnector(ABC):
    spec: ClassVar[TicketConnectorSpec] = TicketConnectorSpec(
        name="base",
        source="mock",
    )

    @abstractmethod
    def fetch(self, ticket_id: str) -> TicketData | None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str | None = None) -> list[TicketData]:
        raise NotImplementedError


    def health(self) -> TicketConnectorHealth:
        return TicketConnectorHealth(
            name=self.spec.name,
            status="ready" if not self.spec.requires_external_api else "external_configuration_required",
            requires_external_api=self.spec.requires_external_api,
            detail=self.spec.description,
        )


class TicketConnectorRegistrationError(ValueError):
    pass


class TicketConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, type[BaseTicketConnector]] = {}

    def register(
        self,
        *,
        name: str,
        source: str,
        description: str = "",
        version: str = "0.1.0",
        requires_external_api: bool = False,
    ):
        normalized_name = _require_name(name)
        spec = TicketConnectorSpec(
            name=normalized_name,
            source=source,
            description=description,
            version=version,
            requires_external_api=requires_external_api,
        )

        def decorator(cls: type[BaseTicketConnector]) -> type[BaseTicketConnector]:
            if not issubclass(cls, BaseTicketConnector):
                raise TypeError("Registered ticket connectors must inherit from BaseTicketConnector")
            if normalized_name in self._connectors:
                raise TicketConnectorRegistrationError(
                    f"Ticket connector '{normalized_name}' is already registered"
                )
            cls.spec = spec
            self._connectors[normalized_name] = cls
            return cls

        return decorator

    def create(self, name: str, **kwargs: object) -> BaseTicketConnector:
        return self.get(name)(**kwargs)

    def get(self, name: str) -> type[BaseTicketConnector]:
        normalized_name = _require_name(name)
        try:
            return self._connectors[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Ticket connector '{normalized_name}' is not registered") from exc

    def has(self, name: str) -> bool:
        return _require_name(name) in self._connectors

    def list_specs(self) -> list[TicketConnectorSpec]:
        return sorted((cls.spec for cls in self._connectors.values()), key=lambda spec: spec.name)


def _require_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise TicketConnectorRegistrationError("Ticket connector names cannot be empty")
    return normalized_name


ticket_connector_registry = TicketConnectorRegistry()
