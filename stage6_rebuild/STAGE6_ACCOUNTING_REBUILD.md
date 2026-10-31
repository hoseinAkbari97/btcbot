# Stage 6 — Setup 1 accounting rebuild

Generated 2026-10-31 08:12 UTC from the frozen Setup 1 development ledger and the 5m BTCUSDT dataset.

## Two answers, kept separate

- **Signal quality (pre-cost):** No, under the frozen stop-first convention. Canonical trades average **-0.2227R gross before costs** (95% episode-cluster CI -0.2290 to -0.2164), and the interval excludes zero on the negative side. The headline is tie-dependent: excluding the 24,998 ambiguous same-bar resolutions leaves +0.0304R gross (n=76,791), so at most a very small non-tie directional edge. Counting ties as wins would turn the gross mean positive, but that is a different intrabar assumption (reported below), not the frozen primary convention.
- **Executable spot feasibility:** No. The primary feasible portfolio ends at **$4.98** (-99.95%), net P&L **-$9,995.02**, with max drawdown **99.95%**. It falls below the venue minimum order by **2021-06-19** and never trades again. Of 103,558 canonical trades, 14,978 (14.46%) meet the predeclared execution constraints, and only a minority of those can be funded inside the spot cash cap.

## Protocol

### Canonical trade identity

One canonical trade is **`(entry_index, entry_price, stop_price, target_r=1)`**. Every ledger row sharing that identity is an observation of the same executable trade. The canonical record keeps the unique event indices, detector set, spill-line range, observation count, and episode id; duplicate rows are not allowed to contribute independent R.

### Execution and sizing

- Venue rules: Binance BTCUSDT spot, tick **$0.01**, lot **0.00001000 BTC**, minimum notional **$5.00**, long-only, no leverage.
- Frozen cost model: fee **0.100% per side**, spread **0.020% per side**, slippage **0.010% per side** (combined adverse concession `ADVERSE_RATE` = **0.030% per side**); entry buys are rounded up to the tick, exits are rounded down, and size is rounded down to the lot.
- Baseline capital **$10,000**, risk budget **1.00%** of equity per trade. Position size is the smaller of the risk-budget size and the cash-cap size; the cash cap includes the entry fee. R is measured against the risk actually taken (`(entry_fill - stop_exec) * size`), not the requested risk budget.
- Entries occur at the **open of the entry bar**. Exits occur at the **close of the bar carrying the barrier**. Unresolved/censored signals are closed at the close of the 12th bar (the end of the frozen outcome window); this is the documented time stop, and a resolved-only run is reported as a sensitivity.
- Signals sharing an entry bar compete for cash. They are sized independently, then scaled pro rata to available cash; if scaling pushes a candidate below the venue minimum it is skipped and freed cash is not reallocated in the same bar. This is deliberately conservative and is stated before any performance number is read.

### Feasibility envelope (predeclared)

A trade is executable only if `cost_at_target / fill_to_stop_risk <= 1.00` **and** the risk-budget order meets the tick, lot and minimum-notional rules. The break-even envelope is not a stop-distance floor: it is the point at which a +1R win is fully consumed by round-trip costs. No arbitrary stop-distance floor is applied. The stricter `cost/risk <= 0.50` envelope is reported only as a sensitivity.

### Tie convention

The primary convention remains **stop-first** for same-bar stop/target ties, exactly as frozen. The tie-win and 50/50-split conventions appear only as labelled sensitivities; they are never substituted into the primary result.

### Dependence

Signal intervals resample **whole episodes** (the Stage 5 `assign_episodes` definition, 12-bar horizon) with replacement. Portfolio intervals use the same episode clusters and, as a temporal-dependence sensitivity, a calendar-month block bootstrap. Neither bootstrap re-simulates the capital path; that limitation is explicit.

## Data integrity

The development ledger spans **2021-01-01T02:50:00+00:00** to **2024-06-30T23:04:59.999000+00:00**. It is the development split only; no validation or out-of-sample data is included.

