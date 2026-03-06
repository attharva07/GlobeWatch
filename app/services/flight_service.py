"""Placeholder flight service layer."""

from app.schemas.common import ServiceStatusResponse


class FlightService:
    """Returns readiness of future flights integration."""

    @staticmethod
    def status() -> ServiceStatusResponse:
        return ServiceStatusResponse(service="flights", ready=False, detail="Provider integration not yet enabled.")
