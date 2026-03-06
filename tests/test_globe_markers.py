"""Globe marker route tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_globe_markers_returns_normalized_news_markers() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/globe/markers?layers=news&limit=3")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] <= 3
    assert len(body["markers"]) == body["count"]
    if body["count"]:
        marker = body["markers"][0]
        assert marker["type"] == "news"
        assert marker["severity"] in {"low", "medium", "high"}
        assert "metadata" in marker


def test_globe_markers_requires_supported_layers() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/globe/markers?layers=weather")

    assert response.status_code == 422
