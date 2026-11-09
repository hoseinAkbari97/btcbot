# Stage 2M — Final Proposal

**Stage:** 2M (research-governance and methodology design only)
**Status:** proposal. No experiment, candidate, or data access is authorized.
**Date:** 2026-11-09 (UTC)

**Repository baseline at review start:** `main` /
`93152bd21893b63422f113d977b677f8386889b2`, clean and synchronized with `origin/main`.

**Evidence labels:** **Verified fact**, **Interpretation**, **Proposal**, **Owner decision**.

---

## 0. The proposal in one page

Stage 2M proposes a seven-gate research framework:

1. **Gate 0 — Economic objective.** The owner declares the minimum meaningful effect, the risk
   limits, the capital and execution context, and the primary estimand.
2. **Gate 1 — Data and venue validity.** Dataset provenance, gaps, alignment, and a venue-specific
   cost study are documented and frozen.
3. **Gate 2 — Hypothesis registration.** The hypothesis, rules, metrics, statistical methods,
   sample-sufficiency calculation, and failure criteria are frozen before outcomes.
4. **Gate 3 — Feasibility.** The hypothesis must produce enough cost-feasible, dependence-aware
   opportunities to meet the derived requirement, with capital and liquidity constraints checked.
5. **Gate 4 — Independent implementation verification.** A party with no prior involvement audits
   the specification-to-code trace, synthetic tests, temporal correctness, alignment, and
   reproducibility.
6. **Gate 5 — Controlled performance evaluation.** Development, validation, and OOS data are
   chronologically separated; costs, dependence, multiple testing, robustness, drawdown, and tail
   risk are pre-registered and reported.
7. **Gate 6 — Final research decision.** Reject, inconclusive, continue, advance to paper trading, or
   abandon — each with explicit conditions and separate owner authorization.

The framework is designed to answer the question the historical programme left open: **is there a
net economic effect large enough to justify the cost, risk, and capital, and is the evidence strong
enough to believe it?**

It does not answer that question. It creates the conditions under which a future, separately
authorized experiment could.

---

## 1. What Stage 2M is responding to

### 1.1 The historical result

**Verified fact:** four frozen designs were censused once each on `[2021-01-01, 2024-07-01)` and none
reached its applicable opportunity gate: A 71, B 24, C 12, D 34
(`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §1.1;
`docs/research/stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §1).

**Verified fact:** no candidate was ever performance-tested. No P&L, expectancy, win rate, drawdown,
Sharpe, Sortino, CAGR, equity curve, bootstrap, or Monte Carlo result exists in the record
(`docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §0, §9.1).

**Verified fact:** Stage 2K recommended stopping the current strategy family under the current
framework and repairing the framework first
(`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §0).

