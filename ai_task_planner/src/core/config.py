"""Application configuration management."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Container for runtime configuration values."""

    openai_api_key: str
    google_client_secret_file: Path
    default_calendar_id: str
    notify_lead_minutes: int
    priority_color_low: str
    priority_color_medium: str
    priority_color_high: str
    priority_color_urgent: str
    timezone: ZoneInfo


def _load_env() -> None:
    """Load environment variables from a `.env` file if present."""

    load_dotenv()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return the singleton :class:`AppConfig` instance."""

    _load_env()
    timezone_key = os.getenv("TIMEZONE", "America/New_York")
    tz = ZoneInfo(timezone_key)

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        google_client_secret_file=Path(
            os.getenv("GOOGLE_CLIENT_SECRET_FILE", "./client_secret.json")
        ),
        default_calendar_id=os.getenv("DEFAULT_CALENDAR_ID", "primary"),
        notify_lead_minutes=int(os.getenv("NOTIFY_LEAD_MINUTES", "30")),
        priority_color_low=os.getenv("PRIORITY_COLOR_LOW", "2"),
        priority_color_medium=os.getenv("PRIORITY_COLOR_MEDIUM", "9"),
        priority_color_high=os.getenv("PRIORITY_COLOR_HIGH", "11"),
        priority_color_urgent=os.getenv("PRIORITY_COLOR_URGENT", "4"),
        timezone=tz,
    )


def reset_config_cache() -> None:
    """Clear the cached configuration (useful for tests)."""

    get_config.cache_clear()
