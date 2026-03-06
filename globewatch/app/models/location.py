"""Optional location model placeholder for future persistence."""

from dataclasses import dataclass


@dataclass
class LocationRecord:
    """Simple in-memory location profile contract for future DB model migration."""

    id: str
    name: str
    lat: float
    lon: float
    country: str
    region: str
