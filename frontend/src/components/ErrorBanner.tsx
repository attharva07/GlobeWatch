interface ErrorBannerProps {
  message: string;
}

export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-icon">⚠</span>
      <span>{message}</span>
    </div>
  );
}
