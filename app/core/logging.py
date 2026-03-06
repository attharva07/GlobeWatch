"""Logging setup for structured API logs."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from app.core.config import Settings


class ContextFormatter(logging.Formatter):
    """Add optional context fields to standard logs."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "path"):
            record.path = "-"
        if not hasattr(record, "client_ip"):
            record.client_ip = "-"
        return super().format(record)


def setup_logging(settings: Settings) -> None:
    """Configure application logging with predictable structure."""

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "()": ContextFormatter,
                    "format": f"%(asctime)s %(levelname)s [%(name)s] env={settings.ENVIRONMENT} path=%(path)s ip=%(client_ip)s %(message)s",
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
