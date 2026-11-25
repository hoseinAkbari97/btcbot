import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  COMPARISON_METRIC_KEYS,
  METRIC_DESCRIPTORS,
  comparisonFailure,
  comparisonRows,
  evidenceSummary,
  filterExperiments,
  formatValue,
  humanize,
  isRecord,
} from "../lib/experiment-view";
import { ApiError, compareExperiments, getExperimentResult, listExperiments } from "../services/api";
import type { ExperimentComparison, ExperimentRecord } from "../types/experiment";

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export function ExperimentCompare() {
  const [params] = useSearchParams();
  const initialIds = (params.get("ids") ?? "").split(",").filter(Boolean);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [selected, setSelected] = useState<string[]>(initialIds);
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null);
  const [evidenceLevels, setEvidenceLevels] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [failure, setFailure] = useState<ReturnType<typeof comparisonFailure> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void listExperiments(500)
      .then(setExperiments)
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      });
  }, []);

  const runComparison = useCallback(async (ids: string[]) => {
    if (ids.length < 2) return;
    setLoading(true);
    setError("");
    setFailure(null);
    setComparison(null);
    setEvidenceLevels({});
    try {
      const payload = await compareExperiments(ids);
      setComparison(payload);
      const levels = await Promise.all(
        (payload.experiment_ids ?? []).map(async (experimentId) => {
          try {
            const detail = await getExperimentResult(experimentId);
            return [experimentId, evidenceSummary(detail.evaluation_report)?.level ?? "unavailable"] as const;
          } catch {
            return [experimentId, "unavailable"] as const;
          }
        }),
      );
      setEvidenceLevels(Object.fromEntries(levels));
    } catch (cause) {
      const parsed = comparisonFailure(cause);
      if (cause instanceof ApiError && cause.status === 422) {
        setFailure(parsed);
      } else {
        setError(cause instanceof Error ? cause.message : String(cause));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialIds.length >= 2) void runComparison(initialIds);
    // The initial query is the sole trigger; later selection is explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runComparison]);

  const completed = filterExperiments(
    experiments.filter((item) => item.status === "COMPLETED" && item.backtest_run_id),
    { status: "COMPLETED", strategy: "ALL", symbol: "ALL", query: "", sort: "newest" },
  );
  const rows = comparisonRows(comparison);
  const experimentIds = comparison?.experiment_ids ?? [];

  const toggle = (id: string) => {
    setSelected((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : previous.length < 10
          ? [...previous, id]
          : previous,
    );
  };

  return (
    <main className="workspace experiment-compare">
      <header className="topbar">
        <div>
          <Link className="back-link" to="/experiments">← Experiments</Link>
          <span className="eyebrow">COMPARISON · RESEARCH ONLY</span>
          <h1>Compare experiments</h1>
        </div>
        <div className="research-badge">NO RANKING CLAIM</div>
      </header>

      <p className="experiment-hint">
        Comparison is computed by the existing backend service from persisted runs. It does not
        rerun a backtest, recalculate metrics here, or establish profitability. Select compatible
        completed experiments; the backend explains any mismatch.
      </p>

      {error && <div className="experiment-alert error">{error}</div>}
      {failure && (
        <div className="experiment-alert error">
          <strong>Compatibility: <code>{failure.category}</code></strong>
          {failure.message && <p>{failure.message}</p>}
          {failure.reasons.length > 0 && (
            <ul>{failure.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
          )}
        </div>
      )}

      <div className="compare-layout">
        <section className="panel compare-selector">
          <h2>Completed experiments</h2>
          <div className="compare-list">
            {completed.map((record) => (
              <label key={record.id} className="compare-option">
                <input
                  type="checkbox"
                  checked={selected.includes(record.id)}
                  onChange={() => toggle(record.id)}
                />
                <span>
                  <code>{record.id.slice(0, 10)}</code>
                  <strong>{record.strategy_name}</strong>
                  <small>{record.symbol} · {record.timeframe} · {record.created_at}</small>
                </span>
              </label>
            ))}
            {completed.length === 0 && <p className="experiment-hint">No completed experiments are stored yet.</p>}
          </div>
          <div className="experiment-buttons">
            <button
              type="button"
              disabled={selected.length < 2 || loading}
              onClick={() => void runComparison(selected)}
            >
              {loading ? "Comparing…" : `Compare ${selected.length} selected`}
            </button>
          </div>
        </section>

        <section className="panel compare-results">
          <h2>Backend comparison</h2>
          {!comparison && !loading && (
            <p className="experiment-hint">Select at least two completed experiments to begin.</p>
          )}
          {loading && <p className="experiment-hint">Loading comparison…</p>}
          {comparison && (
            <>
              <div className="comparison-summary">
                <span className="status-pill">{comparison.comparability}</span>
                <span>Metric basis: {comparison.metric_basis}</span>
              </div>
              <div className="experiment-table-wrap">
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Metric</th>
                      {rows.map((row, index) => (
                        <th key={row.runId || index}>
                          {experimentIds[index] ? (
                            <Link to={`/experiments/${experimentIds[index]}`}>{row.strategy}</Link>
                          ) : (
                            row.strategy
                          )}
                          <small>run {row.runId ? row.runId.slice(0, 8) : "—"}</small>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {COMPARISON_METRIC_KEYS.map((key) => {
                      const descriptor = METRIC_DESCRIPTORS[key];
                      return (
                        <tr key={key}>
                          <th title={descriptor.description}>{descriptor.label}</th>
                          {rows.map((row) => {
                            const metric = row.metrics.find((item) => item.key === key);
                            const unit =
                              comparison.metric_units[key] ?? descriptor.unit;
                            return (
                              <td key={`${row.runId}-${key}`}>
                                {metric
                                  ? formatValue(
                                      metric.raw,
                                      unit as Parameters<typeof formatValue>[1],
                                    )
                                  : "—"}
                                <small>{humanize(unit)}</small>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                    <tr>
                      <th>Evidence level</th>
                      {experimentIds.map((id) => (
                        <td key={id}>
                          {evidenceLevels[id] ?? "unavailable"}
                          <small><Link to={`/experiments/${id}`}>Open report</Link></small>
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
              <details open>
                <summary>Shared assumptions and disclosed gaps</summary>
                <dl className="report-details">
                  {Object.entries(
                    isRecord(comparison.shared_assumptions) ? comparison.shared_assumptions : {},
                  ).map(([key, value]) => (
                    <div key={key}>
                      <dt>{humanize(key)}</dt>
                      <dd>{String(value)}</dd>
                    </div>
                  ))}
                </dl>
                <p className="experiment-hint warning">Unverified assumptions</p>
                <ul>{stringList(comparison.unverified_assumptions).map((item, index) => <li key={index}>{item}</li>)}</ul>
                <p className="experiment-hint warning">Unavailable metrics</p>
                <ul>{stringList(comparison.unavailable_metrics).map((item, index) => <li key={index}>{item}</li>)}</ul>
              </details>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
