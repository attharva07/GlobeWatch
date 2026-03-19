import type { LayerState } from '../types/marker';

interface LayerControlsProps {
  layers: LayerState[];
  markerCount: number;
  onToggleLayer: (id: string) => void;
  onRefresh: () => void;
  loading: boolean;
}

export function LayerControls({ layers, markerCount, onToggleLayer, onRefresh, loading }: LayerControlsProps) {
  return (
    <section className="layer-controls">
      <div className="panel-header">
        <div className="panel-header-icon" />
        <span className="panel-header-label">Layers</span>
      </div>
      <div className="panel-body">
        {layers.map((layer) => (
          <label key={layer.id} className="toggle-row">
            <span className="toggle-label">
              <span className="layer-icon">{layer.icon}</span> {layer.label}
            </span>
            <div className="toggle-switch">
              <input
                type="checkbox"
                checked={layer.enabled}
                onChange={() => onToggleLayer(layer.id)}
              />
              <div className="toggle-track" />
              <div className="toggle-thumb" />
            </div>
          </label>
        ))}

        <button type="button" className="refresh-button" onClick={onRefresh} disabled={loading}>
          <span className="refresh-icon">↻</span>
          {loading ? 'Syncing...' : 'Refresh Feed'}
        </button>

        <div className="marker-count-row">
          <span className="marker-count-label">Regions Active</span>
          <span className="marker-count-value">{markerCount}</span>
        </div>

        <div className="severity-legend">
          <div className="severity-legend-title">Severity</div>
          <div className="severity-item"><div className="severity-dot high" /> High Risk</div>
          <div className="severity-item"><div className="severity-dot medium" /> Medium Risk</div>
          <div className="severity-item"><div className="severity-dot low" /> Low Risk</div>
        </div>
      </div>
    </section>
  );
}
