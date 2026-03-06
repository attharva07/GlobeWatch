"""Repository helpers for event persistence queries."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models.event import Event


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

    def count(self) -> int:
        return len(self.db.execute(select(Event.id)).scalars().all())

    def add_many(self, events: list[Event]) -> None:
        self.db.add_all(events)
        self.db.commit()
