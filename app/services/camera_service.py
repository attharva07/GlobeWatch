"""Placeholder public camera service layer."""

from app.schemas.common import ServiceStatusResponse


class CameraService:
    """Returns readiness of future public camera feeds integration."""

    @staticmethod
    def status() -> ServiceStatusResponse:
        return ServiceStatusResponse(service="cameras", ready=False, detail="Provider integration not yet enabled.")
