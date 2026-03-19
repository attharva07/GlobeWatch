import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Deck } from '@deck.gl/core';
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
  layers,
  flights,
  ships,
  cyberIOCs,
  signals,
  satellites,
  conflicts,
  entityLinks,
}: GlobeViewerProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const deckCanvasRef = useRef<HTMLCanvasElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckRef = useRef<Deck | null>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const isEnabled = useCallback(
    (id: string) => layers.find((l) => l.id === id)?.enabled ?? false,
    [layers]
  );

  // Animate satellite trips
  useEffect(() => {
    if (!isEnabled('satellites')) return;
    const interval = setInterval(() => {
      setCurrentTime((t) => (t + 1) % 100);
    }, 100);
    return () => clearInterval(interval);
  }, [isEnabled]);

  // Init map + deck
  useEffect(() => {
    if (!mapContainerRef.current || !deckCanvasRef.current) return;
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom: INITIAL_VIEW_STATE.zoom,
      pitch: INITIAL_VIEW_STATE.pitch,
      bearing: INITIAL_VIEW_STATE.bearing,
    });

    const deck = new Deck({
      canvas: deckCanvasRef.current,
      initialViewState: INITIAL_VIEW_STATE,
      controller: true,
      layers: [],
      onViewStateChange: ({ viewState }) => {
        map.jumpTo({
          center: [viewState.longitude, viewState.latitude],
          zoom: viewState.zoom,
          pitch: viewState.pitch,
          bearing: viewState.bearing,
        });
      },
    });

    mapRef.current = map;
    deckRef.current = deck;

    return () => {
      deck.finalize();
      map.remove();
      mapRef.current = null;
      deckRef.current = null;
    };
  }, []);

  const deckLayers = useMemo(() => {
    const result: (
      | ScatterplotLayer
      | TextLayer
      | ArcLayer
      | PathLayer
      | IconLayer
      | GeoJsonLayer
      | HeatmapLayer
      | HexagonLayer
      | TripsLayer
    )[] = [];

    // --- News Events (ScatterplotLayer + TextLayer) ---
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
          getPosition: (d: RegionMarker) => [d.lon, d.lat] as [number, number],
          getRadius: (d: RegionMarker) => Math.max(8, Math.sqrt(d.event_count) * 5),
          getFillColor: (d: RegionMarker) =>
            d.region_id === selectedMarkerId
              ? [255, 255, 255, 255] as [number, number, number, number]
              : severityColor(d.severity),
          getLineColor: (d: RegionMarker) => severityColor(d.severity),
          getLineWidth: (d: RegionMarker) => (d.region_id === selectedMarkerId ? 3 : 1),
          onClick: (info) => {
            onSelectMarker((info.object as RegionMarker) ?? null);
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
          getPosition: (d: RegionMarker) => [d.lon, d.lat] as [number, number],
          getText: (d: RegionMarker) => d.region_name,
          getSize: 12,
          getColor: (d: RegionMarker) =>
            d.region_id === selectedMarkerId
              ? [232, 240, 255, 255] as [number, number, number, number]
              : [142, 168, 216, 200] as [number, number, number, number],
          getTextAnchor: 'middle' as const,
          getAlignmentBaseline: 'bottom' as const,
          getPixelOffset: [0, -16] as [number, number],
          fontFamily: '"Syne", sans-serif',
          fontWeight: 500,
          outlineColor: [2, 4, 8, 200] as [number, number, number, number],
          outlineWidth: 2,
          updateTriggers: {
            getColor: [selectedMarkerId],
          },
        })
      );
    }

    // --- Flight Tracking (ArcLayer for routes) ---
    if (isEnabled('flights') && flights.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'flight-positions',
          data: flights,
          pickable: true,
          getPosition: (d: FlightTrack) => [d.current_position[0], d.current_position[1]] as [number, number],
          getRadius: 6,
          radiusMinPixels: 5,
          radiusMaxPixels: 14,
          getFillColor: LAYER_COLORS.flights,
          getLineColor: [255, 255, 255, 200] as [number, number, number, number],
          stroked: true,
          lineWidthMinPixels: 1,
        })
      );

      result.push(
        new ArcLayer({
          id: 'flight-arcs',
          data: flights,
          pickable: true,
          getSourcePosition: (d: FlightTrack) => d.origin as [number, number],
          getTargetPosition: (d: FlightTrack) => d.destination as [number, number],
          getSourceColor: LAYER_COLORS.flights,
          getTargetColor: [255, 200, 0, 150] as [number, number, number, number],
          getWidth: 1.5,
          greatCircle: true,
        })
      );
    }

    // --- Ship/AIS Tracking (ScatterplotLayer + PathLayer) ---
    if (isEnabled('ships') && ships.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: 'ship-positions',
          data: ships,
          pickable: true,
          getPosition: (d: ShipTrack) => d.position as [number, number],
          getRadius: 4,
          radiusMinPixels: 4,
          radiusMaxPixels: 12,
          getFillColor: LAYER_COLORS.ships,
          getLineColor: [255, 255, 255, 150] as [number, number, number, number],
          stroked: true,
          lineWidthMinPixels: 1,
        })
      );

      result.push(
        new PathLayer({
          id: 'ship-trails',
          data: ships.filter((s) => s.path.length > 1),
          pickable: false,
          getPath: (d: ShipTrack) => d.path as [number, number][],
          getColor: [0, 200, 255, 120] as [number, number, number, number],
          getWidth: 2,
          widthMinPixels: 1,
        })
      );
    }

    // --- IP Geolocation / Cyber IOCs (HexagonLayer) ---
    if (isEnabled('cyber') && cyberIOCs.length > 0) {
      result.push(
        new HexagonLayer({
          id: 'cyber-hexagons',
          data: cyberIOCs,
          pickable: true,
          extruded: true,
          radius: 50000,
          elevationScale: 500,
          getPosition: (d: CyberIOC) => [d.lon, d.lat] as [number, number],
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

    // --- Signal / RF Coverage (HeatmapLayer) ---
    if (isEnabled('signals') && signals.length > 0) {
      result.push(
        new HeatmapLayer({
          id: 'signal-heatmap',
          data: signals,
          pickable: false,
          getPosition: (d: SignalCoverage) => [d.lon, d.lat] as [number, number],
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

    // --- Satellite Orbits (PathLayer + TripsLayer + ScatterplotLayer) ---
    if (isEnabled('satellites') && satellites.length > 0) {
      result.push(
        new PathLayer({
          id: 'satellite-orbits',
          data: satellites,
          pickable: false,
          getPath: (d: SatelliteOrbit) => d.path.map((p) => [p[0], p[1]] as [number, number]),
          getColor: [100, 255, 200, 80] as [number, number, number, number],
          getWidth: 1,
          widthMinPixels: 1,
        })
      );

      result.push(
        new TripsLayer({
          id: 'satellite-trips',
          data: satellites,
          getPath: (d: SatelliteOrbit) => d.path.map((p) => [p[0], p[1]] as [number, number]),
          getTimestamps: (d: SatelliteOrbit) => d.path.map((_: unknown, i: number) => i),
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
          getPosition: (d: SatelliteOrbit) => [d.current_position[0], d.current_position[1]] as [number, number],
          getRadius: 5,
          radiusMinPixels: 4,
          getFillColor: [100, 255, 200, 255] as [number, number, number, number],
        })
      );
    }

    // --- Conflict Zones (GeoJsonLayer + IconLayer) ---
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
            getFillColor: [255, 60, 60, 40] as [number, number, number, number],
            getLineColor: [255, 60, 60, 180] as [number, number, number, number],
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
            iconAtlas: 'data:image/svg+xml;base64,' + btoa('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="28" fill="#ff3c3c" opacity="0.8"/><line x1="18" y1="18" x2="46" y2="46" stroke="white" stroke-width="4"/><line x1="46" y1="18" x2="18" y2="46" stroke="white" stroke-width="4"/></svg>'),
            iconMapping: { marker: { x: 0, y: 0, width: 64, height: 64, anchorY: 32 } },
            getIcon: () => 'marker',
            getPosition: (d: { lon: number; lat: number }) => [d.lon, d.lat] as [number, number],
            getSize: 20,
            sizeMinPixels: 12,
          })
        );
      }
    }

    // --- Entity Link Analysis (ArcLayer) ---
    if (isEnabled('entity_links') && entityLinks.length > 0) {
      result.push(
        new ArcLayer({
          id: 'entity-links',
          data: entityLinks,
          pickable: true,
          getSourcePosition: (d: EntityLink) => d.source_position as [number, number],
          getTargetPosition: (d: EntityLink) => d.target_position as [number, number],
          getSourceColor: [150, 100, 255, 200] as [number, number, number, number],
          getTargetColor: [255, 100, 150, 200] as [number, number, number, number],
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
    onSelectMarker,
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

  // Update deck layers
  useEffect(() => {
    if (deckRef.current) {
      deckRef.current.setProps({ layers: deckLayers });
    }
  }, [deckLayers]);

  return (
    <div className="globe-viewer">
      <div ref={mapContainerRef} style={{ position: 'absolute', inset: 0 }} />
      <canvas ref={deckCanvasRef} style={{ position: 'absolute', inset: 0, pointerEvents: 'auto' }} />
    </div>
  );
}
