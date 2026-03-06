"""Shared API schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health payload for service probes."""

    status: str
    app_name: str
    environment: str
    version: str


class ServiceStatusResponse(BaseModel):
    """Standard status response for service layer availability."""

    service: str
    ready: bool
    detail: str
