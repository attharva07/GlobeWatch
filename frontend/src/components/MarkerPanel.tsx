import type { Marker } from '../types/marker';
import { formatTimestamp } from '../lib/cesium';

interface MarkerPanelProps {
  marker: Marker | null;
}

function metadataValue(value: unknown): string {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (value === null || value === undefined) {
    return '—';
  }

  return JSON.stringify(value);
}

export function MarkerPanel({ marker }: MarkerPanelProps) {
  if (!marker) {
    return (
      <aside className="marker-panel marker-panel-empty">
        <h2>Event details</h2>
        <p>Select a marker to inspect world-event details.</p>
      </aside>
    );
  }

  const metadataKeys = ['category', 'country', 'city', 'description'];

  return (
    <aside className="marker-panel">
      <h2>{marker.title}</h2>
      <dl>
        <dt>Type</dt>
        <dd>{marker.type}</dd>

        <dt>Severity</dt>
        <dd>{marker.severity}</dd>

        <dt>Source</dt>
        <dd>{marker.source}</dd>

        <dt>Timestamp</dt>
        <dd>{formatTimestamp(marker.timestamp)}</dd>
      </dl>

      <h3>Metadata</h3>
      <dl>
        {metadataKeys.map((key) => (
          <div key={key} className="metadata-row">
            <dt>{key}</dt>
            <dd>{metadataValue(marker.metadata?.[key])}</dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}
