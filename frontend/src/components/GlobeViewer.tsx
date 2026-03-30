import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Deck, MapView, FlyToInterpolator } from '@deck.gl/core';
import { ScatterplotLayer, ArcLayer, PathLayer, IconLayer, GeoJsonLayer, TextLayer } from '@deck.gl/layers';
import { HeatmapLayer, HexagonLayer } from '@deck.gl/aggregation-layers';
import { TripsLayer } from '@deck.gl/geo-layers';
import type {
  RegionMarker,
  FlightTrack,
  ShipTrack,
  CyberIOC,
  SignalCoverage,
  SatelliteOrbit,
  ConflictZone,
  EntityLink,
  LayerState,
} from '../types/marker';
import { severityColor, LAYER_COLORS } from '../lib/colors';

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.8,
  pitch: 30,
  bearing: 0,
};

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

export interface FlyToTarget {
  lat: number;
  lon: number;
  zoom: number;
  key: number;
}

interface GlobeViewerProps {
  markers: RegionMarker[];
  selectedMarkerId: string | null;
  onSelectMarker: (marker: RegionMarker | null) => void;
  layers: LayerState[];
  flights: FlightTrack[];
  ships: ShipTrack[];
  cyberIOCs: CyberIOC[];
  signals: SignalCoverage[];
  satellites: SatelliteOrbit[];
  conflicts: ConflictZone[];
  entityLinks: EntityLink[];
  flyToTarget: FlyToTarget | null;
  severityFilter: 'all' | 'high' | 'medium' | 'low';
}

// Grid-based geographic clustering at low zoom levels
type ClusterMarker = RegionMarker & { _clusterCount?: number };

function clusterMarkers(markers: RegionMarker[], zoom: number): ClusterMarker[] {
  if (zoom >= 2) return markers;

  const gridSize = zoom < 1 ? 55 : 35;
  const cells = new Map<string, RegionMarker[]>();

  for (const m of markers) {
    const cx = Math.floor((m.lon + 180) / gridSize);
    const cy = Math.floor((m.lat + 90) / gridSize);
    const key = `${cx},${cy}`;
    const cell = cells.get(key) ?? [];
    cell.push(m);
    cells.set(key, cell);
  }

  return Array.from(cells.values()).flatMap((cell) => {
    if (cell.length === 1) return cell;
    const lat = cell.reduce((s, m) => s + m.lat, 0) / cell.length;
    const lon = cell.reduce((s, m) => s + m.lon, 0) / cell.length;
    const totalCount = cell.reduce((s, m) => s + m.event_count, 0);
    const severity = cell.some((m) => m.severity === 'high')
      ? 'high'
      : cell.some((m) => m.severity === 'medium')
        ? 'medium'
        : 'low';
    const allCats = cell.flatMap((m) => m.top_categories);
    const catMap = new Map<string, number>();
    for (const c of allCats) catMap.set(c, (catMap.get(c) ?? 0) + 1);
    const top3 = [...catMap.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([c]) => c);
    const cluster: ClusterMarker = {
      region_id: `cluster-${cell.map((c) => c.region_id).join('-')}`,
      region_name: `${cell.length} regions`,
      lat,
      lon,
      event_count: totalCount,
      top_categories: top3,
      severity,
      _clusterCount: cell.length,
    };
    return [cluster];
  });
}

