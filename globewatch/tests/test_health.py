"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_route_returns_service_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "app_name" in payload
    assert "version" in payload
