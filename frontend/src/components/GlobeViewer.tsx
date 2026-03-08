import { useEffect, useRef } from 'react';
import {
  Cartesian2,
  Cartesian3,
  Color,
  EllipsoidTerrainProvider,
  Entity,
  ImageryLayer,
  Math as CesiumMath,
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

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const imageryProvider = new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/' });
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
    viewer.scene.backgroundColor = Color.fromCssColorString('#03050a');

    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(-25, 25, 24_000_000),
      orientation: {
        heading: CesiumMath.toRadians(0),
        pitch: CesiumMath.toRadians(-58),
        roll: 0
      }
    });

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: { position: Cartesian2 }) => {
      const pickedObject = viewer.scene.pick(movement.position);
      if (!pickedObject || !(pickedObject.id instanceof Entity)) {
        onSelectMarker(null);
        return;
      }
      const marker = pickedObject.id.properties?.marker?.getValue();
      onSelectMarker((marker as RegionMarker) ?? null);
    }, ScreenSpaceEventType.LEFT_CLICK);

    viewerRef.current = viewer;
    handlerRef.current = handler;

    return () => {
      handlerRef.current?.destroy();
      viewerRef.current?.destroy();
      handlerRef.current = null;
      viewerRef.current = null;
    };
  }, [onSelectMarker]);

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
