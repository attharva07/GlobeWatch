"""Desktop notification helper."""

from __future__ import annotations

import logging

try:
    from plyer import notification
except Exception:  # noqa: BLE001 - fallback when plyer not installed on host
    notification = None

LOGGER = logging.getLogger(__name__)


def send(title: str, message: str) -> None:
    """Send a desktop notification if possible."""

    if notification is None:
        LOGGER.warning("Notifications are unavailable on this platform")
        return
    try:
        notification.notify(title=title, message=message, app_name="AI Task Planner")
    except Exception as exc:  # noqa: BLE001 - avoid crashing notifications
        LOGGER.error("Failed to send notification: %s", exc)
