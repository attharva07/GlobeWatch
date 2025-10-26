"""Background scheduler integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from .config import get_config
from .db import session_scope
from .models import Task
from .notify import send as notify_send
from .sync import run_sync

LOGGER = logging.getLogger(__name__)


class SchedulerManager:
    """Manage APScheduler lifecycle for the application."""

    def __init__(self) -> None:
        cfg = get_config()
        self.scheduler = BackgroundScheduler(timezone=str(cfg.timezone))

    def start(self) -> None:
        """Start scheduler jobs."""

        self.scheduler.add_job(run_sync, IntervalTrigger(minutes=5), id="sync-job")
        self.scheduler.add_job(self._check_upcoming_tasks, IntervalTrigger(minutes=1), id="notify-job")
        self.scheduler.start()
        LOGGER.info("Scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler."""

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            LOGGER.info("Scheduler stopped")

    @staticmethod
    def _check_upcoming_tasks() -> None:
        cfg = get_config()
        lead_time = timedelta(minutes=cfg.notify_lead_minutes)
        now_utc = datetime.now(timezone.utc)
        window_start = now_utc
        window_end = now_utc + lead_time
        with session_scope() as session:
            stmt = (
                select(Task)
                .where(Task.due_ts.is_not(None))
                .where(Task.due_ts >= window_start)
                .where(Task.due_ts <= window_end)
                .where(Task.status != "done")
            )
            for task in session.scalars(stmt):
                message = f"Due at {task.due_ts.astimezone(cfg.timezone).strftime('%H:%M')}"
                notify_send(task.title, message)
