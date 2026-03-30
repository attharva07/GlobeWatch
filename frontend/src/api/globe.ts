import { apiGet, apiPost } from './client';
import type { RegionEventsResponse, RegionMarkerListResponse } from '../types/marker';

export interface NewsStatus {
  service: string;
  ready: boolean;
  event_count: number;
  mock_seed_enabled: boolean;
  detail?: string;
}

export interface NewsEvent {
  id: number;
  title: string;
  description: string;
  category: string;
  source: string;
  event_timestamp: string;
  country: string;
  city: string;
  severity: string;
}

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

export function fetchNewsStatus(): Promise<NewsStatus> {
  return apiGet<NewsStatus>('/api/v1/news/status');
}

export function fetchNewsEvents(limit = 50): Promise<{ events: NewsEvent[]; count: number }> {
  return apiGet<{ events: NewsEvent[]; count: number }>(`/api/v1/news/events?limit=${limit}`);
}

export function triggerIngest(): Promise<{ created: number; updated: number; provider: string; data_mode: string }> {
  return apiPost('/api/v1/news/ingest');
}
