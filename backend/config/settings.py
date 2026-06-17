from __future__ import annotations

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AegisQA"
    environment: str = os.getenv("AEGISQA_ENV", "local")
    database_url: str = os.getenv("AEGISQA_DATABASE_URL", "sqlite:///generated/storage/aegisqa.sqlite3")
    workflow_schema_version: str = "0.10.0"
    auth_mode: str = os.getenv("AEGISQA_AUTH_MODE", "permissive")
    local_user: str = os.getenv("AEGISQA_LOCAL_USER", "local-user")
    local_role: str = os.getenv("AEGISQA_LOCAL_ROLE", "qa_lead")
    default_ticket_connector: str = os.getenv("AEGISQA_DEFAULT_TICKET_CONNECTOR", "jira_mock")
    default_execution_adapter: str = os.getenv("AEGISQA_DEFAULT_EXECUTION_ADAPTER", "mock")
    default_artifact_store: str = os.getenv("AEGISQA_DEFAULT_ARTIFACT_STORE", "local_fs")
    default_secret_provider: str = os.getenv("AEGISQA_DEFAULT_SECRET_PROVIDER", "mock_vault")
    external_connectors_enabled: bool = os.getenv("AEGISQA_EXTERNAL_CONNECTORS_ENABLED", "false").lower() == "true"
    default_llm_provider: str = os.getenv("AEGISQA_DEFAULT_LLM_PROVIDER", "mock_llm")
    llm_http_timeout_seconds: float = float(os.getenv("AEGISQA_LLM_HTTP_TIMEOUT_SECONDS", "60"))
    openai_compatible_base_url: str = os.getenv("AEGISQA_OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1")
    openai_compatible_api_key: str | None = os.getenv("AEGISQA_OPENAI_COMPATIBLE_API_KEY")
    openai_compatible_model: str = os.getenv("AEGISQA_OPENAI_COMPATIBLE_MODEL", "gpt-4o-mini")
    openai_compatible_temperature: float = float(os.getenv("AEGISQA_OPENAI_COMPATIBLE_TEMPERATURE", "0.2"))
    ollama_base_url: str = os.getenv("AEGISQA_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("AEGISQA_OLLAMA_MODEL", os.getenv("AEGISQA_OLLAMA_MAIN_MODEL", "qwen3:3b"))
    ollama_temperature: float = float(os.getenv("AEGISQA_OLLAMA_TEMPERATURE", "0.2"))
    ollama_discovery_timeout_seconds: float = float(os.getenv("AEGISQA_OLLAMA_DISCOVERY_TIMEOUT_SECONDS", "2"))
    ollama_main_model: str = os.getenv("AEGISQA_OLLAMA_MAIN_MODEL", os.getenv("AEGISQA_OLLAMA_MODEL", "qwen3:3b"))
    ollama_rag_model: str = os.getenv("AEGISQA_OLLAMA_RAG_MODEL", os.getenv("AEGISQA_OLLAMA_MAIN_MODEL", "qwen3:3b"))
    ollama_baseline_model: str = os.getenv("AEGISQA_OLLAMA_BASELINE_MODEL", "llama3.1:8b")
    ollama_coding_model: str = os.getenv("AEGISQA_OLLAMA_CODING_MODEL", "qwen3-coder:latest")
    ollama_fast_model: str = os.getenv("AEGISQA_OLLAMA_FAST_MODEL", "phi4-mini:latest")
    ollama_fast_fallback_model: str = os.getenv("AEGISQA_OLLAMA_FAST_FALLBACK_MODEL", "gemma3:4b")
    ollama_reasoning_model: str = os.getenv("AEGISQA_OLLAMA_REASONING_MODEL", "deepseek-r1:7b")
    ollama_reasoning_fallback_model: str = os.getenv("AEGISQA_OLLAMA_REASONING_FALLBACK_MODEL", "deepseek-r1:8b")
    ollama_embedding_model: str = os.getenv("AEGISQA_OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    ollama_embedding_fallback_model: str = os.getenv("AEGISQA_OLLAMA_EMBEDDING_FALLBACK_MODEL", "nomic-embed-text")
    default_knowledge_store: str = os.getenv("AEGISQA_DEFAULT_KNOWLEDGE_STORE", "local_knowledge")
    default_memory_store: str = os.getenv("AEGISQA_DEFAULT_MEMORY_STORE", "local_episodic_memory")
    default_embedding_model: str = os.getenv("AEGISQA_DEFAULT_EMBEDDING_MODEL", "local_hash_embedding")
    default_vector_store: str = os.getenv("AEGISQA_DEFAULT_VECTOR_STORE", "local_in_memory_vector")
    default_reranker: str = os.getenv("AEGISQA_DEFAULT_RERANKER", "local_hybrid_reranker")
    memory_retention_days: int = int(os.getenv("AEGISQA_MEMORY_RETENTION_DAYS", "90"))
    execution_worker_backend: str = os.getenv("AEGISQA_EXECUTION_WORKER_BACKEND", "local")
    execution_worker_poll_interval_seconds: float = float(
        os.getenv("AEGISQA_EXECUTION_WORKER_POLL_INTERVAL_SECONDS", "1.0")
    )
    execution_worker_batch_size: int = int(os.getenv("AEGISQA_EXECUTION_WORKER_BATCH_SIZE", "5"))
    celery_broker_url: str = os.getenv("AEGISQA_CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    celery_result_backend: str = os.getenv("AEGISQA_CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")
    celery_task_name: str = os.getenv("AEGISQA_CELERY_EXECUTION_TASK", "aegisqa.execution.process_run")
    celery_fallback_to_local: bool = os.getenv("AEGISQA_CELERY_FALLBACK_TO_LOCAL", "true").lower() == "true"


settings = Settings()
