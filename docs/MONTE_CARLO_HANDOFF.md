# Monte Carlo Handoff Specification

The contract between this platform's backtester and the downstream Monte Carlo /
quantitative-risk project.

This document describes **what the Monte Carlo project receives**, what each field
means, and the assumptions it is entitled to rely on. It is written to be read by
whoever builds that project — it does not require them to know anything about this
codebase.

---

## 1. Source of the data

Rows are produced by `Trade.as_monte_carlo_row()` in
`backend/app/services/backtest/engine.py`. That method is the **single definition** of
the handoff schema. Changing a key there is a breaking change to the downstream
contract and must be deliberate.

Every row is one **closed simulated trade** from one backtest run.

## 2. Required context (one record per experiment, not per trade)

The Monte Carlo project must not receive a bare list of R values. A distribution
without its generation process cannot be resampled honestly. Carry this metadata
alongside the trade rows:

| Field | Source |
|---|---|
| `experiment_id` | `BacktestRunRecord.id` |
| `dataset_version` | dataset content hash (`manifest.json` → `sha256`) |
| `data_start` / `data_end`, `symbol`, `timeframe` | `BacktestRunRecord` |
| `strategy_name`, `strategy_version` | per-trade, but aggregate per run |
| `git_commit` | captured at run time (`runner.py`) |
| `parameters` | strategy parameter snapshot |
| `cost_config`, `risk_config` | cost/risk configuration as executed |
| `seed` | where the strategy is stochastic |
| `trade_count` | run total |

A backtest that cannot be reproduced from these fields is not a valid input.

## 3. The row schema

`net_R` is the primary field. `gross_R` is retained so cost sensitivity can be
re-derived without a re-run.

| Field | Type | Meaning |
|---|---|---|
| `trade_id` | str | Stable id, unique within a run |
| `symbol`, `timeframe` | str | Market the trade was simulated on |
| `side` | str | `long` / `short` |
| `signal_time` | datetime | When the strategy decided |
| `entry_time` | datetime | Fill time. Always **strictly after** `signal_time` |
| `exit_time` | datetime | Fill time of the closing fill |
| `entry_price`, `exit_price` | Decimal | Actual fills, **after** spread and slippage |
| `size` | Decimal | Position size in base units |
| `net_R` | Decimal\|None | `net_pnl / risk_amount`. **The field to resample** |
| `gross_R` | Decimal\|None | `gross_pnl / risk_amount`, before costs |
| `net_pnl` | Decimal | Price move minus all costs |
| `gross_pnl` | Decimal | Price movement only |
| `fees` | Decimal | Commission, entry + exit |
| `spread_cost` | Decimal | Half-spread paid at each fill |
| `slippage_cost` | Decimal | Slippage concession at each fill |
| `total_costs` | Decimal | Sum of all cost components |
| `MAE`, `MFE` | Decimal\|None | Excursions **expressed in R** |
| `mae_price`, `mfe_price` | Decimal\|None | Same excursions in price terms |
| `holding_seconds`, `bars_held` | float / int | Trade duration |
| `exit_reason` | str | `stop` / `target` / `signal` / `end_of_data` / … |
| `sizing_model` | str | `risk` / `capital` / `exposure` — see §4 |
| `risk_amount` | Decimal\|None | `1R` in currency. `None` for non-stop trades |
| `risk_fraction` | Decimal\|None | `risk_amount / equity_at_entry` |
| `initial_stop`, `initial_target` | Decimal\|None | Set at entry; never moved |
| `market_regime` | str | Regime label in force during the trade |
| `strategy_name`, `strategy_version` | str | Provenance |
| `strategy_context` | dict | Strategy-specific extras |

### Invariants the receiver may rely on

- `fees + spread_cost + slippage_cost + latency_cost + other_costs == total_costs`
- `gross_pnl - total_costs == net_pnl` (exact, to the cent)
- `gross_pnl - net_pnl == total_costs` (both directions)
- `entry_time > signal_time` — **no trade is filled on the bar that produced it.**
  A violated row means a lookahead defect upstream; treat the run as suspect.
- `net_R == net_pnl / risk_amount` wherever `risk_amount` is set.

## 4. Handling `None` R — the one thing to get right

`net_R` is `None` when `sizing_model != risk`, i.e. the trade had **no stop**, so no
monetary risk and no R exist.

This is not a data-quality defect. Converting such a trade into R by, say, dividing by
notional would fabricate a risk definition the strategy never used.

Correct handling:

- **Resample only rows with a non-null `net_R`.**
- Filter on `sizing_model == "risk"` to be explicit rather than relying on nullness.
- Do **not** mix allocation-sized benchmark trades (buy & hold, SMA, Donchian) into a
  stop-based R distribution. They answer a different question and will distort the
  tails that the Monte Carlo project exists to measure.

## 5. What this handoff deliberately does not contain

- **Equity curve / drawdown path.** Monte Carlo resampling of trades ignores path;
  modelling drawdown from a resampled trade sequence is the downstream project's job.
- **Optimised parameters.** Parameters here are the ones the run actually used. They
  were not tuned on the test set; if a later phase tunes them, that experiment is a
  *different* record with its own id and must be labelled as such.
- **Live fills.** All rows are simulated. Nobitex execution characteristics are not yet
  represented, so a resampled distribution inherits Binance-shaped costs.

## 6. Known limitations the receiver must carry forward

1. **Fill model is bar-resolution.** A fill happens at the open of the next bar, with a
   concession. Intra-bar path is unknown, so stops and targets within one candle are
   resolved conservatively (stop assumed first). MFE/MAE within a bar are therefore
   approximations from OHLC extremes, not tick-accurate.
2. **Costs are constant-rate.** `fee_rate` / `spread_rate` / `slippage_rate` are flat
   scalars. They do not widen with volatility or size. `CostConfig.scaled()` exists for
   sensitivity analysis — use it rather than assuming the base case.
3. **Research vs execution market differ.** History and costs are Binance BTC/USDT.
   Nobitex spreads, depth and fees differ. Treat every result as an upper bound until
   Nobitex-specific costs are plugged into the same interfaces.
4. **Sample size.** Trade counts from a single parameter set are typically in the
   hundreds. The downstream project should bootstrap from the empirical distribution
   directly rather than fitting a parametric one.
5. **Regime conditioning is coarse.** `market_regime` is a label, not a probability.
   Resampling *within* regime is possible; the regime model itself is not validated.
