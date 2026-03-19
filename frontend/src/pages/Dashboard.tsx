import { useCallback, useEffect, useState } from 'react';
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
import { GlobeViewer } from '../components/GlobeViewer';
import { LayerControls } from '../components/LayerControls';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { MarkerPanel } from '../components/MarkerPanel';
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

function LiveClock() {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return <span>{time} UTC</span>;
}

export function Dashboard() {
  const [layers, setLayers] = useState<LayerState[]>(DEFAULT_LAYERS);
  const [selectedMarker, setSelectedMarker] = useState<RegionMarker | null>(null);
  const [events, setEvents] = useState<RegionEvent[]>([]);
  const [eventsError, setEventsError] = useState<string | null>(null);

  const [flights, setFlights] = useState<FlightTrack[]>([]);
  const [ships, setShips] = useState<ShipTrack[]>([]);
  const [cyberIOCs, setCyberIOCs] = useState<CyberIOC[]>([]);
  const [signals, setSignals] = useState<SignalCoverage[]>([]);
  const [satellites, setSatellites] = useState<SatelliteOrbit[]>([]);
  const [conflicts, setConflicts] = useState<ConflictZone[]>([]);
  const [entityLinks, setEntityLinks] = useState<EntityLink[]>([]);

  const newsEnabled = layers.find((l) => l.id === 'news')?.enabled ?? false;
  const { markers, markerCount, loading, error, refresh } = useMarkers(newsEnabled);

  // Fetch layer data when enabled
  const isEnabled = useCallback(
    (id: string) => layers.find((l) => l.id === id)?.enabled ?? false,
    [layers]
  );

  useEffect(() => {
    if (isEnabled('flights')) {
      fetchFlights()
        .then((r) => setFlights(r.flights as FlightTrack[]))
        .catch(() => setFlights([]));
    } else {
      setFlights([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('ships')) {
      fetchShips()
        .then((r) => setShips(r.ships as ShipTrack[]))
        .catch(() => setShips([]));
    } else {
      setShips([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('cyber')) {
      fetchCyberIOCs()
        .then((r) => setCyberIOCs(r.iocs as CyberIOC[]))
        .catch(() => setCyberIOCs([]));
    } else {
      setCyberIOCs([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('signals')) {
      fetchSignals()
        .then((r) => setSignals(r.signals as SignalCoverage[]))
        .catch(() => setSignals([]));
    } else {
      setSignals([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('satellites')) {
      fetchSatellites()
        .then((r) => setSatellites(r.satellites as SatelliteOrbit[]))
        .catch(() => setSatellites([]));
    } else {
      setSatellites([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('conflicts')) {
      fetchConflicts()
        .then((r) => setConflicts(r.conflicts as ConflictZone[]))
        .catch(() => setConflicts([]));
    } else {
      setConflicts([]);
    }
  }, [isEnabled]);

  useEffect(() => {
    if (isEnabled('entity_links')) {
      fetchEntityLinks()
        .then((r) => setEntityLinks(r.links as EntityLink[]))
        .catch(() => setEntityLinks([]));
    } else {
      setEntityLinks([]);
    }
  }, [isEnabled]);

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

  return (
    <div className="dashboard-layout">
      <GlobeViewer
        markers={markers}
        selectedMarkerId={selectedMarker?.region_id ?? null}
        onSelectMarker={setSelectedMarker}
        layers={layers}
        flights={flights}
        ships={ships}
        cyberIOCs={cyberIOCs}
        signals={signals}
        satellites={satellites}
        conflicts={conflicts}
        entityLinks={entityLinks}
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

      <MarkerPanel marker={selectedMarker} events={events} />
    </div>
  );
}
