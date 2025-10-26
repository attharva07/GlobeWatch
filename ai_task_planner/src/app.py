"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from .core.config import get_config
from .core.db import init_db
from .core.gcal import ensure_client
from .core.logging_conf import setup_from_env
from .core.scheduler import SchedulerManager
from .ui.main_window import MainWindow
from .ui.theme import apply_dark_theme


LOGGER = logging.getLogger(__name__)


def _prepare_environment() -> None:
    setup_from_env()
    cfg = get_config()
    init_db()
    if not cfg.google_client_secret_file.exists():
        LOGGER.warning("Google client secret file missing at %s", cfg.google_client_secret_file)
        return
    try:
        ensure_client()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Google OAuth setup failed: %s", exc)


def main() -> None:
    """Launch the AI Task Planner application."""

    _prepare_environment()
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    scheduler = SchedulerManager()
    scheduler.start()
    window = MainWindow(scheduler)
    window.show()
    exit_code = app.exec()
    scheduler.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
