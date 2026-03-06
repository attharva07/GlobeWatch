import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError } from '../api/client';
import { fetchGlobeMarkers, fetchHealth } from '../api/globe';
import type { Marker } from '../types/marker';

interface UseMarkersResult {
  markers: Marker[];
  markerCount: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useMarkers(selectedLayers: string[]): UseMarkersResult {
  const [markers, setMarkers] = useState<Marker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadMarkers = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await fetchHealth();
      const response = await fetchGlobeMarkers(selectedLayers);
      setMarkers(response.markers ?? []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.details ? `${err.message}: ${err.details}` : err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unknown error while loading markers.');
      }
    } finally {
      setLoading(false);
    }
  }, [selectedLayers]);

  useEffect(() => {
    void loadMarkers();
  }, [loadMarkers]);

  return useMemo(
    () => ({
      markers,
      markerCount: markers.length,
      loading,
      error,
      refresh: loadMarkers
    }),
    [markers, loading, error, loadMarkers]
  );
}
