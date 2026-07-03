from __future__ import annotations

import hmac
import os
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, Field


def _secret_matches(provided: str | None, expected: str) -> bool:
    """Constant-time comparison of a provided header secret to the expected one."""
    if not provided:
        return False
    return hmac.compare_digest(provided.strip(), expected)


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
    organization_id: str = Field(default="local", min_length=1)
    role: Role
    capabilities: set[Capability] = Field(default_factory=set)
    auth_mode: str = "local"

    def can(self, capability: Capability) -> bool:
        return capability in self.capabilities


def _auth_mode() -> str:
    return os.getenv("AEGISQA_AUTH_MODE", "permissive").strip().lower()


def _environment() -> str:
    return os.getenv("AEGISQA_ENV", "local").strip().lower()


def _local_principal() -> Principal:
    role = Role(os.getenv("AEGISQA_LOCAL_ROLE", Role.QA_LEAD).strip())
    return Principal(
        user_id=os.getenv("AEGISQA_LOCAL_USER", "local-user"),
        organization_id=os.getenv("AEGISQA_LOCAL_ORGANIZATION", "local"),
        role=role,
        capabilities=ROLE_CAPABILITIES[role],
        auth_mode="permissive",
    )


def _trusted_header_secret() -> str | None:
    raw = os.getenv("AEGISQA_TRUSTED_AUTH_HEADER_SECRET")
    return raw.strip() if raw else None


def get_current_principal(
    authorization: Annotated[str | None, Header()] = None,
    x_aegis_user: Annotated[str | None, Header(alias="X-Aegis-User")] = None,
    x_aegis_role: Annotated[str | None, Header(alias="X-Aegis-Role")] = None,
    x_aegis_organization: Annotated[
        str | None,
        Header(alias="X-Aegis-Organization"),
    ] = None,
    x_aegis_auth_secret: Annotated[
        str | None,
        Header(alias="X-Aegis-Auth-Secret"),
    ] = None,
) -> Principal:
    """Resolve the current API principal.

    Local development defaults to permissive mode so the architecture can be
    demonstrated with mock data without an identity provider.  Strict mode can
    be enabled with ``AEGISQA_AUTH_MODE=strict`` and then requires either a
    development bearer token or explicit local headers.

    Hardening (C3): permissive mode is refused outside the ``local`` environment
    so a non-local deployment can never silently fall back to an anonymous
    QA_LEAD.  When ``AEGISQA_TRUSTED_AUTH_HEADER_SECRET`` is configured, the
    ``X-Aegis-*`` identity headers are only honored if the caller also presents
    a matching ``X-Aegis-Auth-Secret`` (asserted by a trusted reverse proxy),
    so identity headers can't be spoofed by arbitrary internet callers.
    """
    mode = _auth_mode()

    # Fail closed: permissive auth must never run outside a local environment.
    if mode != "strict" and _environment() != "local":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Permissive authentication is disabled outside the local "
                "environment. Configure AEGISQA_AUTH_MODE=strict with a "
                "verified identity."
            ),
        )

    if mode != "strict" and not authorization and not x_aegis_user and not x_aegis_role:
        return _local_principal()

    expected_token = os.getenv("AEGISQA_DEV_TOKEN")
    if authorization and expected_token:
        scheme, _, token = authorization.partition(" ")
        if scheme.casefold() == "bearer" and token == expected_token:
            role = Role(os.getenv("AEGISQA_TOKEN_ROLE", Role.QA_LEAD).strip())
            return Principal(
                user_id=os.getenv("AEGISQA_TOKEN_USER", "token-user"),
                organization_id=os.getenv(
                    "AEGISQA_TOKEN_ORGANIZATION",
                    "local",
                ),
                role=role,
                capabilities=ROLE_CAPABILITIES[role],
                auth_mode=mode,
            )

    if x_aegis_user and x_aegis_role:
        # When a trusted-proxy secret is configured, identity headers are only
        # honored if the caller proves it presented the shared secret.
        required_secret = _trusted_header_secret()
        if required_secret is not None and not _secret_matches(
            x_aegis_auth_secret, required_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Untrusted identity headers",
            )
        try:
            role = Role(x_aegis_role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported AegisQA role",
            ) from exc
        return Principal(
            user_id=x_aegis_user,
            organization_id=x_aegis_organization or "local",
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
