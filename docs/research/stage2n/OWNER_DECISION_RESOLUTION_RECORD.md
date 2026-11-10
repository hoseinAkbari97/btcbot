# Stage 2N — Owner Decision Resolution Record

**Stage:** 2N (owner decision resolution only)
**Status:** in progress. Only decisions explicitly answered and confirmed by the owner are recorded here.
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
| D-08 | statistical confidence and error-control objective | **OPEN** |
| D-09 | dependence treatment and robustness standard | **OPEN** |
| D-10 | sample-sufficiency methodology | **OPEN** |
| D-11 | multiple-testing and selection policy | **OPEN** |
| D-12 | validation/OOS access and one-look policy | **OPEN** |
| D-13 | independent audit standard | **OPEN** |
| D-14 | data representativeness requirements | **OPEN** |
| D-15 | revisit Candidate A's control or investigate a different family | **OPEN** |

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

## 9. What remains open

All other decisions, D-01, D-02, D-08, D-09, D-10, D-11, D-12, D-13, D-14, and D-15, remain open.
D-01 remains open with definition A selected and its numeric values unset. D-02 remains open with
option C selected and its numeric limits unset. D-05 is resolved as to the venue split and evidence
standard, with Nobitex access still open. D-06 is resolved as a decision rule, with application
pending the Nobitex measurement. The next group is Group C (D-08 through D-12, statistical
confidence, dependence, sufficiency, multiplicity, and validation access).

---

## 10. Integrity statement

- Stage 2M documents were not modified.
- No historical research artifact was modified.
- No market data, validation row, or out-of-sample row was accessed.
- No census, backtest, bootstrap, Monte Carlo, or optimization was run.
- No candidate, strategy, experiment, or implementation stage was authorized.