| check | value |
|---|---:|
| ledger rows read | 2,395,528 |
| canonical trades | 103,558 |
| duplicate observations collapsed | 2,291,970 |
| unique event indices | 103,558 |
| unique episodes | 22,982 |
| entry bars with more than one canonical trade | 0 |
| max canonical trades at one entry bar | 1 |
| max observations collapsed into one trade | 1,756 |
| mean observations per trade | 23.13 |
| entry-index alignment checked | 103,558 |
| entry-index alignment mismatches | 0 |
| confirmation-index conflicts within an identity | 0 |
| target-outcome conflicts within an identity | 0 |
| stop-distance conflicts within an identity | 0 |
| truncated-flag conflicts within an identity | 0 |
| entry indices out of range | 0 |
| resolved exits outside the 12-bar horizon | 0 |
| censored trades given a 12-bar time stop | 1,769 |
| winning exits filled above the target (target gap) | 1 |
| losing exits filled below the stop (stop gap) | 0 |

Reconciliation with the Stage 5 checkpoint:

| quantity | Stage 5 | Stage 6 |
|---|---:|---:|
| observations | 2,395,528 | 2,395,528 |
| unique entry candles | 103,558 | 103,558 |
| resolved trades | 101,789 | 101,789 |
| episodes | 22,982 | 22,982 |

All rows at one identity share the same stop, target outcome and confirmation index in this ledger, so collapsing them changes the unit of analysis, not the measured outcome. The single target gap fill is not an integrity error: when price gaps through the target, the ledger records the bar-open fill, which can be above the nominal +1R level. The canonical record preserves that exit price rather than rewriting the outcome.

## 1. Canonical signal quality (pre-cost)

Resolved canonical trades: **101,789**; censored and excluded from signal statistics: **1,769**. Ambiguous same-bar resolutions: **24,998** (24.56% of resolved).

| tie convention | n | gross win rate | gross expectancy R | 95% CI | gross PF | total gross R |
|---|---:|---:|---:|---:|---:|---:|
| stop-first (primary) | 101,789 | 38.87% | -0.2227 | -0.2290 to -0.2164 | 0.636 | -22,665.0 |
| tie = win (sensitivity) | 101,789 | 63.43% | +0.2685 | +0.2624 to +0.2746 | 1.734 | +27,331.0 |
| 50/50 tie split (sensitivity) | 101,789 | 40.06% | +0.0229 | +0.0173 to +0.0286 | 1.063 | +2,333.0 |

The tie convention matters enormously for the gross result: under stop-first every same-bar tie is a loss, while the alternative conventions count it as a win or a scratch. The primary conclusion is the stop-first row.

Diagnostic — excluding every ambiguous same-bar resolution (**76,791** trades), gross expectancy is **+0.0304R** (95% CI +0.0227 to +0.0378), win rate **51.52%**. This isolates the non-tie directional edge from the tie convention and is not a substitute for the primary result.

### Gross R by year (stop-first, resolved only)

| year | trades | resolved | censored | episodes | win rate | mean R | total R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 26,846 | 26,399 | 447 | 6,344 | 38.70% | -0.2260 | -5,965.0 |
| 2022 | 29,669 | 29,153 | 516 | 6,608 | 39.25% | -0.2150 | -6,267.0 |
| 2023 | 31,191 | 30,629 | 562 | 6,698 | 38.31% | -0.2339 | -7,163.0 |
| 2024 | 15,852 | 15,608 | 244 | 3,334 | 39.52% | -0.2095 | -3,270.0 |

### Cost-adjusted signal R (legacy denominator)

Subtracting the frozen round-trip cost from raw-entry/raw-exit R while keeping the raw stop distance as the denominator gives mean **-381.6959R** (95% CI -395.8571 to -367.6851). This is a continuity check, not the executable result; the executable result uses fill-to-stop risk, actual size, and the spot cash cap.

