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

---

## 4. F2 — Stop geometry and transaction cost

### 4.1 The arithmetic that governs every candidate

```
cost_R = 0.0026 × entry_price / stop_distance = 0.0026 / stop_fraction
```

At 26 bp, the gate `cost_R ≤ 0.20` is exactly `stop_fraction ≥ 0.013`, i.e. a 1.30% stop. The gate is
therefore a **stop-size filter** in disguise. It does not judge whether the stop is structurally
meaningful; it judges whether the stop is wide enough to absorb the assumed round trip.

**Verified fact — the identity reproduces every reported median:**

| candidate | population | median `cost_R` | implied stop | stop reported in artifact |
|---|---|---:|---:|---|
| A | valid triggers, n=195 | 0.1032 | 2.519% | 2.520% |
| A | feasible, n=151 | 0.0898 | 2.895% | 2.894% |
| B | pre-gate, n=32 | 0.086505 | 3.006% | not reported as a percentage |
| C | all triggers, n=17 | 0.124 | 2.097% | 2.10% |
| D | pre-gate, n=295 | 0.322559 | 0.806% | not reported as a percentage |

The B and D implied stops are Stage 2K arithmetic from the reported medians, not values printed in
the census reports. They are **Interpretation**, consistent with the frozen identity.

### 4.2 How much of each population the gate removes

| candidate | pre-gate | passing | failing | feasible share |
|---|---:|---:|---:|---:|
| A | 195 | 151 | 44 | 0.774 |
| B | 32 | 29 | 3 | 0.906 |
| C | 17 | 12 | 5 | 0.706 |
| D | 295 | 45 | **250** | **0.153** |

**Verified fact:** the cost gate is the dominant filter only for D. For A and C it removes roughly a
quarter to a third; for B it is almost irrelevant.

### 4.3 Pre-declared cost sensitivities (gate fixed at 0.20)

| round trip | A passing | B passing | C passing | D passing |
|---|---:|---:|---:|---:|
| 10 bp | 186 | 32 | 17 | 253 |
| **26 bp (primary)** | **151** | **29** | **12** | **45** |
| 39 bp | 122 | 25 | 9 | 8 |
| 52 bp | 93 | 21 | 2 | 2 |

Sources: Stage 2C §10.1; Stage 2J B report §4; Stage 2A §6.1; Stage 2J D report §4.

### 4.4 What a cheaper venue could and could not fix

**Verified fact — upper bounds independent of cost:**

- B's entire pre-gate population is 32. No cost assumption can produce more than 32 canonical 72h
opportunities, which remains far below 150.
- C's entire trigger population is 17. No cost assumption can produce more than 17, below the 200
gate.
- A's entire pre-gate population is 195. A zero-cost world could at most reach 195 before overlap,
  so 150 is arithmetically possible only if the overlap rule removed fewer than 45 of them. At the
  primary cost it removed 80 of 151.
- D's pre-gate population is 295. A very low cost could in principle leave more than 150 after
  non-overlap, but that count **was not computed**.

**Interpretation:** a lower venue cost cannot rescue B or C at all, and can rescue A only if the
overlap loss also shrinks. It is a live but unmeasured possibility for D.

**Verified fact:** the 10 bp row is below the 20 bp that the proxy's 0.1% fee per side alone
contributes. Reaching the 10 bp row would require a venue whose all-in round trip is materially
cheaper than the proxy's fee component, not merely a venue with a tighter spread.

