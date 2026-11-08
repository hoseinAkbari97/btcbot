# Stage 2K — Failure-Mode Analysis

**Stage:** 2K (review only).
**Scope:** why the four reviewed candidates failed their feasibility gates, and which of the causes are
structural, which are research-assumption choices, and which are project decision thresholds.
**Evidence base:** `HISTORICAL_RESEARCH_SYNTHESIS.md` and the artifacts it cites. No market data was
processed for this document. No count, test, backtest or inference was produced here.

Evidence labels: **Verified fact**, **Interpretation**, **Hypothesis**, **Unknown** (defined in the
synthesis, Section 0).

---

## 1. Method and limits

The analysis uses only counts, medians, shares and thresholds that already exist in the Stage 2A,
2C and 2J artifacts. It does not:

- recompute a funnel;
- reclassify a rejected signal;
- estimate what a changed rule would have produced;
- infer an outcome or an edge;
- attribute a cause with statistical confidence.

Where a causal statement goes beyond the recorded counts it is labelled **Interpretation** or
**Hypothesis**. The distinction matters: a funnel shows *where* the population was lost, not *why* the
market produced so few setups.

---

## 2. Failure-mode taxonomy

| id | failure mode | definition | primary evidence |
|---|---|---|---|
| **F1** | Opportunity frequency | The frozen design produces too few deduplicated, non-overlapping opportunities to meet the project floor | all four censuses |
| **F2** | Stop geometry and transaction cost | The structural stop is small relative to the round-trip cost proxy, so `cost_R` fails the gate or the survivor set is a narrow slice | D strongly, A/C moderately, B weakly |
| **F3** | Regime and timeframe restriction | A higher-timeframe condition, signal horizon, or overlap rule removes most of the population | A and B strongly, D moderately, C not at all |
| **F4** | Concentration and effective evidence | Opportunities cluster in a few regimes or episodes, so the nominal count overstates independent evidence | A and D; B has a calendar-view signal; C is sparse everywhere |
| **F5** | Research-design limitation | A frozen definition, threshold, or horizon is a project choice that binds the result, rather than a property of the market | all four, to differing degrees |
| **F6** | Evidence and governance limitation | The record cannot support a stronger conclusion because of proxy costs, a self-audit, one market path, or missing censuses | project-wide |

These modes are not exclusive. A candidate can fail F1 because F3 removed most of its population;
in that case F3 is the mechanism and F1 is the verdict.

---

## 3. F1 / F3(A) — Opportunity frequency

### 3.1 The funnel end-points

| candidate | pre-gate population | cost-feasible | canonical non-overlapping | floor | shortfall |
|---|---:|---:|---:|---:|---:|
| A | 195 | 151 | **71** (120h) | 150 | 79 |
| B | 32 | 29 | **24** (72h) | 150 | 126 |
| C | 17 | 12 | **12** (3-day hold) | 200 (Stage 2A) | 188 |
| D | 295 | 45 | **34** (24h) | 150 | 116 |

**Verified fact.** No candidate is within 50% of its applicable floor. A is the closest at 47% of 150;
B at 16%, D at 23%, C at 6% of 200.

### 3.2 Was the signal simply rare, or was the rule conjunction restrictive?

Both, and the record can separate the two at the funnel level but not at the market level.

**Verified facts:**

- **A:** 644 crossunder episodes exist; 445 confirm; the 4h regime admits 195 (43.8% of confirmed);
  cost admits 151; 120h overlap admits 71. The regime filter and the overlap rule each remove about
  half of what remains.
- **B:** 503 expansion bars occur in 30,625 usable 1h bars. They form 458 episode attempts. The 4h
  permission admits 117 (25.5%); structural validation admits 34 (29.1% of regime-qualified). Cost
  removes 3 and overlap 5. Almost the entire loss is the conjunction of a rare 1h event with a
  minority 4h state and a strict retest/resumption sequence.
- **C:** 461 compression episodes exist; only 63 last six bars. The six-bar duration floor is the
  binding constraint, before breakout confirmation and cost. No threshold relaxation recovers more
  than 17 triggers from those 63 episodes.
- **D:** 3,829 evaluable sessions produce 927 directional signals (24.2%). The volatility budget
  admits 332 (35.8%). VWAP admits 296. Cost admits 45 (15.3%). Here the conjunction is not the main
  loss: the cost gate is.

**Interpretation:** A and B are "rare state × strict conjunction" failures. C is a "rare state" failure.
D is a "cost geometry" failure that also fails frequency. They are different mechanisms that happen
to produce the same verdict.

### 3.3 Did non-overlap materially reduce the population?

| candidate | feasible | canonical | rejected by overlap | share lost |
|---|---:|---:|---:|---:|
| A | 151 | 71 | 80 | 53.0% |
| B | 29 | 24 | 5 | 17.2% |
| C | 12 | 12 | 0 | 0.0% |
| D | 45 | 34 | 11 | 24.4% |

**Verified fact:** non-overlap is material only for A. For C it is irrelevant because no two triggers
fell inside the 3-day hold (Stage 2A §3.2). For B and D it removes roughly one in five.

**Interpretation:** the non-overlap rule cannot be the general explanation for the failures. It is a
secondary constraint for A, and negligible for B, C and D.

### 3.4 Were opportunities concentrated in a few market episodes?

**Verified facts:**

- A: 67 up-regime episodes exist; 24 contain at least one feasible signal; the largest contains
  13.9% of feasible signals; median 3.5 signals per signal-producing episode; maximum 21
  (Stage 2C §8.1).
- B: 171 maximal permission runs; 21 non-empty clusters on the S8 population; largest cluster 3 of
  29 (10.34%); canonical 2 of 24 (8.33%) (Stage 2J B report §6).
- C: events are not time-clustered; median gap 84.2 days between feasible events and 0 pairs closer
  than the 3-day hold (Stage 2A §3.2).
- D: 212 maximal budget runs; 20 non-empty clusters on S7; largest 8 of 45 (17.78%); all 34 canonical
  signals fall in 2021–2022, with none after 2022-09 (Stage 2J D report §6).

**Interpretation:** frequency is not merely low; for A and D it is also unevenly distributed. That
matters for any future sufficiency rule, because a count of 71 or 34 does not buy 71 or 34 independent
observations.

### 3.5 Opportunity density against the calendar ceiling

The development interval is 1,277 days. The maximum number of non-overlapping windows is
`floor(1277 / H_days)`: 425 at 72h, 1,277 at 24h, 255 at 120h.

**Verified fact:** B used 5.6% of its 72h ceiling, D 2.7% of its 24h ceiling, A 27.8% of its 120h
ceiling, and C 19.0% of the 63-episode state ceiling. The calendar was never the binding limit, except
in the weak sense that a long horizon lowers the ceiling.

**Unknown:** whether the low capture rate is a property of BTC (few such setups) or of the frozen
definitions (too many simultaneous conditions). The censuses were designed to count, not to decompose
the two. A decomposition would require a pre-registered ablation of conditions, which Stage 2K is not
authorized to run.
