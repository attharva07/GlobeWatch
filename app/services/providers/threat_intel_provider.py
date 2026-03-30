"""Threat intelligence provider aggregating free Abuse.ch feeds.

Sources (all free, no registration):
  - Feodo Tracker botnet C2 list: https://feodotracker.abuse.ch/
  - ThreatFox IOC database: https://threatfox.abuse.ch/
  - ip-api.com batch geolocation (free, 100 IPs/req, 15 req/min)

Merged results are cached; on any failure the last known cache is kept.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.services.layer_cache import get_cache, set_cache
from app.services.layer_data_service import LayerDataService

logger = logging.getLogger(__name__)

_FEODO_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
_THREATFOX_URL = "https://threatfox-api.abuse.ch/api/v1/"
_IPAPI_BATCH = "http://ip-api.com/batch"
_MAX_IOCS = 200
_GEO_BATCH_SIZE = 100


async def _fetch_feodo(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    try:
        r = await client.get(_FEODO_URL, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        return data
    except Exception as exc:
        logger.debug("Feodo fetch failed: %s", exc)
        return []


async def _fetch_threatfox(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    try:
        r = await client.post(_THREATFOX_URL, json={"query": "get_iocs", "days": 1}, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        if data.get("query_status") != "ok":
            return []
        return data.get("data") or []
    except Exception as exc:
        logger.debug("ThreatFox fetch failed: %s", exc)
        return []


async def _geolocate_ips(client: httpx.AsyncClient, ips: list[str]) -> dict[str, dict[str, Any]]:
    """Batch-geolocate IPs using ip-api.com (free, 100/req, 15 req/min)."""
    result: dict[str, dict[str, Any]] = {}
    for i in range(0, len(ips), _GEO_BATCH_SIZE):
        batch = ips[i : i + _GEO_BATCH_SIZE]
        try:
            r = await client.post(
                _IPAPI_BATCH,
                json=[{"query": ip, "fields": "status,country,lat,lon,isp,org,query"} for ip in batch],
                timeout=15.0,
            )
            r.raise_for_status()
            entries = r.json()
            if isinstance(entries, list):
                for entry in entries:
                    if entry.get("status") == "success":
                        result[entry["query"]] = entry
        except Exception as exc:
            logger.debug("ip-api batch failed: %s", exc)
    return result


def _ioc_id(ip: str, threat_type: str) -> str:
    h = hashlib.md5(f"{ip}:{threat_type}".encode()).hexdigest()[:8]
    return f"ioc-{h}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def refresh_cyber_iocs() -> None:
    """Fetch, geolocate and merge threat intel feeds into the cache."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        feodo_raw, threatfox_raw = (
            await _fetch_feodo(client),
            await _fetch_threatfox(client),
        )

    raw_iocs: list[dict[str, Any]] = []
    now = _now_iso()

    # --- Feodo Tracker ---
    for entry in feodo_raw:
        ip = str(entry.get("ip_address") or "").strip()
        if not ip:
            continue
        status = str(entry.get("status") or "").lower()
        raw_iocs.append({
            "ip": ip,
            "threat_type": str(entry.get("malware") or "Botnet C2"),
            "severity": "high" if status == "online" else "medium",
            "country": str(entry.get("country") or "Unknown"),
            "isp": str(entry.get("as_name") or "Unknown"),
            "first_seen": str(entry.get("first_seen") or now),
            "last_seen": str(entry.get("last_seen") or now),
            "count": 1,
            "lat": None,
            "lon": None,
        })

    # --- ThreatFox ---
    seen_ips = {e["ip"] for e in raw_iocs}
    for entry in threatfox_raw:
        ioc_value = str(entry.get("ioc_value") or "").strip()
        # ThreatFox IOCs may be IPs or domains; keep only IPv4
        parts = ioc_value.split(":")
        ip = parts[0].strip()
        if not ip or not _is_ipv4(ip) or ip in seen_ips:
            continue
        seen_ips.add(ip)
        malware = str(entry.get("malware_printable") or entry.get("malware_alias") or "Unknown")
        threat_type = str(entry.get("threat_type_desc") or entry.get("threat_type") or "Malware")
        raw_iocs.append({
            "ip": ip,
            "threat_type": f"{malware} — {threat_type}",
            "severity": "high" if entry.get("confidence_level", 0) >= 75 else "medium",
            "country": "Unknown",
            "isp": "Unknown",
            "first_seen": str(entry.get("first_seen") or now),
            "last_seen": str(entry.get("last_seen") or now),
            "count": int(entry.get("reference_count") or 1),
            "lat": None,
            "lon": None,
        })

    # Limit before geolocating
    raw_iocs = raw_iocs[:_MAX_IOCS]

    # Geolocate IPs that don't have coordinates yet
    ips_to_geo = [e["ip"] for e in raw_iocs if e["lat"] is None]
    if ips_to_geo:
        async with httpx.AsyncClient(timeout=20.0) as client:
            geo_map = await _geolocate_ips(client, ips_to_geo)
    else:
        geo_map = {}

    iocs: list[dict] = []
    for entry in raw_iocs:
        ip = entry["ip"]
        geo = geo_map.get(ip, {})
        lat = float(geo.get("lat") or entry.get("lat") or 0)
        lon = float(geo.get("lon") or entry.get("lon") or 0)
        if lat == 0 and lon == 0:
            continue  # skip unresolvable
        iocs.append({
            "id": _ioc_id(ip, entry["threat_type"]),
            "ip": ip,
            "lat": lat,
            "lon": lon,
            "threat_type": entry["threat_type"],
            "severity": entry["severity"],
            "country": geo.get("country") or entry["country"],
            "isp": geo.get("isp") or geo.get("org") or entry["isp"],
            "count": entry["count"],
            "first_seen": entry["first_seen"],
            "last_seen": entry["last_seen"],
        })

    if iocs:
        set_cache("cyber", iocs, source="abuse_ch")
        logger.info("Threat intel: cached %d IOCs (feodo=%d, threatfox=%d)",
                    len(iocs), len(feodo_raw), len(threatfox_raw))
    else:
        logger.warning("Threat intel: no geolocatable IOCs — keeping cache")
        if get_cache("cyber") is None:
            set_cache("cyber", LayerDataService.get_cyber_iocs(), source="demo")


def _is_ipv4(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
