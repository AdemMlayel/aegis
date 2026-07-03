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


def _deterministic_demo_mode() -> bool:
    return _env_bool("AEGISQA_DETERMINISTIC_DEMO_MODE", False)


def _provider_default(env_name: str, normal_default: str, deterministic_default: str) -> str:
    if _deterministic_demo_mode():
        return deterministic_default
    return os.getenv(env_name, normal_default)


class Settings(BaseModel):
    """Central environment-driven settings for local/demo operation.

    The defaults are intentionally local: no company APIs or embedded secrets.
    Ollama provides real local inference, while external providers require
    explicit server-side configuration.
    """

    app_name: str = "AegisQA"
    environment: str = Field(default_factory=lambda: os.getenv("AEGISQA_ENV", "local"))
    deterministic_demo_mode: bool = Field(default_factory=_deterministic_demo_mode)
    workflow_schema_version: str = "0.15.0"
    sqlite_db_path: str | None = Field(
        default_factory=lambda: os.getenv("AEGISQA_SQLITE_DB_PATH")
    )
    generated_root: str | None = Field(
        default_factory=lambda: os.getenv("AEGISQA_GENERATED_ROOT")
    )
    knowledge_documents_dir: str | None = Field(
        default_factory=lambda: os.getenv("AEGISQA_KNOWLEDGE_DOCUMENTS_DIR")
    )
    storage_backend: str = Field(default_factory=lambda: os.getenv("AEGISQA_STORAGE_BACKEND", "sqlite"))
    database_url: str | None = Field(default_factory=lambda: os.getenv("AEGISQA_DATABASE_URL"))
    robot_docker_image: str = Field(default_factory=lambda: os.getenv("AEGISQA_ROBOT_DOCKER_IMAGE", "aegisqa-robot-runner:local"))
    robot_docker_timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_ROBOT_DOCKER_TIMEOUT_SECONDS", "180")))

    auth_mode: str = Field(default_factory=lambda: os.getenv("AEGISQA_AUTH_MODE", "permissive"))
    local_user: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_USER", "local-user"))
    local_role: str = Field(default_factory=lambda: os.getenv("AEGISQA_LOCAL_ROLE", "qa_lead"))
    # Shared secret that a trusted reverse proxy must send (header
    # X-Aegis-Auth-Secret) for X-Aegis-* identity headers to be honored. When
    # unset, header identity is trusted as-is (local/demo behavior). Set this in
    # any exposed deployment so identity headers can't be spoofed by arbitrary
    # callers. Secrets belong only in the gitignored .env, never committed.
    trusted_auth_header_secret: str | None = Field(default_factory=lambda: os.getenv("AEGISQA_TRUSTED_AUTH_HEADER_SECRET"))
    # Comma-separated list of allowed browser origins for CORS. Empty means the
    # local dev origins only. Never use "*" together with credentials.
    cors_allow_origins: str = Field(default_factory=lambda: os.getenv("AEGISQA_CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))

    default_ticket_connector: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_TICKET_CONNECTOR", "demo", "demo"))
    default_execution_adapter: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_EXECUTION_ADAPTER", "robot", "mock"))
    default_artifact_store: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_ARTIFACT_STORE", "local_fs", "local_fs"))
    default_secret_provider: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_SECRET_PROVIDER", "mock_vault", "mock_vault"))
    external_connectors_enabled: bool = Field(default_factory=lambda: _env_bool("AEGISQA_EXTERNAL_CONNECTORS_ENABLED", False))

    default_llm_provider: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_LLM_PROVIDER", "ollama", "mock_llm"))
    default_embedding_provider: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_EMBEDDING_PROVIDER", "ollama_nomic_embed_text", "local_hash_embeddings"))
    default_knowledge_store: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_KNOWLEDGE_STORE", "local_knowledge", "local_knowledge"))
    default_memory_store: str = Field(default_factory=lambda: _provider_default("AEGISQA_DEFAULT_MEMORY_STORE", "local_episodic_memory", "local_episodic_memory"))

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
    # Total context window (prompt + output) of the served model. Used to clamp
    # requested max_output_tokens so prompt+max_tokens never exceeds the window —
    # otherwise servers like vLLM reject the request with HTTP 400 and the agent
    # silently falls back to the mock provider. 0 disables clamping.
    openai_compatible_context_window: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_OPENAI_COMPATIBLE_CONTEXT_WINDOW", "0")))
    # Minimum output tokens to preserve when clamping, so a large prompt still
    # leaves room for a usable answer.
    openai_compatible_min_output_tokens: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_OPENAI_COMPATIBLE_MIN_OUTPUT_TOKENS", "256")))

    # When true, chat messages that the deterministic classifier maps to
    # "unknown" are answered by the configured LLM, grounded with system
    # knowledge and retrieved RAG context, instead of the generic fallback.
    # The LLM is used for free-form ANSWERS only — it never triggers actions.
    # Off by default (and forced off in deterministic demo mode) so the copilot
    # stays fully deterministic unless a real provider is explicitly enabled.
    chat_llm_fallback_enabled: bool = Field(default_factory=lambda: (not _deterministic_demo_mode()) and _env_bool("AEGISQA_CHAT_LLM_FALLBACK_ENABLED", False))
    chat_llm_max_output_tokens: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_CHAT_LLM_MAX_OUTPUT_TOKENS", "512")))

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
    # W7: when True, an agent whose policy carries require_human_approval=True
    # may only run inside a workflow context that already holds a granted human
    # approval -- a real runtime gate instead of inert advisory metadata. Default
    # False preserves the autonomous generate-then-approve pipeline (those agents
    # legitimately produce the artifacts a human later approves); turn it on for
    # deployments that must hard-block approval-required agents pre-approval.
    enforce_agent_human_approval: bool = Field(default_factory=lambda: _env_bool("AEGISQA_ENFORCE_AGENT_HUMAN_APPROVAL", False))
    organization_daily_token_quota: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_ORGANIZATION_DAILY_TOKEN_QUOTA", "1000000")))
    token_reservation_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("AEGISQA_TOKEN_RESERVATION_TTL_SECONDS", "300")))
    external_input_cost_per_1k: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_EXTERNAL_INPUT_COST_PER_1K", "0.00015")))
    external_output_cost_per_1k: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_EXTERNAL_OUTPUT_COST_PER_1K", "0.0006")))
    observability_error_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OBSERVABILITY_ERROR_RATE_THRESHOLD", "0.05")))
    observability_agent_failure_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OBSERVABILITY_AGENT_FAILURE_RATE_THRESHOLD", "0.10")))
    # Operational-health signal: warn when the share of model calls that silently
    # degraded to the deterministic mock provider exceeds this fraction of today's
    # calls. Catches the system's #1 trust risk (a real provider failing and the
    # output quietly becoming mock) which no other health signal observes.
    observability_mock_fallback_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("AEGISQA_OBSERVABILITY_MOCK_FALLBACK_RATE_THRESHOLD", "0.0")))
    # When False, a failed real-LLM call raises instead of silently returning a
    # deterministic mock response. Default True preserves the local/demo
    # graceful-degradation behavior; set False in any environment where a mock
    # answer presented as real output is unacceptable (fail-closed).
    allow_mock_fallback: bool = Field(default_factory=lambda: _env_bool("AEGISQA_ALLOW_MOCK_FALLBACK", True))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
