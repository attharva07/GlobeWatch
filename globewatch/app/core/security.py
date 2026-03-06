"""Simple security hooks and API key placeholder validation."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def optional_api_key_guard(
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate API key only when API key mode is enabled."""

    if not settings.API_KEY_ENABLED:
        return
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
