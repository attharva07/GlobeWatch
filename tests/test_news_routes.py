"""News route tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_news_status_reports_readiness() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/news/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "news"
    assert payload["ready"] is True


def test_news_events_endpoint_returns_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/news/events?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] <= 2
    assert len(payload["events"]) == payload["count"]
