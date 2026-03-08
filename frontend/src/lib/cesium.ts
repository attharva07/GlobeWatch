import { Color } from 'cesium';

export function severityColor(severity: string): string {
  const normalized = severity.toLowerCase();
  if (normalized === 'critical' || normalized === 'high') return '#ff4e50';
  if (normalized === 'medium' || normalized === 'moderate') return '#ffb347';
  return '#3ddc97';
}

export function severityCesiumColor(severity: string): Color {
  return Color.fromCssColorString(severityColor(severity));
}

/**
 * Builds a clean SVG circle marker as a data URI.
 * Replaces the default bulky Cesium PinBuilder pins with minimal glowing dots.
 */
export function buildPinDataUri(severity: string, selected = false): string {
  const color = severityColor(severity);
  const size = selected ? 22 : 16;
  const ring = selected ? 10 : 7;
  const glow = selected ? 8 : 4;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size * 2}" height="${size * 2}" viewBox="0 0 ${size * 2} ${size * 2}">
    <defs>
      <filter id="glow">
        <feGaussianBlur stdDeviation="${glow}" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <!-- outer pulse ring -->
    <circle cx="${size}" cy="${size}" r="${ring}" fill="none" stroke="${color}" stroke-width="1" opacity="0.4" filter="url(#glow)"/>
    <!-- inner filled dot -->
    <circle cx="${size}" cy="${size}" r="${selected ? 7 : 5}" fill="${color}" opacity="0.95" filter="url(#glow)"/>
    <!-- bright center -->
    <circle cx="${size}" cy="${size}" r="${selected ? 3 : 2}" fill="white" opacity="0.8"/>
  </svg>`;

  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
    timeZoneName: 'short'
  });
}
