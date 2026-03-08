import { useEffect, useState } from 'react';
import { fetchRegionEvents } from '../api/globe';
import { ErrorBanner } from '../components/ErrorBanner';
import { GlobeViewer } from '../components/GlobeViewer';
import { LayerControls } from '../components/LayerControls';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { MarkerPanel } from '../components/MarkerPanel';
import { useMarkers } from '../hooks/useMarkers';
import type { RegionEvent, RegionMarker } from '../types/marker';

export function Dashboard() {
  const [newsEnabled, setNewsEnabled] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState<RegionMarker | null>(null);
  const [events, setEvents] = useState<RegionEvent[]>([]);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const { markers, markerCount, loading, error, refresh } = useMarkers(newsEnabled);

  useEffect(() => {
    if (!selectedMarker) {
      setEvents([]);
      setEventsError(null);
      return;
    }
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
      <GlobeViewer markers={markers} selectedMarkerId={selectedMarker?.region_id ?? null} onSelectMarker={setSelectedMarker} />
      {loading && <LoadingOverlay />}
      {error && <ErrorBanner message={error} />}
      {eventsError && <ErrorBanner message={eventsError} />}

      {!loading && !error && markers.length === 0 && <div className="empty-state">No region markers returned from backend.</div>}

      <LayerControls
        newsEnabled={newsEnabled}
        markerCount={markerCount}
        loading={loading}
        onToggleNews={() => {
          setSelectedMarker(null);
          setNewsEnabled((current) => !current);
        }}
        onRefresh={() => {
          setSelectedMarker(null);
          void refresh();
        }}
      />

      <MarkerPanel marker={selectedMarker} events={events} />
    </div>
  );
}
