# Strategy evaluation

Stage 3D turns persisted backtest results into a reproducible evaluation of how
credible they are. It reads stored runs; it never re-runs the engine, never edits
a stored run, and never reads validation or out-of-sample data.

The purpose is deliberately narrow: **measure what the sample supports, and
refuse the rest.** Historical metrics alone cannot establish that a strategy is
profitable, robust or production-ready, and nothing in this package says so.

## Guarantees

| Guarantee | How it is enforced |
| --- | --- |
| Read-only | The service only issues `SELECT`s; a test asserts the run row, trade count and summed PnL are byte-identical after evaluation. |
| Authorised data only | A run whose mode is not in `EvaluationConfig.allowed_modes` (default `("research",)`) is refused, and an unrecorded mode reads as unknown, never as research. |
| Observed inputs only | Every simulated path is built from the run's own persisted trades. No win rate, payoff ratio or trade frequency is assumed. |
| Reproducible | Configuration, seed, method version and input fingerprint are stored in the report, and the same inputs produce the same digest. |
| Honest about gaps | A statistic the data cannot support is `null` with a stated reason, never `0.0`. |

## Pipeline

1. **Input validation and provenance** (`provenance.py`) — snapshot the run,
   check mode, capital, period and cost assumptions, and record incomplete
   provenance as named warnings.
2. **Performance** (`performance.py`) — equity and trade PnL, annualised
   statistics only when the run's own span supports them, drawdown availability.
3. **Trade statistics** (`trade_stats.py`) — wins, losses, profit factor,
   expectancy in R, cost attribution, streaks.
4. **Tail risk** (`tail_risk.py`) — observed expected shortfall, downside
   deviation, profit concentration.
5. **Cost and execution sensitivity** (`sensitivity.py`) — the same trades
   re-priced under cost multipliers and a break-even multiplier.
6. **Robustness** (`robustness.py`) — calendar segments within the sample, and a
   comparison with already-persisted parameter neighbours.
7. **Statistical robustness and Monte Carlo** (`montecarlo.py`) — circular
   block bootstrap of observed trades, drawdown and ruin probabilities,
   dependence screen, permutation pass.
8. **Report** (`report.py`) — one serialisable, digestible artifact with an
   evidence grade and a list of withheld claims.

## Metric definitions

Let `n` be the number of persisted trades, `net_i` the stored net PnL of trade
`i`, `cost_i` its itemised costs and `risk_i` its recorded risk amount.

| Metric | Definition | Source and caveat |
| --- | --- | --- |
| Net PnL | `Σ net_i` | Persisted ledger. |
| Gross PnL | `Σ (net_i + cost_i)` | Reconstructed from stored gross columns. |
| Total return | `(final_equity - initial_capital) / initial_capital` | Run record; the persisted `total_return` is cross-checked and a disagreement is reported. |
| CAGR, volatility, Sharpe, Sortino, Calmar | As computed by `app/services/backtest/metrics.py` | Read from the run, and reported as `null` when the run flags `insufficient_sample`, because a `0.0` there means "not computable". |
| Max drawdown | Run-time maximum drawdown fraction | Persisted with the run. The equity curve is **not** persisted, so drawdown **duration** is unavailable. |
| Exposure | Share of bars in a position | Persisted `exposure` when present. |
| Time in market | `Σ holding_seconds / observed span` | Computed from the ledger, reported unclamped, with a warning when it exceeds 1 (overlapping or same-bar positions). |
| Win rate | `#(net_i > 0) / n` | Scratches (`net_i == 0`) are counted separately. |
| Average win / loss | `Σ net^+ / #wins`, `Σ net^- / #losses` | Net of costs. |
| Profit factor | `Σ net^+ / |Σ net^-|` | `null` when there is no losing trade; the denominator would be zero. |
| Payoff ratio | `average win / |average loss|` | `null` unless both sides exist. |
| Expectancy | `Σ net_i / n` | Currency per trade. |
| Expectancy in R | `mean(net_i / risk_i)` | Reported only when **every** trade has a finite `net_r`; a partial R sample is omitted, not averaged. |
| Win-rate standard error | `sqrt(p(1-p)/n)` | Binomial approximation; assumes independent trades, which is exactly what the dependence screen tests. |
| Cost to gross profit | `Σ cost_i / Σ gross_pnl^+` | Compares costs with the winnings measured **before** costs. |
| Cost breakdown | Share of total costs from fees, spread, slippage, latency, other | Shares of the persisted itemised costs. |
| Max consecutive wins / losses | Longest run in the stored sequence | Order-dependent by definition. |
| VaR (R) | `percentile_{α}(R)` with `α = 1 - confidence` | Observed sample quantile. |
| CVaR / expected shortfall (R) | Mean of the worst `ceil(αn)` R values (at least one) | Seasoned with the sample; not a forward-looking estimate. |
| Downside deviation (R) | `sqrt(mean(R_i^2))` over negative `R_i` | A dispersion measure, not an annualised Sortino denominator. |
| Tail ratio | `|percentile_{confidence}(R)| / |percentile_α(R)|` | Describes asymmetry of the observed tails. |
| Lower-tail loss share | Share of total losses in the worst `α` fraction | Concentration of damage. |
| Profit concentration (top 5) | Share of gross winnings from the five largest wins | Warns when more than half the result rests on at most five trades. |
| Break-even cost multiplier | `Σ gross_pnl / Σ cost_i` when gross is positive | Exact only while decisions, sizes and fills are unchanged. |