## 2. Stop-distance and execution feasibility

### Why tiny stops are not free

A +1R target is only one stop-distance away, so a tiny stop makes the target a tiny price move while the round-trip cost stays proportional to price. The ratio that decides viability is therefore `round_trip_cost / fill_to_stop_risk`, not stop distance in isolation. The frozen cost model makes that ratio large exactly where Stage 5 found the small stops.

| distribution | n | p5 | p25 | median | p75 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stop distance ($) | 103,558 | 0.7000 | 8.6400 | 25.1650 | 61.7100 | 168.2130 | 319.3804 | 3,561.4500 |
| stop distance (bp of entry) | 103,558 | 0.2272 | 2.7565 | 7.0923 | 16.0200 | 38.6836 | 71.7825 | 781.6754 |
| round-trip cost per unit ($) | 103,558 | 48.4857 | 69.1355 | 96.2273 | 125.2256 | 172.5989 | 182.3187 | 190.6118 |
| fill-to-stop risk per unit ($) | 103,558 | 9.0100 | 18.7300 | 36.8500 | 74.5300 | 182.9130 | 333.5776 | 3,575.1200 |
| cost / risk | 103,558 | 0.6250 | 1.3681 | 2.5769 | 4.5163 | 8.0545 | 8.6581 | 8.6629 |
| implied leverage at 1% risk | 103,558 | 2.3996 | 5.2589 | 9.9096 | 17.3699 | 30.9847 | 33.3076 | 33.3272 |
| effective minimum stop = max(tick, cost) | 103,558 | 48.4857 | 69.1355 | 96.2273 | 125.2256 | 172.5989 | 182.3187 | 190.6118 |

- Raw stop distance below one venue tick ($0.01): **0** trades. This alone does not make a trade infeasible; the stop must be at least one tick below the *fill*, which is stricter.
- Raw stop distance below the round-trip cost per unit: **91,623** trades.
- Trades whose 1%-risk notional exceeds available spot cash: **103,102** (99.56%). For these the spot cap binds and the risk actually taken is below the 1% budget.

Two denominators matter. Stage 5 divided cost by the **raw stop distance**, which can be a few cents, and reported ratios up to 18,941. Stage 6 divides by **fill-to-stop risk**: the entry fill already includes the adverse concession, so for a nominal stop only cents away the measured risk is still roughly 0.03% of price (about $9 at BTC $30k). The ratio therefore saturates near 8.66 instead of exploding. The economics are unchanged; the denominator is now the risk an executed position actually carries.

On this sample the tick, lot and minimum-notional checks never bind on their own: every infeasible trade fails the cost envelope. The binding constraint is `cost/risk`, not a venue minimum or a discretionary stop floor.

### Infeasible counts and reasons

| outcome | trades | share |
|---|---:|---:|
| feasible | 14,978 | 14.46% |
| infeasible | 88,580 | 85.54% |
| feasible, resolved | 13,599 | 13.13% |
| infeasible, resolved | 88,190 | 85.16% |

| reason | all trades | resolved trades |
|---|---:|---:|
| cost_exceeds_1R | 88,580 | 88,190 |
| feasible | 14,978 | 13,599 |

`cost_exceeds_1R` dominates: the stop is too small relative to the round-trip cost for a +1R win to survive. No stop-distance floor was introduced to change this count.

Observationally, the envelope is a **cost-driven minimum stop**: the median effective minimum is **$96.23** (p5 $48.49, p95 $172.60), which is roughly 25-30 bp of price at these BTC levels. That minimum is the round-trip cost itself, not a discretionary stop-distance floor, and it was fixed before any Stage 6 performance number was read. Applying it is a protocol rule, not a tuning decision.

### Feasible subset under the tie conventions

