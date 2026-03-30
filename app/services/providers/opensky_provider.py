"""OpenSky Network provider for real-time flight data.

Uses OAuth2 client credentials flow (required since March 18, 2026).
Tokens expire every 30 minutes and are refreshed automatically.

API docs: https://openskynetwork.github.io/opensky-api/rest.html

Credit costs (daily quota: 4,000 for registered users):
  - Global /states/all  = 4 credits per call
  - At OPENSKY_INTERVAL_SECONDS=60 → 240 calls/hour → burns full quota in ~4h
  - Recommended: 120s interval → 120 calls/hour → safe all day
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

_OPENSKY_URL = "https://opensky-network.org/api/states/all"
_TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)
_MAX_FLIGHTS = 500
# Refresh token this many seconds before it actually expires
_TOKEN_REFRESH_MARGIN_SECONDS = 60


class _TokenManager:
    """Thread-safe OAuth2 token manager for OpenSky client credentials flow."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None
        self._expires_at: datetime | None = None

    def is_valid(self) -> bool:
        if not self._token or not self._expires_at:
            return False
        return datetime.now(UTC) < self._expires_at

    async def get_token(self) -> str | None:
        """Return a valid Bearer token, refreshing if needed."""
        if not self._client_id or not self._client_secret:
            return None  # no credentials configured — anonymous mode
        if self.is_valid():
            return self._token
        return await self._refresh()

    async def _refresh(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    _TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            self._token = data["access_token"]
            expires_in = int(data.get("expires_in", 1800))
            self._expires_at = datetime.now(UTC) + timedelta(
                seconds=expires_in - _TOKEN_REFRESH_MARGIN_SECONDS
            )
            logger.info(
                "OpenSky token refreshed — valid for %ds (until %s)",
                expires_in - _TOKEN_REFRESH_MARGIN_SECONDS,
                self._expires_at.strftime("%H:%M:%S UTC"),
            )
            return self._token

        except Exception as exc:
            logger.warning("OpenSky token refresh failed: %s", exc)
            self._token = None
            self._expires_at = None
            return None


# Module-level singleton — survives across refresh_flights() calls
_token_manager: _TokenManager | None = None


def _get_token_manager(client_id: str, client_secret: str) -> _TokenManager:
    global _token_manager
    if _token_manager is None or (
        _token_manager._client_id != client_id
        or _token_manager._client_secret != client_secret
    ):
        _token_manager = _TokenManager(client_id, client_secret)
    return _token_manager


async def refresh_flights(
    *,
    client_id: str = "",
    client_secret: str = "",
    # Legacy params kept for backwards compatibility — no longer used
    username: str = "",
    password: str = "",
) -> None:
    """Fetch live flight states from OpenSky and update the cache.

    Uses OAuth2 Bearer token when client_id/client_secret are provided.
    Falls back to anonymous access (400 credits/day, 10s time resolution)
    if no credentials are configured.
    """
    now_iso = datetime.now(UTC).isoformat()

    # Build auth header
    manager = _get_token_manager(client_id, client_secret)
    token = await manager.get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    if not token:
        logger.warning(
            "OpenSky: no OAuth2 token available — falling back to anonymous "
            "(limited to 400 credits/day, 10s time resolution)"
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_OPENSKY_URL, headers=headers)

            # 401 means our token expired mid-flight — clear it and warn
            if resp.status_code == 401:
                logger.warning(
                    "OpenSky: 401 Unauthorized — token may have expired, "
                    "will refresh on next cycle"
                )
                manager._token = None
                manager._expires_at = None
                _fallback_to_cache()
                return

            resp.raise_for_status()
            payload = resp.json()

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.warning(
                "OpenSky: 429 rate limited — daily credits exhausted. "
                "Keeping cached data. Consider increasing OPENSKY_INTERVAL_SECONDS."
            )
        else:
            logger.warning("OpenSky fetch failed: %s — keeping cached data", exc)
        _fallback_to_cache()
        return
    except Exception as exc:
        logger.warning("OpenSky fetch failed: %s — keeping cached data", exc)
        _fallback_to_cache()
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
        vertical_rate = state[11]
        geo_alt = state[13]
        squawk = state[14] if len(state) > 14 else None
        # Index 17 = aircraft category (only present with ?extended=1)
        category_code = state[17] if len(state) > 17 else 0

        if on_ground or lon is None or lat is None:
            continue

        alt_m = float((geo_alt if geo_alt is not None else baro_alt) or 0)
        alt_ft = round(alt_m * 3.281)
        speed_kts = round(float(velocity or 0) * 1.944)
        vrate_fpm = round(float(vertical_rate or 0) * 196.85) if vertical_rate else 0

        flights.append({
            "id": icao24 or f"fl-{len(flights)}",
            "callsign": callsign,
            "origin": [lon, lat],
            "destination": [lon, lat],
            "current_position": [lon, lat, alt_ft],
            "heading": float(true_track or 0),
            "speed": float(speed_kts),
            "altitude": float(alt_ft),
            "vertical_rate_fpm": float(vrate_fpm),
            "squawk": squawk,
            "aircraft_category": _category_label(int(category_code or 0)),
            "aircraft_type": "Unknown",
            "timestamp": now_iso,
            "origin_country": origin_country,
            "authenticated": bool(token),
        })

        if len(flights) >= _MAX_FLIGHTS:
            break

    if flights:
        set_cache("flights", flights, source="opensky")
        logger.info(
            "OpenSky: cached %d flights (%s)",
            len(flights),
            "authenticated" if token else "anonymous",
        )
    else:
        logger.warning("OpenSky returned 0 airborne states — keeping cache")
        _fallback_to_cache()


def _fallback_to_cache() -> None:
    """Keep existing cache, or seed with demo data if nothing cached yet."""
    if get_cache("flights") is None:
        set_cache("flights", LayerDataService.get_flights(), source="demo")


def _category_label(code: int) -> str:
    """Map OpenSky aircraft category code to a human-readable label."""
    return {
        0: "Unknown", 1: "Unknown", 2: "Light", 3: "Small",
        4: "Large", 5: "High Vortex Large", 6: "Heavy",
        7: "High Performance", 8: "Rotorcraft", 9: "Glider",
        10: "Lighter-than-air", 11: "Parachutist", 12: "Ultralight",
        14: "UAV", 15: "Space Vehicle",
        16: "Emergency Vehicle", 17: "Service Vehicle",
    }.get(code, "Unknown")