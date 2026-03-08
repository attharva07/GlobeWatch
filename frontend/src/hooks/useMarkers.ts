import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError } from '../api/client';
import { fetchHealth, fetchRegionMarkers } from '../api/globe';
import type { RegionMarker } from '../types/marker';

interface UseMarkersResult {
  markers: RegionMarker[];
  markerCount: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useMarkers(enabled: boolean): UseMarkersResult {
  const [markers, setMarkers] = useState<RegionMarker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadMarkers = useCallback(async () => {
    if (!enabled) {
      setMarkers([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    try {
      await fetchHealth();
      const response = await fetchRegionMarkers();
      setMarkers(response.regions ?? []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.details ? `${err.message}: ${err.details}` : err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unknown error while loading region markers.');
      }
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void loadMarkers();
    const intervalId = window.setInterval(() => {
      void loadMarkers();
    }, 30_000);
    return () => window.clearInterval(intervalId);
  }, [loadMarkers]);

  return useMemo(
    () => ({ markers, markerCount: markers.length, loading, error, refresh: loadMarkers }),
    [markers, loading, error, loadMarkers]
  );
}
