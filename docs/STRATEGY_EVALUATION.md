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