| tie convention | n | gross win rate | gross expectancy R | 95% CI |
|---|---:|---:|---:|---:|
| stop-first (primary) | 13,599 | 48.30% | -0.0340 | -0.0518 to -0.0167 |
| tie = win | 13,599 | 50.31% | +0.0063 | -0.0112 to +0.0233 |
| 50/50 tie split | 13,599 | 48.37% | -0.0139 | -0.0314 to +0.0031 |

Even the feasible subset has a slightly negative stop-first gross mean. Counting ties as wins makes it positive, but costs and the capital path still decide the executable result.

For the feasible subset the median cost/risk is **0.726** (p95 **0.974**). Using the break-even relation `p > (1 + c) / 2`, the median implied break-even win rate is **86.31%** (p95 **98.72%**), against an actual stop-first gross win rate of **48.30%**. Most feasible trades need a win rate far above the signal's actual rate simply to break even.

### Stop distance by bucket

| stop bucket | trades | resolved | feasible | feasible & resolved |
|---|---:|---:|---:|---:|
| 0-1 bp | 11,332 | 11,332 | 0 | 0 |
| 1-5 bp | 29,885 | 29,876 | 0 | 0 |
| 5-10 bp | 21,346 | 21,304 | 0 | 0 |
| 10-25 bp | 28,094 | 27,693 | 2,077 | 2,015 |
| 25-50 bp | 10,193 | 9,468 | 10,193 | 9,468 |
| 50-100 bp | 2,288 | 1,831 | 2,288 | 1,831 |
| >100 bp | 420 | 285 | 420 | 285 |

### Selection effect of the feasibility filter

| subset | resolved n | gross win rate | gross expectancy R | 95% CI |
|---|---:|---:|---:|---:|
| feasible | 13,599 | 48.30% | -0.0340 | -0.0518 to -0.0167 |
| infeasible | 88,190 | 37.41% | -0.2518 | -0.2583 to -0.2451 |

Feasibility is not random: it selects larger stops, which can select a different signal population. The comparison above is the honest check on whether the filter itself creates the result.

## 3. Portfolio accounting

### Primary portfolio

- Candidates: **103,558** canonical trades; taken: **2,711** (2.62% of all candidates). Of the **14,978** feasible candidates, **18.10%** were actually funded; the rest were skipped because available cash could not meet the venue minimum order at the time.
- Initial capital **$10,000.00**, final equity **$4.98**, total return **-99.95%**, CAGR **-88.66%**.
- Net P&L **-$9,995.02**; gross P&L **-$821.38**; fees **$7,055.91**; spread+slippage **$2,117.74**; total cost **$9,173.64**. Costs are the dominant term: total cost is **11.17x** the absolute gross P&L.
- Max drawdown **$10,003.94** (**99.95%**) from 2021-01-01T18:00:00+00:00 to 2021-06-19T13:00:00+00:00; recovery not reached.
- Mean net R per taken trade **-0.6918**, median **-1.1764**; win rate **39.14%**; profit factor **0.303**.
- Exposure: average invested/equity **1.60%** over the whole development span, **95.39%** while a position was open; maximum **100.00%**; time in market **1.68%**. Maximum concurrent positions **2**, average **0.02** (**1.01** while active).

**The path is ruined early.** Equity falls from $10,000 to about $4.98 by 2021-06-19T13:00:00+00:00, which is below the venue minimum notional plus fee. After that point every remaining feasible signal is skipped for insufficient cash, so the yearly table has no later trades. This is a real consequence of the accounting, not a missing data period: the 2022-2024 signals exist in the ledger but the portfolio cannot fund them.

Capital competition and skipped candidates:

| skip reason | count |
|---|---:|
| below_min_order_at_entry | 12,267 |
| cost_exceeds_1R | 88,580 |

Exit mix among taken positions:

| exit reason | count |
|---|---:|
| stop | 1,382 |
| target | 1,184 |
| time_stop | 145 |

### Yearly portfolio results

