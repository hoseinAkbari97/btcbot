import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  cancelExperiment,
  getBacktestStrategies,
  getCandles,
  listExperiments,
  submitExperiment,
} from "../services/api";
import type {
  ExperimentRecord,
  ExperimentSubmissionInput,
} from "../types/experiment";
import type { Timeframe } from "../types/market";
import {
  experimentConfigurationSummary,
  filterExperiments,
  type ExperimentFilters,
} from "../lib/experiment-view";

const TIMEFRAMES: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];
const TIMEFRAME_MS: Record<Timeframe, number> = {
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
};
const CANCELLABLE = new Set(["DRAFT", "VALIDATING", "QUEUED"]);

function toInputDate(value: string | number): string {
  return new Date(value).toISOString().slice(0, 16);
}

/** datetime-local inputs carry no zone; these experiment windows are UTC. */
function toIso(value: string): string {
  return new Date(`${value}:00Z`).toISOString();
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
  const navigate = useNavigate();
  const [form, setForm] = useState<ExperimentSubmissionInput>(initialForm);
  const [parametersText, setParametersText] = useState("{}");
  const [strategies, setStrategies] = useState<string[]>([]);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [filters, setFilters] = useState<ExperimentFilters>({
    status: "ALL",
    strategy: "ALL",
    symbol: "ALL",
    query: "",
    sort: "newest",
  });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setExperiments(
        await listExperiments(100, {
          strategy: filters.strategy === "ALL" ? "" : filters.strategy,
          status: filters.status === "ALL" ? "" : filters.status,
          symbol: filters.symbol === "ALL" ? "" : filters.symbol,
          timeframe: !filters.timeframe || filters.timeframe === "ALL" ? "" : filters.timeframe,
          createdAfter: filters.createdAfter ?? "",
          createdBefore: filters.createdBefore ?? "",
        }),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setLoading(false);
    }
  }, [
    filters.status,
    filters.strategy,
    filters.symbol,
    filters.timeframe,
    filters.createdAfter,
    filters.createdBefore,
  ]);

  useEffect(() => {
    void refresh();
    void getBacktestStrategies()
      .then((names) => {
        if (names.length > 0) setStrategies(names);
      })
      .catch((cause: unknown) => {
        setError(`Strategy registry unavailable: ${cause instanceof Error ? cause.message : String(cause)}`);
      });
  }, [refresh]);

  const update = <K extends keyof ExperimentSubmissionInput>(
    key: K,
    value: ExperimentSubmissionInput[K],
  ) => {
    setForm((previous) => ({ ...previous, [key]: value }));
  };

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

  const openCompare = () => {
    navigate(
      `/experiments/compare?ids=${encodeURIComponent(selectedForCompare.join(","))}`,
    );
  };

  const visibleExperiments = filterExperiments(experiments, filters);
  const strategyOptions = [...new Set(experiments.map((item) => item.strategy_name))].sort();
  const symbolOptions = [...new Set(experiments.map((item) => item.symbol))].sort();

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
                disabled={strategies.length === 0}
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
            <button type="button" onClick={() => void handleSubmit()} disabled={busy || strategies.length === 0}>
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
          <div className="experiment-filters">
            <label>
              Status
              <select
                value={filters.status}
                onChange={(event) => setFilters({ ...filters, status: event.target.value })}
              >
                <option value="ALL">All statuses</option>
                {["COMPLETED", "FAILED", "BACKTEST_COMPLETED", "REJECTED", "CANCELLED", "RUNNING"].map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </label>
            <label>
              Strategy
              <select
                value={filters.strategy}
                onChange={(event) => setFilters({ ...filters, strategy: event.target.value })}
              >
                <option value="ALL">All strategies</option>
                {strategyOptions.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>
            <label>
              Symbol
              <select
                value={filters.symbol}
                onChange={(event) => setFilters({ ...filters, symbol: event.target.value })}
              >
                <option value="ALL">All symbols</option>
                {symbolOptions.map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}
              </select>
            </label>
            <label>
              Timeframe
              <select
                value={filters.timeframe ?? "ALL"}
                onChange={(event) => setFilters({ ...filters, timeframe: event.target.value })}
              >
                <option value="ALL">All timeframes</option>
                {TIMEFRAMES.map((timeframe) => (
                  <option key={timeframe} value={timeframe}>{timeframe}</option>
                ))}
              </select>
            </label>
            <label>
              Created after (UTC)
              <input
                type="datetime-local"
                value={filters.createdAfter ? toInputDate(filters.createdAfter) : ""}
                onChange={(event) =>
                  setFilters({
                    ...filters,
                    createdAfter: event.target.value ? toIso(event.target.value) : "",
                  })
                }
              />
            </label>
            <label>
              Created before (UTC)
              <input
                type="datetime-local"
                value={filters.createdBefore ? toInputDate(filters.createdBefore) : ""}
                onChange={(event) =>
                  setFilters({
                    ...filters,
                    createdBefore: event.target.value ? toIso(event.target.value) : "",
                  })
                }
              />
            </label>
            <label>
              Search
              <input
                value={filters.query}
                placeholder="ID, notes, dataset"
                onChange={(event) => setFilters({ ...filters, query: event.target.value })}
              />
            </label>
            <label>
              Sort
              <select
                value={filters.sort}
                onChange={(event) => setFilters({ ...filters, sort: event.target.value as ExperimentFilters["sort"] })}
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="strategy">Strategy</option>
              </select>
            </label>
          </div>
          <div className="experiment-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Compare</th>
                  <th>Experiment</th>
                  <th>Strategy / configuration</th>
                  <th>Market / range</th>
                  <th>Lifecycle</th>
                  <th>Results</th>
                </tr>
              </thead>
              <tbody>
                {visibleExperiments.map((record) => (
                  <tr
                    key={record.id}
                    onClick={() => navigate(`/experiments/${record.id}`)}
                  >
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Compare ${record.id}`}
                        checked={selectedForCompare.includes(record.id)}
                        disabled={
                          record.status !== "COMPLETED" || record.backtest_run_id === null
                        }
                        onClick={(event) => event.stopPropagation()}
                        onChange={() => toggleCompare(record.id)}
                      />
                    </td>
                    <td>
                      <Link
                        to={`/experiments/${record.id}`}
                        onClick={(event) => event.stopPropagation()}
                      >
                        <code>{record.id.slice(0, 12)}</code>
                      </Link>
                      <small>Created {record.created_at}</small>
                      {record.notes && <small>Notes: {record.notes}</small>}
                    </td>
                    <td>
                      <strong>{record.strategy_name}</strong>
                      <small>{record.strategy_version ?? "version not recorded"}</small>
                      <small>{experimentConfigurationSummary(record)}</small>
                    </td>
                    <td>
                      <strong>{record.symbol} · {record.timeframe}</strong>
                      <small>
                        {record.period_start} → {record.period_end}
                      </small>
                      <small>Dataset: {record.dataset_version ?? "not recorded"}</small>
                    </td>
                    <td>
                      <span className={`status-pill ${record.status.toLowerCase()}`}>
                        {record.status}
                      </span>
                      {record.failure_stage && (
                        <small>
                          {record.failure_stage}: {record.failure_reason ?? "no reason recorded"}
                        </small>
                      )}
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
                    <td>
                      <small>
                        Backtest: {record.backtest_run_id ? "available" : "not available"}
                      </small>
                      <small>
                        Evaluation: {record.evaluation_report_id ? "available" : "not available"}
                      </small>
                      <small>
                        run {record.backtest_run_id?.slice(0, 8) ?? "—"} · report{" "}
                        {record.evaluation_report_id?.slice(0, 8) ?? "—"}
                      </small>
                    </td>
                  </tr>
                ))}
                {visibleExperiments.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-row">
                      {loading
                        ? "Loading experiments…"
                        : experiments.length === 0
                          ? "No experiments yet."
                          : "No experiments match these filters."}
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
              disabled={selectedForCompare.length < 2 || busy}
              onClick={openCompare}
            >
              Compare {selectedForCompare.length} selected
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
