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
  VerticalOrigin,
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

  const onSelectMarkerRef = useRef(onSelectMarker);
  useEffect(() => { onSelectMarkerRef.current = onSelectMarker; }, [onSelectMarker]);

  const stableOnSelect = useCallback((marker: RegionMarker | null) => {
    onSelectMarkerRef.current(marker);
  }, []);

  // Init globe once
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const imageryProvider = new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/' });
    imageryProvider.errorEvent.addEventListener((error) => {
      console.error('OpenStreetMap imagery failed to load.', error);
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
      terrainProvider: new EllipsoidTerrainProvider(),
    });

    viewer.scene.globe.show = true;
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.baseColor = Color.fromCssColorString('#0a0f1a');
    if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = true;
    viewer.scene.backgroundColor = Color.fromCssColorString('#020408');

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(0, 20, 22_000_000),
      duration: 0,
    });

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: { position: Cartesian2 }) => {
      const picked = viewer.scene.pick(movement.position);
      if (!picked || !(picked.id instanceof Entity)) {
        stableOnSelect(null);
        return;
      }
      const marker = picked.id.properties?.marker?.getValue();
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

  // Update markers
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    viewer.entities.removeAll();

    markers.forEach((marker) => {
      const isSelected = selectedMarkerId === marker.region_id;

      viewer.entities.add({
        id: marker.region_id,
        position: Cartesian3.fromDegrees(marker.lon, marker.lat, 0),
        billboard: {
          image: buildPinDataUri(marker.severity, isSelected),
          verticalOrigin: VerticalOrigin.CENTER,
          scale: 1,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: `${marker.region_name}`,
          font: '500 11px "Syne", sans-serif',
          fillColor: Color.fromCssColorString(isSelected ? '#e8f0ff' : '#8ea8d8'),
          outlineColor: Color.fromCssColorString('#020408'),
          outlineWidth: 3,
          style: 2, // FILL_AND_OUTLINE
          scale: 1,
          pixelOffset: new Cartesian2(0, isSelected ? -18 : -14),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          translucencyByDistance: undefined,
        },
        properties: { marker },
      });
    });
  }, [markers, selectedMarkerId]);

  return <div ref={containerRef} className="globe-viewer" />;
}
