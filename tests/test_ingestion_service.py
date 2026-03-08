from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_db_session
from app.db.base import Base
from app.db.session import engine
from app.services.event_ingestion_service import EventIngestionService
from app.services.providers.gdelt_provider import ProviderEvent, ProviderRateLimitError


def test_ingestion_deduplicates_by_external_id() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db_session())
    settings = Settings(ENVIRONMENT="test")
    service = EventIngestionService(db, settings)

    class StubProvider:
        def fetch_events(self):
            ext = f"x-{uuid4()}"
            event = ProviderEvent(
                external_id=ext,
                title="Flood warning",
                description="desc",
                category="weather_alert",
                source="example.com",
                provider="gdelt",
                lat=10.0,
                lon=20.0,
                country="Testland",
                city="Capital",
                event_timestamp=datetime.now(UTC),
                url="https://example.com/1",
                metadata={},
            )
            return [event, event]

    service._provider = lambda: StubProvider()  # type: ignore[method-assign]
    result = service.ingest()
    assert result["created"] == 1
    assert result["updated"] == 1
    db.close()


def test_ingestion_handles_provider_rate_limit() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db_session())
    settings = Settings(ENVIRONMENT="test")
    service = EventIngestionService(db, settings)

    class StubProvider:
        def fetch_events(self):
            raise ProviderRateLimitError("rate limited")

    service._provider = lambda: StubProvider()  # type: ignore[method-assign]
    result = service.ingest()
    assert result["created"] == 0
    assert result["updated"] == 0
    assert result["rate_limited"] is True
    assert result["data_mode"] == "cached"
    db.close()
