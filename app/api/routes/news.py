"""News event routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.common import ServiceStatusResponse
from app.schemas.event import EventListResponse, EventRead
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/events", response_model=EventListResponse)
def list_events(
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> EventListResponse:
    """List geolocated news events from DB-backed data."""

    service = NewsService(db)
    events = service.get_events(severity=severity, category=category, limit=limit)
    return EventListResponse(events=[EventRead.model_validate(e) for e in events], count=len(events))


@router.get("/status")
def news_status(db: Session = Depends(get_db_session)) -> dict[str, str | bool | int]:
    """Return news ingestion/readiness details."""

    service = NewsService(db)
    return service.status()
