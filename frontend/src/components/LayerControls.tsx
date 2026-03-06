interface LayerControlsProps {
  newsEnabled: boolean;
  markerCount: number;
  onToggleNews: () => void;
  onRefresh: () => void;
  loading: boolean;
}

export function LayerControls({ newsEnabled, markerCount, onToggleNews, onRefresh, loading }: LayerControlsProps) {
  return (
    <section className="layer-controls">
      <h2>Layers</h2>
      <label className="toggle-row">
        <input type="checkbox" checked={newsEnabled} onChange={onToggleNews} />
        <span>News</span>
      </label>

      <button type="button" className="refresh-button" onClick={onRefresh} disabled={loading}>
        {loading ? 'Refreshing…' : 'Refresh feed'}
      </button>

      <p className="marker-count">Markers: {markerCount}</p>
    </section>
  );
}
