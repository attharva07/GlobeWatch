"""Dry-run tests for the sync logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from ..core import sync
from ..core.db import DB_FILE, init_db, session_scope
from ..core.models import Task


@pytest.fixture(autouse=True)
def _reset_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    init_db()


def test_run_sync_push_and_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    pushed_events: list[int] = []

    def fake_upsert(task: Task) -> str:
        pushed_events.append(task.id)
        return f"event-{task.id}"

    remote_event = {
        "id": "event-1",
        "status": "confirmed",
        "summary": "Task from Google",
        "description": "Imported\n\n[Priority:high][Status:in_progress][LocalID:1]",
        "start": {"dateTime": "2023-09-01T12:00:00Z"},
        "end": {"dateTime": "2023-09-01T13:00:00Z"},
        "colorId": "11",
        "organizer": {"email": "primary"},
        "updated": "2099-09-01T12:30:00Z",
    }

    def fake_pull(token: str | None) -> tuple[list[dict[str, Any]], str | None]:
        return ([remote_event], "token-123")

    monkeypatch.setattr(sync.gcal, "upsert_event", fake_upsert)
    monkeypatch.setattr(sync.gcal, "pull_changed_events", fake_pull)

    with session_scope() as session:
        task = Task(
            title="Local Task",
            description="",
            priority="medium",
            status="pending",
            start_ts=datetime.now(timezone.utc),
            due_ts=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        session.add(task)

    sync.run_sync()

    with session_scope() as session:
        stored = session.get(Task, 1)
        assert stored is not None
        assert stored.gcal_event_id == "event-1"
        assert stored.priority == "high"
        assert stored.status == "in_progress"
        assert pushed_events == [1]
