interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Loading globe intelligence feed...' }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-spinner" />
      <p>{message}</p>
    </div>
  );
}
