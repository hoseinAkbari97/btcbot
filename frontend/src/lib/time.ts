/**
 * Timezone handling for the chart and its labels.
 *
 * The backend stores and serves everything in UTC, and lightweight-charts
 * works in epoch seconds with no timezone concept of its own. So the conversion
 * has to happen at the edge: at the point a timestamp becomes text.
 *
 * The one place it must not be done is at the data layer. Candle `open_time`
 * values are absolute instants; shifting them by an offset before they reach the
 * chart would move the bars themselves, and every overlay — swings, structure
 * shifts, liquidity levels — is positioned by time, so every marker would drift
 * off its bar by however much the offset happened to be.
 *
 * So: the numbers stay in UTC, and only the rendered text is localized. A user
 * in +03:30 and a user in UTC see the same bar at the same x position and read
 * it as different clock times, which is correct.
 */

export const TIMEZONES = [
  { id: "UTC", label: "UTC", offset: "+00:00", local: "UTC" },
  {
    id: "Asia/Tehran",
    label: "+03:30",
    offset: "+03:30",
    local: "Tehran",
  },
] as const;

export type TimezoneId = (typeof TIMEZONES)[number]["id"];

export const DEFAULT_TIMEZONE: TimezoneId = "UTC";

export function isTimezoneId(value: string): value is TimezoneId {
  return TIMEZONES.some((zone) => zone.id === value);
}

/** Read the saved preference, falling back to UTC if it is unset or unknown. */
export function loadTimezone(): TimezoneId {
  const stored =
    typeof window === "undefined" ? null : window.localStorage.getItem("btcbot.tz");
  return stored && isTimezoneId(stored) ? stored : DEFAULT_TIMEZONE;
}

export function saveTimezone(id: TimezoneId): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("btcbot.tz", id);
  }
}

/**
 * Format an ISO timestamp in the given zone.
 *
 * `Intl.DateTimeFormat` is used rather than a hand-rolled offset because a
 * fixed-offset calculation is wrong for exactly the zones people care about:
 * Tehran has been +03:30 year-round since 2022 but was +04:30 for part of the
 * history this project holds, and any other zone may observe DST. Letting the
 * platform resolve the zone for a specific instant is the only version that is
 * right for all of them.
 */
export function formatTimestamp(
  iso: string,
  timezone: TimezoneId,
  options: Intl.DateTimeFormatOptions = {},
): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    hour12: false,
    ...options,
  }).format(date);
}

/** `2026-10-05 08:55 UTC+03:30` — the full form, for the last-bar readout. */
export function formatFull(iso: string, timezone: TimezoneId): string {
  return `${formatTimestamp(iso, timezone, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })} ${offsetLabel(timezone)}`;
}

/** The zone's offset as configured, e.g. `UTC+03:30`. */
export function offsetLabel(timezone: TimezoneId): string {
  const zone = TIMEZONES.find((item) => item.id === timezone);
  return zone ? `UTC${zone.offset}` : "UTC+00:00";
}

/** Compact age of a candle relative to now: `12s`, `4m`, `3h`, `2d`. */
export function formatAge(iso: string, now: number = Date.now()): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const seconds = Math.max(0, Math.round((now - then) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

/** A live UTC+local clock string for the toolbar. */
export function formatClock(timezone: TimezoneId, now: Date = new Date()): string {
  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(now);
  return `${time} ${offsetLabel(timezone)}`;
}