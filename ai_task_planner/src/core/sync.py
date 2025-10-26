"""Two-way synchronization with Google Calendar."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import gcal
from .config import get_config
from .db import get_meta, session_scope, set_meta
from .mapping import color_to_priority
from .models import Task
from .validators import ensure_priority, ensure_status

LOGGER = logging.getLogger(__name__)

META_SYNC_TOKEN = "gcal_sync_token"
META_LAST_PUSH = "gcal_last_push"


def _parse_gcal_datetime(value: dict[str, str]) -> datetime:
    if "dateTime" in value:
        iso_value = value["dateTime"].replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_value)
    else:
        iso_value = f"{value['date']}T00:00:00+00:00"
        dt = datetime.fromisoformat(iso_value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_description(description: str) -> dict[str, str]:
    markers = {}
    if not description:
        return markers
    for token in description.split("["):
        if ":" in token and "]" in token:
            key_val = token.split("]", 1)[0]
            if ":" in key_val:
                key, val = key_val.split(":", 1)
                markers[key] = val
    return markers


def local_to_gcal(session: Session) -> None:
    """Push local changes to Google Calendar."""

    last_push_str = get_meta(session, META_LAST_PUSH)
    last_push = (
        datetime.fromisoformat(last_push_str).astimezone(timezone.utc)
        if last_push_str
        else datetime.fromtimestamp(0, tz=timezone.utc)
    )
    stmt = select(Task)
    tasks: Iterable[Task] = session.scalars(stmt)
    now = datetime.now(timezone.utc)
    for task in tasks:
        if task.gcal_event_id is None or task.updated_at > last_push:
            try:
                event_id = gcal.upsert_event(task)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to push task %s: %s", task.id, exc)
                continue
            task.gcal_event_id = event_id
            task.gcal_calendar_id = task.gcal_calendar_id or get_config().default_calendar_id
    set_meta(session, META_LAST_PUSH, now.isoformat())


def _update_task_from_event(task: Task, event: dict[str, Any]) -> None:
    cfg = get_config()
    start = event.get("start", {})
    end = event.get("end", {})
    start_dt = _parse_gcal_datetime(start) if start else None
    end_dt = _parse_gcal_datetime(end) if end else None
    priority = color_to_priority(event.get("colorId", "")) or task.priority
    description = event.get("description", "") or ""
    markers = _parse_description(description)
    status = markers.get("Status", task.status)
    try:
        status = ensure_status(status)
    except Exception:
        status = task.status
    try:
        priority = ensure_priority(priority)
    except Exception:
        priority = task.priority
    task.title = event.get("summary", task.title)
    task.description = description.split("\n\n")[0]
    task.priority = priority
    task.status = status
    task.start_ts = start_dt
    task.due_ts = end_dt
    task.gcal_event_id = event["id"]
    task.gcal_calendar_id = event.get("organizer", {}).get("email", cfg.default_calendar_id)
    task.color_id = event.get("colorId")


def gcal_to_local(session: Session) -> None:
    """Pull changes from Google Calendar into the local database."""

    sync_token = get_meta(session, META_SYNC_TOKEN)
    try:
        events, new_token = gcal.pull_changed_events(sync_token)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to fetch Google events: %s", exc)
        return

    for event in events:
        event_id = event["id"]
        status = event.get("status", "confirmed")
        if status == "cancelled":
            stmt = select(Task).where(Task.gcal_event_id == event_id)
            task = session.scalars(stmt).first()
            if task:
                task.status = "done"
                task.gcal_event_id = None
            continue

        description = event.get("description", "") or ""
        markers = _parse_description(description)
        local_id = markers.get("LocalID")
        google_updated = datetime.fromisoformat(event["updated"].replace("Z", "+00:00")).astimezone(timezone.utc)
        task: Task | None = None
        if local_id:
            stmt = select(Task).where(Task.id == int(local_id))
            task = session.scalars(stmt).first()
        if not task:
            stmt = select(Task).where(Task.gcal_event_id == event_id)
            task = session.scalars(stmt).first()
        if task:
            if task.updated_at > google_updated:
                continue
            _update_task_from_event(task, event)
        else:
            status_value = markers.get("Status", "pending")
            try:
                status_value = ensure_status(status_value)
            except Exception:
                status_value = "pending"
            start_payload = event.get("start", {})
            end_payload = event.get("end", {})
            task = Task(
                title=event.get("summary", "Untitled"),
                description=description.split("\n\n")[0],
                priority=color_to_priority(event.get("colorId", "")) or "medium",
                status=status_value,
                start_ts=_parse_gcal_datetime(start_payload) if start_payload else None,
                due_ts=_parse_gcal_datetime(end_payload) if end_payload else None,
                gcal_event_id=event_id,
                gcal_calendar_id=event.get("organizer", {}).get("email", get_config().default_calendar_id),
                color_id=event.get("colorId"),
            )
            session.add(task)
            if task.priority in {"high", "urgent"}:
                from .notify import send

                send(task.title, "New high priority task imported from Google")

    if new_token:
        set_meta(session, META_SYNC_TOKEN, new_token)


def run_sync() -> None:
    """Run a full synchronization cycle."""

    with session_scope() as session:
        local_to_gcal(session)
        gcal_to_local(session)
