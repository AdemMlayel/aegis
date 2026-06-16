from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.security import Capability, Principal, Role, get_current_principal
from backend.security.rbac import ROLE_CAPABILITIES


router = APIRouter(tags=["security"])


@router.get("/security/me", response_model=Principal)
def read_current_principal(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    return principal


@router.get("/security/rbac")
def read_rbac_matrix() -> dict[str, object]:
    return {
        "roles": {
            role.value: sorted(capability.value for capability in capabilities)
            for role, capabilities in ROLE_CAPABILITIES.items()
        },
        "capabilities": [capability.value for capability in Capability],
        "supported_roles": [role.value for role in Role],
    }
