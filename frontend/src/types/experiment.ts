/** Hand-written mirrors of the Stage 3E API shapes (Decimal values are strings). */

export type ExperimentStatus =
  | "DRAFT"
  | "VALIDATING"
  | "REJECTED"
  | "QUEUED"
  | "RUNNING"
  | "BACKTEST_COMPLETED"
  | "EVALUATING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface EvaluationSettingsInput {
  resamples: number;
  seed: number;
  min_trades_for_inference: number;
}

export interface ExperimentSubmissionInput {
  strategy: string;
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  initial_capital: string;
  fee_rate: string;
  spread_rate: string;
  slippage_rate: string;
  latency_bars: number;
  cost_scale: string;
  allow_short: boolean;
  mode: "research";
  parameters: Record<string, unknown>;
  evaluation: EvaluationSettingsInput;
  notes: string;
  replay?: boolean;
}

export interface ExperimentRecord {
  id: string;
  strategy_name: string;
  strategy_version: string | null;
  symbol: string;
  timeframe: string;
  period_start: string;
  period_end: string;
  initial_capital: string;
  accounting_currency: string;
  configuration: Record<string, unknown>;
  configuration_fingerprint: string;
  idempotency_key: string;
  parent_experiment_id: string | null;
  status: ExperimentStatus;
  failure_stage: string | null;
  failure_reason: string | null;
  notes: string;
  dataset_version: string | null;
  engine_version: string | null;
  random_seed: number | null;
  backtest_run_id: string | null;
  evaluation_report_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentResult {
  experiment: ExperimentRecord;
  backtest_run: {
    id: string;
    strategy_name: string;
    symbol: string;
    timeframe: string;
    metrics: Record<string, unknown>;
    costs: Record<string, string | number>;
    dataset_version: string | null;
    git_commit: string | null;
    mode: string | null;
  } | null;
  evaluation_report: Record<string, unknown> | null;
}

export interface ExperimentEvaluation {
  experiment_id: string;
  report_id: string;
  report: Record<string, unknown>;
}

/** Read-only projection of persisted closed trades; never a mark-to-market curve. */
export interface ExperimentCurvePoint {
  time: string;
  equity: string | number;
  drawdown: string | number;
}

export interface ExperimentCurve {
  experiment_id: string;
  run_id: string | null;
  basis: string;
  initial_capital: string | null;
  accounting_currency: string | null;
  limit: number;
  point_count: number;
  truncated: boolean;
  unavailable_reason: string | null;
  points: ExperimentCurvePoint[];
}

export interface ComparisonRun {
  run_id: string;
  strategy: string;
  dataset_fingerprint: string | null;
  metrics: Record<string, unknown>;
}

export interface ExperimentComparison {
  experiment_ids?: string[];
  comparability: string;
  shared_assumptions: Record<string, unknown>;
  metric_basis: string;
  metric_units: Record<string, string>;
  runs: ComparisonRun[];
  unverified_assumptions: string[];
  unavailable_metrics: string[];
}
