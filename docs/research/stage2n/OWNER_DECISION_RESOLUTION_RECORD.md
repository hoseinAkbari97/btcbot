# Stage 2N — Owner Decision Resolution Record

**Stage:** 2N (owner decision resolution only)
**Status:** owner decision process addressed. Only decisions explicitly answered and confirmed by the
owner are recorded here; unresolved items remain open.
**Date:** 2026-11-09 (UTC)
**Last updated:** 2026-11-10 (UTC)
**Source register:** `docs/research/stage2m/OWNER_DECISION_REGISTER.md`

**Source integrity:** the Stage 2M freeze manifest self-hash was verified as
`6469d6a417681c9a6615d08ede9059a48aa104ab301c5bd42a17e4b24f54b0a9`, with all six
deliverables and twenty-one source artifacts matching their recorded hashes and byte counts.

**Scope note:** this record does not modify Stage 2M, does not implement the proposed framework,
does not create a candidate, does not process market data, does not run a census or backtest,
does not access validation or out-of-sample data, and does not authorize Stage 2O.

---

## 1. Status summary

| ID | decision | status |
|---|---|---|
| D-01 | minimum meaningful effect | **OPEN — DEFINITION A SELECTED; VALUE NOT SET** |
| D-02 | acceptable drawdown and risk | **OPEN — OPTION C SELECTED; LIMITS NOT SET** |
| D-03 | primary performance estimand | **RESOLVED** |
| D-04 | capital and execution context | **RESOLVED — RESEARCH LEG ONLY; REAL-CAPITAL CHECK OPEN** |
| D-05 | venue and cost evidence standard | **RESOLVED — STAGED A + B; ACCESS OPEN** |
| D-06 | cost-uncertainty and conservative-cost rule | **RESOLVED — CONSERVATIVE PRIMARY (p95); APPLICATION PENDING NOBITEX MEASUREMENT** |
| D-07 | annual contribution as a co-primary metric | **RESOLVED — CO-PRIMARY; ANNUAL TARGET PENDING D-01** |
| D-08 | statistical confidence and error-control objective | **RESOLVED — A+B; α=5%; POWER=80%; HIERARCHICAL** |
| D-09 | dependence treatment and robustness standard | **RESOLVED — C; INCONCLUSIVE ON DISAGREEMENT; PARAMETERS OPEN** |
| D-10 | sample-sufficiency methodology | **RESOLVED — METHODOLOGY A; NUMERIC REQUIREMENT PENDING INPUTS** |
| D-11 | multiple-testing and selection policy | **RESOLVED — A+D; ONE PRIMARY HYPOTHESIS; NO MULTIPLE HYPOTHESES; OOS CONFIRMATION REQUIRED** |
| D-12 | validation/OOS access and one-look policy | **RESOLVED — STRICT ONE-LOOK; LOGGING; EMBARGO** |
| D-13 | independent audit standard | **RESOLVED — B+E; SPECIALIST IF FEASIBLE; RESIDUAL DISCLOSURE REQUIRED** |
| D-14 | data representativeness requirements | **RESOLVED — C; ALL THREE REGIMES; D-12 OOS LOOK; SINGLE-INTERVAL PROVISIONAL** |
| D-15 | revisit Candidate A's control or investigate a different family | **OPEN — DEFERRED UNTIL D-01/D-02 RESOLVED AND GATE 0–4 COMPLETE** |

An open decision has not been defaulted. Where the register marks a decision **BLOCKING**, the
dependent gate remains blocked.

---

## 2. D-04 — Capital and execution context

### 2.1 Owner answer

- **Chosen option:** **C — Scaled research basis.**
- The owner approved the historical research convention as the frozen research leg and chose to
  record the real-capital basis as an open Gate 0 input.

### 2.2 Recorded values

| field | recorded value | basis |
|---|---|---|
| research equity | `$10,000` | historical research convention, not the owner's real account |
| risk per trade | 1% of equity (`$100` at inception) | historical research convention |
| position sizing | fixed-fractional | implied by the 1% rule |
| concurrent positions | 1 | historical research convention |
| leverage | none | historical research convention |
| direction | spot long-only | historical research convention |
| order type | next-bar-open market entry | historical assumption |
| real-capital check | **open** | no real equity, risk budget, or constraints supplied yet |

