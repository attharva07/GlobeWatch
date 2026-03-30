"""OpenSky Network provider for real-time flight data.

Free, anonymous access (rate-limited to 1 req/10s, 400 req/day).
Optionally use credentials to get a higher rate limit.
API docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

_OPENSKY_URL = "https://opensky-network.org/api/states/all"
_MAX_FLIGHTS = 500


async def refresh_flights(
    *,
    username: str = "",
    password: str = "",
) -> None:
    """Fetch live flight states from OpenSky and update the cache."""
    auth = (username, password) if username and password else None
    now_iso = datetime.now(UTC).isoformat()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_OPENSKY_URL, auth=auth)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        logger.warning("OpenSky fetch failed: %s — keeping cached data", exc)
        if get_cache("flights") is None:
            set_cache("flights", LayerDataService.get_flights(), source="demo")
        return

    states = payload.get("states") or []
    flights: list[dict] = []

    for state in states:
        if not isinstance(state, list) or len(state) < 14:
            continue
        icao24 = str(state[0] or "").strip()
        callsign = str(state[1] or "").strip() or icao24.upper()
        origin_country = str(state[2] or "Unknown")
        lon = state[5]
        lat = state[6]
        baro_alt = state[7]
        on_ground = state[8]
        velocity = state[9]
        true_track = state[10]
        geo_alt = state[13]

        if on_ground or lon is None or lat is None:
            continue

        alt_m = float((geo_alt if geo_alt is not None else baro_alt) or 0)
        alt_ft = round(alt_m * 3.281)
        speed_kts = round(float(velocity or 0) * 1.944)

        flights.append({
            "id": icao24 or f"fl-{len(flights)}",
            "callsign": callsign,
            "origin": [lon, lat],        # free tier has no route; use current pos
            "destination": [lon, lat],
            "current_position": [lon, lat, alt_ft],
            "heading": float(true_track or 0),
            "speed": float(speed_kts),
            "altitude": float(alt_ft),
            "aircraft_type": "Unknown",
            "timestamp": now_iso,
            "origin_country": origin_country,
        })

        if len(flights) >= _MAX_FLIGHTS:
            break

    if flights:
        set_cache("flights", flights, source="opensky")
        logger.info("OpenSky: cached %d flights", len(flights))
    else:
        logger.warning("OpenSky returned 0 airborne states — keeping cache")
        if get_cache("flights") is None:
            set_cache("flights", LayerDataService.get_flights(), source="demo")
