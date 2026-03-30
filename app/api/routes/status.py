"""Overall provider and system status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import rate_limit_guard
from app.repositories.event_repository import EventRepository
from app.services.layer_cache import get_status as get_layer_status

router = APIRouter(prefix="/status", tags=["status"])


@router.get("", dependencies=[Depends(rate_limit_guard)])
def system_status(db: Session = Depends(get_db_session)) -> dict:
    """Return live counts and last-fetch timestamps for all data providers."""
    news_count = EventRepository(db).count()
    layer_status = get_layer_status()

    return {
        "news": {
            "count": news_count,
            "source": "gdelt",
            "status": "ok",
        },
        **{
            key: val
            for key, val in layer_status.items()
        },
    }
