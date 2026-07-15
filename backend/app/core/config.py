import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, BeforeValidator
from typing import Union

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    PROJECT_NAME: str = "LoomSense AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretloomsensekeychangeinprod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "sqlite:///./loomsense.db"

    # Multi-tenancy
    TENANT_HEADER: str = "X-Tenant-ID"
    DEFAULT_TENANT_ID: str = "factory_alpha"

    # Background Jobs / Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Third Party Integrations
    SLACK_WEBHOOK_URL: str = ""
    
    # Model Registry
    MODEL_REGISTRY_DIR: str = "./models"
    
    # Logging
    LOG_FILE: str = "logs/backend.log"

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
os.makedirs(settings.MODEL_REGISTRY_DIR, exist_ok=True)
