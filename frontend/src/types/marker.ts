export interface RegionMarker {
  region_id: string;
  region_name: string;
  lat: number;
  lon: number;
  event_count: number;
  top_categories: string[];
  severity: string;
}

export interface RegionMarkerListResponse {
  regions: RegionMarker[];
  count?: number;
}

export interface RegionEvent {
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

export interface RegionEventsResponse {
  region_id: string;
  region_name: string;
  event_count: number;
  events: RegionEvent[];
}
