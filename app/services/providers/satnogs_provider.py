"""SatNOGS ground station provider for signal coverage layer.

Uses active SatNOGS ground stations as signal coverage data points.
Free API, no key required: https://network.satnogs.org/api/
"""

from __future__ import annotations

import logging

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

_STATIONS_URL = "https://network.satnogs.org/api/stations/"
_MAX_PAGES = 3


async def refresh_signals() -> None:
    """Fetch SatNOGS online ground stations and use them as signal coverage points."""
    stations: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            url: str | None = _STATIONS_URL
            page = 0
            while url and page < _MAX_PAGES:
                r = await client.get(url, params={"status": "Online", "format": "json", "limit": 100})
                r.raise_for_status()
                payload = r.json()
                results = payload.get("results") or (payload if isinstance(payload, list) else [])
                for station in results:
                    lat = station.get("lat")
                    lng = station.get("lng")
                    if lat is None or lng is None:
                        continue
                    obs_count = int(station.get("observations") or station.get("total_count") or 1)
                    # Map observation count → intensity (log scale, capped at 1.0)
                    import math
                    intensity = min(1.0, math.log10(max(1, obs_count)) / 4.0)
                    stations.append({
                        "lat": float(lat),
                        "lon": float(lng),
                        "intensity": round(intensity, 3),
                        "frequency": 435.0,  # typical VHF/UHF amateur satellite frequency MHz
                        "signal_type": "SatNOGS",
                        "station_name": str(station.get("name") or ""),
                        "observations": obs_count,
                    })
                url = payload.get("next") if isinstance(payload, dict) else None
                page += 1
    except Exception as exc:
        logger.warning("SatNOGS fetch failed: %s — keeping cached data", exc)
        if get_cache("signals") is None:
            set_cache("signals", LayerDataService.get_signals(), source="demo")
        return

    if stations:
        set_cache("signals", stations, source="satnogs")
        logger.info("SatNOGS: cached %d ground stations", len(stations))
    else:
        logger.warning("SatNOGS returned 0 stations")
        if get_cache("signals") is None:
            set_cache("signals", LayerDataService.get_signals(), source="demo")
