import { Color, PinBuilder } from 'cesium';

export function severityColor(severity: string): Color {
  const normalized = severity.toLowerCase();

  if (normalized === 'critical' || normalized === 'high') {
    return Color.fromCssColorString('#ff4e50');
  }

  if (normalized === 'medium' || normalized === 'moderate') {
    return Color.fromCssColorString('#ffb347');
  }

  return Color.fromCssColorString('#3ddc97');
}

const pinBuilder = new PinBuilder();

export function buildPinDataUri(severity: string): string {
  const color = severityColor(severity);
  return pinBuilder.fromColor(color, 44).toDataURL();
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString();
}
