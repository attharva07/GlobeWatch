"""Globe marker and region route tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_globe_markers_returns_normalized_news_markers() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/globe/markers?layers=news&limit=3")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] <= 3
    assert len(body["markers"]) == body["count"]


def test_globe_regions_endpoint_returns_aggregated_markers() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/globe/regions")

    assert response.status_code == 200
    body = response.json()
    assert "regions" in body
    if body["count"]:
        marker = body["regions"][0]
        assert "region_id" in marker
        assert "event_count" in marker
