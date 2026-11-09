# Stage 2M — Current Framework Gap Analysis

**Stage:** 2M (research-governance and methodology design only)
**Status:** design-only proposal. No candidate, census, backtest, market-data processing, or
implementation is authorized or performed by this document.
**Date:** 2026-11-09 (UTC)

**Repository baseline at review start:** branch `main`, HEAD
`93152bd21893b63422f113d977b677f8386889b2`
(`stage2l: seal the audit with a freeze manifest`), clean working tree, synchronized with
`origin/main`.

**Evidence labels used in Stage 2M:**

- **Verified fact:** supported by an existing repository artifact, cited by path and section.
- **Interpretation:** a reasoned conclusion based on verified facts; not itself recorded history.
- **Proposal:** a suggested future methodology requiring owner approval.
- **Owner decision:** a decision that cannot responsibly be made by the research agent.

---

## 0. Purpose and limits

This document records what the existing research framework actually is, what it has established,
what it has not established, and where the gaps lie. It is the evidence base for the three design
documents that follow:

- `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md`
- `STATISTICAL_SUFFICIENCY_FRAMEWORK.md`
- `RESEARCH_GOVERNANCE_PROTOCOL.md`

It does **not**:

- develop or modify a trading strategy;
- create a candidate specification;
- run a detector, census, or backtest;
- read, decode, or summarize development, validation, or out-of-sample market rows;
- recompute a historical opportunity count;
- calculate P&L, expectancy, win rate, CAGR, drawdown, Sharpe, Sortino, or an equity curve;
- run bootstrap, Monte Carlo, or optimization;
- change a historical report, specification, threshold, or verdict;
- repair Stage 2J or Stage 2L implementation code;
- begin Stage 2N.

The gap analysis is based on the documents and aggregate machine-readable evidence already in the
repository. No market data was opened for this document.

---

## 1. Repository and integrity baseline

### 1.1 Repository state at review start

| item | observed value | source |
|---|---|---|
| branch | `main` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `93152bd21893b63422f113d977b677f8386889b2` | `git rev-parse HEAD` |
| remote tracking | `origin/main`, synchronized | `git status -sb` |
| working tree | clean | `git status --short` |

**Verified fact:** the Stage 2K and Stage 2L freeze manifests both validate against their recorded
self-hashes and file hashes. The verification method and results are recorded in the Stage 2M
`FREEZE_MANIFEST.json` and are reproducible with the procedure stated there.

