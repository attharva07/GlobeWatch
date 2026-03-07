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
import type { Marker } from '../types/marker';
import { buildPinDataUri } from '../lib/cesium';

interface GlobeViewerProps {
  markers: Marker[];
  selectedMarkerId: string | null;
  onSelectMarker: (marker: Marker | null) => void;
}

export function GlobeViewer({ markers, selectedMarkerId, onSelectMarker }: GlobeViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const handlerRef = useRef<ScreenSpaceEventHandler | null>(null);

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) {
      return;
    }

    let cancelled = false;

    const initializeViewer = () => {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
      const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN;
      console.info('[GlobeViewer] Initializing Cesium viewer', {
        apiBaseUrl,
        hasIonToken: Boolean(ionToken)
      });

      const imageryProvider = new OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/'
      });

      imageryProvider.errorEvent.addEventListener((error) => {
        console.error('[GlobeViewer] Base imagery provider error', error);
      });

      let viewer: Viewer;

      try {
        viewer = new Viewer(containerRef.current!, {
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
      } catch (error) {
        console.error('[GlobeViewer] Failed to create Cesium viewer', error);
        return;
      }

      if (cancelled) {
        viewer.destroy();
        return;
      }

      viewer.scene.globe.show = true;
      viewer.scene.globe.enableLighting = true;
      if (viewer.scene.skyBox) {
        viewer.scene.skyBox.show = true;
      }
      viewer.scene.backgroundColor = Color.fromCssColorString('#03050a');

      const hasTerrainProvider = viewer.terrainProvider instanceof EllipsoidTerrainProvider;
      if (!hasTerrainProvider) {
        console.error('[GlobeViewer] Unexpected terrain provider configuration', viewer.terrainProvider);
      } else {
        console.info('[GlobeViewer] Using ellipsoid terrain provider for reliable globe rendering');
      }

      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(0, 18, 23_000_000),
        orientation: {
          heading: CesiumMath.toRadians(0),
          pitch: CesiumMath.toRadians(-52),
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
        onSelectMarker((marker as Marker) ?? null);
      }, ScreenSpaceEventType.LEFT_CLICK);

      viewerRef.current = viewer;
      handlerRef.current = handler;
    };

    initializeViewer();

    return () => {
      cancelled = true;
      handlerRef.current?.destroy();
      viewerRef.current?.destroy();
      handlerRef.current = null;
      viewerRef.current = null;
    };
  }, [onSelectMarker]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }

    viewer.entities.removeAll();

    markers.forEach((marker) => {
      viewer.entities.add({
        id: marker.id,
        position: Cartesian3.fromDegrees(marker.lon, marker.lat, 0),
        billboard: {
          image: buildPinDataUri(marker.severity),
          verticalOrigin: 1,
          scale: selectedMarkerId === marker.id ? 1.2 : 1,
          eyeOffset: new Cartesian3(0, 0, selectedMarkerId === marker.id ? -50 : 0)
        },
        properties: {
          marker
        }
      });
    });
  }, [markers, selectedMarkerId]);

  return <div ref={containerRef} className="globe-viewer" />;
}
