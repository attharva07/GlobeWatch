"""Utility helper functions."""

from __future__ import annotations

from app.utils.enums import SeverityLevel


SEVERITY_MAPPING = {
    "low": SeverityLevel.LOW,
    "minor": SeverityLevel.LOW,
    "medium": SeverityLevel.MEDIUM,
    "moderate": SeverityLevel.MEDIUM,
    "high": SeverityLevel.HIGH,
    "critical": SeverityLevel.HIGH,
}


def normalize_severity(value: str) -> SeverityLevel:
    """Normalize arbitrary severity value into accepted enum."""

    return SEVERITY_MAPPING.get(value.lower(), SeverityLevel.MEDIUM)