**Verified fact:** Stage 2L records the Stage 2J census execution commit as
`bc1285c8277c37c93b76addfe83dcb50267c1f35` and the Stage 2J artifact commit as
`737bf90f32b3c49f72008040696c07f9ce326d84`; both are ancestors of the Stage 2M baseline
(`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1, §5).

### 1.2 Frozen baseline used by the historical census

| item | value | source |
|---|---|---|
| frozen research baseline | `docs/research/stage2e_v2/`, version `2.0.0` | `stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §1 |
| frozen manifest SHA256 | `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` | same |
| frozen manifest self-hash | `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93` | same |
| development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` | same, §2 |
| cost proxy | 26 bp round trip (`0.0026`) | `stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §1 |
| primary opportunity floor | 150 non-overlapping events | same, §1; `CANDIDATE_B_SPEC.md` §0.1 |
| planning reference | 349 independent observations | same |

**Verified fact:** the 26 bp figure is a Binance spot proxy for fees plus adverse execution. It is
**not** a measured Nobitex execution cost (`CANDIDATE_B_SPEC.md` §0.1 and §10.2;
`CANDIDATE_D_SPEC.md` §0.1; `SHARED_CENSUS_PROTOCOL.md` §1; `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md`
§4).

**Verified fact:** the 150 floor was introduced at the Stage 2C freeze with no statistical
derivation. The 349 figure is an independence-based planning reference for a `0.15R` effect at 1R
outcome standard deviation, 5% two-sided significance, and 80% power. Neither is a universal
standard (`CANDIDATE_B_SPEC.md` §11.3; `CANDIDATE_D_SPEC.md` §12.2;
`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0).

---

## 2. The framework as it actually exists

The historical framework was not a single written governance protocol. It was a sequence of stage
decisions, frozen specifications, pre-registered analysis plans, and census reports. Its operative
elements can be reconstructed as follows.

### 2.1 Stage lineage

| stage | artifact family | recorded outcome |
|---|---|---|
| 2A | `STAGE2A_FEASIBILITY_CENSUS.md`, `stage2a_census/` | Candidate C failed |
| 2B | `STAGE2B_STRATEGY_DISCOVERY.md`, `STAGE2B_STRATEGY_RECOMMENDATION.md` | four hypotheses designed; Candidate A selected for census |
| 2C | `STAGE2C_FEASIBILITY_CENSUS.md`, `stage2c_census/` | Candidate A failed |
| 2D | `STAGE2D_STRATEGY_REDESIGN.md`, `STAGE2D_STRATEGY_RECOMMENDATION.md` | Candidates B and D recommended |
| 2E v1 | `STAGE2E_*` specifications, protocol, manifest | freeze only |
| 2F | `STAGE2F_INDEPENDENT_FREEZE_AUDIT.md` | v1 freeze failed on four critical defects |
| 2G | `stage2e_v2/*`, `REMEDIATION_MATRIX.md`, `INDEPENDENT_REVIEW.md` | remediation; self-review |
| 2H | `STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md` | conditional pass; self-audit limitation disclosed |
| 2I | `stage2i/*` | readiness and owner ratification of K0–K4 |
| 2J | `stage2j/*`, `stage2j_census/` | Candidates B and D failed |
| 2K | `stage2k/*` | recommended stopping the current family under the current framework |
| 2L | `stage2l/*` | self-review of Stage 2J implementation; independence not established |

**Verified fact:** the lineage and outcomes are recorded in
`docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §1.2.

### 2.2 Operating sequence used for Candidates B and D

1. **Hypothesis design and selection** (Stage 2D).
2. **Frozen specification** with named parameters, entry, stop, cost gate, and verdict table
   (Stage 2E v2).
3. **Remediation and freeze audit** (Stage 2F–2H), with the audit limitation disclosed.
4. **Readiness and owner ratification of open implementation choices** (Stage 2I).
5. **Pre-registered analysis plan** before counting (Stage 2J).
6. **Feasibility census**: count opportunities, apply cost gate, deduplicate, apply non-overlap,
   report diagnostics, and issue a verdict.
7. **Historical review and stop recommendation** (Stage 2K).
8. **Technical audit of the census implementation** (Stage 2L), with independence not established.

**Interpretation:** this is a recognizable research pipeline, but it is missing three elements that a
defensible governance framework requires: an owner-declared economic objective, a dependence-aware
sufficiency rule derived from that objective, and an arms-length implementation audit.

### 2.3 The operative decision rule

For Stage 2J, a candidate failed if any of the following held
(`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §7.2):

- `N_nonoverlap < 150`;
- `M_all > 0.20` (pre-gate median `cost_R`);
- any cost-feasible signal had `notional_pct > 1.00`.

A separate, pre-registered descriptive concentration criterion could add
`FEASIBILITY FAIL — EXCESSIVE CONCENTRATION` when the largest non-empty 4h regime cluster held more
than 50% of the primary population, or the Kish design effect was at least 2.00
(`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §7.3).

**Verified fact:** the concentration FAIL term is a Stage 2J extension, not a term in the frozen
specification's own verdict table (`docs/research/stage2l/TECHNICAL_FINDINGS.md` L-002).

**Verified fact:** the capital-geometry verdict condition was evaluated on the cost-feasible
population under pre-registered interpretation C-1, while the frozen wording says "any signal"
(`docs/research/stage2l/TECHNICAL_FINDINGS.md` L-001).

---

## 3. What the framework has established

### 3.1 The central verified result

**Verified fact:** four frozen designs were censused once each on the same development interval, and
none reached its applicable opportunity gate
(`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §1.1):

| candidate | canonical opportunities | gate | recorded result |
|---|---:|---:|---|
| A — multi-timeframe trend pullback | 71 | 150 | fail |
| B — expansion and retest | 24 | 150 | `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` |
| C — compression breakout | 12 | 200 (Stage 2A gate) | fail |
| D — session momentum | 34 | 150 | `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` |

**Verified fact:** no candidate in Stages 2A–2J was ever performance-tested. No artifact contains a
trade outcome, P&L, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR, equity curve, bootstrap
interval, or Monte Carlo result (`HISTORICAL_RESEARCH_SYNTHESIS.md` §0, §9.1).

### 3.2 What the record demonstrates

The record demonstrates all of the following:

1. **The frozen conjunctions produced few opportunities on this interval.** The counts are
   reproducible structural counts, not profitability estimates.
2. **The loss points differ by candidate.** A and B were throttled mainly by the 4h regime
   conjunction; C by the duration floor; D by the cost gate and stop geometry
   (`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §8.1, §9.1).
3. **The 150 floor is not statistically derived.** It was first fixed at Stage 2C; Stage 2A used
   200; the two are not interchangeable (`HISTORICAL_RESEARCH_SYNTHESIS.md` §3, §9.6–§9.7).
4. **The 349 reference is not a requirement.** It assumes independent observations at a `0.15R`
   effect and is optimistic under clustering and fat tails
   (`SHARED_CENSUS_PROTOCOL.md` §7.3; `STAGE2K_FINAL_RECOMMENDATION.md` §1.2).
5. **Non-overlap is a construction rule, not an independence claim.** The reports state this
   explicitly (`SHARED_CENSUS_PROTOCOL.md` §3.1; `stage2j/CANDIDATE_COMPARISON.md` §7).
6. **The cluster diagnostics are descriptive.** Kish effective sample size is a concentration
   diagnostic, not a serial-dependence estimator (`SHARED_CENSUS_PROTOCOL.md` §3.1;
   `FAILURE_MODE_ANALYSIS.md` §6.3–§6.5).
7. **The 26 bp cost is unverified for the execution venue.**
8. **The Stage 2H freeze audit and the Stage 2L implementation audit were both self-reviews.**
   Stage 2I accepted Stage 2H as the audit of record with that limitation explicit
   (`stage2i/OWNER_RATIFICATION.md` §1); Stage 2L's primary verdict is
   `SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`
   (`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1).

### 3.3 What the record does not demonstrate

The record does **not** demonstrate:

- that any candidate is unprofitable;
- that any candidate has no edge;
- that BTC lacks these opportunities in general;
- that the 26 bp cost is wrong, or that Nobitex is cheaper or more expensive;
- that 150 is the right or wrong number;
- that 349 is a requirement;
- that `0.15R` is the correct minimum economic effect;
- that the strategy family is invalid;
- that a different venue, timeframe, or filter would pass;
- that the Stage 2J implementation is correct in every respect.

**Verified fact:** these limitations are stated in
`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §5 and
`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §4.

---

## 4. What remains unresolved

The unresolved items below are the inputs to Stage 2M. Each is stated as a gap, with the evidence
that establishes it, the reason it matters, and the Stage 2M treatment. None is resolved silently.

### G-01 — No owner-declared economic objective

**Current state:** the project has used opportunity counts, a cost gate, and a `0.15R` design
assumption, but has never declared the minimum net economic effect that would make further research
worthwhile, the acceptable risk, or the capital context in which the effect would be earned.

**Evidence:** `CANDIDATE_B_SPEC.md` §0.1 and §11.3; `CANDIDATE_D_SPEC.md` §0.1 and §12.2;
`FAILURE_MODE_ANALYSIS.md` §7.3 and §8.3; `STAGE2K_FINAL_RECOMMENDATION.md` §7 (U4).

**Why it matters:** without an economic objective, a "feasibility pass" only says that a design
produced enough countable events. It does not say that the events could produce a return worth
having, or that a statistically detectable effect would be economically useful.

**Stage 2M treatment:** `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` presents estimand options,
minimum-effect options, risk options, and an owner-decision structure. It does not choose the
numbers.

### G-02 — No frozen primary performance estimand

**Current state:** the censuses count opportunities. They do not define the quantity a future
performance experiment would estimate. Gross return, net return, net return per opportunity, net
return per executed trade, opportunity frequency, capital utilization, risk-adjusted performance,
tail outcomes, and stability are not interchangeable.

**Evidence:** `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0; `HISTORICAL_RESEARCH_SYNTHESIS.md`
§9.1.

**Why it matters:** a decision rule that does not name its estimand cannot be pre-registered
coherently, and a result that is significant on one metric may be irrelevant on another.

**Stage 2M treatment:** `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §2–§4 proposes a primary and
secondary metric structure and explains the trade-offs.

### G-03 — Execution cost is an unverified proxy

**Current state:** all historical censuses use a 26 bp round-trip Binance proxy. No repository
artifact contains a Nobitex fee schedule, measured spread distribution, market-impact estimate,
slippage measurement, depth record, fill-rate observation, latency measurement, or venue outage
record.

**Evidence:** `CANDIDATE_B_SPEC.md` §0.1 and §10.2; `CANDIDATE_D_SPEC.md` §0.1;
`SHARED_CENSUS_PROTOCOL.md` §1 and §7; `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §4;
`STAGE2K_FINAL_RECOMMENDATION.md` §7 (U1).

**Why it matters:** cost is not a constant of nature. It depends on venue, order type, size, spread,
depth, latency, and fill quality. A proxy can be wrong in either direction. A strategy that passes
only under an optimistic cost is not admissible.

**Stage 2M treatment:** `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §7–§9 defines the cost
components, the evidence standard, the venue-specific requirements, and the cost-uncertainty rule.

### G-04 — The sufficiency rule is underived and internally inconsistent

**Current state:** the 150 floor is a project choice with no statistical derivation. The 349 figure
is an independence-based planning reference. Under the record's own assumptions, 150 is sufficient
only for an effect near `0.23R`, not the stated `0.15R`.

**Evidence:** `FAILURE_MODE_ANALYSIS.md` §7.3; `CANDIDATE_B_SPEC.md` §11.3;
`CANDIDATE_D_SPEC.md` §12.2; `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0.

**Why it matters:** a candidate could pass the floor and still be unable to detect the effect the
project says it cares about. A universal count threshold cannot encode effect size, variance,
dependence, opportunity definition, and practical frequency.

**Stage 2M treatment:** `STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3–§5 defines a derived,
dependence-aware sufficiency methodology and explains why a universal count is insufficient.

### G-05 — Dependence is diagnosed but not modeled

**Current state:** the census reports maximal 4h regime runs, largest-cluster shares, Kish effective
sample size, design effects, and `rho` sensitivities. These are descriptive. No inferential
procedure for dependence is pre-registered, and non-overlapping observations are explicitly not
described as independent.

**Evidence:** `SHARED_CENSUS_PROTOCOL.md` §3.1; `stage2j/CANDIDATE_COMPARISON.md` §7;
`FAILURE_MODE_ANALYSIS.md` §6.3–§6.5; `HISTORICAL_RESEARCH_SYNTHESIS.md` §9.11.

**Why it matters:** opportunity counts, confidence intervals, and power calculations are all
sensitive to dependence. A count that ignores dependence can overstate the evidence by a large
factor.

**Stage 2M treatment:** `STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3 evaluates clustering, temporal
dependence, block bootstrap, cluster-robust inference, effective-sample diagnostics, and
cluster-definition sensitivity, with their assumptions and limits.

### G-06 — The feasibility gate is not connected to the economic objective

**Current state:** the feasibility gate asks whether a candidate produces at least 150
non-overlapping, cost-feasible opportunities. It does not connect opportunity frequency to the
owner's economic objective, capital utilization, or a derived sample requirement.

**Evidence:** `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0 and §7.2;
`FAILURE_MODE_ANALYSIS.md` §7.3–§7.4.

**Why it matters:** frequency is necessary but not sufficient. A dense strategy with a tiny edge can
fail economically; a sparse strategy with a large edge can be untestable. The gate must reflect the
decision the project is actually trying to make.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` Gate 3 and
`STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §5 define a feasibility gate that connects frequency, cost,
dependence, and the approved economic objective.

### G-07 — Independent verification has not been established

**Current state:** Stage 2H was a self-audit. Stage 2L was a self-review with the primary verdict
`SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`. No arms-length audit of the Stage 2J census
implementation exists.

**Evidence:** `stage2i/OWNER_RATIFICATION.md` §1; `stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md` §6;
`stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1.

**Why it matters:** passing tests and verifying hashes are not equivalent to independent
verification. A self-review can find concrete defects, but it cannot supply the adversarial distance
that independence is meant to provide.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` §7 and §11 define an independent-audit
policy, including practical alternatives and what each can and cannot establish. Stage 2L is
explicitly treated as insufficient for a future Gate 4.

### G-08 — Data representativeness is unresolved

**Current state:** the development interval is a single 1,277-day path from 2021-01-01 to
2024-07-01. It covers a bull phase, a bear phase, and a recovery, but it is one realized history. No
regime-coverage standard, structural-break analysis, or later-period evidence exists. The dataset
has seven registered gaps, 31 zero-volume 5m placeholders, and twelve gap-adjacent 4h buckets handled
under the M3 exemption.

**Evidence:** `HISTORICAL_RESEARCH_SYNTHESIS.md` §9.5, §9.10;
`stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md` §3–§5; `STAGE2K_FINAL_RECOMMENDATION.md` §7 (U6, U8).

**Why it matters:** a result estimated on one market path may not generalize. Extrapolation to
future conditions requires evidence about regime coverage, stability, and structural change, not
just a positive in-sample result.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` §12 defines a representativeness framework
for future research. No market data is accessed in Stage 2M.

### G-09 — Multiple-testing and candidate-selection governance is weak

**Current state:** four candidates were designed and censused, the opportunity floor changed from
200 to 150 between stages, and candidate selection was frequency-first. No formal multiplicity
control, alpha-spending, or selection-adjusted inference was pre-registered.

**Evidence:** `HISTORICAL_RESEARCH_SYNTHESIS.md` §3 and §9.6–§9.7;
`FAILURE_MODE_ANALYSIS.md` §7.4; `STAGE2K_FINAL_RECOMMENDATION.md` §1.4.

**Why it matters:** sequential candidate design and threshold changes inflate the chance of a false
positive and make a later "pass" difficult to interpret. A governance protocol must pre-declare the
testing family and the reporting of all attempts.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` Gate 2 and Gate 5, and
`STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §6.

### G-10 — Execution and capital realism are incomplete

**Current state:** the historical capital geometry assumes `$10,000` equity, 1% risk (`$100`), one
position, spot long-only, no leverage, and next-bar-open entry. It contains no order-book model,
fill model, partial-fill handling, or latency model. For Candidate D, 208 of 295 pre-gate signals
had `notional_pct > 1.00`; the verdict population was narrowed to the cost-feasible set under C-1.

**Evidence:** `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6;
`stage2l/TECHNICAL_FINDINGS.md` L-001; `FAILURE_MODE_ANALYSIS.md` §8.2.

**Why it matters:** a strategy can be statistically detectable and economically unusable if the
required position size exceeds available capital or liquidity. Capital geometry and execution
feasibility must be part of the economic objective, not an afterthought.

**Stage 2M treatment:** `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §4 and §5;
`RESEARCH_GOVERNANCE_PROTOCOL.md` Gate 1 and Gate 3.

### G-11 — Reproducibility evidence is incomplete

**Current state:** Stage 2J records a determinism claim, but no second-run artifacts or digests were
retained. The recorded code identity omits `freeze_verify.py` and test files.

**Evidence:** `stage2l/TECHNICAL_FINDINGS.md` L-009 and L-010;
`stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §7.

**Why it matters:** reproducibility is part of the evidence standard. A claim that cannot be
checked from retained artifacts is weaker than a claim supported by them.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` Gate 4 and §14 define
evidence-preservation requirements. Stage 2M does not repair the historical record.

### G-12 — Labels and thresholds drifted across stages

**Current state:** the labels A, B, C, and D denote different objects at different stages. The
opportunity floor changed from 200 (Stage 2A) to 150 (Stage 2C onward). Several specification
tensions were resolved by pre-registered interpretation rather than by freezing unambiguous text.

**Evidence:** `HISTORICAL_RESEARCH_SYNTHESIS.md` §2 and §3;
`stage2l/TECHNICAL_FINDINGS.md` L-001–L-006.

**Why it matters:** cross-stage statements that omit the stage name are uninterpretable. A future
framework should use versioned names, explicit populations, and unambiguous verdict tables.

**Stage 2M treatment:** `RESEARCH_GOVERNANCE_PROTOCOL.md` §10 (freeze policy) and Gate 2.

### G-13 — No outcome evidence exists

**Current state:** every historical verdict is a structural feasibility verdict. No trade was
entered or resolved; no outcome was observed.

**Evidence:** `HISTORICAL_RESEARCH_SYNTHESIS.md` §9.1; `STAGE2K_FINAL_RECOMMENDATION.md` §1.5.

**Why it matters:** the project cannot yet distinguish a market problem from a framework problem.
Stage 2M cannot resolve that distinction; it can only design the process that would.

**Stage 2M treatment:** the entire framework is designed to make a future outcome experiment
interpretable if and only if the owner authorizes it. Stage 2M does not run one.

---

## 5. How Stage 2K and Stage 2L affect the next research decision

### 5.1 Stage 2K

**Verified fact:** Stage 2K recommends stopping the current strategy family under the current
framework. It does not recommend proceeding to an outcome study on A, B, C, or D; it recommends
repairing the framework first if the owner wants to preserve the option of later testing
(`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §0).

**Verified fact:** Stage 2K identifies the conditional path as: declare the minimum economic effect;
measure the venue cost; derive the sufficiency rule; re-freeze the framework; audit it; only then
consider a candidate (`STAGE2K_FINAL_RECOMMENDATION.md` §3.1).

**Interpretation:** Stage 2M is the design phase of that conditional path. It addresses the
framework repair, not candidate selection.

### 5.2 Stage 2L

**Verified fact:** Stage 2L verified substantial artifact integrity, traced the frozen B and D
specifications into the implementation, and passed 98 synthetic checks. It found zero
CRITICAL and zero MAJOR defects, six MINOR findings, and four OBSERVATION items
(`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1–§3).

**Verified fact:** Stage 2L's primary verdict is
`SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`. The auditor participated in prior Stage 2J work and
therefore cannot be treated as an arms-length auditor
(`docs/research/stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md` §6).

**Interpretation:** Stage 2L is useful evidence about the implementation, but it is not a substitute
for independent verification. A future Gate 4 must be performed by a party with no prior
implementation involvement. Stage 2L's findings remain open and are not repaired by Stage 2M.

### 5.3 Combined effect

The two stages together establish a clear boundary:

- the historical record is preserved and its structural verdicts stand;
- the current strategy family is stopped under the current framework;
- the framework has known defects in economic objective, cost evidence, sufficiency, dependence,
  representativeness, and independent verification;
- no new candidate or experiment is authorized;
- the next defensible action is a framework decision by the owner, not another count.

Stage 2M therefore proposes governance and methodology. It does not reopen candidate selection and
does not use Stage 2L to argue that the Stage 2J verdicts were wrong.

---

## 6. Gap-to-treatment matrix

| gap | current state | why it blocks a defensible experiment | Stage 2M treatment | classification |
|---|---|---|---|---|
| G-01 economic objective | no owner-declared minimum effect or risk limit | a pass/fail rule cannot be derived without it | economic framework and decision register | **essential** |
| G-02 primary estimand | counts only; no outcome metric | results would not answer a decision question | estimand hierarchy | **essential** |
| G-03 cost evidence | 26 bp Binance proxy | cost can determine feasibility and conclusions | component-by-component cost study design | **essential** |
| G-04 sufficiency | underived 150; independence-based 349 | a count can be met while the effect is undetectable | derived, dependence-aware method | **essential** |
| G-05 dependence | descriptive diagnostics only | uncertainty and power are understated | dependence model and sensitivity policy | **essential** |
| G-06 feasibility gate | frequency-only | does not connect to economics or capital | Gate 3 redesign | **essential** |
| G-07 independent audit | self-review | implementation correctness is not arms-length verified | audit policy and alternatives | **essential** |
| G-08 representativeness | one 1,277-day path | extrapolation is unsupported | representativeness framework | important, partly deferrable |
| G-09 multiplicity | no formal control | false-positive risk across candidates/variants | pre-registration and multiplicity policy | **essential** before a multi-candidate programme |
| G-10 capital/execution | simple geometry; no fill model | a signal may be unfundable or unfillable | economic context and cost/execution design | **essential** at Gate 1 |
| G-11 reproducibility | no retained second-run artifacts | determinism claim is not checkable | evidence-preservation rules | important |
| G-12 label/threshold drift | stage-dependent labels and 200/150 | cross-stage claims are ambiguous | versioned freeze policy | important |
| G-13 no outcome evidence | all verdicts structural | market vs framework cause unresolved | framework design; no experiment in 2M | contextual |

**Interpretation:** the essential gaps are not independent. G-01 and G-02 determine what G-04 can
mean; G-03 and G-10 determine whether a candidate is executable; G-05 determines how much evidence
G-04 requires; G-07 determines whether any of it can be trusted. A framework that fixes only one of
them would repeat the historical pattern of a superficially rigorous process with an unresolved
foundation.

---

## 7. Resource and practical constraints

**Verified fact:** the Stage 2J census ran with a peak RSS of 551.793 MiB, against a 4 GiB target and
a 6 GiB hard ceiling, and completed in 99.137 seconds
(`stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §3).

**Proposal:** every Stage 2M requirement is classified as **essential**, **important but
deferrable**, or **optional** in `STAGE2M_FINAL_PROPOSAL.md` §4. The classification respects the
following constraints:

- 4 GiB RAM target and 6 GiB hard ceiling;
- limited development hardware;
- financial constraints;
- limited ability to obtain professional execution infrastructure;
- existing repository and historical artifacts;
- no dependency installation, Docker, or application services in Stage 2M.

The framework deliberately avoids requirements that need large simulations, full order-book
reconstruction, or professional market-data subscriptions before the owner has approved the
objective. Those can be added later if the owner authorizes them.

---

## 8. What Stage 2M does not change

Stage 2M records the following positions without reinterpretation:

1. Candidates A, B, C, and D retain their historical results and verdicts.
2. Stage 2K's decision to stop the current strategy family under the existing framework remains in
   force.
3. Stage 2J's census results remain historical evidence, not proof of profitability or
   unprofitability.
4. Stage 2L's verdict remains `SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`.
5. No new candidate is authorized.
6. No Stage 2N or subsequent implementation stage is authorized.

No historical artifact, application file, frozen specification, dataset, threshold, or verdict was
modified in the preparation of this document.

---

## 9. Summary

The current framework is a disciplined counting pipeline with an underived decision rule. It has
established that four frozen designs produced too few opportunities on one development interval. It
has not established whether any design has an edge, whether the execution cost assumption is
realistic, whether the opportunity requirement is economically meaningful, whether the observations
are sufficiently independent, or whether the implementation has been independently verified.

Stage 2M addresses the framework, not the market. Its central conclusion is that the next research
decision is an owner decision about economic objective, risk, cost evidence, statistical
sufficiency, and audit standard — not another candidate count.
