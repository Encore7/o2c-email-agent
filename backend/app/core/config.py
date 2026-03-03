from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "O2C Email Agent API"
    api_v1_prefix: str = "/api/v1"
    postgres_dsn: str = "postgresql://o2c:o2c@localhost:5432/o2c"
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_fallback_provider: str | None = "ollama"
    llm_fallback_model: str | None = "llama3.1:latest"
    llm_temperature: float = 0.0
    llm_enabled: bool = True
    ollama_base_url: str = "http://host.docker.internal:11434"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    gmail_enabled: bool = False
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_refresh_token: str | None = None
    gmail_user_id: str = "me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
