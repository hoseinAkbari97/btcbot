# Stage 2M — Statistical Sufficiency Framework

**Stage:** 2M (research-governance and methodology design only)
**Status:** proposal requiring owner approval. No census, backtest, bootstrap, Monte Carlo, or
market-data analysis is performed.
**Date:** 2026-11-09 (UTC)

**Evidence labels:** **Verified fact** (repository-supported, cited), **Interpretation** (reasoned
conclusion), **Proposal** (suggested methodology requiring approval), **Owner decision** (cannot be
made by the research agent).

---

## 0. Purpose

This document proposes how a future experiment should decide whether it has enough evidence to
support an economic conclusion. It addresses:

1. the distinction between signals, opportunities, trades, episodes, and effective sample size;
2. the definition and role of a minimum meaningful effect;
3. dependence-aware evidence and the limits of common techniques;
4. a sample-sufficiency methodology derived from the owner's objective;
5. statistical uncertainty and error control;
6. multiple-testing concerns;
7. why the historical thresholds are not universal standards.

It does **not** derive a new numerical requirement from historical data. It does **not** run a
bootstrap, Monte Carlo, power simulation, or census. It provides a structure that the owner can
approve, modify, or reject.

**Verified fact:** the historical programme used a 150-opportunity floor, a 349-observation planning
reference, and a `0.15R` design assumption. None is a universal statistical standard
(`docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` §11.3;
`docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` §12.2;
`docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0).

---

## 1. Definitions and why the distinctions matter

### 1.1 The evidence hierarchy

| concept | definition | how it is obtained | what it can support | what it cannot support |
|---|---|---|---|---|
| **Raw signal** | every detector trigger, including duplicates, overlaps, and signals that cannot be executed | detector run on the frozen rules | debugging and funnel accounting | opportunity count; independence |
| **Unique opportunity** | a signal deduplicated by the frozen episode/session rule | deduplication | the size of the candidate's opportunity set | trade count; independence |
| **Non-overlapping trade** | an opportunity accepted after the frozen overlap rule | greedy or equivalent acceptance | a countable, executable-ish set | independent observations; absence of dependence |
| **Independent episode** | a market episode separated from others by a defined cooling-off or regime break | pre-specified episode definition | an approximation to independent units | proof of independence; a universal definition |
| **Effective sample size (ESS)** | the number of independent observations that would carry the same information as the dependent sample | a dependence model or diagnostic | an input to uncertainty and power | a unique, model-free quantity |
| **Statistical uncertainty** | the range of plausible values for the estimand under a stated model | standard error, confidence interval, posterior, bootstrap | a decision about whether the MME is supported | economic usefulness by itself |
| **Minimum meaningful effect (MME)** | the smallest true net effect that would justify operating the rule | owner decision, before seeing outcomes | the threshold for economic usefulness | a statistical estimate |

### 1.2 Why the distinctions matter

**Interpretation:**

- A **raw signal count** overstates the evidence because it includes duplicates and overlaps. The
  historical funnel reports make this visible: for Candidate B, 458 episode attempts became 34
  structurally valid episodes and 24 canonical opportunities; for Candidate D, 3,829 evaluable
  sessions became 295 pre-gate signals and 34 canonical opportunities
  (`docs/research/stage2j/CANDIDATE_B_CENSUS_REPORT.md` §2;
  `docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md` §2).
- A **unique opportunity count** still overstates the evidence if the opportunities cluster in a few
  regimes or episodes. Candidate D's design effect was 3.93, and its cost-feasible signals were
  concentrated in 2021–2022 (`CANDIDATE_D_CENSUS_REPORT.md` §6).
- A **non-overlapping trade count** is a construction rule, not an independence claim. The historical
  reports state this explicitly (`SHARED_CENSUS_PROTOCOL.md` §3.1;
  `stage2j/CANDIDATE_COMPARISON.md` §7).
- An **independent episode count** is a modelling choice. Different episode definitions produce
  different counts and different uncertainty.
- **Effective sample size** is model-dependent. There is no single correct value; there are
  defensible ranges under different assumptions.
- **Statistical uncertainty** answers "how precisely do we know the effect?" It does not answer "is
  the effect large enough to matter?" That is the MME question.
- The **MME** is an economic decision, not a data quantity. It must be declared before the outcome is
  observed.

**Proposal:** every future report should state all seven quantities, or explicitly state which are
not applicable and why. A report that gives only one count is not sufficient for a decision.

---

## 2. Minimum meaningful effect

### 2.1 Definition and timing

**Proposal:** the MME is the smallest **true net effect** — after all execution costs and under the
declared risk policy — that would make the rule worth operating. It must be declared before the
experiment observes any outcome, and it must be expressed in the same metric as the primary estimand.

The MME is not:

- the observed effect;
- the effect the project hopes to find;
- a statistically detectable effect;
- a number chosen to make a candidate pass.

### 2.2 Candidate definitions and consequences

The economic framework sets out the full option set. For statistical purposes, the key choices are:

| definition | statistical consequence | economic consequence |
|---|---|---|
| **net R per executed trade** | requires a variance estimate in R; natural for a one-sample or regression test | ignores frequency; a sparse rule can pass |
| **net expectancy per opportunity** | requires a definition of the opportunity denominator; includes unfilled signals | penalizes execution losses; can be diluted by unusable signals |
| **net return on notional** | variance depends on price volatility and stop; comparable to funding costs | ignores risk; can favour tight-stop rules |
| **annualized net return** | requires a time-series model, compounding, and a capital policy; highly noisy | directly decision-relevant; sensitive to idle capital and regime |
| **risk-adjusted ratio** | ratio estimators have poor small-sample properties; bootstrap or delta method needed | useful as a secondary metric; risky as a primary target |
| **certainty-equivalent utility** | requires a utility function and a distributional model | theoretically complete; practically demanding |

**Interpretation:** the choice of MME definition determines the entire sufficiency calculation. A
`0.15R` per-trade target, a `3%` annual return target, and a `0.05` Sharpe target imply different
sample sizes, different data requirements, and different failure modes. The framework should not
pretend that one number can stand for all of them.

**Owner decision:** the MME definition and value. This is D-01 in the owner-decision register.

### 2.3 Why the historical `0.15R` cannot be assumed

**Verified fact:** `0.15R` appears in the historical specifications as a design assumption used for
the detectable-effect diagnostic, not as an owner-declared economic threshold
(`CANDIDATE_B_SPEC.md` §0.1; `SHARED_CENSUS_PROTOCOL.md` §7.3).

**Verified fact:** under the record's own independence assumptions, the smallest detectable effect at
150 observations is about `0.229R`, not `0.15R` (`FAILURE_MODE_ANALYSIS.md` §7.3).

**Interpretation:** the historical programme was testing a design assumption, not the owner's
economic objective. A future framework must not inherit `0.15R` as if it were approved.

---

## 3. Dependence

### 3.1 Sources of dependence

Trading observations can be dependent through several mechanisms:

| source | example | consequence |
|---|---|---|
| **Market-episode clustering** | several signals in the same volatility expansion or trend | observations within an episode share the same market path |
| **Temporal dependence** | overlapping holding periods, autocorrelated returns, intraday seasonality | adjacent observations are correlated |
| **Regime persistence** | a bull, bear, or low-volatility regime lasts months | observations in the same regime share conditions |
| **Signal overlap** | two rules trigger on the same bar or episode | duplicate information |
| **Cross-sectional dependence** | multiple instruments or sessions exposed to the same shock | observations are not independent across the cross-section |
| **Model/selection dependence** | the same data were used to choose the rule | the reported effect is optimistically biased |

**Interpretation:** the historical concentration diagnostics show that these mechanisms are not
hypothetical. Candidate A's largest regime-episode share was 13.9% and its Kish effective size was
12.69; Candidate D's design effect was 3.93; Candidate B's was 1.69
(`HISTORICAL_RESEARCH_SYNTHESIS.md` §4.3, §6.3, §7.3). These are descriptive, but they establish that
the observations are not plausibly independent.

### 3.2 Methods and their limits

| method | what it does | assumptions | strengths | weaknesses | descriptive or inferential? |
|---|---|---|---|---|---|
| **Market-episode clustering** | groups observations into pre-defined episodes and treats the episode as the unit | episodes are exchangeable; within-episode correlation is captured; between-episode dependence is negligible | transparent; directly tied to the trading mechanism | episode definition is contestable; residual between-episode dependence remains | inferential if used with a cluster-robust estimator; descriptive if only shares are reported |
| **Cluster-robust standard errors (CRSE)** | adjusts SEs for correlation within clusters | clusters independent; large number of clusters; regularity conditions | standard; available in common software | unreliable with few clusters; sensitive to cluster definition; can be anti-conservative | inferential |
| **Wild cluster bootstrap** | bootstraps residuals within clusters to improve small-cluster inference | cluster exchangeability; maintained model | better than CRSE with few clusters | computationally heavier; still model-dependent | inferential |
| **HAC/Newey-West** | adjusts SEs for serial correlation | stationarity; bandwidth choice; linear model | standard for time series | bandwidth sensitive; poor with strong persistence or breaks | inferential |
| **Moving-block bootstrap** | resamples contiguous blocks to preserve local dependence | weak dependence; block length captures dependence | non-parametric; captures autocorrelation | block length choice; boundary effects; nonstationarity | inferential |
| **Stationary bootstrap** | random block lengths; preserves dependence | stationarity; dependence decays | smoother than fixed blocks | tuning parameter; still model-dependent | inferential |
| **Kish effective sample size** | `n_eff = (Σ n_k)^2 / Σ n_k^2` over non-empty clusters | perfect within-cluster dependence; no between-cluster dependence | simple; transparent concentration diagnostic | not a serial-dependence estimator; ignores between-cluster dependence; model-free but assumption-heavy | **descriptive** |
| **Design effect** | `N / n_eff` | same as Kish | intuitive inflation factor | inherits Kish's limitations; not a test | **descriptive** |
| **Autocorrelation-based ESS** | `n_eff = N / (1 + 2 Σ ρ_k)` or a spectral estimate | stationarity; estimated autocorrelation | captures temporal dependence | sensitive to lag choice and nonstationarity | inferential if used with a model; diagnostic otherwise |
| **Variance-ratio / batch-means** | estimates long-run variance from batches | weak dependence; batch size | robust to some model misspecification | batch-size choice; small-sample bias | inferential |

### 3.3 What the methods do not do

**Interpretation:**

- **Non-overlap is not independence.** The historical overlap rule is a construction rule that
  prevents concurrent trades. It does not remove serial dependence, regime clustering, or common
  shocks. The reports correctly refuse to describe non-overlapping observations as independent
  (`SHARED_CENSUS_PROTOCOL.md` §3.1; `stage2j/CANDIDATE_COMPARISON.md` §7).
- **Kish effective sample size is not a serial-dependence estimator.** It measures the concentration
  of observations across clusters under an assumed perfect within-cluster correlation. It does not
  estimate autocorrelation, and it does not produce a valid standard error on its own
  (`FAILURE_MODE_ANALYSIS.md` §6.5).
- **No single technique automatically solves dependence.** Cluster-robust SEs can fail with few
  clusters; block bootstrap can fail with nonstationarity; HAC can fail with strong persistence.
  A defensible analysis reports more than one method and shows whether the conclusion is robust.

### 3.4 Proposed dependence policy

**Proposal:**

1. **Pre-specify a primary dependence model.** Define the cluster or block unit before seeing
   outcomes. The natural candidate is the market episode used by the strategy, but the owner/analyst
   must justify it.
2. **Report at least two defensible treatments.** For example, episode-clustered SEs and a
   block bootstrap with a pre-specified block length. If the conclusion changes across treatments,
   the result is **inconclusive**.
3. **Report the effective sample size under each treatment.** Do not report a single Kish number as
   if it were the effective sample size.
4. **Report sensitivity to cluster definition.** Use at least episode, calendar period, and regime
   run where meaningful. Show how the SE, CI, and decision change.
5. **Do not use non-overlap as a substitute for a dependence model.** Non-overlap is a construction
   rule; it is not an inferential adjustment.
6. **Do not use Kish as the primary uncertainty estimate.** Report it as a descriptive concentration
   diagnostic alongside the inferential treatment.
7. **Pre-specify the small-sample correction.** With few clusters, use a method designed for few
   clusters (e.g., wild cluster bootstrap) or acknowledge the limitation.

**Owner decision:** the acceptable dependence treatment and the required robustness standard. This
is D-09 in the register.

---

## 4. Statistical uncertainty and error control

### 4.1 What to report

**Proposal:** every primary estimate should be reported with:

- the point estimate;
- a confidence interval (or credible interval) under the pre-specified dependence model;
- the number of raw signals, unique opportunities, non-overlapping trades, and clusters;
- the effective sample size and design effect under each treatment;
- the method and its assumptions;
- a sensitivity table across at least two dependence treatments and at least two cost scenarios.

### 4.2 Error-control options

| objective | what it controls | how it is specified | consequence |
|---|---|---|---|
| **Two-sided significance** | probability of a false positive under the null | `α` (e.g., 5%) | familiar; does not control power or economic relevance |
| **Power for the MME** | probability of detecting the MME if it is true | `1-β` (e.g., 80%) | requires an assumed variance and sample size |
| **Precision / interval width** | width of the confidence interval | maximum half-width `h` | directly useful for decision-making; may require a large sample |
| **False discovery rate** | expected share of false positives among discoveries | `q` (e.g., 10%) | relevant when testing many hypotheses |
| **Family-wise error rate** | probability of any false positive in a family | `α` with a correction | conservative; can be impractical with many tests |
| **Bayesian credible interval** | posterior probability that the effect exceeds the MME | prior and likelihood | requires a prior; sensitive to prior choice |
| **Decision-theoretic loss** | expected loss from a wrong decision | loss function and prior | most decision-relevant; hardest to specify |

**Interpretation:** the owner does not need to choose a single objective for every purpose, but the
primary decision rule must name one. A common structure is: control the two-sided error rate for the
primary test, target power for the MME, and report the interval width as a precision diagnostic.

**Owner decision:** the error-control objective and the confidence level. This is D-08 in the
register.

### 4.3 Decision rule based on uncertainty

**Proposal:** for a primary estimand with a two-sided interval `[L, U]` and an MME `δ`:

| condition | interpretation | proposed decision |
|---|---|---|
| `L ≥ δ` | the evidence supports an effect at least as large as the MME | the hypothesis may proceed to the next gate, subject to risk and robustness checks |
| `U < δ` and `L > 0` | a positive effect is detected, but it is too small to be economically useful | reject the hypothesis as economically insufficient |
| `U < 0` | the evidence supports a negative effect | reject the hypothesis |
| interval includes `δ` or `0` | the evidence is not precise enough to distinguish the MME from zero | **inconclusive**; do not promote |

**Interpretation:** this rule is stricter than "statistically significant." It requires the evidence
to distinguish the MME from zero, not merely the effect from zero. It also prevents a large point
estimate with a wide interval from being treated as a pass.

---

## 5. Sample sufficiency

### 5.1 Why a universal count is insufficient

**Interpretation:** a count threshold cannot encode:

- the size of the effect the owner cares about;
- the variance of the outcome;
- the dependence structure;
- the definition of an opportunity;
- the fill/execution rate;
- the capital and risk context;
- the cost level;
- the number of hypotheses tested.

The historical 150 floor was underived, and the 349 reference assumed independence
(`FAILURE_MODE_ANALYSIS.md` §7.3; `CANDIDATE_B_SPEC.md` §11.3). A future framework should derive the
requirement from the decision, not inherit a count.

### 5.2 Proposed methodology

**Proposal:** the sample-sufficiency methodology has six steps.

**Step 1 — Declare the decision inputs.**

- MME `δ` in the primary metric (owner decision);
- outcome variance `σ²` or a defensible estimate/model;
- error-control objective (`α`, power `1-β`, or precision `h`);
- primary dependence model and design effect `DE` (or a distribution);
- expected execution/fill rate `p_exec`;
- expected opportunity frequency `f` (from a feasibility census, not from outcomes);
- risk and capital constraints.

**Step 2 — Choose the estimator and test.**

- e.g., a one-sample test of mean net R, a regression with cluster-robust SEs, or a block-bootstrap
  interval;
- pre-specify the primary estimand and the null/alternative;
- pre-specify the dependence treatment and the small-sample correction.

**Step 3 — Compute the independent-observation requirement.**

For a two-sided test of a mean with known/assumed variance, the standard approximation is:

```
N_ind ≈ (z_{1-α/2} + z_{1-β})² × σ² / δ²
```

For a precision target with half-width `h`:

```
N_ind ≈ (z_{1-α/2} × σ / h)²
```

These are conventional approximations, not universal rules. They assume a normal or asymptotically
normal estimator and a correctly specified variance. The framework should state the assumptions and
use a simulation or a finite-sample correction if they are doubtful.

**Step 4 — Inflate for dependence.**

```
N_obs ≈ N_ind × DE
```

where `DE` is the design effect implied by the dependence model. For cluster sampling with average
cluster size `m` and intra-cluster correlation `ρ`, `DE ≈ 1 + (m-1)ρ`. For time series, `DE` can be
estimated from the long-run variance or a block-bootstrap simulation. The framework should report a
range of `DE` values, not a single point.

**Step 5 — Convert to opportunities and check practicality.**

```
required_opportunities ≈ N_obs / p_exec
```

where `p_exec` is the expected share of opportunities that become executed trades. Compare the result
with the expected opportunity frequency `f` and the calendar ceiling over the intended test period.
If the required count cannot be reached within the available calendar and data, the hypothesis is
**not testable on this interval** under the declared objective. That is a legitimate outcome, not a
reason to lower the requirement.

**Step 6 — Freeze the rule.**

Record the MME, `α`, power/precision, `σ`, `DE`, `p_exec`, `N_ind`, `N_obs`, `required_opportunities`,
the estimator, the dependence treatment, and the decision rule in the pre-registration. Freeze the
hashes before the outcome experiment.

### 5.3 Conceptual illustrations

**Proposal:** the following examples are arithmetic illustrations of the method. They are **not**
recommendations, **not** derived from historical data, and **not** a new threshold. They show how the
required sample changes with the inputs.

| illustration | assumptions | `N_ind` | `DE` | `N_obs` | interpretation |
|---|---|---:|---:|---:|---|
| I-1 | `δ = 0.15R`, `σ = 1R`, `α = 0.05` two-sided, power 0.80 | ≈ 349 | 1.0 | ≈ 349 | the historical independence reference |
| I-2 | same as I-1 | ≈ 349 | 2.0 | ≈ 698 | a modest cluster inflation doubles the requirement |
| I-3 | same as I-1 | ≈ 349 | 4.0 | ≈ 1,396 | strong clustering makes the requirement four times larger |
| I-4 | `δ = 0.30R`, `σ = 1R`, `α = 0.05`, power 0.80 | ≈ 87 | 2.0 | ≈ 174 | a larger MME reduces the requirement |
| I-5 | precision `h = 0.05R`, `σ = 1R`, 95% | ≈ 1,537 | 2.0 | ≈ 3,074 | a precision target can be much stricter than a power target |

**Interpretation:** the examples show why a universal count is indefensible. A requirement can range
from tens to thousands depending on the MME, variance, dependence, and precision objective. The
framework must derive the number, not assume it.

**Important:** these illustrations use only conventional statistical arithmetic. They do not use
historical market data, historical counts, or historical outcomes. The historical counts are not
inputs to the calculation.

### 5.4 What the owner must approve

**Owner decision:** the sample-sufficiency methodology, including:

- whether the primary objective is power, precision, or a decision-theoretic criterion;
- the MME and its definition;
- the variance assumption and its source;
- the dependence model and design-effect range;
- the execution/fill-rate assumption;
- the rule for what happens if the required sample exceeds the available calendar.

This is D-10 in the register.

---

## 6. Multiple-testing and selection concerns

### 6.1 Why it matters

**Interpretation:** if the project tests many candidate rules, variants, thresholds, or timeframes,
the chance of a false positive rises. The historical programme designed and censused four candidates,
changed the opportunity floor from 200 to 150, and selected candidates on frequency intuition
(`HISTORICAL_RESEARCH_SYNTHESIS.md` §3; `FAILURE_MODE_ANALYSIS.md` §7.4). Even without a formal
multiplicity problem in the historical censuses (which observed no outcomes), a future outcome
programme would face one.

### 6.2 Options

| approach | what it controls | when it is appropriate | cost |
|---|---|---|---|
| **Single pre-registered hypothesis** | nothing beyond the primary test; avoids multiplicity by construction | one hypothesis, one primary test | requires discipline; no exploration |
| **Bonferroni / Holm** | family-wise error rate | a small, pre-declared family | conservative; low power |
| **Benjamini-Hochberg FDR** | expected false-discovery proportion | many hypotheses, exploratory programme | requires a defined family; less conservative |
| **Hierarchical / gatekeeping** | FWER across ordered hypotheses | a pre-declared testing order | complex; requires discipline |
| **Alpha spending** | type I error across sequential looks | sequential monitoring | requires a pre-specified spending function |
| **Sample split / holdout** | selection bias | model or parameter selection | consumes data; needs a clean holdout |
| **Pre-registration + OOS confirmation** | selection and overfitting | any programme with exploration | requires a genuine holdout and one-look discipline |

**Proposal:** pre-register one primary hypothesis and one primary test. Treat all other candidates,
variants, and metrics as secondary or exploratory. If the programme intends to test multiple
hypotheses, declare the family and the correction before seeing outcomes. Report every attempt,
including failures. Do not select the reported result after seeing the outcomes.

### 6.3 Selection bias

**Interpretation:** if a candidate is chosen because its count is high, or a threshold is chosen
because it makes a candidate pass, the nominal p-value is invalid. The historical Stage 2K warning is
directly relevant: a new variant after seeing 24 opportunities would be a post-hoc hypothesis
(`STAGE2K_FINAL_RECOMMENDATION.md` §1.4 and §3.3). A future framework should freeze the hypothesis
and the decision rule before looking at outcomes, and should record every version of the hypothesis
that was considered.

---

## 7. Limitations of the previous thresholds

| threshold | status | limitation | consequence for a future framework |
|---|---|---|---|
| **150 non-overlapping opportunities** | project choice from the Stage 2C freeze | no statistical derivation; not tied to the MME; sufficient only for about `0.23R` under independence | do not inherit; derive the requirement |
| **349 independent observations** | planning reference for `0.15R`, `σ=1R`, 5%, 80% | assumes independence; ignores clustering and fat tails; not a requirement | use as an input to a dependence-aware calculation, not as a rule |
| **`0.15R` effect of interest** | design assumption | not owner-declared; may be too small or too large for the owner's objective | owner must declare the MME |
| **`cost_R ≤ 0.20`** | project threshold | not derived from the owner's economics; equivalent to a 1.30% minimum stop at 26 bp | replace with a cost model tied to the economic objective |
| **Concentration screen 50% / 2.00** | descriptive project criterion | not a statistical test; arbitrary cut-offs; Kish is not a serial-dependence estimator | keep as a diagnostic; do not treat as proof of independence or dependence |
| **Non-overlap horizons (24h, 72h, 120h)** | construction rules | not holding periods or independence guarantees; materially affect counts | pre-specify the horizon and report sensitivity |
| **Feasible-share thresholds 0.25 / 0.30** | proposed, never adopted | not derived; would classify B and A as feasible and D as not | do not adopt without an economic rationale |
| **500 / 50% concentration rules** | project choices | descriptive; no inferential justification | use as diagnostics, not verdict terms |

**Verified fact:** the status of these thresholds is recorded in
`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §8.3 and
`docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §7.

---

## 8. Proposed decision structure

**Proposal:** a future experiment should use the following structure. It is a template, not an
authorization.

### 8.1 Before the experiment

1. Owner approves the MME, risk limits, capital context, and primary estimand.
2. Analyst declares the error-control objective, dependence model, estimator, and multiple-testing
   policy.
3. Analyst computes `N_ind`, `N_obs`, and `required_opportunities`, with sensitivity ranges.
4. A feasibility census (no outcomes) estimates whether the required opportunity count is plausible
   within the available calendar.
5. The hypothesis, rules, metrics, methods, and decision rule are frozen and hashed.
6. An independent auditor verifies the specification-to-code trace and the synthetic tests.

### 8.2 At the analysis

1. Estimate the primary metric with a dependence-adjusted interval.
2. Compare the interval with the MME and the risk limits.
3. Report the secondary metrics, cost sensitivity, regime stability, and concentration diagnostics.
4. Report every pre-registered test and every deviation.
5. Apply the pre-registered decision rule.

### 8.3 Possible outcomes

| outcome | condition | authority |
|---|---|---|
| **Reject** | interval upper bound below the MME, or a risk limit breached | pre-registered rule; owner informed |
| **Inconclusive** | interval includes the MME or zero; or robustness fails | pre-registered rule; no promotion |
| **Continue research** | interval supports the MME but a gate or robustness check is unresolved | separately authorized stage |
| **Advance to paper trading** | all gates pass, including independent audit and OOS confirmation | separate owner authorization |
| **Abandon direction** | the requirement is unattainable or the mechanism fails | owner decision |

**Interpretation:** no outcome automatically authorizes the next stage. The decision structure is a
filter, not a promotion machine.

---

## 9. Owner decisions arising from this document

| ID | decision | why it cannot be made by the research agent |
|---|---|---|
| D-08 | statistical confidence/error-control objective (`α`, power, precision, or decision-theoretic) | depends on the owner's tolerance for uncertainty and the cost of a wrong decision |
| D-09 | dependence treatment and required robustness standard | depends on the owner's acceptance of model risk and the available data |
| D-10 | sample-sufficiency methodology and whether the MME is defined in R, notional, or annual terms | determines the entire experiment design |
| D-11 | multiple-testing policy and the definition of the testing family | depends on how many hypotheses the owner intends to consider |
| D-12 | validation/OOS access policy and one-look discipline | determines whether the final evidence is credible |

---

## 10. Summary

The historical framework used a count threshold that was not derived from an economic objective and
a dependence diagnostic that was not an inferential procedure. It correctly refused to treat
non-overlapping observations as independent, but it did not replace that refusal with a positive
dependence model.

Stage 2M proposes:

- a clear hierarchy from raw signals to effective sample size;
- an owner-declared MME;
- a pre-specified dependence model with at least two robustness treatments;
- a derived sample requirement that inflates for dependence and execution losses;
- an interval-based decision rule that compares the evidence with the MME, not merely with zero;
- a multiple-testing and selection policy.

The framework does not choose the MME, the error-control objective, the dependence model, or the
required sample. Those are owner decisions. It provides the structure in which those decisions can be
made without inventing a universal threshold.
