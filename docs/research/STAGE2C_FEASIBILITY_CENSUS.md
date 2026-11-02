# Stage 2C — Candidate A Feasibility Census

**Strategy:** `CANDIDATE_A_MTF_TREND_PULLBACK_CONTINUATION`
**Scope:** BTCUSDT spot, long-only, development interval `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Status:** complete. Feasibility counting only — **no backtest, no P&L, no expectancy, no win rate**.
**Final verdict:** **FAIL — insufficient non-overlapping opportunity frequency**

The frozen definition is in `stage2c_census/STAGE2C_SIGNAL_SPECIFICATION.md`; the machine
configuration is `stage2c_census/stage2c_config.json`; the freeze record is
`stage2c_census/freeze.json`. Both files were hashed before the first counting run, and
`stage2c_census/census.py` aborts if either hash changes. The full machine result is
`stage2c_census/census_result.json` and the curated summary is
`docs/research/STAGE2C_FEASIBILITY_CENSUS.json`.

---

## 1. Executive result

| item | Primary — 4h regime + 1h pullback | Control — same LTF stream, no regime filter | Control, matched window |
|---|---:|---:|---:|
| Crossunder episodes | 644 | 644 | — |
| Confirmed triggers (raw) | 195 | 445 | 429 |
| Valid entry bar | 195 | 445 | 429 |
| Valid structural stop | 195 | 445 | 429 |
| Pass `cost_R <= 0.20` | 151 | 342 | 327 |
| Unique after deduplication | 151 | 342 | 327 |
| **Non-overlapping (120h)** | **71** | **156** | **150** |
| Median `cost_R` (feasible) | **0.0898** | 0.0876 | 0.0881 |
| Feasible share of valid triggers | **0.774** | 0.769 | 0.762 |
| Non-overlapping per active year | **20.9** | 44.6 | — |

The primary arm fails the pre-registered decision rule on frequency alone:

- `N_non_overlapping = 71`, below the `150` floor and far below the `349` independent-sample
  reference.
- Median `cost_R = 0.0898 <= 0.20` — the cost gate itself is not the problem.
- Feasible share `= 0.774 >= 0.25` — the gate is not discarding most of the sample.

The control is **not** promoted. It is a selectivity diagnostic; its count is not an alternative
strategy result.

---

## 2. Frozen signal definition (summary)

The Stage 2B recommendation is the primary hypothesis source. Stage 2B left the regime, pullback,
confirmation, stop, cooldown, and overlap rules qualitative; the Stage 2C specification resolves
each placeholder before counting. The complete definition is in the specification; the operative
rules are:

| element | frozen rule |
|---|---|
| Regime timeframe | 4h, closed bars |
| Regime | `close > SMA200` **and** `SMA200[t] > SMA200[t-20]` (strict) |
| Regime confirmation timing | a 1h bar opening at `T` uses the most recent 4h bar whose `close_time < T` |
| Signal timeframe | 1h, closed, usable bars |
| Pullback start | `close[i] < EMA20[i]` and `close[i-1] >= EMA20[i-1]` |
| Reference high `R` | `high[i-1]` (the last 1h high at or above the EMA) |
| Pullback low `L` | lowest 1h low from the crossunder bar through the confirmation bar |
| Resumption | `close[j] > R`, strictly, with `j > i` |
| Invalidation | regime flip before confirmation, 72-bar pullback age, or 15% pullback depth; invalidation is evaluated **before** confirmation |
| Signal timestamp | `close_time` of confirmation bar `j` |
| Entry | open of the 5m bar at `open_time[j] + 1h`; missing/unclosed/zero-volume entry is rejected |
| Stop | `L`; signal rejected if `L <= 0`, entry `<= 0`, or entry `<= L` |
| Cost gate | `cost_R = 0.0026 * entry / (entry - L) <= 0.20` |
| Duplicate | same entry timestamp (verified; none occurred) |
| Primary cooldown | none beyond one signal per pullback episode |
| Conservative overlap view | greedy 120h separation on entry timestamps |
| Primary clustering view | maximal run of 4h bars with `regime_up == true` |

The 1h signal timeframe and 4h regime timeframe were chosen before counting. The 1h choice is an
engineering judgment: a 15m pullback range is usually too narrow to produce the stop the 0.20R gate
requires at 26 bp, while a 1h pullback is coarser than the already-censused 4h breakout. No
parameter was selected by looking at Stage 2C counts.

**Ambiguities resolved before counting:** Stage 2B's "moving average with slope/structure" became
the 4h SMA200 plus 20-bar slope; "recent swing area or MA zone" became the 1h EMA20 crossunder and
pre-crossunder high; "close above pullback high" became a strict close above `R`; "one position
logic or explicit rules" became one signal per episode plus the 120h non-overlap view. These are
documented in the specification, not discovered after counting.

---

## 3. Data scope and alignment

Only the development interval was loaded. The reader stops immediately after the final development
bar and does not decode the first out-of-window observation.

| series | bars in interval | expected | missing | duplicates | off-grid | unclosed | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 5m | 367,563 | 367,776 | 213 (7 gaps) | 0 | 0 | 0 | PASS with documented gaps |
| 1h | 30,634 | 30,648 | 14 | 0 | 0 | 0 | PASS with documented exceptions |
| 4h | 7,662 | 7,662 | 0 | 0 | 0 | 0 | PASS with documented exceptions |

Key findings (full detail in `docs/research/STAGE2C_DATA_ALIGNMENT_AUDIT.md`):

- The seven 5m gaps account for all 213 missing 5m bars. They are vendor gaps, not reader errors.
- 1h reconstruction from 5m is exact on the fields the design reads (`high`, `low`, `close`) for all
  30,625 usable 1h bars. Seven 1h buckets are gap-adjacent partial buckets; all seven are exact on
  the used fields. Nine 1h bars are excluded: 5 partial-only, 2 last-5m-member zero-volume, and 2
  both partial and zero-volume. The 1h series is split into 8 contiguous segments; the EMA is
  re-initialised per segment.
- 4h reconstruction is exact on `close` for all 7,662 bars, including 12 gap-adjacent partial
  buckets. One `open` mismatch exists at `2023-03-24T3` (vendor `28079.99`, reconstructed
  `28080.00`); `open` is not read by the regime rule, and `close` is exact.
- Every signal entry timestamp exists on the 5m grid and is the first 5m bar after the confirmation
  close. Stop recomputation from the 1h bars matches the state-machine stop for every trigger. The
  cost formula recomputes exactly for every trigger.

**Warm-up:** the first valid 4h regime label is at 4h bar `2021-02-06T12:00:00Z`, which closes at
`15:59:59.999Z`; the first 1h bar allowed to use it opens at `2021-02-06T16:00:00Z`. The 1h EMA
needs 20 bars per segment. The primary active window is therefore 3.396 years, not 3.496. The
control is also reported on the same matched window, so the regime contrast is not confounded by a
longer control window.

---

## 4. Episode funnel — every exclusion accounted for

```
644  crossunder episodes
445  confirmed triggers
     − 170  max pullback age (72 bars)
     −  22  max pullback depth (15%)
     −   7  segment break (1h gap)
