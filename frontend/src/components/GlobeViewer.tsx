import { useCallback, useEffect, useRef } from 'react';
import {
  Cartesian2,
  Cartesian3,
  Color,
  EllipsoidTerrainProvider,
  Entity,
  ImageryLayer,
  OpenStreetMapImageryProvider,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  Viewer
} from 'cesium';
import type { RegionMarker } from '../types/marker';
import { buildPinDataUri } from '../lib/cesium';

interface GlobeViewerProps {
  markers: RegionMarker[];
  selectedMarkerId: string | null;
  onSelectMarker: (marker: RegionMarker | null) => void;
}

export function GlobeViewer({ markers, selectedMarkerId, onSelectMarker }: GlobeViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const handlerRef = useRef<ScreenSpaceEventHandler | null>(null);
  // Store the latest callback in a ref so the Cesium click handler never becomes stale
  // without causing the viewer to be torn down and recreated on every render.
  const onSelectMarkerRef = useRef(onSelectMarker);
  useEffect(() => { onSelectMarkerRef.current = onSelectMarker; }, [onSelectMarker]);

  const stableOnSelect = useCallback((marker: RegionMarker | null) => {
    onSelectMarkerRef.current(marker);
  }, []);

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const imageryProvider = new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/' });
    imageryProvider.errorEvent.addEventListener((error) => {
      console.error('OpenStreetMap imagery failed to load in GlobeViewer.', error);
    });

    const viewer = new Viewer(containerRef.current, {
      animation: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      geocoder: false,
      homeButton: false,
      infoBox: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      selectionIndicator: false,
      timeline: false,
      shouldAnimate: true,
      baseLayer: new ImageryLayer(imageryProvider),
      terrainProvider: new EllipsoidTerrainProvider()
    });

    viewer.scene.globe.show = true;
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.baseColor = Color.DARKSLATEGRAY;
    if (viewer.scene.skyAtmosphere) {
      viewer.scene.skyAtmosphere.show = true;
    }
    viewer.scene.backgroundColor = Color.fromCssColorString('#03050a');

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(0, 20, 22_000_000),
      duration: 0
    });

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: { position: Cartesian2 }) => {
      const pickedObject = viewer.scene.pick(movement.position);
      if (!pickedObject || !(pickedObject.id instanceof Entity)) {
        onSelectMarker(null);
        return;
      }
      const marker = pickedObject.id.properties?.marker?.getValue();
      stableOnSelect((marker as RegionMarker) ?? null);
    }, ScreenSpaceEventType.LEFT_CLICK);

    viewerRef.current = viewer;
    handlerRef.current = handler;

    return () => {
      handlerRef.current?.destroy();
      viewerRef.current?.destroy();
      handlerRef.current = null;
      viewerRef.current = null;
    };
  }, [stableOnSelect]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    viewer.entities.removeAll();
    markers.forEach((marker) => {
      viewer.entities.add({
        id: marker.region_id,
        position: Cartesian3.fromDegrees(marker.lon, marker.lat, 0),
        billboard: {
          image: buildPinDataUri(marker.severity),
          verticalOrigin: 1,
          scale: selectedMarkerId === marker.region_id ? 1.2 : 1,
          eyeOffset: new Cartesian3(0, 0, selectedMarkerId === marker.region_id ? -50 : 0)
        },
        label: {
          text: `${marker.region_name} (${marker.event_count})`,
          scale: 0.35,
          pixelOffset: new Cartesian2(0, -36)
        },
        properties: { marker }
      });
    });
  }, [markers, selectedMarkerId]);

  return <div ref={containerRef} className="globe-viewer" />;
}
