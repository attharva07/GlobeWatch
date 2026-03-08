"""FastAPI app factory and startup lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import cameras, flights, globe, health, locations, news, weather
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


def create_app(app_settings: Settings) -> FastAPI:
    app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        debug=bool(app_settings.DEBUG and app_settings.ENVIRONMENT != "production"),
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

    async def ingestion_loop(initial_delay_seconds: int = 0) -> None:
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

    @app.on_event("startup")
    async def startup_event() -> None:
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

        if app_settings.ENVIRONMENT != "test" and app_settings.INGESTION_ENABLED and app_settings.INGESTION_PROVIDER:
            initial_delay = app_settings.INGESTION_INTERVAL_SECONDS if startup_ingestion_attempted else 0
            app.state.ingestion_task = asyncio.create_task(ingestion_loop(initial_delay_seconds=initial_delay))
        logger.info("Service ready", extra={"path": "startup", "client_ip": "-"})

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        task = getattr(app.state, "ingestion_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        logger.info("Shutting down service", extra={"path": "shutdown", "client_ip": "-"})

    app.include_router(health.router, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(news.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(globe.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(locations.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(weather.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(flights.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    app.include_router(cameras.router, prefix=app_settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
    return app


app = create_app(settings)
