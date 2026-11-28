import assert from "node:assert/strict";
import test from "node:test";

import {
  ApiError,
  compareExperiments,
  getExperimentCurves,
  getExperimentEngineCurves,
  getExperimentVerification,
  listExperiments,
} from "../.test-dist/services/api.js";
import {
  comparisonFailure,
  comparisonRows,
  evidenceSummary,
  experimentConfigurationSummary,
  filterExperiments,
  formatValue,
  metricRows,
  normalizeCurvePoints,
  normalizeEngineCurvePoints,
  reportSections,
  verificationSummary,
  VERIFICATION_STATUS_DESCRIPTIONS,
} from "../.test-dist/lib/experiment-view.js";

function experiment(id, overrides = {}) {
  return {
    id,
    strategy_name: "buy_and_hold",
    strategy_version: null,
    symbol: "BTCUSDT",
    timeframe: "15m",
    period_start: "2024-01-01T00:00:00Z",
    period_end: "2024-01-02T00:00:00Z",
    initial_capital: "10000",
    accounting_currency: "USDT",
    configuration: { max_candles: 500, allow_short: false },
    configuration_fingerprint: "fingerprint",
    idempotency_key: "key",
    parent_experiment_id: null,
    status: "COMPLETED",
    failure_stage: null,
    failure_reason: null,
    notes: "",
    dataset_version: "dataset-v1",
    engine_version: null,
    random_seed: null,
    backtest_run_id: "run-1",
    evaluation_report_id: "report-1",
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
    ...overrides,
  };
}

test("formatValue uses one unit convention and preserves missing values", () => {
  assert.equal(formatValue(0.0512, "fraction"), "5.12%");
  assert.equal(formatValue("-0.1", "fraction"), "-10.00%");
  assert.equal(formatValue("1234.5", "currency"), "1,234.50");
  assert.equal(formatValue(3, "count"), "3");
  assert.equal(formatValue("1.23456", "ratio"), "1.235");
  assert.equal(formatValue(null, "currency"), "—");
  assert.equal(formatValue("not-a-number", "currency"), "not-a-number");
});

test("metricRows keeps backend keys, known units and explicit gaps", () => {
  const rows = metricRows({
    max_drawdown: "-0.08",
    trade_count: 4,
    unknown_metric: "7",
    net_pnl: null,
  });
  const byKey = Object.fromEntries(rows.map((row) => [row.key, row]));
  assert.deepEqual(
    rows.map((row) => row.key),
    ["net_pnl", "trade_count", "max_drawdown", "unknown_metric"],
  );
  assert.equal(byKey.net_pnl.display, "—");
  assert.equal(byKey.trade_count.display, "4");
  assert.equal(byKey.max_drawdown.display, "-8.00%");
  assert.equal(byKey.max_drawdown.unit, "fraction");
  assert.equal(byKey.unknown_metric.label, "Unknown Metric");
});

test("filterExperiments honours filters and sorts without fabricating fields", () => {
  const records = [
    experiment("older", { created_at: "2024-01-01T00:00:00Z", strategy_name: "sma_trend" }),
    experiment("newer", { created_at: "2024-01-05T00:00:00Z" }),
    experiment("failed", { status: "FAILED", notes: "cost data missing" }),
  ];
  const all = { status: "ALL", strategy: "ALL", symbol: "ALL", query: "", sort: "newest" };
  assert.deepEqual(
    filterExperiments(records, all).map((item) => item.id),
    ["newer", "failed", "older"],
  );
  assert.deepEqual(
    filterExperiments(records, { ...all, status: "FAILED" }).map((item) => item.id),
    ["failed"],
  );
  assert.deepEqual(
    filterExperiments(records, { ...all, sort: "oldest" }).map((item) => item.id),
    ["older", "failed", "newer"],
  );
  assert.deepEqual(
    filterExperiments(records, { ...all, query: "DATASET-V1" }).length,
    3,
  );
  assert.deepEqual(
    filterExperiments(records, { ...all, timeframe: "5m" }).map((item) => item.id),
    [],
  );
  assert.deepEqual(
    filterExperiments(records, {
      ...all,
      createdAfter: "2024-01-04T00:00:00Z",
    }).map((item) => item.id),
    ["newer"],
  );
  assert.equal(
    experimentConfigurationSummary(records[0]),
    "BTCUSDT · 15m · capital 10,000.00 USDT · max 500 candles · long only",
  );
});