| year | trades | net P&L | gross P&L | win rate | mean R |
|---|---:|---:|---:|---:|---:|
| 2021 | 2,711 | -$9,995.02 | -$821.38 | 39.14% | -0.6918 |

### Dependence-aware intervals for the primary portfolio

- Net R per taken trade: **-0.6918** (episode-cluster 95% CI -0.7275 to -0.6566; 1,675 contributing episodes).
- Net P&L per taken trade: **-$3.69** (episode-cluster 95% CI -$4.34 to -$3.03; 1,675 contributing episodes).
- Total net P&L: **-$9,995.02** (episode-cluster 95% CI -$11,852.20 to -$8,161.71; 1,675 contributing episodes); as a return on initial capital, -118.52% to -81.62%.
- Calendar-month block bootstrap for net R per trade: **-0.6918** (95% CI -0.7190 to -0.6561; 6 months).

The episode bootstrap addresses overlapping signals that share an episode. The month bootstrap addresses broader temporal dependence. Neither re-simulates capital allocation, so the portfolio path remains one realised path, not a distribution over paths. Because the total-P&L interval resamples realised trade P&L without enforcing the equity floor, its lower bound can exceed -100%; that is uncertainty in trade P&L, not a feasible equity path. The month bootstrap has only six months because the primary path is ruined by 2021-06; it is a local temporal check, not a full-sample one. The taken set is itself selected by the early equity path, so these intervals describe the funded trades, not the full feasible universe.

The mean net R of -0.6918 is not a restatement of the gross signal mean (-0.0340R on the feasible subset). The spot cash cap forces actual risk far below the 1% budget, so the R denominator is small and costs consume a large multiple of it. That gap between gross edge and net R is the execution result this section is measuring.

## 4. Sensitivities

| scenario | taken | taken / all candidates | final equity | total return | max DD | net P&L | mean R | win rate | PF | max concurrent | avg utilization |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| primary (stop-first, all outcomes) | 2,711 | 2.62% | $4.98 | -99.95% | 99.95% | -$9,995.02 | -0.6918 | 39.14% | 0.303 | 2 | 1.60% |
| resolved only (no censored) | 2,601 | 2.56% | $4.99 | -99.95% | 99.95% | -$9,995.01 | -0.7237 | 39.29% | 0.295 | 2 | 1.26% |
| tie = win | 3,107 | 3.00% | $4.98 | -99.95% | 99.95% | -$9,995.02 | -0.5960 | 43.22% | 0.350 | 2 | 1.73% |
| 50/50 tie split | 2,908 | 2.81% | $5.00 | -99.95% | 99.95% | -$9,995.00 | -0.6402 | 39.72% | 0.320 | 2 | 1.65% |
| 0.5x costs, re-filtered | 5,105 | 4.93% | $5.00 | -99.95% | 99.95% | -$9,995.00 | -0.5664 | 42.90% | 0.447 | 2 | 1.92% |
| 1.5x costs, re-filtered | 1,926 | 1.86% | $4.99 | -99.95% | 99.95% | -$9,995.01 | -0.7198 | 35.98% | 0.220 | 2 | 1.41% |
| 2x costs, re-filtered | 1,451 | 1.40% | $5.00 | -99.95% | 99.95% | -$9,995.00 | -0.7610 | 30.67% | 0.169 | 3 | 1.39% |
| cost/risk <= 0.5 envelope | 2,736 | 2.64% | $7.72 | -99.92% | 99.92% | -$9,992.28 | -0.3832 | 43.53% | 0.420 | 3 | 3.26% |
| 0.5x costs, fixed primary set | 5,060 | 4.89% | $4.98 | -99.95% | 99.95% | -$9,995.02 | -0.3911 | 46.38% | 0.514 | 3 | 3.22% |
| 1.5x costs, fixed primary set | 1,885 | 1.82% | $5.00 | -99.95% | 99.95% | -$9,995.00 | -0.9562 | 20.58% | 0.174 | 2 | 1.06% |
| 2x costs, fixed primary set | 1,434 | 1.38% | $4.97 | -99.95% | 99.95% | -$9,995.03 | -1.1730 | 12.76% | 0.104 | 2 | 0.71% |
| $1,000 capital | 1,909 | 1.84% | $5.00 | -99.50% | 99.50% | -$995.00 | -0.6861 | 39.65% | 0.303 | 2 | 1.08% |
| $100,000 capital | 3,587 | 3.46% | $5.00 | -100.00% | 100.00% | -$99,995.00 | -0.6837 | 39.64% | 0.303 | 3 | 2.01% |
| 0.5% risk | 3,044 | 2.94% | $4.99 | -99.95% | 99.95% | -$9,995.01 | -0.6933 | 39.42% | 0.253 | 2 | 1.41% |
| 2% risk | 2,673 | 2.58% | $4.98 | -99.95% | 99.95% | -$9,995.02 | -0.6882 | 39.21% | 0.334 | 2 | 1.66% |