### 2.3 Implications

1. The research leg is comparable to the historical basis, so results can be read against the
   existing research record.
2. Annual-return and annual-contribution calculations will be stated on the `$10,000` / 1% research
   basis and must be labelled as a convention, not a forecast for a live account.
3. Real-world viability at the owner's actual capital is **not** established. If the real basis
   differs materially, position size, minimum notional, liquidity, and annual contribution must be
   re-checked.
4. D-01, D-02, D-07, and D-14 can now be decided for the research leg, but the open real-capital
   input continues to block Gate 0 passage.

### 2.4 Qualifications and open items

- D-04 is resolved for the **research leg only**. The real-capital check remains an open Gate 0
  input and is not satisfied.
- The venue's cost evidence standard is **not** part of this decision; it is D-05 and remains open.
- No venue, real capital, real risk budget, or live execution constraint is recorded as approved.
- No other decision is affected or resolved by this entry.

### 2.5 Confirmation

- The owner explicitly selected option C.
- The owner explicitly selected the research-leg values recorded in §2.2.
- The owner explicitly chose to record the real-capital check as an open Gate 0 input.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 3. D-03 — Primary performance estimand

### 3.1 Owner answer

- **Primary estimand:** **A — Net R per executed trade**, after all-in execution costs.
- **Co-primary estimand:** **D — Net annual contribution.**
- By selecting A and D, the owner did not designate B (net expectancy per opportunity),
  C (net annual return on capital), or E (risk-adjusted ratio) as primary or co-primary.

### 3.2 Implications

1. The headline result is net R per executed trade, after all-in costs. It is scale-free and
   comparable to the stop, but by itself ignores frequency and capital utilization.
2. The annual contribution is a co-primary **decision** metric, not merely descriptive. A rule that
   passes the per-trade test but fails the annual contribution target is a research result, not an
   investment candidate.
3. The annual contribution will be computed on the D-04 research basis (`$10,000`, 1% risk, one
   position, no leverage). The real-capital check remains open, so the annual figure is a
   convention, not a live-account forecast.
4. D-01 must be stated in two parts: an MME in **net R per executed trade**, and an annual
   contribution target.
5. D-10 sample-size work will use the R-based outcome variance and the R-based MME as the primary
   calculation.
6. The exact rule for combining the two co-primary results — for example, whether both must pass,
   and how error control is allocated across them — is **not** decided here. That belongs to D-08
   and D-11.

### 3.3 Qualifications and open items

- The reporting role of the non-primary metrics (B, C, E, and risk/tail diagnostics) is not decided
  by this entry; it is to be fixed at pre-registration.
- The consistency of D-07 with this entry is to be confirmed when D-07 is decided. The owner's
  choice of D as co-primary logically implies D-07 option A, unless D-03 is revised.
- No MME value, annual target, error-control rule, dependence treatment, or sample-size method is
  recorded as decided here.

### 3.4 Confirmation

- The owner explicitly selected A as primary and D as co-primary.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 4. D-01 — Minimum meaningful effect

### 4.1 Owner answer

- **Definition selected:** **A — Net R per executed trade.**
- **Numeric MME (`δ_R`):** open — not set.
- **Annual contribution target:** open — not set.
- The owner chose to keep the numeric values open rather than select a threshold.

### 4.2 Implications

1. The MME will be expressed in **net R per executed trade**, consistent with D-03.
2. No specific `δ_R` is adopted. The historical `0.15R` is **not** treated as a default or as
   approved.
3. Because the value is open, Gate 0 remains blocked and D-10 cannot derive a sample-size
   requirement.
4. The annual contribution target is also open; until it is set, the D-07 co-primary requirement
   cannot be operationalized.

### 4.3 Qualifications and open items

- Selecting the definition is not the same as resolving D-01. The numeric threshold is the core of
  the decision and remains owner-only.
- D-01 remains **open** in the status summary. The definition selection is recorded as an interim
  selection, not a resolution.

### 4.4 Confirmation

