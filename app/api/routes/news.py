"""News event routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import rate_limit_guard
from app.schemas.event import EventListResponse, EventRead
from app.services.news_service import NewsService
from app.utils.enums import SeverityLevel

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/events", response_model=EventListResponse, dependencies=[Depends(rate_limit_guard)])
def list_events(
    severity: Annotated[SeverityLevel | None, Query()] = None,
    category: Annotated[str | None, Query(min_length=2, max_length=40, pattern=r"^[a-zA-Z_\-]+$")] = None,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db_session),
) -> EventListResponse:
    """List geolocated news events from DB-backed data."""

    service = NewsService(db)
    severity_value = severity.value if severity else None
    events = service.get_events(severity=severity_value, category=category, limit=limit)
    return EventListResponse(events=[EventRead.model_validate(e) for e in events], count=len(events))


@router.get("/status")
def news_status(db: Session = Depends(get_db_session)) -> dict[str, str | bool | int]:
    """Return news ingestion/readiness details."""

    service = NewsService(db)
    return service.status()
