# Stage 2M — Research Governance Protocol

**Stage:** 2M (research-governance and methodology design only)
**Status:** proposed protocol requiring owner approval. It authorizes no experiment, candidate, or
data access.
**Date:** 2026-11-09 (UTC)

**Evidence labels:** **Verified fact** (repository-supported, cited), **Interpretation** (reasoned
conclusion), **Proposal** (suggested methodology requiring approval), **Owner decision** (cannot be
made by the research agent).

---

## 0. Purpose

This document proposes a controlled process for future strategy research. It defines seven gates,
the evidence required at each gate, the freeze and audit rules, the separation of development,
validation, and out-of-sample data, and the conditions under which a hypothesis may be rejected,
continued, or advanced.

The protocol is deliberately conservative. Its purpose is not to make research fast. Its purpose is
to make a future result interpretable, reproducible, and economically meaningful.

**Verified fact:** the historical programme had a recognizable pipeline but no single written
governance protocol. It used frozen specifications, pre-registered analysis plans, and stage-specific
decision rules, but it did not have an owner-approved economic objective, a dependence-aware
sufficiency rule, or an arms-length implementation audit
(`docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §1.2;
`docs/research/stage2l/STAGE2L_FINAL_AUDIT_REPORT.md` §1).

---

## 1. Principles

**Proposal:** the protocol rests on eight principles.

1. **Economic objective first.** No hypothesis is accepted before the owner has approved the
   minimum meaningful effect, the risk limits, the capital context, and the primary estimand.
2. **Pre-registration before outcomes.** The hypothesis, rules, metrics, statistical methods,
   sample-sufficiency calculation, and failure criteria are frozen before any outcome is observed.
3. **Data provenance and separation.** Development, validation, and out-of-sample data are
   identified, hashed, and separated chronologically. Access is logged and limited.
4. **Dependence-aware evidence.** Non-overlap is not independence. Uncertainty is estimated under a
   pre-specified dependence model, with robustness checks.
5. **Cost realism.** Execution costs are measured for the execution venue, not assumed from a
   research proxy. The primary verdict uses a conservative cost estimate.
6. **Independent verification.** Implementation correctness is audited by a party with no prior
   involvement in the design or implementation. A self-review is not sufficient.
7. **No automatic promotion.** Passing a gate does not authorize the next stage. Each stage requires
   separate owner authorization.
8. **Preserve the record.** Specifications, code, data manifests, outputs, audits, and owner
   decisions are versioned, hashed, and retained.

---

## 2. Stage authorization model

### 2.1 The rule

**Proposal:** every stage requires a written owner authorization that names:

- the stage and its objective;
- the exact artifacts it may create or modify;
- the data it may access;
- the analyses it may run;
- the prohibitions it must respect;
- the stop condition.

A stage authorization does not imply authorization for the next stage. A stage that produces a
positive result may recommend a next step, but it may not take it.

### 2.2 The gate sequence

```
Gate 0  Economic objective
   ↓
Gate 1  Data and venue validity
   ↓
Gate 2  Hypothesis registration
   ↓
Gate 3  Feasibility
   ↓
Gate 4  Independent implementation verification
   ↓
Gate 5  Controlled performance evaluation
   ↓
Gate 6  Final research decision
```

**Interpretation:** the order matters. A hypothesis cannot be registered before the objective is
approved; a feasibility count cannot be interpreted before the data and cost basis are valid; a
performance result cannot be accepted before the implementation is independently verified.

### 2.3 Gate failure

**Proposal:** if a gate fails, the process stops at that gate. The owner may:

- reject the hypothesis;
- authorize a remediation stage;
- authorize a new hypothesis;
- abandon the direction.

A gate failure does not authorize a workaround, a threshold change, or a data extension.

---

## 3. Gate 0 — Economic objective

### 3.1 Purpose

To establish what the research is trying to prove and what would make it worth doing.

### 3.2 Required inputs

- owner-approved minimum meaningful effect (definition and value);
- owner-approved risk limits (drawdown, per-trade loss, tail, liquidity, operational);
- owner-approved capital and position-sizing context;
- owner-approved primary and secondary estimands;
- owner-approved execution venue and cost evidence standard;
- owner-approved error-control objective and dependence-treatment standard.

### 3.3 Pass criteria

- every decision in the owner register that is marked **blocking** is resolved;
- no unresolved decision is silently defaulted;
- the objective is written in a form that a future experiment can test;
- the risk limits are expressed in the same units as the primary metric.

### 3.4 Artifacts

- a signed owner decision record;
- an economic objective memo;
- a risk policy statement;
- a capital and execution context statement.

### 3.5 Failure handling

If Gate 0 is incomplete, no hypothesis may be registered and no data may be accessed for a strategy
experiment. A research stage may still review documentation or design methodology, but it may not
count signals or outcomes.

**Owner decision:** all Gate 0 inputs. The research agent must not choose them.

---

## 4. Gate 1 — Data and venue validity

### 4.1 Purpose

To establish that the data and the execution assumptions are fit for the experiment.

### 4.2 Required inputs

- dataset provenance: source, extraction date, instrument, timeframe, timezone, file hashes;
- data-quality report: gaps, duplicates, off-grid records, zero-volume placeholders, invalid OHLC,
  partial buckets, segment boundaries;
- alignment report: lower-timeframe to higher-timeframe reconciliation, gap-aware denominators,
  tolerance rules;
- development/validation/OOS separation: exact date ranges and hashes;
- execution-cost evidence: fee schedule, spread, depth, slippage, latency, fill rates, operational
  constraints, or a documented plan to collect them;
- venue specification: instrument, minimum notional, lot size, order types, API limits, maintenance
  windows;
- a statement separating market-data facts from execution assumptions.

### 4.3 Pass criteria

- every dataset hash matches the recorded manifest;
- every registered gap is accounted for;
- alignment mismatches in fields the design reads are zero, or are explained and bounded;
- the development interval is clearly separated from validation and OOS;
- cost evidence is either measured or explicitly labelled as an assumption with a plan to replace
  it;
- no validation or OOS row is read during the gate.

### 4.4 Artifacts

- data provenance manifest;
- data-quality and alignment report;
- execution-cost evidence file;
- venue specification;
- access log.

### 4.5 Failure handling

If the data or cost basis is not fit for purpose, the experiment is **inconclusive** or **not
authorized**. It is not permissible to substitute an assumption and proceed as if the gate had
passed.

**Verified fact:** the historical Stage 2J alignment audit was clean: zero high/low/close or volume
mismatches in complete buckets, with the registered gaps and the M3 exemption documented
(`docs/research/stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md` §1–§5). That is a model for the data side
of Gate 1. The cost side was not met: the 26 bp figure is a Binance proxy, not a Nobitex measurement
(`docs/research/stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §4).