**Warning — the 26 bp figure is a Binance research proxy, not a verified Nobitex execution cost**
(Verified fact: every candidate specification and `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §4). Stage
2K does not assert that Nobitex is cheaper or more expensive.

**What evidence would be required to make a venue claim:**

1. the venue's actual maker and taker fee schedule, and whether a resting limit order is achievable
   for these entries;
2. a measured bid-ask spread distribution for BTCUSDT at the times the signals fire;
3. realised slippage from fills, not an assumed 3 bp;
4. minimum notional, lot step, tick size, and whether the sizes implied by 1% risk are executable;
5. order-book depth at the entry and exit moments;
6. outage and maintenance behaviour, since two of the seven data gaps fall inside the development
   interval.

**How a future sensitivity study should be designed (not performed here):** pre-register the cost
scenarios and the gate; recompute `cost_R` from the already-frozen signal set; recompute the canonical
non-overlap count for each scenario, not only the gate-pass count; report the count and the cost
median together; and keep the frozen verdicts unchanged. The study would need explicit owner
authorization and must not read validation or out-of-sample rows.

### 4.5 Is the problem structural or venue-specific?

| element | status |
|---|---|
| A tight structural stop consumes a large fraction of R | **Verified fact** for C (0.54%–1.00% stops at the 10th percentile) and D (implied median 0.806%) |
| The gate mechanically excludes tight-stop designs | **Verified fact** — it is arithmetic |
| The 26 bp level is correct for the intended venue | **Unknown** |
| A cheaper venue would raise D above 150 canonical | **Unknown** — not computed |
| A cheaper venue would raise A, B or C above their floors | **Verified impossible for B and C; unlikely for A** — bounded by pre-gate populations |
| The cost gate is too strict as a research threshold | **Interpretation** — it is a project choice, but Stage 2K has no evidence for a better value |

**Interpretation:** the stop-geometry problem is partly structural (a compression or ATR stop is
small by construction) and partly a cost-assumption problem (26 bp is unverified). The record cannot
separate the two for D, and for B and C the separation does not matter because the pre-gate ceiling
is already below the floor.

---

## 5. F3 — Regime and timeframe restrictions

### 5.1 The regime states are minority states

**Verified facts from `stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §4.3:**

| state | true | false | unknown | maximal true runs |
|---|---:|---:|---:|---:|
| B 4h permission | 1,826 | 5,284 | 552 | 171 |
| D 4h volatility budget | 2,863 | 4,247 | 552 | 212 |

Of 7,662 4h bars, B permits 23.8% and D budgets 37.4% (raw shares; excluding the 552 warm-up
`Unknown` bars gives 25.7% and 40.3%).

### 5.2 What each regime condition removed

| candidate | condition | removed | share of the relevant population |
|---|---|---:|---:|
| A | 4h regime not up / unknown / flipped before confirmation | 250 of 445 confirmed | 56.2% |
| B | permission false or unknown at the expansion bar | 341 of 458 attempts | 74.5% |
| D | volatility budget out of band or warm-up | 595 of 927 directional signals | 64.2% |
| D | first-two-hour threshold not met | 2,902 of 3,829 sessions | 75.8% |
| C | no regime condition | — | — |

**Verified fact:** every regime-conditioned candidate loses most of its raw population to conditions,
not to costs. C, which has no regime condition, loses its population to the rarity of the compression
state instead.

### 5.3 Signal timeframe versus holding and non-overlap horizon

| candidate | signal timeframe | canonical overlap | stated holding basis | match |
|---|---|---|---|---|
| A | 1h | 120h | 120h maximum intended hold | internally consistent, conservative relative to an average hold |
| B | 1h | 72h | 3-day horizon | matched |
| C | 4h | 3-day hold; no cooldown | 18 × 4h | matched; overlap not binding |
| D | 15m | 24h | 6h session (8h session bound reported) | 24h is four times the stated session hold |

**Interpretation:** the overlap horizon is not systematically mismatched. It is most conservative for
D (24h versus a 6h session), and most costly for A because 120h is a maximum rather than an expected
hold. Those two choices discard 11 and 80 feasible signals respectively. They are project choices,
not market facts, but changing them after seeing counts would be a new hypothesis, not a correction.

### 5.4 Spot-only, long-only, and the "5-minute" framing

- **Spot-only, long-only, no leverage** is a binding research assumption (all candidate specs §0).
  No artifact measures the counterfactual. Whether removing it would add opportunities is **Unknown**;
  that a short leg would add *some* opportunities is a **Hypothesis**, not a measurement. Short-side
  liquidity provision carries its own adverse-selection and borrow constraints that this project has
  not studied.
- **The signal timeframes are not 5 minutes.** A and B signal on 1h, C on 4h, D on 15m. The 5m series
  serves as the entry/alignment grid for A and C and as a bucket-membership diagnostic for B and D.
  The cost tension is a function of **stop size**, not of the sampling grid. A claim that "the 5m
  framework is incompatible with the cost model" is therefore **not demonstrated**; the demonstrated
  claim is narrower: 15m- and ATR-based stops are small relative to 26 bp.
- **C's "structural incompatibility" with 5m** is not established. C's failure is the six-bar
duration floor on 4h bars, which has nothing to do with 5m sampling.

### 5.5 Demonstrated versus hypothesised

| claim | status |
|---|---|
| Higher-timeframe regime conditions remove most raw signals | **Verified fact** |
| The regimes are mis-specified or too strict | **Hypothesis** — no relaxed-regime census exists |
| The overlap horizons are mismatched to expected holding | **Interpretation** for A and D; matched for B and C |
| Spot-only long-only is the binding constraint | **Hypothesis** — no counterfactual measured |
| The 5m framework is structurally incompatible with the cost model | **Not supported** — the binding variable is stop size |
| The strategy family is incompatible with the selected framework | **Unknown** — the four failures are consistent with it, but do not establish it |
