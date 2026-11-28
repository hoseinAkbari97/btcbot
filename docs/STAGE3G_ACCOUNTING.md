# Stage 3G accounting audit and invariants

Baseline: `263fd18` (Stage 3F close). This document records the accounting model
that was found in the code, not an assumed model. It is the contract the Stage 3G
changes implement.

## Actual model

`BacktestEngine.run()` is a spot, single-position, no-leverage simulation.

- `cash` starts at `initial_capital`.
- A new position can only be opened while `position is None`. There is no
  pyramiding, partial reduction, margin account, borrow cost or liquidation
  engine. `CLOSE` closes the whole position.
- Entry notional is **not** debited from cash. The entry fee is debited at the
  fill; sizing reserves that fee so the notional cannot exceed cash.
- While a position is open, `unrealized = (mark - entry_price) * size * direction`
  where `direction = +1` for long and `-1` for short. The mark is the current
  candle's `close`.
- `equity = cash + unrealized`. On exit, cash is credited with the realized price
  move minus the exit fee, so once flat `cash = initial_capital + sum(net_pnl)`.
- Any position still open at the end is liquidated at the final close with
  adverse spread/slippage, and the final engine equity point is rewritten to the
  resulting cash-only state. Final equity is therefore fully realized.
- Gross PnL is measured between frictionless reference prices. Spread and
  slippage are embedded in the fill prices and recovered as costs; fees are
  charged separately. The engine deliberately splits the combined price
  concession pro rata so `fees + spread_cost + slippage_cost + latency_cost +
  other_costs == gross_pnl - net_pnl` exactly. `latency_cost` and `other_costs`
  are explicitly zero.
- `EquityPoint.drawdown` is `equity - running_peak`: a negative absolute amount in
  quote currency. `PerformanceMetrics.max_drawdown` is a negative fraction
  (`equity / peak - 1`). These are different units and must never be mixed.
- Returns are simple arithmetic fractions (`final_equity / initial_capital -
  1`); CAGR is geometric and only reported for long samples. Trade PnL is an
  absolute amount in the accounting currency.

A complete simulated trade runs: strategy decision at bar close -> pending order
with latency -> fill at a later bar's open after spread/slippage -> fee debited ->
`OpenPosition` -> per-close mark-to-market -> bracket/time/risk/signal exit ->
`Trade` settlement with gross PnL, itemised costs and net PnL -> repository run
and trade rows -> evaluation ledger and run metrics -> experiment dashboard.

## Invariants

For a newly generated run under the Stage 3G accounting version:

1. `equity = cash + unrealized` at every engine point.
2. `unrealized = 0`, `position_side is None` and `equity = cash` on the final
   point after end-of-data liquidation.
3. `initial_capital + sum(trade.net_pnl) = final_equity` (within Decimal storage
   precision).
4. For every trade, `gross_pnl - total_costs = net_pnl`.
5. `entry_fee + exit_fee = fees`, and `entry_concession + exit_concession =
   spread_cost + slippage_cost` when the new per-leg fields are present.
6. Trade `sequence` values are unique within a run; `exit_time >= entry_time`
   and `size > 0`.
7. Engine equity points are ordered by `bar_index`, unique per
   `(run_id, bar_index)` and associated with their run. A timestamp is not a
   unique key: the engine emits one point per processed candle, so candles that
   share a `close_time` legitimately produce multiple events at that timestamp.
8. The persisted terminal engine-equity point equals the persisted run
   `final_equity`.
9. Running peak starts at `initial_capital`; engine drawdown is non-positive
   quote currency, while reported `max_drawdown` is a non-positive fraction.

Legacy rows written before Stage 3G have no equity series and no per-leg cost
columns. They are reported as unavailable, never backfilled or reconstructed.

## Defects found, with evidence

1. **Gap-through exits misbooked PnL as cost.** `_intrabar_exit()` used the raw
   fill reference from `resolve_barriers()` (the gap `open`) to set the executed
   price, but `_settle()` reconstructed the frictionless reference from the
   bracket level via `_raw_exit_price()`. A gapped stop therefore understated
   gross loss; a gapped target could produce negative spread/slippage totals,
   contradicting `test_every_cost_component_is_non_negative`. Net PnL and cash
   still reconciled, but gross PnL, cost decomposition and gross R did not.
2. **Rejected pending entries skipped the bar's equity point.** The long-only
   short rejection and risk refusal used `continue` before mark-to-market, so
   equity was not appended, `_equity_index` was stale, `risk.on_bar()` was not
   called and the strategy was not consulted. This changes return, exposure and
   drawdown denominators.
3. **A stale `CLOSE` order could suppress later signals.** If a bracket or risk
   exit closed the position while a `CLOSE` order was pending, step 2 required a
   position and step 5 skipped strategy calls whenever `pending` existed. The
   pending close was never cleared.
4. **The exact engine curve was never persisted.** Only final equity and metrics
   were stored. Stage 3F's realized curve is a closed-trade projection and is
   explicitly not mark-to-market.
5. **No accounting identity tied a report to its run and ledger.** Evaluation
   had isolated warnings but no structured reconciliation status, ledger
   fingerprint, equity-series fingerprint or accounting-model version.

## Stage 3G decisions

- Fix defects 1-3 at the engine level for newly generated runs. Historical rows
  are not edited or reinterpreted.
- Persist the exact engine `EquityPoint` series in a new child table, including
  `bar_index`, raw `drawdown` currency, cash, unrealized and position side.
- Extend the ledger with nullable per-leg audit fields: `entry_fee`, `exit_fee`,
  `raw_exit_price`, `entry_concession` and `exit_concession`. Old rows keep
  `NULL`; new runs populate them.
- Record `accounting_model_version` on new runs and expose it in evaluation
  provenance. Historical runs read as `unknown`.
- Add a read-only reconciliation section to evaluation reports. Definitional
  per-trade violations and duplicate sequences are hard accounting failures for
  newly generated data; equity/ledger disagreement and legacy unavailable
  fields remain explicit warnings instead of being silently repaired.
- Expose the engine curve through a separately labelled read-only endpoint. The
  Stage 3F realized curve stays unchanged as a fallback.
- Do not change statistical methods, evidence thresholds, authorization,
  execution modes, historical results or any trading boundary.
