"""Database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Task(Base):
    """Task model representing local planner tasks."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String, default="")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    due_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gcal_event_id: Mapped[str | None] = mapped_column(String(128))
    gcal_calendar_id: Mapped[str | None] = mapped_column(String(256), default=None)
    color_id: Mapped[str | None] = mapped_column(String(16))

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id!r}, title={self.title!r}, priority={self.priority!r}, "
            f"status={self.status!r})"
        )
