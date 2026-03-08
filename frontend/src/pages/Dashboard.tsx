import { useEffect, useState } from 'react';
import { fetchRegionEvents } from '../api/globe';
import { ErrorBanner } from '../components/ErrorBanner';
import { GlobeViewer } from '../components/GlobeViewer';
import { LayerControls } from '../components/LayerControls';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { MarkerPanel } from '../components/MarkerPanel';
import { useMarkers } from '../hooks/useMarkers';
import type { RegionEvent, RegionMarker } from '../types/marker';

function LiveClock() {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return <span>{time} UTC</span>;
}

export function Dashboard() {
  const [newsEnabled, setNewsEnabled] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState<RegionMarker | null>(null);
  const [events, setEvents] = useState<RegionEvent[]>([]);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const { markers, markerCount, loading, error, refresh } = useMarkers(newsEnabled);

  useEffect(() => {
    if (!selectedMarker) { setEvents([]); setEventsError(null); return; }
    setEventsError(null);
    fetchRegionEvents(selectedMarker.region_id)
      .then((response) => setEvents(response.events))
      .catch((err: unknown) => {
        setEvents([]);
        setEventsError(err instanceof Error ? err.message : 'Failed to load region events.');
      });
  }, [selectedMarker]);

  return (
    <div className="dashboard-layout">
      <GlobeViewer
        markers={markers}
        selectedMarkerId={selectedMarker?.region_id ?? null}
        onSelectMarker={setSelectedMarker}
      />

      {/* Scanline + corner decorations */}
      <div className="scanline" />
      <div className="corner-tl" />
      <div className="corner-br" />

      {/* Top bar */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="top-bar-logo">
            <div className="top-bar-logo-dot" />
            GlobeWatch
          </div>
          <span className="top-bar-tag">Live Intel</span>
        </div>
        <div className="top-bar-right">
          <div className="top-bar-stat">
            <span className="top-bar-stat-value">{markerCount}</span>
            <span className="top-bar-stat-label">Regions</span>
          </div>
          <div className="top-bar-divider" />
          <div className="top-bar-stat">
            <span className="top-bar-stat-value"><LiveClock /></span>
            <span className="top-bar-stat-label">Time</span>
          </div>
        </div>
      </header>

      {loading && <LoadingOverlay />}
      {error && <ErrorBanner message={error} />}
      {eventsError && <ErrorBanner message={eventsError} />}
      {!loading && !error && markers.length === 0 && (
        <div className="empty-state">No region markers returned from backend.</div>
      )}

      <LayerControls
        newsEnabled={newsEnabled}
        markerCount={markerCount}
        loading={loading}
        onToggleNews={() => { setSelectedMarker(null); setNewsEnabled((c) => !c); }}
        onRefresh={() => { setSelectedMarker(null); void refresh(); }}
      />

      <MarkerPanel marker={selectedMarker} events={events} />
    </div>
  );
}
