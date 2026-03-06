interface ErrorBannerProps {
  message: string;
}

export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <strong>Backend connection issue:</strong> {message}
    </div>
  );
}