---

## 5. Gate 2 — Hypothesis registration

### 5.1 Purpose

To freeze the hypothesis and the analysis plan before any outcome is observed.

### 5.2 Required inputs

A registration document containing:

1. **Hypothesis:** a clear, falsifiable statement of the economic mechanism.
2. **Rationale:** why the mechanism should exist, independent of the observed data.
3. **Universe and data:** instrument, venue, timeframes, development interval, exclusions.
4. **Entry rules:** signal conditions, timing, and look-ahead safeguards.
5. **Exit rules:** target, stop, time exit, and holding policy.
6. **Risk rules:** position sizing, maximum concurrent positions, capital limits.
7. **Eligibility conditions:** regime, liquidity, session, or other filters.
8. **Primary estimand and MME:** the metric and the owner-approved threshold.
9. **Secondary metrics:** frequency, utilization, drawdown, tail, stability, cost sensitivity.
10. **Statistical methods:** estimator, dependence model, error control, multiple-testing policy.
11. **Sample-sufficiency calculation:** `N_ind`, `N_obs`, `required_opportunities`, assumptions, and
    sensitivity.
12. **Feasibility criteria:** what opportunity count and capital geometry would justify proceeding.
13. **Failure criteria:** what evidence would reject the hypothesis.
14. **Data-access plan:** development, validation, OOS, and the one-look rule.
15. **Audit plan:** the independent auditor and the scope of Gate 4.
16. **Version and hashes:** the frozen specification and code identity.

### 5.3 Pass criteria

- the registration is complete and internally consistent;
- the MME and risk limits match the Gate 0 record;
- the sample-sufficiency calculation is reproducible from its stated assumptions;
- the failure criteria are stated before the outcome;
- no outcome data has been observed by the analyst;
- the specification and analysis plan are hashed and frozen.

