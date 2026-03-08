"""Schemas for region aggregation endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.event import EventRead


class RegionMarker(BaseModel):
    region_id: str
    region_name: str
    lat: float
    lon: float
    event_count: int
    top_categories: list[str]
    severity: str


class RegionMarkerListResponse(BaseModel):
    regions: list[RegionMarker]
    count: int


class RegionEventsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    region_id: str
    region_name: str
    event_count: int
    events: list[EventRead]
