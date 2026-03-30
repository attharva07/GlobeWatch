"""UCDP GED (Georeferenced Event Dataset) provider for conflict data.

Free API, no key required.
API docs: https://ucdpapi.pcr.uu.se/
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

# UCDP GED API — fetch recent events (last 2 years, page 1)
_UCDP_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/23.1"
_MAX_ZONES = 30


def _severity_from_fatalities(fatalities: int) -> str:
    if fatalities >= 100:
        return "high"
    if fatalities >= 10:
        return "medium"
    return "low"


def _make_bbox_feature(lats: list[float], lons: list[float], name: str) -> dict[str, Any]:
    """Return a GeoJSON Feature with a bounding-box Polygon."""
    min_lat = min(lats) - 1.0
    max_lat = max(lats) + 1.0
    min_lon = min(lons) - 1.0
    max_lon = max(lons) + 1.0
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]],
        },
    }


async def refresh_conflicts() -> None:
    """Fetch UCDP events and aggregate into conflict zones by country."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                _UCDP_URL,
                params={"pagesize": 1000, "page": 1},
                timeout=30.0,
            )
            r.raise_for_status()
            payload = r.json()
    except Exception as exc:
        logger.warning("UCDP fetch failed: %s — keeping cached data", exc)
        if get_cache("conflicts") is None:
            set_cache("conflicts", LayerDataService.get_conflicts(), source="demo")
        return

    raw_events: list[dict] = payload.get("Result") or []
    if not raw_events:
        logger.warning("UCDP returned 0 events")
        if get_cache("conflicts") is None:
            set_cache("conflicts", LayerDataService.get_conflicts(), source="demo")
        return

    # Group events by country_id → aggregate
    country_groups: dict[str, list[dict]] = defaultdict(list)
    for ev in raw_events:
        country = str(ev.get("country") or ev.get("country_id") or "Unknown").strip()
        lat = ev.get("latitude")
        lon = ev.get("longitude")
        if lat is None or lon is None:
            continue
        country_groups[country].append(ev)

    zones: list[dict] = []
    for country, events in sorted(country_groups.items(), key=lambda x: -len(x[1])):
        if len(zones) >= _MAX_ZONES:
            break
        lats = [float(e["latitude"]) for e in events]
        lons = [float(e["longitude"]) for e in events]
        total_fatalities = sum(int(e.get("best") or e.get("deaths_civilians") or 0) for e in events)
        severity = _severity_from_fatalities(total_fatalities)
        # Sample up to 20 individual events
        sample = events[:20]

        zones.append({
            "id": f"ucdp-{country.lower().replace(' ', '-')[:20]}",
            "name": f"{country} Conflict Zone",
            "geometry": _make_bbox_feature(lats, lons, country),
            "severity": severity,
            "event_count": len(events),
            "description": (
                f"UCDP: {len(events)} recorded conflict events in {country}. "
                f"Estimated total fatalities: {total_fatalities}."
            ),
            "events": [
                {
                    "lat": float(e["latitude"]),
                    "lon": float(e["longitude"]),
                    "type": str(e.get("type_of_violence_label") or e.get("type_of_violence") or "armed_conflict"),
                    "date": str(e.get("date_start") or "")[:10],
                    "fatalities": int(e.get("best") or 0),
                    "actor1": str(e.get("side_a") or ""),
                    "actor2": str(e.get("side_b") or ""),
                }
                for e in sample
            ],
        })

    if zones:
        set_cache("conflicts", zones, source="ucdp")
        logger.info("UCDP: cached %d conflict zones from %d events", len(zones), len(raw_events))
    else:
        logger.warning("UCDP: no zones built — keeping cache")
        if get_cache("conflicts") is None:
            set_cache("conflicts", LayerDataService.get_conflicts(), source="demo")
