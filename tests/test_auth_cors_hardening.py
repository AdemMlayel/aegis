"""Phase 1 hardening — C3 (auth fail-closed + non-spoofable identity headers),
C4 (CORS allow-list), S7 (rate-limit key anchored to client IP).

These prove the exposure-gate fixes: permissive auth cannot run outside a local
environment, identity headers require a trusted-proxy secret when one is
configured, and CORS only permits allow-listed origins.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_permissive_auth_refused_outside_local_environment(monkeypatch) -> None:
    # Default permissive mode must NOT hand out an anonymous QA_LEAD when the
    # service is not running locally (e.g. exposed via a tunnel/prod).
    monkeypatch.setenv("AEGISQA_ENV", "production")
    monkeypatch.delenv("AEGISQA_AUTH_MODE", raising=False)
    client = TestClient(app)
    response = client.get("/api/v1/security/me")
    assert response.status_code == 401
    assert "Permissive authentication is disabled" in response.json()["detail"]


def test_permissive_auth_allowed_locally(monkeypatch) -> None:
    monkeypatch.setenv("AEGISQA_ENV", "local")
    monkeypatch.delenv("AEGISQA_AUTH_MODE", raising=False)
    client = TestClient(app)
    response = client.get("/api/v1/security/me")
    assert response.status_code == 200
    assert response.json()["auth_mode"] == "permissive"


def test_identity_headers_require_trusted_secret_when_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AEGISQA_AUTH_MODE", "strict")
    monkeypatch.setenv("AEGISQA_TRUSTED_AUTH_HEADER_SECRET", "proxy-shared-secret")
    client = TestClient(app)

    # Spoofed identity headers WITHOUT the shared secret are rejected — this is
    # the public-tunnel attack (anyone sets X-Aegis-Role: admin).
    spoofed = client.get(
        "/api/v1/security/me",
        headers={"X-Aegis-User": "attacker", "X-Aegis-Role": "admin"},
    )
    assert spoofed.status_code == 401
    assert spoofed.json()["detail"] == "Untrusted identity headers"

    # The trusted reverse proxy, presenting the secret, is honored.
    trusted = client.get(
        "/api/v1/security/me",
        headers={
            "X-Aegis-User": "real-admin",
            "X-Aegis-Role": "admin",
            "X-Aegis-Auth-Secret": "proxy-shared-secret",
        },
    )
    assert trusted.status_code == 200
    assert trusted.json()["user_id"] == "real-admin"

    # A wrong secret is rejected.
    wrong = client.get(
        "/api/v1/security/me",
        headers={
            "X-Aegis-User": "attacker",
            "X-Aegis-Role": "admin",
            "X-Aegis-Auth-Secret": "wrong",
        },
    )
    assert wrong.status_code == 401


def test_cors_allows_listed_origin_and_rejects_unknown(monkeypatch) -> None:
    client = TestClient(app)

    # An allow-listed origin gets the CORS echo header.
    allowed = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert allowed.headers.get("access-control-allow-origin") == (
        "http://localhost:5173"
    )

    # An unknown origin does NOT receive an allow-origin header (browser blocks).
    blocked = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in blocked.headers
