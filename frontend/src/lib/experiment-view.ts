/**
 * Pure presentation helpers for the experiment dashboard.
 *
 * These functions only format and arrange values that already came from the
 * backend. They never derive research metrics, rank strategies, or invent
 * provenance; keeping that boundary here makes the dashboard testable without
 * a browser test framework.
 */

import type { ExperimentRecord } from "../types/experiment";

export type JsonRecord = Record<string, unknown>;

export interface MetricDescriptor {
  label: string;
  unit: "currency" | "fraction" | "count" | "ratio" | "number" | "text";
  description: string;
}

/** Backend keys are the authority; labels and units only explain them. */
export const METRIC_DESCRIPTORS: Record<string, MetricDescriptor> = {
  net_pnl: {
    label: "Net PnL",
    unit: "currency",
    description: "Final equity minus initial capital, after persisted costs.",
  },
  total_return: {
    label: "Net return",
    unit: "fraction",
    description: "Persisted total return as a fraction of initial capital.",
  },
  net_return: {
    label: "Net return",
    unit: "fraction",
    description: "Persisted net return as a fraction of initial capital.",
  },
  trade_count: {
    label: "Trades",
    unit: "count",
    description: "Number of persisted closed trades.",
  },
  win_rate: {
    label: "Win rate",
    unit: "fraction",
    description: "Fraction of trades with positive net PnL.",
  },
  profit_factor: {
    label: "Profit factor",
    unit: "ratio",
    description: "Gross winning net PnL divided by gross losing net PnL.",
  },
  expectancy: {
    label: "Expectancy",
    unit: "currency",
    description: "Mean net PnL per trade, in the accounting currency.",
  },
  average_win: {
    label: "Average winner",
    unit: "currency",
    description: "Mean positive net PnL of winning trades.",
  },
  average_loss: {
    label: "Average loser",
    unit: "currency",
    description: "Mean negative net PnL of losing trades.",
  },
  max_drawdown: {
    label: "Maximum drawdown",
    unit: "fraction",
    description: "Largest persisted decline below the equity peak, as a fraction.",
  },
  final_equity: {
    label: "Final equity",
    unit: "currency",
    description: "Persisted final account value after all closed trades.",
  },
  total_fees: {
    label: "Fees",
    unit: "currency",
    description: "Sum of persisted per-trade fees; already inside net PnL.",
  },
  total_spread_cost: {
    label: "Spread cost",
    unit: "currency",
    description: "Sum of persisted spread costs; already inside net PnL.",
  },
  total_slippage_cost: {
    label: "Slippage cost",
    unit: "currency",
    description: "Sum of persisted slippage costs; already inside net PnL.",
  },
  total_latency_cost: {
    label: "Latency cost",
    unit: "currency",
    description: "Sum of persisted latency costs; already inside net PnL.",
  },
  total_other_costs: {
    label: "Other costs",
    unit: "currency",
    description: "Sum of other persisted costs; already inside net PnL.",
  },
  sharpe: {
    label: "Sharpe",
    unit: "ratio",
    description: "Persisted risk-adjusted statistic; null when the sample is too short.",
  },
  sortino: {
    label: "Sortino",
    unit: "ratio",
    description: "Persisted downside risk-adjusted statistic.",
  },
  calmar: {
    label: "Calmar",
    unit: "ratio",
    description: "Persisted return-to-drawdown statistic.",
  },
  exposure: {
    label: "Exposure",
    unit: "fraction",
    description: "Fraction of observed curve points with an open position.",
  },
};

export const COMPARISON_METRIC_KEYS = [
  "net_return",
  "net_pnl",
  "max_drawdown",
  "trade_count",
  "win_rate",
  "profit_factor",
  "expectancy",
  "total_fees",
] as const;

