"""Region aggregation service for globe rendering."""

from __future__ import annotations

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
            total_lat = sum(event.lat for event in region_events)
            total_lon = sum(event.lon for event in region_events)
            categories = Counter(event.category for event in region_events)
            max_severity = self._aggregate_severity([event.severity for event in region_events])

            regions.append(
                {
                    "region_id": region_id,
                    "region_name": region_events[0].country,
                    "lat": total_lat / len(region_events),
                    "lon": total_lon / len(region_events),
                    "event_count": len(region_events),
                    "top_categories": [name for name, _ in categories.most_common(3)],
                    "severity": max_severity,
                }
            )

        return sorted(regions, key=lambda item: int(item["event_count"]), reverse=True)

    def region_events(self, region_id: str, limit: int = 200) -> list[Event]:
        return list(self.repo.list_events_by_country(region_id, limit=limit))

    @staticmethod
    def _aggregate_severity(severities: list[str]) -> str:
        if any(value == "high" for value in severities):
            return "high"
        if any(value == "medium" for value in severities):
            return "medium"
        return "low"
