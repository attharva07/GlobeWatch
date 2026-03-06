"""Location routes."""

from fastapi import APIRouter

from app.schemas.location import LocationProfile
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/sample", response_model=LocationProfile)
def sample_location() -> LocationProfile:
    """Return sample location profile for frontend development."""

    return LocationService.sample_profile()
