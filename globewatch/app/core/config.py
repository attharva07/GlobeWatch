"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for GlobeWatch."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    APP_NAME: str = "GlobeWatch API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "local"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./globewatch.db"
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_KEY_ENABLED: bool = False
    API_KEY: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return singleton settings object."""

    return Settings()
