from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AegisQA"
    environment: str = "local"
    workflow_schema_version: str = "0.1.0"


settings = Settings()
