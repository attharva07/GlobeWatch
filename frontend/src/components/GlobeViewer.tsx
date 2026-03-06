import { useEffect, useRef } from 'react';
import {
  Cartesian3,
  Entity,
  Math as CesiumMath,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  Cartesian2,
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
      shouldAnimate: true
    });

    viewer.scene.globe.enableLighting = true;
    if (viewer.scene.skyBox) {
      viewer.scene.skyBox.show = true;
    }
    viewer.scene.camera.flyTo({
      destination: Cartesian3.fromDegrees(10, 18, 20_000_000),
      orientation: {
        heading: CesiumMath.toRadians(15),
        pitch: CesiumMath.toRadians(-35),
        roll: 0
      },
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
      onSelectMarker((marker as Marker) ?? null);
    }, ScreenSpaceEventType.LEFT_CLICK);

    viewerRef.current = viewer;
    handlerRef.current = handler;

    return () => {
      handler.destroy();
      viewer.destroy();
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

  return <div className="globe-viewer" ref={containerRef} />;
}