### 5.4 Artifacts

- the frozen registration document;
- the frozen specification and config;
- the analysis plan;
- the hash manifest;
- the data-access log showing no outcome access.

### 5.5 Failure handling

If the registration is incomplete or the analyst has already seen outcome data, the hypothesis is
**not eligible** for a confirmatory experiment. It may be treated as exploratory, but it cannot be
presented as a pre-registered test.

**Verified fact:** the historical Stage 2J pre-registered analysis plan fixed implementation choices
before counting and recorded them with reasons
(`docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §0, §10). That is a useful precedent for
Gate 2.

---

## 6. Gate 3 — Feasibility

### 6.1 Purpose

To determine whether a hypothesis produces enough economically feasible, dependence-aware
opportunities to justify a full performance experiment.

### 6.2 Required inputs

- the frozen hypothesis and rules;
- the cost model from Gate 1;
- the owner's MME and capital/risk policy;
- the derived sample requirement from Gate 2;
- a feasibility census that counts signals and opportunities but observes **no outcomes**;
- a dependence model or a pre-specified design-effect range;
- a capital-utilization analysis;
- a calendar-ceiling analysis.

### 6.3 Method

**Proposal:** the feasibility gate has five steps.

1. **Count the funnel.** Raw signals, unique opportunities, non-overlapping trades, and clusters.
2. **Apply the cost model.** For each opportunity, compute the all-in cost and the cost-feasible
   subset under the conservative primary cost.
3. **Apply the dependence model.** Estimate the effective number of independent or
   approximately-independent episodes under the pre-specified model, with sensitivity.
4. **Compare with the requirement.** Compare the dependence-adjusted feasible opportunity count with
   `required_opportunities` from Gate 2.
5. **Check practicality.** Compare the count with the expected annual frequency, the calendar
   ceiling, the capital utilization, and the liquidity/position-size constraints.

### 6.4 Decision rule

**Proposal:** use an interval, not a point.

| condition | decision |
|---|---|
| upper bound of the feasible-opportunity interval < `required_opportunities` | **stop** or redesign; the hypothesis is not testable on this interval |
| lower bound ≥ `required_opportunities`, and capital/liquidity constraints pass | **proceed** to Gate 4 |
| interval spans `required_opportunities` | **conditional**: collect more feasibility evidence or redesign; do not proceed to outcomes on the current design |
| capital or liquidity constraint fails | **stop** or redesign, regardless of the count |

The interval should reflect uncertainty in the cost model, the dependence model, and the execution
rate. It must not be narrowed by optimistic assumptions.

### 6.5 Why this is not a universal count

The requirement is derived from the owner's MME, the outcome variance, the dependence model, and the
execution rate. It is not a fixed number. Two hypotheses with the same opportunity count can have
different requirements because their stops, costs, dependence, and fill rates differ.

**Verified fact:** the historical 150 floor was not derived this way, and the 349 reference assumed
independence (`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §7.3;
`docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` §11.3).

### 6.6 Artifacts

- the feasibility census report;
- the cost-feasible and dependence-adjusted counts;
- the capital-utilization and liquidity analysis;
- the comparison with the derived requirement;
- the decision record.

### 6.7 Failure handling

A failed feasibility gate is a legitimate result. It does not authorize a lower requirement, a
relaxed cost, or a new variant chosen after seeing the count. A redesign must be a new, separately
authorized hypothesis.

---

## 7. Gate 4 — Independent implementation verification

### 7.1 Purpose

To establish that the implementation faithfully executes the frozen specification and that the
recorded result is reproducible, before any historical performance result is accepted.

### 7.2 Required inputs

- the frozen specification and config;
- the source code and version hashes;
- the test suite and synthetic fixtures;
- the data manifest and alignment report;
- the recorded outputs and logs;
- a specification-to-code trace;
- an independent auditor with access to the above.

### 7.3 Independence requirements

**Proposal:** the auditor must satisfy all of the following:

1. **No prior implementation involvement.** The auditor did not design, write, review, or report on
   the implementation under audit.
2. **No decision involvement.** The auditor did not participate in the choice of candidate,
   threshold, population, or verdict rule.
3. **No conflict of interest.** No financial, employment, or personal interest in the outcome.
4. **Separate context.** The auditor works from the frozen artifacts, not from the implementer's
   undocumented assumptions.
