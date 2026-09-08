"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"
    app_name: str = "Adaptive Fitness Coach API"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://fitness:fitness@localhost:5432/fitness"
    database_url_sync: str = "postgresql+psycopg://fitness:fitness@localhost:5432/fitness"

    # Auth
    auth_mode: str = "mock"  # "supabase" | "mock"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    auth_require_email_confirm: bool = False
    mock_jwt_secret: str = "dev-only-secret-change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # AI
    ai_provider: str = "mock"  # "gemini" | "mock"
    gemini_api_key: str = ""
    ai_model: str = "gemini-2.0-flash"
    ai_timeout_seconds: float = 2.5

    # CORS
    frontend_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8081"

    # Misc
    log_level: str = "INFO"
    enable_docs: bool = True
    generator_version: str = "rules-v1"
    default_timezone: str = "UTC"

    # Rate limiting (per-process, see DECISIONS.md)
    rate_limit_generate_per_minute: int = 10
    rate_limit_insight_per_minute: int = 5
    rate_limit_weekly_generate_per_minute: int = 5

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
