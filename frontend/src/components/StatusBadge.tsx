import { useEffect, useRef, useState } from 'react';
import { fetchNewsStatus, triggerIngest, type NewsStatus } from '../api/globe';

export function StatusBadge() {
  const [status, setStatus] = useState<NewsStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [delta, setDelta] = useState<number>(0);
  const prevCountRef = useRef<number | null>(null);
  const deltaTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = () => {
    fetchNewsStatus()
      .then((s) => {
        setStatus(s);
        if (prevCountRef.current !== null && s.event_count > prevCountRef.current) {
          const diff = s.event_count - prevCountRef.current;
          setDelta(diff);
          if (deltaTimerRef.current) clearTimeout(deltaTimerRef.current);
          deltaTimerRef.current = setTimeout(() => setDelta(0), 4000);
        }
        prevCountRef.current = s.event_count;
      })
      .catch(() => {/* silently ignore */});
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => {
      clearInterval(id);
      if (deltaTimerRef.current) clearTimeout(deltaTimerRef.current);
    };
  }, []);

  const handleManualIngest = () => {
    setSyncing(true);
    triggerIngest()
      .then(() => load())
      .catch(() => {/* ignore */})
      .finally(() => setSyncing(false));
  };

  if (!status) return null;

  const badgeClass = syncing
    ? 'status-badge status-syncing'
    : status.mock_seed_enabled
      ? 'status-badge status-demo'
      : 'status-badge status-live';

  const label = syncing ? 'SYNCING' : status.mock_seed_enabled ? 'DEMO' : 'LIVE';

  return (
    <div className="status-badge-group">
      {status.mock_seed_enabled && (
        <span className="status-demo-warn">DEMO MODE</span>
      )}
      <button
        className={badgeClass}
        onClick={handleManualIngest}
        disabled={syncing}
        title="Click to trigger manual ingestion"
      >
        <span className="status-dot" />
        {label}
      </button>
      <span className="status-event-count">
        {status.event_count.toLocaleString()}
        {delta > 0 && (
          <span className="status-delta">+{delta}</span>
        )}
        <span className="status-event-label">events</span>
      </span>
    </div>
  );
}
