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

---

## 6. F4 — Concentration and effective evidence

### 6.1 What the two diagnostics mean

The Stage 2J concentration criterion is met if **either** the largest non-empty 4h regime cluster
contains more than 50% of the population **or** the Kish design effect `N / n_eff` is at least 2.00,
where `n_eff = (Σ n_k)² / Σ n_k²` over non-empty clusters
(`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §5; `stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §3.1).

- The **largest-share** component asks whether one episode dominates.
- The **design-effect** component asks whether the population is spread thinly across many small
  clusters rather than concentrated in a few large ones.
- They can disagree, and they do.

### 6.2 Recorded values

| candidate / population | N | non-empty clusters | largest share | Kish `n_eff` | design effect |
|---|---:|---:|---:|---:|---:|
| A — feasible signals, regime episodes | 151 | 24 | 0.139 | 12.69 | 11.9 |
| B — S8 cost-feasible | 29 | 21 of 171 | 0.1034 | 17.16 | 1.69 |
| B — S10 canonical | 24 | 21 of 171 | 0.0833 | 19.20 | 1.25 |
| B — calendar quarter view | 29 | 9 | 0.2759 | — | 4.93 |
| B — permission-decile view | 29 | 8 | 0.2069 | — | 3.97 |
| D — S7 cost-feasible | 45 | 20 of 212 | 0.1778 | 11.44 | **3.93** |
| D — S9 canonical | 34 | 19 of 212 | 0.1765 | 11.12 | 3.06 |
| D — S6 pre-gate view | 295 | 111 of 212 | 0.0712 | 51.96 | 5.68 |
| D — session-id view | 45 | 3 | 0.3556 | — | 15.13 |
| D — calendar-quarter view | 45 | 5 | 0.3778 | — | 11.62 |
| C — all events | 12 | — | — | — | not computed |

Sources: Stage 2C §8.1; Stage 2J B report §6; Stage 2J D report §6. Dashes mean the artifact does not
report the value; Stage 2K did not compute it.

### 6.3 What the diagnostics actually tell us

**Verified fact:** B does not meet the pre-declared screen on its primary S8 population (design
effect 1.69) or on the canonical S10 population (1.25), but its calendar-quarter view gives a design
effect of 4.93 and a largest share of 27.6%. The screen result is therefore **view-dependent**.

**Verified fact:** D meets the screen on the primary S7 population (3.93) and on the canonical S9
population (3.06). Its largest-share component is below 50% in both, so the design-effect component is
what triggers the screen.

**Verified fact:** D's canonical 34 signals all fall in 2021–2022, and no cost-feasible signal occurs
after 2022-09. That is a stronger statement than any cluster statistic: the opportunity set is
confined to a subset of the development interval.

**Interpretation:** the largest-share component is insensitive to dispersion across many small
clusters, while the design-effect component is sensitive to it. A candidate can be "not concentrated"
because no single episode dominates and still have an effective sample far below its nominal count.

### 6.4 Why non-overlap does not establish independence

Non-overlap is a greedy construction on entry timestamps. It guarantees that selected entry windows
do not overlap in clock time. It does **not** guarantee that the selected opportunities are
independent observations, because:

1. Opportunities in the same trend, volatility regime, or macro episode share common drivers even
   when their holding windows do not overlap.
2. A greedy earliest-first rule can select a whole sequence from one favourable regime and skip a
   later cluster, so the selected set inherits the regime's dependence.
3. Returns can be serially correlated across non-overlapping windows through volatility clustering
   and slow-moving regimes.
4. The dependence structure of **outcomes** cannot be estimated from a census that observes no
   outcomes.

**Verified fact:** both the Stage 2J final decision and the Stage 2C report state explicitly that
non-overlapping observations are not independent observations
(`stage2j/STAGE2J_FINAL_DECISION.md` §3; `STAGE2C_FEASIBILITY_CENSUS.md` §8.2–§8.3).

### 6.5 Why Kish must not be read as a serial-dependence estimator