5. **Access.** The auditor can inspect the specifications, code, tests, logs, and outputs, and can
   run synthetic tests.
6. **Attestation.** The auditor signs a statement of independence and lists the evidence reviewed.

### 7.4 Audit scope

**Proposal:** the audit covers:

- **Specification-to-code traceability:** every frozen requirement maps to a code path or is recorded
  as unimplemented.
- **Synthetic testing:** controlled inputs test boundaries, labels, arithmetic, time handling, and
  error paths.
- **Temporal correctness:** previous-closed-bar reads, entry timing, no look-ahead, interval
  boundaries.
- **Data alignment:** gaps, partial buckets, segment breaks, ATR resets, upper-timeframe
  reconciliation.
- **Cost and capital arithmetic:** cost formula, gate boundary, stop validity, notional geometry.
- **Non-overlap and deduplication:** horizon, inclusive boundary, greedy acceptance, tie-breaking.
- **Diagnostics:** cluster assignment, effective sample size, quantiles, cost buckets.
- **Verdict logic:** precedence, populations, exact verdict terms.
- **Reproducibility:** code hash coverage, deterministic serialization, retained run artifacts.
- **Provenance:** commit ancestry, manifest hashes, dataset hashes, run identity.

### 7.5 Finding severity and resolution

**Proposal:** reuse the Stage 2L severity definitions:

| severity | meaning | resolution required |
|---|---|---|
| **CRITICAL** | the conclusion is wrong, the census is not traceable, or a prohibition was violated | immediate stop; correction and re-audit before any use |
| **MAJOR** | a frozen requirement is materially unimplemented, or a defect could plausibly change a verdict | correction and re-audit before any use |
| **MINOR** | a bounded divergence with no observed verdict effect | owner sign-off and a remediation plan; may proceed with disclosure |
| **OBSERVATION** | a latent risk, ambiguity, or evidence gap | record; address in a future version |

A MINOR finding that could become MAJOR under a different dataset should be treated as MAJOR for a
new experiment.

### 7.6 Stage 2L and the independence requirement

**Verified fact:** Stage 2L's primary verdict is
`SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`. The auditor participated in the prior Stage 2J work
(`docs/research/stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md` §6).

**Interpretation:** Stage 2L is a useful technical record, but it **cannot** be used as Gate 4
evidence for the Stage 2J implementation. A future Gate 4 must be a new review by a party with no
prior involvement. Relabeling Stage 2L, changing the model, or starting a new conversation does not
create independence.

### 7.7 Practical alternatives when no external professional auditor is available

**Proposal:** the owner may choose one of the following, with the stated limits.

| alternative | what it can establish | what it cannot establish |
|---|---|---|
| **External professional auditor** | arms-length review, domain expertise, formal accountability | may be expensive and hard to obtain; still needs access and time |
| **Separate reviewer with no prior implementation involvement** | fresh-eyes traceability, synthetic testing, and code review | not a professional audit; the reviewer may lack domain expertise; independence depends on the reviewer's actual separation |
| **Second independent agent with a clean context and separate toolchain** | reproducibility of the review process; a second inspection of the code and artifacts | not human accountability; the agent may share training biases; independence must be documented, not assumed |
| **Reproducible synthetic tests plus a separate code review** | testable behavior and a second reading of the code | does not establish full independence or domain competence |
| **External specialist review of critical components** | deep review of the cost model, statistics, or execution logic | limited scope; not a full audit |

**Interpretation:** the minimum defensible standard for a decision-critical experiment is a separate
reviewer with no prior involvement, access to the frozen artifacts, and a signed independence
statement. If that is unavailable, the experiment must be labelled **provisional** and the
independence limitation must be disclosed in every result. A different model or a new conversation is
not, by itself, independence.

### 7.8 Re-audit

**Proposal:** after a CRITICAL or MAJOR finding is remediated, the auditor re-audits the affected
scope. The re-audit report states what changed, what was retested, and whether the finding is closed.
The original finding remains in the record; it is not deleted.

---

## 8. Gate 5 — Controlled performance evaluation

### 8.1 Purpose

To estimate the economic effect of the frozen hypothesis on data that were not used to design it,
under a pre-registered protocol.

### 8.2 Data separation

**Proposal:** define three chronological blocks:

