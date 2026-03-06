"""Schemas for location profiles."""

from pydantic import BaseModel


class LocationProfile(BaseModel):
    """Frontend-ready location object."""

    id: str
    name: str
    lat: float
    lon: float
    country: str
    region: str
    context: str