- The owner explicitly selected definition A.
- The owner explicitly chose to keep the values open.
- The owner confirmed the interim record above before it was written.
- No numeric value in this entry was defaulted by the research agent.

---

## 5. D-07 — Annual contribution as a co-primary metric

### 5.1 Owner answer

- **Chosen option:** **A — Yes, co-primary.**
- **Annual target value:** pending D-01.

### 5.2 Implications

1. A future experiment must satisfy both the per-trade MME and an annual contribution target; the
   target value is part of D-01 and is not yet set.
2. A rule that passes the per-trade test but fails the annual target is a research result, not an
   investment candidate.
3. The exact conjunction rule and error-control allocation across the two co-primary metrics remain
   **undecided**; they belong to D-08 and D-11.

### 5.3 Qualifications and open items

- D-07 is resolved in principle, but the annual target is not set. The decision is recorded as
  **co-primary; annual target pending D-01**.
- D-07 A is consistent with D-03's co-primary designation; no revision to D-03 is needed.

### 5.4 Confirmation

- The owner explicitly selected option A.
- The owner confirmed the interim record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 6. D-02 — Acceptable drawdown and risk

### 6.1 Owner answer

- **Chosen option:** **C — Drawdown, tail, and liquidity.**
- **Maximum drawdown:** open — not set.
- **Per-trade loss limit:** open — not set.
- **Tail measure and limit:** open — not set.
- **Liquidity / position-size constraint:** open — not set.
- The owner chose to keep the numeric limits open rather than set them now.

### 6.2 Implications

1. The agreed scope is a maximum drawdown, a per-trade loss limit, a tail measure, and a
   liquidity/position-size constraint. No numeric limit is adopted.
2. Because the limits are open, Gate 5 and Gate 6 remain blocked, and no rule can be judged
   acceptable or unacceptable on risk grounds.
3. The risk limits must eventually be expressed in the same units as the primary metric (R), with
   the drawdown and liquidity constraints stated in their natural units.
4. The tail and liquidity measurement methods are not decided here; they may depend on D-05 and
   D-14.
5. On the D-04 research basis, 1R = `$100` = 1% of `$10,000`; this is a translation, not an approved
   limit.

### 6.3 Qualifications and open items

- D-02 remains **open** in the status summary. The option selection is recorded as an interim
  selection, not a resolution.
- No maximum drawdown, per-trade loss limit, tail limit, or liquidity constraint is recorded as
  approved.
- Option D additions (time under water, ruin probability, concentration, operational risk) are not
  adopted; the owner chose C.

### 6.4 Confirmation

- The owner explicitly selected option C.
- The owner explicitly chose to keep the numeric limits open.
- The owner confirmed the interim record above before it was written.
- No numeric limit in this entry was defaulted by the research agent.

---

## 7. D-05 — Venue and cost evidence standard

### 7.1 Owner answer

- **Chosen variant:** **Staged A + B** — Binance research proxy for research; Nobitex-specific
  measurement for execution.
- **Research data venue:** Binance — research only.
- **Execution venue:** Nobitex.
- **Nobitex access status:** unknown / open.
- The owner explicitly confirmed the Binance-research / Nobitex-execution split.

### 7.2 Implications

1. No live-decision feasibility claim may rest on the 26 bp Binance proxy.
2. Nobitex may be cheaper or more expensive than the proxy; only a measured study can establish
   which.
3. The Nobitex study is a prerequisite for the execution-cost evidence standard, not an
   authorization to trade.
4. If Nobitex access is unavailable, option B cannot be completed and D-05 must be revisited or the
   limitation explicitly accepted.
5. D-06 remains open and depends on this decision.

### 7.3 Required execution evidence

- dated fee schedule (maker/taker, tier, effective dates);
- measured bid-ask spread at decision and exit times;
- order-book depth and size-depth;
- slippage and fill evidence;
- latency;
- partial fills and rejections;
- entry/exit asymmetry;
- operational constraints.

