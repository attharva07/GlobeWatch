import { useMemo, useState } from 'react';
import { ErrorBanner } from '../components/ErrorBanner';
import { GlobeViewer } from '../components/GlobeViewer';
import { LayerControls } from '../components/LayerControls';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { MarkerPanel } from '../components/MarkerPanel';
import { useMarkers } from '../hooks/useMarkers';
import type { Marker } from '../types/marker';

const NEWS_LAYER = 'news';

export function Dashboard() {
  const [newsEnabled, setNewsEnabled] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState<Marker | null>(null);

  const selectedLayers = useMemo(() => (newsEnabled ? [NEWS_LAYER] : []), [newsEnabled]);
  const { markers, markerCount, loading, error, refresh } = useMarkers(selectedLayers);

  return (
    <div className="dashboard-layout">
      <GlobeViewer
        markers={markers}
        selectedMarkerId={selectedMarker?.id ?? null}
        onSelectMarker={setSelectedMarker}
      />

      {loading && <LoadingOverlay />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && markers.length === 0 && (
        <div className="empty-state">No markers returned from backend for the active layers.</div>
      )}

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

      <MarkerPanel marker={selectedMarker} />
    </div>
  );
}
