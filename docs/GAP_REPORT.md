# Phase 1–5 Research Hardening — Implementation Gap Report

Written before any code was changed, against commit `1cd95d9` (143 tests passing).

## Verdict

The **backtester** is already trustworthy. The **market-structure engine is not** — it
contains a systemic lookahead bias that makes every structure-derived feature unusable
for research. There is no event→outcome capability at all, which is the single most
important missing piece.

---

## A. What is already correct — do not touch

| Area | Evidence |
|---|---|
| Strategy history truncation | `engine.py:448` passes `self.candles[: index + 1]`. Leakage is structurally impossible, not merely discouraged. |
| Execution never precedes signal | `engine.py:195` rejects `latency_bars < 1`; fill is always a *later* bar's open (`engine.py:371`). |
| OHLC ambiguity | `engine.py:529` resolves a stop/target tie conservatively (stop first). Correct default. |
| Cost separation | `costs.py` keeps `fee_rate` / `spread_rate` / `slippage_rate` / `latency_bars` as distinct fields. `scaled()` supports sensitivity analysis. |
| Sizing formula | `_size_for` implements `risk_amount / stop_distance` correctly, reserving the entry fee. |
| Annualisation guard | `metrics.py:35,177,192` refuses CAGR/Sharpe annualisation below a 30-day span. Exactly the required protection. |
| Data validation | `validation.py` covers duplicates, gaps, overlap, OHLC relations, negative volume, tz-awareness, boundary alignment, ordering. |
| Baseline strategies | All four exist with an explicitly seeded RNG (`baselines.py:79`). |
| Reproducibility baseline | `runner.py:41` captures git commit; `BacktestRunRecord` stores cost, parameter, dataset and model version columns. |
| Risk engine separation | `risk.py` is a gate outside strategy logic; it clamps strategy requests rather than trusting them. |

These satisfy requirements 7, 12, 17 and 18 substantially. The work below is additive.

---

## B. Gaps — ranked by severity

### CRITICAL

**B1. Systemic lookahead in market structure.** `analysis.py:40` computes a swing at bar
`i` by comparing against bars `i-lookback … i+lookback`. The `lookback` bars to the
*right* do not exist at bar `i`. No confirmation timestamp is stored, so a consumer
cannot tell which swings were knowable when. This leak propagates into HH/HL/LH/LL, BOS
(`_detect_bos`), structure shift, and liquidity levels. **Nothing in the structure
pipeline is currently usable for research.**

**B2. No confirmation timestamps anywhere.** `SwingPoint`, `StructureEvent`,
`LiquidityLevel` carry a single `timestamp` = the bar the thing happened. There is no
`confirmation_time`, so requirement 2's distinction between *event time* and *information
time* cannot be represented, let alone enforced.

**B3. Non-causal liquidity levels.** `extract_liquidity_levels` (`analysis.py:210`)
computes `touch_count` over the *entire* candle series, so a level's strength encodes
future price action.

**B4. No event→outcome dataset.** Requirement 5, the core new capability, does not exist.
There is no way to ask "what happens after a liquidity sweep?".

**B5. Structure events are pre-labelled as trade signals.** `confidence=0.95` on BOS,
`0.9` on HH/HL, `0.7` on shift (`analysis.py:93,134,161`). These are hand-assigned
constants with no empirical meaning that read as conviction scores. Requirement 3
demands events be descriptive and direction-neutral.

### HIGH

**B6. Incomplete trade ledger.** `Trade` (`engine.py:99`) lacks `signal_time`,
`order_time`, `fill_time`, `strategy_id`/`version`, `notional_value`, `risk_amount`,
`spread_cost`, `slippage_cost`, `MAE`, `MFE`, `market_regime`, `strategy_context`.
`BacktestTradeRecord` mirrors the gap.

**B7. Only gross R.** `engine.py:588` computes `r_multiple = gross / risk_cash`. Costs
are inside the fill price, so R silently absorbs them. Requirement 15 needs net R — the
Monte Carlo project's actual input.

**B8. No MFE/MAE tracking.** The engine never observes the position's intra-life
extremes. Required for the event outcomes and for the Monte Carlo handoff.

**B9. Costs opaque in the ledger.** Spread and slippage are folded into the fill price;
only `fees` reaches the trade record. Requirement 7 says do not combine internally.

**B10. Risk/allocation terminology conflated.** `_size_for` (`engine.py:216`) overloads
`risk_fraction` as *either* stop-risk *or* direct share of account depending on whether
a stop exists. Requirement 8 forbids exactly this, and buy & hold is currently labelled
as a 100% risk trade.

**B11. Risk engine freely bypassable.** `risk=None` is the default on `BacktestEngine`
and `run_backtest` with no notion of run mode. Requirement 9 forbids
`live_engine(risk=None)`.

