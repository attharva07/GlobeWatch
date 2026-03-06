"""Location profile service for frontend testing and future extension."""

from app.schemas.location import LocationProfile


class LocationService:
    """Provides location profiles for UI development."""

    @staticmethod
    def sample_profile() -> LocationProfile:
        return LocationProfile(
            id="sample-sg-001",
            name="Marina Bay",
            lat=1.2834,
            lon=103.8607,
            country="Singapore",
            region="Central Region",
            context="Sample profile for map focus and side-panel rendering.",
        )
