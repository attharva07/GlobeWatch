"""Schemas for news event endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.utils.enums import SeverityLevel


class EventRead(BaseModel):
    """Read projection for event entities."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None
    title: str
    description: str
    category: str
    source: str
    lat: float
    lon: float
    severity: SeverityLevel
    event_timestamp: datetime
    country: str
    city: str
    metadata_json: dict[str, Any]


class EventListResponse(BaseModel):
    """Paginated-like list response for events."""

    events: list[EventRead]
    count: int
