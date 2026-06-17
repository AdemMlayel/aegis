from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

import backend.artifacts  # Registers local artifact store.
import backend.execution  # Registers local execution adapters.
import backend.secrets  # Registers mock Vault provider.
import backend.tickets  # Registers local ticket connectors.
import backend.llm  # Registers local LLM providers.
import backend.tools.git_handoff  # Registers local Git handoff tool.
from backend.artifacts import artifact_store_registry
from backend.config.settings import settings
from backend.execution import execution_adapter_registry
from backend.llm import llm_provider_registry
from backend.secrets import secret_provider_registry
from backend.tickets import ticket_connector_registry
from backend.tools import tool_registry


class ProviderKind(StrEnum):
    TICKET_CONNECTOR = "ticket_connector"
    EXECUTION_ADAPTER = "execution_adapter"
    ARTIFACT_STORE = "artifact_store"
    SECRET_PROVIDER = "secret_provider"
    GIT_HANDOFF = "git_handoff"
    LLM_PROVIDER = "llm_provider"
    KNOWLEDGE_STORE = "knowledge_store"
    MEMORY_STORE = "memory_store"
    EMBEDDING_MODEL = "embedding_model"
    VECTOR_STORE = "vector_store"
    RERANKER = "reranker"


class ProviderMode(StrEnum):
    MOCK = "mock"
    LOCAL = "local"
    EXTERNAL = "external"


@dataclass(frozen=True)
class ProviderSelection:
    kind: ProviderKind
    selected: str
    requires_external_api: bool
    status: str


@dataclass(frozen=True)
class ProviderCatalogEntry:
    kind: ProviderKind
    name: str
    mode: ProviderMode
    description: str = ""
    version: str = "0.1.0"
    requires_external_api: bool = False
    enabled: bool = True
    selected: bool = False
    config_key: str | None = None
    configuration_status: str = "ready"
    configuration_keys: tuple[str, ...] = ()


class ProviderCatalog:
    """Read-only catalog for integration-ready local providers.

    This catalog intentionally exposes provider boundaries without opening any
    company API connection.  External providers should be added later as new
    entries with ``requires_external_api=True`` and disabled until company
    credentials/configuration exist.
    """

    def __init__(self, entries: list[ProviderCatalogEntry]) -> None:
        self._entries = entries

    def list(self, *, include_external: bool = False) -> list[ProviderCatalogEntry]:
        if include_external:
            return sorted(self._entries, key=lambda entry: (entry.kind, entry.name))
        return sorted(
            [entry for entry in self._entries if not entry.requires_external_api],
            key=lambda entry: (entry.kind, entry.name),
        )

    def selections(self) -> list[ProviderSelection]:
        selections: list[ProviderSelection] = []
        for entry in self._entries:
            if entry.selected:
                selections.append(
                    ProviderSelection(
                        kind=entry.kind,
                        selected=entry.name,
                        requires_external_api=entry.requires_external_api,
                        status="ready" if entry.enabled else "disabled",
                    )
                )
        return sorted(selections, key=lambda item: item.kind)

    def selected(self, kind: ProviderKind) -> ProviderCatalogEntry | None:
        return next((entry for entry in self._entries if entry.kind == kind and entry.selected), None)

    def as_dict(self, *, include_external: bool = False) -> dict[str, Any]:
        return {
            "environment": settings.environment,
            "external_connectors_enabled": settings.external_connectors_enabled,
            "selected": [asdict(selection) for selection in self.selections()],
            "providers": [asdict(entry) for entry in self.list(include_external=include_external)],
        }


