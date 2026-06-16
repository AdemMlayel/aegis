from __future__ import annotations

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AegisQA"
    environment: str = os.getenv("AEGISQA_ENV", "local")
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


settings = Settings()
