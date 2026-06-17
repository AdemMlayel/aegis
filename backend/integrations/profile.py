from __future__ import annotations

from backend.graph.state import IntegrationProfileBlock, IntegrationProviderRef
from backend.integrations.providers import ProviderCatalogEntry, ProviderKind, ProviderMode, build_provider_catalog


def build_integration_profile() -> IntegrationProfileBlock:
    catalog = build_provider_catalog()
    entries = {entry.kind: entry for entry in catalog.list(include_external=True) if entry.selected}
    external_enabled = catalog.as_dict(include_external=True)["external_connectors_enabled"]
    return IntegrationProfileBlock(
        ticket_connector=_to_ref(entries.get(ProviderKind.TICKET_CONNECTOR)),
        execution_adapter=_to_ref(entries.get(ProviderKind.EXECUTION_ADAPTER)),
        artifact_store=_to_ref(entries.get(ProviderKind.ARTIFACT_STORE)),
        secret_provider=_to_ref(entries.get(ProviderKind.SECRET_PROVIDER)),
        git_handoff=_to_ref(entries.get(ProviderKind.GIT_HANDOFF)),
        llm_provider=_to_ref(entries.get(ProviderKind.LLM_PROVIDER)),
        knowledge_store=_to_ref(entries.get(ProviderKind.KNOWLEDGE_STORE)),
        memory_store=_to_ref(entries.get(ProviderKind.MEMORY_STORE)),
        policy="external_allowed" if external_enabled else "mock_only",
        external_connectors_enabled=bool(external_enabled),
    )


def _to_ref(entry: ProviderCatalogEntry | None) -> IntegrationProviderRef | None:
    if entry is None:
        return None
    notes: list[str] = []
    if entry.requires_external_api and not entry.enabled:
        notes.append("Provider requires external API configuration and is disabled in local mode.")
    if entry.mode in {ProviderMode.MOCK, ProviderMode.LOCAL}:
        notes.append("Provider is safe for local architecture proofs.")
    if entry.configuration_status not in {"ready", "configured"}:
        notes.append(f"Provider configuration status: {entry.configuration_status}.")
    return IntegrationProviderRef(
        kind=entry.kind.value,
        name=entry.name,
        mode=entry.mode.value,
        requires_external_api=entry.requires_external_api,
        status="ready" if entry.enabled else "disabled",
        notes=notes,
    )
