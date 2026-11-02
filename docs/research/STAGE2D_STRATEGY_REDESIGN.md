# Stage 2D — Strategy Research Redesign

**Status:** Research and design only. No market-data processing, signal counting, backtesting,
P&L, expectancy, portfolio simulation, bootstrap, Monte Carlo, parameter optimisation, strategy
implementation, or validation/OOS access was performed for this document.

**Scope:** Reconsider the BTCUSDT spot, long-only research direction after three failed research
programmes: Setup 1 (low-side liquidity sweep and rejection), Strategy 2 Candidate C (volatility
compression breakout), and Strategy 2 Candidate A / Stage 2C (multi-timeframe trend pullback
continuation).

**Development interval for any future research:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.
The full dataset extends to 2026-08-31, but the later period is **not** development data and is not
read, summarised, or used here.

**Evidence tags:** **[F]** repository fact; **[L]** literature-backed mechanism; **[E]**
engineering judgment; **[H]** unverified hypothesis. A tag describes the *kind* of support, not its
strength. A literature citation is not evidence that a particular implementation is profitable.

---

## 0. Executive summary

The Stage 2C failure was not only a strategy failure. It exposed three methodological problems that
would repeat in any new census unless they are fixed first:

1. **The 150-event floor was introduced at the Stage 2C freeze, not derived from an earlier
   document.** It was committed before the Stage 2C counting script and before the Stage 2C results,
   so it was not invented after seeing the 71 count. But it has no antecedent in Stage 2A or Stage 2B,
   it is lower than the earlier `>= 200` language, and it is far below the 349 independent-observation
   reference. Calling it "pre-registered" overstates what the repository can show. It is a frozen
   protocol choice, not an independently pre-registered standard.
2. **The 0.20R cost gate and the 0.15R effect target are not integrated.** A strategy with a 0.15R
   gross edge and a 0.20R cost cannot be profitable. The gate is a feasibility bound, not an economic
   sufficiency bound. Stage 2C's median feasible `cost_R` of 0.0898 already consumes about 60% of a
   0.15R edge. Future censuses must report the cost-adjusted edge, not only the pass/fail gate.
3. **The Kish number was used as a dependence diagnostic but described with inverted bound
   language.** The arithmetic is correct, and the Stage 2C narrative mostly caveats it correctly, but
   the frozen specification says "upper bound" where it should say "lower bound" under the stated
   assumption. Kish is a cluster-size concentration measure, not an estimate of statistical
   dependence.

The redesign also adds a constraint the earlier stages did not state explicitly: **calendar
arithmetic**. The development interval is 1,277 days. At most `floor(1277 / H)` non-overlapping
episodes can exist for a strategy whose non-overlap horizon is `H` days, even with perfect signal
density and independence. The 150 floor requires `H <= 8.51` days; the 349 reference requires
`H <= 3.66` days. Any multi-day or multi-week strategy with a 10–30 day holding period is therefore
structurally incapable of reaching 150 non-overlapping episodes in this interval, before any
consideration of signal sparsity or clustering.

That constraint drives the recommendation in the companion document: the two candidates worth a
future feasibility census are **B (volatility expansion plus retest continuation)** and **D
(intraday continuation with a higher-timeframe volatility budget)**. Candidate A (multi-day
time-series momentum) has the strongest and least overfit economic mechanism, but under the existing
150 floor it cannot produce enough non-overlapping episodes. Candidate C (longer-horizon
regime-conditioned mean reversion) is the most exposed to falling-knife risk and is even less
testable.

---

## 1. Audit of the previous decision criteria

### 1.1 Method

The audit uses repository history only: first appearance of each number or rule in a committed file,
the commit date, whether an earlier document contains the same rule, and whether the Stage 2C
counting script or results existed at that commit. It does **not** re-analyse trades, recompute
counts, or inspect market data.

The relevant commits are:

| commit | date (author time, +03:30) | content |
|---|---|---|
| `e5f495f` | 2026-11-01 12:20:47 | Strategy 2 candidate comparison and recommendation; first `0.15R` and `>= 200` language |
| `049975f` | 2026-11-01 12:56:37 | Stage 2A feasibility census; first `349` derivation; corrects the earlier 100–250/`>= 200` claim |
| `de3adb7` | 2026-11-02 10:18:40 | Stage 2B discovery and recommendation; carries `349` forward |
| `201831b` | 2026-11-02 10:28:56 | Stage 2C signal specification and config freeze; first `150`, `120h`, and `Kish` |
| `cd161e4` | 2026-11-02 10:44:22 | Stage 2C census script and results; first `71` non-overlapping count |
| `fb7f375` | later | Stage 2C documentation alignment; no threshold change |

`stage2c_census/freeze.json` records `frozen_at_utc = 2026-11-02T07:01:05Z` (10:31:05 +03:30) and
states that the hashes were computed before the first Stage 2C counting run. The counting script was
first committed at 10:44:22, thirteen minutes later. The freeze record therefore does establish that
the Stage 2C specification and config did not change between the hash computation and the first
counting run. It does **not** establish that no exploratory data analysis occurred before the freeze.

### 1.2 Provenance table

