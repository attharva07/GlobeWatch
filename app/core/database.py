"""Convenience accessors for DB session wiring."""

from app.db.session import SessionLocal


def get_db_session():
    """Yield SQLAlchemy session for route dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
