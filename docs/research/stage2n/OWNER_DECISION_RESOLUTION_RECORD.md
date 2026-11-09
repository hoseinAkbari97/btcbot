# Stage 2N — Owner Decision Resolution Record

**Stage:** 2N (owner decision resolution only)
**Status:** in progress. Only decisions explicitly answered and confirmed by the owner are recorded here.
**Date:** 2026-11-09 (UTC)
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
| D-01 | minimum meaningful effect | **OPEN** |
| D-02 | acceptable drawdown and risk | **OPEN** |
| D-03 | primary performance estimand | **OPEN** |
| D-04 | capital and execution context | **RESOLVED — RESEARCH LEG ONLY; REAL-CAPITAL CHECK OPEN** |
| D-05 | venue and cost evidence standard | **OPEN** |
| D-06 | cost-uncertainty and conservative-cost rule | **OPEN** |
| D-07 | annual contribution as a co-primary metric | **OPEN** |
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

## 3. What remains open

All other decisions, D-01, D-02, D-03, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13,
D-14, and D-15, remain open. The next decision in the proposed order is the coupled
D-03 / D-01 / D-07 economic-target cluster, followed by D-02.

---

## 4. Integrity statement

- Stage 2M documents were not modified.
- No historical research artifact was modified.
- No market data, validation row, or out-of-sample row was accessed.
- No census, backtest, bootstrap, Monte Carlo, or optimization was run.
- No candidate, strategy, experiment, or implementation stage was authorized.