| criterion | first repository appearance | antecedent | timing relative to Stage 2C results | classification | audit finding |
|---|---|---|---|---|---|
| **150 non-overlapping events** | `201831b`, Stage 2C spec §12, 2026-11-02 10:28 | **None.** Stage 2A used `>= 200`; Stage 2B referred to 349 and said not to require `> 200` as a guarantee | **Before** the Stage 2C script and results (`cd161e4`, 10:44) | Introduced at the Stage 2C freeze; pre-specified before counting, **not derived**, not independently pre-registered | A new, lower floor. It relaxes the earlier `>= 200` language without an explicit methodological derivation. The word "pre-registered" is inaccurate if it implies independent registration. |
| **349 independent observations** | `049975f`, Stage 2A §8.3, 2026-11-01 12:56 | Arithmetic from `0.15R`, `sigma = 1R`, two-sided `alpha = 0.05`, 80% power; corrects the earlier 100–250/`>= 200` claim | **Before** Stage 2C | Derived from an earlier document | Arithmetic is correct. Assumptions are explicit. It is a planning reference under independence, not a result and not a guarantee. |
| **0.15R minimum effect** | `e5f495f`, Strategy 2 comparison, 2026-11-01 12:20 | Design target; no derivation from cost, capital, or opportunity cost | **Before** Stage 2C | Explicitly specified earlier; design choice | Predates all Stage 2 censuses. Not estimated from data. The `1R` outcome standard deviation is also an assumption. |
| **120h non-overlap horizon** | `201831b`, Stage 2C spec §6/§7, 2026-11-02 10:28 | Stage 2B said "intraday–few days"; no 120h figure | **Before** the Stage 2C script and results | Introduced at the Stage 2C freeze; design choice | Not derived. It is the maximum intended holding horizon, used only for non-overlap. It directly determines the decision count. The 24/72/168h sensitivities were run after the results and are diagnostics, not pre-registered tests. |
| **Kish effective sample size** | `201831b`, Stage 2C spec §8.3; implementation in `census.py` | None earlier | **Before** the Stage 2C script and results | Introduced at the Stage 2C freeze | Formula is correct for the perfect-within-cluster-dependence case. Interpretation is partly inverted in the specification. It is a concentration diagnostic, not an estimate of statistical dependence. |

### 1.3 The 150-event floor

**Literal timing.** The 150-event floor *was* specified before the Stage 2C results were observed. It
appears in the Stage 2C specification and config committed at `201831b`, and the counting script was
first committed at `cd161e4`, after the freeze. The repository therefore does not support the claim
that 150 was introduced after seeing the 71 count.

**But the provenance is weaker than "pre-registered" suggests.**

- The floor has **no antecedent** in Stage 2A or Stage 2B. Stage 2A used `>= 200` as the comparison
  gate and separately derived `349` for a `0.15R` effect. Stage 2B referred to `349` and explicitly
  said "Do not require >200 as guarantee; require credible argument if borderline." Neither document
  defines 150.
- The floor is **lower** than the earlier `>= 200` language. The Stage 2A document went further and
  said: "Passing 200 would not by itself have established that the experiment could answer the
  question." Stage 2C then introduced a floor of 150 without explaining why 150 is adequate when 200
  was already described as insufficient for `0.15R`.
- The floor's stated rationale is detectable effect: at `n = 150`, the smallest detectable effect is
  `2.801585 / sqrt(150) = 0.229R` at 80% power. That is **larger** than the `0.15R` target. So the
  150–349 band is explicitly a "pass with limitations" band that cannot answer the programme's own
  `0.15R` question. That may be a deliberate compromise, but it is a compromise, not a derivation
  from the `0.15R` requirement.
- The floor sits almost exactly at the Stage 2C raw feasible count. Stage 2C produced **151 unique
  cost-feasible signals** and **71 non-overlapping** signals. Because 151 unique signals is only one
  above 150, *any* non-overlap separation pushes the decision count below the floor. The floor was
  therefore not calibrated to the clustering the strategy actually exhibited. This is an observation,
  not a retrospective justification for changing the floor.
- The freeze record proves file immutability before counting. It does not prove that the threshold was
  chosen without prior data exploration. The repository cannot establish that stronger claim.

**Classification:** introduced at the Stage 2C freeze; pre-specified before counting; not derived from
an earlier document; not independently pre-registered. Future documents should call it "the frozen
Stage 2C floor," not "the pre-registered floor." If the programme wants a genuinely pre-registered
threshold for Stage 2D, it must register it before the next census, state its derivation, and not
change it after seeing counts.

### 1.4 The 349-independent-observation estimate

The arithmetic is correct:

```
(1.959964 + 0.841621)^2 / 0.15^2 = 7.848878 / 0.0225 = 348.839... ~ 349
```

It assumes a two-sided 5% test, 80% power, a true effect of `0.15R`, an outcome standard deviation of
`1R`, and independent observations. The `1R` standard deviation is a provisional design assumption,
not a measured value. Fat tails and skew in trade outcomes would generally require a **larger** sample
than the normal approximation implies, so 349 is optimistic even under independence.

The estimate first appears in Stage 2A, where it correctly corrects the earlier Strategy 2 comparison's
100–250 range. It is carried into Stage 2B and Stage 2C. It predates the Stage 2C census and is not a
result-driven number.

**Implication the earlier documents did not draw.** The development interval is 1,277 days. Even with
perfect signal density and independence, 349 non-overlapping episodes require a non-overlap horizon of
at most `1277 / 349 = 3.66` days. A strategy that intends to hold for 10–30 days cannot reach 349 in
this interval. It cannot even reach 150 if its horizon exceeds 8.51 days. This is calendar arithmetic,
not a market-data result, and it is the single most important constraint on candidate selection.

### 1.5 The 0.15R minimum effect

`0.15R` first appears in the Strategy 2 comparison (`e5f495f`) on 2026-11-01, before Stage 2A, 2B, and
2C. It is a **design target**, not an estimate. The document does not derive it from the cost model,
the capital base, or the opportunity cost of holding a position; it is asserted as the smallest edge
the programme cares about. That is legitimate as a design choice, but it should be labelled as one.

Two consequences follow:

1. **The earlier sample-size range was wrong and was corrected.** The Strategy 2 comparison suggested
   that ~100–250 events might be enough and set a `>= 200` gate. Stage 2A showed that a `0.15R` effect
   at 80% power needs ~349 independent observations, and that a `>= 200` gate is not proof of power.
   That correction happened *before* Stage 2C and is a methodological improvement, not a post-hoc
   adjustment.
