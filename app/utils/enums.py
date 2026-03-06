"""Domain enums for normalized response values."""

from enum import Enum


class SeverityLevel(str, Enum):
    """Allowed marker severity values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
