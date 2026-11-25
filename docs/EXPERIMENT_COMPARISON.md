# Experiment Comparison (Stage 3C)

Comparison is a **measurement** over backtest records that already exist. It does not
rerun a backtest, reload market candles, edit a run, or certify that a strategy is
profitable. A strategy ranking first in a comparison has merely done better on that
particular sample under those assumptions.

## Submitting a comparison

```http
POST /api/v1/backtests/compare
Content-Type: application/json

{"run_ids": ["<run-id-a>", "<run-id-b>"]}
```

- Between 2 and 10 existing run IDs are accepted.
- IDs must be non-empty single tokens, and duplicates are rejected.
- Unknown IDs return `404`; invalid requests and incompatible runs return `422`.
- The response contains only the requested runs. No other run is read into the payload.
- The endpoint inherits the project's existing research-only exposure: there is no
  authentication layer in this platform today, so it must not be published publicly.
  No new auth mechanism is introduced here.

The same operation is available in-process:

```python
from app.services.backtest.comparison import compare_runs

response = await compare_runs(session, [run_id_a, run_id_b])
```

The service reads run-level columns only. It deliberately suppresses the eager load
of the `trades` relationship and aggregates itemised costs inside the database, so a
comparison stays bounded in memory regardless of how many trades a run contains.

## What makes two runs comparable

A run is comparable with another only when every field below has the **same recorded
value**. Strategy name, strategy parameters, strategy version and random seed are
intentionally *not* on this list: they are normally the reason for a comparison and
remain visible in each result entry.

| Field | Source on the run record | Why it must match |
|---|---|---|
| `symbol` | `symbol` | Different instruments are different markets. |
| `timeframe` | `timeframe` | Bar spacing changes the execution grid and annualised statistics. |
| `period_start`, `period_end` | `period_start`, `period_end` | The historical window must be identical. |
| `dataset_fingerprint` | `dataset_version` | Both runs must have seen byte-identical candles. Matching dates alone are not enough. |
| `initial_capital` | `initial_capital` | Sizing and the PnL denominator would otherwise differ. |
| `fee_rate` | `fee_rate` | The *applied* rate is compared; `cost_scale` is already folded into it. |
| `spread_rate` | `spread_rate` | Spread assumption. |
| `slippage_rate` | `slippage_rate` | Slippage assumption. |
| `latency_bars` | `latency_bars` | The recorded fill delay is this platform's execution model. |
| `allow_short` | `parameters.allow_short` | Direction eligibility changes what the engine permitted. |
| `risk_limits` | `parameters.risk_limits` | Risk enforcement changes which trades the engine permits. |
| `run_mode` | `parameters.run_mode` / `mode` | Research may be unconstrained; other modes enforce risk. |

Values are compared by meaning, not by storage representation: UTC-aware and naive
timestamps representing the same instant are equal, and decimal values with different
trailing zeroes are equal.

### Outcomes

- **Comparable** — every field above matches. Returns `200` with `comparability:
  "comparable"`, a `shared_assumptions` map, and one entry per requested run.
- **Conditionally comparable** — a difference is understood but not normalised in
  this version (currently only `run_mode`). Returns `422` with
  `detail.category == "conditionally_comparable"`.
- **Incompatible** — a difference would make a direct reading misleading. Returns
  `422` with `detail.category == "incompatible"`.

Every rejection lists each problematic field separately in `detail.reasons`, with the
per-run values and an explanation. For example:

```json
{
  "detail": {
    "category": "incompatible",
    "reasons": [
      "fee_rate differs (run_a=0.002, run_b=0.001); compare the applied fee rate; the scale factor is already folded into it"
    ]
  }
}
```

A field that is **not recorded** (for example a run with no `dataset_version`) is
never treated as equal. It is reported as `... is not recorded ...` and rejected.
The `accounting_currency` and detailed fill model are not independently stored fields;
they are named explicitly in `unverified_assumptions` rather than silently assumed.

## Metrics and their units

`metric_basis` is `net_of_costs`. All trade-derived statistics use persisted **net**
PnL. A `null` metric means it was not persisted for that run; it is never replaced by
zero. `metric_units` in the response is the authoritative unit key.

