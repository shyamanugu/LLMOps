/** Small, dependency-free formatting helpers used across pages. */

/** Format a USD amount with sensible precision. */
export function usd(value: number): string {
  const digits = value !== 0 && Math.abs(value) < 1 ? 4 : 2;
  return `$${value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

/** Compact integer with thousands separators. */
export function count(value: number): string {
  return value.toLocaleString();
}

/** Milliseconds as a human duration. */
export function ms(value: number): string {
  return value >= 1000 ? `${(value / 1000).toFixed(2)}s` : `${Math.round(value)}ms`;
}

/** ISO timestamp -> short local date-time. */
export function dateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Truncate a hex/id for compact display. */
export function shortId(id: string, head = 8): string {
  return id.length > head ? `${id.slice(0, head)}…` : id;
}
