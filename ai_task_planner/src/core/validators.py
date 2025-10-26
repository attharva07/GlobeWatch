"""Validation helpers for task payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import get_config

VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_STATUSES = {"pending", "in_progress", "done"}


class ValidationError(ValueError):
    """Raised when validation fails."""


def ensure_priority(value: str) -> str:
    """Validate and normalize a priority string."""

    normalized = value.lower()
    if normalized not in VALID_PRIORITIES:
        raise ValidationError(f"Invalid priority: {value}")
    return normalized


def ensure_status(value: str) -> str:
    """Validate and normalize a status string."""

    normalized = value.lower()
    if normalized not in VALID_STATUSES:
        raise ValidationError(f"Invalid status: {value}")
    return normalized


def parse_iso_datetime(value: str | None, tz: ZoneInfo | None = None) -> datetime | None:
    """Parse an ISO8601 datetime string into a timezone-aware UTC datetime."""

    if value in (None, "", "null"):
        return None
    tzinfo = tz or get_config().timezone
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzinfo)
    dt_utc = dt.astimezone(ZoneInfo("UTC"))
    return dt_utc


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the dictionary returned by the AI parser."""

    cfg = get_config()
    payload = payload.copy()
    payload["title"] = payload.get("title", "").strip()
    if not payload["title"]:
        raise ValidationError("Title is required")
    payload["description"] = payload.get("description", "").strip()
    payload["priority"] = ensure_priority(payload.get("priority", "medium"))
    payload["status"] = ensure_status(payload.get("status", "pending"))
    payload["start_ts"] = parse_iso_datetime(payload.get("start_ts"), cfg.timezone)
    payload["due_ts"] = parse_iso_datetime(payload.get("due_ts"), cfg.timezone)
    return payload
