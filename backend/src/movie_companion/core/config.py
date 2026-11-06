"""Application settings.

Single source of configuration for every process (API, jobs worker, browser worker).
Values come from environment variables, then `.env`, then `.env.<APP_ENV>` (later files win).
Secrets are typed as `SecretStr` so they never print in logs or reprs.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "test", "production"]

_ENV = os.environ.get("APP_ENV", "development")


class Settings(BaseSettings):
    """Typed settings shared by all backend processes."""

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_ENV}"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # `KEY=` in .env means "not set", so empty secrets never become "" tokens.
        env_ignore_empty=True,
    )

    # --- Application -------------------------------------------------------------
    app_env: AppEnv = "development"
    app_name: str = "Movie Companion"
    api_prefix: str = "/api/v1"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Logging -----------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: Path = Path("logs")
    log_to_file: bool = True
    log_file_max_bytes: int = 10 * 1024 * 1024
    log_file_backup_count: int = 5

    # --- Data stores -------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://movie:movie@localhost:5432/movie_companion"
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # --- Security ----------------------------------------------------------------
    # Single-owner app: the API is protected by one bearer token. Required in production.
    owner_api_token: SecretStr | None = None

    # --- Browser worker (home machine only) ----------------------------------------
    # persistent: Playwright launches Chrome with a dedicated profile directory.
    # cdp: Playwright attaches to a Chrome you started with --remote-debugging-port.
    browser_mode: Literal["persistent", "cdp"] = "persistent"
    browser_channel: Literal["chrome", "chromium"] = "chrome"
    browser_profile_dir: Path = Path.home() / ".movie-companion" / "chrome-profile"
    browser_cdp_url: str = "http://127.0.0.1:9222"
    browser_headless: bool = False
    browser_max_page_loads_per_hour: int = Field(default=60, ge=1, le=600)

    # --- External integrations (used from later milestones) ----------------------
    tmdb_api_key: SecretStr | None = None
    omdb_api_key: SecretStr | None = None
    google_maps_api_key: SecretStr | None = None
    youtube_api_key: SecretStr | None = None
    llm_provider: Literal["anthropic", "openai", "gemini", "none"] = "none"
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    vapid_public_key: str | None = None
    vapid_private_key: SecretStr | None = None

    @property
    def is_production(self) -> bool:
        """True when running with production safeguards."""
        return self.app_env == "production"

    @model_validator(mode="after")
    def _enforce_production_safeguards(self) -> Settings:
        """Refuse to start a production process with unsafe defaults."""
        if not self.is_production:
            return self
        problems: list[str] = []
        if self.owner_api_token is None or len(self.owner_api_token.get_secret_value()) < 32:
            problems.append("OWNER_API_TOKEN must be set to at least 32 characters")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain '*'")
        if "movie:movie@" in self.database_url:
            problems.append("DATABASE_URL still uses the development credentials")
        if self.log_level == "DEBUG":
            problems.append("LOG_LEVEL=DEBUG is not allowed in production")
        if problems:
            raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance (cached)."""
    return Settings()
