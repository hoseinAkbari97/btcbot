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
import type {
  ExperimentComparison,
  ExperimentCurve,
  ExperimentEngineCurve,
  ExperimentEvaluation,
  ExperimentRecord,
  ExperimentResult,
  ExperimentSubmissionInput,
} from "../types/experiment";

/** Keeps structured backend error details available to the comparison view. */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const record = item as { msg?: unknown };
        return typeof record?.msg === "string" ? record.msg : JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>;
    if (typeof record.reason === "string") {
      return `${String(record.stage ?? "error")}: ${record.reason}`;
    }
    if (Array.isArray(record.reasons)) {
      return record.reasons.map((reason) => String(reason)).join("; ");
    }
    return JSON.stringify(record);
  }
  return "request failed";
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    let detail: unknown = null;
    try {
      const body = (await response.json()) as { detail?: unknown };
      detail = body.detail;
      message = formatDetail(detail);
    } catch {
      // Keep the HTTP status message when the body is not JSON.
    }
    throw new ApiError(response.status, detail, message);
  }
  return (await response.json()) as T;
}

async function getJson<T>(url: string): Promise<T> {
  return requestJson<T>(url);
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

// ── Stage 3E experiment workflow ────────────────────────────────────────────

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  return requestJson<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

export function getBacktestStrategies(): Promise<string[]> {
  return getJson<string[]>("/api/v1/backtests/strategies");
}

export function submitExperiment(
  definition: ExperimentSubmissionInput,
): Promise<ExperimentRecord> {
  return postJson<ExperimentRecord>("/api/v1/experiments", definition);
}

export interface ExperimentListQuery {
  strategy?: string;
  status?: string;
  symbol?: string;
  timeframe?: string;
  createdAfter?: string;
  createdBefore?: string;
}

/** Uses only the filters the API actually supports; sorting stays client-side. */
export function listExperiments(
  limit = 50,
  query: ExperimentListQuery = {},
): Promise<ExperimentRecord[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const apiKeys: Record<keyof ExperimentListQuery, string> = {
    strategy: "strategy",
    status: "status",
    symbol: "symbol",
    timeframe: "timeframe",
    createdAfter: "created_after",
    createdBefore: "created_before",
  };
  for (const [key, value] of Object.entries(query)) {
    if (typeof value === "string" && value !== "") {
      params.set(apiKeys[key as keyof ExperimentListQuery], value);
    }
  }
  return getJson<ExperimentRecord[]>(`/api/v1/experiments?${params.toString()}`);
}

export function getExperimentResult(experimentId: string): Promise<ExperimentResult> {
  return getJson<ExperimentResult>(`/api/v1/experiments/${experimentId}/result`);
}

export function getExperimentEvaluation(
  experimentId: string,
): Promise<ExperimentEvaluation> {
  return getJson<ExperimentEvaluation>(`/api/v1/experiments/${experimentId}/evaluation`);
}

export function getExperimentCurves(
  experimentId: string,
  limit = 5000,
): Promise<ExperimentCurve> {
  const params = new URLSearchParams({ limit: String(limit) });
  return getJson<ExperimentCurve>(
    `/api/v1/experiments/${experimentId}/curves?${params.toString()}`,
  );
}

export function getExperimentEngineCurves(
  experimentId: string,
  limit = 5000,
): Promise<ExperimentEngineCurve> {
  const params = new URLSearchParams({ limit: String(limit) });
  return getJson<ExperimentEngineCurve>(
    `/api/v1/experiments/${experimentId}/engine-curves?${params.toString()}`,
  );
}

export function compareExperiments(
  experimentIds: string[],
): Promise<ExperimentComparison> {
  return postJson<ExperimentComparison>("/api/v1/experiments/compare", {
    experiment_ids: experimentIds,
  });
}

export function cancelExperiment(experimentId: string): Promise<ExperimentRecord> {
  return postJson<ExperimentRecord>(`/api/v1/experiments/${experimentId}/cancel`);
}

