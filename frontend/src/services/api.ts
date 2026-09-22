import type { CandlePage, SystemStatus, Timeframe } from "../types/market";

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