2. **The 0.20R cost gate is too loose for a 0.15R edge.** `cost_R` is the round-trip cost expressed in
   units of `R`. If the gross edge is `0.15R` and `cost_R = 0.20R`, costs exceed the entire edge. Even
   the Stage 2C median feasible `cost_R` of `0.0898` consumes about 60% of a `0.15R` edge, leaving
   roughly `0.06R` before any other friction. The `0.20R` gate is a **feasibility** bound: it rejects
   designs whose costs are catastrophically large. It is not an **economic sufficiency** bound. Future
   censuses should report `0.15 - median cost_R` (or the relevant target minus cost) and require it to
   be positive, preferably with a margin. This does not weaken the gate; it adds a second, stricter
   economic screen.

### 1.6 The 120h non-overlap horizon

The 120h (5-day) horizon first appears in the Stage 2C freeze. It has no antecedent: Stage 2B said
"intraday–few days" but did not define a number. The specification calls it the "maximum intended
holding horizon" and uses it only for the non-overlap rule; it is not a claim about the optimal exit,
and the census did not simulate exits.

Consequences:

- The 120h horizon directly sets the decision count. It is a design choice, not an empirical holding
  period.
- The 24h/72h/168h cooldown sensitivities were run after the results and are diagnostic only. They
  produced 127, 87, and 59 non-overlapping signals respectively, all below 150. The failure is
  therefore robust to the horizon choice *within that sensitivity set*, but the sensitivities were not
  pre-registered and cannot be used to claim a pre-specified robustness result.
- The capital-geometry "at most 6 concurrent positions" estimate also assumes 120h holding. If actual
  holds are shorter, concurrency and non-overlap change. A future census should report a holding-period
  sensitivity and, in a later outcome stage, measure actual time-to-stop/target.

### 1.7 The Kish effective sample size

**What was computed.** The implementation is:

```
n_eff = (sum_k n_k)^2 / sum_k n_k^2
```

over the 24 signal-producing 4h up-regime episodes, where `n_k` is the number of feasible primary
signals in episode `k`. With 151 feasible signals, the result is `n_eff = 12.69`, the cluster count is
24, and the design effect against the 151 raw signals is `151 / 12.69 = 11.9`.

**Is the formula correct?** Yes, for the specific model it assumes: unequal cluster sizes, perfect
correlation among observations within a cluster, and independence across clusters. It is the Kish
design-effect formula for a one-way cluster sample. The implementation matches the formula.

**Is it an estimate of statistical dependence?** No. It is a **concentration diagnostic**. It assumes
`rho = 1` within a regime episode; it does not estimate `rho` from outcomes, and the census cannot do so
because no outcome is computed. The number answers: "if every signal in a regime episode were the same
observation, how many independent observations would this sample be worth?" It does not answer: "how
correlated are these signals in reality?"

**The bound language is inverted in the frozen specification.** The specification says:

> It is an upper bound on the effective sample if regimes are the only dependence structure, and a
> lower bound if they are not.

The correct statement is the reverse:

- If regimes are the only dependence structure and within-regime correlation is **less than perfect**
  (`rho < 1`), the true effective sample is **larger** than Kish. Kish is then a conservative **lower
  bound**.
- If there is **additional cross-regime dependence** (for example, a macro shock that spans several
  regime episodes), the true effective sample is **smaller** than Kish. Kish is then an optimistic
  **upper bound**.
- Because neither `rho` nor cross-regime dependence is estimated, Kish is neither a universal lower nor
  a universal upper bound. It is a **scenario**, not a bound.

The Stage 2C narrative says "deliberately conservative lower bound" without the cross-regime caveat.
That is acceptable as a shorthand if the caveat is stated, but it is not a general bound. The census's
own limitation section correctly says the effective sample is not identified and the Kish/cluster
counts are design diagnostics. That is the right interpretation.

**Two further cautions.**

- The Kish calculation uses only the 24 signal-producing episodes, not the 67 up-regime episodes. That
  is correct for the signal-weighted mean formula, but it is not an estimate of the strategy's
  independent-episode frequency. The 24/67 = 36% signal-producing share is itself a frequency
  diagnostic. The "cluster count" of 24 is the more interpretable independent-episode proxy, and even
  that is optimistic if episodes are correlated.
- The detectable effect at `n_eff = 12.69` (`0.785R`) is a **what-if** calculation, not a power result.
  It shows that under an extreme dependence assumption the sample is far from 349; it should not be
  presented as "the" effective sample size.

**Recommendation for future censuses.** Report at least three clustering views: 4h regime episodes,
calendar months/quarters, and volatility regimes or event windows. Report the cluster-size
distribution, the largest-cluster share, and a sensitivity of `n_eff` to assumed `rho` values (for
example 0.25, 0.50, 0.75, 1.00). Do not use one Kish number as the decision count. The decision count
remains the non-overlap count; the clustering views are diagnostics.

### 1.8 What the audit changes for Stage 2D

1. **Do not call the 150 floor "pre-registered."** Call it the frozen Stage 2C floor. If Stage 2D uses
   a floor, state its derivation and register it before counting.
2. **Keep the 0.20R cost gate, but add a cost-adjusted edge screen.** Report `target_effect - median
   cost_R` and reject designs where it is not positive with a margin. A design that passes 0.20R but
   consumes most of a 0.15R edge is not economically viable.
3. **Use calendar arithmetic as a first-pass feasibility filter.** A candidate whose intended holding
   period exceeds 8.5 days cannot reach 150 non-overlapping episodes in 3.5 years. It may still be
   economically interesting, but it cannot satisfy the existing floor; the programme must either
   accept a larger detectable effect or extend the development interval (which is not authorized here).
