"""News domain service for event retrieval and optional seeding."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.event import Event
from app.repositories.event_repository import EventRepository


class NewsService:
    """Handles event retrieval and optional development fallback seeding."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self.repo = EventRepository(db)
        self.settings = settings

    def get_events(self, severity: str | None = None, category: str | None = None, limit: int = 100) -> list[Event]:
        return list(self.repo.list_events(severity=severity, category=category, limit=limit))

    def status(self) -> dict[str, str | bool | int]:
        count = self.repo.count()
        return {
            "service": "news",
            "ready": True,
            "detail": "Real ingestion enabled via provider adapters.",
            "event_count": count,
            "mock_seed_enabled": self.settings.ENABLE_MOCK_SEED,
        }

    def seed_if_empty(self) -> None:
        if not self.settings.ENABLE_MOCK_SEED or self.repo.count() > 0:
            return

        now = datetime.now(UTC)
        self.repo.add_many(
            [
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
                    metadata_json={"provider": "mock", "tags": ["transit", "strike"], "language": "en"},
                )
            ]
        )