**Verified fact:** Stage 2L audited the Stage 2J implementation, found no CRITICAL or MAJOR defects,
passed 98 synthetic checks, but could not establish independence; its primary verdict is
`SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`
(`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1).

### 1.2 The framework defects

Stage 2M identifies the following defects in the current framework:

| defect | evidence | consequence |
|---|---|---|
| no owner-declared economic objective | `FAILURE_MODE_ANALYSIS.md` §7.3, §8.3; `STAGE2K_FINAL_RECOMMENDATION.md` §7 U4 | a count cannot be interpreted as economic feasibility |
| no frozen primary estimand | `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0 | the experiment has no clear decision metric |
| unverified execution cost | `CANDIDATE_B_SPEC.md` §0.1; `STAGE2J_SUMMARY_AND_VERDICT.md` §4 | the cost gate may be wrong in either direction |
| underived and inconsistent sufficiency | `FAILURE_MODE_ANALYSIS.md` §7.3 | 150 is sufficient only for about `0.23R`, not `0.15R` |
| dependence is diagnosed but not modeled | `SHARED_CENSUS_PROTOCOL.md` §3.1; `CANDIDATE_COMPARISON.md` §7 | uncertainty and power are understated |
| feasibility gate is frequency-only | `PRE_REGISTERED_ANALYSIS_PLAN.md` §7.2 | frequency is not connected to economics or capital |
| no independent audit | `stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md` §6; `stage2i/OWNER_RATIFICATION.md` §1 | implementation correctness is self-assessed |
| representativeness unresolved | `HISTORICAL_RESEARCH_SYNTHESIS.md` §9.5 | one 1,277-day path cannot support extrapolation |
| multiplicity and selection risk | `HISTORICAL_RESEARCH_SYNTHESIS.md` §3; `FAILURE_MODE_ANALYSIS.md` §7.4 | sequential candidates and threshold drift inflate false positives |
| reproducibility gaps | `stage2l/TECHNICAL_FINDINGS.md` L-009, L-010 | determinism and code identity are not fully evidenced |

The full analysis is in `CURRENT_FRAMEWORK_GAP_ANALYSIS.md`.

---

## 2. The proposed framework

### 2.1 Economic objective

**Proposal:** the primary statistical estimand is **net return per executed trade in R**, after
all-in execution costs, with a frozen exit and holding policy. The co-primary decision metric is
**net annual contribution** (or net annual return) at the owner's declared capital and risk policy.
Secondary metrics include net expectancy per opportunity, opportunity frequency, capital utilization,
maximum drawdown, worst trade, CVaR/expected shortfall, maximum adverse excursion, time under water,
and performance stability.

**Why this structure:**

- R is the risk unit already used by the historical specifications and is scale-free across
  volatility.
- The annual metric captures frequency, capital utilization, and the owner's actual objective.
- Tail and drawdown metrics prevent a positive average from hiding an unacceptable path.
- Stability metrics prevent a single regime from dominating the conclusion.

**Owner decisions:** D-01 (MME), D-02 (risk), D-03 (estimand), D-04 (capital), D-07 (annual
contribution). The framework does not choose the numbers.

### 2.2 Cost framework

**Proposal:** replace the single 26 bp proxy with a component model:

- trading fees (maker/taker, tier, effective dates);
- bid-ask spread (at the strategy's decision times, by session and volatility);
- market impact (order size relative to depth);
- slippage (decision/arrival price versus fill);
- order type and execution assumptions (market, limit, IOC/FOK, stop);
- liquidity and depth (minimum notional, lot size, visible size);
- partial fills and rejections;
- latency and market movement;
- entry/exit asymmetry;
- venue operational restrictions.

The primary verdict uses a **conservative** all-in cost estimate (a pre-specified upper percentile or
upper bound of the measured distribution). A candidate that passes only under an optimistic scenario
is not admissible. The 26 bp proxy may be used for research comparability but not as a verified
Nobitex cost.

**Owner decisions:** D-05 (venue and evidence standard), D-06 (cost-uncertainty rule).

### 2.3 Statistical sufficiency

**Proposal:** derive the sample requirement from the owner's objective:

1. declare the MME `δ`, the error-control objective, and the outcome variance `σ²`;
2. choose the estimator and the primary dependence model;
3. compute the independent-observation requirement
   `N_ind ≈ (z_{1-α/2} + z_{1-β})² σ² / δ²` (or the precision analogue);
4. inflate for dependence: `N_obs ≈ N_ind × DE`;
5. convert to opportunities: `required_opportunities ≈ N_obs / p_exec`;
6. compare with the expected opportunity frequency and calendar ceiling;
7. freeze the calculation before the outcome experiment.

Use an interval-based decision rule: the lower bound of the primary estimate must meet the MME, and
the risk limits must hold. An interval that includes the MME or zero is **inconclusive**. Non-overlap
is not independence; Kish is a concentration diagnostic, not a serial-dependence estimator; no single
technique solves dependence.

**Owner decisions:** D-08 (error control), D-09 (dependence), D-10 (sufficiency methodology).

### 2.4 Feasibility gate

**Proposal:** Gate 3 compares the dependence-adjusted, cost-feasible opportunity count with the
derived `required_opportunities`, using an interval:

- if the upper bound is below the requirement, stop or redesign;
- if the lower bound is at or above the requirement and capital/liquidity pass, proceed to Gate 4;
- if the interval spans the requirement, collect more feasibility evidence or redesign;
- if capital or liquidity fails, stop or redesign.

The gate is not a universal count. It is derived from the owner's objective, the cost model, the
dependence model, and the execution rate.

### 2.5 Independent audit

**Proposal:** Gate 4 is an audit by a party with no prior involvement in the design, implementation,
or reporting of the artifact. The auditor has access to the frozen specification, code, tests, data
manifest, and outputs; performs a specification-to-code trace, synthetic tests, temporal and alignment
checks, and reproducibility checks; classifies findings as CRITICAL, MAJOR, MINOR, or OBSERVATION;
and signs an independence statement.

Stage 2L is a useful technical record but **cannot** serve as Gate 4 evidence. A different model or a
new conversation is not, by itself, independence.

**Owner decision:** D-13 (audit standard).

### 2.6 Controlled evaluation

**Proposal:** Gate 5 separates development, validation, and OOS data chronologically, with an embargo
or purge between blocks. Validation and OOS are one-look. Parameter selection is confined to
development. Multiple testing is pre-registered. Costs, dependence, robustness, drawdown, and tail
risk are reported. The report includes the full funnel, the primary interval, the MME comparison, all
secondary metrics, all deviations, and the audit findings.

### 2.7 Final decision

**Proposal:** Gate 6 maps the evidence to one of: reject, inconclusive, continue research, advance to
paper trading, or abandon the direction. No outcome automatically authorizes the next stage. Each
requires separate owner authorization.

---

## 3. Most important unresolved decisions

The framework cannot proceed to a defensible experiment until the owner resolves the following. The
full register is in `OWNER_DECISION_REGISTER.md`.

| rank | decision | why it is critical |
|---|---|---|
| 1 | **D-01 minimum meaningful effect** | defines what "worth doing" means and drives the sample requirement |
| 2 | **D-02 acceptable risk** | a positive average can still be unacceptable |
| 3 | **D-03 primary estimand** | determines what the experiment is allowed to conclude |
| 4 | **D-04 capital and execution context** | determines position size, fundability, and annual contribution |
| 5 | **D-05 venue and cost evidence** | the 26 bp proxy is not a Nobitex measurement |
| 6 | **D-13 independent audit standard** | Stage 2L cannot supply independence |
| 7 | **D-07 annual contribution** | prevents a sparse rule from passing on per-trade edge alone |
| 8 | **D-08–D-12 statistical policy** | determines the sample, uncertainty, and multiplicity treatment |
| 9 | **D-14 representativeness** | determines whether a result can be extrapolated |
| 10 | **D-15 next candidate** | must not be answered before the framework is repaired |

**Interpretation:** the first six decisions are the minimum package. D-08–D-12 can be resolved during
pre-registration; D-14 during Gate 1/5; D-15 only after the framework is repaired and audited.

---

## 4. Essential, deferrable, and optional requirements

### 4.1 Essential before any future experiment

| requirement | why essential | practical cost |
|---|---|---|
| Owner decisions D-01–D-07 and D-13 | without them, the experiment has no objective, risk limit, capital context, or credible audit | owner time |
| Venue-specific cost study | the cost basis can determine feasibility | medium–high: external data/account access |
| Data provenance and alignment | a result on unverified data is not evidence | low–medium: hashing and audit |
| Frozen pre-registration | prevents post-hoc fitting | low–medium: writing and review |
| Derived sample-sufficiency calculation | a count threshold is not a sufficiency rule | low–medium: analytical work |
| Development/validation/OOS separation | prevents leakage and selection bias | low: planning and access control |
| Independent audit plan | a self-review is not independent verification | medium: reviewer time |

### 4.2 Important but deferrable

| requirement | why deferrable | practical cost |
|---|---|---|
| Full regime taxonomy and coverage analysis | can be completed at Gate 5, before extrapolation | medium |
| Advanced dependence models (block bootstrap, wild cluster bootstrap) | start with analytic approximations; add if the decision is sensitive | medium |
| Full order-book reconstruction | needed for execution realism, but can follow a simpler top-of-book study | high: data and compute |
| Multi-venue cost comparison | useful, but the primary venue can be studied first | high: data and access |
| Automated access logging | can be manual at first, with a documented log | low–medium |
| Extended OOS confirmation | can be a later stage after validation | medium |

### 4.3 Optional improvements

| requirement | why optional | practical cost |
|---|---|---|
| External professional audit | stronger than a separate reviewer, but may be unavailable or expensive | high |
| Bayesian decision-theoretic framework | more complete, but requires a prior and loss function | medium–high |
| Certainty-equivalent utility objective | theoretically appealing, but hard to specify | medium |
| Multi-instrument or cross-sectional extension | out of scope for the current project | high |
| High-frequency or order-book-level backtest | may exceed the 4 GiB/6 GiB resource target | high |

### 4.4 Resource discipline

**Proposal:** keep the existing discipline:

- 4 GiB RAM target, 6 GiB hard ceiling;
- no dataset loading in design stages;
- no Docker or application services for research design;
- no dependency installation without authorization;
- prefer analytical approximations and small pre-registered simulations over large Monte Carlo
  studies;
- store aggregates and manifests, not raw data copies.

**Verified fact:** the Stage 2J census achieved 551.793 MiB peak RSS and 99.137 seconds wall time,
well within the resource constraints (`stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §3). The
governance framework should preserve that efficiency.

---

## 5. Recommended next decision

**Proposal:** the owner should:

1. **Complete the minimum decision package:** D-01, D-02, D-03, D-04, D-05, D-06, D-07, and D-13.
2. **Authorize a venue-specific cost study** as a separate, read-only research stage. The study
   should collect dated fee evidence, spread and depth at the strategy's decision times, fill and
   slippage evidence, latency, and operational constraints. It should not run a strategy or observe
   outcomes.
3. **Authorize a framework freeze** that incorporates the owner's decisions and the cost study into
   a new versioned protocol.
4. **Commission an independent audit** of the framework and, later, of any implementation.
5. **Do not authorize a candidate** until Gates 0–4 are complete and the owner has separately
   approved the hypothesis.

**Interpretation:** this order follows the Stage 2K conditional path
(`STAGE2K_FINAL_RECOMMENDATION.md` §3.1): declare the effect, measure the cost, derive the rule,
re-freeze, audit, and only then consider a candidate.

**What this recommendation does not do:** it does not select a candidate, does not reopen the Stage 2J
verdicts, does not lower the historical thresholds, and does not authorize a backtest.

---

## 6. What would change the recommendation

**Proposal:** the framework should be reconsidered if any of the following occurs:

| event | effect |
|---|---|
| the owner declares an MME so large that no plausible design can meet it | the correct conclusion may be to abandon the direction, not to lower the requirement |
| the venue cost study shows a much higher all-in cost | the feasible opportunity set shrinks; some candidates may become permanently untestable |
| the venue cost study shows a much lower cost | the feasible set grows; D's cost-geometry failure may warrant a new, pre-registered look, but not a retroactive verdict change |
| an independent audit finds a CRITICAL or MAJOR defect | the affected result is suspended until remediation and re-audit |
| the owner cannot obtain any independent reviewer | the experiment can proceed only as **provisional**, with the limitation disclosed, and cannot support a live-decision claim |
| the data prove unrepresentative | the framework must require a new period or a new instrument before extrapolation |

**Interpretation:** none of these events is a reason to skip a gate. They are reasons to revisit the
owner's decisions with better evidence.

---

## 7. What Stage 2M does not authorize

Stage 2M explicitly does **not** authorize:

- a new candidate specification;
- a detector run on any data;
- a census or re-count;
- a backtest or performance simulation;
- a bootstrap or Monte Carlo study;
- parameter optimization or tuning;
- access to validation or OOS data;
- application or research implementation changes;
- a change to any historical report, specification, threshold, or verdict;
- Stage 2N or any subsequent stage.

The framework is a proposal. The owner must decide whether to adopt it, modify it, or reject it.

---

## 8. Completion report

### 8.1 Repository state

| item | value |
|---|---|
| branch | `main` |
| HEAD at review start | `93152bd21893b63422f113d977b677f8386889b2` |
| remote tracking | `origin/main`, synchronized |
| working tree before Stage 2M | clean |
| working tree after document creation | only new files under `docs/research/stage2m/` |
| working tree after stage commits | clean (verified after the final commit) |

### 8.2 Stage 2K and Stage 2L manifest verification

| manifest | self-hash recomputed | file hashes recomputed | result |
|---|---|---|---|
| `docs/research/stage2k/FREEZE_MANIFEST.json` | matched | matched | pass |
| `docs/research/stage2l/FREEZE_MANIFEST.json` | matched | matched | pass |

The Stage 2K self-hash and the Stage 2L self-hash were recomputed over the canonical JSON content
excluding the `self_hash` field. All recorded artifact, deliverable, supporting-file, and source
hashes and byte counts matched. The exact values and the hashing procedure are recorded in
`FREEZE_MANIFEST.json`.

### 8.3 Historical artifacts reviewed

Directly reviewed for Stage 2M:

- `docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md`
- `docs/research/stage2k/FAILURE_MODE_ANALYSIS.md`
- `docs/research/stage2k/RESEARCH_DIRECTION_COMPARISON.md`
- `docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md`
- `docs/research/stage2k/FREEZE_MANIFEST.json`
- `docs/research/stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md`
- `docs/research/stage2l/SPECIFICATION_IMPLEMENTATION_TRACE.md` (supporting)
- `docs/research/stage2l/TECHNICAL_FINDINGS.md`
- `docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md`
- `docs/research/stage2l/FREEZE_MANIFEST.json`
- `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md`
- `docs/research/stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md`
- `docs/research/stage2j/STAGE2J_SUMMARY_AND_VERDICT.md`
- `docs/research/stage2j/STAGE2J_FINAL_DECISION.md`
- `docs/research/stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md`
- `docs/research/stage2j/CANDIDATE_B_CENSUS_REPORT.md` (supporting)
- `docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md` (supporting)
- `docs/research/stage2j/CANDIDATE_COMPARISON.md` (supporting)
- `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` (key sections)
- `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` (key sections)
- `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` (key sections)
- `docs/research/stage2e_v2/REMEDIATION_MATRIX.md` (supporting)
- `docs/research/stage2i/OWNER_RATIFICATION.md` (key sections)
- `docs/research/stage2i/CHANGE_PROPOSALS.md` (key sections)
- `docs/research/stage2i/STAGE2I_FINAL_READINESS_DECISION.md` (key sections)

### 8.4 Files created

| file | purpose |
|---|---|
| `docs/research/stage2m/CURRENT_FRAMEWORK_GAP_ANALYSIS.md` | current framework, established facts, unresolved gaps |
| `docs/research/stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` | estimands, MME options, risk, capital, cost model |
| `docs/research/stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` | dependence, sufficiency, uncertainty, multiplicity |
| `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | Gates 0–6, freeze, audit, data separation, representativeness |
| `docs/research/stage2m/OWNER_DECISION_REGISTER.md` | fifteen owner decisions with options and consequences |
| `docs/research/stage2m/STAGE2M_FINAL_PROPOSAL.md` | this document |
| `docs/research/stage2m/FREEZE_MANIFEST.json` | hashes, provenance, confirmations |

### 8.5 Most important framework deficiencies

1. **No owner-declared economic objective or minimum effect.**
2. **No frozen primary performance estimand.**
3. **The execution cost is an unverified proxy.**
4. **The sufficiency rule is underived and inconsistent with the stated effect of interest.**
5. **Dependence is diagnosed but not modeled inferentially.**
6. **The feasibility gate is frequency-only and not connected to economics.**
7. **Independent verification has not been established.**
8. **Data representativeness is unresolved.**
9. **Multiple-testing and selection governance is weak.**
10. **Reproducibility evidence is incomplete.**

### 8.6 Proposed economic objective structure

A primary net-R-per-executed-trade metric, a co-primary annual contribution metric, secondary
frequency/utilization/drawdown/tail/stability metrics, and a conservative venue-specific cost model.
The MME, risk limits, capital context, and annual target are owner decisions.

### 8.7 Proposed statistical sufficiency methodology

A seven-step derivation: MME and error control → estimator and dependence model → `N_ind` → `N_obs`
via design effect → required opportunities via execution rate → comparison with frequency and
calendar → freeze. Decision by a dependence-adjusted interval compared with the MME; non-overlap is
not independence; Kish is descriptive; no single method solves dependence.

### 8.8 Proposed independent-review policy

A party with no prior involvement in design, implementation, or reporting; access to frozen
specifications, code, tests, and outputs; a trace, synthetic tests, temporal and alignment checks, and
reproducibility checks; CRITICAL/MAJOR/MINOR/OBSERVATION classification; remediation and re-audit;
signed independence attestation. Stage 2L is explicitly insufficient for Gate 4. Practical
alternatives are listed with their limits.

### 8.9 Essential owner decisions

D-01 (MME), D-02 (risk), D-03 (estimand), D-04 (capital/execution), D-05 (venue/cost evidence),
D-06 (cost-uncertainty rule), D-07 (annual contribution), D-13 (audit standard). The remaining
decisions can be resolved during pre-registration or later gates.

### 8.10 Primary recommendation

Complete the minimum owner-decision package, authorize a venue-specific cost study, freeze the
framework, and commission an independent audit. Do not authorize a candidate or an experiment until
Gates 0–4 are complete.

### 8.11 Confirmations

| confirmation | status |
|---|---|
| no development, validation, or OOS market-data rows processed | **confirmed** |
| validation/OOS data not accessed or decoded | **confirmed** |
| no census, re-count, detector run, or historical analysis executed | **confirmed** |
| no backtest, P&L, expectancy, drawdown, Sharpe, Sortino, CAGR, or equity curve computed | **confirmed** |
| no bootstrap, Monte Carlo, or optimization run | **confirmed** |
| no candidate specification or implementation created | **confirmed** |
| no application or research implementation code modified | **confirmed** |
| no historical report, specification, threshold, or verdict modified | **confirmed** |
| no frozen artifact or manifest modified | **confirmed** |
| no dependency installed, Docker started, or application service started | **confirmed** |
| no Stage 2N or subsequent stage started | **confirmed** |

### 8.12 Unresolved limitations

1. **The framework is a proposal, not an approved protocol.** It has not been reviewed or adopted by
   the owner.
2. **The owner decisions are open.** No minimum effect, risk limit, capital context, venue standard,
   or audit standard has been selected.
3. **The cost study has not been performed.** The framework specifies what evidence is required, not
   what the cost is.
4. **No independent review of Stage 2M has occurred.** This document is a design proposal, not an
   audited framework.
5. **The statistical examples are illustrative.** They use conventional arithmetic and do not
   constitute a sample-size recommendation.
6. **The framework has not been tested on a real hypothesis.** It is designed to be testable, but its
   practicality can only be assessed when a future, separately authorized stage applies it.
7. **The historical record remains unchanged.** The Stage 2J verdicts, the Stage 2K stop decision, and
   the Stage 2L self-review verdict stand.

---

## 9. Final statement

Stage 2M proposes a framework, not a strategy. It replaces an underived count threshold with an
economic objective, a dependence-aware sufficiency rule, a venue-specific cost model, an independent
audit standard, and a controlled evaluation protocol. It preserves every historical verdict and does
not reopen the Stage 2K decision to stop the current strategy family under the current framework.

**No future strategy experiment is authorized by Stage 2M.** The next step is an owner decision on
the register, followed — only if the owner authorizes it — by a cost study and a framework freeze.
Stage 2N is not started.
