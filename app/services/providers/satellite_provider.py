"""Satellite provider using Celestrak TLE data + sgp4 orbit propagation.

TLE data: https://celestrak.org/SPACEDATA/GP.php (free, no key)
Requires: sgp4==2.22 (pip install sgp4)
Falls back to demo data if sgp4 is not installed or fetch fails.
"""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from typing import Any

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

try:
    from sgp4.api import Satrec, jday as sgp4_jday  # type: ignore[import-untyped]
    _SGP4_AVAILABLE = True
except ImportError:
    _SGP4_AVAILABLE = False
    logger.warning("sgp4 library not installed — satellite provider will use demo data")

# Celestrak TLE groups to fetch (visual = brightest ~150 sats, stations = ISS/Tiangong)
_TLE_URLS = [
    "https://celestrak.org/SPACEDATA/GP.php?GROUP=stations&FORMAT=TLE",
    "https://celestrak.org/SPACEDATA/GP.php?GROUP=visual&FORMAT=TLE",
]
_MAX_SATS = 80
_PATH_STEP_MIN = 6       # propagate every 6 minutes
_PATH_DURATION_MIN = 90  # 90 minutes total track


def _parse_tle_text(text: str) -> list[tuple[str, str, str]]:
    """Parse 3-line TLE blocks from Celestrak text format."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result: list[tuple[str, str, str]] = []
    i = 0
    while i < len(lines) - 2:
        name = lines[i]
        l1 = lines[i + 1]
        l2 = lines[i + 2]
        if l1.startswith("1 ") and l2.startswith("2 "):
            result.append((name, l1, l2))
            i += 3
        else:
            i += 1
    return result


def _compute_gmst(jd: float, fr: float) -> float:
    """Approximate Greenwich Mean Sidereal Time in radians."""
    d = (jd - 2451545.0) + fr
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360
    return math.radians(gmst_deg)


def _eci_to_geodetic(x: float, y: float, z: float, gmst: float) -> tuple[float, float, float]:
    """Convert ECI position (km) to geographic lat, lon (deg), alt (km)."""
    x_ecef = x * math.cos(gmst) + y * math.sin(gmst)
    y_ecef = -x * math.sin(gmst) + y * math.cos(gmst)
    z_ecef = z
    rxy = math.sqrt(x_ecef ** 2 + y_ecef ** 2)
    lat = math.degrees(math.atan2(z_ecef, rxy))
    lon = math.degrees(math.atan2(y_ecef, x_ecef))
    alt_km = math.sqrt(x_ecef ** 2 + y_ecef ** 2 + z_ecef ** 2) - 6371.0
    return lat, lon, alt_km


def _orbit_type(line2: str) -> str:
    """Infer orbit type from mean motion (rev/day) in TLE line 2."""
    try:
        mean_motion = float(line2[52:63].strip())
    except (ValueError, IndexError):
        return "LEO"
    if mean_motion >= 11.25:
        return "LEO"
    if mean_motion >= 1.5:
        return "MEO"
    return "GEO"


def _propagate(
    sat: Any,
    now: datetime,
) -> tuple[list[list[float]], list[float] | None]:
    """Generate ground track path and current position."""
    jd_base, fr_base = sgp4_jday(  # type: ignore[possibly-undefined]
        now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond / 1e6
    )
    path: list[list[float]] = []
    current: list[float] | None = None

    for step in range(0, _PATH_DURATION_MIN + 1, _PATH_STEP_MIN):
        extra_days = step / 1440.0
        jd = jd_base + int(fr_base + extra_days)
        fr = (fr_base + extra_days) % 1.0

        e, r, _ = sat.sgp4(jd, fr)
        if e != 0 or r is None:
            continue

        gmst = _compute_gmst(jd, fr)
        lat, lon, alt_km = _eci_to_geodetic(r[0], r[1], r[2], gmst)
        point = [round(lon, 3), round(lat, 3), round(alt_km, 1)]
        path.append(point)
        if current is None:
            current = point  # first point = current position

    return path, current


async def refresh_satellites() -> None:
    """Fetch TLE data from Celestrak, propagate orbits, cache results."""
    if not _SGP4_AVAILABLE:
        if get_cache("satellites") is None:
            set_cache("satellites", LayerDataService.get_satellites(), source="demo")
        return

    all_tles: list[tuple[str, str, str]] = []
    seen_names: set[str] = set()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for url in _TLE_URLS:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    tles = _parse_tle_text(r.text)
                    for name, l1, l2 in tles:
                        if name not in seen_names:
                            seen_names.add(name)
                            all_tles.append((name, l1, l2))
                except Exception as exc:
                    logger.debug("TLE fetch %s failed: %s", url, exc)
    except Exception as exc:
        logger.warning("Satellite fetch failed: %s — keeping cache", exc)
        if get_cache("satellites") is None:
            set_cache("satellites", LayerDataService.get_satellites(), source="demo")
        return

    if not all_tles:
        logger.warning("No TLE data retrieved")
        if get_cache("satellites") is None:
            set_cache("satellites", LayerDataService.get_satellites(), source="demo")
        return

    now = datetime.now(UTC)
    now_iso = now.isoformat()
    satellites: list[dict] = []

    for name, l1, l2 in all_tles[:_MAX_SATS]:
        try:
            sat = Satrec.twoline2rv(l1, l2)  # type: ignore[possibly-undefined]
            norad_id = int(l2.split()[1])
            path, current = _propagate(sat, now)
            if not path or current is None:
                continue
            orbit_type = _orbit_type(l2)
            satellites.append({
                "id": f"sat-{norad_id}",
                "name": name,
                "norad_id": norad_id,
                "path": path,
                "current_position": current,
                "orbit_type": orbit_type,
                "timestamp": now_iso,
                "tle_line1": l1,
                "tle_line2": l2,
            })
        except Exception as exc:
            logger.debug("Propagation failed for %s: %s", name, exc)

    if satellites:
        set_cache("satellites", satellites, source="celestrak")
        logger.info("Satellites: cached %d orbits from %d TLEs", len(satellites), len(all_tles))
    else:
        logger.warning("No satellites propagated — keeping cache")
        if get_cache("satellites") is None:
            set_cache("satellites", LayerDataService.get_satellites(), source="demo")
