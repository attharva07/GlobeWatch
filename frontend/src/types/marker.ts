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

export interface FlightTrack {
  id: string;
  callsign: string;
  origin: [number, number];
  destination: [number, number];
  current_position: [number, number, number];
  heading: number;
  speed: number;
  altitude: number;
  aircraft_type: string;
  timestamp: string;
  origin_country?: string;
}

export interface ShipTrack {
  id: string;
  name: string;
  mmsi: string;
  position: [number, number];
  path: [number, number][];
  speed: number;
  heading: number;
  ship_type: string;
  destination: string;
  timestamp: string;
  flag?: string;
  imo?: string;
}

export interface CyberIOC {
  id: string;
  ip: string;
  lat: number;
  lon: number;
  threat_type: string;
  severity: string;
  country: string;
  isp: string;
  count: number;
  first_seen: string;
  last_seen: string;
}

export interface SignalCoverage {
  lat: number;
  lon: number;
  intensity: number;
  frequency: number;
  signal_type: string;
}

export interface SatelliteOrbit {
  id: string;
  name: string;
  norad_id: number;
  path: [number, number, number][];
  current_position: [number, number, number];
  orbit_type: string;
  timestamp: string;
  tle_line1?: string;
  tle_line2?: string;
}

export interface ConflictZone {
  id: string;
  name: string;
  geometry: GeoJSON.Feature;
  severity: string;
  event_count: number;
  description: string;
  events: { lat: number; lon: number; type: string; date: string }[];
}

export interface EntityLink {
  id: string;
  source_name: string;
  target_name: string;
  source_position: [number, number];
  target_position: [number, number];
  relationship: string;
  strength: number;
  source_events?: number;
  target_events?: number;
}

export interface LayerCounts {
  news: number;
  flights: number;
  ships: number;
  cyber: number;
  signals: number;
  satellites: number;
  conflicts: number;
  entity_links: number;
}

export type LayerType =
  | 'news'
  | 'flights'
  | 'ships'
  | 'cyber'
  | 'signals'
  | 'satellites'
  | 'conflicts'
  | 'entity_links';

export interface LayerState {
  id: LayerType;
  label: string;
  enabled: boolean;
  icon: string;
}
