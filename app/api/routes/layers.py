"""Routes for additional geospatial data layers."""

from fastapi import APIRouter, Depends

from app.core.security import rate_limit_guard
from app.schemas.layers import (
    ConflictListResponse,
    CyberIOCListResponse,
    EntityLinkListResponse,
    FlightListResponse,
    SatelliteListResponse,
    ShipListResponse,
    SignalListResponse,
)
from app.services.layer_data_service import LayerDataService

router = APIRouter(prefix="/layers", tags=["layers"])


@router.get("/flights", response_model=FlightListResponse, dependencies=[Depends(rate_limit_guard)])
def list_flights() -> FlightListResponse:
    data = LayerDataService.get_flights()
    return FlightListResponse(flights=data, count=len(data))


@router.get("/ships", response_model=ShipListResponse, dependencies=[Depends(rate_limit_guard)])
def list_ships() -> ShipListResponse:
    data = LayerDataService.get_ships()
    return ShipListResponse(ships=data, count=len(data))


@router.get("/cyber", response_model=CyberIOCListResponse, dependencies=[Depends(rate_limit_guard)])
def list_cyber_iocs() -> CyberIOCListResponse:
    data = LayerDataService.get_cyber_iocs()
    return CyberIOCListResponse(iocs=data, count=len(data))


@router.get("/signals", response_model=SignalListResponse, dependencies=[Depends(rate_limit_guard)])
def list_signals() -> SignalListResponse:
    data = LayerDataService.get_signals()
    return SignalListResponse(signals=data, count=len(data))


@router.get("/satellites", response_model=SatelliteListResponse, dependencies=[Depends(rate_limit_guard)])
def list_satellites() -> SatelliteListResponse:
    data = LayerDataService.get_satellites()
    return SatelliteListResponse(satellites=data, count=len(data))


@router.get("/conflicts", response_model=ConflictListResponse, dependencies=[Depends(rate_limit_guard)])
def list_conflicts() -> ConflictListResponse:
    data = LayerDataService.get_conflicts()
    return ConflictListResponse(conflicts=data, count=len(data))


@router.get("/entity-links", response_model=EntityLinkListResponse, dependencies=[Depends(rate_limit_guard)])
def list_entity_links() -> EntityLinkListResponse:
    data = LayerDataService.get_entity_links()
    return EntityLinkListResponse(links=data, count=len(data))
