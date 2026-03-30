"""Repository helpers for event persistence queries."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.event import Event


# Named tuple-like for country aggregate results
from dataclasses import dataclass


@dataclass
class CountryAggregate:
    country: str
    lat: float
    lon: float
    event_count: int
    top_category: str


class EventRepository:
    """Data-access abstraction for Event queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_events(
        self,
        *,
        severity: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> Sequence[Event]:
        query: Select[tuple[Event]] = select(Event).order_by(desc(Event.event_timestamp))
        if severity:
            query = query.where(Event.severity == severity)
        if category:
            query = query.where(Event.category == category)
        return self.db.execute(query.limit(limit)).scalars().all()

    def list_events_by_country(self, region_id: str, limit: int = 200) -> Sequence[Event]:
        query: Select[tuple[Event]] = (
            select(Event)
            .where(Event.country.ilike(region_id))
            .order_by(desc(Event.event_timestamp))
            .limit(limit)
        )
        return self.db.execute(query).scalars().all()

    def count(self) -> int:
        return self.db.execute(select(func.count()).select_from(Event)).scalar_one()

    def add_many(self, events: list[Event]) -> None:
        self.db.add_all(events)
        self.db.commit()

    def add(self, event: Event) -> None:
        self.db.add(event)

    def commit(self) -> None:
        self.db.commit()

    def country_aggregates(self, limit: int = 30) -> list[CountryAggregate]:
        """Return per-country event summaries with centroid coordinates."""
        rows = (
            self.db.execute(
                select(
                    Event.country,
                    func.avg(Event.lat).label("lat"),
                    func.avg(Event.lon).label("lon"),
                    func.count().label("cnt"),
                    Event.category,
                )
                .where(Event.country != "")
                .group_by(Event.country, Event.category)
                .order_by(desc(func.count()))
                .limit(limit * 5)
            )
            .all()
        )
        # Aggregate across categories per country
        country_data: dict[str, dict] = {}
        for row in rows:
            c = row.country
            if c not in country_data:
                country_data[c] = {
                    "lat": float(row.lat),
                    "lon": float(row.lon),
                    "count": 0,
                    "top_category": row.category,
                    "top_count": 0,
                }
            country_data[c]["count"] += row.cnt
            if row.cnt > country_data[c]["top_count"]:
                country_data[c]["top_count"] = row.cnt
                country_data[c]["top_category"] = row.category

        return [
            CountryAggregate(
                country=c,
                lat=d["lat"],
                lon=d["lon"],
                event_count=d["count"],
                top_category=d["top_category"],
            )
            for c, d in sorted(country_data.items(), key=lambda x: -x[1]["count"])[:limit]
        ]

    def find_by_external_id_or_fingerprint(self, external_id: str | None, fingerprint: str) -> Event | None:
        if external_id:
            by_external = self.db.execute(select(Event).where(Event.external_id == external_id)).scalar_one_or_none()
            if by_external:
                return by_external
        return self.db.execute(select(Event).where(Event.metadata_json["fingerprint"].as_string() == fingerprint)).scalar_one_or_none()
