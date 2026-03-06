"""Placeholder weather service layer."""

from app.schemas.common import ServiceStatusResponse


class WeatherService:
    """Returns readiness of future weather integration."""

    @staticmethod
    def status() -> ServiceStatusResponse:
        return ServiceStatusResponse(service="weather", ready=False, detail="Provider integration not yet enabled.")
