from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        normalized_name = name.strip()
        normalized_value = value.strip()
        if (
            len(normalized_value) >= 2
            and normalized_value[0] == normalized_value[-1]
            and normalized_value[0] in {"'", '"'}
        ):
            normalized_value = normalized_value[1:-1]
        if normalized_name:
            os.environ.setdefault(normalized_name, normalized_value)


_load_local_env()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    """Central environment-driven settings for local/demo operation.

    The defaults are intentionally local: no company APIs or embedded secrets.
    Ollama provides real local inference, while external providers require
    explicit server-side configuration.
    """

    app_name: str = "AegisQA"
    environment: str = Field(default_factory=lambda: os.getenv("AEGISQA_ENV", "local"))
    workflow_schema_version: str = "0.15.0"
    sqlite_db_path: str | None = Field(
        default_factory=lambda: os.getenv("AEGISQA_SQLITE_DB_PATH")
    )
    generated_root: str | None = Field(
        default_factory=lambda: os.getenv("AEGISQA_GENERATED_ROOT")
    )

    auth_mode: str = Field(default_factory=lambda: os.getenv("AEGISQA_AUTH_MODE", "permissive"))
    local_user: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_USER", "local-user"))
    local_role: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_ROLE", "qa_lead"))

    default_ticket_connector: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_TICKET_CONNECTOR", "jira_mock"))
    default_execution_adapter: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_EXECUTION_ADAPTER", "robot"))
    default_artifact_store: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_ARTIFACT_STORE", "local_fs"))
    default_secret_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_SECRET_PROVIDER", "mock_vault"))
    external_connectors_enabled: bool = Field(default_factory=lambda: _env_bool("AEGISQA_EXTERNAL_CONNECTORS_ENABLED", False))

    default_llm_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_LLM_PROVIDER", "ollama"))
    default_embedding_provider: str = Field(default_factory=lambda: os.getenv("AEGISQA_DEFAULT_EMBEDDING_PROVIDER", "ollama_nomic_embed_text"))
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
    execution_worker_batch_size: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_EXECUTION_WORKER_BATCH_SIZE", "10")))
    execution_worker_poll_interval_seconds: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_EXECUTION_WORKER_POLL_INTERVAL_SECONDS", "1")))
    celery_broker_url: str = Field(default_factory=lambda: os.getenv("AEGISQA_CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"))
    celery_result_backend: str = Field(default_factory=lambda: os.getenv("AEGISQA_CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"))
    celery_task_name: str = Field(default_factory=lambda: os.getenv("AEGISQA_CELERY_EXECUTION_TASK", "aegisqa.execution.process_run"))
    celery_fallback_to_local: bool = Field(default_factory=lambda: _env_bool("AEGISQA_CELERY_FALLBACK_TO_LOCAL", True))

    gateway_requests_per_minute: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_GATEWAY_REQUESTS_PER_MINUTE", "240")))
    gateway_daily_request_quota: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_GATEWAY_DAILY_REQUEST_QUOTA", "10000")))
    gateway_request_timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_GATEWAY_REQUEST_TIMEOUT_SECONDS", "60")))
    provider_circuit_failure_threshold: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_PROVIDER_CIRCUIT_FAILURE_THRESHOLD", "3")))
    provider_circuit_reset_seconds: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_PROVIDER_CIRCUIT_RESET_SECONDS", "30")))
    agent_max_model_calls_per_workflow: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_AGENT_MAX_MODEL_CALLS_PER_WORKFLOW", "24")))
    agent_max_tokens_per_call: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_AGENT_MAX_TOKENS_PER_CALL", "16000")))
    agent_max_tokens_per_workflow: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_AGENT_MAX_TOKENS_PER_WORKFLOW", "120000")))
    organization_daily_token_quota: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_ORGANIZATION_DAILY_TOKEN_QUOTA", "1000000")))
    token_reservation_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_TOKEN_RESERVATION_TTL_SECONDS", "300")))
    external_input_cost_per_1k: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_EXTERNAL_INPUT_COST_PER_1K", "0.00015")))
    external_output_cost_per_1k: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_EXTERNAL_OUTPUT_COST_PER_1K", "0.0006")))
    observability_error_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OBSERVABILITY_ERROR_RATE_THRESHOLD", "0.05")))
    observability_agent_failure_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OBSERVABILITY_AGENT_FAILURE_RATE_THRESHOLD", "0.10")))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
