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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
