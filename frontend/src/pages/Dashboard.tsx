import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchRegionEvents,
  fetchFlights,
  fetchShips,
  fetchCyberIOCs,
  fetchSignals,
  fetchSatellites,
  fetchConflicts,
  fetchEntityLinks,
} from '../api/globe';
import { ErrorBanner } from '../components/ErrorBanner';
import { GlobeViewer, type FlyToTarget } from '../components/GlobeViewer';
import { LayerControls } from '../components/LayerControls';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { MarkerPanel } from '../components/MarkerPanel';
import { NewsTicker } from '../components/NewsTicker';
import { StatusBadge } from '../components/StatusBadge';
import { useMarkers } from '../hooks/useMarkers';
import type {
  RegionEvent,
  RegionMarker,
  LayerState,
  LayerCounts,
  FlightTrack,
  ShipTrack,
  CyberIOC,
  SignalCoverage,
  SatelliteOrbit,
  ConflictZone,
  EntityLink,
} from '../types/marker';

const DEFAULT_LAYERS: LayerState[] = [
  { id: 'news', label: 'News Events', enabled: true, icon: '📰' },
  { id: 'flights', label: 'Flight Tracking', enabled: false, icon: '✈️' },
  { id: 'ships', label: 'Ship / AIS', enabled: false, icon: '🚢' },
  { id: 'cyber', label: 'Cyber IOCs', enabled: false, icon: '🌐' },
  { id: 'signals', label: 'Signal / RF', enabled: false, icon: '📡' },
  { id: 'satellites', label: 'Satellites', enabled: false, icon: '🛰️' },
  { id: 'conflicts', label: 'Conflicts', enabled: false, icon: '⚔️' },
  { id: 'entity_links', label: 'Entity Links', enabled: false, icon: '🔗' },
];

// Auto-refresh intervals per layer (ms)
const LAYER_REFRESH_MS: Partial<Record<string, number>> = {
  flights: 15_000,
  ships: 30_000,
  cyber: 300_000,
  satellites: 120_000,
  signals: 600_000,
  conflicts: 600_000,
  entity_links: 600_000,
};

type SeverityFilter = 'all' | 'high' | 'medium' | 'low';

function LiveClock() {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return <span>{time} UTC</span>;
}

function SeverityFilterBar({
  filter,
  onChange,
  counts,
}: {
  filter: SeverityFilter;
  onChange: (f: SeverityFilter) => void;
  counts: { high: number; medium: number; low: number };
}) {
  return (
    <div className="severity-filter-bar">
      {(['all', 'high', 'medium', 'low'] as SeverityFilter[]).map((f) => (
        <button
          key={f}
          className={`sev-filter-btn sev-filter-${f}${filter === f ? ' active' : ''}`}
          onClick={() => onChange(f)}
        >
          {f === 'all' ? 'ALL' : f.toUpperCase()}
          {f !== 'all' && <span className="sev-filter-count">{counts[f]}</span>}
        </button>
      ))}
    </div>
  );
}

