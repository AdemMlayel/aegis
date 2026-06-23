from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.security import Capability, Principal, require_capability
from backend.artifacts import ArtifactRecord
from backend.secrets import SecretReference
from backend.services.integrations import (
    IntegrationConfigurationError,
    list_local_artifacts as service_list_local_artifacts,
    read_integration_profile as service_read_integration_profile,
    read_provider_catalog as service_read_provider_catalog,
    read_secret_references as service_read_secret_references,
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
    catalog = service_read_provider_catalog(include_external=include_external)
    return ProviderCatalogResponse(**catalog)


@router.get("/integrations/profile", response_model=IntegrationProfileResponse)
def read_integration_profile(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_WORKFLOW))],
) -> IntegrationProfileResponse:
    return IntegrationProfileResponse(profile=service_read_integration_profile())


@router.get("/integrations/secrets/references", response_model=SecretReferencesResponse)
def read_secret_references(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_AUDIT))],
) -> SecretReferencesResponse:
    try:
        provider_name, references = service_read_secret_references()
    except IntegrationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return SecretReferencesResponse(
        provider=provider_name,
        references=references,
    )


@router.get("/integrations/artifacts", response_model=ArtifactListResponse)
def list_local_artifacts(
    principal: Annotated[Principal, Depends(require_capability(Capability.READ_ARTIFACTS))],
    context_id: str | None = None,
) -> ArtifactListResponse:
    try:
        store_name, artifacts = service_list_local_artifacts(context_id=context_id)
    except IntegrationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return ArtifactListResponse(
        store=store_name,
        artifacts=artifacts,
    )
