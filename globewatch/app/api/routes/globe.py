"""Globe marker routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.marker import MarkerListResponse
from app.services.marker_service import MarkerService
from app.services.news_service import NewsService

router = APIRouter(prefix="/globe", tags=["globe"])


@router.get("/markers", response_model=MarkerListResponse)
def get_markers(
    layers: str = Query(default="news"),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> MarkerListResponse:
    """Return normalized markers for requested globe layers."""

    markers = []
    requested_layers = {item.strip().lower() for item in layers.split(",") if item.strip()}

    if "news" in requested_layers:
        news_events = NewsService(db).get_events(severity=severity, category=category, limit=limit)
        markers.extend(MarkerService().build_markers(news_events))

    return MarkerListResponse(markers=markers, count=len(markers))
