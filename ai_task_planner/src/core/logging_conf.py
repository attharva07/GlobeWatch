"""Logging configuration for the AI Task Planner application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def configure_logging(debug: bool = False) -> None:
    """Configure application-wide logging handlers.

    Args:
        debug: When ``True`` sets lower logging levels for verbose debugging.
    """

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    log_level = logging.DEBUG if debug else logging.INFO
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if not debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    core_logger_level = logging.DEBUG if debug else logging.INFO
    for name in ["src.core", "src.ui"]:
        logging.getLogger(name).setLevel(core_logger_level)


def setup_from_env() -> None:
    """Configure logging based on the ``APP_DEBUG`` environment variable."""

    debug_flag = os.getenv("APP_DEBUG", "0") == "1"
    configure_logging(debug_flag)
