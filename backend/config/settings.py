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
