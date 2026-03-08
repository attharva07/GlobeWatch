"""Region aggregation service for globe rendering."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from app.models.event import Event
from app.repositories.event_repository import EventRepository


class RegionService:
    def __init__(self, repo: EventRepository) -> None:
        self.repo = repo

    def list_regions(self) -> list[dict[str, object]]:
        events = self.repo.list_events(limit=5000)
        grouped: dict[str, list[Event]] = defaultdict(list)
        for event in events:
            region_id = (event.country or "unknown").strip().lower()
            grouped[region_id].append(event)

        regions: list[dict[str, object]] = []
        for region_id, region_events in grouped.items():
            centroid_lat, centroid_lon = self._safe_centroid(region_events)
            categories = Counter(event.category for event in region_events)
            max_severity = self._aggregate_severity([event.severity for event in region_events])

            regions.append(
                {
                    "region_id": region_id,
                    "region_name": region_events[0].country,
                    "lat": centroid_lat,
                    "lon": centroid_lon,
                    "event_count": len(region_events),
                    "top_categories": [name for name, _ in categories.most_common(3)],
                    "severity": max_severity,
                }
            )

        return sorted(regions, key=lambda item: int(item["event_count"]), reverse=True)

    def region_events(self, region_id: str, limit: int = 200) -> list[Event]:
        # Normalise to lowercase so both "United States" and "united states" resolve correctly
        return list(self.repo.list_events_by_country(region_id.strip().lower(), limit=limit))

    @staticmethod
    def _safe_centroid(events: list[Event]) -> tuple[float, float]:
        """Compute a centroid that is safe across the antimeridian (±180° lon).

        Uses the unit-vector averaging method on the longitude so that regions
        straddling the antimeridian (e.g. Russia, Fiji) produce a correct
        centroid rather than collapsing to ~0° longitude.
        """
        n = len(events)
        # Latitude: plain average is fine (no wrap-around issue)
        avg_lat = sum(e.lat for e in events) / n

        # Longitude: project onto unit circle, average, then atan2 back
        sin_sum = sum(math.sin(math.radians(e.lon)) for e in events)
        cos_sum = sum(math.cos(math.radians(e.lon)) for e in events)
        avg_lon = math.degrees(math.atan2(sin_sum / n, cos_sum / n))

        return round(avg_lat, 6), round(avg_lon, 6)

    @staticmethod
    def _aggregate_severity(severities: list[str]) -> str:
        if any(value == "high" for value in severities):
            return "high"
        if any(value == "medium" for value in severities):
            return "medium"
        return "low"