test("normalizeCurvePoints handles irregular times, duplicates and invalid rows", () => {
  const points = [
    { time: "2024-01-01T02:00:00Z", equity: 103, drawdown: -0.02 },
    { time: "2024-01-01T00:00:00Z", equity: 100, drawdown: 0 },
    { time: "2024-01-01T01:00:00Z", equity: 101, drawdown: -0.01 },
    { time: "2024-01-01T01:00:00Z", equity: 102, drawdown: -0.005 },
    { time: "not-a-date", equity: 999, drawdown: 0 },
    { time: "2024-01-01T03:00:00Z", equity: null, drawdown: 0 },
  ];
  const normalized = normalizeCurvePoints(points);
  assert.deepEqual(
    normalized.map((point) => [point.time, point.equity, point.drawdown]),
    [
      [1704067200, 100, 0],
      [1704070800, 102, -0.005],
      [1704074400, 103, -0.02],
    ],
  );
  assert.equal(normalizeCurvePoints(points, 1).length, 1);
  assert.deepEqual(normalizeCurvePoints({}), []);
});

test("normalizeEngineCurvePoints keeps raw counts and flags duplicate timestamps", () => {
  const raw = [
    {
      bar_index: 2,
      time: "2024-01-01T00:00:00Z",
      equity: 103,
      cash: 103,
      unrealized: 0,
      position_side: null,
      drawdown: -5,
    },
    {
      bar_index: 0,
      time: "2024-01-01T00:00:00Z",
      equity: 100,
      cash: 100,
      unrealized: 0,
      position_side: null,
      drawdown: 0,
    },
    {
      bar_index: 1,
      time: "2024-01-01T00:00:00Z",
      equity: 101,
      cash: 100,
      unrealized: 1,
      position_side: "long",
      drawdown: -2,
    },
    {
      bar_index: 3,
      time: "2024-01-01T01:00:00Z",
      equity: 104,
      cash: 104,
      unrealized: 0,
      position_side: null,
      drawdown: 0,
    },
    { bar_index: "invalid", time: "2024-01-01T02:00:00Z", equity: 999, drawdown: 0 },
  ];
  const normalized = normalizeEngineCurvePoints(raw);
  assert.equal(normalized.raw_count, 4);
  assert.equal(normalized.duplicate_timestamps, 2);
  assert.deepEqual(
    normalized.points.map((point) => [point.time, point.equity, point.drawdown]),
    [
      [1704067200, 101, -2],
      [1704070800, 104, 0],
    ],
  );
  assert.equal(normalizeEngineCurvePoints(raw, 1).points.length, 1);
  assert.deepEqual(normalizeEngineCurvePoints({}), {
    points: [],
    raw_count: 0,
    duplicate_timestamps: 0,
  });
});

test("evidenceSummary exposes warnings and withheld claims verbatim", () => {
  const summary = evidenceSummary({
    warnings: ["dependence detected"],
    evidence: {
      level: "insufficient",
      headline: "Not enough trades",
      sample_size: 4,
      min_trades_for_inference: 30,
      reasons: ["4 trades is below the 30-trade inference threshold"],
      limitations: ["in-sample only"],
      withheld_claims: ["that the strategy is profitable"],
    },
  });
  assert.equal(summary.level, "insufficient");
  assert.match(summary.description, /no statistical claim/i);
  assert.equal(summary.sampleSize, 4);
  assert.deepEqual(summary.warnings, ["dependence detected"]);
  assert.deepEqual(summary.withheldClaims, ["that the strategy is profitable"]);
  assert.equal(evidenceSummary(null), null);
});

test("reportSections uses only stored sections in a stable order", () => {
  const sections = reportSections({ evidence: {}, performance: {}, missing: {}, trades: {} });
  assert.deepEqual(
    sections.map((section) => section.key),
    ["performance", "trades", "evidence"],
  );
});

test("comparisonRows and comparisonFailure use backend fields only", () => {
  const rows = comparisonRows({
    runs: [
      {
        run_id: "run-a",
        strategy: "buy_and_hold",
        metrics: { net_return: "0.05", trade_count: 2 },
      },
      { run_id: "run-b", strategy: "sma_trend", metrics: { net_return: "-0.01" } },
    ],
  });
  assert.equal(rows.length, 2);
  assert.equal(rows[0].strategy, "buy_and_hold");
  assert.equal(rows[0].metrics[0].key, "net_return");
  assert.equal(rows[0].metrics[0].display, "5.00%");

  const failure = comparisonFailure({
    status: 422,
    message: "incompatible",
    detail: {
      category: "incompatible",
      reasons: ["fee_rate differs (run_a=0.002, run_b=0.001)"],
    },
  });
  assert.equal(failure.category, "incompatible");
  assert.deepEqual(failure.reasons, ["fee_rate differs (run_a=0.002, run_b=0.001)"]);
});

