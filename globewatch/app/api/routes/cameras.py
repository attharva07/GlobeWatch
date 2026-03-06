"""Camera readiness routes."""

from fastapi import APIRouter

from app.schemas.common import ServiceStatusResponse
from app.services.camera_service import CameraService

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/status", response_model=ServiceStatusResponse)
def cameras_status() -> ServiceStatusResponse:
    return CameraService.status()
