"""Schemas for map marker payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.utils.enums import SeverityLevel


class Marker(BaseModel):
    """Unified marker consumed by frontend globe layers."""

    id: str
    type: str
    title: str
    lat: float
    lon: float
    source: str
    timestamp: datetime
    severity: SeverityLevel
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarkerListResponse(BaseModel):
    """Collection of normalized markers."""

    markers: list[Marker]
    count: int