export function Dashboard() {
  const [layers, setLayers] = useState<LayerState[]>(DEFAULT_LAYERS);
  const [selectedMarker, setSelectedMarker] = useState<RegionMarker | null>(null);
  const [events, setEvents] = useState<RegionEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [flyToTarget, setFlyToTarget] = useState<FlyToTarget | null>(null);
  const flyKeyRef = useRef(0);

  const [flights, setFlights] = useState<FlightTrack[]>([]);
  const [ships, setShips] = useState<ShipTrack[]>([]);
  const [cyberIOCs, setCyberIOCs] = useState<CyberIOC[]>([]);
  const [signals, setSignals] = useState<SignalCoverage[]>([]);
  const [satellites, setSatellites] = useState<SatelliteOrbit[]>([]);
  const [conflicts, setConflicts] = useState<ConflictZone[]>([]);
  const [entityLinks, setEntityLinks] = useState<EntityLink[]>([]);

  const newsEnabled = layers.find((l) => l.id === 'news')?.enabled ?? false;
  const { markers, markerCount, loading, error, refresh } = useMarkers(newsEnabled);

  const isEnabled = useCallback(
    (id: string) => layers.find((l) => l.id === id)?.enabled ?? false,
    [layers]
  );

  // Per-layer fetch functions (stable references via useCallback)
  const doFetchFlights = useCallback(() => {
    fetchFlights().then((r) => setFlights(r.flights as FlightTrack[])).catch(() => {});
  }, []);
  const doFetchShips = useCallback(() => {
    fetchShips().then((r) => setShips(r.ships as ShipTrack[])).catch(() => {});
  }, []);
  const doFetchCyber = useCallback(() => {
    fetchCyberIOCs().then((r) => setCyberIOCs(r.iocs as CyberIOC[])).catch(() => {});
  }, []);
  const doFetchSignals = useCallback(() => {
    fetchSignals().then((r) => setSignals(r.signals as SignalCoverage[])).catch(() => {});
  }, []);
  const doFetchSatellites = useCallback(() => {
    fetchSatellites().then((r) => setSatellites(r.satellites as SatelliteOrbit[])).catch(() => {});
  }, []);
  const doFetchConflicts = useCallback(() => {
    fetchConflicts().then((r) => setConflicts(r.conflicts as ConflictZone[])).catch(() => {});
  }, []);
  const doFetchEntityLinks = useCallback(() => {
    fetchEntityLinks().then((r) => setEntityLinks(r.links as EntityLink[])).catch(() => {});
  }, []);

  const layerFetchers: Record<string, () => void> = useMemo(() => ({
    flights: doFetchFlights,
    ships: doFetchShips,
    cyber: doFetchCyber,
    signals: doFetchSignals,
    satellites: doFetchSatellites,
    conflicts: doFetchConflicts,
    entity_links: doFetchEntityLinks,
  }), [doFetchFlights, doFetchShips, doFetchCyber, doFetchSignals, doFetchSatellites, doFetchConflicts, doFetchEntityLinks]);

  // Initial fetch + reset when layers are toggled
  useEffect(() => {
    if (isEnabled('flights')) { doFetchFlights(); } else { setFlights([]); }
  }, [isEnabled, doFetchFlights]);

  useEffect(() => {
    if (isEnabled('ships')) { doFetchShips(); } else { setShips([]); }
  }, [isEnabled, doFetchShips]);

  useEffect(() => {
    if (isEnabled('cyber')) { doFetchCyber(); } else { setCyberIOCs([]); }
  }, [isEnabled, doFetchCyber]);

  useEffect(() => {
    if (isEnabled('signals')) { doFetchSignals(); } else { setSignals([]); }
  }, [isEnabled, doFetchSignals]);

  useEffect(() => {
    if (isEnabled('satellites')) { doFetchSatellites(); } else { setSatellites([]); }
  }, [isEnabled, doFetchSatellites]);

  useEffect(() => {
    if (isEnabled('conflicts')) { doFetchConflicts(); } else { setConflicts([]); }
  }, [isEnabled, doFetchConflicts]);

  useEffect(() => {
    if (isEnabled('entity_links')) { doFetchEntityLinks(); } else { setEntityLinks([]); }
  }, [isEnabled, doFetchEntityLinks]);

  // Auto-refresh intervals per active layer
  useEffect(() => {
    const timers: ReturnType<typeof setInterval>[] = [];
    for (const [id, ms] of Object.entries(LAYER_REFRESH_MS)) {
      if (!isEnabled(id) || !ms) continue;
      const fn = layerFetchers[id];
      if (fn) timers.push(setInterval(fn, ms));
    }
    return () => timers.forEach(clearInterval);
  }, [isEnabled, layerFetchers]);

  // Fetch region events when a marker is selected
  useEffect(() => {
    if (!selectedMarker) {
      setEvents([]);
      setEventsError(null);
      setEventsLoading(false);
      return;
    }
    setEventsError(null);
    setEventsLoading(true);
    fetchRegionEvents(selectedMarker.region_id)
      .then((r) => setEvents(r.events))
      .catch((err: unknown) => {
        setEvents([]);
        setEventsError(err instanceof Error ? err.message : 'Failed to load region events.');
      })
      .finally(() => setEventsLoading(false));
  }, [selectedMarker]);

  const toggleLayer = useCallback((id: string) => {
    setLayers((prev) => prev.map((l) => (l.id === id ? { ...l, enabled: !l.enabled } : l)));
    if (id === 'news') setSelectedMarker(null);
  }, []);

  const handleRefresh = useCallback(() => {
    setSelectedMarker(null);
    void refresh();
  }, [refresh]);

  const handleSelectMarker = useCallback((marker: RegionMarker | null) => {
    setSelectedMarker(marker);
    if (marker) {
      flyKeyRef.current += 1;
      setFlyToTarget({ lat: marker.lat, lon: marker.lon, zoom: 5, key: flyKeyRef.current });
    }
  }, []);

  const handleBack = useCallback(() => {
    setSelectedMarker(null);
    flyKeyRef.current += 1;
    setFlyToTarget({ lat: 20, lon: 0, zoom: 1.8, key: flyKeyRef.current });
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      switch (e.key) {
        case 'Escape': handleBack(); break;
        case 'r': case 'R': handleRefresh(); break;
        case '1': toggleLayer('news'); break;
        case '2': toggleLayer('flights'); break;
        case '3': toggleLayer('ships'); break;
        case '4': toggleLayer('cyber'); break;
        case '5': toggleLayer('signals'); break;
        case '6': toggleLayer('satellites'); break;
        case '7': toggleLayer('conflicts'); break;
        case '8': toggleLayer('entity_links'); break;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [toggleLayer, handleRefresh, handleBack]);

  // Severity counts for filter bar
  const severityCounts = useMemo(() => ({
    high: markers.filter((m) => m.severity === 'high').length,
    medium: markers.filter((m) => m.severity === 'medium').length,
    low: markers.filter((m) => m.severity === 'low').length,
  }), [markers]);

  // Layer record counts for LayerControls badges
  const layerCounts: LayerCounts = useMemo(() => ({
    news: markers.length,
    flights: flights.length,
    ships: ships.length,
    cyber: cyberIOCs.length,
    signals: signals.length,
    satellites: satellites.length,
    conflicts: conflicts.length,
    entity_links: entityLinks.length,
  }), [markers, flights, ships, cyberIOCs, signals, satellites, conflicts, entityLinks]);

  return (
    <div className="dashboard-layout">
      <GlobeViewer
        markers={markers}
        selectedMarkerId={selectedMarker?.region_id ?? null}
        onSelectMarker={handleSelectMarker}
        layers={layers}
        flights={flights}
        ships={ships}
        cyberIOCs={cyberIOCs}
        signals={signals}
        satellites={satellites}
        conflicts={conflicts}
        entityLinks={entityLinks}
        flyToTarget={flyToTarget}
        severityFilter={severityFilter}
      />

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
          <StatusBadge />
          <div className="top-bar-divider" />
          <div className="top-bar-stat">
            <span className="top-bar-stat-value">{markerCount}</span>
            <span className="top-bar-stat-label">Regions</span>
          </div>
          <div className="top-bar-divider" />
          <div className="top-bar-stat">
            <span className="top-bar-stat-value">{layers.filter((l) => l.enabled).length}</span>
            <span className="top-bar-stat-label">Layers</span>
          </div>
          <div className="top-bar-divider" />
          <div className="top-bar-stat">
            <span className="top-bar-stat-value"><LiveClock /></span>
            <span className="top-bar-stat-label">Time</span>
          </div>
        </div>
      </header>

      {newsEnabled && (
        <SeverityFilterBar filter={severityFilter} onChange={setSeverityFilter} counts={severityCounts} />
      )}

      {selectedMarker && (
        <button className="back-button" onClick={handleBack} title="ESC to deselect">← Back</button>
      )}

      {loading && <LoadingOverlay />}
      {error && <ErrorBanner message={error} />}
      {eventsError && <ErrorBanner message={eventsError} />}
      {!loading && !error && newsEnabled && markers.length === 0 && (
        <div className="empty-state">No region markers returned from backend.</div>
      )}

      <LayerControls
        layers={layers}
        markerCount={markerCount}
        layerCounts={layerCounts}
        loading={loading}
        onToggleLayer={toggleLayer}
        onRefresh={handleRefresh}
      />

      <MarkerPanel marker={selectedMarker} events={events} loading={eventsLoading} />
      <NewsTicker />

      <div className="kbd-hint">
        <span>R: refresh</span>
        <span>ESC: deselect</span>
        <span>1–8: layers</span>
      </div>
    </div>
  );
}