export function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function humanize(key: string): string {
  return key
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function asFiniteNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

/** Decimal values arrive as strings; formatting never changes their source. */
export function formatValue(value: unknown, unit: MetricDescriptor["unit"]): string {
  if (value === null || value === undefined || value === "") return "—";
  const number = asFiniteNumber(value);
  if (number === null) return String(value);
  if (unit === "fraction") return `${(number * 100).toFixed(2)}%`;
  if (unit === "currency") {
    return number.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (unit === "count") return number.toFixed(0);
  if (unit === "ratio") return number.toFixed(3);
  return number.toFixed(4);
}

export interface MetricRow extends MetricDescriptor {
  key: string;
  display: string;
  raw: unknown;
}

/** Known metrics first, then any additional backend keys in stable order. */
export function metricRows(metrics: unknown): MetricRow[] {
  if (!isRecord(metrics)) return [];
  const keys = [
    ...Object.keys(METRIC_DESCRIPTORS).filter((key) => key in metrics),
    ...Object.keys(metrics)
      .filter((key) => !(key in METRIC_DESCRIPTORS))
      .sort(),
  ];
  return keys.map((key) => {
    const descriptor = METRIC_DESCRIPTORS[key] ?? {
      label: humanize(key),
      unit: "number" as const,
      description: "Backend metric; unit is shown only when the backend records it.",
    };
    return { key, ...descriptor, display: formatValue(metrics[key], descriptor.unit), raw: metrics[key] };
  });
}

export interface ExperimentFilters {
  status: string;
  strategy: string;
  symbol: string;
  timeframe?: string;
  createdAfter?: string;
  createdBefore?: string;
  query: string;
  sort: "newest" | "oldest" | "strategy";
}

export function filterExperiments(
  records: ExperimentRecord[],
  filters: ExperimentFilters,
): ExperimentRecord[] {
  const query = filters.query.trim().toLowerCase();
  const filtered = records.filter((record) => {
    if (filters.status !== "ALL" && record.status !== filters.status) return false;
    if (filters.strategy !== "ALL" && record.strategy_name !== filters.strategy) return false;
    if (filters.symbol !== "ALL" && record.symbol !== filters.symbol) return false;
    if (filters.timeframe && filters.timeframe !== "ALL" && record.timeframe !== filters.timeframe) {
      return false;
    }
    const created = Date.parse(record.created_at);
    const after = filters.createdAfter ? Date.parse(filters.createdAfter) : NaN;
    const before = filters.createdBefore ? Date.parse(filters.createdBefore) : NaN;
    if (Number.isFinite(after) && created < after) return false;
    if (Number.isFinite(before) && created > before) return false;
    if (!query) return true;
    return [record.id, record.strategy_name, record.notes, record.dataset_version ?? ""]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
  return filtered.sort((left, right) => {
    if (filters.sort === "strategy") {
      return left.strategy_name.localeCompare(right.strategy_name) || left.created_at.localeCompare(right.created_at);
    }
    const direction = filters.sort === "oldest" ? 1 : -1;
    return direction * left.created_at.localeCompare(right.created_at);
  });
}

/** Only values recorded on the experiment are described; gaps stay explicit. */
export function experimentConfigurationSummary(record: ExperimentRecord): string {
  const configuration = isRecord(record.configuration) ? record.configuration : {};
  const parts = [
    record.symbol,
    record.timeframe,
    `capital ${formatValue(record.initial_capital, "currency")} ${record.accounting_currency}`,
  ];
  if (typeof configuration.max_candles === "number") {
    parts.push(`max ${configuration.max_candles} candles`);
  }
  if (typeof configuration.allow_short === "boolean") {
    parts.push(configuration.allow_short ? "shorts enabled" : "long only");
  }
  return parts.join(" · ");
}

export interface CurvePoint {
  time: number;
  iso: string;
  equity: number;
  drawdown: number;
}

/**
 * Chart-safe points from the bounded curve response. Duplicate timestamps are
 * collapsed by taking the last value at that instant rather than shifting data
 * onto artificial times.
 */
export function normalizeCurvePoints(value: unknown, limit = 5000): CurvePoint[] {
  if (!Array.isArray(value)) return [];
  const byTime = new Map<number, CurvePoint>();
  for (const item of value) {
    if (!isRecord(item)) continue;
    const iso = typeof item.time === "string" ? item.time : "";
    const time = Date.parse(iso) / 1000;
    const equity = asFiniteNumber(item.equity);
    const drawdown = asFiniteNumber(item.drawdown);
    if (!iso || !Number.isFinite(time) || equity === null || drawdown === null) continue;
    byTime.set(Math.floor(time), { time: Math.floor(time), iso, equity, drawdown });
  }
  return [...byTime.values()].sort((a, b) => a.time - b.time).slice(0, Math.max(0, limit));
}

export interface NormalizedEngineCurve {
  /** Chart-safe points; duplicate timestamps keep only the last bar_index. */
  points: CurvePoint[];
  /** Valid raw points received from the bounded endpoint, before time de-duplication. */
  raw_count: number;
  /** Number of raw points that could not share one timestamp on the chart. */
  duplicate_timestamps: number;
}

/**
 * Normalize exact engine points without inventing positions in time.
 *
 * The endpoint keys rows by bar_index because timestamps may repeat, while the
 * chart needs one value per instant. Raw rows stay available for inspection,
 * and the number of collisions is reported rather than silently discarded.
 */
export function normalizeEngineCurvePoints(
  value: unknown,
  limit = 5000,
): NormalizedEngineCurve {
  if (!Array.isArray(value)) {
    return { points: [], raw_count: 0, duplicate_timestamps: 0 };
  }
  const byBar = new Map<number, CurvePoint>();
  for (const item of value) {
    if (!isRecord(item)) continue;
    const barIndex = asFiniteNumber(item.bar_index);
    const iso = typeof item.time === "string" ? item.time : "";
    const time = Date.parse(iso) / 1000;
    const equity = asFiniteNumber(item.equity);
    const drawdown = asFiniteNumber(item.drawdown);
    if (barIndex === null || !Number.isInteger(barIndex) || !iso) continue;
    if (!Number.isFinite(time) || equity === null || drawdown === null) continue;
    byBar.set(barIndex, {
      time: Math.floor(time),
      iso,
      equity,
      drawdown,
    });
  }
  const byTime = new Map<number, CurvePoint>();
  for (const point of [...byBar.values()].sort((a, b) => a.iso.localeCompare(b.iso))) {
    byTime.set(point.time, point);
  }
  const bounded = [...byTime.values()]
    .sort((a, b) => a.time - b.time)
    .slice(0, Math.max(0, limit));
  return {
    points: bounded,
    raw_count: byBar.size,
    duplicate_timestamps: byBar.size - byTime.size,
  };
}

export const EVIDENCE_DESCRIPTIONS: Record<string, string> = {
  insufficient:
    "Too few trades or a fragile result: no statistical claim is made beyond describing this sample.",
  descriptive:
    "The sample can be described, but fragility or dependence prevents an interval being presented as informative.",
  conditional_inference:
    "Intervals are reported for this sample only, under the recorded assumptions. This is not proof of profitability.",
};

export interface EvidenceSummary {
  level: string;
  description: string;
  headline: string | null;
  sampleSize: unknown;
  threshold: unknown;
  reasons: string[];
  warnings: string[];
  limitations: string[];
  withheldClaims: string[];
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export function evidenceSummary(report: unknown): EvidenceSummary | null {
  if (!isRecord(report)) return null;
  const evidence = isRecord(report.evidence) ? report.evidence : {};
  const level = typeof evidence.level === "string" ? evidence.level : "unknown";
  return {
    level,
    description: EVIDENCE_DESCRIPTIONS[level] ?? "The report did not record a recognised evidence level.",
    headline: typeof evidence.headline === "string" ? evidence.headline : null,
    sampleSize: evidence.sample_size ?? null,
    threshold: evidence.min_trades_for_inference ?? null,
    reasons: stringList(evidence.reasons),
    warnings: stringList(report.warnings),
    limitations: stringList(evidence.limitations),
    withheldClaims: stringList(evidence.withheld_claims),
  };
}

export const REPORT_SECTIONS = [
  "provenance",
  "performance",
  "trades",
  "tail_risk",
  "sensitivity",
  "segments",
  "simulation",
  "evidence",
  "ledger",
] as const;

/** Sections are read from the stored report in this order; absent means absent. */
export function reportSections(report: unknown): Array<{ key: string; value: JsonRecord }> {
  if (!isRecord(report)) return [];
  return REPORT_SECTIONS.filter((key) => isRecord(report[key])).map((key) => ({
    key,
    value: report[key] as JsonRecord,
  }));
}

export const VERIFICATION_STATUS_DESCRIPTIONS: Record<string, string> = {
  verified: "Recorded inputs and outputs match their stored fingerprints.",
  partial: "Some evidence is recorded, but identity or integrity is incomplete.",
  unavailable: "The evidence was not recorded and has not been reconstructed.",
  changed: "Current stored evidence differs from the recorded fingerprint.",
  corrupted: "A stored record could not be read as the expected structure.",
};

export interface VerificationSummary {
  status: string;
  statusDescription: string;
  identification: string;
  manifestStatus: string;
  datasetStatus: string;
  reportStatus: string | null;
  manifestFingerprint: string | null;
  datasetFingerprint: string | null;
  canonicalDigest: string | null;
  findings: string[];
  limitations: string[];
}

function verificationStatus(value: unknown): string | null {
  return typeof value === "string" && value in VERIFICATION_STATUS_DESCRIPTIONS
    ? value
    : null;
}

/** Pure view of the backend verification response; no status is invented. */
export function verificationSummary(payload: unknown): VerificationSummary | null {
  if (!isRecord(payload)) return null;
  const manifest = isRecord(payload.manifest) ? payload.manifest : {};
  const dataset = isRecord(payload.dataset) ? payload.dataset : {};
  const report = isRecord(payload.report) ? payload.report : null;
  const status =
    verificationStatus(payload.status) ??
    (report === null ? "unavailable" : "partial");
  const identification =
    payload.identification === "fully_identified" ||
    payload.identification === "partially_identified" ||
    payload.identification === "not_reproducible"
      ? payload.identification
      : "not_reproducible";

  return {
    status,
    statusDescription: VERIFICATION_STATUS_DESCRIPTIONS[status],
    identification,
    manifestStatus: verificationStatus(manifest.status) ?? "unavailable",
    datasetStatus: verificationStatus(dataset.status) ?? "unavailable",
    reportStatus: report === null ? null : verificationStatus(report.status) ?? "unavailable",
    manifestFingerprint:
      typeof manifest.manifest_fingerprint === "string" ? manifest.manifest_fingerprint : null,
    datasetFingerprint:
      typeof dataset.observed_fingerprint === "string" ? dataset.observed_fingerprint : null,
    canonicalDigest:
      report !== null && typeof report.canonical_digest === "string"
        ? report.canonical_digest
        : null,
    findings: stringList(payload.findings),
    limitations: stringList(payload.limitations),
  };
}

export interface ComparisonRow {
  runId: string;
  strategy: string;
  metrics: MetricRow[];
}

export function comparisonRows(payload: unknown): ComparisonRow[] {
  if (!isRecord(payload) || !Array.isArray(payload.runs)) return [];
  return payload.runs.filter(isRecord).map((run) => ({
    runId: typeof run.run_id === "string" ? run.run_id : "",
    strategy: typeof run.strategy === "string" ? run.strategy : "—",
    metrics: metricRows(run.metrics),
  }));
}

export interface ComparisonFailure {
  category: string;
  reasons: string[];
  message: string;
}

/** Preserve the backend's compatibility explanation instead of flattening it. */
export function comparisonFailure(error: unknown): ComparisonFailure {
  const record = error as { message?: unknown; detail?: unknown; status?: unknown } | null;
  const detail = isRecord(record?.detail) ? record.detail : {};
  return {
    category: typeof detail.category === "string" ? detail.category : "error",
    reasons: stringList(detail.reasons),
    message: typeof record?.message === "string" ? record.message : "Comparison failed",
  };
}
