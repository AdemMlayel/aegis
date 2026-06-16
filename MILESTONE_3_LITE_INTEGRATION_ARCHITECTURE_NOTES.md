# Milestone 3 Lite — Integration Architecture Without Company APIs

## Goal

Milestone 3 Lite proves that AegisQA is integration-ready without depending on company Jira, Azure DevOps, GitLab, Vault, CI, browser grids, or internal environments.

The implementation keeps all runtime providers local or mocked while exposing the same boundaries that real providers will later implement.

## Implemented

- Generic provider catalog for selected integration providers.
- Local/mock provider profile stored on `TestContext.integration_profile`.
- Generic ticket connector start/search/health endpoints.
- Improved `jira_mock` connector boundary as the first Jira-shaped ticket provider.
- Local filesystem artifact store registry and `local_fs` implementation.
- Mock Vault-compatible secret provider registry and `mock_vault` implementation.
- Mock execution summary persisted as a local artifact-store object.
- Integration API routes for provider catalog, active integration profile, mock secret references, and local artifact listing.
- Tests proving the default provider set does not require external APIs.

## Deliberately Not Implemented Yet

The following remain out of scope until company setup is available:

- Real Jira REST API calls.
- Azure DevOps or GitLab issue providers.
- Company identity provider integration.
- Real Vault secret resolution.
- Real CI runner handoff.
- Company execution environments.
- Browser/device farms.
- Production artifact storage.

## Default Local Provider Set

```text
ticket_connector: jira_mock
execution_adapter: mock
artifact_store: local_fs
secret_provider: mock_vault
git_handoff: LocalGitHandoffTool
```

## New / Updated Endpoints

```text
GET  /api/v1/integrations/providers
GET  /api/v1/integrations/profile
GET  /api/v1/integrations/secrets/references
GET  /api/v1/integrations/artifacts
GET  /api/v1/tickets/connectors/{connector_name}/health
GET  /api/v1/tickets/connectors/{connector_name}/tickets
POST /api/v1/workflows/start-from-ticket-connector
```

## Configuration

```text
AEGISQA_DEFAULT_TICKET_CONNECTOR=jira_mock
AEGISQA_DEFAULT_EXECUTION_ADAPTER=mock
AEGISQA_DEFAULT_ARTIFACT_STORE=local_fs
AEGISQA_DEFAULT_SECRET_PROVIDER=mock_vault
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=false
```

External providers should later be registered with `requires_external_api=True` and remain disabled unless `AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true` and the relevant configuration is present.

## Verification

```bash
python -m pytest -q
# 76 passed
```
