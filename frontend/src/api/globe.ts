import { apiGet } from './client';
import type { RegionEventsResponse, RegionMarkerListResponse } from '../types/marker';

export function fetchHealth(): Promise<{ status: string }> {
  return apiGet('/health');
}

export function fetchRegionMarkers(): Promise<RegionMarkerListResponse> {
  return apiGet<RegionMarkerListResponse>('/api/v1/globe/regions');
}

export function fetchRegionEvents(regionId: string): Promise<RegionEventsResponse> {
  return apiGet<RegionEventsResponse>(`/api/v1/globe/regions/${encodeURIComponent(regionId)}/events`);
}

export function fetchFlights(): Promise<{ flights: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/flights');
}

export function fetchShips(): Promise<{ ships: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/ships');
}

export function fetchCyberIOCs(): Promise<{ iocs: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/cyber');
}

export function fetchSignals(): Promise<{ signals: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/signals');
}

export function fetchSatellites(): Promise<{ satellites: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/satellites');
}

export function fetchConflicts(): Promise<{ conflicts: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/conflicts');
}

export function fetchEntityLinks(): Promise<{ links: unknown[]; count: number }> {
  return apiGet('/api/v1/layers/entity-links');
}
