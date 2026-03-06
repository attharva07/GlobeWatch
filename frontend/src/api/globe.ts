import { apiGet } from './client';
import type { MarkerListResponse } from '../types/marker';

export function fetchHealth(): Promise<{ status: string }> {
  return apiGet('/health');
}

export function fetchGlobeMarkers(layers: string[]): Promise<MarkerListResponse> {
  const params = new URLSearchParams();
  if (layers.length > 0) {
    params.set('layers', layers.join(','));
  }

  const query = params.toString();
  return apiGet<MarkerListResponse>(`/api/v1/globe/markers${query ? `?${query}` : ''}`);
}
