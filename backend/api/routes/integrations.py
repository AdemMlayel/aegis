from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.artifacts import ArtifactRecord, artifact_store_registry
from backend.config.settings import settings
from backend.integrations.profile import build_integration_profile
from backend.integrations.providers import build_provider_catalog
from backend.secrets import SecretReference, secret_provider_registry
from backend.security import Capability, Principal, require_capability


router = APIRouter(tags=["integrations"])


class ProviderCatalogResponse(BaseModel):
    environment: str
    external_connectors_enabled: bool
    selected: list[dict[str, object]]
    providers: list[dict[str, object]]


class IntegrationProfileResponse(BaseModel):
    profile: object


class SecretReferencesResponse(BaseModel):
    provider: str
    references: list[SecretReference]


class ArtifactListResponse(BaseModel):
    store: str
    artifacts: list[ArtifactRecord]


@router.get("/integrations/providers", response_model=ProviderCatalogResponse)
def read_provider_catalog(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
    include_external: bool = Query(default=False),
) -> ProviderCatalogResponse:
    catalog = build_provider_catalog().as_dict(include_external=include_external)
    return ProviderCatalogResponse(**catalog)


@router.get("/integrations/profile", response_model=IntegrationProfileResponse)
def read_integration_profile(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> IntegrationProfileResponse:
    return IntegrationProfileResponse(profile=build_integration_profile().model_dump(mode="json"))


@router.get("/integrations/secrets/references", response_model=SecretReferencesResponse)
def read_secret_references(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_AUDIT))],
) -> SecretReferencesResponse:
    if not secret_provider_registry.has(settings.default_secret_provider):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Secret provider '{settings.default_secret_provider}' is not registered",
        )
    provider = secret_provider_registry.create(settings.default_secret_provider)
    return SecretReferencesResponse(
        provider=settings.default_secret_provider,
        references=provider.list_references(),
    )


@router.get("/integrations/artifacts", response_model=ArtifactListResponse)
def list_local_artifacts(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
    context_id: str | None = None,
) -> ArtifactListResponse:
    if not artifact_store_registry.has(settings.default_artifact_store):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Artifact store '{settings.default_artifact_store}' is not registered",
        )
    store = artifact_store_registry.create(settings.default_artifact_store)
    return ArtifactListResponse(
        store=settings.default_artifact_store,
        artifacts=store.list(context_id=context_id),
    )