Kish's `n_eff` is the effective size under **perfect within-cluster correlation and zero
between-cluster correlation**. It is a concentration diagnostic and a deliberately conservative bound
for that assumed structure. If within-cluster correlation is below 1, the true effective sample is
larger than Kish; if dependence spans clusters (for example two adjacent 4h runs in the same trend),
the true effective sample can be smaller. The artifact states this limitation in
`stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §3.1, and the protocol prescribes a `rho` sensitivity
(`n_eff(ρ) = N / (1 + (m̄ − 1)ρ)` for ρ ∈ {0.25, 0.50, 0.75, 1.00}) precisely so that no single
number is presented as the effective sample size.

**Interpretation:** substituting `n_eff` into the independence-based detectable-effect formula is
illustrative only. It would raise the smallest detectable effect above the already-reported values
(0.332R for A at 71, 0.572R for B at 24, 0.480R for D at 34, 0.809R for C at 12), but it is not a
power calculation and must not be quoted as one.

### 6.6 Does the concentration weaken confidence in the opportunity count?

| candidate | assessment |
|---|---|
| A | **Yes.** 24 signal-producing regime episodes, Kish `n_eff` 12.69, largest episode 13.9%. The nominal 151 feasible / 71 canonical overstate independent evidence. |
| B | **Mildly.** The primary screen passes (1.69) and the canonical screen passes (1.25), but the quarter view (4.93) shows calendar concentration. The nominal 24 is not 24 independent draws. |
| C | **Moot.** 12 events spread over 3.5 years with no pair inside the 3-day hold; the failure is scarcity, not clustering. |
| D | **Yes, strongly.** Design effect 3.93 on the primary population, 3.06 on the canonical set, all signals in 2021–2022, and quarter/session views worse. |

**Interpretation:** concentration does not change any recorded verdict — every candidate already
fails on count. It changes what a future sufficiency rule would have to require: a nominal count of
150 would not be enough if the design effect is near 4.

---

## 7. F5 — Research-design limitations

These are questions about the design, not permission to alter frozen rules. Each is recorded as a
possible attribution, with its evidential status.

### 7.1 Conjunctive definitions

**Verified fact:** B requires an expansion bar, 4h permission at the expansion bar, a retest touch
within six bars, penetration no deeper than 0.50 ATR, resumption within three bars, 4h permission at
confirmation, a valid stop, the cost gate, and the 72h overlap rule. From 30,625 usable 1h bars this
yields 24 opportunities.

**Interpretation:** each condition is defensible in isolation; their conjunction is the design. The
census cannot say which condition is "too strict" because no condition was ablated.

### 7.2 Thresholds that dominate the population

| threshold | candidate | effect |
|---|---|---|
| duration ≥ 6 bars | C | caps the sample at 63 episodes before any other rule |
| 4h regime conjunction | A, B | removes 56% and 74.5% of the relevant populations |
| 4h volatility budget | D | removes 64% of directional signals |
| 26 bp cost gate | D | removes 84.7% of pre-gate sessions |
| 120h overlap | A | removes 53% of feasible signals |

**Interpretation:** these five choices, not the market alone, determine the observed counts. Whether
a different value is defensible is a separate question that would require a new pre-registration.

### 7.3 The sufficiency rule does not match the stated effect of interest

This is the deepest design limitation in the record.

**Verified arithmetic:** under the project's own assumptions (σ = 1R, α = 0.05 two-sided, 80% power,
independence), the smallest detectable effect is `2.801585 / √N`:

| N | smallest detectable effect |
|---:|---:|
| 349 | 0.150R (the stated target) |
| 150 | 0.229R |
| 71 (A) | 0.332R |
| 34 (D) | 0.480R |
| 24 (B) | 0.572R |
| 12 (C) | 0.809R |

**Verified fact:** the 349 reference is what the stated 0.15R target requires under independence. The
150 floor is only sufficient for an effect near 0.23R, and no candidate's count is sufficient for
0.15R.

**Interpretation:** the programme has been applying a **sample-size floor** (150) that is inconsistent
with its own **effect-size target** (0.15R). A candidate could have passed the 150 floor and still
been unable to detect the effect the project says it cares about. This is a research-design mismatch,
not a market finding.

### 7.4 Candidate selection was frequency-first, and the frequency judgement failed

**Verified fact:** Stage 2D recommended B and D explicitly on feasibility grounds: B because a 72h
horizon has a 425-episode calendar ceiling; D because it was "the only candidate with a credible path
to the 150 floor" (`STAGE2D_STRATEGY_RECOMMENDATION.md` §1, §3). Both then failed frequency.

**Interpretation:** ex ante frequency intuition was unreliable in both recommended cases. That is an
argument against selecting the next candidate on a similar judgement without a pre-count bound.

### 7.5 One-shot instantiation

Each candidate was frozen once and counted once. No parameter was tuned in the decision path, which
protects the census from overfitting but limits the conclusion: the verdict is about **this
instantiation**, not about the hypothesis family as a whole. The reports say this explicitly (for
example Stage 2C §12 item 3).

### 7.6 Missing controls and missing ablations

- A and C have unconditioned control arms, but neither control was promoted and C's control stop was
  a provisional substitute.
- B and D have no outcome control arm.
- No condition was ablated in any census, so the marginal contribution of each condition to the
  population loss is unmeasured.

**Interpretation:** the record can say which conjunction failed; it cannot say which element of the
conjunction is responsible.

---

## 8. Structural constraints versus project choices

This is the distinction the Stage 2K brief requires. A **structural** item is potentially inherent in
the market, instrument or strategy family. A **research assumption** is a condition chosen for this
setup. A **project threshold** is a rule chosen to decide whether research proceeds. Only the first
category is a market claim; the other two are decisions.

### 8.1 Structural or market-related constraints

| item | what it means | evidence status | what remains unknown | how changing it would affect interpretation |
|---|---|---|---|---|
| **Opportunity density of the setup family** | Few qualifying setups occur in 3.5 years once the frozen conjunctions are applied | **Verified fact** that the counts are low; **Unknown** whether the cause is the market or the definitions | Whether an unconditioned or less-conditioned version is denser (partly measured for A and C controls) | Cannot be changed; if structural, no filter design will fix it |
| **BTC volatility level and its variation** | Stop size in percent is largely a volatility property; `cost_R` is inverse to it | **Verified fact** that implied stops span roughly 0.8% (D) to 3.0% (B); **Verified fact** that D has no cost-feasible signal after 2022-09 | Whether the 2023–24 low-volatility state is persistent | A permanently lower-volatility market makes tight-stop designs permanently cost-infeasible |
| **Cost relative to stop distance** | A round trip consumes a fixed fraction of R determined by stop size | **Verified fact** as arithmetic; the 26 bp level itself is a proxy | The true venue cost | If true cost is higher, every count falls; if lower, only D's population changes materially |
| **Clustering of opportunities in regimes** | Signals arrive in episodes rather than evenly | **Verified fact** for A and D; view-dependent for B; absent for C | The outcome dependence structure | Lower effective sample than nominal; affects any sufficiency rule |
| **Continuous 24/7 trading and vendor gaps** | No session close; the dataset has 7 gaps | **Verified fact** (213 missing 5m bars, 12 exempt 4h buckets) | Whether the gaps are exchange outages or vendor omissions | Handled by protocol; does not explain the counts |
| **Fat tails and jump reversal** | Large moves may exhaust rather than continue, competing with B and C | **Hypothesis** — no outcome was observed | Whether continuation or reversal dominates after an expansion | If reversal dominates, the family's premise is wrong, not merely rare |
| **Long-only upside asymmetry** | Spot long-only cannot express downside continuation | **Hypothesis** | The size of the missing opportunity set | Not measurable from this record; would require a short-leg study |

### 8.2 Research and execution assumptions

| item | what it means | evidence status | what remains unknown | how changing it would affect interpretation |
|---|---|---|---|---|
| **Spot-only, long-only, no leverage** | Mandate constraint applied to every candidate | **Verified fact** as a specification, **unmeasured** as an effect | Counterfactual opportunity count with a short leg | Removing it changes the hypothesis, not just the sample; prior verdicts would not transfer |
| **26 bp round-trip Binance proxy** | Fee plus adverse-execution estimate | **Verified fact** as the assumption; **not verified** for Nobitex | Real fees, spread, slippage, depth | A lower verified cost raises D's feasible share sharply; B and C remain below their floors by construction |
| **5m dataset and execution/alignment grid** | 5m is the entry grid for A and C and a membership diagnostic for B and D | **Verified fact** | Whether a coarser execution grid changes stop geometry | Little effect on counts; the binding variable is stop size, not sampling frequency |
| **Signal timeframes (1h, 4h, 15m)** | Chosen per candidate before counting | **Verified fact** | Whether another timeframe combination would be denser | Changing it creates a new hypothesis; no prior verdict applies |
| **Indicator constructions** | Wilder ATR(14), SMA50/200, EMA20, 540-bar percentile, HLC3 VWAP, session UTC | **Verified fact** | Sensitivity to each construction | Any change is a new specification and requires a new freeze |
| **Development interval 2021-01-01 → 2024-07-01** | One 1,277-day path | **Verified fact** | Behaviour in other periods | Extending it would consume validation/OOS data and requires separate authorization; per-year rates suggest the floor would still be hard to reach |
| **Next-bar-open entry, no explicit slippage** | Causal fill assumption | **Verified fact** | Realised fill quality | A worse fill raises effective cost without changing the signal counts |
| **$10,000 equity, 1% risk, one position** | Capital geometry basis | **Verified fact** | Scalability at other equity | Capital was not the binding constraint in any verdict; no capital violation was found on the cost-feasible populations |
| **UTC sessions (D only)** | Research convention for intraday anchoring | **Verified fact**, and the specification denies any claim that the equity result transfers | Whether session-relative behaviour exists at all in BTC | A null result would be a genuine refutation of D's premise, not a convention failure |
| **Implementation conventions B-1, C-1, M3** | Regime-failed episodes occupy the slot; capital check on cost-feasible population; 4h supplied-bar exemption | **Verified fact**, fixed before counting | Alternative conventions' effect on counts | M3 sensitivity changes B to 18 and D to 22 canonical; neither verdict direction changes |

### 8.3 Project-specific decision thresholds

| item | what it means | evidence status | what remains unknown | how changing it would affect interpretation |
|---|---|---|---|---|
| **150-opportunity floor** | The count required to proceed | **Project choice** from the Stage 2C freeze, with no statistical derivation (`stage2e_v2/CANDIDATE_B_SPEC.md` §0.1, §11.3) | Why 150 rather than a derived number | Lowering it after seeing counts would invalidate the pre-registration; deriving it beforehand is a legitimate but separate decision |
| **200-opportunity gate (Stage 2A only)** | The earlier floor used for C | **Project choice**, inconsistent with the later 150 | Why it changed | The 200 and 150 results are not directly comparable; C would still fail either |
| **349 tier boundary** | Top-tier label for `N ≥ 349` | **Planning reference** under independence, 0.15R, σ=1R, 5% two-sided, 80% power | Nothing statistically; it is an assumption set | It is not a requirement and not a power result for this design; treating it as one would overstate precision |
| **`cost_R ≤ 0.20`** | Maximum round-trip cost as a fraction of R | **Project threshold**; equivalent to a 1.30% minimum stop at 26 bp | Whether 0.20 is the right economic cutoff | Relaxing it admits trades whose costs are a larger share of risk; the B and C counts would still fail |
| **0.15R effect of interest** | Assumed minimum edge used in the design-margin diagnostic | **Design assumption**, not measured | The project's actual minimum economic effect | With 0.15R, no candidate is testable; with a larger declared effect, a different sufficiency rule follows |
| **Non-overlap horizons (72h, 24h, 120h)** | Minimum spacing between accepted entries | **Project choices**, not optimal holding periods | Expected holding distributions (no outcome) | Shorter horizons raise counts; they also raise overlap and dependence. A's 120h choice costs 80 of 151 signals |
| **Concentration screen (50% / 2.00)** | Screening rule, not a test | **Project choice** | Whether 2.00 is the right dependence allowance | It already triggers for D and not for B on the primary view; it does not drive any verdict |
| **C duration ≥ 6 bars** | Minimum compression length | **Project choice** | Whether 4–5 bars is still a "compression state" | It is the binding cap: 63 of 461 episodes. Relaxing it would change the hypothesis |
| **B retest and permission parameters** | 1–6 bars, 0.25 ATR tolerance, 0.50 ATR penetration, percentile 20–95 | **Project choices**, frozen before counting | Marginal yield of each condition | Not decomposable from this record; no ablation exists |
| **D threshold and budget parameters** | 0.5 × ATR1h threshold, percentile 25–80 | **Project choices**, frozen before counting | Same | Same |
| **Feasible-share thresholds 0.25 / 0.30** | Proposed economic screens | **Proposed, never adopted** | Whether they would have changed any verdict | B's 0.906 and A's 0.774 pass; D's 0.153 fails; B and D already fail on count, so the verdicts would not change |

**Warning:** none of the items in Section 8.3 is a market fact. Presenting 150 as a universal
statistical standard, or 349 as a power requirement, would misstate the record. Stage 2K does not do
so, and no number in this analysis should be quoted that way.

---

## 9. Attribution and what would separate the explanations

### 9.1 Attribution matrix

| candidate | F1 frequency | F2 cost/stop | F3 regime/timeframe | F4 concentration | F5 design | F6 evidence |
|---|---|---|---|---|---|---|
| **A** | **Strong** — 71 vs 150 | Moderate — 44 of 195 fail; feasible share 0.774 | **Strong** — regime removes 56%; overlap removes 53% | **Strong** — `n_eff` 12.69, 24 clusters | Moderate — 120h overlap; 0.15R mismatch | Shared project limitation |
| **B** | **Strong** — 24 vs 150 | **Weak** — 3 of 32 fail; share 0.906 | **Strong** — regime removes 74.5%; structure removes 70.9% of the rest | Mild — primary 1.69, quarter view 4.93 | Moderate — nine-condition conjunction | Shared project limitation |
| **C** | **Strong and structural** — 63-episode ceiling | Moderate — 5 of 17 fail; best case 17 | Not applicable — no regime condition | Moot — sparse, not clustered | **Strong** — six-bar floor is the cap | Shared project limitation |
| **D** | **Strong** — 34 vs 150 | **Strong** — 250 of 295 fail; share 0.153 | Moderate — budget removes 64% | **Strong** — 3.93, signals only in 2021–22 | Moderate — 1h-ATR stop near the gate | Shared project limitation |

### 9.2 What the matrix supports

**Interpretation:** F1 is the verdict for every candidate, but the causal routes differ. There is no
single dominant failure mode across the family. Two candidates are regime-limited, one is
state-limited, one is cost-geometry-limited. A project response that assumes a single cause — for
example "lower the cost proxy" or "add a better filter" — would address at most one candidate.

**Interpretation:** F6 applies to all four. The record's strongest common limitation is not any
individual rule; it is that no outcome was ever observed, so the project knows where opportunities
were lost but not whether the survivors carry any edge.

### 9.3 What would separate structural from project-specific

| question | evidence required | authorized in Stage 2K? |
|---|---|---|
| Which condition is responsible for the low yield? | Pre-registered ablation: yield of the frozen rule with one condition removed at a time, no threshold tuning, no outcome observed | **No** — new counting |
| Is the cost proxy too high? | Verified venue fee, spread and slippage measurement, then a pre-registered cost-scenario recomputation including the non-overlap count | **No** — new analysis and external data |
| Would more data help? | A longer interval, which necessarily consumes validation/OOS data, plus a new freeze | **No** — prohibited and governance-sensitive |
| Is the effect-size target achievable? | An owner-declared minimum economic effect and a dependence-aware sufficiency rule, frozen before any count | **No** — owner decision |
| Does the family work in another instrument or period? | Out-of-sample replication under a new pre-registration | **No** — later stage |
| Is the v2 freeze trustworthy? | An arms-length third-party audit, not a self-audit | **No** — governance |

**Conclusion of this analysis:** the record is sufficient to establish that these four frozen designs
produced too few opportunities, and sufficient to show that the cause differs by candidate. It is
**not** sufficient to establish that the market lacks the opportunities, that the cost proxy is
wrong, or that the family has no edge. The distinction cannot be resolved without new, separately
authorized work.
