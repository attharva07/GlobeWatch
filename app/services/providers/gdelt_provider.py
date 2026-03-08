"""GDELT provider for fetching real-world geolocated events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings


class ProviderRateLimitError(Exception):
    """Raised when provider responds with HTTP 429."""


class ProviderNetworkError(Exception):
    """Raised when a network/transport-level failure prevents fetching events."""


@dataclass
class ProviderEvent:
    external_id: str | None
    title: str
    description: str
    category: str
    source: str
    provider: str
    lat: float
    lon: float
    country: str
    city: str
    event_timestamp: datetime
    url: str | None
    metadata: dict[str, Any]


class GDELTProvider:
    """Adapter for GDELT DOC 2.0 API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_events(self) -> list[ProviderEvent]:
        params = {
            "query": self.settings.GDELT_QUERY,
            "mode": "ArtList",
            "maxrecords": self.settings.GDELT_MAX_RECORDS,
            "format": "json",
            "sort": "datedesc",
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(self.settings.GDELT_BASE_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderRateLimitError("GDELT rate limit reached (HTTP 429)") from exc
            raise ProviderNetworkError(f"GDELT request failed with HTTP {exc.response.status_code}") from exc
        except httpx.TransportError as exc:
            raise ProviderNetworkError(f"GDELT network error: {exc}") from exc

        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        normalized: list[ProviderEvent] = []
        for item in articles:
            if not isinstance(item, dict):
                continue
            lat = item.get("locationlat")
            lon = item.get("locationlong")
            if lat is None or lon is None:
                continue
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except (TypeError, ValueError):
                continue

            title = str(item.get("title") or "Untitled event").strip()
            if not title:
                continue
            seen_date = self._parse_timestamp(item.get("seendate"))
            source_country = str(item.get("sourcecountry") or "Unknown").strip() or "Unknown"
            source_name = str(item.get("domain") or "GDELT").strip() or "GDELT"
            url = item.get("url")
            category = self._categorize(title)

            normalized.append(
                ProviderEvent(
                    external_id=self._external_id(url, item),
                    title=title,
                    description=title,
                    category=category,
                    source=source_name,
                    provider="gdelt",
                    lat=lat_f,
                    lon=lon_f,
                    country=source_country,
                    city=str(item.get("location") or "Unknown").strip() or "Unknown",
                    event_timestamp=seen_date,
                    url=str(url).strip() if isinstance(url, str) and url.strip() else None,
                    metadata={
                        "tone": item.get("tone"),
                        "theme": item.get("theme"),
                        "language": item.get("language"),
                        "socialimage": item.get("socialimage"),
                    },
                )
            )

        return normalized

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, str):
            for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
                try:
                    return datetime.strptime(value, fmt).replace(tzinfo=UTC)
                except ValueError:
                    continue
        return datetime.now(UTC)

    @staticmethod
    def _external_id(url: Any, item: dict[str, Any]) -> str | None:
        if isinstance(url, str) and url.strip():
            return url.strip()
        docid = item.get("documentidentifier")
        if isinstance(docid, str) and docid.strip():
            return docid.strip()
        return None

    @staticmethod
    def _categorize(title: str) -> str:
        lowered = title.lower()
        if any(word in lowered for word in ["flood", "storm", "wildfire", "earthquake", "weather"]):
            return "weather_alert"
        if any(word in lowered for word in ["health", "virus", "outbreak", "hospital"]):
            return "public_health"
        if any(word in lowered for word in ["protest", "strike", "election", "conflict"]):
            return "civic"
        return "world_event"
