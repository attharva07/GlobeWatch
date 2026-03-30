"""Schemas for additional geospatial data layers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class _ExtraAllowed(BaseModel):
    """Base model that passes unknown fields through to the JSON response."""
    model_config = ConfigDict(extra="allow")


class FlightTrack(_ExtraAllowed):
    id: str
    callsign: str
    origin: list[float]
    destination: list[float]
    current_position: list[float]
    heading: float
    speed: float
    altitude: float
    aircraft_type: str
    timestamp: datetime
    # Optional enriched fields from live providers
    origin_country: str | None = None


class FlightListResponse(BaseModel):
    flights: list[FlightTrack]
    count: int


class ShipTrack(_ExtraAllowed):
    id: str
    name: str
    mmsi: str
    position: list[float]
    path: list[list[float]]
    speed: float
    heading: float
    ship_type: str
    destination: str
    timestamp: datetime
    flag: str | None = None
    imo: str | None = None


class ShipListResponse(BaseModel):
    ships: list[ShipTrack]
    count: int


class CyberIOC(_ExtraAllowed):
    id: str
    ip: str
    lat: float
    lon: float
    threat_type: str
    severity: str
    country: str
    isp: str
    count: int
    first_seen: str
    last_seen: str


class CyberIOCListResponse(BaseModel):
    iocs: list[CyberIOC]
    count: int


class SignalCoverage(_ExtraAllowed):
    lat: float
    lon: float
    intensity: float
    frequency: float
    signal_type: str
    station_name: str | None = None
    observations: int | None = None


class SignalListResponse(BaseModel):
    signals: list[SignalCoverage]
    count: int


class SatelliteOrbit(_ExtraAllowed):
    id: str
    name: str
    norad_id: int
    path: list[list[float]]
    current_position: list[float]
    orbit_type: str
    timestamp: datetime
    tle_line1: str | None = None
    tle_line2: str | None = None


class SatelliteListResponse(BaseModel):
    satellites: list[SatelliteOrbit]
    count: int


class ConflictEvent(_ExtraAllowed):
    lat: float
    lon: float
    type: str
    date: str
    fatalities: int | None = None
    actor1: str | None = None
    actor2: str | None = None


class ConflictZone(_ExtraAllowed):
    id: str
    name: str
    geometry: dict[str, Any]
    severity: str
    event_count: int
    description: str
    events: list[ConflictEvent]


class ConflictListResponse(BaseModel):
    conflicts: list[ConflictZone]
    count: int


class EntityLink(_ExtraAllowed):
    id: str
    source_name: str
    target_name: str
    source_position: list[float]
    target_position: list[float]
    relationship: str
    strength: float
    source_events: int | None = None
    target_events: int | None = None


class EntityLinkListResponse(BaseModel):
    links: list[EntityLink]
    count: int
