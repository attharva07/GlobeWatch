import type { RegionEvent, RegionMarker } from '../types/marker';
import { formatTimestamp } from '../lib/colors';

interface MarkerPanelProps {
  marker: RegionMarker | null;
  events: RegionEvent[];
}

function CategoryPill({ category }: { category: string }) {
  const labels: Record<string, string> = {
    weather_alert: 'Weather',
    public_health: 'Health',
    civic: 'Civic',
    world_event: 'World',
  };
  return (
    <span className={`event-category-pill ${category}`}>
      {labels[category] ?? category}
    </span>
  );
}

export function MarkerPanel({ marker, events }: MarkerPanelProps) {
  if (!marker) {
    return (
      <aside className="marker-panel">
        <div className="panel-header">
          <div className="panel-header-icon" />
          <span className="panel-header-label">Intelligence Feed</span>
        </div>
        <div className="marker-panel-empty">
          <div className="empty-globe-icon">🌐</div>
          <div className="empty-title">No Region Selected</div>
          <div className="empty-sub">Click any marker on the globe to inspect aggregated event intelligence for that region.</div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="marker-panel">
      <div className="marker-panel-header">
        <div className="region-name">{marker.region_name}</div>
        <div className="region-meta">
          <span className={`region-badge ${marker.severity}`}>{marker.severity}</span>
          <span className="region-event-count">{marker.event_count} events</span>
        </div>
        {marker.top_categories.length > 0 && (
          <div className="region-categories">
            {marker.top_categories.map((cat) => (
              <span key={cat} className="category-chip">{cat.replace('_', ' ')}</span>
            ))}
          </div>
        )}
      </div>

      <div className="marker-panel-events">
        {events.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: '11px', padding: '12px 0', textAlign: 'center' }}>
            Loading events...
          </div>
        )}
        {events.map((event) => (
          <div key={event.id} className="event-card">
            <div className="event-card-top">
              <div className="event-title">{event.title}</div>
              <CategoryPill category={event.category} />
            </div>
            <div className="event-meta">
              <span className="event-source">{event.source}</span>
              <span className="event-meta-sep" />
              <span className="event-time">{formatTimestamp(event.event_timestamp)}</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