| block | purpose | access rule |
|---|---|---|
| **Development** | hypothesis design, rule development, feasibility, and any exploratory analysis | may be used, but every use is logged; the final rule must be frozen before validation |
| **Validation** | one confirmatory look at the frozen rule | one look only; no rule changes after the look; access logged |
| **Out-of-sample (OOS)** | final confirmation after validation | one look only; no changes; access logged; used only if validation passes the pre-registered criteria |

**Proposal:** the blocks are chronological and non-overlapping. An embargo or purge period separates
them so that overlapping holding periods do not leak information across the boundary. The exact
dates and hashes are frozen at Gate 2.

**Interpretation:** reusing validation data for a second look, or changing a rule after seeing
validation, converts the validation block into development data. The framework must record this
explicitly and treat the result as exploratory.

### 8.3 Leakage prevention

**Proposal:**

- no future bar is read at a decision point;
- higher-timeframe reads use only closed bars;
- entry is at the next available open, not at the signal bar's close;
- indicators are computed from data available at the decision time;
- the same data-prep pipeline is used for development, validation, and OOS;
- any feature or filter that uses the full sample is prohibited;
- the audit checks look-ahead and alignment before the performance run.

### 8.4 Multiple testing and parameter selection

**Proposal:**

- one primary hypothesis and one primary test;
- all secondary tests are labelled exploratory;
- if multiple hypotheses are tested, the family and the correction are pre-registered;
- parameter selection is confined to development data and is frozen before validation;
- no post-hoc threshold changes;
- every variant, failed attempt, and abandoned parameter set is reported.

### 8.5 Robustness

**Proposal:** report, at minimum:

- cost sensitivity across the measured range;
- dependence sensitivity across at least two treatments;
- regime/subperiod stability;
- concentration diagnostics;
- a control or placebo where the hypothesis implies one;
- a condition ablation only if it was pre-registered (otherwise it is exploratory).

### 8.6 Drawdown and tail risk

**Proposal:** report maximum drawdown, worst trade, CVaR/expected shortfall, maximum adverse
excursion, time under water, and the largest concentration by episode, regime, and session. Compare
each with the owner's risk limits from Gate 0.

### 8.7 Reporting requirements

**Proposal:** the report includes:

- the frozen protocol and its hash;
- the data blocks and hashes;
- the full funnel from raw signals to executed trades;
- the primary estimate with a dependence-adjusted interval;
- the MME comparison and the decision;
- all secondary metrics;
- all sensitivity and robustness results;
- every deviation from the protocol;
- the independent audit report and the resolution of findings;
- a statement of what the result does not establish.

### 8.8 Rejection conditions

**Proposal:** reject the hypothesis if any of the following holds:

- the primary interval's upper bound is below the MME;
- a risk limit is breached;
- the result is not robust across the pre-specified cost or dependence treatments;
- the effect is concentrated in one episode or regime and the stability requirement fails;
- the implementation audit has an open CRITICAL or MAJOR finding;
- the validation/OOS protocol was violated.

If the interval includes the MME or zero, the result is **inconclusive**, not a pass.

### 8.9 No execution in Stage 2M

**Verified fact:** Stage 2M does not access validation or OOS data, does not run a performance
evaluation, and does not compute P&L, expectancy, drawdown, Sharpe, Sortino, or any other performance
metric.

---

## 9. Gate 6 — Final research decision

### 9.1 Purpose

To convert the evidence into a decision without automatic promotion.

### 9.2 Decision options

| decision | condition | authority |
|---|---|---|
| **Reject hypothesis** | the pre-registered failure criterion is met | pre-registered rule; owner informed |
| **Inconclusive** | the evidence is insufficient or the protocol was compromised | pre-registered rule; no promotion |
| **Continue research** | the evidence supports the MME but a gate or robustness check is unresolved | separate owner authorization for a named next stage |
| **Advance to paper trading** | all gates pass, including independent audit and OOS confirmation | separate owner authorization |
| **Abandon the research direction** | the requirement is unattainable, the mechanism fails, or the cost/risk context is unsuitable | owner decision |

### 9.3 Decision matrix

**Proposal:**

