"""Security hardening behavior tests."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import rate_limiter
from app.main import app


def test_api_key_disabled_allows_requests() -> None:
    settings = get_settings()
    original_enabled = settings.API_KEY_ENABLED
    try:
        settings.API_KEY_ENABLED = False
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.status_code == 200
    finally:
        settings.API_KEY_ENABLED = original_enabled


def test_invalid_api_key_rejected_when_enabled() -> None:
    settings = get_settings()
    original_enabled = settings.API_KEY_ENABLED
    original_keys = list(settings.API_KEYS)
    try:
        settings.API_KEY_ENABLED = True
        settings.API_KEYS = ["valid-key"]
        with TestClient(app) as client:
            response = client.get("/health", headers={settings.API_KEY_HEADER_NAME: "bad-key"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API key"
    finally:
        settings.API_KEY_ENABLED = original_enabled
        settings.API_KEYS = original_keys


def test_rate_limit_returns_429_after_threshold() -> None:
    settings = get_settings()
    original_enabled = settings.RATE_LIMIT_ENABLED
    original_limit = settings.RATE_LIMIT_PER_MINUTE
    rate_limiter._requests.clear()
    try:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_PER_MINUTE = 2
        with TestClient(app) as client:
            ok_1 = client.get("/api/v1/news/events")
            ok_2 = client.get("/api/v1/news/events")
            blocked = client.get("/api/v1/news/events")
        assert ok_1.status_code == 200
        assert ok_2.status_code == 200
        assert blocked.status_code == 429
    finally:
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_PER_MINUTE = original_limit
        rate_limiter._requests.clear()


def test_security_headers_present() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_validation_rejects_invalid_parameters() -> None:
    with TestClient(app) as client:
        bad_limit = client.get("/api/v1/news/events?limit=999")
        bad_layer = client.get("/api/v1/globe/markers?layers=weather")
        bad_severity = client.get("/api/v1/news/events?severity=critical")

    assert bad_limit.status_code == 422
    assert bad_layer.status_code == 422
    assert bad_severity.status_code == 422
