from __future__ import annotations

from typing import Literal

from backend.config.settings import settings
from backend.embeddings import embedding_provider_registry
from backend.llm import llm_provider_registry


ConfigurationStatus = Literal["ready", "disabled", "unconfigured"]


def llm_provider_metadata(name: str) -> dict[str, object]:
    spec = llm_provider_registry.get(name).spec
    configuration_keys: list[str] = []
    status: ConfigurationStatus = "ready"
    selectable = True

    if spec.name == "openai_compatible":
        configuration_keys = [
            "AEGISQA_EXTERNAL_CONNECTORS_ENABLED",
            "AEGISQA_OPENAI_COMPATIBLE_BASE_URL",
            "AEGISQA_OPENAI_COMPATIBLE_API_KEY",
            "AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL",
        ]
        if not settings.external_connectors_enabled:
            status = "disabled"
            selectable = False
        elif (
            not settings.openai_compatible_base_url
            or not settings.openai_compatible_api_key
        ):
            status = "unconfigured"
            selectable = False

    return {
        "configuration_status": status,
        "configuration_keys": configuration_keys,
        "selectable": selectable,
    }


def embedding_provider_metadata(name: str) -> dict[str, object]:
    spec = embedding_provider_registry.get(name).spec
    status: ConfigurationStatus = "ready"
    selectable = True
    configuration_keys: list[str] = []
    if spec.name == "ollama_nomic_embed_text":
        configuration_keys = [
            "AEGISQA_OLLAMA_BASE_URL",
            "AEGISQA_OLLAMA_EMBEDDING_MODEL",
        ]
    if spec.requires_external_api and not settings.external_connectors_enabled:
        status = "disabled"
        selectable = False
    return {
        "configuration_status": status,
        "configuration_keys": configuration_keys,
        "selectable": selectable,
    }


def validate_llm_provider_selection(name: str) -> None:
    if not llm_provider_registry.has(name):
        raise ValueError(f"LLM provider '{name}' is not registered")
    metadata = llm_provider_metadata(name)
    if metadata["selectable"]:
        return
    if metadata["configuration_status"] == "disabled":
        raise ValueError(
            f"LLM provider '{name}' is disabled. Set "
            "AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true on the server."
        )
    raise ValueError(
        f"LLM provider '{name}' is not configured. Set the required server-side "
        "endpoint and credential environment variables."
    )


def validate_embedding_provider_selection(name: str) -> None:
    if not embedding_provider_registry.has(name):
        raise ValueError(f"Embedding provider '{name}' is not registered")
    metadata = embedding_provider_metadata(name)
    if metadata["selectable"]:
        return
    raise ValueError(f"Embedding provider '{name}' is disabled.")
