"""Settings parsing tests."""

from app.core.config import Settings


def test_allowed_origins_parses_comma_separated_string() -> None:
    settings = Settings(ALLOWED_ORIGINS="http://localhost:5173, http://127.0.0.1:5173")

    assert settings.ALLOWED_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_allowed_origins_parses_json_list_string() -> None:
    settings = Settings(ALLOWED_ORIGINS='["http://localhost:3000", "http://127.0.0.1:3000"]')

    assert settings.ALLOWED_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]