445  confirmed triggers
     − 224  regime not up at crossunder
     −  16  regime unknown (before first valid 4h label)
     −  10  regime flipped before confirmation
195  primary-eligible triggers
195  valid entry bar
195  valid structural stop
 −44  cost gate
151  feasible unique signals
 −80  inside a previous 120h window
 71  non-overlapping primary opportunities
```

The accounting check is exact: `445 + 170 + 22 + 7 = 644`. The confirmed split is exact:
`224 + 16 + 205 = 445`; of the 205 up-regime confirmations, 10 flipped before confirmation, leaving
195. The control funnel is the same LTF stream without the regime stages: `445 → 445 → 445 → 342
feasible → 156 non-overlapping`.

No trigger failed entry or stop validity. That is plausible because the 5m data has only seven gaps
and the structural stop is by construction below the entry for a confirmed resumption. It is
reported as a result, not assumed.

---

## 5. Primary candidate — cost/R and stop geometry

### 5.1 Cost/R

`cost_R = 0.0026 * entry_price / stop_distance`.

| bucket | valid triggers | % | feasible triggers | % |
|---|---:|---:|---:|---:|
| `<= 0.10` | 93 | 47.69% | 93 | 61.59% |
| `(0.10, 0.20]` | 58 | 29.74% | 58 | 38.41% |
| `(0.20, 0.30]` | 21 | 10.77% | 0 | 0% |
| `(0.30, 0.50]` | 14 | 7.18% | 0 | 0% |
| `> 0.50` | 9 | 4.62% | 0 | 0% |
| **Total** | **195** | **100%** | **151** | **100%** |

Primary valid `cost_R` distribution: median `0.1032`, mean `0.1614`, p10 `0.0462`, p25 `0.0700`,
p75 `0.1890`, p90 `0.3390`, min `0.0198`, max `1.1508`.
Feasible-only `cost_R`: median `0.0898`, mean `0.0954`, p10 `0.0449`, p25 `0.0657`, p75 `0.1203`,
p90 `0.1654`, min `0.0198`, max `0.1997`.

At 26 bp, `cost_R <= 0.20` is exactly equivalent to `stop_distance / entry >= 0.013`. The check
holds: 44 of 195 triggers have a stop below 1.30%, and 44 of 195 have `cost_R > 0.20`. The gate and
the stop-percentage condition agree exactly.

### 5.2 Stop distance

| measure | valid triggers (n=195) | feasible only (n=151) |
|---|---:|---:|
| median | 2.520% | 2.894% |
| mean | 2.842% | 3.432% |
| p10 | 0.767% | 1.572% |
| p25 | 1.376% | 2.162% |
| p75 | 3.712% | 3.958% |
| p90 | 5.625% | 5.786% |
| min | 0.226% | 1.302% |
| max | 13.105% | 13.105% |

The feasible minimum stop is `1.302%`, just above the `1.30%` implied by the gate. This is a
mechanical consequence of the frozen gate, not an independent filter. The widest feasible stop is
`13.105%`; a stop that wide lowers `cost_R` but implies a large position for a fixed risk budget
and substantial adverse price exposure. Low `cost_R` is not evidence of profitability.

Stop distance in USDT per BTC is also reported in the JSON. It scales with the BTC price level, so
the percentage is the more useful cross-period comparison.

---

## 6. Opportunity frequency and per-year distribution

The primary active window begins `2021-02-06T16:00:00Z` and ends `2024-06-30T23:59:59.999Z`, or
3.396 years.

| year | raw | valid stop | feasible | non-overlapping |
|---|---:|---:|---:|---:|
| 2021 | 68 | 68 | 61 | 21 |
| 2022 | 20 | 20 | 16 | 10 |
| 2023 | 71 | 71 | 50 | 27 |
| 2024 (Jan–Jun) | 36 | 36 | 24 | 13 |

The 2022 count is visibly lower. That is a property of the frozen regime filter and the 2022 bear
market, not a post-hoc exclusion. The 2024 row is a half-year.

Spacing of feasible signals: median `2.40` days, p10 `0.71`, p90 `11.88`. Spacing of
non-overlapping signals: median `7.96` days, p10 `5.38`, p90 `42.33`. The maximum gap is `111.3`
days. The non-overlapping count is `20.9` per active year; the raw feasible count is `44.5` per
active year.

Cooldown sensitivities (greedy, after the cost gate): 24h → 127; 72h → 87; 168h → 59. These are
diagnostics only and do not change the primary decision count of 71.

---

## 7. Control arm and the contribution of the regime filter

The control uses the **same** 1h crossunder, reference high, pullback low, confirmation, entry
timing, stop, cost model, and validity rules. It removes only the 4h directional-regime condition.
Both arms are evaluated on one shared LTF episode stream, so the primary is a strict subset of the
control.

| stage | primary | control | overlap | primary-only | control-only |
|---|---:|---:|---:|---:|---:|
| confirmed triggers | 195 | 445 | 195 | 0 | 250 |
| valid stop | 195 | 445 | 195 | 0 | 250 |
| feasible | 151 | 342 | 151 | 0 | 191 |
| non-overlapping | 71 | 156 | 56 | 15 | 100 |

The control-only feasible signals split by the regime label at the crossunder: 168 `not_up`, 15
`unknown`, 8 `flip`. The strict subset relation is verified.

The regime filter roughly halves raw frequency (`445 → 195`) and feasible frequency (`342 → 151`),
and reduces the non-overlapping count from `156` to `71`. The matched-window control count is `150`
non-overlapping, so the difference is not caused by the control's longer window. The regime filter
does add selectivity, but the result is still too few non-overlapping opportunities.

The control is **not** an alternative strategy and is **not** promoted. Its 150 matched-window
non-overlapping events would only reach the `PASS WITH LIMITATIONS` floor if it were the primary
arm; it is not.

---

## 8. Episode clustering and effective sample size

A raw signal count is not an independent sample. Two transparent views are reported.

### 8.1 View 1 — 4h regime episodes (primary clustering view)

- 67 up-regime episodes in the development interval.
- 24 of them contain at least one feasible primary signal.
- Median regime-episode duration: `0.67` days; p90 `24.17` days; maximum `80.0` days. The
  distribution is heavily skewed: many short episodes and a few long bull phases.
- Signals per signal-producing regime episode: median `3.5`, p90 `17`, maximum `21`.
- The largest regime episode contains `13.9%` of all feasible primary signals.
- Time between signal-producing regime-episode starts: median `42.3` days, p90 `109.0` days.
- Kish effective size across signal-producing regime episodes:
  `n_eff = (Σ n_k)^2 / Σ n_k^2 = 12.69`. This treats every signal in a regime episode as perfectly
  dependent, so it is a deliberately conservative lower bound on effective sample size.
- The cluster count is 24; the design effect against the 151 feasible signals is `11.9`.

### 8.2 View 2 — greedy 120h non-overlap (conservative event view)

`71` primary opportunities are separated by at least 120 hours (the maximum intended holding
horizon). This is the count used in the decision rule. It is the maximum number of non-overlapping
120h windows that can be selected (equal-length interval scheduling), not a portfolio simulation.

### 8.3 Effective sample-size assessment

| view | count | smallest detectable effect at 80% power, α=0.05 |
|---|---:|---:|
| raw feasible signals | 151 | `0.228R` |
| non-overlapping 120h events | 71 | `0.332R` |
| signal-producing regime episodes | 24 | `0.572R` |
| Kish effective size | 12.7 | `0.785R` |

The planning reference is 349 independent events for a `0.15R` effect at 80% power. **Even the most
generous count, 151 raw feasible signals, implies a smallest detectable effect of `0.228R`, which is
larger than the `0.15R` target.** The non-overlapping count of 71 is worse. The census therefore
fails the frequency requirement under every clustering view, not only under the most conservative
one.

The census cannot estimate an outcome-based dependence structure because no outcome is computed.
The Kish and cluster counts are design diagnostics, not a substitute for a formal dependence
analysis. What can be said is that the true effective sample is bounded above by 151 and is almost
certainly below it; no defensible reading makes 349.

---

## 9. Capital and execution geometry (no simulation)

At a fixed risk budget of 1% of $10,000 equity ($100 risk), the implied position notional is
`100 / stop_pct`:

| measure | implied notional (USD) | % of $10,000 equity |
|---|---:|---:|
| median | 3,456 | 34.6% |
| mean | 3,668 | 36.7% |
| p10 | 1,728 | 17.3% |
| p25 | 2,527 | 25.3% |
| p75 | 4,626 | 46.3% |
| p90 | 6,360 | 63.6% |
| min | 763 | 7.6% |
| max | 7,680 | 76.8% |

- 0 of 151 feasible signals require more than 100% of equity at this risk budget; 3 exceed 75%; 31
  exceed 50%.
- No position fails the $5 minimum notional or the `1e-5 BTC` lot step after rounding.
- At most 6 positions would be open simultaneously under a 120h holding assumption.
- 131 of 151 feasible signals occur within 120h of another signal; a strict one-position policy
  would skip 80 of them. This is a real execution constraint, but it is not the reason for the
  verdict: the decision count already accounts for it through the 120h non-overlap rule.

The capital geometry is not obviously impracticable at $10,000 equity with 1% risk. At smaller
equity, the implied notionals scale down proportionally and the minimum-notional check would become
more relevant. No cash path, portfolio, or P&L is modelled.

---

## 10. Sensitivity analyses (diagnostic only)

### 10.1 Cost multiples

| round-trip cost | pass `cost_R <= 0.20` | share of valid | median `cost_R` |
|---|---:|---:|---:|
| 10 bp | 186 | 95.4% | 0.0397 |
| **26 bp (primary)** | **151** | **77.4%** | **0.1032** |
| 39 bp (1.5×) | 122 | 62.6% | 0.1547 |
| 52 bp (2×) | 93 | 47.7% | 0.2063 |
| 78 bp (3×) | 40 | 20.5% | 0.3095 |
| 100 bp | 29 | 14.9% | 0.3968 |

The count is sensitive to the cost assumption but the verdict is not: at 3× the base cost only 40
triggers pass, and at the base cost the non-overlapping count is already 71. The gate is not
relaxed to obtain a pass.

### 10.2 Cooldowns

24h → 127; 72h → 87; 168h → 59 non-overlapping signals. All are below 150. The primary count (no
cooldown) is 71, so adding a cooldown cannot rescue the frequency.

### 10.3 Other diagnostics

Per-year counts are in §6. The 1h/4h alignment diagnostics are in §3 and the separate audit. No
parameter optimization, definition search, or outcome-based filtering was performed.

---

## 11. Resource usage

| item | value |
|---|---|
| Wall-clock runtime | 9.7 s |
| Peak RSS | 575 MiB |
| Target RAM | ≤ 4,096 MiB |
| Absolute ceiling | 6,144 MiB |
| Python | 3.14.6 |
| Platform | Linux 6.6.114.1 (WSL2), x86_64 |
| Memory strategy | streaming JSON reader; development interval only; one copy of each series; no O(n²) signal comparison |

The run is comfortably inside the target. The 5m series is the largest allocation; the 1h and 4h
series and the signal lists are small by comparison. No large intermediate dataframes were created.

---

## 12. Limitations

1. **This is not a backtest.** No trade is entered or resolved. No P&L, expectancy, win rate,
   drawdown, Sharpe, or profitability figure exists in this stage.
2. **The cost model is a Binance spot proxy.** 26 bp round trip is not a measured Nobitex cost. A
   Nobitex deployment would need its own fee, spread, slippage, and fill measurements.
3. **The definition is one instantiation of Stage 2B.** The 1h/4h choice and the 72-bar/15% guards
   are engineering decisions made before counting. A different defensible instantiation could
   produce a different count; this census does not search for a more attractive one.
4. **The 2021–2024 window is one market regime mix.** The 2022 bear market contributes relatively
   few signals. The result is conditional on this window.
5. **The non-overlapping count is a design count, not a tradable count.** It assumes a 120h maximum
   holding horizon and ignores the actual exit path. It does not model stops, targets, or funding.
6. **Effective sample size is not identified.** The Kish/cluster diagnostics are bounds and design
   heuristics; an outcome-based dependence estimate is not available at this stage.
7. **The control is not promoted.** Its higher frequency is evidence about the regime filter's
   selectivity, not evidence that the unconditioned strategy is profitable.
8. **2024 is a partial year.** The development interval ends 2024-07-01, so the 2024 row covers
   January–June only.
9. **Wide stops can be misleading.** A 13% stop produces a low `cost_R` but a large position and
   large adverse exposure. The cost gate alone is not a risk judgement.

---

## 13. Final verdict

**FAIL — insufficient opportunity frequency.**

The pre-registered rule requires `N_non_overlapping >= 150` for `PASS WITH LIMITATIONS` and
`>= 349` for `PASS`. The primary arm produces **71** non-overlapping feasible opportunities over
3.4 years, or **20.9 per active year**. Median `cost_R` is `0.0898` and the feasible share is
`0.774`, so the failure is specifically frequency, not cost geometry.

The result is robust to the clustering view: 151 raw feasible signals already imply a smallest
detectable effect of `0.228R` at 80% power, above the `0.15R` target; 71 non-overlapping events
imply `0.332R`; the 24 signal-producing regime episodes imply `0.572R`. No view reaches the
planning reference.

**A PASS would not have meant profitable; a FAIL does not prove the hypothesis is economically
false.** It means this frozen, causally specified version of the hypothesis does not produce enough
independent opportunities to justify a formal strategy experiment on this data. The control's higher
count does not change that conclusion and is not promoted.

**Recommended next action:** do not proceed to strategy implementation or performance testing for
this candidate. If the programme continues, the next step is a new Stage 2B-style hypothesis
selection, not a relaxation of this gate or a search over pullback parameters.

---

## 14. Artifacts

| artifact | path |
|---|---|
| Frozen specification | `stage2c_census/STAGE2C_SIGNAL_SPECIFICATION.md` |
| Machine configuration | `stage2c_census/stage2c_config.json` |
| Freeze record | `stage2c_census/freeze.json` |
| Census code | `stage2c_census/census.py` |
| Raw census result | `stage2c_census/census_result.json` |
| Manifest | `stage2c_census/manifest.json` |
| This report | `docs/research/STAGE2C_FEASIBILITY_CENSUS.md` |
| Curated JSON | `docs/research/STAGE2C_FEASIBILITY_CENSUS.json` |
| Alignment audit | `docs/research/STAGE2C_DATA_ALIGNMENT_AUDIT.md` |

Hashes for the dataset, specification, configuration, code, and outputs are in
`stage2c_census/manifest.json`.

---

## 15. Confirmation

No P&L, return, expectancy, win rate, drawdown, Sharpe, CAGR, or profitability calculation was
performed. No backtest, portfolio simulation, bootstrap, Monte Carlo, parameter optimization, or
outcome-based filtering was run. No validation or OOS observation was used to initialize an
indicator, construct a signal, count an event, or compute a statistic. The reader stops immediately
after the final development bar and does not decode the first out-of-window observation. No frozen
Stage 2A, Stage 2B, Stage 6, Stage 6A, or Setup 1 artifact was modified.
