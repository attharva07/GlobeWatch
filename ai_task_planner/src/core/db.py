"""Database utilities and session management."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from sqlalchemy import Column, Engine, String, Table, create_engine, event, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base declarative class."""


_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None
_META_TABLE: Table | None = None


DB_FILE = Path("ai_task_planner.db")


def _utcnow() -> datetime:
    return datetime.utcnow()


def get_engine() -> Engine:
    """Return the singleton SQLAlchemy engine."""

    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)
    return _ENGINE


def get_session_factory() -> sessionmaker[Session]:
    """Return the configured :class:`sessionmaker`."""

    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine(), expire_on_commit=False, class_=Session)
    return _SESSION_FACTORY


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_meta_table() -> Table:
    global _META_TABLE
    if _META_TABLE is None:
        metadata = Base.metadata
        _META_TABLE = Table(
            "meta",
            metadata,
            Column("key", String(255), primary_key=True),
            Column("value", String(2048)),
        )
    return _META_TABLE


def init_db() -> None:
    """Create all database tables."""

    from . import models  # noqa: F401 ensures models are registered

    engine = get_engine()
    _ensure_meta_table()
    Base.metadata.create_all(engine)


def get_meta(session: Session, key: str) -> str | None:
    """Retrieve a value from the meta table."""

    meta_table = _ensure_meta_table()
    statement = select(meta_table.c.value).where(meta_table.c.key == key)
    result = session.execute(statement).scalar_one_or_none()
    return result


def set_meta(session: Session, key: str, value: str | None) -> None:
    """Upsert a value in the meta table."""

    meta_table = _ensure_meta_table()
    if value is None:
        session.execute(meta_table.delete().where(meta_table.c.key == key))
        return
    insert_stmt = insert(meta_table).values(key=key, value=value)
    session.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=[meta_table.c.key], set_={"value": value}
        )
    )


@event.listens_for(Base, "attribute_instrument")
def _setup_timestamp_listener(mapper, cls) -> None:  # type: ignore[override]
    if not hasattr(cls, "__table__"):
        return
    table = cls.__table__
    if "created_at" in table.c and "updated_at" in table.c:

        @event.listens_for(cls, "before_insert", propagate=True)
        def before_insert(mapper, connection, target) -> None:  # type: ignore[override]
            now = _utcnow()
            if getattr(target, "created_at", None) is None:
                setattr(target, "created_at", now)
            setattr(target, "updated_at", now)

        @event.listens_for(cls, "before_update", propagate=True)
        def before_update(mapper, connection, target) -> None:  # type: ignore[override]
            setattr(target, "updated_at", _utcnow())
