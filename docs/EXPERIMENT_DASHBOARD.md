# Experiment results dashboard (Stage 3F)

Stage 3F is a read-only presentation layer over the Stage 3E experiment workflow. It does not
add a research method, change any stored result, or introduce execution capability. Metrics and
comparison verdicts come from the existing backend services.

## Pages

### `/experiments`

The experiment history list shows, for each stored experiment:

- experiment ID, creation time and notes;
- strategy name/version and the recorded configuration summary;
- symbol, timeframe, dataset version and backtest period;
- actual lifecycle status and failure stage/reason when present;
- whether a backtest run and evaluation report are linked, with abbreviated IDs;
- a detail link and a comparison selector.

Status, strategy, symbol, timeframe and created-after/before filters are sent to the API using
the filters it actually supports. Text search and newest/oldest/strategy sorting are applied to
that bounded response in the browser; the API itself returns newest first.

### `/experiments/:id`

The detail page reads `GET /api/v1/experiments/{id}/result` and the bounded curve endpoint. It
presents:

- identity and provenance: IDs, fingerprints, parent/replay link, dataset and engine versions,
  seed, period, accounting currency and creation/update times;
- persisted run metrics with backend-derived labels and units, including an explicit gap for
  `null` values and the `insufficient_sample` warning;
- executed cost assumptions from the run record;
- a bounded realized-equity/drawdown view when at least two points exist;
- the full stored evaluation report in stable section order, including evidence level, reasons,
  limitations, withheld claims and warnings.

Fields the backend does not record are shown as unavailable. The inline raw-JSON result panel was
removed; the detail page is the single full-result view.

### `/experiments/compare`

The comparison page sends only completed experiment IDs to `POST /api/v1/experiments/compare`.
It renders the backend response verbatim: shared assumptions, `metric_basis`, `metric_units`, each
run's persisted metrics, `unverified_assumptions` and `unavailable_metrics`. Incompatible or
conditionally comparable selections show the backend's `category` and every `detail.reasons`
entry. Each column links back to the corresponding experiment detail page. The page performs no
ranking, recalculation or profitability claim.

## Realized curve contract

`GET /api/v1/experiments/{experiment_id}/curves?limit=5000` is a bounded, read-only projection of
persisted closed trades:

| Field | Meaning |
|---|---|
| `basis` | `closed_trade_net_pnl_additive; drawdown_fraction_from_running_peak; not_engine_mark_to_market` |
| `points[].time` | Persisted trade `exit_time`; a starting point uses the run's `period_start` |
| `points[].equity` | Starting capital plus each prior trade's stored net PnL |
| `points[].drawdown` | Equity divided by the running realized peak minus one; negative fraction |
| `limit`, `point_count`, `truncated` | Request bound, returned point count and whether more trades exist |
| `unavailable_reason` | Explanation when no run, no linked run or no trades are available |

Candidate rows are selected in stored sequence order (the engine trade ID) and bounded before
they are projected; points are then ordered by exit time, with sequence breaking ties. The
default and hard maximum is 5000 points. The repository fetches at most `limit + 1` ledger rows,
so the dashboard never materialises the full trade table. The chart collapses duplicate
timestamps by keeping the last realized value instead of inventing intermediate times.

This projection is **not** the engine's per-candle equity curve. The engine curve is transient and
is not persisted with a run. The projection excludes cash, unrealized PnL, position side, intrabar
excursions and rejected signals, and it may not reproduce the persisted `max_drawdown` or
`exposure`, which were derived from per-bar points. Drawdown duration remains unavailable.

## Boundaries and limitations

- Research only: no order routing, live account, paper account, execution or threshold change.
- No discovery, optimisation or ML-based strategy selection was added.
- No production mock data is shipped; empty, failed and partial experiments show real gaps.
- The API remains unauthenticated and execution remains synchronous, as in the rest of Phase 1.
- The frontend has no browser test framework; tests cover pure presentation helpers and the exact
  API request shapes using Node's built-in test runner.
- Chart data is limited to 5000 points; full candle or full trade dumps are not exposed by this
  dashboard.
- A completed experiment or a positive realized sample is not evidence of profitability.
