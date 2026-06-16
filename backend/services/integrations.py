from __future__ import annotations

from backend.artifacts import ArtifactRecord, artifact_store_registry
from backend.config.settings import settings
from backend.integrations.profile import build_integration_profile
from backend.integrations.providers import build_provider_catalog
from backend.secrets import SecretReference, secret_provider_registry


class IntegrationServiceError(Exception):
    """Base exception for integration service failures."""


class IntegrationConfigurationError(IntegrationServiceError):
    pass


def read_provider_catalog(*, include_external: bool = False) -> dict[str, object]:
    return build_provider_catalog().as_dict(include_external=include_external)


def read_integration_profile() -> dict[str, object]:
    return build_integration_profile().model_dump(mode="json")


def read_secret_references() -> tuple[str, list[SecretReference]]:
    if not secret_provider_registry.has(settings.default_secret_provider):
        raise IntegrationConfigurationError(
            f"Secret provider '{settings.default_secret_provider}' is not registered"
        )
    provider = secret_provider_registry.create(settings.default_secret_provider)
    return settings.default_secret_provider, provider.list_references()


def list_local_artifacts(
    *,
    context_id: str | None = None,
) -> tuple[str, list[ArtifactRecord]]:
    if not artifact_store_registry.has(settings.default_artifact_store):
        raise IntegrationConfigurationError(
            f"Artifact store '{settings.default_artifact_store}' is not registered"
        )
    store = artifact_store_registry.create(settings.default_artifact_store)
    return settings.default_artifact_store, store.list(context_id=context_id)