def build_provider_catalog() -> ProviderCatalog:
    entries: list[ProviderCatalogEntry] = []

    for spec in ticket_connector_registry.list_specs():
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.TICKET_CONNECTOR,
                name=spec.name,
                mode=ProviderMode.MOCK if spec.name.endswith("mock") else ProviderMode.EXTERNAL,
                description=spec.description,
                version=spec.version,
                requires_external_api=spec.requires_external_api,
                enabled=_enabled(spec.requires_external_api),
                selected=spec.name == settings.default_ticket_connector,
                config_key="AEGISQA_DEFAULT_TICKET_CONNECTOR",
            )
        )

    for spec in execution_adapter_registry.list_specs():
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.EXECUTION_ADAPTER,
                name=spec.name,
                mode=ProviderMode.LOCAL,
                description=spec.description,
                version=spec.version,
                requires_external_api=False,
                enabled=True,
                selected=spec.name == settings.default_execution_adapter,
                config_key="AEGISQA_DEFAULT_EXECUTION_ADAPTER",
            )
        )

    for spec in artifact_store_registry.list_specs():
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.ARTIFACT_STORE,
                name=spec.name,
                mode=ProviderMode(spec.mode),
                description=spec.description,
                version=spec.version,
                requires_external_api=spec.requires_external_api,
                enabled=_enabled(spec.requires_external_api),
                selected=spec.name == settings.default_artifact_store,
                config_key="AEGISQA_DEFAULT_ARTIFACT_STORE",
            )
        )

    for spec in secret_provider_registry.list_specs():
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.SECRET_PROVIDER,
                name=spec.name,
                mode=ProviderMode(spec.mode),
                description=spec.description,
                version=spec.version,
                requires_external_api=spec.requires_external_api,
                enabled=_enabled(spec.requires_external_api),
                selected=spec.name == settings.default_secret_provider,
                config_key="AEGISQA_DEFAULT_SECRET_PROVIDER",
            )
        )


    for spec in llm_provider_registry.list_specs():
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.LLM_PROVIDER,
                name=spec.name,
                mode=ProviderMode(spec.mode),
                description=spec.description,
                version="0.1.0",
                requires_external_api=spec.requires_external_api,
                enabled=_enabled(spec.requires_external_api) and spec.configuration_status != "missing_api_key",
                selected=spec.name == settings.default_llm_provider,
                config_key="AEGISQA_DEFAULT_LLM_PROVIDER",
                configuration_status=spec.configuration_status,
                configuration_keys=spec.configuration_keys,
            )
        )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.KNOWLEDGE_STORE,
            name="local_knowledge",
            mode=ProviderMode.LOCAL,
            description="Local deterministic knowledge store for RAG architecture proofs.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_knowledge_store == "local_knowledge",
            config_key="AEGISQA_DEFAULT_KNOWLEDGE_STORE",
        )
    )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.MEMORY_STORE,
            name="local_episodic_memory",
            mode=ProviderMode.LOCAL,
            description="Local seeded episodic memory store for previous-failure retrieval and archive proofs.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_memory_store == "local_episodic_memory",
            config_key="AEGISQA_DEFAULT_MEMORY_STORE",
        )
    )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.EMBEDDING_MODEL,
            name="local_hash_embedding",
            mode=ProviderMode.LOCAL,
            description="Deterministic local hashing embedding model for RAG architecture proofs.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_embedding_model == "local_hash_embedding",
            config_key="AEGISQA_DEFAULT_EMBEDDING_MODEL",
        )
    )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.EMBEDDING_MODEL,
            name="ollama_embedding",
            mode=ProviderMode.LOCAL,
            description="Local Ollama embedding model for RAG and memory retrieval.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_embedding_model == "ollama_embedding",
            config_key="AEGISQA_DEFAULT_EMBEDDING_MODEL",
            configuration_status="configured",
            configuration_keys=("AEGISQA_OLLAMA_EMBEDDING_MODEL", "AEGISQA_OLLAMA_EMBEDDING_FALLBACK_MODEL"),
        )
    )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.VECTOR_STORE,
            name="local_in_memory_vector",
            mode=ProviderMode.LOCAL,
            description="Local in-memory vector index for deterministic knowledge and memory search.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_vector_store == "local_in_memory_vector",
            config_key="AEGISQA_DEFAULT_VECTOR_STORE",
        )
    )

    entries.append(
        ProviderCatalogEntry(
            kind=ProviderKind.RERANKER,
            name="local_hybrid_reranker",
            mode=ProviderMode.LOCAL,
            description="Local hybrid reranker combining vector similarity, lexical overlap, and tag matches.",
            version="0.1.0",
            requires_external_api=False,
            enabled=True,
            selected=settings.default_reranker == "local_hybrid_reranker",
            config_key="AEGISQA_DEFAULT_RERANKER",
        )
    )

    if tool_registry.has("LocalGitHandoffTool"):
        git_spec = tool_registry.get("LocalGitHandoffTool").spec
        entries.append(
            ProviderCatalogEntry(
                kind=ProviderKind.GIT_HANDOFF,
                name=git_spec.name,
                mode=ProviderMode.LOCAL,
                description=git_spec.description,
                version=git_spec.version,
                requires_external_api=False,
                enabled=True,
                selected=True,
                config_key=None,
            )
        )

    return ProviderCatalog(entries)


def _enabled(requires_external_api: bool) -> bool:
    return not requires_external_api or settings.external_connectors_enabled
