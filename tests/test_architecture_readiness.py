from __future__ import annotations

import os

from fastapi.testclient import TestClient

from backend.config.settings import settings
from backend.execution import RobotExecutionAdapter, execution_adapter_registry
from backend.main import app
from backend.security import Capability, Role
from backend.security.rbac import ROLE_CAPABILITIES
from backend.tickets import MockJiraTicketConnector, ticket_connector_registry
from backend.tools.base import BaseTool, ToolRegistry


def test_security_rbac_matrix_and_strict_mode(monkeypatch) -> None:
    assert Capability.APPROVE_WORKFLOW in ROLE_CAPABILITIES[Role.QA_LEAD]
    assert Capability.APPROVE_WORKFLOW not in ROLE_CAPABILITIES[Role.QA_ENGINEER]

    monkeypatch.setenv("AEGISQA_AUTH_MODE", "strict")
    client = TestClient(app)
    assert client.get("/api/v1/security/me").status_code == 401

    response = client.get(
        "/api/v1/security/me",
        headers={"X-Aegis-User": "lead", "X-Aegis-Role": "qa_lead"},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == "lead"
    assert "approve:workflow" in response.json()["capabilities"]


def test_mock_jira_connector_boundary_is_registered_and_local() -> None:
    assert ticket_connector_registry.has("jira_mock") is True
    assert ticket_connector_registry.get("jira_mock") is MockJiraTicketConnector
    spec = ticket_connector_registry.get("jira_mock").spec
    assert spec.source == "jira"
    assert spec.requires_external_api is False

    connector = ticket_connector_registry.create("jira_mock")
    tickets = connector.search("refund")
    assert tickets
    assert all(ticket.source == "jira" for ticket in tickets)
    assert all(ticket.raw_url and ticket.raw_url.startswith("mock://jira/") for ticket in tickets)


def test_robot_execution_adapter_is_registered_without_external_api() -> None:
    assert execution_adapter_registry.has("robot") is True
    assert execution_adapter_registry.get("robot") is RobotExecutionAdapter
    spec = execution_adapter_registry.get("robot").spec
    assert spec.engine == "robot-framework"
    assert "artifact-capture" in spec.capabilities


def test_tool_contract_records_successful_invocation() -> None:
    registry = ToolRegistry()

    @registry.register(name="EchoTool", max_retries=1)
    class EchoTool(BaseTool):
        def invoke(self, **kwargs: object) -> dict[str, object]:
            return {"received": kwargs}

    result = registry.execute("EchoTool", actor="pytest", value="ok")

    assert result.value == {"received": {"value": "ok"}}
    assert result.record.status == "success"
    assert result.record.attempts == 1
    assert result.record.input_hash
    assert result.record.output_hash


def test_milestone3_provider_catalog_is_local_and_swappable() -> None:
    from backend.artifacts import LocalFilesystemArtifactStore, artifact_store_registry
    from backend.integrations.providers import ProviderKind, build_provider_catalog
    from backend.secrets import MockVaultSecretProvider, secret_provider_registry

    assert artifact_store_registry.has("local_fs") is True
    assert artifact_store_registry.get("local_fs") is LocalFilesystemArtifactStore
    assert secret_provider_registry.has("mock_vault") is True
    assert secret_provider_registry.get("mock_vault") is MockVaultSecretProvider

    catalog = build_provider_catalog()
    providers = catalog.list()
    assert providers
    assert all(provider.requires_external_api is False for provider in providers)

    selected = {selection.kind: selection.selected for selection in catalog.selections()}
    assert selected[ProviderKind.TICKET_CONNECTOR] == "jira_mock"
    assert selected[ProviderKind.ARTIFACT_STORE] == "local_fs"
    assert selected[ProviderKind.SECRET_PROVIDER] == "mock_vault"
    assert selected[ProviderKind.EXECUTION_ADAPTER] == "mock"


def test_integration_endpoints_expose_local_providers_only(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "external_connectors_enabled", False)
    monkeypatch.setattr(settings, "default_llm_provider", "mock_llm")
    client = TestClient(app)

    response = client.get("/api/v1/integrations/providers")
    assert response.status_code == 200
    body = response.json()
    assert body["external_connectors_enabled"] is False
    provider_names = {provider["name"] for provider in body["providers"]}
    assert {"jira_mock", "mock", "robot", "local_fs", "mock_vault"} <= provider_names
    assert all(provider["requires_external_api"] is False for provider in body["providers"])

    profile_response = client.get("/api/v1/integrations/profile")
    assert profile_response.status_code == 200
    profile = profile_response.json()["profile"]
    assert profile["policy"] == "mock_only"
    assert profile["ticket_connector"]["name"] == "jira_mock"
    assert profile["artifact_store"]["name"] == "local_fs"
    assert profile["secret_provider"]["name"] == "mock_vault"


def test_mock_vault_returns_references_without_secret_values() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/secrets/references")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock_vault"
    assert body["references"]
    assert all(ref["uri"].startswith("mock-vault://") for ref in body["references"])
    assert all(ref["masked_value"] == "********" for ref in body["references"])


def test_start_workflow_from_connector_uses_mock_jira_boundary(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "external_connectors_enabled", False)
    monkeypatch.setattr(settings, "default_llm_provider", "mock_llm")
    client = TestClient(app)

    response = client.post(
        "/api/v1/workflows/start-from-ticket-connector",
        json={"created_by": "pytest", "connector": "jira_mock", "ticket_id": "MOCK-101"},
    )
    assert response.status_code == 202
    context = response.json()["context"]
    assert context["ticket"]["source"] == "jira"
    assert context["ticket"]["raw_url"].startswith("mock://jira/")
    assert context["integration_profile"]["ticket_connector"]["name"] == "jira_mock"
    assert context["integration_profile"]["policy"] == "mock_only"
