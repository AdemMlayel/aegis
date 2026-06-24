from __future__ import annotations

import os
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, Field


class Capability(StrEnum):
    READ_TICKETS = "read:tickets"
    WRITE_TICKETS = "write:tickets"
    START_WORKFLOW = "start:workflow"
    READ_WORKFLOW = "read:workflow"
    APPROVE_WORKFLOW = "approve:workflow"
    EXECUTE_WORKFLOW = "execute:workflow"
    READ_ARTIFACTS = "read:artifacts"
    EDIT_ARTIFACTS = "edit:artifacts"
    READ_AUDIT = "read:audit"


class Role(StrEnum):
    VIEWER = "viewer"
    QA_ENGINEER = "qa_engineer"
    QA_LEAD = "qa_lead"
    ADMIN = "admin"


ROLE_CAPABILITIES: dict[Role, set[Capability]] = {
    Role.VIEWER: {
        Capability.READ_TICKETS,
        Capability.READ_WORKFLOW,
        Capability.READ_ARTIFACTS,
    },
    Role.QA_ENGINEER: {
        Capability.READ_TICKETS,
        Capability.WRITE_TICKETS,
        Capability.START_WORKFLOW,
        Capability.READ_WORKFLOW,
        Capability.EXECUTE_WORKFLOW,
        Capability.READ_ARTIFACTS,
        Capability.EDIT_ARTIFACTS,
    },
    Role.QA_LEAD: {
        Capability.READ_TICKETS,
        Capability.WRITE_TICKETS,
        Capability.START_WORKFLOW,
        Capability.READ_WORKFLOW,
        Capability.APPROVE_WORKFLOW,
        Capability.EXECUTE_WORKFLOW,
        Capability.READ_ARTIFACTS,
        Capability.EDIT_ARTIFACTS,
        Capability.READ_AUDIT,
    },
    Role.ADMIN: set(Capability),
}


class Principal(BaseModel):
    user_id: str = Field(min_length=1)
    role: Role
    capabilities: set[Capability] = Field(default_factory=set)
    auth_mode: str = "local"

    def can(self, capability: Capability) -> bool:
        return capability in self.capabilities


def _auth_mode() -> str:
    return os.getenv("AEGISQA_AUTH_MODE", "permissive").strip().lower()


def _local_principal() -> Principal:
    role = Role(os.getenv("AEGISQA_LOCAL_ROLE", Role.QA_LEAD).strip())
    return Principal(
        user_id=os.getenv("AEGISQA_LOCAL_USER", "local-user"),
        role=role,
        capabilities=ROLE_CAPABILITIES[role],
        auth_mode="permissive",
    )


def get_current_principal(
    authorization: Annotated[str | None, Header()] = None,
    x_aegis_user: Annotated[str | None, Header(alias="X-Aegis-User")] = None,
    x_aegis_role: Annotated[str | None, Header(alias="X-Aegis-Role")] = None,
) -> Principal:
    """Resolve the current API principal.

    Local development defaults to permissive mode so the architecture can be
    demonstrated with mock data without an identity provider.  Strict mode can
    be enabled with ``AEGISQA_AUTH_MODE=strict`` and then requires either a
    development bearer token or explicit local headers.
    """
    mode = _auth_mode()
    if mode != "strict" and not authorization and not x_aegis_user and not x_aegis_role:
        return _local_principal()

    expected_token = os.getenv("AEGISQA_DEV_TOKEN")
    if authorization and expected_token:
        scheme, _, token = authorization.partition(" ")
        if scheme.casefold() == "bearer" and token == expected_token:
            role = Role(os.getenv("AEGISQA_TOKEN_ROLE", Role.QA_LEAD).strip())
            return Principal(
                user_id=os.getenv("AEGISQA_TOKEN_USER", "token-user"),
                role=role,
                capabilities=ROLE_CAPABILITIES[role],
                auth_mode=mode,
            )

    if x_aegis_user and x_aegis_role:
        try:
            role = Role(x_aegis_role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported AegisQA role",
            ) from exc
        return Principal(
            user_id=x_aegis_user,
            role=role,
            capabilities=ROLE_CAPABILITIES[role],
            auth_mode=mode,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required",
    )


def require_capability(capability: Capability):
    def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if not principal.can(capability):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Capability required: {capability}",
            )
        return principal

    return dependency