4. **Treat 349 as a planning reference, not a target that every candidate must hit.** It is
   unattainable for multi-day strategies in this interval. The relevant question is what effect the
   candidate can detect with the episodes it can produce, and whether that effect is economically
   meaningful.
5. **Report Kish with the correct bound language and multiple clustering views.** Do not use it as a
   formal dependence estimate.
6. **Do not modify the frozen Stage 2A/2B/2C artifacts.** The corrections in this document are
   forward-looking; the frozen documents remain the historical record.

---

## 2. Evaluation framework

### 2.1 The twelve questions

Every candidate below is assessed against the same twelve questions. The questions separate the
*mechanism* (why the effect should exist) from the *economics* (whether it can be traded at this
venue, size, and cost) from the *epistemics* (whether the programme could ever falsify it).

| # | question | what a weak answer looks like |
|---|---|---|
| Q1 | What precise market state does the rule identify, using only information available at the decision bar? | A narrative state ("trend", "fear") with no objective, reproducible definition |
| Q2 | Who is the counterparty, and why do they persistently accept an adverse price? | "The market is inefficient" with no identified trader, constraint, or flow |
| Q3 | What economic or behavioural mechanism sustains the effect, and why is it not arbitraged away? | A story that predicts both continuation and reversal |
| Q4 | Why should the effect exist in BTC spot specifically, rather than in any liquid asset? | A generic momentum/reversal claim with no crypto-specific channel |
| Q5 | Why long-only spot, and what does that exclude? | Ignoring that long-only removes the short leg that carries much of the documented effect |
| Q6 | Where is the stop, and why is it outside normal noise rather than inside it? | A stop so tight that ordinary volatility removes the position before the hypothesis is tested |
| Q7 | What is the exit, and why is that holding horizon the right one? | An arbitrary fixed bar count with no mechanism for why the edge decays there |
| Q8 | How frequent are qualifying episodes, qualitatively, and what drives the estimate? | A point frequency estimate with no data behind it |
| Q9 | What is the typical stop distance, `cost_R`, and margin to the `0.20R` gate? | Reporting only the gate pass rate, not the cost-adjusted edge |
| Q10 | What capital is required at $10,000 equity and 1% risk, and how does concurrency bind? | Ignoring that a tight stop implies a large notional and a cash constraint |
| Q11 | What execution frictions can turn a paper edge into a loss? | Assuming the 26 bp proxy covers spread widening, gaps, and unfilled limits |
| Q12 | What would falsify the hypothesis, and what is the strongest argument that it will fail? | A hypothesis that no conceivable result could reject |

### 2.2 Evidence discipline

Frequency answers use only the four permitted qualitative labels: **very low**, **low**, **moderate**,
**high**. Every frequency statement is tagged **[H]** and marked unverified. No market data was read
to produce them. They are priors derived from the mechanism and from the published literature's
asset-class coverage, not from this repository's BTC series.

A literature citation is tagged **[L]** and means "the mechanism has support in published work." It
does not mean the cited paper tested this rule, this venue, this sample, or this cost model. Several
of the cited papers use cross-sectional portfolios, multiple assets, short legs, or futures — none of
which is available here. Those differences are stated explicitly where they matter.

### 2.3 The calendar filter

Let `H` be the non-overlap horizon in days and `D = 1277` the development-interval length. No strategy
can produce more than `floor(D / H)` non-overlapping episodes, regardless of signal density:

| non-overlap horizon `H` | maximum non-overlapping episodes | reaches 150? | reaches 349? |
|---:|---:|:---:|:---:|
| 6 h (`0.25 d`) | 5,108 | yes | yes |
| 24 h (`1 d`) | 1,277 | yes | yes |
| 72 h (`3 d`) | 425 | yes | yes |
| 5 d | 255 | yes | no |
| 8.51 d | 150 | exactly | no |
| 10 d | 127 | no | no |
| 20 d | 63 | no | no |
| 30 d | 42 | no | no |

This is arithmetic, not a market result. It is applied as a first-pass filter before any candidate is
judged on signal quality. A multi-day strategy is not "unpromising" because of this; it is
*structurally unable to satisfy the frozen Stage 2C floor* in the available interval. The programme
must either accept a larger detectable effect for that candidate or extend the interval, and extending
the interval is not authorized here.

---

## 3. Candidate A — multi-day time-series momentum

### 3.1 What it is, and how it differs from Stage 2C

**Canonical form for a future census.** On the daily close, compute
`TSMOM(L)_t = close_t / close_{t-L} - 1` for `L in {30, 60, 90}` calendar days. Hold a long spot
position when `TSMOM(60) > 0` and `close_t > SMA(200)_t`; be flat otherwise. An *episode* begins on the
flat-to-long transition and ends when the condition fails. The census non-overlap horizon is 20 days
(sensitivity 10 and 30 days). A disaster stop at `3 x ATR(20, daily)` below entry is used only to
compute `cost_R`; the primary exit is the signal reversal.

**Is this a renamed Stage 2C?** No, but the overlap must be disclosed. Stage 2C was a *discrete
pullback event*: a 4h up-regime, a pullback into a zone, and a resumption trigger, held for at most
120h. Candidate A is a *continuous long/flat state rule* on daily data with a 20–30 day horizon. The
signal construction, timeframe, entry logic, and holding period differ. Both, however, belong to the
trend family, and the economic objection that defeats one may defeat the other. The redesign does not
present A as a fresh family; it presents it as the cleanest expression of the trend mechanism, tested
against a frequency constraint that Stage 2C did not confront in advance.

### 3.2 The twelve questions

