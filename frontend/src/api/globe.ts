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
