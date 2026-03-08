import type { RegionEvent, RegionMarker } from '../types/marker';
import { formatTimestamp } from '../lib/cesium';

interface MarkerPanelProps {
  marker: RegionMarker | null;
  events: RegionEvent[];
}

export function MarkerPanel({ marker, events }: MarkerPanelProps) {
  if (!marker) {
    return (
      <aside className="marker-panel marker-panel-empty">
        <h2>Region details</h2>
        <p>Select a region marker to inspect aggregated events.</p>
      </aside>
    );
  }

  return (
    <aside className="marker-panel">
      <h2>Region: {marker.region_name}</h2>
      <p>Events: {marker.event_count}</p>
      {events.map((event) => (
        <div key={event.id} className="metadata-row">
          <strong>{event.title}</strong>
          <p>{event.description}</p>
          <small>
            {event.category} · {event.city}, {event.country} · {formatTimestamp(event.event_timestamp)}
          </small>
        </div>
      ))}
    </aside>
  );
}
