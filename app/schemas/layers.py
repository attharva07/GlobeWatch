"""Schemas for additional geospatial data layers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FlightTrack(BaseModel):
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


class FlightListResponse(BaseModel):
    flights: list[FlightTrack]
    count: int


class ShipTrack(BaseModel):
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


class ShipListResponse(BaseModel):
    ships: list[ShipTrack]
    count: int


class CyberIOC(BaseModel):
    id: str
    ip: str
    lat: float
    lon: float
    threat_type: str
    severity: str
    country: str
    isp: str
    count: int
    first_seen: datetime
    last_seen: datetime


class CyberIOCListResponse(BaseModel):
    iocs: list[CyberIOC]
    count: int


class SignalCoverage(BaseModel):
    lat: float
    lon: float
    intensity: float
    frequency: float
    signal_type: str


class SignalListResponse(BaseModel):
    signals: list[SignalCoverage]
    count: int


class SatelliteOrbit(BaseModel):
    id: str
    name: str
    norad_id: int
    path: list[list[float]]
    current_position: list[float]
    orbit_type: str
    timestamp: datetime


class SatelliteListResponse(BaseModel):
    satellites: list[SatelliteOrbit]
    count: int


class ConflictEvent(BaseModel):
    lat: float
    lon: float
    type: str
    date: str


class ConflictZone(BaseModel):
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


class EntityLink(BaseModel):
    id: str
    source_name: str
    target_name: str
    source_position: list[float]
    target_position: list[float]
    relationship: str
    strength: float


class EntityLinkListResponse(BaseModel):
    links: list[EntityLink]
    count: int
