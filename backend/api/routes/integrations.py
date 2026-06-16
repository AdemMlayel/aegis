from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.artifacts import ArtifactRecord
from backend.secrets import SecretReference
from backend.security import Capability, Principal, require_capability
from backend.services.integrations import (
    IntegrationConfigurationError,
    list_local_artifacts as list_local_artifacts_service,
    read_integration_profile as read_integration_profile_service,
    read_provider_catalog as read_provider_catalog_service,
    read_secret_references as read_secret_references_service,
)


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
    catalog = read_provider_catalog_service(include_external=include_external)
    return ProviderCatalogResponse(**catalog)


@router.get("/integrations/profile", response_model=IntegrationProfileResponse)
def read_integration_profile(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> IntegrationProfileResponse:
    return IntegrationProfileResponse(profile=read_integration_profile_service())


@router.get("/integrations/secrets/references", response_model=SecretReferencesResponse)
def read_secret_references(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_AUDIT))],
) -> SecretReferencesResponse:
    try:
        provider, references = read_secret_references_service()
    except IntegrationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return SecretReferencesResponse(provider=provider, references=references)


@router.get("/integrations/artifacts", response_model=ArtifactListResponse)
def list_local_artifacts(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
    context_id: str | None = None,
) -> ArtifactListResponse:
    try:
        store, artifacts = list_local_artifacts_service(context_id=context_id)
    except IntegrationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return ArtifactListResponse(store=store, artifacts=artifacts)