| # | answer | tag |
|---|---|---|
| Q1 | Market state: positive trailing return over 60 days with price above its 200-day mean. Both are computable at the daily close with no look-ahead. | [F] definition, [E] choice of 60/200 |
| Q2 | Counterparty: late-informed or constrained participants who underreact to persistent flows and sell to rebalancers/hedgers during sustained moves. In crypto, retail attention and exchange inflows are plausible slow-moving channels. | [L] underreaction, [H] crypto-specific channel |
| Q3 | Mechanism: gradual information diffusion and herding (Barberis–Shleifer–Vishny; Hong–Stein) plus a risk premium for bearing crash risk (Daniel–Moskowitz). Time-series momentum is documented across 58 liquid instruments (Moskowitz–Ooi–Pedersen) and over a century of trend-following data (Hurst–Ooi–Pedersen). | [L] |
| Q4 | BTC-specific: crypto returns show a strong time-series momentum effect (Liu–Tsyvinski), and momentum is reported in cryptocurrency samples (Grobys–Sapkota; Tzouvanas et al.). The effect is not obviously stronger in BTC than in other crypto assets; single-asset BTC is the *least* diversified implementation. | [L] effect, [E] single-asset limitation |
| Q5 | Long-only spot excludes the short leg. Most TSMOM evidence uses long/short portfolios across many instruments. Long-only BTC TSMOM is closer to a trend-filtered beta exposure than to the diversified strategy in the literature. | [E], [L] for the long/short evidence |
| Q6 | Stop: `3 x ATR(20, daily)` below entry, typically 10–15% at BTC daily volatility. This is a disaster stop, not the thesis invalidation. It is deliberately outside normal noise, which is appropriate for a multi-day trend but means adverse exposure is large in dollar terms. | [E] |
| Q7 | Exit: `TSMOM(60) <= 0` or `close < SMA(200)`. The horizon is the time the slow signal takes to turn, not a fixed bar count. A 20-day non-overlap is a census convention, not the expected hold. | [E] |
| Q8 | Frequency: **low** [H]. A long/flat daily trend rule on one asset produces few regime transitions; bull and bear phases last months. The 20-day calendar ceiling is 63 episodes, and the realistic count is below that. | [H] |
| Q9 | Stop distance ~10–15%, so `cost_R = 0.0026 / 0.10` to `0.0026 / 0.15` = `0.017–0.026`. It clears the `0.20R` gate by a wide margin. Cost is not the binding constraint; calendar frequency is. | [E] arithmetic |
| Q10 | At $10,000 equity and 1% risk, a 10% stop implies `0.01 x 10,000 / 0.10 = $1,000` notional, or 10% of equity. A 15% stop implies $667, or 6.7%. Concurrency is effectively one, and most capital sits idle. Capital utilisation is low, but capital at risk is controlled. | [E] arithmetic |
| Q11 | Daily-close market orders; 24/7 trading removes the equity-market overnight gap but not exchange outages, weekend liquidity thinning, or stop slippage. A 26 bp round-trip proxy is plausible for Binance BTCUSDT at $10k but unverified for Nobitex. A disaster stop can be gapped through in a fast move. | [E], [H] venue |
| Q12 | Falsified if net long-only TSMOM does not beat buy-and-hold on a risk-adjusted basis, or if its return is explained by time-varying beta with no timing information. Strongest objection: with one asset, long-only, and no short leg, the strategy is beta timing on a single bull–bear path, and the cross-sectional diversification that makes TSMOM robust is unavailable. | [E] |

### 3.3 Economics and frequency

**Mechanism strength.** This is the strongest and least overfit mechanism among the four. It has
multi-asset, multi-decade support, a behavioural channel, and a risk-premium channel. It does not
depend on a novel microstructure story or on a threshold fitted to BTC.

**Why it still fails the existing floor.** The mechanism operates over weeks to months. At a 20-day
non-overlap the calendar ceiling is 63; at 30 days it is 42. The 150 floor requires `H <= 8.51` days,
which is shorter than the horizon at which the mechanism is supposed to work. Tightening the horizon
to satisfy the floor would test a different hypothesis (short-horizon continuation), not multi-day
TSMOM. The candidate is therefore *infeasible under the frozen floor*, not merely low-frequency.

**Strongest economic argument against it.** Single-asset, long-only TSMOM is not the strategy the
literature validates. The literature's robustness comes from diversification across dozens of
instruments and from a short leg that profits in sustained downtrends. Removing both leaves a
trend-filtered long BTC exposure whose apparent edge may be the 2021 and 2023 up-legs. One 3.5-year
path containing roughly one bull and one bear phase cannot distinguish a genuine timing edge from
regime luck.

**Verdict for this stage.** Do not recommend for a feasibility census under the existing 150 floor.
Retain as the first alternative if the floor is revised or the development interval is extended.

---

## 4. Candidate B — volatility expansion with directional continuation

### 4.1 What it is, and why it is not Strategy 2 C

**Canonical form for a future census.** On 1h BTCUSDT:

1. **Expansion event.** True range `>= 2.0 x ATR(14, 1h)`, body/range `>= 0.55`, close in the top
   25% of the bar's range, and close > open.
2. **Higher-timeframe permission.** The 4h regime is not down: 4h close > 4h SMA(50), or the 10-bar
   4h return > 0. The 4h ATR(14) must be above its 20th percentile of the trailing 90 days (avoid
   dead markets) and below its 95th percentile (avoid crisis jumps).
3. **Retest.** Within 1–6 bars, price returns to within `0.25 x ATR(14)` of the expansion bar's close
   and the bar closes back above that level. Enter long at the next bar's open.
4. **Stop.** Below the expansion bar's low, or `1.0 x ATR(14)` below entry, whichever is farther. If
   the resulting stop is below 1.30% of entry, skip the signal — this is the explicit cost floor, not
   a fitted parameter.
5. **Exit for census purposes.** 2R target, stop, or 72h time exit. The census only needs entry, stop,
   and the 72h non-overlap horizon.

