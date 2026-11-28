import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { ExperimentCurveChart } from "../components/ExperimentCurveChart";
import {
  EVIDENCE_DESCRIPTIONS,
  evidenceSummary,
  formatValue,
  humanize,
  isRecord,
  metricRows,
  normalizeCurvePoints,
  normalizeEngineCurvePoints,
  reportSections,
  type JsonRecord,
} from "../lib/experiment-view";
import {
  getExperimentCurves,
  getExperimentEngineCurves,
  getExperimentResult,
} from "../services/api";
import type {
  ExperimentCurve,
  ExperimentEngineCurve,
  ExperimentResult,
} from "../types/experiment";

function unavailable(): ReactNode {
  return <span className="missing-value">Not recorded</span>;
}

function scalar(value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") return unavailable();
  if (typeof value === "number" && Number.isFinite(value)) return value.toFixed(6);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string" || typeof value === "number") return String(value);
  return <span className="missing-value">Unreadable value</span>;
}

function SectionBody({ value }: { value: unknown }) {
  if (isRecord(value)) {
    return (
      <dl className="report-details">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt>{humanize(key)}</dt>
            <dd>
              <SectionBody value={item} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }
  if (Array.isArray(value)) {
    if (value.every((item) => isRecord(item) || Array.isArray(item))) {
      return (
        <pre className="experiment-json-output">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }
    return <span>{value.map((item, index) => <span key={index}>{scalar(item)}{index < value.length - 1 ? ", " : ""}</span>)}</span>;
  }
  return <>{scalar(value)}</>;
}

interface FieldProps {
  label: string;
  value: ReactNode;
  hint?: string;
}

function Field({ label, value, hint }: FieldProps) {
  return (
    <div className="detail-field">
      <dt title={hint}>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function ExperimentDetail() {
  const { id = "" } = useParams();
  const [result, setResult] = useState<ExperimentResult | null>(null);
  const [curves, setCurves] = useState<ExperimentCurve | null>(null);
  const [engineCurves, setEngineCurves] = useState<ExperimentEngineCurve | null>(null);
  const [error, setError] = useState("");
  const [curveError, setCurveError] = useState("");
  const [engineCurveError, setEngineCurveError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setCurveError("");
    setEngineCurveError("");
    setResult(null);
    setCurves(null);
    setEngineCurves(null);
    void Promise.allSettled([
      getExperimentResult(id),
      getExperimentCurves(id),
      getExperimentEngineCurves(id),
    ]).then(([resultOutcome, curveOutcome, engineCurveOutcome]) => {
      if (!active) return;
      setLoading(false);
      if (resultOutcome.status === "fulfilled") {
        setResult(resultOutcome.value);
      } else {
        setError(
          resultOutcome.reason instanceof Error
            ? resultOutcome.reason.message
            : String(resultOutcome.reason),
        );
      }
      if (curveOutcome.status === "fulfilled") {
        setCurves(curveOutcome.value);
      } else {
        setCurveError(
          curveOutcome.reason instanceof Error
            ? curveOutcome.reason.message
            : String(curveOutcome.reason),
        );
      }
      if (engineCurveOutcome.status === "fulfilled") {
        setEngineCurves(engineCurveOutcome.value);
      } else {
        setEngineCurveError(
          engineCurveOutcome.reason instanceof Error
            ? engineCurveOutcome.reason.message
            : String(engineCurveOutcome.reason),
        );
      }
    });
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) return <main className="workspace"><p className="experiment-hint">Loading experiment…</p></main>;
  if (!result) {
    return (
      <main className="workspace">
        <Link className="back-link" to="/experiments">← Experiments</Link>
        <div className="experiment-alert error">{error || "Experiment unavailable"}</div>
      </main>
    );
  }

  const experiment = result.experiment;
  const run = result.backtest_run;
  const report = result.evaluation_report;
  const configuration: JsonRecord = isRecord(experiment.configuration) ? experiment.configuration : {};
  const evaluationConfig: JsonRecord = isRecord(configuration.evaluation) ? configuration.evaluation : {};
  const costs: JsonRecord = isRecord(run?.costs) ? run.costs : {};
  const evidence = evidenceSummary(report);
  const realizedPoints = normalizeCurvePoints(curves?.points ?? []);
  const engineCurve = normalizeEngineCurvePoints(engineCurves?.points ?? []);
  const metrics = metricRows(run?.metrics);
  const failed = experiment.status === "FAILED" || experiment.status === "REJECTED";

  return (
    <main className="workspace experiment-detail">
      <header className="topbar">
        <div>
          <Link className="back-link" to="/experiments">← Experiments</Link>
          <span className="eyebrow">EXPERIMENT DETAIL · RESEARCH ONLY</span>
          <h1>{experiment.strategy_name}</h1>
        </div>
        <div className="detail-actions">
          <span className={`status-pill ${experiment.status.toLowerCase()}`}>{experiment.status}</span>
          <Link className="secondary-link" to={`/experiments/compare?ids=${encodeURIComponent(experiment.id)}`}>
            Compare
          </Link>
        </div>
      </header>

      {failed && (
        <div className="experiment-alert error">
          {experiment.failure_stage ?? "Failure"}: {experiment.failure_reason ?? "No reason recorded"}
        </div>
      )}
      {error && <div className="experiment-alert error">{error}</div>}
      {curveError && (
        <div className="experiment-alert notice">Curve data unavailable: {curveError}</div>
      )}
      {engineCurveError && (
        <div className="experiment-alert notice">
          Engine curve data unavailable: {engineCurveError}
        </div>
      )}

      <section className="panel detail-section">
        <h2>Identity and provenance</h2>
        <p className="experiment-hint">
          Values below are stored facts. Fields the backend does not record are marked as such.
        </p>
        <dl className="detail-grid">
          <Field label="Experiment ID" value={<code>{experiment.id}</code>} />
          <Field label="Strategy" value={experiment.strategy_name} />
          <Field label="Strategy version" value={experiment.strategy_version ?? unavailable()} />
          <Field label="Parent experiment" value={experiment.parent_experiment_id ? <code>{experiment.parent_experiment_id}</code> : unavailable()} />
          <Field label="Symbol / timeframe" value={`${experiment.symbol} · ${experiment.timeframe}`} />
          <Field label="Backtest period (UTC)" value={`${experiment.period_start} → ${experiment.period_end}`} />
          <Field label="Initial capital" value={`${formatValue(experiment.initial_capital, "currency")} ${experiment.accounting_currency}`} />
          <Field label="Dataset version" value={experiment.dataset_version ?? unavailable()} />
          <Field label="Dataset fingerprint" value={run?.dataset_version ?? experiment.dataset_version ?? unavailable()} />
          <Field label="Configuration fingerprint" value={<code>{experiment.configuration_fingerprint}</code>} />
          <Field label="Engine version" value={experiment.engine_version ?? unavailable()} />
          <Field label="Random seed" value={experiment.random_seed ?? unavailable()} />
          <Field label="Created" value={experiment.created_at} />
          <Field
            label="Completion timestamp"
            value={experiment.status === "COMPLETED" ? experiment.updated_at : <span>Not recorded separately; last updated {experiment.updated_at}</span>}
          />
          <Field label="Backtest run ID" value={run ? <code>{run.id}</code> : unavailable()} />
          <Field label="Evaluation report ID" value={experiment.evaluation_report_id ? <code>{experiment.evaluation_report_id}</code> : unavailable()} />
        </dl>
        <details>
          <summary>Strategy parameters and risk configuration</summary>
          <pre className="experiment-json-output">
            {JSON.stringify(
              {
                parameters: configuration.parameters ?? {},
                risk_limits: configuration.risk_limits ?? null,
                evaluation: evaluationConfig,
                mode: configuration.mode ?? "research",
                allow_short: configuration.allow_short ?? null,
              },
              null,
              2,
            )}
          </pre>
        </details>
      </section>

      <section className="panel detail-section">
        <h2>Backtest performance</h2>
        {run ? (
          <>
            <p className="experiment-hint">
              Metrics are the persisted run values. Units come from the backend metric definitions;
              null values remain unavailable rather than becoming zero.
            </p>
            <div className="metric-grid">
              {metrics.map((metric) => (
                <div className="metric-card" key={metric.key} title={metric.description}>
                  <span>{metric.label}</span>
                  <strong>{metric.display}</strong>
                  <small>{humanize(metric.unit)}{metric.unit === "currency" ? ` · ${experiment.accounting_currency}` : ""}</small>
                </div>
              ))}
            </div>
            {run.metrics?.insufficient_sample === true && (
              <p className="experiment-hint warning">
                Short sample: annualised figures are withheld by the backend as meaningful estimates.
              </p>
            )}
            <h3>Executed cost assumptions</h3>
            <dl className="detail-grid compact">
              <Field label="Fee rate" value={formatValue(costs.fee_rate, "fraction")} />
              <Field label="Spread rate" value={formatValue(costs.spread_rate, "fraction")} />
              <Field label="Slippage rate" value={formatValue(costs.slippage_rate, "fraction")} />
              <Field label="Latency bars" value={formatValue(costs.latency_bars, "count")} />
              <Field label="Cost scale" value={formatValue(costs.cost_scale, "ratio")} />
              <Field label="Run mode" value={run.mode ?? unavailable()} />
            </dl>
          </>
        ) : (
          <p className="experiment-hint">
            No persisted backtest run for this experiment. A rejected or failed submission has no
            performance metrics.
          </p>
        )}
      </section>

      <section className="panel detail-section">
        <h2>Engine mark-to-market equity (persisted)</h2>
        <p className="experiment-hint">
          These are the exact engine-generated points, one per processed candle and keyed by
          bar_index. Equity is cash plus unrealized PnL. Drawdown is the engine&apos;s negative
          absolute {experiment.accounting_currency} amount from its running peak, not a fraction.
          The run&apos;s accounting model is {engineCurves?.accounting_model_version ?? "unknown"};
          legacy runs are not reconstructed.
        </p>
        {engineCurve.points.length >= 2 ? (
          <>
            <ExperimentCurveChart
              points={engineCurve.points}
              currency={experiment.accounting_currency}
              equityLabel="Engine mark-to-market equity"
              drawdownLabel="Drawdown from engine peak"
              drawdownUnit="currency"
            />
            {engineCurves?.truncated && (
              <p className="experiment-hint warning">
                Only the first {engineCurves.limit} of {engineCurves.total_points} persisted engine
                points are shown; the rest were not loaded.
              </p>
            )}
            {engineCurve.duplicate_timestamps > 0 && (
              <p className="experiment-hint warning">
                {engineCurve.duplicate_timestamps} engine points share a timestamp with another
                point. The chart keeps the last point at each instant; the endpoint retains every
                row under its bar_index.
              </p>
            )}
          </>
        ) : (
          <p className="experiment-hint">
            {engineCurves?.unavailable_reason ??
              "Fewer than two persisted engine points are available; no curve is drawn."}
          </p>
        )}
      </section>

      <section className="panel detail-section">
        <h2>Realized equity and drawdown</h2>
        <p className="experiment-hint">
          This legacy fallback adds each persisted net trade PnL at its exit time. It excludes
          unrealized PnL, cash, position side and intrabar excursions, and its drawdown is a
          fraction of the running realized peak, not the engine currency amount or the run's
          recorded maximum drawdown. It is retained for runs without a persisted engine curve.
        </p>
        {realizedPoints.length >= 2 ? (
          <>
            <ExperimentCurveChart
              points={realizedPoints}
              currency={experiment.accounting_currency}
            />
            {curves?.truncated && (
              <p className="experiment-hint warning">
                Only the first {curves.limit} persisted trades are shown; the remaining trades were
                not loaded.
              </p>
            )}
          </>
        ) : (
          <p className="experiment-hint">
            {curves?.unavailable_reason ?? "Fewer than two realized points are available; no curve is drawn."}
          </p>
        )}
      </section>

      <section className="panel detail-section">
        <h2>Evaluation report</h2>
        {report ? (
          <>
            <div className={`evidence-card ${evidence?.level ?? "unknown"}`}>
              <div>
                <span className="eyebrow">EVIDENCE LEVEL</span>
                <strong>{evidence?.level ?? "unknown"}</strong>
              </div>
              <p>{evidence?.description ?? EVIDENCE_DESCRIPTIONS.unknown}</p>
              {evidence?.headline && <p className="evidence-headline">{evidence.headline}</p>}
              <dl className="detail-grid compact">
                <Field label="Sample size" value={formatValue(evidence?.sampleSize, "count")} />
                <Field label="Inference threshold" value={formatValue(evidence?.threshold, "count")} />
                <Field label="Generated" value={isRecord(report) && typeof report.generated_at === "string" ? report.generated_at : unavailable()} />
              </dl>
            </div>

            {evidence && evidence.warnings.length > 0 && (
              <div className="experiment-alert warning">
                <strong>Warnings</strong>
                <ul>{evidence.warnings.map((item, index) => <li key={index}>{item}</li>)}</ul>
              </div>
            )}
            {evidence && evidence.reasons.length > 0 && (
              <div className="evidence-list">
                <strong>Why this level</strong>
                <ul>{evidence.reasons.map((item, index) => <li key={index}>{item}</li>)}</ul>
              </div>
            )}
            {evidence && evidence.withheldClaims.length > 0 && (
              <div className="evidence-list withheld">
                <strong>Claims this evaluation does not make</strong>
                <ul>{evidence.withheldClaims.map((item, index) => <li key={index}>{item}</li>)}</ul>
              </div>
            )}
            {evidence && evidence.limitations.length > 0 && (
              <details>
                <summary>Limitations</summary>
                <ul>{evidence.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>
              </details>
            )}

            {reportSections(report).map(({ key, value }) => (
              <details key={key} className="report-section" open={key === "tail_risk" || key === "sensitivity"}>
                <summary>{humanize(key)}</summary>
                <SectionBody value={value} />
              </details>
            ))}
          </>
        ) : (
          <div className="experiment-alert notice">
            No evaluation report is linked. {run ? "The successful backtest above is retained; evaluation did not complete." : "No backtest result is available either."}
            {experiment.failure_reason && <p>{experiment.failure_reason}</p>}
          </div>
        )}
      </section>
    </main>
  );
}
