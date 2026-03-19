import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Deck, MapView } from '@deck.gl/core';
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
}: GlobeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const deckRef = useRef<Deck<any> | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const onSelectRef = useRef(onSelectMarker);
  onSelectRef.current = onSelectMarker;

  const isEnabled = useCallback(
    (id: string) => layerStates.find((l) => l.id === id)?.enabled ?? false,
    [layerStates]
  );

  // Animate satellite trips
  useEffect(() => {
    if (!isEnabled('satellites')) return;
    const interval = setInterval(() => {
      setCurrentTime((t) => (t + 1) % 100);
    }, 100);
    return () => clearInterval(interval);
  }, [isEnabled]);

  // Initialize MapLibre + Deck
  useEffect(() => {
    const el = containerRef.current;
    if (!el || mapRef.current) return;

    // Create MapLibre map
    const map = new maplibregl.Map({
      container: el,
      style: MAP_STYLE,
      center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom: INITIAL_VIEW_STATE.zoom,
      pitch: INITIAL_VIEW_STATE.pitch,
      bearing: INITIAL_VIEW_STATE.bearing,
      interactive: false, // deck.gl controls interactions
      attributionControl: false,
    });
    mapRef.current = map;

    // Create deck.gl overlay canvas
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
        const obj = object as Record<string, unknown>;
        if (obj.region_name) {
          const m = obj as unknown as RegionMarker;
          return `${m.region_name}\n${m.event_count} events (${m.severity})`;
        }
        if (obj.callsign) {
          const f = obj as unknown as FlightTrack;
          return `${f.callsign}\nAlt: ${f.altitude}ft  Speed: ${f.speed}kts`;
        }
        if (obj.mmsi) {
          const s = obj as unknown as ShipTrack;
          return `${s.name}\nType: ${s.ship_type}  Dest: ${s.destination}`;
        }
        if (obj.threat_type) {
          const c = obj as unknown as CyberIOC;
          return `${c.ip}\n${c.threat_type} (${c.severity})\n${c.country}`;
        }
        if (obj.norad_id) {
          const sat = obj as unknown as SatelliteOrbit;
          return `${sat.name}\nNORAD: ${sat.norad_id}\nOrbit: ${sat.orbit_type}`;
        }
        if (obj.source_name) {
          const e = obj as unknown as EntityLink;
          return `${e.source_name} → ${e.target_name}\n${e.relationship}`;
        }
        return null;
      },
      onClick: (info: { object?: unknown }) => {
        if (!info.object) {
          onSelectRef.current(null);
        }
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onViewStateChange: ({ viewState }: any) => {
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

  // Build layers
  const deckLayers = useMemo(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result: any[] = [];

    // --- News Events ---
    if (isEnabled('news') && markers.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'news-markers',
          data: markers,
          pickable: true,
          opacity: 0.9,
          stroked: true,
          filled: true,
          radiusScale: 1,
          radiusMinPixels: 6,
          radiusMaxPixels: 30,
          lineWidthMinPixels: 1,
          getPosition: (d: RegionMarker) => [d.lon, d.lat],
          getRadius: (d: RegionMarker) => Math.max(8, Math.sqrt(d.event_count) * 5),
          getFillColor: (d: RegionMarker) =>
            d.region_id === selectedMarkerId
              ? [255, 255, 255, 255]
              : severityColor(d.severity),
          getLineColor: (d: RegionMarker) => severityColor(d.severity),
          getLineWidth: (d: RegionMarker) => (d.region_id === selectedMarkerId ? 3 : 1),
          onClick: (info: { object?: RegionMarker }) => {
            onSelectRef.current(info.object ?? null);
          },
          updateTriggers: {
            getFillColor: [selectedMarkerId],
            getLineWidth: [selectedMarkerId],
          },
        })
      );

      result.push(
        new TextLayer({
          id: 'news-labels',
          data: markers,
          pickable: false,
          getPosition: (d: RegionMarker) => [d.lon, d.lat],
          getText: (d: RegionMarker) => d.region_name,
          getSize: 12,
          getColor: (d: RegionMarker) =>
            d.region_id === selectedMarkerId
              ? [232, 240, 255, 255]
              : [142, 168, 216, 200],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'bottom',
          getPixelOffset: [0, -16],
          fontFamily: '"Syne", sans-serif',
          fontWeight: 500,
          outlineColor: [2, 4, 8, 200],
          outlineWidth: 2,
          updateTriggers: {
            getColor: [selectedMarkerId],
          },
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
    markers,
    selectedMarkerId,
    isEnabled,
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