**Why this is materially different from Strategy 2 C.** Strategy 2 C required a *prolonged
compression* (a coil) and traded the breakout *out of* low volatility. Candidate B requires a
*volatility expansion event* and trades *continuation after* the expansion, with a retest that C did
not require. The state is the opposite: C is low-vol → breakout; B is an already-realized expansion →
retest → continuation. The failure modes differ. C failed on episode scarcity because long
compressions are rare. B's scarcity comes from the retest and the cost floor, not from the expansion
itself. A census of B would not re-count C's events.

### 4.2 The twelve questions

| # | answer | tag |
|---|---|---|
| Q1 | Market state: a 1h bar with abnormal range and a strong directional close, in a non-down 4h regime with a non-extreme volatility budget, followed by a successful retest of the expansion level. All inputs are computed from closed bars. | [F] definition |
| Q2 | Counterparty: traders who fade the first expansion (mean-reversion sellers, profit-takers, stop-hunt liquidity), and late entrants who provide the continuation once the retest holds. The expansion is where stop cascades and forced flows are visible. | [E], [L] microstructure |
| Q3 | Mechanism: volatility clustering means high-volatility states persist (Engle; Bollerslev), and large directional moves can reflect order-flow imbalance and slow information diffusion rather than pure overreaction. The retest separates continuation from a single-bar spike. The opposite mechanism — jump reversal — is equally plausible for BTC, which is why the retest is the test. | [L] clustering, [H] continuation |
| Q4 | BTC-specific: crypto has a large jump component (Scaillet–Treccani–Trevisan) and pronounced volatility clustering (Baur–Dimpfl). A large 1h range is often a jump; the hypothesis is that a subset of jumps is information-driven and continues. This is plausible but unproven for BTC spot. | [L] jumps/vol, [H] continuation |
| Q5 | Long-only spot means only upside expansions are traded. Downside expansions — the more common crash signature — are excluded. This removes the short leg that would profit from the asymmetric volatility result. | [E], [L] asymmetry |
| Q6 | Stop below the expansion low or 1.0×ATR(14), whichever is farther, with a hard 1.30% floor. The floor is required by `cost_R <= 0.20`, not by market structure. A structural stop tighter than 1.30% is skipped rather than widened arbitrarily. | [E] |
| Q7 | Exit at 2R, stop, or 72h. The 72h horizon matches the typical decay of a 1h expansion impulse and keeps the calendar ceiling at 425. A 2R target is a census convention; the outcome stage would need to test target sensitivity. | [E] |
| Q8 | Frequency: **moderate** [H]. 1h expansion bars are common, but the conjunction of 4h permission, a 1–6 bar retest, and a stop >= 1.30% removes most of them. A realistic range is 150–400 raw candidates and 60–150 non-overlapping at 72h. The upper end is not guaranteed. | [H] |
| Q9 | Stop 1.5–3.0% typical, so `cost_R = 0.087–0.173`. Median may be ~0.12. It passes the gate but consumes 60–80% of a 0.15R edge. The cost-adjusted screen (`0.15 - median cost_R`) is only ~0.03R at the median; a median above 0.12R should be treated as a fail for economic purposes even if the gate passes. | [E] arithmetic |
| Q10 | At 1% risk, a 2% stop implies $5,000 notional (50% of $10,000); a 1.5% stop implies $6,667 (67%). Two concurrent positions can exhaust cash. The existing backtest engine allows only one simultaneous position, so a multi-position census or outcome stage needs new accounting. | [E], [F] engine limitation |
| Q11 | Expansion bars have wide spreads and elevated slippage; a retest may never arrive (adverse selection: the best continuations may not retest); a stop below the expansion low can be gapped through. The 26 bp proxy likely understates cost during the exact state being traded. | [E], [H] |
| Q12 | Falsified if expansion events are predominantly jumps that reverse, if the retest filter selects the failures, or if median `cost_R` exceeds ~0.12R. Strongest objection: BTC's jump component is large and expansions are often exhaustion, so "continuation" may be the minority case; the retest may be a liquidity vacuum rather than confirmation. | [E], [L] jumps |

### 4.3 Economics and frequency

**Mechanism strength.** Moderate. Volatility clustering is one of the most robust facts in financial
time series, but clustering of *volatility* is not the same as *directional continuation*. The
candidate needs the second link, and that link is the unverified part. The retest rule is a serious
attempt to avoid buying a one-bar spike, but it is also the filter most likely to introduce
selection bias: if only the expansions that retest are counted, the census conditions on a
post-event outcome.

**Frequency and the floor.** At 72h non-overlap the ceiling is 425. If the conjunction produces
60–150 non-overlapping episodes, B is at or just below the frozen floor. That is a genuine risk, not
a formality. A future census should report the count at 24h, 72h, and 120h non-overlap so the
decision does not hinge on one horizon.

**Capital and cost.** The 1.30% stop floor is the binding design constraint. At 1.5–2.0% stops the
notional is 50–67% of a $10,000 account per position, so concurrency is 1–2. The cost-adjusted edge is
thin. B is economically viable only if the median stop is at the wide end of the range and the
continuation effect is large enough to survive 0.10–0.17R of cost.

**Verdict for this stage.** Recommend for a future feasibility census, with the explicit warning that
it may fail on frequency or cost-adjusted edge rather than on mechanism.

---

## 5. Candidate C — longer-horizon regime-conditioned mean reversion

### 5.1 What it is, and the falling-knife constraint

**Canonical form for a future census.** On the daily close:

1. **Regime permission.** `close > SMA(200, daily)` and the 200-day slope is non-negative, or price is
   above the 200-day mean and drawdown from the 90-day high is at most 25%. Trailing 30-day realized
   volatility must be below its 80th percentile over the prior year. The regime filter is the
   falling-knife guard: no longs in a confirmed downtrend or in a volatility crisis.
2. **Dislocation signal.** Daily RSI(14) < 30, or close below the lower Bollinger band (20, 2), or a
   five-day return below `-1.5 x ATR(14, daily)`.
