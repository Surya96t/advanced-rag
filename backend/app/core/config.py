"""Application configuration."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- Application ------------------------------------------------------
    app_name: str = "Advanced RAG"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False, description="Enable debug mode")

    # -- Server -----------------------------------------------------------
    host: str = Field(default="0.0.0.0", description="Bind address")
    port: int = Field(default=8000, description="Bind port")
    reload: bool = Field(default=True, description="Auto-reload")

    # -- CORS -------------------------------------------------------------
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins (comma-separated or JSON array)",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["Content-Type", "Authorization"]

    # -- Supabase ---------------------------------------------------------
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_key: str = Field(
        ...,
        description="Supabase service-role key",
        repr=False,
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )

    # -- Auth -------------------------------------------------------------
    auth_enabled: bool = Field(default=True, description="Require authentication")

    # -- Logging ----------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = Field(default=False, description="Emit JSON logs")

    @classmethod
    def _split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(cls, values: dict[str, object]) -> dict[str, object]:
        raw = values.get("cors_origins") or values.get("CORS_ORIGINS")
        if raw is not None:
            values["cors_origins"] = cls._split_origins(raw)  # type: ignore[arg-type]
        return values

    @model_validator(mode="after")
    def enforce_production_safety(self) -> "Settings":
        """Refuse to boot production with development toggles left on."""
        if self.environment != "production":
            return self

        if self.debug:
            raise ValueError("DEBUG must be disabled in production")
        if self.reload:
            raise ValueError("Auto-reload must be disabled in production")
        if not self.auth_enabled:
            raise ValueError(
                "AUTH_ENABLED must be true in production — disabling it collapses every "
                "tenant into a single shared identity"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, constructed once."""
    return Settings()


settings = get_settings()