Gross and net are never mixed: the trade table reports both, and the evidence
layer treats a gross-positive, net-negative run as not showing an edge.

## Statistical methods

### Circular block bootstrap

Paths are built by drawing **observed trades**, never parameters:

1. Choose a block length `L`. The default is the cube-root rule
   `L = round(n^(1/3))`, clamped to `[2, 50]` and to at most `n/2`
   (`derive_block_length`). It is a transparent heuristic: automatic
   (Politis–White) block selection is not implemented.
2. Draw `ceil(n/L)` block starts uniformly from `0..n-1`; block contents are
   taken with wraparound, so a block that starts near the end continues at the
   beginning. This is a circular block bootstrap.
3. Concatenate and truncate to `n` trades, keeping each trade's own net PnL, net
   R and risk fraction together.

Adjacent trades stay adjacent inside a block, so serial dependence within a
block survives resampling. Dependence that spans block boundaries is broken,
which is why intervals are still described as optimistic when the dependence
screen fires.

### Equity models

The model is chosen from the ledger and named in every report:

- `compounding_risk_fraction` — used when every trade has a finite, positive
  risk fraction and a finite net R. Equity evolves as
  `E_{t+1} = E_t · (1 + R_t · f_t)` where `f_t` is the trade's recorded risk
  fraction. A growth factor at or below zero wipes the path out and is counted
  in `wipeout_paths`.
- `additive_pnl` — used otherwise. `E_{t+1} = E_t + net_t`, i.e. each drawn
  trade adds its own recorded net PnL.

Both models use the **observed** trade outcomes. Neither assumes a win rate, an
average win/loss, a reward-to-risk ratio or a trade frequency.

### Reported distributions

| Quantity | Definition |
| --- | --- |
| Terminal return | `E_n / E_0 - 1` over `resamples` paths; reported as median, mean, standard deviation, and a `confidence` percentile interval. |
| Drawdown on a path | `min_t (E_t / max_{s≤t} E_s - 1)`, with the starting equity included. |
| Drawdown probability threshold `d` | Share of paths whose maximum drawdown is at least `d`. |
| Ruin | Share of paths whose equity touched or fell below `(1 - ruin_fraction) · E_0` within the `n`-trade horizon. This is a **horizon-conditional** definition, not a probability of eventual ruin. |
| Losing streak | Longest run of negative net R in a path; reported as median, p90, p95, p99 and maximum. |
| Mean R interval | Percentile interval of the per-path mean R, i.e. the sampling uncertainty of the observed mean. |
| CVaR of terminal return | Mean of the worst `ceil(α · resamples)` terminal returns. |
| Order sensitivity | `resamples` uniform permutations of the same trade multiset, using the same equity model. |

Terminal equity is order-invariant under both models, because per-trade growth
factors and PnL increments commute; the permutation pass therefore speaks only
to **how deep a drawdown the same trades can produce**.

### Dependence screen

For the observed net R series the lag-`k` autocorrelation is

```
ρ_k = Σ_{t=1}^{n-k} (R_t - R̄)(R_{t+k} - R̄) / Σ_{t=1}^{n} (R_t - R̄)^2
```

for `k = 1..min(5, n/5)`. A lag is flagged when `|ρ_k| > 2/√n`; any flag marks
the sample as dependent, downgrades the evidence level, and is stated in the
report. The screen needs at least eight trades and a complete R series.

### Cost scenarios

A scenario with multiplier `m` re-prices each trade as

```
net_i(m) = gross_pnl_i - m · (fees_i + spread_i + slippage_i + latency_i + other_i)
```

This is exact for costs that scale with the fill and for **unchanged decisions,
sizes and fills**. It cannot model a different latency, fill order or market
impact, because those change which trades exist; the report says so and marks
such analysis as requiring a matched re-run. Average R under a scenario divides
the re-priced PnL by the recorded risk amount, which itself depends on the
original costs.

### Segments and parameter neighbours

Calendar months are cut from the **authorised research sample** by entry time
and are labelled as in-sample, never as holdout. Parameter sensitivity compares
runs that already exist and differ only in parameters, symbol, timeframe and
dataset version held equal; nothing is re-optimised and no engine run is
triggered. A narrow spread is not evidence of robustness, and a wide one may
only reflect a coarse grid.