3. **Stabilization confirmation.** The next daily bar closes above the prior bar's low and back above
   the lower band, or a higher low forms over two to three bars. Enter long at the next open after
   confirmation. This is the second falling-knife guard: the rule does not buy a close at the low.
4. **Stop.** Below the confirmed swing low by `1.0 x ATR(14, daily)`, with a 2.5% floor. Typical stop
   5–10%.
5. **Exit.** Reversion to the 20-day mean, 2R, or a 20-day time exit.
6. **Non-overlap.** 20 days canonical; 10 and 30 days as sensitivity.

The design deliberately gives up the first part of the bounce in exchange for evidence that the
decline has stopped. That trade-off is the hypothesis: the cost of confirmation is smaller than the
cost of catching a knife.

### 5.2 The twelve questions

| # | answer | tag |
|---|---|---|
| Q1 | Market state: an established non-bear regime, a short-horizon dislocation, and a stabilization bar. Each condition is objective and computed from closed daily bars. | [F] definition |
| Q2 | Counterparty: panic sellers, forced liquidators, and attention-driven retail flow that overshoots fundamental value. The counterparty is not necessarily wrong about the news; they are constrained to sell at any price. | [L] overreaction, [H] crypto flow |
| Q3 | Mechanism: long-horizon overreaction and subsequent reversal (De Bondt–Thaler), with short-horizon reversal as a liquidity-provision premium. The regime and stabilization filters are intended to keep the trade out of genuine regime changes. | [L] reversal, [E] filters |
| Q4 | BTC-specific: BTC exhibits speculative bubble behaviour and negative bubbles (Cheah–Fry; Fry–Cheah), and it is used as a speculative asset rather than a medium of exchange (Baur–Hong–Lee). That supports overreaction, but it also supports strong trends, which is the opposite of mean reversion. | [L] both directions |
| Q5 | Long-only spot means the strategy can only buy dips. It cannot short euphoria, which is where much of the overreaction evidence is strongest. It is structurally long crash risk: capped upside, fat left tail. | [E] |
| Q6 | Stop below the confirmed swing low by 1.0×ATR, typically 5–10%. The stop is outside normal daily noise but not outside a regime break; a gap through it is the main tail risk. | [E] |
| Q7 | Exit at the 20-day mean, 2R, or 20 days. The reversion horizon is days to weeks, consistent with the dislocation being a liquidity/attention event rather than a change in the long-run trend. | [E] |
| Q8 | Frequency: **low** [H]. The conjunction of a non-bear regime, a dislocation, and a stabilization bar is rare. In a strong bull phase the dislocation may not occur; in a bear phase the regime filter blocks it. A realistic count is 10–30 episodes over 3.5 years, and the 20-day calendar ceiling is 63. | [H] |
| Q9 | Stop 5–10%, so `cost_R = 0.026–0.052`. It clears the gate comfortably. The binding constraint is not cost; it is episode scarcity and adverse exposure. | [E] arithmetic |
| Q10 | At 1% risk, an 8% stop implies `$1,250` notional (12.5% of $10,000); a 5% stop implies $2,000 (20%). Concurrency is 1–2. Capital utilisation is low, but the position is exposed to a multi-day drawdown. | [E] arithmetic |
| Q11 | Buying into a falling market means the entry and stop are both in a high-slippage state. A stabilization bar can fail on the next open; a stop can gap. The 26 bp proxy is unlikely to cover a panic-day fill. | [E], [H] |
| Q12 | Falsified if the regime filter removes all bear-market signals and the strategy collapses to long beta, if the stabilization filter enters after the bounce is over, or if the drawdown/vol filters are fit to 2022. Strongest objection: long-only mean reversion in an asset with strong momentum and fat left tails is structurally short crash risk, and the filters are a single-cycle fit. | [E], [L] |

### 5.3 Economics and frequency

**Mechanism strength.** Weak-to-moderate for BTC spot. The overreaction literature is real, but it is
strongest in cross-sectional equity portfolios and in short-horizon liquidity provision. For a single
long-only crypto asset, the dominant empirical fact is momentum, not reversal. The candidate is
therefore fighting the asset's own dynamics. The regime and stabilization filters are sensible risk
controls, but they also make the hypothesis harder to falsify: almost any outcome can be attributed
to the filter being too tight or too loose.

**The falling-knife problem is not solved by a filter.** A regime filter reduces the probability of
buying a bear-market decline, but it does not eliminate it: the 2022 bear market had multiple rallies
above the 200-day mean that failed. The stabilization bar is a one-bar confirmation; it is not
evidence that the decline has ended. The honest description is "delayed entry into a falling knife,"
not "avoidance of falling knives."

**Frequency and the floor.** At a 20-day non-overlap the ceiling is 63, and the realistic count is
lower. C cannot satisfy the 150 floor. It is the least testable of the four candidates under the
existing protocol.

**Verdict for this stage.** Do not recommend. The mechanism is the weakest for BTC spot, the
falling-knife risk is the highest, and the frequency is structurally below the floor. Retain only as
a research question if the programme later obtains a cross-sectional universe or a short leg.

---

## 6. Candidate D — intraday continuation with a higher-timeframe volatility budget

### 6.1 What it is, and why the volatility budget matters

**Canonical form for a future census.** On 15m BTCUSDT, with 1h execution and 4h/daily context:

1. **Volatility budget.** Daily ATR(14) must be between its 25th and 80th percentile over the trailing
   90 days, or 4h realized volatility must be between 0.5× and 1.5× its 30-day median. This excludes
   dead markets (no range to continue) and crisis markets (jump risk and whipsaw). The budget is the
   higher-timeframe conditioner.
