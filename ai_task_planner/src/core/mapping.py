"""Priority to Google Calendar color mapping utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .config import get_config


@dataclass(frozen=True)
class PriorityMapping:
    """Priority to color mapping container."""

    forward: Dict[str, str]
    reverse: Dict[str, str]


def build_mapping() -> PriorityMapping:
    """Build mapping dictionaries from configuration."""

    cfg = get_config()
    forward = {
        "low": cfg.priority_color_low,
        "medium": cfg.priority_color_medium,
        "high": cfg.priority_color_high,
        "urgent": cfg.priority_color_urgent,
    }
    reverse = {v: k for k, v in forward.items()}
    return PriorityMapping(forward=forward, reverse=reverse)


def priority_to_color(priority: str) -> str:
    """Return the Google color ID for a priority."""

    mapping = build_mapping().forward
    try:
        return mapping[priority]
    except KeyError as exc:
        raise KeyError(f"Unknown priority '{priority}'") from exc


def color_to_priority(color_id: str) -> str | None:
    """Return the priority for a Google color ID if known."""

    mapping = build_mapping().reverse
    return mapping.get(color_id)
