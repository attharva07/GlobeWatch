"""News domain service for event retrieval and seeding."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.event_repository import EventRepository


class NewsService:
    """Handles event bootstrap and retrieval operations."""

    def __init__(self, db: Session) -> None:
        self.repo = EventRepository(db)

    def get_events(self, severity: str | None = None, category: str | None = None, limit: int = 100) -> list[Event]:
        return list(self.repo.list_events(severity=severity, category=category, limit=limit))

    def status(self) -> dict[str, str | bool | int]:
        count = self.repo.count()
        return {
            "service": "news",
            "ready": True,
            "detail": "Mock ingestion available; provider adapters can be plugged in.",
            "event_count": count,
        }

    def seed_if_empty(self) -> None:
        """Seed globally distributed mock events when the DB has no rows."""

        if self.repo.count() > 0:
            return

        now = datetime.now(UTC)
        seed_events = [
            Event(
                external_id="mock-paris-001",
                title="Transport strike updates in central Paris",
                description="Public transit delays reported as unions stage a one-day strike.",
                category="transport",
                source="internal-seed",
                lat=48.8566,
                lon=2.3522,
                severity="medium",
                event_timestamp=now,
                country="France",
                city="Paris",
                metadata_json={"tags": ["transit", "strike"], "language": "en"},
            ),
            Event(
                external_id="mock-tokyo-001",
                title="Technology expo opens in Tokyo",
                description="International attendees gather at a public technology event in Tokyo.",
                category="public_event",
                source="internal-seed",
                lat=35.6762,
                lon=139.6503,
                severity="low",
                event_timestamp=now,
                country="Japan",
                city="Tokyo",
                metadata_json={"tags": ["expo", "technology"], "language": "en"},
            ),
            Event(
                external_id="mock-milan-001",
                title="Heavy rainfall warning around Milan",
                description="Local authorities issue caution notices due to expected intense rain.",
                category="weather_alert",
                source="internal-seed",
                lat=45.4642,
                lon=9.19,
                severity="high",
                event_timestamp=now,
                country="Italy",
                city="Milan",
                metadata_json={"tags": ["rainfall", "advisory"], "language": "en"},
            ),
            Event(
                external_id="mock-nyc-001",
                title="Major parade road closures in New York",
                description="Multiple avenues are closed for a city-permitted cultural parade.",
                category="civic",
                source="internal-seed",
                lat=40.7128,
                lon=-74.006,
                severity="medium",
                event_timestamp=now,
                country="United States",
                city="New York",
                metadata_json={"tags": ["parade", "closures"], "language": "en"},
            ),
            Event(
                external_id="mock-delhi-001",
                title="Air quality advisory issued for New Delhi",
                description="Public health bulletin advises reduced outdoor activity in peak hours.",
                category="public_health",
                source="internal-seed",
                lat=28.6139,
                lon=77.209,
                severity="high",
                event_timestamp=now,
                country="India",
                city="New Delhi",
                metadata_json={"tags": ["air-quality", "advisory"], "language": "en"},
            ),
        ]
        self.repo.add_many(seed_events)
