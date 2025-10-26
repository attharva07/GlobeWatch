"""Database tests for Task model."""

from __future__ import annotations

import pytest

from ..core.db import DB_FILE, init_db, session_scope
from ..core.models import Task


@pytest.fixture(autouse=True)
def _prepare_db() -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    init_db()


def test_create_update_delete_task() -> None:
    with session_scope() as session:
        task = Task(title="Test", description="", priority="medium", status="pending")
        session.add(task)
    assert task.id is not None

    with session_scope() as session:
        stored = session.get(Task, task.id)
        assert stored is not None
        stored.title = "Updated"

    with session_scope() as session:
        stored = session.get(Task, task.id)
        assert stored is not None
        assert stored.title == "Updated"
        session.delete(stored)

    with session_scope() as session:
        assert session.get(Task, task.id) is None