The detailed checklist is in `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §7.1.

### 7.4 Qualifications and open items

- D-05 is resolved as to the venue split and the evidence standard.
- The Nobitex access status is **unknown/open**; if access cannot be obtained, this decision must be
  revisited.
- No market data was collected and no venue measurement was performed in Stage 2N.
- D-06 remains open.

### 7.5 Confirmation

- The owner explicitly selected the staged A + B variant.
- The owner explicitly confirmed Binance for research and Nobitex for execution.
- The owner explicitly recorded the Nobitex access status as unknown/open.
- No value in this entry was defaulted by the research agent.

---

## 8. D-06 — Cost-uncertainty and conservative-cost rule

### 8.1 Owner answer

- **Chosen option:** **A — Conservative primary.**
- **Conservative threshold:** **95th percentile (p95)** of the measured cost distribution.
- **Sensitivity reporting:** **mandatory.**
- **Optimistic-only pass:** **prohibited.**

### 8.2 Implications

1. The primary verdict uses the **p95** of the measured cost distribution, not the mean or the most
   favourable estimate.
2. This protects against optimistic cost assumptions and may reject a rule that would pass on the
   mean.
3. The cost range and sensitivity scenarios must be reported alongside the primary verdict.
4. A pass that depends **solely** on an optimistic cost scenario is prohibited.
5. The rule is fully specified but **cannot be applied** until a Nobitex cost distribution exists.
   Stage 2N does not collect or process that data.
6. D-05's Nobitex access remains open; if access cannot be obtained, D-06 remains defined but
   inapplicable to Nobitex evidence.

### 8.3 Qualifications and open items

- The rule is a decision rule, not a cost estimate. No cost data has been measured.
- D-06 is resolved as a decision rule, with application pending the Nobitex measurement.
- No candidate or experiment is authorized.
- D-06 does not resolve the Nobitex access question in D-05.

### 8.4 Confirmation

- The owner explicitly selected option A.
- The owner explicitly selected p95 as the conservative threshold.
- The owner explicitly made sensitivity reporting mandatory.
- The owner explicitly prohibited an optimistic-only pass.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 9. D-08 — Statistical confidence and error-control objective

### 9.1 Owner answer

- **Chosen standard:** **A + B combination** — two-sided significance for the primary test, plus
  power for the MME.
- **Two-sided `α`:** **5%**.
- **Target power:** **80%**.
- **Co-primary allocation:** **hierarchical** — the per-trade primary must pass first; the annual
  co-primary is tested conditionally.
- **Precision reporting:** required — the interval width must be reported.

### 9.2 Implications

1. The primary test uses a **two-sided 5%** error rate.
2. The design targets **80% power** for the MME. The numeric sample-size requirement depends on the
   MME value (D-01, currently open), the variance, and the dependence treatment (D-09).
3. The per-trade primary is tested **first**; the annual co-primary is tested **only if the primary
   passes**. This preserves the error rate and prevents a frequency-driven annual result from
   rescuing a failed per-trade result.
4. The confidence-interval width must be reported alongside the verdict.
5. The exact decision rule — for example, whether the lower confidence bound must be at or above the
   MME — is **not** separately decided here. It remains to be specified in D-10 or pre-registration.
6. D-08 cannot produce a sample size until D-01's numeric MME is set. Gate 2 therefore remains
   blocked despite D-08 being resolved.

### 9.3 Qualifications and open items

- No variance, sample size, or MME value is recorded as decided here. The `α` and power are decision
  inputs, not estimates from data.
- The hierarchical allocation is recorded; the exact test sequence and the treatment of the annual
  metric's dependence on the per-trade result remain to be specified operationally.
- D-08 is resolved as an error-control standard, not as a complete experimental design.

### 9.4 Confirmation

- The owner explicitly selected the A + B combination.
- The owner explicitly selected 5% two-sided `α`.
- The owner explicitly selected 80% power.
- The owner explicitly selected hierarchical co-primary allocation.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 10. D-09 — Dependence treatment and robustness standard

### 10.1 Owner answer

- **Primary treatment:** **C — cluster-robust plus block bootstrap.**
- **Requirement:** the two treatments must agree.
- **Disagreement rule:** **inconclusive** — not a pass and not a failure.
- **Diagnostics:** Kish and design effects are reported as descriptive only.
- **Episode definition:** open — to be fixed at pre-registration.
- **Block length / resampling scheme:** open — to be fixed at pre-registration.

### 10.2 Implications

1. Episode-clustered standard errors are the primary dependence treatment; the block bootstrap is a
   required sensitivity.
2. The two treatments must agree. If the conclusion changes between them, the result is
   **inconclusive** — it is not promoted to a pass and not recorded as a failure.
3. Kish and design effects are reported as **descriptive diagnostics**, not as the decision rule.
4. The episode definition and block length remain open. They must be fixed **before** any outcome is
   observed; choosing them after seeing results would invalidate the pre-registration.
5. D-10 will use the dependence treatment and design effect to inflate the sample-size requirement.
   D-09 resolves the treatment and robustness standard, not the numeric design effect.
6. D-01's numeric MME remains open, so Gate 2 remains blocked despite D-09 being resolved.

### 10.3 Qualifications and open items

- No episode definition, block length, design effect, or sample size is recorded as decided here.
- No data has been processed.
- The exact operational test sequence and the implementation of the agreement rule remain to be
  specified with D-10.

### 10.4 Confirmation

- The owner explicitly selected option C.
- The owner explicitly selected the inconclusive disagreement rule.
- The owner explicitly required descriptive Kish and design-effect reporting.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 11. D-10 — Sample-sufficiency methodology

### 11.1 Owner answer

- **Chosen methodology:** **A — power for the MME.**
- **Dependence inflation:** required — uses D-09's design effect / cluster-bootstrap treatment.
- **Execution-rate adjustment:** required — inflate the opportunity count for the fill/execution
  rate.
- **Sensitivity reporting:** required — report the requirement as a function of `DE`, `σ`, and `δ`.
- **Universal fixed count:** not adopted.
- **Numeric sample size:** pending D-01 MME value, variance, D-09 parameters, and fill rate.

### 11.2 Implications

1. The sample requirement is derived from **power for the MME**, using the D-08 settings (`α=5%`
   two-sided, 80% power, hierarchical co-primary).
2. The requirement is inflated for dependence using D-09's treatment, and adjusted for the
   execution/fill rate so the required number of **executed** trades is reached.
3. The requirement must be reported as sensitive to `DE`, `σ`, and `δ`; a single unqualified `N` is
   not sufficient.
4. No universal fixed count is adopted. The historical 150-event floor is **not** inherited.
5. The numeric sample size cannot be computed until D-01's MME value is set, a variance estimate
   exists, D-09's episode/block parameters are fixed, and a fill-rate estimate exists.
6. Gate 3 remains blocked until the numeric requirement can be derived.

### 11.3 Qualifications and open items

- D-10 resolves the methodology, not the number.
- No variance, design effect, fill rate, or sample size is recorded as decided here.
- The variance source/assumption and the exact dependence-inflation method remain to be specified
  at pre-registration.

### 11.4 Confirmation

- The owner explicitly selected option A.
- The owner explicitly required the execution-rate adjustment.
- The owner explicitly required sensitivity reporting.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 12. D-11 — Multiple-testing and selection policy

### 12.1 Owner answer

- **Chosen policy:** **A + D combination** — one pre-registered primary hypothesis per stage, plus
  OOS confirmation for promotion.
- **Multiple hypotheses:** **not permitted within a stage**.
- **Exploratory tests:** allowed but explicitly labelled exploratory.
- **Family correction:** not applicable under the no-multiple-hypotheses rule; a future change would
  require a new decision before outcomes.
- **OOS confirmation:** **required** for any promotion to a candidate.

### 12.2 Implications

1. Each stage tests **one** pre-registered primary hypothesis; every other test is labelled
   exploratory.
2. Multiple hypotheses within a stage are **not permitted**. If a future need arises, it requires a
   new owner decision and a new pre-registration — not an ad hoc addition.
3. Any promotion to a candidate requires **OOS confirmation**. D-12 will define how the OOS data is
   protected, accessed, and looked at.
4. No family-wise or false-discovery correction is adopted, because the no-multiple-hypotheses rule
   makes it inapplicable. If that rule is later relaxed, a correction policy must be decided
   **before** outcomes.
5. The historical pattern of changing the floor and selecting on frequency intuition is prohibited
   without a new pre-registration.
6. D-12 remains open; OOS confirmation is required in principle, but the access and protection
   policy is not yet set.

### 12.3 Qualifications and open items

- D-11 resolves the selection policy; it does not resolve the OOS access mechanics (D-12).
- No candidate or promotion is authorized.
- The definition of "exploratory" and the reporting format remain to be specified at
  pre-registration.

### 12.4 Confirmation

- The owner explicitly selected the A + D combination.
- The owner explicitly excluded multiple hypotheses within a stage.
- The owner explicitly required OOS confirmation for promotion.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 13. D-12 — Validation/OOS access and one-look policy

### 13.1 Owner answer

- **Chosen policy:** **A — strict one-look.**
- **Validation looks:** one.
- **OOS looks:** one.
- **Changes after a look:** none.
- **Access logging:** required — date, purpose, and result for every access.
- **Embargo between blocks:** required.
- **Additional looks:** only as a new, separately authorized stage with a new pre-registration.

### 13.2 Implications

1. Validation gets **one** look and OOS gets **one** look. No changes are permitted after either
   look.
2. Every validation and OOS access must be logged with date, purpose, and result.
3. An embargo separates the validation block from the OOS block.
4. Any additional look is a **new stage** with a new pre-registration — not a second look at the
   same data.
5. Reusing validation or OOS data converts it into development data and destroys its confirmatory
   status.
6. **Stage 2N has not spent any look and does not access validation or OOS data.** This entry sets
   the policy only.
7. D-11's OOS-confirmation requirement is operationalized by this policy.

### 13.3 Qualifications and open items

- The exact embargo duration and the logging format remain to be specified at pre-registration.
- No validation or OOS row has been read.
- The policy is a protection standard; it does not authorize a look.

### 13.4 Confirmation

- The owner explicitly selected option A.
- The owner explicitly required access logging.
- The owner explicitly required an embargo between blocks.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 14. D-13 — Independent audit standard

### 14.1 Owner answer

- **Chosen standard:** **B + E combination** — separate reviewer with no prior involvement, plus an
  external specialist for critical components.
- **Minimum reviewer:** a separate reviewer who did not design, implement, review, or report on the
  artifact.
- **Critical specialist:** external review of the cost model and statistical method, **required if
  feasible**.
- **Residual limitations:** disclosure required in every result.

### 14.2 Implications

1. Gate 4 requires a **separate reviewer with no prior involvement** in the design, implementation,
   review, or reporting of the artifact.
2. An **external specialist** reviews the cost model and the statistical method if feasible. If it
   is not feasible, the limitation must be recorded explicitly.
3. Any residual independence limitation must be **disclosed in every result**.
4. Stage 2L's self-review **cannot** satisfy Gate 4. A different model or a different conversation
   is not, by itself, independence.
5. Gate 4 cannot pass until the reviewer and specialist are identified and the audit is performed.
6. The standard applies **before** any historical performance result is accepted.

### 14.3 Qualifications and open items

- The reviewer's identity, the specialist's availability, and the feasibility of external review
  are not set.
- No audit has been performed.
- The documentation standard for proving "no prior involvement" remains to be specified.

### 14.4 Confirmation

- The owner explicitly selected the B + E combination.
- The owner explicitly required the external specialist if feasible.
- The owner explicitly required residual limitation disclosure.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 15. D-14 — Data representativeness requirements

### 15.1 Owner answer

- **Chosen option:** **C — regime coverage plus later-period confirmation.**
- **Regime coverage:** **all three** — volatility, trend, and liquidity.
- **Later-period confirmation:** the single D-12 OOS look.
- **Single-interval result:** provisional.
- **Structural-break analysis:** not adopted by this decision.

### 15.2 Implications

1. Extrapolation requires coverage across **volatility, trend, and liquidity** regimes.
2. Later-period confirmation uses the **single OOS look** protected by D-12. It is not an additional
   look; once spent, it cannot be reused.
3. A result based on a single development interval is **provisional**, not a basis for extrapolation.
4. Structural-break analysis (option D) is **not** required by this decision. If it is wanted later,
   it requires a new decision.
5. D-12's one-look policy governs the confirmation; D-14 does not create a second look.
6. D-05's Nobitex access remains open; if later-period data is unavailable, the confirmation cannot
   be completed.
7. Gate 1 and Gate 5 remain blocked until the data and venue evidence exists.

### 15.3 Qualifications and open items

- The numeric regime definitions are not set and must be fixed **before** outcomes.
- The later-period data source is not identified.
- No data has been processed.
- Structural-break analysis is not required, but the limitation of omitting it should be disclosed.

### 15.4 Confirmation

- The owner explicitly selected option C.
- The owner explicitly selected all three regimes.
- The owner explicitly selected the D-12 OOS look for later confirmation.
- The owner confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 16. D-15 — Future research direction (deferred)

### 16.1 Owner answer

- **Status:** **deferred** — not resolved.
- **No option selected.** None of A, B, C, D, or E was chosen.
- **Deferral condition:** D-15 will be revisited only after D-01 and D-02 are resolved and the
  Gate 0–4 work is complete.
- The owner explicitly chose to defer rather than to record a provisional preference.

### 16.2 Implications

1. No future research direction is authorized. Option A (status-quo stop) remains the operative
   posture by default, because nothing else has been approved.
2. Candidate A's control arm is **not** promoted. Option D is explicitly rejected by Stage 2C as a
   selectivity diagnostic, and no decision here changes that.
3. No A-family variant (option B), no different strategy family (option C), and no abandonment
   (option E) is authorized.
4. Deferring D-15 does not unblock any gate. The framework repair and the open numeric decisions
   still come first.
5. The deferral preserves owner optionality; it does not create an implicit preference for any
   option.

### 16.3 Qualifications and open items

- D-15 remains **open** in substance; deferral is a scheduling decision, not a resolution.
- D-01's numeric MME and D-02's numeric risk limits remain unset, and both are prerequisites for
  revisiting D-15.
- D-05's Nobitex access remains open; D-13's audit standard is set but no auditor is identified and
  no audit has been performed.
- No candidate, experiment, or implementation stage is authorized by this entry.

### 16.4 Confirmation

- The owner explicitly chose to defer D-15.
- The owner explicitly did not select any of options A–E.
- The owner confirmed the deferral condition (D-01/D-02 resolved, Gate 0–4 complete).
- No option in this entry was defaulted by the research agent.

---

## 17. What remains open and process status

**Decisions resolved or qualified:** twelve decisions have an explicit, confirmed owner answer —
D-03, D-04, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, and D-14. D-01 and D-02 have an
explicit owner answer at the level of definition/option only, with their numeric values still open.
D-15 is deferred and remains unresolved. No decision was defaulted.

**Still open:**

- **D-01** — definition A selected, numeric MME and annual target **not set**.
- **D-02** — option C selected, numeric drawdown, per-trade, tail, and liquidity limits **not set**.
- **D-15** — **deferred**, to be revisited after D-01 and D-02 are resolved and Gate 0–4 work is
  complete.

**Qualifications carried forward:**

- **D-04** — real-capital check remains open as a Gate 0 input.
- **D-05** — Nobitex access is unknown/open; the execution-cost evidence cannot be completed without
  it.
- **D-06** — the conservative p95 rule is defined but cannot be applied until a Nobitex cost
  distribution exists.
- **D-07** — the annual target depends on D-01.
- **D-08, D-09, D-10** — standards and methodology are set; numeric sample size and dependence
  parameters remain pending D-01 and data.
- **D-11, D-12, D-14** — policies are set; no look has been spent and no later-period data source is
  identified.
- **D-13** — the audit standard is set; no reviewer or specialist is identified and no audit has
  been performed.

**Gate status:** Gate 1, Gate 2, Gate 3, Gate 4, and Gate 5 remain blocked. No Stage 2O, candidate,
strategy, experiment, or implementation stage is authorized.

---

## 18. Integrity statement

- Stage 2M documents were not modified.
- No historical research artifact was modified.
- No market data, validation row, or out-of-sample row was accessed.
- No census, backtest, bootstrap, Monte Carlo, or optimization was run.
- No candidate, strategy, experiment, or implementation stage was authorized.
