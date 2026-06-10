from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OPNs IgAN Analysis System"
    app_env: str = "development"
    database_url: str = "sqlite:///./opns_medical.db"
    jwt_secret_key: str = "change-this-secret-in-local-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    ai_mode: str = "llm"
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
