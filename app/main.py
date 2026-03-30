"""FastAPI app factory and startup lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import cameras, flights, globe, health, layers, locations, news, status, weather
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.logging import setup_logging
from app.core.security import optional_api_key_guard
from app.db.base import Base
from app.db.session import engine
from app.services.event_ingestion_service import EventIngestionService
from app.services.news_service import NewsService
from app.models import event as _event_model  # noqa: F401

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)


async def ingestion_loop(app_settings: Settings, initial_delay_seconds: int = 0) -> None:
    """Periodic background task that ingests events from the configured provider."""
    if initial_delay_seconds > 0:
        await asyncio.sleep(initial_delay_seconds)

    while True:
        db = next(get_db_session())
        try:
            EventIngestionService(db, app_settings).ingest()
        except Exception:
            logger.exception("Ingestion cycle failed")
        finally:
            db.close()
        await asyncio.sleep(app_settings.INGESTION_INTERVAL_SECONDS)


async def _provider_loop(name: str, coro_fn: Any, interval: float) -> None:
    """Generic background loop for live-data providers."""
    while True:
        try:
            await coro_fn()
        except Exception:
            logger.exception("Provider loop '%s' failed", name)
        await asyncio.sleep(interval)


def create_app(app_settings: Settings) -> FastAPI:
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Starting service", extra={"path": "startup", "client_ip": "-"})
        Base.metadata.create_all(bind=engine)
        startup_ingestion_attempted = False
        db = next(get_db_session())
        try:
            news_service = NewsService(db, app_settings)
            news_service.seed_if_empty()
            if (
                app_settings.ENVIRONMENT != "test"
                and app_settings.INGESTION_ENABLED
                and app_settings.INGESTION_PROVIDER
                and app_settings.INGESTION_STARTUP_RUN
            ):
                startup_ingestion_attempted = True
                try:
                    EventIngestionService(db, app_settings).ingest()
                except Exception:
                    logger.exception("Startup ingestion cycle failed")
        finally:
            db.close()

        ingestion_task: asyncio.Task[None] | None = None
        provider_tasks: list[asyncio.Task[None]] = []

        if app_settings.ENVIRONMENT != "test" and app_settings.INGESTION_ENABLED and app_settings.INGESTION_PROVIDER:
            initial_delay = app_settings.INGESTION_INTERVAL_SECONDS if startup_ingestion_attempted else 0
            ingestion_task = asyncio.create_task(ingestion_loop(app_settings, initial_delay_seconds=initial_delay))

        if app_settings.ENVIRONMENT != "test":
            from app.services.providers import (
                opensky_provider,
                satellite_provider,
                satnogs_provider,
                threat_intel_provider,
                ucdp_provider,
            )
            from app.services.layer_data_service import LayerDataService
            from app.services.layer_cache import set_cache

            # Populate caches immediately with demo data so first requests are fast
            set_cache("flights", LayerDataService.get_flights(), source="demo")
            set_cache("ships", LayerDataService.get_ships(), source="demo")
            set_cache("cyber", LayerDataService.get_cyber_iocs(), source="demo")
            set_cache("signals", LayerDataService.get_signals(), source="demo")
            set_cache("satellites", LayerDataService.get_satellites(), source="demo")
            set_cache("conflicts", LayerDataService.get_conflicts(), source="demo")

            # Start live provider refresh loops
            if app_settings.OPENSKY_ENABLED:
                provider_tasks.append(asyncio.create_task(
                    _provider_loop(
                        "opensky",
                        lambda: opensky_provider.refresh_flights(
                            username=app_settings.OPENSKY_USERNAME,
                            password=app_settings.OPENSKY_PASSWORD,
                        ),
                        15.0,
                    )
                ))
            if app_settings.CELESTRAK_ENABLED:
                provider_tasks.append(asyncio.create_task(
                    _provider_loop("satellites", satellite_provider.refresh_satellites, 300.0)
                ))
                provider_tasks.append(asyncio.create_task(
                    _provider_loop("satnogs", satnogs_provider.refresh_signals, 600.0)
                ))
            if app_settings.THREAT_INTEL_ENABLED:
                provider_tasks.append(asyncio.create_task(
                    _provider_loop("threat_intel", threat_intel_provider.refresh_cyber_iocs, 300.0)
                ))
            # UCDP conflicts refresh hourly
            provider_tasks.append(asyncio.create_task(
                _provider_loop("ucdp", ucdp_provider.refresh_conflicts, 3600.0)
            ))

        logger.info("Service ready", extra={"path": "startup", "client_ip": "-"})
        yield

        if ingestion_task:
            ingestion_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ingestion_task
        for task in provider_tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        logger.info("Shutting down service", extra={"path": "shutdown", "client_ip": "-"})

    app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        debug=bool(app_settings.DEBUG and app_settings.ENVIRONMENT != "production"),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", app_settings.API_KEY_HEADER_NAME],
    )

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Apply no-store only to API data endpoints, not to health/static routes
        # that benefit from proxy/CDN caching.
        if request.url.path.startswith(app_settings.API_PREFIX):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors(), "message": "Request validation failed"})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", extra={"path": request.url.path})
        content = {"detail": "Internal server error"}
        if app_settings.DEBUG and app_settings.ENVIRONMENT != "production":
            content["error_type"] = exc.__class__.__name__
        return JSONResponse(status_code=500, content=content)

    app.include_router(health.router, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(news.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(globe.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(locations.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(weather.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(flights.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(cameras.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(layers.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(status.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    return app


app = create_app(settings)
