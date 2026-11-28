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

/** Exact persisted engine point: bar_index is the event key, time is not unique. */
export interface ExperimentEngineCurvePoint {
  bar_index: number;
  time: string;
  equity: string | number;
  cash: string | number;
  unrealized: string | number;
  position_side: string | null;
  drawdown: string | number;
}

export interface ExperimentEngineCurve {
  experiment_id: string;
  run_id: string | null;
  basis: string;
  accounting_model_version: string;
  accounting_currency: string | null;
  limit: number;
  total_points: number;
  point_count: number;
  truncated: boolean;
  unavailable_reason: string | null;
  points: ExperimentEngineCurvePoint[];
}

export type VerificationStatus =
  | "verified"
  | "partial"
  | "unavailable"
  | "changed"
  | "corrupted";

export type VerificationIdentification =
  | "fully_identified"
  | "partially_identified"
  | "not_reproducible";

export interface ManifestVerification {
  status: VerificationStatus;
  available: boolean;
  manifest_fingerprint: string | null;
  schema_version: string | null;
  run_id: string | null;
  experiment_id: string | null;
  fingerprint_matches: boolean | null;
  link_matches: boolean | null;
  detail: string;
}

export interface DatasetVerification {
  status: VerificationStatus;
  expected_fingerprint: string | null;
  observed_fingerprint: string | null;
  expected_candle_count: number | null;
  observed_candle_count: number | null;
  fingerprint_version: string | null;
  source_ids: string[];
  detail: string;
}

export interface ReportVerification {
  status: VerificationStatus;
  report_version: string | null;
  expected_report_version: string;
  run_id: string | null;
  expected_run_id: string;
  manifest_fingerprint: string | null;
  evaluation_method_version: string | null;
  expected_method_version: string;
  accounting_model_version: string | null;
  reconciliation_status: string | null;
  trade_ledger_fingerprint: string | null;
  equity_series_fingerprint: string | null;
  canonical_digest: string | null;
  stored_digest_matches: boolean | null;
  config_fingerprint_matches: boolean | null;
  input_fingerprint_matches: boolean | null;
  failed_checks: string[];
  detail: string;
}

/** Read-only integrity result; never a strategy or profitability verdict. */
export interface ExperimentVerification {
  experiment_id: string;
  status: VerificationStatus;
  identification: VerificationIdentification;
  manifest: ManifestVerification;
  dataset: DatasetVerification;
  report: ReportVerification | null;
  findings: string[];
  limitations: string[];
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
