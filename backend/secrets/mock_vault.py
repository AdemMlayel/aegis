from __future__ import annotations

from backend.secrets.base import (
    BaseSecretProvider,
    SecretProviderMode,
    SecretReference,
    secret_provider_registry,
)


_DEFAULT_REFERENCES = (
    "jira/api-token",
    "git/robot-repository-token",
    "execution/browser-grid-token",
)


@secret_provider_registry.register(
    name="mock_vault",
    mode=SecretProviderMode.MOCK,
    description="Mock Vault-compatible provider that returns secret references only and never stores real credentials.",
    requires_external_api=False,
    resolves_values=False,
)
class MockVaultSecretProvider(BaseSecretProvider):
    def __init__(self, names: tuple[str, ...] = _DEFAULT_REFERENCES) -> None:
        self._names = names

    def reference(self, name: str) -> SecretReference:
        normalized_name = name.strip().strip("/")
        if not normalized_name:
            raise ValueError("Secret reference name cannot be empty")
        return SecretReference(
            provider=self.spec.name,
            name=normalized_name,
            uri=f"mock-vault://{normalized_name}",
            masked_value="********",
            external_resolution_required=False,
        )

    def list_references(self) -> list[SecretReference]:
        return [self.reference(name) for name in self._names]