**B12. No distribution statistics.** `PerformanceMetrics` has mean R and win rate only.
Requirement 16 needs median, σ, percentiles, skew, streaks, MAE/MFE, cost-per-trade.

### MEDIUM

**B13. Local dataset is ~3 days.** `data/parquet` holds 690+720+414 5m bars, 57 1h,
14 4h, 230 15m — all from September 2026. Requirement 11: no strategy conclusions from
a tiny sample. Needs a real multi-year fetch plus a dataset version.

**B14. No statistical machinery.** No bootstrap, no confidence interval, no baseline
comparison for events (requirements 6, 23).

**B15. No research report generator.** Requirement 22.

**B16. No reusable lookahead audit.** Requirement 2's "reusable utility".

**B17. No Monte Carlo handoff export.** Requirement 25F.

### LOW / BY DESIGN

- No ML, news, paper or live execution — correctly absent, must stay absent.
- Risk defaults (1%/5%/10%/20%) are unlabelled examples. Requirement 10 says keep them
  but *label* them; no numeric change needed.

---

## C. Plan

1. **Causality rewrite of market structure** — add `confirmation_time`/`confirmation_index`
   to swings, events and levels; make every derived quantity respect an `as_of_index`;
   strip the fake `confidence` field. Keep the existing API shape so the frontend chart
   keeps working.
2. **New `services/research/` package** — event schema, causal detector for
   structure / liquidity-sweep / displacement / volatility / regime events, outcome
   labeller (forward returns, MFE/MAE, R barriers), null baselines, bootstrap statistics,
   report renderer, Monte Carlo ledger export.
3. **Backtest ledger hardening** — full trade record, gross *and* net R, MAE/MFE,
   decomposed costs, explicit `SizingModel`, run modes that make the risk engine
   mandatory outside research.
4. **Metrics** — full R-distribution statistics, explicit `insufficient_sample` flags.
5. **Reusable lookahead audit + tests** proving prefixes cannot influence signals.
6. **Real multi-year dataset** with a content-hash dataset version.
7. **Run one complete event→outcome analysis** on real data.

## D. Intentionally deferred

Walk-forward optimisation, ML, Nobitex execution, paper trading, live trading. The
interfaces they need (event records, ledger, experiment metadata) are produced now so
they can be added without redesign.

---

## Addendum — findings from the execution pass (2026-10-03)

Most of B1–B17 above had already been implemented in this working tree before this
session. Verification against the code confirmed the fixes are real (confirmation
timestamps on swings/events/levels; the `research/` package; the full trade ledger;
gross *and* net R; `SizingModel`; `RunMode` enforcement; distribution statistics).
Two defects were found and fixed here that the plan did not anticipate.

### F1. Liquidity sweeps counted a persistent condition as an event (correctness)

`detect_liquidity_sweeps` treated "price is trading beyond this level" as an event on
*every* bar it held. A sweep is a **crossing** — a transition from one side of the
level to the other and back — but the detector had no memory of whether an excursion
had already been reported.

On 6 000 1h bars this produced **1 033 617** sweep events from 743 levels. Every
sample after the first crossing was a re-count of the same crossing, so the "sample"
was ~170 events per bar of independent information. Consequences:

- every statistic computed over sweeps was meaningless (the samples are not
  independent), and Benjamini–Hochberg over 176 tests could not repair that;
- the full 1h history **could not be analysed at all** — it died with `MemoryError`.

Fixed by tracking whether each level is already beyond the current bar
(`beyond_since`), and firing only on the first bar it is found beyond; the flag
clears when price returns inside the level, so a genuine second crossing counts
again. Same 6 000 bars now yield **9 019** events (115× fewer), and the full 1h
history completes. Regression test:
`test_a_sweep_is_a_crossing_not_a_persistent_condition`.

### F2. Bootstrap was O(resamples × n) in scalar Python (performance)

`bootstrap_mean`, `paired_difference` and `difference_p_value` each ran
`resamples` (2 000) Python loops of `n` `randrange` calls. With n in the tens of
thousands and ~176 detector/side/stop/horizon combinations, a research pass that
should take seconds ran for over 28 minutes.

Vectorised with numpy (already a dependency) and **batched**, because a full
`(2000, n)` index matrix is 1.6 GB on the large event sets and would have traded a
slow run for an OOM. `BOOTSTRAP_BATCH_CELLS` caps peak memory at ~8 MB of indices
regardless of sample size.

Note on reproducibility: the resampling method and the fixed seed are unchanged, so
intervals remain reproducible run-to-run, but the *specific* resample indices differ
from the scalar implementation. Tests assert distributional properties (an interval
widens with dispersion, a constant sample gives a degenerate interval, a sample
compared with itself gives exactly zero) rather than exact values, so this is sound —
but previously reported bootstrap intervals would shift slightly on re-run.
