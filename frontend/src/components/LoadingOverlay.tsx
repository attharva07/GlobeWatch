interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Syncing intelligence feed...' }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-ring">
        <div className="loading-ring-outer" />
        <div className="loading-ring-inner" />
      </div>
      <p className="loading-text">{message}</p>
    </div>
  );
}
