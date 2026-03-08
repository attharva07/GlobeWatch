"""Globe marker routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import rate_limit_guard
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventRead
from app.schemas.marker import MarkerListResponse
from app.schemas.region import RegionEventsResponse, RegionMarkerListResponse
from app.services.marker_service import MarkerService
from app.services.news_service import NewsService
from app.services.region_service import RegionService
from app.utils.enums import SeverityLevel

router = APIRouter(prefix="/globe", tags=["globe"])


@router.get("/markers", response_model=MarkerListResponse, dependencies=[Depends(rate_limit_guard)])
def get_markers(
    layers: Annotated[str, Query(min_length=4, max_length=32)] = "news",
    severity: Annotated[SeverityLevel | None, Query()] = None,
    category: Annotated[str | None, Query(min_length=2, max_length=40, pattern=r"^[a-zA-Z_\-]+$")] = None,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db_session),
) -> MarkerListResponse:
    markers = []
    requested_layers = {item.strip().lower() for item in layers.split(",") if item.strip()}
    allowed_layers = {"news"}
    if not requested_layers or not requested_layers.issubset(allowed_layers):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid layers. Allowed values: news")

    if "news" in requested_layers:
        severity_value = severity.value if severity else None
        news_events = NewsService(db, get_settings()).get_events(severity=severity_value, category=category, limit=limit)
        markers.extend(MarkerService().build_markers(news_events))

    return MarkerListResponse(markers=markers, count=len(markers))


@router.get("/regions", response_model=RegionMarkerListResponse, dependencies=[Depends(rate_limit_guard)])
def list_regions(db: Session = Depends(get_db_session)) -> RegionMarkerListResponse:
    regions = RegionService(EventRepository(db)).list_regions()
    return RegionMarkerListResponse(regions=regions, count=len(regions))


@router.get("/regions/{region_id}/events", response_model=RegionEventsResponse, dependencies=[Depends(rate_limit_guard)])
def list_region_events(region_id: str, db: Session = Depends(get_db_session)) -> RegionEventsResponse:
    events = RegionService(EventRepository(db)).region_events(region_id)
    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return RegionEventsResponse(
        region_id=region_id,
        region_name=events[0].country,
        event_count=len(events),
        events=[EventRead.model_validate(item) for item in events],
    )