Nearly every path is ruined and ends within a few dollars of the **$5 venue minimum-order floor**; the stricter 0.5 envelope ends at $7.72 but is still down 99.92%. The informative differences are how many trades can be funded, the trade-level mean R, and how quickly the capital is exhausted. Even halving costs does not produce a surviving path; doubling costs simply ruins the account with fewer trades. The stricter `cost/risk <= 0.5` envelope is a sensitivity only.

`fixed primary set` holds the baseline feasible trade universe constant while changing execution costs, isolating the cost effect from the feasibility re-filter. The re-filtered rows are the protocol-consistent cost sensitivities; the fixed-set rows answer what would happen to the same trades under a different cost regime.

### Cost break-even arithmetic

Let `c = cost / risk`. A +1R winner nets approximately `(1 - c)R`; a -1R loser loses approximately `(1 + c)R`. Break-even therefore requires a win rate above `(1 + c) / 2`. At the primary envelope `c = 1`, even a 100% win rate cannot produce a positive net result; at `c = 0.5`, the required win rate is 75%. This is why feasibility must be judged on the cost/risk ratio, not on stop distance alone.

## 5. What this means

- **Canonical accounting changes the denominator, not the story.** Collapsing 2,291,970 duplicate observations removes the per-row explosion that made Stage 5 totals meaningless. The canonical stop-first gross expectancy is -0.2227R; the legacy cost-adjusted mean (-381.70R) reproduces the Stage 5 order of magnitude, confirming that deduplication alone does not repair the accounting.
- **The pre-cost answer is convention-dependent.** Stop-first is negative and statistically clear; excluding ties the edge is only +0.0304R, and counting ties as wins would make it positive. The primary result stays stop-first, so there is no robust pre-cost edge to build on.
- **Most signals are not executable spot trades.** 88,580 of 103,558 canonical trades fail the predeclared execution constraints, overwhelmingly because the round-trip cost exceeds one unit of risk.
- **The feasible subset still cannot survive costs and the spot cap.** Its stop-first gross mean is -0.0340R, and the capital-constrained portfolio is ruined by mid-2021. The cash cap binds for 99.56% of all candidates, so risk actually taken is below the 1% budget and R is measured on that smaller base.
- **No protocol tuning.** No stop floor, tie rule, cost assumption, or sizing rule was changed after seeing a Stage 6 performance number. Alternative tie and cost assumptions are reported separately and are not substitutes for the primary result.
- **Scope.** This is development-sample accounting, not validation or out-of-sample evidence. No strategy parameter was tuned.

## Reproduction

```bash
python stage6_rebuild/rebuild_setup1_accounting.py
```

Machine-readable results: `stage6_rebuild/stage6_summary.json`. Canonical records: `stage6_rebuild/canonical_trades.jsonl.gz`. Primary equity curve: `stage6_rebuild/daily_equity.csv`.

