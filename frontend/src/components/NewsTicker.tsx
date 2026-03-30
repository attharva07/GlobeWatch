import { useEffect, useRef, useState } from 'react';
import { fetchNewsEvents, type NewsEvent } from '../api/globe';
import { formatTimestamp } from '../lib/colors';

const SEVERITY_LABEL: Record<string, string> = { high: 'HIGH', medium: 'MED', low: 'LOW' };

export function NewsTicker() {
  const [events, setEvents] = useState<NewsEvent[]>([]);
  const [paused, setPaused] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = () => {
      fetchNewsEvents(60)
        .then((r) => setEvents(r.events))
        .catch(() => {/* silently keep stale data */});
    };
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, []);

  // Restart animation when new events arrive
  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    el.style.animation = 'none';
    // force reflow
    void el.offsetWidth;
    el.style.animation = '';
  }, [events]);

  if (events.length === 0) return null;

  // Duplicate items so the scroll is seamless
  const items = [...events, ...events];

  return (
    <div
      className="news-ticker"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="ticker-label">LIVE</div>
      <div className="ticker-viewport">
        <div
          ref={trackRef}
          className={`ticker-track${paused ? ' ticker-paused' : ''}`}
          style={{ '--item-count': events.length } as React.CSSProperties}
        >
          {items.map((e, i) => (
            <span key={`${e.id}-${i}`} className={`ticker-item ticker-sev-${e.severity}`}>
              <span className={`ticker-badge ticker-badge-${e.severity}`}>
                {SEVERITY_LABEL[e.severity] ?? e.severity.toUpperCase()}
              </span>
              <span className="ticker-country">{e.country}</span>
              <span className="ticker-sep">—</span>
              <span className="ticker-title">{e.title}</span>
              <span className="ticker-sep">—</span>
              <span className="ticker-time">{formatTimestamp(e.event_timestamp)}</span>
              <span className="ticker-divider">|</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