| primary interval | risk limits | robustness | audit | decision |
|---|---|---|---|---|
| lower bound ≥ MME | pass | pass | clear | advance (with separate authorization) |
| lower bound ≥ MME | pass | fail | clear | inconclusive; do not advance |
| lower bound ≥ MME | fail | any | any | reject |
| interval includes MME | any | any | any | inconclusive |
| upper bound < MME | any | any | any | reject |
| any | any | any | open CRITICAL/MAJOR | stop; no decision until resolved |

**Interpretation:** a pass on the primary metric is necessary but not sufficient. The risk,
robustness, and audit gates can each block advancement.

### 9.4 No automatic action

**Proposal:** no decision in this table authorizes a trade, a paper-trading account, a live account,
or a new candidate. Each requires a separate owner authorization with its own scope and stop
condition.

---

## 10. Freeze policy

### 10.1 What is frozen

**Proposal:** the following are frozen before the relevant stage:

- hypothesis statement and economic mechanism;
- entry, exit, risk, and eligibility rules;
- primary and secondary metrics;
- MME and risk limits;
- statistical methods and dependence model;
- sample-sufficiency calculation;
- feasibility criteria;
- failure criteria;
- data blocks and access rules;
- code version and test suite.

### 10.2 Versioning

**Proposal:**

- use semantic versions (`major.minor.patch`);
- a major version changes a rule, metric, population, or verdict;
- a minor version clarifies text without changing behavior;
- a patch fixes a defect without changing the intended behavior;
- every version has a manifest with SHA256 hashes and byte counts;
- the manifest has a self-hash computed over its canonical content, excluding the self-hash field.

### 10.3 Change control

**Proposal:**

- no change to a frozen artifact after counting begins;
- a change discovered before counting is recorded in the pre-registration with the reason and the
  affected population;
- a change discovered after counting voids the run; a new pre-registration is required;
- no threshold, population, or verdict change after seeing counts;
- no retroactive editing of a historical artifact.

