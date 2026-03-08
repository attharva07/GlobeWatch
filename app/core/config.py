"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    API_KEY_ENABLED: bool = False
    API_KEY_HEADER_NAME: str = "X-API-Key"
    API_KEYS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    LOG_LEVEL: str = "INFO"

    ENABLE_MOCK_SEED: bool = False
    INGESTION_PROVIDER: str = "gdelt"
    INGESTION_ENABLED: bool = True
    INGESTION_INTERVAL_SECONDS: int = 900
    INGESTION_STARTUP_RUN: bool = True
    GDELT_BASE_URL: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    GDELT_QUERY: str = "(flood OR wildfire OR earthquake OR outbreak OR protest)"
    GDELT_MAX_RECORDS: int = 50

    @staticmethod
    def _parse_list_like_env(value: object) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            try:
                parsed_value = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed_value = None

            if isinstance(parsed_value, list):
                return [str(item).strip() for item in parsed_value if str(item).strip()]

            return [item.strip() for item in raw_value.split(",") if item.strip()]

        return [str(value).strip()] if str(value).strip() else []

    @field_validator("ALLOWED_ORIGINS", "API_KEYS", mode="before")
    @classmethod
    def parse_list_fields(cls, value: object) -> list[str]:
        return cls._parse_list_like_env(value)

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

    @field_validator("INGESTION_INTERVAL_SECONDS")
    @classmethod
    def validate_ingestion_interval(cls, value: int) -> int:
        if value < 60:
            raise ValueError("INGESTION_INTERVAL_SECONDS must be >= 60")
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
