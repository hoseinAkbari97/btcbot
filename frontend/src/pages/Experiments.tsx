import { useCallback, useEffect, useState } from "react";

import {
  cancelExperiment,
  compareExperiments,
  getBacktestStrategies,
  getCandles,
  getExperimentResult,
  listExperiments,
  submitExperiment,
} from "../services/api";
import type {
  ExperimentRecord,
  ExperimentResult,
  ExperimentSubmissionInput,
} from "../types/experiment";
import type { Timeframe } from "../types/market";

const TIMEFRAMES: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];
const TIMEFRAME_MS: Record<Timeframe, number> = {
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
};
const FALLBACK_STRATEGIES = ["buy_and_hold", "random", "sma_trend", "donchian_breakout"];
const CANCELLABLE = new Set(["DRAFT", "VALIDATING", "QUEUED"]);

function toInputDate(value: string | number): string {
  return new Date(value).toISOString().slice(0, 16);
}

/** datetime-local inputs carry no zone; these experiment windows are UTC. */
function toIso(value: string): string {
  return new Date(`${value}:00Z`).toISOString();
}

function display(value: unknown, digits = 4): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number" && Number.isFinite(value)) return value.toFixed(digits);
  return String(value);
}

function initialForm(): ExperimentSubmissionInput {
  const end = Date.now();
  return {
    strategy: "buy_and_hold",
    symbol: "BTCUSDT",
    timeframe: "15m",
    start: toInputDate(end - 30 * 86_400_000),
    end: toInputDate(end),
    initial_capital: "10000",
    fee_rate: "0.001",
    spread_rate: "0.0002",
    slippage_rate: "0.0001",
    latency_bars: 1,
    cost_scale: "1",
    allow_short: false,
    mode: "research",
    parameters: {},
    evaluation: { resamples: 200, seed: 7, min_trades_for_inference: 30 },
    notes: "",
  };
}