**Verified fact:** the historical Stage 2J plan followed this discipline: implementation choices were
fixed before counting, and the plan states that a post-count change would void the run
(`docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §10).

### 10.4 Labels and populations

**Proposal:** every population, label, and verdict term is defined in the frozen text. The verdict
table names the population to which each condition applies. A pre-registered interpretation may
resolve an ambiguity before counting, but it must be recorded in the plan and disclosed in the
report.

**Interpretation:** the historical L-001 and L-002 findings show why this matters: a capital-geometry
condition and a concentration FAIL term were resolved outside the frozen verdict table. They did not
change the Stage 2J verdicts, but they created interpretive distance between the specification and
the report (`docs/research/stage2l/TECHNICAL_FINDINGS.md`).

---

## 11. Independent review and audit governance

### 11.1 Separation of duties

**Proposal:** the following roles are separated:

- **Owner:** approves objectives, risk, and stage authorizations.
- **Researcher/implementer:** designs the hypothesis and writes the code.
- **Auditor:** verifies the implementation and the evidence; does not design or implement.
- **Reviewer (optional):** challenges the methodology and the interpretation.

One person may hold more than one role only if the overlap is disclosed and the audit is performed by
someone else. An implementer cannot audit their own work.

### 11.2 Auditor access

**Proposal:** the auditor receives:

- the frozen specification and config;
- the source code and version hashes;
- the test suite and synthetic fixtures;
- the data manifest and alignment report;
- the recorded outputs and logs;
- the pre-registration and any amendments;
- the owner decisions that affect the verdict.

The auditor may run synthetic tests and inspect code and aggregate outputs. The auditor may not
access validation or OOS data unless the audit scope explicitly requires it and the owner authorizes
it.

### 11.3 Conflict-of-interest disclosure

**Proposal:** the auditor discloses:

- any prior involvement in the design, implementation, or reporting;
- any financial or employment interest in the outcome;
- any relationship with the implementer or owner that could affect judgment;
- the scope and limits of their expertise.

### 11.4 Review of historical evidence

**Proposal:** when auditing a historical result, the auditor reviews the frozen artifacts and the
recorded outputs, not a reconstructed narrative. If the original data are unavailable, the auditor
states that the result cannot be fully reproduced.

### 11.5 Finding classification and remediation

**Proposal:** use the CRITICAL/MAJOR/MINOR/OBSERVATION scale in §7.5. Each finding has:

- a unique ID;
- a location;
- the requirement it violates;
- an explanation;
- the impact;
- a proof status;
- the historical-conclusion impact;
- the evidence;
- a recommended resolution.

**Proposal:** CRITICAL and MAJOR findings block the next gate. MINOR findings require owner sign-off
and a remediation plan. OBSERVATION items are recorded and addressed in a future version.

### 11.6 Re-audit and evidence preservation

**Proposal:**

- after remediation, the auditor re-audits the affected scope;
- the re-audit report states what changed and what was retested;
- the original finding and the re-audit are both retained;
- audit reports, hashes, and owner decisions are versioned and never deleted;
- the audit record is part of the stage's freeze manifest.

### 11.7 What each alternative can and cannot establish

The practical alternatives are set out in §7.7. The key point is that **independence is a property of
the relationship, not of the tool**. A different model, a new conversation, or a separate agent does
not automatically create independence. The project must document:

- who performed the audit;
- what prior involvement they had;
- what they reviewed;
- what they could and could not verify;
- what independence limitations remain.

### 11.8 Stage 2L's status

**Verified fact:** Stage 2L performed a self-review and explicitly did not establish independence
(`docs/research/stage2l/AUDIT_SCOPE_AND_INDEPENDENCE.md` §6).

**Proposal:** Stage 2L is retained as a technical record and as evidence of the implementation's
traceability and synthetic-test coverage. It is **not** accepted as Gate 4 evidence for the Stage 2J
census. A future Gate 4 must be a new review by a party with no prior involvement in the design,
implementation, or reporting of the artifact under audit.

---

## 12. Data representativeness framework

### 12.1 Purpose

To decide whether a result estimated on one historical interval can be extrapolated to future market
conditions.

### 12.2 Target population

**Proposal:** define the target population explicitly:

- instrument and venue;
- timeframe and holding horizon;
- capital and position size;
- market conditions in which the rule is intended to operate;
- conditions in which it is intended to stand aside.

A result that is estimated on a different population is not evidence for the target.

### 12.3 Regime dimensions

**Proposal:** characterize the development, validation, and OOS blocks along at least these
dimensions:

| dimension | example measurement | why it matters |
|---|---|---|
| **Volatility** | realized volatility, ATR percentile, range | stop size and cost_R depend on volatility |
| **Trend** | moving-average slope, drawdown from high, trend-state classification | many rules are regime-dependent |
| **Liquidity** | volume, spread, depth, trade count | execution cost and fill probability depend on liquidity |
| **Market structure** | fees, tick size, session conventions, venue rules | a structural change can invalidate a rule |
| **Exchange-specific behavior** | outages, maintenance, listing changes, API limits | operational risk is venue-specific |
| **Data quality** | gaps, zero-volume bars, partial buckets | gaps can bias counts and outcomes |
| **Selection/survivorship** | instrument universe construction, delisting, data vendor choices | can bias the sample |

### 12.4 Evidence needed for extrapolation

**Proposal:** extrapolation to future conditions requires:

1. **Coverage:** the development block includes multiple volatility, trend, and liquidity regimes,
   not just one.
2. **Stability:** the result is not driven by a single episode, month, or regime; the pre-specified
   stability test passes.
3. **Mechanism robustness:** the economic rationale does not depend on a market structure that has
   changed.
4. **Validation and OOS:** the result holds on chronologically later data under the same frozen
   rules.
5. **Structural-break analysis:** known changes (fee changes, tick-size changes, venue changes,
   regulatory changes) are identified and their impact is assessed.
6. **Gap sensitivity:** the result is robust to the registered gaps and to the treatment of partial
   buckets.
7. **Cost stability:** the cost model is valid for the target period, not only the historical period.

**Interpretation:** a positive in-sample result on one 1,277-day path is not sufficient for
extrapolation. The historical interval covers a bull phase, a bear phase, and a recovery, but it is
still one realized history (`HISTORICAL_RESEARCH_SYNTHESIS.md` §9.5). The framework should require
evidence of stability and later-period confirmation, not just a longer backtest.

### 12.5 What is prohibited in Stage 2M

**Verified fact:** Stage 2M does not access or process any market data, including development,
validation, or OOS rows. It does not use validation or OOS observations to inform the framework
design.

---

## 13. Resource and implementation constraints

### 13.1 Classification

**Proposal:** every requirement is classified as:

- **Essential before any future experiment:** must be complete before Gate 0/1/2/3/4.
- **Important but deferrable:** can be completed during a later authorized stage, provided the
  limitation is disclosed.
- **Optional improvement:** desirable but not required for a defensible experiment.

### 13.2 Practical cost

| requirement | classification | practical cost | notes |
|---|---|---|---|
| Owner decision register completed | **essential** | low: owner time | blocks all subsequent work |
| Economic objective and MME | **essential** | low: owner time | no computation |
| Risk and capital policy | **essential** | low: owner time | no computation |
| Venue cost study | **essential** before a venue-specific experiment | medium–high: external data/account access | can be a separate authorized stage |
| Data provenance and alignment | **essential** | low–medium: hashing and audit | existing tooling can be reused |
| Frozen pre-registration | **essential** | low–medium: writing and review | no computation |
| Dependence-aware sufficiency | **essential** | low–medium: analytical work | no large simulation required initially |
| Independent audit | **essential** | medium: reviewer time | alternative standards in §7.7 |
| Regime coverage and stability analysis | important, deferrable to Gate 5 | medium | requires data access at Gate 5 only |
| Full order-book reconstruction | important for execution, deferrable | high: data and compute | may exceed project resources |
| Advanced bootstrap/Monte Carlo | optional | medium: compute | use analytic approximations first |
| External professional audit | optional / desirable | high: cost | not a substitute for the minimum standard |
| Multi-venue comparison | optional | high: data and access | only if owner authorizes |

### 13.3 Resource discipline

**Proposal:**

- no dataset loading in governance/design stages;
- no Docker or application services for research design;
- no dependency installation without owner authorization;
- bounded-memory analysis: target 4 GiB, hard ceiling 6 GiB;
- prefer analytical approximations and small, pre-registered simulations over large Monte Carlo
  studies;
- store aggregates and manifests, not raw data copies;
- keep all new files within the authorized research directory.

**Verified fact:** the Stage 2J census achieved 551.793 MiB peak RSS against the 4 GiB target, showing
that the existing pipeline is resource-efficient (`stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §3).
The governance framework should preserve that discipline.

