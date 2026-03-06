"""Weather readiness routes."""

from fastapi import APIRouter

from app.schemas.common import ServiceStatusResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/status", response_model=ServiceStatusResponse)
def weather_status() -> ServiceStatusResponse:
    return WeatherService.status()