export function Experiments() {
  const [form, setForm] = useState<ExperimentSubmissionInput>(initialForm);
  const [parametersText, setParametersText] = useState("{}");
  const [strategies, setStrategies] = useState<string[]>(FALLBACK_STRATEGIES);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [result, setResult] = useState<ExperimentResult | null>(null);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [comparison, setComparison] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingResult, setLoadingResult] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setExperiments(await listExperiments(100));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }, []);

  useEffect(() => {
    void refresh();
    void getBacktestStrategies()
      .then((names) => {
        if (names.length > 0) setStrategies(names);
      })
      .catch(() => {
        // Keep the baseline fallback when the strategy endpoint is unavailable.
      });
  }, [refresh]);

  const update = <K extends keyof ExperimentSubmissionInput>(
    key: K,
    value: ExperimentSubmissionInput[K],
  ) => {
    setForm((previous) => ({ ...previous, [key]: value }));
  };

  const loadResult = useCallback(async (id: string) => {
    setLoadingResult(true);
    setError("");
    try {
      setResult(await getExperimentResult(id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setLoadingResult(false);
    }
  }, []);

  const useStoredRange = async () => {
    setError("");
    setNotice("");
    try {
      const timeframe = form.timeframe as Timeframe;
      const page = await getCandles(form.symbol, timeframe);
      if (page.candles.length < 2) {
        throw new Error(`no stored candles for ${form.symbol} ${form.timeframe}`);
      }
      const first = Date.parse(page.candles[0].open_time);
      const last = Date.parse(page.candles[page.candles.length - 1].open_time);
      setForm((previous) => ({
        ...previous,
        start: toInputDate(first),
        end: toInputDate(last + TIMEFRAME_MS[timeframe]),
      }));
      setNotice(`Loaded ${page.candles.length} stored candles as the experiment window.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  };

  const handleSubmit = async () => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const parsed: unknown = JSON.parse(parametersText || "{}");
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("strategy parameters must be a JSON object");
      }
      const start = toIso(form.start);
      const end = toIso(form.end);
      if (start >= end) throw new Error("start must be before end");
      const definition: ExperimentSubmissionInput = {
        ...form,
        start,
        end,
        parameters: parsed as Record<string, unknown>,
      };
      const created = await submitExperiment(definition);
      setNotice(`${created.status}: ${created.id}`);
      await refresh();
      await loadResult(created.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async (record: ExperimentRecord) => {
    setBusy(true);
    setError("");
    try {
      await cancelExperiment(record.id);
      setNotice(`Cancelled ${record.id}`);
      await refresh();
      await loadResult(record.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const toggleCompare = (id: string) => {
    setSelectedForCompare((previous) =>
      previous.includes(id)
        ? previous.filter((candidate) => candidate !== id)
        : previous.length < 10
          ? [...previous, id]
          : previous,
    );
  };

  const handleCompare = async () => {
    setBusy(true);
    setError("");
    setComparison("");
    try {
      const payload = await compareExperiments(selectedForCompare);
      setComparison(JSON.stringify(payload, null, 2));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const metrics = result?.backtest_run?.metrics ?? {};
  const report = result?.evaluation_report;

  return (
    <main className="workspace">
      <header className="topbar">
        <div>
          <span className="eyebrow">STAGE 3E · STRATEGY RESEARCH</span>
          <h1>Experiments</h1>
        </div>
        <div className="research-badge">RESEARCH ONLY · NO EXECUTION</div>
      </header>

      {error && <div className="experiment-alert error">{error}</div>}
      {notice && <div className="experiment-alert notice">{notice}</div>}

      <div className="experiment-layout">
        <section className="panel experiment-form">
          <h2>Define an experiment</h2>
          <p className="experiment-hint">
            The submitted definition is immutable. Repeats are served from the
            idempotency key; “replay” deliberately creates a linked new run.
          </p>
          <div className="experiment-fields">
            <label>
              Strategy
              <select
                value={form.strategy}
                onChange={(event) => update("strategy", event.target.value)}
              >
                {strategies.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Symbol
              <input
                value={form.symbol}
                onChange={(event) => update("symbol", event.target.value.toUpperCase())}
              />
            </label>
            <label>
              Timeframe
              <select
                value={form.timeframe}
                onChange={(event) => update("timeframe", event.target.value as Timeframe)}
              >
                {TIMEFRAMES.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Start (UTC)
              <input
                type="datetime-local"
                value={form.start}
                onChange={(event) => update("start", event.target.value)}
              />
            </label>
            <label>
              End (UTC, exclusive)
              <input
                type="datetime-local"
                value={form.end}
                onChange={(event) => update("end", event.target.value)}
              />
            </label>
            <label>
              Initial capital
              <input
                value={form.initial_capital}
                onChange={(event) => update("initial_capital", event.target.value)}
              />
            </label>
            <label>
              Fee rate
              <input
                value={form.fee_rate}
                onChange={(event) => update("fee_rate", event.target.value)}
              />
            </label>
            <label>
              Spread rate
              <input
                value={form.spread_rate}
                onChange={(event) => update("spread_rate", event.target.value)}
              />
            </label>
            <label>
              Slippage rate
              <input
                value={form.slippage_rate}
                onChange={(event) => update("slippage_rate", event.target.value)}
              />
            </label>
            <label>
              Latency bars
              <input
                type="number"
                min={1}
                max={10}
                value={form.latency_bars}
                onChange={(event) => update("latency_bars", Number(event.target.value))}
              />
            </label>
            <label>
              Cost scale
              <input
                value={form.cost_scale}
                onChange={(event) => update("cost_scale", event.target.value)}
              />
            </label>
            <label>
              Bootstrap resamples
              <input
                type="number"
                min={200}
                max={100000}
                value={form.evaluation.resamples}
                onChange={(event) =>
                  setForm((previous) => ({
                    ...previous,
                    evaluation: {
                      ...previous.evaluation,
                      resamples: Number(event.target.value),
                    },
                  }))
                }
              />
            </label>
            <label>
              Evaluation seed
              <input
                type="number"
                min={0}
                value={form.evaluation.seed}
                onChange={(event) =>
                  setForm((previous) => ({
                    ...previous,
                    evaluation: { ...previous.evaluation, seed: Number(event.target.value) },
                  }))
                }
              />
            </label>
          </div>
          <label className="experiment-actions-label">
            <input
              type="checkbox"
              checked={form.allow_short}
              onChange={(event) => update("allow_short", event.target.checked)}
            />
            Allow short entries
          </label>
          <label className="experiment-actions-label">
            <input
              type="checkbox"
              checked={Boolean(form.replay)}
              onChange={(event) => update("replay", event.target.checked)}
            />
            Replay (force a distinct linked run)
          </label>
          <label className="experiment-json">
            Strategy parameters (JSON object)
            <textarea
              rows={3}
              value={parametersText}
              onChange={(event) => setParametersText(event.target.value)}
            />
          </label>
          <label className="experiment-json">
            Notes
            <textarea
              rows={2}
              value={form.notes}
              onChange={(event) => update("notes", event.target.value)}
            />
          </label>
          <div className="experiment-buttons">
            <button type="button" onClick={() => void handleSubmit()} disabled={busy}>
              {busy ? "Running…" : "Run experiment"}
            </button>
            <button type="button" className="secondary" onClick={() => void useStoredRange()}>
              Use stored candle range
            </button>
          </div>
        </section>

        <section className="panel experiment-list">
          <div className="experiment-list-head">
            <h2>Experiment history</h2>
            <button type="button" className="secondary" onClick={() => void refresh()}>
              Refresh
            </button>
          </div>
          <div className="experiment-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Compare</th>
                  <th>Experiment</th>
                  <th>Strategy</th>
                  <th>Status</th>
                  <th>Run / report</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((record) => (
                  <tr
                    key={record.id}
                    className={result?.experiment.id === record.id ? "selected" : ""}
                    onClick={() => void loadResult(record.id)}
                  >
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Compare ${record.id}`}
                        checked={selectedForCompare.includes(record.id)}
                        disabled={record.backtest_run_id === null}
                        onClick={(event) => event.stopPropagation()}
                        onChange={() => toggleCompare(record.id)}
                      />
                    </td>
                    <td>
                      <code>{record.id.slice(0, 10)}</code>
                      <small>
                        {record.symbol} {record.timeframe} · {record.initial_capital}{" "}
                        {record.accounting_currency}
                      </small>
                    </td>
                    <td>{record.strategy_name}</td>
                    <td>
                      <span className={`status-pill ${record.status.toLowerCase()}`}>
                        {record.status}
                      </span>
                      {record.failure_stage && (
                        <small>
                          {record.failure_stage}: {record.failure_reason}
                        </small>
                      )}
                    </td>
                    <td>
                      <small>run {record.backtest_run_id?.slice(0, 8) ?? "—"}</small>
                      <small>report {record.evaluation_report_id?.slice(0, 8) ?? "—"}</small>
                      {CANCELLABLE.has(record.status) && (
                        <button
                          type="button"
                          className="danger"
                          disabled={busy}
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleCancel(record);
                          }}
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {experiments.length === 0 && (
                  <tr>
                    <td colSpan={5} className="empty-row">
                      No experiments yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="experiment-buttons">
            <button
              type="button"
              className="secondary"
              disabled={selectedForCompare.length !== 2 || busy}
              onClick={() => void handleCompare()}
            >
              Compare {selectedForCompare.length}/2
            </button>
          </div>
          {comparison && <pre className="experiment-json-output">{comparison}</pre>}
        </section>
      </div>

      {loadingResult && <p className="experiment-hint">Loading result…</p>}
      {result && (
        <section className="panel experiment-result">
          <h2>Result · {result.experiment.id}</h2>
          {result.backtest_run ? (
            <>
              <div className="result-grid">
                <div>
                  <span>Net return</span>
                  <strong>{display(metrics.total_return)}</strong>
                </div>
                <div>
                  <span>Trades</span>
                  <strong>{display(metrics.trade_count, 0)}</strong>
                </div>
                <div>
                  <span>Win rate</span>
                  <strong>{display(metrics.win_rate)}</strong>
                </div>
                <div>
                  <span>Max drawdown</span>
                  <strong>{display(metrics.max_drawdown)}</strong>
                </div>
                <div>
                  <span>Sharpe</span>
                  <strong>{display(metrics.sharpe)}</strong>
                </div>
                <div>
                  <span>Final equity</span>
                  <strong>{display(metrics.final_equity, 2)}</strong>
                </div>
              </div>
              {metrics.insufficient_sample === true && (
                <p className="experiment-hint warning">
                  Short sample: annualised figures are withheld as meaningful estimates.
                </p>
              )}
              <details>
                <summary>Backtest assumptions</summary>
                <pre className="experiment-json-output">
                  {JSON.stringify(result.backtest_run, null, 2)}
                </pre>
              </details>
            </>
          ) : (
            <p className="experiment-hint">No persisted backtest run for this experiment.</p>
          )}
          <details open>
            <summary>Evaluation report</summary>
            <pre className="experiment-json-output">
              {JSON.stringify(report ?? result.experiment.failure_reason, null, 2)}
            </pre>
          </details>
        </section>
      )}
    </main>
  );
}
