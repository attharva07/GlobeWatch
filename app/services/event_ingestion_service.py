"""Event ingestion pipeline for external providers."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.providers.gdelt_provider import GDELTProvider, ProviderEvent, ProviderNetworkError, ProviderRateLimitError

logger = logging.getLogger(__name__)


class EventIngestionService:
    """Fetches, normalizes and upserts provider events."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self.repo = EventRepository(db)
        self.settings = settings

    def ingest(self) -> dict[str, int | str | bool]:
        provider = self._provider()
        try:
            provider_events = provider.fetch_events()
        except ProviderRateLimitError:
            logger.warning(
                "Ingestion skipped due to provider rate limit; retaining cached database data",
                extra={"provider": self.settings.INGESTION_PROVIDER, "data_mode": "cached", "rate_limited": True},
            )
            return {
                "provider": self.settings.INGESTION_PROVIDER,
                "created": 0,
                "updated": 0,
                "rate_limited": True,
                "data_mode": "cached",
            }
        except ProviderNetworkError:
            logger.warning(
                "Ingestion skipped due to network error; retaining cached database data",
                extra={"provider": self.settings.INGESTION_PROVIDER, "data_mode": "cached", "rate_limited": False},
            )
            return {
                "provider": self.settings.INGESTION_PROVIDER,
                "created": 0,
                "updated": 0,
                "rate_limited": False,
                "data_mode": "cached",
            }
        created = 0
        updated = 0
        seen_external_ids: set[str] = set()
        seen_fingerprints: set[str] = set()

        for incoming in provider_events:
            fingerprint = self._fingerprint(incoming)
            existing = self.repo.find_by_external_id_or_fingerprint(incoming.external_id, fingerprint)
            if not existing and ((incoming.external_id and incoming.external_id in seen_external_ids) or fingerprint in seen_fingerprints):
                # Duplicate within this batch — count as updated (already ingested earlier in this cycle)
                updated += 1
                continue
            metadata_json = dict(incoming.metadata)
            metadata_json["provider"] = incoming.provider
            metadata_json["url"] = incoming.url
            metadata_json["fingerprint"] = fingerprint

            if existing:
                existing.title = incoming.title
                existing.description = incoming.description
                existing.category = incoming.category
                existing.source = incoming.source
                existing.lat = incoming.lat
                existing.lon = incoming.lon
                existing.country = incoming.country
                existing.city = incoming.city
                existing.event_timestamp = incoming.event_timestamp
                existing.metadata_json = metadata_json
                updated += 1
            else:
                severity = self._severity_from_category(incoming.category)
                self.repo.add(
                    Event(
                        external_id=incoming.external_id,
                        title=incoming.title,
                        description=incoming.description,
                        category=incoming.category,
                        source=incoming.source,
                        lat=incoming.lat,
                        lon=incoming.lon,
                        severity=severity,
                        event_timestamp=incoming.event_timestamp.astimezone(UTC)
                        if incoming.event_timestamp.tzinfo
                        else incoming.event_timestamp.replace(tzinfo=UTC),
                        country=incoming.country,
                        city=incoming.city,
                        metadata_json=metadata_json,
                    )
                )
                created += 1

            if incoming.external_id:
                seen_external_ids.add(incoming.external_id)
            seen_fingerprints.add(fingerprint)

        self.repo.commit()
        data_mode = "fresh" if (created or updated) else "cached"
        logger.info(
            "Ingestion cycle complete",
            extra={
                "events_created": created,
                "events_updated": updated,
                "provider": self.settings.INGESTION_PROVIDER,
                "data_mode": data_mode,
            },
        )
        if not provider_events:
            logger.warning(
                "Ingestion returned no provider events; continuing with cached database data",
                extra={"provider": self.settings.INGESTION_PROVIDER, "data_mode": "cached", "rate_limited": False},
            )
        return {
            "provider": self.settings.INGESTION_PROVIDER,
            "created": created,
            "updated": updated,
            "rate_limited": False,
            "data_mode": data_mode,
        }

    def _provider(self) -> GDELTProvider:
        return GDELTProvider(self.settings)

    @staticmethod
    def _fingerprint(event: ProviderEvent) -> str:
        payload = f"{event.title}|{event.event_timestamp.isoformat()}|{event.lat:.4f}|{event.lon:.4f}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _severity_from_category(category: str) -> str:
        if category in {"weather_alert", "public_health"}:
            return "high"
        if category in {"civic"}:
            return "medium"
        return "low"