| Field | Source | Unit / convention |
|---|---|---|
| `net_pnl` | `final_equity - initial_capital` from persisted columns | Accounting currency; exact accounting identity, net of costs. |
| `net_return` | persisted `total_return` | Fraction of initial capital (`0.05` = 5%). |
| `initial_capital`, `final_equity` | persisted columns | Accounting currency; final equity is fully realised. |
| `trade_count` | persisted `trade_count` | Count. |
| `win_rate` | persisted `win_rate` | Fraction of trades with positive net PnL (`0..1`). |
| `profit_factor` | persisted `profit_factor` | Gross winning net PnL / gross losing net PnL; `0` when there are no losses. |
| `expectancy` | persisted `expectancy` | Mean net PnL per trade in currency, **not** a percentage. |
| `average_win`, `average_loss` | persisted | Mean net PnL of winners/losers; `average_loss` is negative. |
| `average_r` | persisted `average_r` | Mean R multiple over trades that have one. |
| `max_drawdown` | persisted `max_drawdown` | Fraction below running equity peak (negative; `-0.1` = -10%). |
| `exposure` | persisted `exposure` | Fraction of equity-curve points with an open position. |
| `total_fees` | persisted `total_fees` | Sum of per-trade fees in currency; already inside net PnL. |
| `total_spread_cost`, `total_slippage_cost`, `total_latency_cost`, `total_other_costs` | Sums of the persisted per-trade columns | Currency; computed by the database, not a new cost formula. |
| `insufficient_sample` | persisted flag | When true, annualised statistics are withheld and must not be read as annual figures. |
| `sample_span_seconds` | persisted | Seconds between period start and end. |

Not available, and listed in `unavailable_metrics` rather than invented: an average
drawdown, an average per-trade return percentage, and the engine's per-candle equity curve.
Drawdown and exposure statistics derived from that curve are available; the curve itself is not
stored. The dashboard's `/experiments/{id}/curves` endpoint is a separately labelled bounded
projection of persisted closed trades, not a substitute for the engine curve
(see [EXPERIMENT_DASHBOARD.md](EXPERIMENT_DASHBOARD.md)).

## Realistic example (synthetic fixture data)

Two runs are produced from the same synthetic 80-bar BTCUSDT 5m series, with identical
capital and costs, first with `buy_and_hold` and then with `sma_trend`:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "period_start": "2024-01-01T00:00:00+00:00",
  "period_end": "2024-01-01T06:39:59.999000+00:00",
  "comparability": "comparable",
  "shared_assumptions": {
    "dataset_fingerprint": "9f2c...",
    "fee_rate": "0.001",
    "initial_capital": "10000",
    "latency_bars": "1",
    "symbol": "BTCUSDT",
    "timeframe": "5m"
  },
  "metric_basis": "net_of_costs",
  "runs": [
    {
      "run_id": "...",
      "strategy": "buy_and_hold",
      "dataset_fingerprint": "9f2c...",
      "metrics": {
        "net_pnl": 558.07,
        "net_return": 0.0558,
        "trade_count": 1,
        "win_rate": 1.0,
        "max_drawdown": -0.004,
        "total_fees": 20.6
      }
    },
    {
      "run_id": "...",
      "strategy": "sma_trend",
      "dataset_fingerprint": "9f2c...",
      "metrics": {
        "net_pnl": -49.51,
        "net_return": -0.00495,
        "trade_count": 8,
        "win_rate": 0.25,
        "max_drawdown": -0.011,
        "total_fees": 3.2
      }
    }
  ]
}
```

Read this as: *under identical data and costs, these two strategies realised these
outcomes on this sample*. It is not evidence of an edge, and it says nothing about
other periods, symbols, or market regimes. The `unverified_assumptions` and
`unavailable_metrics` lists are part of the result and should be read with it.

## Current limitations

- Conditional comparability is rejected, not normalised. Comparing across run modes
  requires creating a new set of runs with a single mode.
- The accounting currency is not a persisted column. Equality is inferred from the
  checked `symbol` match and disclosed in `unverified_assumptions`, not independently
  verified.
- The fill algorithm is a platform invariant; only the stored `latency_bars` is
  compared. A future change to the fill algorithm is not captured by a per-run field.
- `risk_limits` absence means "no risk engine" for runs written by the current
  runner. Older runs may not have recorded it; this ambiguity is disclosed.
- Comparisons are computed on demand and are not persisted. The result is a
  deterministic projection of the run records, not a new research artifact.
- Per-trade cost totals are summed from stored columns; itemised cost *rates* are the
  run-level assumptions and are shown in each run's `costs` block.

Statistical evaluation of a single run — cost sensitivity, resampled drawdowns
and the evidence it does or does not support — is documented separately in
[STRATEGY_EVALUATION.md](STRATEGY_EVALUATION.md).
