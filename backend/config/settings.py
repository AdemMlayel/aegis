from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel, Field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    """Central environment-driven settings for local/demo operation.

    The defaults are intentionally safe: no company APIs, no real secrets, and
    deterministic local providers. Real providers can be enabled later through
    explicit environment variables.
    """

    app_name: str = "AegisQA"
    environment: str = Field(default_factory=lambda: os.getenv("AEGISQA_ENV", "local"))
    workflow_schema_version: str = "0.12.0"

    auth_mode: str = Field(default_factory=lambda: os.getenv("AEGISQA_AUTH_MODE", "permissive"))
    local_user: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_USER", "local-user"))
    local_role: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_ROLE", "qa_lead"))

    default_ticket_connector: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_TICKET_CONNECTOR", "jira_mock"))
    default_execution_adapter: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_EXECUTION_ADAPTER", "mock"))
    default_artifact_store: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_ARTIFACT_STORE", "local_fs"))
    default_secret_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_SECRET_PROVIDER", "mock_vault"))
    external_connectors_enabled: bool = Field(default_factory=lambda: _env_bool("AEGISQA_EXTERNAL_CONNECTORS_ENABLED", False))

    default_llm_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_LLM_PROVIDER", "mock_llm"))
    default_embedding_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_EMBEDDING_PROVIDER", "local_hash_embeddings"))
    default_knowledge_store: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_KNOWLEDGE_STORE", "local_knowledge"))
    default_memory_store: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_MEMORY_STORE", "local_episodic_memory"))

    ollama_base_url: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    ollama_chat_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_CHAT_MODEL", "qwen3:3b"))
    ollama_rag_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_RAG_MODEL", "qwen3:3b"))
    ollama_baseline_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_BASELINE_MODEL", "llama3.1:8b"))
    ollama_coding_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_CODING_MODEL", "qwen3-coder"))
    ollama_fast_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_FAST_MODEL", "phi4-mini"))
    ollama_fast_fallback_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_FAST_FALLBACK_MODEL", "gemma3:4b"))
    ollama_reasoning_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_REASONING_MODEL", "deepseek-r1:8b"))
    ollama_reasoning_fallback_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_REASONING_FALLBACK_MODEL", "deepseek-r1:7b"))
    ollama_embedding_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b"))
    ollama_embedding_fallback_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OLLAMA_EMBEDDING_FALLBACK_MODEL", "nomic-embed-text"))
    ollama_timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_OLLAMA_TIMEOUT_SECONDS", "20")))
    ollama_discovery_timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OLLAMA_DISCOVERY_TIMEOUT_SECONDS", "2")))
    llm_http_timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_LLM_HTTP_TIMEOUT_SECONDS", "20")))
    ollama_temperature: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OLLAMA_TEMPERATURE", "0.1")))

    openai_compatible_base_url: str | None = Field(default_factory=lambda: os.getenv("AEGISQA_OPENAI_COMPATIBLE_BASE_URL"))
    openai_compatible_api_key: str | None = Field(default_factory=lambda: os.getenv("AEGISQA_OPENAI_COMPATIBLE_API_KEY"))
    openai_compatible_chat_model: str = Field(default_factory=lambda: os.getenv("AEGISQA_OPENAI_COMPATIBLE_CHAT_MODEL", "gpt-4o-mini"))

    execution_worker_backend: str = Field(default_factory=lambda: os.getenv("AEGISQA_EXECUTION_WORKER_BACKEND", "local"))
    celery_task_name: str = Field(default_factory=lambda: os.getenv("AEGISQA_CELERY_EXECUTION_TASK", "aegisqa.execution.process_run"))
    celery_fallback_to_local: bool = Field(default_factory=lambda: _env_bool("AEGISQA_CELERY_FALLBACK_TO_LOCAL", True))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
