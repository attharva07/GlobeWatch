"""Flight readiness routes."""

from fastapi import APIRouter

from app.schemas.common import ServiceStatusResponse
from app.services.flight_service import FlightService

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/status", response_model=ServiceStatusResponse)
def flights_status() -> ServiceStatusResponse:
    return FlightService.status()
