import logging
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    LLM_API_KEY: str
    JWT_SECRET: str = "change-me"
    JWT_EXP_SECONDS: int = 86400
    ENVIRONMENT: str = "development"
    LLM_RESPONSE_MODEL: str = "gpt-4o-mini"
    LOG_LEVEL: str = "INFO"
    CONVERSATION_MEMORY_K: int = 5
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


logger = logging.getLogger(__name__)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:  # pragma: no cover - startup failure
        logger.error("Failed to load configuration: %s", exc)
        raise SystemExit(
            "Invalid configuration. Please check your environment variables."
        ) from exc
