"""Tests for the new geospatial layer endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def test_flights_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/flights")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    flight = body["flights"][0]
    assert "callsign" in flight
    assert "origin" in flight
    assert "destination" in flight
    assert "current_position" in flight


def test_ships_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/ships")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    ship = body["ships"][0]
    assert "mmsi" in ship
    assert "path" in ship


def test_cyber_iocs_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/cyber")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    ioc = body["iocs"][0]
    assert "ip" in ioc
    assert "threat_type" in ioc


def test_signals_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/signals")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    signal = body["signals"][0]
    assert "intensity" in signal
    assert "frequency" in signal


def test_satellites_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/satellites")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    sat = body["satellites"][0]
    assert "norad_id" in sat
    assert "path" in sat
    assert len(sat["path"]) > 0


def test_conflicts_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/conflicts")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    conflict = body["conflicts"][0]
    assert "geometry" in conflict
    assert "events" in conflict


def test_entity_links_endpoint_returns_demo_data() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/layers/entity-links")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    link = body["links"][0]
    assert "source_name" in link
    assert "target_name" in link
    assert "source_position" in link
    assert "relationship" in link
