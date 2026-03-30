"""Routes for additional geospatial data layers.

Each endpoint reads from the in-memory live cache populated by background
provider tasks.  When the cache is empty (startup, test environment, or
provider failure) it falls back to the demo data from LayerDataService so
the frontend always receives a valid, shaped response.
"""

from __future__ import annotations

import hashlib
import math

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import rate_limit_guard
from app.repositories.event_repository import EventRepository
from app.schemas.layers import (
    ConflictListResponse,
    CyberIOCListResponse,
    EntityLinkListResponse,
    FlightListResponse,
    SatelliteListResponse,
    ShipListResponse,
    SignalListResponse,
)
from app.services.layer_cache import get_cache
from app.services.layer_data_service import LayerDataService

router = APIRouter(prefix="/layers", tags=["layers"])


def _cached_or_demo(key: str, demo_fn) -> list[dict]:  # type: ignore[type-arg]
    return get_cache(key) or demo_fn()


@router.get("/flights", response_model=FlightListResponse, dependencies=[Depends(rate_limit_guard)])
def list_flights() -> FlightListResponse:
    data = _cached_or_demo("flights", LayerDataService.get_flights)
    return FlightListResponse(flights=data, count=len(data))


@router.get("/ships", response_model=ShipListResponse, dependencies=[Depends(rate_limit_guard)])
def list_ships() -> ShipListResponse:
    data = _cached_or_demo("ships", LayerDataService.get_ships)
    return ShipListResponse(ships=data, count=len(data))


@router.get("/cyber", response_model=CyberIOCListResponse, dependencies=[Depends(rate_limit_guard)])
def list_cyber_iocs() -> CyberIOCListResponse:
    data = _cached_or_demo("cyber", LayerDataService.get_cyber_iocs)
    return CyberIOCListResponse(iocs=data, count=len(data))


@router.get("/signals", response_model=SignalListResponse, dependencies=[Depends(rate_limit_guard)])
def list_signals() -> SignalListResponse:
    data = _cached_or_demo("signals", LayerDataService.get_signals)
    return SignalListResponse(signals=data, count=len(data))


@router.get("/satellites", response_model=SatelliteListResponse, dependencies=[Depends(rate_limit_guard)])
def list_satellites() -> SatelliteListResponse:
    data = _cached_or_demo("satellites", LayerDataService.get_satellites)
    return SatelliteListResponse(satellites=data, count=len(data))


@router.get("/conflicts", response_model=ConflictListResponse, dependencies=[Depends(rate_limit_guard)])
def list_conflicts() -> ConflictListResponse:
    data = _cached_or_demo("conflicts", LayerDataService.get_conflicts)
    return ConflictListResponse(conflicts=data, count=len(data))


@router.get("/entity-links", response_model=EntityLinkListResponse, dependencies=[Depends(rate_limit_guard)])
def list_entity_links(db: Session = Depends(get_db_session)) -> EntityLinkListResponse:
    """Generate entity links dynamically from co-occurring events in the database."""
    data = _build_entity_links_from_db(db)
    if not data:
        data = LayerDataService.get_entity_links()
    return EntityLinkListResponse(links=data, count=len(data))


# ── Entity link generation from DB ────────────────────────────────────────────

_CATEGORY_LABELS: dict[str, str] = {
    "weather_alert": "Climate Crisis",
    "public_health": "Health Emergency",
    "civic": "Political Event",
    "world_event": "World Affairs",
}

_MIN_EVENTS = 3
_MAX_LINKS = 30


def _link_id(src: str, tgt: str) -> str:
    h = hashlib.md5(f"{src}:{tgt}".encode()).hexdigest()[:8]
    return f"el-{h}"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_entity_links_from_db(db: Session) -> list[dict]:
    aggregates = EventRepository(db).country_aggregates(limit=25)
    if len(aggregates) < 2:
        return []

    # Index by country
    by_country = {a.country: a for a in aggregates}
    countries = list(aggregates)
    max_count = max(a.event_count for a in countries)

    links: list[dict] = []
    seen_pairs: set[frozenset] = set()

    for i, src in enumerate(countries):
        for tgt in countries[i + 1 :]:
            pair = frozenset([src.country, tgt.country])
            if pair in seen_pairs:
                continue
            # Only link countries that share a dominant category
            if src.top_category != tgt.top_category:
                continue
            seen_pairs.add(pair)
            strength = math.sqrt(src.event_count * tgt.event_count) / max_count
            relationship = _CATEGORY_LABELS.get(src.top_category, "Shared Events")
            links.append({
                "id": _link_id(src.country, tgt.country),
                "source_name": src.country,
                "target_name": tgt.country,
                "source_position": [round(src.lon, 4), round(src.lat, 4)],
                "target_position": [round(tgt.lon, 4), round(tgt.lat, 4)],
                "relationship": relationship,
                "strength": round(min(1.0, strength), 3),
                "source_events": src.event_count,
                "target_events": tgt.event_count,
            })
            if len(links) >= _MAX_LINKS:
                break
        if len(links) >= _MAX_LINKS:
            break

    # Sort by strength descending
    return sorted(links, key=lambda x: -x["strength"])
