export type Timeframe = "5m" | "15m" | "1h" | "4h" | "1d";

export interface Candle {
  symbol: string;
  timeframe: Timeframe;
  open_time: string;
  close_time: string;
  open: string | number;
  high: string | number;
  low: string | number;
  close: string | number;
  volume: string | number;
  quote_volume: string | number | null;
  trade_count: number | null;
  taker_buy_base_volume: string | number | null;
  taker_buy_quote_volume: string | number | null;
  is_closed: boolean;
}

export interface CandlePage {
  symbol: string;
  timeframe: Timeframe;
  count: number;
  candles: Candle[];
}

export interface SystemStatus {
  status: "healthy" | "degraded";
  api: { status: "up" | "down"; detail?: string };
  database: { status: "up" | "down"; detail?: string };
  redis: { status: "up" | "down"; detail?: string };
}

