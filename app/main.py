"""FastAPI app factory and startup lifecycle."""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import cameras, flights, globe, health, locations, news, weather
from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.logging import setup_logging
from app.core.security import optional_api_key_guard
from app.db.base import Base
from app.db.session import engine
from app.services.news_service import NewsService
# Ensure ORM models are registered with SQLAlchemy metadata.
from app.models import event as _event_model  # noqa: F401

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Avoid exposing internals while retaining useful validation details."""

    return JSONResponse(status_code=422, content={"detail": exc.errors(), "message": "Request validation failed"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Generic error handler for controlled error responses."""

    logger.exception("Unhandled error: %s", exc.__class__.__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def startup_event() -> None:
    """Initialize database and seed baseline data."""

    Base.metadata.create_all(bind=engine)
    db = next(get_db_session())
    try:
        NewsService(db).seed_if_empty()
    finally:
        db.close()


app.include_router(health.router, dependencies=[Depends(optional_api_key_guard)])
app.include_router(news.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
app.include_router(globe.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
app.include_router(locations.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
app.include_router(weather.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
app.include_router(flights.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
app.include_router(cameras.router, prefix=settings.API_PREFIX, dependencies=[Depends(optional_api_key_guard)])
