export interface Marker {
  id: string;
  type: string;
  title: string;
  lat: number;
  lon: number;
  source: string;
  timestamp: string;
  severity: string;
  metadata: Record<string, unknown>;
}

export interface MarkerListResponse {
  markers: Marker[];
  count?: number;
}
