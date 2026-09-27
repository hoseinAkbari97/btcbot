import type {
  Candle,
  CandlePage,
  LiquidityLevel,
  MarketRegime,
  MarketStructure,
  StructureEvent,
  SwingPoint,
  SystemStatus,
  Timeframe,
} from "../types/market";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function getSystemStatus(): Promise<SystemStatus> {
  return getJson<SystemStatus>("/api/v1/system/status");
}

export function getCandles(symbol: string, timeframe: Timeframe): Promise<CandlePage> {
  const params = new URLSearchParams({ symbol, timeframe, limit: "2000" });
  return getJson<CandlePage>(`/api/v1/candles?${params.toString()}`);
}

export function candleWebSocketUrl(symbol: string, timeframe: Timeframe): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/ws/candles/${symbol}/${timeframe}`;
}

/** Fetch market structure analysis for the given symbol / timeframe. */
export function getMarketStructure(
  symbol: string,
  timeframe: Timeframe,
): Promise<MarketStructure> {
  const params = new URLSearchParams({ symbol, timeframe });
  return getJson<MarketStructure>(`/api/v1/structure/analyze?${params.toString()}`);
}

// ── Helper type converters (Candle ↔ lightweight-charts shapes) ────────────

export function toCandleTime(candle: { open_time: string }): number {
  return Math.floor(new Date(candle.open_time).getTime() / 1000);
}

export function toCandlePoint(candle: Candle) {
  return {
    time: toCandleTime(candle) as import("lightweight-charts").UTCTimestamp,
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  };
}

export function toVolumePoint(candle: Candle) {
  return {
    time: toCandleTime(candle) as import("lightweight-charts").UTCTimestamp,
    value: Number(candle.volume),
    color: Number(candle.close) >= Number(candle.open) ? "#12b88670" : "#fa525270",
  };
}

