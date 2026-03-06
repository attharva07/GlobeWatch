"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for GlobeWatch."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    APP_NAME: str = "GlobeWatch API"
    APP_VERSION: str = "0.2.0"
    ENVIRONMENT: Literal["local", "development", "staging", "production", "test"] = "local"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./globewatch.db"
    SECRET_KEY: str = "local-dev-change-me"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])

    API_KEY_ENABLED: bool = False
    API_KEY_HEADER_NAME: str = "X-API-Key"
    API_KEYS: list[str] = Field(default_factory=list)

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    LOG_LEVEL: str = "INFO"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [key.strip() for key in value.split(",") if key.strip()]
        return value

    @field_validator("API_PREFIX")
    @classmethod
    def ensure_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("API_PREFIX must start with '/'")
        return value.rstrip("/") or "/"

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, value: int) -> int:
        if value < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be >= 1")
        return value

    @model_validator(mode="after")
    def harden_runtime_flags(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.DEBUG:
            self.DEBUG = False
        if self.ENVIRONMENT == "production" and (self.ALLOWED_ORIGINS == ["*"]):
            raise ValueError("Wildcard ALLOWED_ORIGINS is not allowed in production")
        if self.API_KEY_ENABLED and not self.API_KEYS:
            raise ValueError("API_KEY_ENABLED requires at least one API key in API_KEYS")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return singleton settings object."""

    return Settings()