function buildTooltipHtml(obj: Record<string, unknown>): { html: string; style: Record<string, string> } | null {
  if (obj.region_name) {
    const m = obj as unknown as ClusterMarker;
    const cats = m.top_categories
      .slice(0, 3)
      .map((c) => `<span class="tt-pill tt-pill-${c}">${c.replace('_', ' ')}</span>`)
      .join('');
    const clusterNote = m._clusterCount ? `<div class="tt-cluster">${m._clusterCount} countries</div>` : '';
    return {
      html: `
        <div class="tt-card">
          <div class="tt-region">${m.region_name}</div>
          ${clusterNote}
          <div class="tt-meta-row">
            <span class="tt-severity tt-sev-${m.severity}">${m.severity.toUpperCase()}</span>
            <span class="tt-count">${m.event_count} events</span>
          </div>
          ${cats ? `<div class="tt-cats">${cats}</div>` : ''}
        </div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  if (obj.callsign) {
    const f = obj as unknown as FlightTrack;
    return {
      html: `<div class="tt-card"><div class="tt-region">${f.callsign}</div><div class="tt-meta-row"><span class="tt-count">Alt: ${f.altitude}ft</span><span class="tt-count">Speed: ${f.speed}kts</span></div></div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  if (obj.mmsi) {
    const s = obj as unknown as ShipTrack;
    return {
      html: `<div class="tt-card"><div class="tt-region">${s.name}</div><div class="tt-meta-row"><span class="tt-count">${s.ship_type}</span><span class="tt-count">→ ${s.destination}</span></div></div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  if (obj.threat_type) {
    const c = obj as unknown as CyberIOC;
    return {
      html: `<div class="tt-card"><div class="tt-region">${c.ip}</div><div class="tt-meta-row"><span class="tt-severity tt-sev-${c.severity}">${c.threat_type}</span><span class="tt-count">${c.country}</span></div></div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  if (obj.norad_id) {
    const sat = obj as unknown as SatelliteOrbit;
    return {
      html: `<div class="tt-card"><div class="tt-region">${sat.name}</div><div class="tt-meta-row"><span class="tt-count">NORAD: ${sat.norad_id}</span><span class="tt-count">${sat.orbit_type}</span></div></div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  if (obj.source_name) {
    const e = obj as unknown as EntityLink;
    return {
      html: `<div class="tt-card"><div class="tt-region">${e.source_name} → ${e.target_name}</div><div class="tt-meta-row"><span class="tt-count">${e.relationship}</span></div></div>`,
      style: { padding: '0', background: 'transparent', border: 'none' },
    };
  }
  return null;
}

export function GlobeViewer({
  markers,
  selectedMarkerId,
  onSelectMarker,
  layers: layerStates,
  flights,
  ships,
  cyberIOCs,
  signals,
  satellites,
  conflicts,
  entityLinks,
  flyToTarget,
  severityFilter,
}: GlobeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const deckRef = useRef<Deck<any> | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [pulsePhase, setPulsePhase] = useState(0);
  const [viewZoom, setViewZoom] = useState(INITIAL_VIEW_STATE.zoom);
  const onSelectRef = useRef(onSelectMarker);
  onSelectRef.current = onSelectMarker;

  const isEnabled = useCallback(
    (id: string) => layerStates.find((l) => l.id === id)?.enabled ?? false,
    [layerStates]
  );

  // Satellite trip animation
  useEffect(() => {
    if (!isEnabled('satellites')) return;
    const interval = setInterval(() => {
      setCurrentTime((t) => (t + 1) % 100);
    }, 100);
    return () => clearInterval(interval);
  }, [isEnabled]);

  // Pulse animation via requestAnimationFrame
  useEffect(() => {
    if (!isEnabled('news')) return;
    let frame: number;
    const tick = () => {
      setPulsePhase((p) => (p + 0.018) % 1);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [isEnabled]);

  // Initialize MapLibre + Deck
  useEffect(() => {
    const el = containerRef.current;
    if (!el || mapRef.current) return;

    const map = new maplibregl.Map({
      container: el,
      style: MAP_STYLE,
      center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom: INITIAL_VIEW_STATE.zoom,
      pitch: INITIAL_VIEW_STATE.pitch,
      bearing: INITIAL_VIEW_STATE.bearing,
      interactive: false,
      attributionControl: false,
    });
    mapRef.current = map;

    const deckCanvas = document.createElement('canvas');
    deckCanvas.id = 'deck-canvas';
    deckCanvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:1;';
    el.appendChild(deckCanvas);

    const deck = new Deck({
      canvas: deckCanvas,
      initialViewState: INITIAL_VIEW_STATE,
      controller: true,
      views: new MapView({ repeat: true }),
      layers: [],
      getTooltip: ({ object }: { object?: unknown }) => {
        if (!object || typeof object !== 'object') return null;
        return buildTooltipHtml(object as Record<string, unknown>);
      },
      onClick: (info: { object?: unknown }) => {
        if (!info.object) {
          onSelectRef.current(null);
        }
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onViewStateChange: ({ viewState }: any) => {
        setViewZoom(viewState.zoom as number);
        map.jumpTo({
          center: [viewState.longitude, viewState.latitude],
          zoom: viewState.zoom,
          bearing: viewState.bearing,
          pitch: viewState.pitch,
        });
      },
    });
    deckRef.current = deck;

    return () => {
      deck.finalize();
      map.remove();
      deckRef.current = null;
      mapRef.current = null;
    };
  }, []);

  // Programmatic fly-to when flyToTarget changes
  useEffect(() => {
    if (!flyToTarget || !deckRef.current) return;
    deckRef.current.setProps({
      initialViewState: {
        longitude: flyToTarget.lon,
        latitude: flyToTarget.lat,
        zoom: flyToTarget.zoom,
        pitch: flyToTarget.zoom > 3 ? 45 : 30,
        bearing: 0,
        transitionDuration: 1200,
        transitionInterpolator: new FlyToInterpolator({ speed: 1.5 }),
      },
    });
  }, [flyToTarget]);

  // Filtered + clustered markers for rendering
  const visibleMarkers = useMemo(() => {
    const filtered =
      severityFilter === 'all' ? markers : markers.filter((m) => m.severity === severityFilter);
    return clusterMarkers(filtered, viewZoom);
  }, [markers, severityFilter, viewZoom]);

  // Build deck.gl layers
  const deckLayers = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result: any[] = [];

    // --- News Events ---
    if (isEnabled('news') && visibleMarkers.length > 0) {
      const hasSelection = !!selectedMarkerId;

      // Halo / pulse layer (rendered behind main markers)
      result.push(
        new ScatterplotLayer({
          id: 'news-halo',
          data: visibleMarkers,
          pickable: false,
          stroked: false,
          filled: true,
          radiusMinPixels: 0,
          radiusMaxPixels: 80,
          getPosition: (d: ClusterMarker) => [d.lon, d.lat],
          getRadius: (d: ClusterMarker) => {
            const speed = d.severity === 'high' ? 2.5 : d.severity === 'medium' ? 1.5 : 0.8;
            const phase = (pulsePhase * speed) % 1;
            const base = Math.max(10, Math.sqrt(d.event_count) * 6);
            return base + phase * base * 0.9;
          },
          getFillColor: (d: ClusterMarker) => {
            if (hasSelection && d.region_id !== selectedMarkerId) return [0, 0, 0, 0];
            const speed = d.severity === 'high' ? 2.5 : d.severity === 'medium' ? 1.5 : 0.8;
            const phase = (pulsePhase * speed) % 1;
            const [r, g, b] = severityColor(d.severity);
            return [r, g, b, Math.round((1 - phase) * 90)];
          },
          updateTriggers: {
            getRadius: [pulsePhase],
            getFillColor: [pulsePhase, selectedMarkerId],
          },
        })
      );

      // Main marker dots
      result.push(
        new ScatterplotLayer({
          id: 'news-markers',
          data: visibleMarkers,
          pickable: true,
          opacity: 1,
          stroked: true,
          filled: true,
          radiusScale: 1,
          radiusMinPixels: 5,
          radiusMaxPixels: 32,
          lineWidthMinPixels: 1,
          getPosition: (d: ClusterMarker) => [d.lon, d.lat],
          getRadius: (d: ClusterMarker) => Math.max(8, Math.sqrt(d.event_count) * 5),
          getFillColor: (d: ClusterMarker) => {
            if (d.region_id === selectedMarkerId) return [255, 255, 255, 255];
            if (hasSelection) return [...severityColor(d.severity).slice(0, 3), 50] as [number, number, number, number];
            return severityColor(d.severity);
          },
          getLineColor: (d: ClusterMarker) => {
            if (hasSelection && d.region_id !== selectedMarkerId) return [...severityColor(d.severity).slice(0, 3), 30] as [number, number, number, number];
            return severityColor(d.severity);
          },
          getLineWidth: (d: ClusterMarker) => (d.region_id === selectedMarkerId ? 3 : 1),
          onClick: (info: { object?: ClusterMarker }) => {
            if (info.object) {
              // If it's a cluster, zoom in to expand it; otherwise select
              if (info.object._clusterCount && info.object._clusterCount > 1) {
                onSelectRef.current(null);
                if (deckRef.current) {
                  deckRef.current.setProps({
                    initialViewState: {
                      longitude: info.object.lon,
                      latitude: info.object.lat,
                      zoom: 2.5,
                      pitch: 35,
                      bearing: 0,
                      transitionDuration: 800,
                      transitionInterpolator: new FlyToInterpolator({ speed: 1.5 }),
                    },
                  });
                }
              } else {
                onSelectRef.current(info.object);
              }
            }
          },
          updateTriggers: {
            getFillColor: [selectedMarkerId],
            getLineColor: [selectedMarkerId],
            getLineWidth: [selectedMarkerId],
          },
        })
      );

      // Region name labels
      result.push(
        new TextLayer({
          id: 'news-labels',
          data: visibleMarkers,
          pickable: false,
          getPosition: (d: ClusterMarker) => [d.lon, d.lat],
          getText: (d: ClusterMarker) => d.region_name,
          getSize: 11,
          getColor: (d: ClusterMarker) => {
            if (d.region_id === selectedMarkerId) return [232, 240, 255, 255];
            if (hasSelection) return [142, 168, 216, 60];
            return [142, 168, 216, 200];
          },
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'bottom',
          getPixelOffset: [0, -14],
          fontFamily: '"Syne", sans-serif',
          fontWeight: 500,
          outlineColor: [2, 4, 8, 200],
          outlineWidth: 2,
          updateTriggers: { getColor: [selectedMarkerId] },
        })
      );

      // Event count badge
      result.push(
        new TextLayer({
          id: 'news-counts',
          data: visibleMarkers,
          pickable: false,
          getPosition: (d: ClusterMarker) => [d.lon, d.lat],
          getText: (d: ClusterMarker) =>
            d._clusterCount && d._clusterCount > 1
              ? `${d._clusterCount} rgns · ${d.event_count}`
              : String(d.event_count),
          getSize: (d: ClusterMarker) => (d._clusterCount && d._clusterCount > 1 ? 10 : 13),
          getColor: (d: ClusterMarker) => {
            if (hasSelection && d.region_id !== selectedMarkerId) return [255, 200, 80, 40];
            return [255, 200, 80, 220];
          },
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'top',
          getPixelOffset: [0, 5],
          fontFamily: '"Syne", sans-serif',
          fontWeight: 700,
          outlineColor: [2, 4, 8, 200],
          outlineWidth: 2,
          updateTriggers: { getColor: [selectedMarkerId] },
        })
      );
    }

    // --- Flight Tracking ---
    if (isEnabled('flights') && flights.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'flight-positions',
          data: flights,
          pickable: true,
          getPosition: (d: FlightTrack) => [d.current_position[0], d.current_position[1]],
          getRadius: 6,
          radiusMinPixels: 5,
          radiusMaxPixels: 14,
          getFillColor: LAYER_COLORS.flights,
          getLineColor: [255, 255, 255, 200],
          stroked: true,
          lineWidthMinPixels: 1,
        })
      );

      result.push(
        new ArcLayer({
          id: 'flight-arcs',
          data: flights,
          pickable: true,
          getSourcePosition: (d: FlightTrack) => d.origin,
          getTargetPosition: (d: FlightTrack) => d.destination,
          getSourceColor: LAYER_COLORS.flights,
          getTargetColor: [255, 200, 0, 150],
          getWidth: 1.5,
          greatCircle: true,
        })
      );
    }

    // --- Ship/AIS Tracking ---
    if (isEnabled('ships') && ships.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'ship-positions',
          data: ships,
          pickable: true,
          getPosition: (d: ShipTrack) => d.position,
          getRadius: 4,
          radiusMinPixels: 4,
          radiusMaxPixels: 12,
          getFillColor: LAYER_COLORS.ships,
          getLineColor: [255, 255, 255, 150],
          stroked: true,
          lineWidthMinPixels: 1,
        })
      );

      result.push(
        new PathLayer({
          id: 'ship-trails',
          data: ships.filter((s) => s.path.length > 1),
          pickable: false,
          getPath: (d: ShipTrack) => d.path,
          getColor: [0, 200, 255, 120],
          getWidth: 2,
          widthMinPixels: 1,
        })
      );
    }

    // --- Cyber IOCs ---
    if (isEnabled('cyber') && cyberIOCs.length > 0) {
      result.push(
        new HexagonLayer({
          id: 'cyber-hexagons',
          data: cyberIOCs,
          pickable: true,
          extruded: true,
          radius: 50000,
          elevationScale: 500,
          getPosition: (d: CyberIOC) => [d.lon, d.lat],
          getColorWeight: (d: CyberIOC) => d.count,
          getElevationWeight: (d: CyberIOC) => d.count,
          colorRange: [
            [65, 20, 120],
            [120, 40, 180],
            [170, 60, 220],
            [200, 80, 255],
            [230, 120, 255],
            [255, 180, 255],
          ],
        })
      );
    }

    // --- Signal / RF Coverage ---
    if (isEnabled('signals') && signals.length > 0) {
      result.push(
        new HeatmapLayer({
          id: 'signal-heatmap',
          data: signals,
          pickable: false,
          getPosition: (d: SignalCoverage) => [d.lon, d.lat],
          getWeight: (d: SignalCoverage) => d.intensity,
          radiusPixels: 60,
          intensity: 1,
          threshold: 0.05,
          colorRange: [
            [255, 255, 100],
            [255, 220, 50],
            [255, 180, 0],
            [255, 120, 0],
            [255, 60, 0],
            [255, 0, 0],
          ],
        })
      );
    }

    // --- Satellite Orbits ---
    if (isEnabled('satellites') && satellites.length > 0) {
      result.push(
        new PathLayer({
          id: 'satellite-orbits',
          data: satellites,
          pickable: false,
          getPath: (d: SatelliteOrbit) =>
            d.path.map((p) => [p[0], p[1]]) as [number, number][],
          getColor: [100, 255, 200, 80],
          getWidth: 1,
          widthMinPixels: 1,
        })
      );

      result.push(
        new TripsLayer({
          id: 'satellite-trips',
          data: satellites,
          getPath: (d: SatelliteOrbit) =>
            d.path.map((p) => [p[0], p[1]]) as [number, number][],
          getTimestamps: (d: SatelliteOrbit) =>
            d.path.map((_: number[], i: number) => i),
          getColor: LAYER_COLORS.satellites,
          trailLength: 20,
          currentTime,
          widthMinPixels: 2,
        })
      );

      result.push(
        new ScatterplotLayer({
          id: 'satellite-current',
          data: satellites,
          pickable: true,
          getPosition: (d: SatelliteOrbit) => [d.current_position[0], d.current_position[1]],
          getRadius: 5,
          radiusMinPixels: 4,
          getFillColor: [100, 255, 200, 255],
        })
      );
    }

    // --- Conflict Zones ---
    if (isEnabled('conflicts') && conflicts.length > 0) {
      const geoFeatures = conflicts.filter((c) => c.geometry);
      if (geoFeatures.length > 0) {
        result.push(
          new GeoJsonLayer({
            id: 'conflict-zones',
            data: {
              type: 'FeatureCollection' as const,
              features: geoFeatures.map((c) => c.geometry),
            },
            pickable: true,
            stroked: true,
            filled: true,
            getFillColor: [255, 60, 60, 40],
            getLineColor: [255, 60, 60, 180],
            getLineWidth: 2,
            lineWidthMinPixels: 1,
          })
        );
      }

      const conflictEvents = conflicts.flatMap((c) =>
        c.events.map((e) => ({ ...e, conflict_id: c.id, severity: c.severity }))
      );
      if (conflictEvents.length > 0) {
        result.push(
          new IconLayer({
            id: 'conflict-events',
            data: conflictEvents,
            pickable: true,
            iconAtlas:
              'data:image/svg+xml;base64,' +
              btoa(
                '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">' +
                  '<circle cx="32" cy="32" r="28" fill="#ff3c3c" opacity="0.8"/>' +
                  '<line x1="18" y1="18" x2="46" y2="46" stroke="white" stroke-width="4"/>' +
                  '<line x1="46" y1="18" x2="18" y2="46" stroke="white" stroke-width="4"/>' +
                  '</svg>'
              ),
            iconMapping: {
              marker: { x: 0, y: 0, width: 64, height: 64, anchorY: 32 },
            },
            getIcon: () => 'marker',
            getPosition: (d: { lon: number; lat: number }) => [d.lon, d.lat],
            getSize: 20,
            sizeMinPixels: 12,
          })
        );
      }
    }

    // --- Entity Link Analysis ---
    if (isEnabled('entity_links') && entityLinks.length > 0) {
      result.push(
        new ArcLayer({
          id: 'entity-links',
          data: entityLinks,
          pickable: true,
          getSourcePosition: (d: EntityLink) => d.source_position,
          getTargetPosition: (d: EntityLink) => d.target_position,
          getSourceColor: [150, 100, 255, 200],
          getTargetColor: [255, 100, 150, 200],
          getWidth: (d: EntityLink) => Math.max(1, d.strength * 3),
          widthMinPixels: 1,
          greatCircle: true,
        })
      );
    }

    return result;
  }, [
    visibleMarkers,
    selectedMarkerId,
    isEnabled,
    pulsePhase,
    flights,
    ships,
    cyberIOCs,
    signals,
    satellites,
    conflicts,
    entityLinks,
    currentTime,
  ]);

  // Sync layers to deck instance
  useEffect(() => {
    if (deckRef.current) {
      deckRef.current.setProps({ layers: deckLayers });
    }
  }, [deckLayers]);

  return <div ref={containerRef} className="globe-viewer" />;
}
