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

// ── Market Structure Types (Phase 2) ────────────────────────────────────────

export type SwingKind = "high" | "low";

export interface SwingPoint {
  index: number;
  timestamp: string;
  price: string;
  kind: SwingKind;
}

export type StructureEventType = "HH" | "HL" | "LH" | "LL" | "BOS" | "structure_shift";

export interface StructureEvent {
  timestamp: string;
  price: string;
  event_type: StructureEventType;
  source_swing_idx: number | null;
  confidence: number;
}

export type LiquidityLevelType =
  | "swing_high"
  | "swing_low"
  | "equal_highs"
  | "equal_lows"
  | "range_high"
  | "range_low";

export interface LiquidityLevel {
  price: string;
  level_type: LiquidityLevelType;
  strength: number;
  first_seen: string;
  last_seen: string;
  touch_count: number;
}

export type MarketRegime = "TREND_UP" | "TREND_DOWN" | "RANGE" | "UNKNOWN";

export interface MarketStructure {
  symbol: string;
  timeframe: string;
  swings: SwingPoint[];
  events: StructureEvent[];
  liquidity_levels: LiquidityLevel[];
  recent_range_high: string | null;
  recent_range_low: string | null;
  current_regime: MarketRegime;
}
