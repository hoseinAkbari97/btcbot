# Stage 2J — Candidate B and Candidate D Comparison

**Scope:** structural feasibility under the frozen Stage 2E v2 rules. This comparison does not
rank candidates by profitability, edge, win rate, or expected return. Neither candidate was traded,
and no outcome was observed.

**Development interval:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Cost proxy:** 26 bp round trip, gate `cost_R <= 0.20`
**Verdict vocabulary:** the four authorized Stage 2J terms only.

---

## 1. Verdict summary

| item | Candidate B | Candidate D |
|---|---|---|
| primary signal definition | 1 h expansion, retest, resumption, confirmation | 15 m intraday session, volatility budget, VWAP |
| canonical holding horizon | 72 h | 24 h |
| canonical non-overlapping opportunities `N` | **24** | **34** |
| project floor | 150 | 150 |
| `M_all` (pre-gate median `cost_R`) | 0.086505 | 0.322559 |
| frozen cost-median condition | `<= 0.20` | `<= 0.20` |
| capital-geometry violation | none | none |
| concentration criterion | not met | **met** (design effect 3.93) |
| compliance | passed | passed |
| **final verdict** | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** |
| frozen tier label | `FAIL` | `FAIL` |

Both candidates fail the project floor. Candidate D additionally fails the frozen cost-median
condition. Candidate D's concentration screen is also met, but `INSUFFICIENT OPPORTUNITIES` has
higher precedence, so that is the recorded verdict for both.

---

## 2. Stage counts are not directly comparable

The candidates count different objects. B's stages are 1 h bars and episode attempts; D's stages are
intraday sessions. The table is descriptive only.

| B stage | count | D stage | count |
|---|---:|---|---:|
| S1 usable 1h bars | 30,625 | S1 usable 15m bars | 122,510 |
| S2 expansion-testable | 30,513 | S2 signal-evaluable sessions | 3,829 |
| S3 expansion bars | 503 | S3 directional signals | 927 |
| S4 episode attempts | 458 | S4 budget-qualified | 332 |
| S5 regime-qualified attempts | 117 | S5 VWAP-valid | 296 |
| S6 structurally valid episodes | 34 | S6 valid entry/stop, pre-gate | 295 |
| S7 valid entry/stop, pre-gate | 32 | S7 cost-feasible | 45 |
| S8 cost-feasible | 29 | S8 deduplicated | 45 |
| S9 deduplicated | 29 | S9 canonical 24 h | 34 |
| S10 canonical 72 h | 24 | — | — |

B's conversion from expansion to feasible signal is relatively high once a valid episode exists
(S8/S7 = 0.906), but the absolute opportunity count is small because only 117 of 458 attempts are
regime-qualified and only 34 reach structural validity. D produces more raw and cost-feasible
signals, but its pre-gate cost median is much higher (0.323 vs 0.087) because its ATR-based stops are
small relative to the 26 bp proxy; 250 of 295 pre-gate sessions fail the cost gate.

---

## 3. Non-overlap and opportunity count

| horizon | B accepted / rejected | D accepted / rejected |
|---|---|---|
| short sensitivity | 24 h: 29 / 0 | 12 h: 36 / 9 |
| **canonical** | **72 h: 24 / 5** | **24 h: 34 / 11** |
| long sensitivity | 120 h: 23 / 6 | 48 h: 27 / 18 |

Both canonical counts are far below 150. Even the most permissive pre-registered non-overlap
sensitivity (B 24 h = 29; D 12 h = 36) is below the floor. Non-overlap is a construction rule, not
an independence claim.

---

## 4. Cost and capital geometry

| quantity | B | D |
|---|---:|---:|
| `M_all` | 0.086505 | 0.322559 |
| `M_feasible` | 0.074808 | 0.165085 |
| feasible share | 0.906250 | 0.152542 |
| design margin `0.15 - M_all` | +0.063495 | −0.172559 |
| max `notional_pct` on verdict population | 0.696012 | 0.760891 |
| capital violation | no | no |
| pre-gate signals above 100% notional | 0 of 32 | 208 of 295 |

Both candidates pass the capital-geometry condition on the cost-feasible population. Candidate D's
pre-gate diagnostic shows why the cost gate is doing most of the work: most pre-gate D signals would
require more than the stated equity at 1% risk. That diagnostic is not the verdict population.

---

## 5. Concentration diagnostics

| quantity | B primary S8 | B canonical S10 | D primary S7 | D canonical S9 |
|---|---:|---:|---:|---:|
| population | 29 | 24 | 45 | 34 |
| non-empty clusters | 21 | 21 | 20 | 19 |
| largest cluster share | 0.103448 | 0.083333 | 0.177778 | 0.176471 |
| Kish `n_eff` | 17.163265 | 19.2 | 11.440678 | 11.115385 |
| design effect | 1.689655 | 1.250000 | **3.933333** | 3.058824 |

B is not concentrated under the pre-declared screen. D is concentrated under the design-effect
component on both the primary S7 population and the canonical S9 sensitivity. The largest-cluster
share component is below 50% for both. These are descriptive diagnostics, not dependence tests and
not effective sample sizes for returns.

---

## 6. 4 h supplied-bar exemption sensitivity

| quantity | B sensitivity | D sensitivity |
|---|---:|---:|
| exempt slots | 12 | 12 |
| cost-feasible | 22 | 28 |
| canonical non-overlapping | 18 | 22 |
| `M_all` | 0.093452 | 0.356311 |
| `M_feasible` | 0.080522 | 0.171512 |
| largest cluster share | 0.136364 | 0.250000 |
| design effect | 1.727273 | 3.428571 |

Excluding the twelve registered gap-adjacent 4 h buckets and breaking the 4 h ATR at them lowers
both counts. Neither verdict direction changes. The sensitivity is non-decision evidence and never
replaces the primary signal set or denominator.

---

## 7. What the comparison does and does not show

It shows that, under the frozen rules and the development interval:

- neither candidate reaches the 150-opportunity project floor;
- Candidate D also fails the frozen cost-median condition at 26 bp;
- Candidate D's cost-feasible signals are more concentrated in a few 4 h budget runs;
- both candidates pass protocol compliance and the capital-geometry check on their cost-feasible
  populations.

It does **not** show that either candidate is profitable or unprofitable, that one has a larger
edge, or that either should be traded. The census observes no outcome. The 349 planning reference is
not a power result, the 150 floor is a project choice, and non-overlapping signals are not
independent observations.

Both verdicts are `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`. Stage 2K was not started.
