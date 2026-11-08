# Stage 2K — Research Direction Comparison

**Status:** historical review and research design only.
**Date:** 2026-11-08.
**Scope:** compares the directions available after the four feasibility failures. It proposes no candidate,
runs no census, processes no market data, and computes no P&L, expectancy or optimisation.

This document does **not** make the decision. The decision is in
`STAGE2K_FINAL_RECOMMENDATION.md`. This document records the options, the criteria, the ordinal
scores, and the considerations that drive the ranking, so that the decision can be checked against
them.

---

## 0. What this document is and is not

It is a comparison of **research directions**, not of strategies. A direction is what the project
does next; a strategy is what it would test. The distinction matters here because the record's central
finding is that the project cannot yet tell whether it has a market problem or a framework problem
(`FAILURE_MODE_ANALYSIS.md` §9). Directions differ mainly in which of those two they address.

It is **not**:

- a new candidate specification, or a revision of any frozen one;
- a census, a feasibility count, or a re-count;
- an outcome study, a backtest, or an estimate of edge;
- an authorization to read validation or out-of-sample data;
- a Stage 2L plan.

Every quantitative statement below is quoted from a frozen artifact or is arithmetic on a quoted
value. Where Stage 2K computes something new (for example a detectable-effect figure), it is labelled
as Stage 2K arithmetic.

---

## 1. How the directions were generated

### 1.1 Constraints any direction must respect

| constraint | consequence for the comparison |
|---|---|
| Review-only authority | A direction cannot be executed inside Stage 2K; it can only be described, costed and scored |
| Frozen artifacts are immutable | No direction may propose editing a Stage 2A–2J artifact; the most it can do is supersede one by a new, separately authorized freeze |
| No validation or OOS use | Any direction needing data beyond 2021-01-01 → 2024-07-01 leaves the current authorization boundary |
| No Stage 2L | No direction may assume an outcome study is already permitted |
| Evidence labels | A direction's rationale must distinguish what the record establishes from what it assumes |

### 1.2 The generation rule

A direction qualifies only if it:

1. addresses at least one failure mode from the taxonomy in `FAILURE_MODE_ANALYSIS.md` §2;
2. is executable without altering a frozen artifact;
3. has a defined output that a later stage could audit.

Seven possibilities were generated first, then consolidated into five directions. The consolidation is
recorded in §6 so it can be challenged; it is not a claim that the five are exhaustive.

| id | possibility | becomes |
|---|---|---|
| P1 | Proceed to an outcome study on an existing candidate despite the floor | **D1** (with P2) |
| P2 | Lower the floor to fit the observed counts | **D1** |
| P3 | Relax the cost gate because the 26 bp proxy may be too high | **D2** |
| P4 | Re-run a censused candidate under a modified definition | **D3** (Candidate A only) |
| P5 | Verify venue cost and derive the sufficiency rule before deciding | **D2**, and the precondition for **D3** |
| P6 | Change the strategy family or the instrument | **D4** |
| P7 | Stop the direction and preserve the record | **D5** |

P1 and P2 consolidate because both are the same act — proceeding without a sufficiency rule — differing
only in whether the gate is formally amended. P3 does not stand alone because changing one input
without measuring it or replacing the decision rule is not a direction; it is an assumption change
inside D2. P4 survives only in the narrow form D3 because the record gives a specific reason to
revisit A and no comparable reason for B, C or D.

### 1.3 Evidence available to each direction

| direction | primary evidence base |
|---|---|
| D1 | The four census reports and the Stage 2J verdicts, which establish the counts |
| D2 | Stage 2D §9 (the 150 floor is underived); every candidate spec §0.1 (26 bp is a proxy); Stage 2J §4 (349 is a planning reference) |
| D3 | Stage 2C (A: 151 feasible, 71 canonical, 120h overlap removes 53%); Stage 2J A-related concentration diagnostics |
| D4 | The four failures, which say nothing about other families; Stage 2K synthesis §10 |
| D5 | The Stage 2J final decision and the four failed gates |

---

## 2. Scoring method

### 2.1 Criteria

Six criteria, each scored on a five-point **ordinal** scale. The scores are judgements about this
record, not measurements, and they are not commensurable across criteria.

| code | criterion | question it answers |
|---|---|---|
| **E** | Evidential support | Does the frozen record support this direction's premise? |
| **I** | Information gain | How much would the project learn per unit of work? |
| **C** | Effort and cost | How much work, data collection and elapsed time does it need? (high score = low effort) |
| **R** | Pre-registration safety | How low is the risk of post-hoc inference, HARKing or gate-moving? (high = safer) |
| **G** | Data and governance safety | How low is the risk of touching OOS data, frozen artifacts or unratified conventions? (high = safer) |
| **V** | Reversibility | How easily can the decision be undone if it proves wrong? |

### 2.2 Scale

| score | meaning |
|---:|---|
| 0 | contradicted by the record, or unacceptable on this criterion |
| 1 | weak / high cost / high risk |
| 2 | mixed / moderate |
| 3 | supported / low cost / low risk |
| 4 | directly supported / minimal cost / minimal risk |

### 2.3 Why there is no composite score

A single weighted total would require weights that encode a preference the owner has not declared —
how much information gain is worth how much governance risk. Averaging would launder that preference
into a number and make the ranking look empirical. Instead the comparison reports the six scores and
one **decisive consideration** per direction, and §5 states what would change the ranking.

**Verified fact:** nothing in this scoring is derived from a statistical model, a backtest or a
simulation. It is a structured judgement over the frozen record.
