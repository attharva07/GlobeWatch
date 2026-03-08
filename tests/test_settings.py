"""Settings parsing tests for list-based environment variables."""

from app.core.config import Settings


def _build_settings(**env_values: str) -> Settings:
    return Settings(_env_file=None, **env_values)


def test_allowed_origins_parses_from_json_list() -> None:
    settings = _build_settings(ALLOWED_ORIGINS='["https://one.example","https://two.example"]')
    assert settings.ALLOWED_ORIGINS == ["https://one.example", "https://two.example"]


def test_allowed_origins_parses_from_comma_separated_string() -> None:
    settings = _build_settings(ALLOWED_ORIGINS="https://one.example, https://two.example")
    assert settings.ALLOWED_ORIGINS == ["https://one.example", "https://two.example"]


def test_api_keys_parses_from_json_list() -> None:
    settings = _build_settings(API_KEYS='["key-1","key-2"]')
    assert settings.API_KEYS == ["key-1", "key-2"]


def test_api_keys_parses_from_comma_separated_string() -> None:
    settings = _build_settings(API_KEYS="key-1, key-2")
    assert settings.API_KEYS == ["key-1", "key-2"]


def test_api_keys_empty_string_becomes_empty_list() -> None:
    settings = _build_settings(API_KEYS="")
    assert settings.API_KEYS == []


def test_ingestion_defaults_are_provider_safe() -> None:
    settings = _build_settings()
    assert settings.INGESTION_ENABLED is True
    assert settings.INGESTION_INTERVAL_SECONDS == 900
    assert settings.INGESTION_STARTUP_RUN is True
    assert settings.GDELT_MAX_RECORDS == 50