2. **Session definition.** Use UTC sessions: Asia `00:00–08:00`, Europe `08:00–16:00`, US
   `16:00–00:00`. For each session, compute the first-two-hour return. A long candidate requires that
   return to exceed `+0.5 x ATR(14, 1h)` and price to be above the session VWAP.
3. **Entry.** At the end of the first two hours of the session, enter long at the next 15m open.
4. **Stop.** `1.0 x ATR(14, 1h)` below entry, or a hard 1.30% floor, whichever is farther. The floor
   is required by `cost_R <= 0.20`. If the structural stop is tighter than 1.30%, skip the signal.
5. **Exit.** Session end, 2R, or stop. The census uses a 24h non-overlap horizon, i.e. at most one
   accepted signal per UTC day.
6. **Sensitivity.** 12h and 48h non-overlap, and a single-session (US only) variant, to test whether
   the result depends on the session definition.

**Why the volatility budget is not cosmetic.** The documented intraday-momentum effect is strongest in
normal-volatility conditions and can invert in crisis conditions, when the first move is a liquidity
shock and the rest of the day mean-reverts. A naive "first two hours predict the rest" rule would be
tested across both states and would average to nothing. The budget is an attempt to state the
condition under which the mechanism is supposed to hold. It is also a degrees-of-freedom risk: a
three-parameter budget can be tuned to the sample.

### 6.2 The twelve questions

| # | answer | tag |
|---|---|---|
| Q1 | Market state: a normal-volatility day, a directional first two hours in a UTC session, price above session VWAP, and a session-relative continuation entry. All inputs are closed-bar values. | [F] definition |
| Q2 | Counterparty: late-informed traders and infrequent rebalancers who trade toward the session close, plus intraday mean-reversion traders who fade the first move too early. | [L] equity evidence, [H] crypto |
| Q3 | Mechanism: intraday momentum is documented in US equity indices — the first half-hour return predicts the last half-hour return (Gao–Han–Li–Zhou). Proposed drivers are late-informed trading and infrequent rebalancing. The mechanism is session-close-specific; BTC has no close. | [L] equities, [H] BTC |
| Q4 | BTC-specific: BTC trades 24/7, so the "session" is a convention, not an exchange close. The closest crypto analogue is the dominance of US/Europe flow at certain UTC hours. There is no strong published BTC spot evidence for this exact rule. | [H] |
| Q5 | Long-only spot excludes the short side of a down-open day. If the effect is symmetric, the long-only version captures only part of it; if it is asymmetric, the long side may be the weaker side. | [E] |
| Q6 | Stop 1.0×ATR(1h) or 1.30%, whichever is farther. The 1.30% floor is a cost constraint, not a market-structure stop. For BTC, 1.30% is roughly 0.4–0.6 of a daily ATR, so it is not absurdly wide, but it is wider than a typical intraday stop. | [E] |
| Q7 | Exit at session end, 2R, or stop. The session-end exit is the mechanism's natural horizon: the predicted quantity is the rest of the session. A 24h non-overlap is a census convention to prevent multiple same-day counts. | [E] |
| Q8 | Frequency: **high** [H]. Three sessions per day for 1,277 days gives up to 3,831 session candidates before filters; after the vol budget and signal threshold, a realistic range is 300–800 raw and 150–300 non-overlapping at 24h. This is the only candidate with a plausible path to 150. | [H] |
| Q9 | Stop 1.3–2.0% typical, so `cost_R = 0.13–0.20`. The 1.30% floor is exactly the gate boundary. Median may be ~0.17. This is the central tension: the candidate is frequent enough, but cost consumes most of a 0.15R edge. | [E] arithmetic |
| Q10 | At 1% risk, a 1.3% stop implies `$7,692` notional (77% of $10,000); a 2.0% stop implies $5,000 (50%). One position at a time is the realistic cash constraint; two concurrent 1.3%-stop positions would exceed 100% of spot cash. | [E] arithmetic |
| Q11 | Intraday market orders cross the spread; stops are close and can be hit by noise; target fills are uncertain; session boundaries are arbitrary; the 26 bp proxy may understate Nobitex spread. At $10k the minimum notional and lot size are unlikely to bind, but the venue is unverified. | [E], [H] |
| Q12 | Falsified if BTC spot shows no session-relative intraday momentum, if the vol budget selects only noise, or if median `cost_R` exceeds 0.20R. Strongest objection: the evidence is from equity indices with a fixed close; BTC has no close, the session is arbitrary, and the cost gate forces stops so wide that the strategy is only nominally intraday. | [E], [L] equities |

### 6.3 Economics and frequency

**Mechanism strength.** Moderate but fragile. Intraday momentum has credible evidence in equity
indices, and the "late-informed traders / infrequent rebalancing" explanation is plausible. The
transfer to 24/7 BTC spot is an analogy, not a result. The higher-timeframe volatility budget is a
genuine improvement over a naive rule because it states the regime in which the mechanism should
operate, but it also adds three parameters that can be fitted.

**Frequency versus cost.** D is the only candidate that can plausibly reach 150 non-overlapping
episodes. It is also the candidate where the cost gate bites hardest: a 1.30% stop is the minimum that
keeps `cost_R <= 0.20`, and at that minimum the entire round trip consumes the full gate. A future
census must report the feasible share, the median `cost_R`, and the cost-adjusted edge. A high raw
count with a 40% feasible share is not a pass.

**Capital.** The tight-stop/large-notional geometry is the opposite of Candidate A's. D uses most of
the account per position and cannot run two positions without exceeding spot cash. That is a real
constraint, not a modelling detail: the backtest engine's single-position limit happens to match D's
cash reality, but B would need multi-position accounting.

**Verdict for this stage.** Recommend for a future feasibility census, primarily because it is the
only candidate with a credible path to the 150 floor and the best statistical testability. The
recommendation is conditional on the cost-adjusted screen and on a session-sensitivity test.

---

<!-- STAGE2D_APPEND -->
