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
          {f !== 'all' && (
            <span className="sev-filter-count">{counts[f]}</span>
          )}
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

  // Severity counts for filter bar
  const severityCounts = useMemo(
    () => ({
      high: markers.filter((m) => m.severity === 'high').length,
      medium: markers.filter((m) => m.severity === 'medium').length,
      low: markers.filter((m) => m.severity === 'low').length,
    }),
    [markers]
  );

  // Fetch layer data when enabled
  useEffect(() => {
    if (isEnabled('flights')) {
      fetchFlights().then((r) => setFlights(r.flights as FlightTrack[])).catch(() => setFlights([]));
    } else {
      setFlights([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('ships')) {
      fetchShips().then((r) => setShips(r.ships as ShipTrack[])).catch(() => setShips([]));
    } else {
      setShips([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('cyber')) {
      fetchCyberIOCs().then((r) => setCyberIOCs(r.iocs as CyberIOC[])).catch(() => setCyberIOCs([]));
    } else {
      setCyberIOCs([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('signals')) {
      fetchSignals().then((r) => setSignals(r.signals as SignalCoverage[])).catch(() => setSignals([]));
    } else {
      setSignals([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('satellites')) {
      fetchSatellites().then((r) => setSatellites(r.satellites as SatelliteOrbit[])).catch(() => setSatellites([]));
    } else {
      setSatellites([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('conflicts')) {
      fetchConflicts().then((r) => setConflicts(r.conflicts as ConflictZone[])).catch(() => setConflicts([]));
    } else {
      setConflicts([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('entity_links')) {
      fetchEntityLinks().then((r) => setEntityLinks(r.links as EntityLink[])).catch(() => setEntityLinks([]));
    } else {
      setEntityLinks([]);
    }
  }, [isEnabled]);

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
      .then((response) => {
        setEvents(response.events);
      })
      .catch((err: unknown) => {
        setEvents([]);
        setEventsError(err instanceof Error ? err.message : 'Failed to load region events.');
      })
      .finally(() => setEventsLoading(false));
  }, [selectedMarker]);

  const toggleLayer = useCallback((id: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, enabled: !l.enabled } : l))
    );
    if (id === 'news') {
      setSelectedMarker(null);
    }
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
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      switch (e.key) {
        case 'Escape':
          handleBack();
          break;
        case 'r':
        case 'R':
          handleRefresh();
          break;
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

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleLayer, handleRefresh, handleBack]);

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

      {/* Decorative overlays */}
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

      {/* Severity filter bar */}
      {newsEnabled && (
        <SeverityFilterBar
          filter={severityFilter}
          onChange={setSeverityFilter}
          counts={severityCounts}
        />
      )}

      {/* Back button when region is selected */}
      {selectedMarker && (
        <button className="back-button" onClick={handleBack} title="ESC to deselect">
          ← Back
        </button>
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
        loading={loading}
        onToggleLayer={toggleLayer}
        onRefresh={handleRefresh}
      />

      <MarkerPanel marker={selectedMarker} events={events} loading={eventsLoading} />

      <NewsTicker />

      {/* Keyboard shortcut hint */}
      <div className="kbd-hint">
        <span>R: refresh</span>
        <span>ESC: deselect</span>
        <span>1–8: layers</span>
      </div>
    </div>
  );
}
