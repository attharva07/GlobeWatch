"""Logging setup for structured API logs."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from app.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """Configure application logging with predictable structure."""

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": settings.LOG_LEVEL,
                }
            },
            "root": {"handlers": ["default"], "level": settings.LOG_LEVEL},
        }
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
