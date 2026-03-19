export function severityColor(severity: string): [number, number, number, number] {
  const normalized = severity.toLowerCase();
  if (normalized === 'critical' || normalized === 'high') return [255, 78, 80, 220];
  if (normalized === 'medium' || normalized === 'moderate') return [255, 179, 71, 220];
  return [61, 220, 151, 220];
}

export function severityHex(severity: string): string {
  const normalized = severity.toLowerCase();
  if (normalized === 'critical' || normalized === 'high') return '#ff4e50';
  if (normalized === 'medium' || normalized === 'moderate') return '#ffb347';
  return '#3ddc97';
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  });
}

export const LAYER_COLORS: Record<string, [number, number, number, number]> = {
  news: [77, 159, 255, 200],
  flights: [255, 165, 0, 200],
  ships: [0, 200, 255, 200],
  cyber: [200, 50, 255, 200],
  signals: [255, 255, 100, 180],
  satellites: [100, 255, 200, 200],
  conflicts: [255, 60, 60, 200],
  entity_links: [150, 100, 255, 180],
};