test("frontend API helpers send bounded, explicit request shapes", async () => {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url: new URL(url, "http://test.invalid"), init });
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => ({ points: [], comparability: "comparable" }),
    };
  };
  try {
    await getExperimentCurves("exp-1", 25);
    await getExperimentEngineCurves("exp-1", 25);
    await compareExperiments(["exp-1", "exp-2"]);
    await listExperiments(10, {
      status: "COMPLETED",
      timeframe: "5m",
      createdAfter: "2024-01-04T00:00:00Z",
    });
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(calls[0].url.pathname, "/api/v1/experiments/exp-1/curves");
  assert.equal(calls[0].url.searchParams.get("limit"), "25");
  assert.equal(calls[1].url.pathname, "/api/v1/experiments/exp-1/engine-curves");
  assert.equal(calls[1].url.searchParams.get("limit"), "25");
  assert.equal(calls[2].url.pathname, "/api/v1/experiments/compare");
  assert.equal(calls[2].init.method, "POST");
  assert.deepEqual(JSON.parse(calls[2].init.body), {
    experiment_ids: ["exp-1", "exp-2"],
  });
  assert.equal(calls[3].url.searchParams.get("limit"), "10");
  assert.equal(calls[3].url.searchParams.get("status"), "COMPLETED");
  assert.equal(calls[3].url.searchParams.get("timeframe"), "5m");
  assert.equal(
    calls[3].url.searchParams.get("created_after"),
    "2024-01-04T00:00:00Z",
  );
});

test("verificationSummary preserves every explicit backend status", () => {
  const response = {
    experiment_id: "exp-1",
    status: "verified",
    identification: "fully_identified",
    manifest: { status: "verified", manifest_fingerprint: "manifest-1" },
    dataset: { status: "verified", observed_fingerprint: "dataset-1" },
    report: { status: "verified", canonical_digest: "report-1" },
    findings: ["manifest fingerprint and run/experiment links match"],
    limitations: ["does not rerun the backtest"],
  };
  const verified = verificationSummary(response);
  assert.equal(verified.status, "verified");
  assert.equal(verified.statusDescription, VERIFICATION_STATUS_DESCRIPTIONS.verified);
  assert.equal(verified.identification, "fully_identified");
  assert.equal(verified.manifestFingerprint, "manifest-1");
  assert.equal(verified.datasetFingerprint, "dataset-1");
  assert.equal(verified.canonicalDigest, "report-1");
  assert.deepEqual(verified.limitations, ["does not rerun the backtest"]);

  for (const status of Object.keys(VERIFICATION_STATUS_DESCRIPTIONS)) {
    const summary = verificationSummary({ ...response, status });
    assert.equal(summary.status, status);
    assert.equal(summary.statusDescription, VERIFICATION_STATUS_DESCRIPTIONS[status]);
  }

  const legacy = verificationSummary({ ...response, status: "partial", report: null });
  assert.equal(legacy.reportStatus, null);
  assert.equal(legacy.identification, "fully_identified");
  assert.equal(verificationSummary(null), null);
  assert.equal(verificationSummary({ status: "invented", report: {} }).status, "partial");
});

test("verification API helper targets the narrow read-only endpoint", async () => {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url: new URL(url, "http://test.invalid"), init });
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => ({
        experiment_id: "exp-1",
        status: "unavailable",
        identification: "not_reproducible",
        manifest: { status: "unavailable", available: false, detail: "none" },
        dataset: { status: "unavailable", detail: "none" },
        report: null,
        findings: [],
        limitations: [],
      }),
    };
  };
  try {
    await getExperimentVerification("exp-1");
  } finally {
    globalThis.fetch = originalFetch;
  }
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url.pathname, "/api/v1/experiments/exp-1/verification");
  assert.equal(calls[0].init, undefined);
});

test("API errors retain structured comparison rejection details", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 422,
    statusText: "Unprocessable Entity",
    json: async () => ({
      detail: {
        category: "incompatible",
        reasons: ["fee_rate differs"],
      },
    }),
  });
  try {
    await assert.rejects(
      compareExperiments(["exp-1", "exp-2"]),
      (error) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 422);
        const failure = comparisonFailure(error);
        assert.equal(failure.category, "incompatible");
        assert.deepEqual(failure.reasons, ["fee_rate differs"]);
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