---

## 14. Evidence preservation

**Proposal:** every stage retains:

- the frozen specification and config;
- the analysis plan and amendments;
- the code and test suite, with hashes;
- the data manifest and hashes;
- the run manifest and logs;
- the outputs and reports;
- the audit report and finding log;
- the owner decisions and stage authorizations;
- the access log for development, validation, and OOS data.

The retention rule is: **if it affected a decision, it is retained and hashed**. A narrative
reconstruction is not a substitute for the artifact.

**Verified fact:** the historical Stage 2L finding L-009 records that the determinism claim had no
retained second-run artifacts, and L-010 records that the code hash omitted `freeze_verify.py` and
test files. These are examples of evidence-preservation gaps that a future framework should avoid
(`docs/research/stage2l/TECHNICAL_FINDINGS.md`).

---

## 15. Prohibitions

The following are prohibited under this protocol unless a separate owner authorization explicitly
permits them:

- creating a candidate specification before Gate 0–2 are complete;
- running a detector or census on validation or OOS data;
- reading, decoding, or summarizing validation or OOS rows outside an authorized Gate 5 stage;
- changing a frozen rule, threshold, population, or verdict after counting;
- repairing a historical implementation without a separate remediation authorization;
- applying the Stage 2I change proposals CP-1 through CP-5 without a new freeze;
- running a backtest, bootstrap, Monte Carlo, or optimization before the relevant gates are passed;
- presenting a structural feasibility count as a profitability result;
- presenting a self-review as an independent audit;
- starting Stage 2N or any subsequent stage without explicit authorization.

**Verified fact:** Stage 2M respects these prohibitions. It creates only design documents and a
manifest, accesses no market data, runs no analysis, and changes no historical artifact.

---

## 16. Summary

The protocol replaces a stage-specific counting pipeline with a gate-based governance process. The
central changes are:

1. an owner-approved economic objective before any hypothesis;
2. a venue-specific cost model and a conservative cost rule;
3. a dependence-aware sample-sufficiency calculation;
4. a feasibility gate connected to the derived requirement;
5. an independent implementation audit with a documented independence standard;
6. a controlled development/validation/OOS evaluation;
7. an explicit final decision that does not automatically promote a hypothesis.

The protocol is a proposal. It does not authorize an experiment, create a candidate, or begin
Stage 2N.
