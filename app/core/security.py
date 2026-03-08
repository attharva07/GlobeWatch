"""Security hooks for API key validation and request throttling."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Lightweight in-memory fixed-window limiter keyed by endpoint and IP.

    WARNING: This limiter is process-local. In multi-worker deployments
    (e.g. uvicorn --workers N) each worker maintains its own counter, so the
    effective limit is RATE_LIMIT_PER_MINUTE × num_workers.  For production
    deployments with multiple workers, replace this with a shared backend such
    as Redis (e.g. slowapi + redis).
    """

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.time()
        timestamps = self._requests[key]
        while timestamps and now - timestamps[0] > window_seconds:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return False
        timestamps.append(now)
        return True


rate_limiter = InMemoryRateLimiter()


def optional_api_key_guard(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate API key only when API key mode is enabled."""

    if not settings.API_KEY_ENABLED:
        return

    api_key = request.headers.get(settings.API_KEY_HEADER_NAME)
    if not api_key or api_key not in settings.API_KEYS:
        logger.warning("Rejected request with invalid API key", extra={"path": str(request.url.path)})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def rate_limit_guard(
    request: Request,
    x_forwarded_for: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Apply per-IP rate limits for selected endpoints."""

    if not settings.RATE_LIMIT_ENABLED:
        return

    forwarded_ip = (x_forwarded_for or "").split(",")[0].strip()
    client_ip = forwarded_ip or (request.client.host if request.client else "unknown")
    key = f"{request.url.path}:{client_ip}"
    if not rate_limiter.is_allowed(key=key, limit=settings.RATE_LIMIT_PER_MINUTE):
        logger.warning("Rate limit exceeded", extra={"path": str(request.url.path), "client_ip": client_ip})
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
