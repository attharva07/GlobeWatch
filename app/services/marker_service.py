"""Marker normalization and layer aggregation service."""

from __future__ import annotations

from app.models.event import Event
from app.schemas.marker import Marker
from app.utils.helpers import normalize_severity


class MarkerService:
    """Builds normalized marker payloads for frontend layer consumption."""

    @staticmethod
    def event_to_marker(event: Event) -> Marker:
        metadata = {
            "category": event.category,
            "description": event.description,
            "country": event.country,
            "city": event.city,
            **(event.metadata_json or {}),
        }
        return Marker(
            id=f"news-{event.id}",
            type="news",
            title=event.title,
            lat=event.lat,
            lon=event.lon,
            source=event.source,
            timestamp=event.event_timestamp,
            severity=normalize_severity(event.severity),
            metadata=metadata,
        )

    def build_markers(self, events: list[Event]) -> list[Marker]:
        return [self.event_to_marker(event) for event in events]
