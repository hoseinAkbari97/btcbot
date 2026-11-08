# Stage 2J — Final Decision

**Decision date:** 2026-11-08 (UTC)
**Stage:** 2J feasibility census
**Candidates:** B and D
**Frozen baseline:** `docs/research/stage2e_v2/`, version `2.0.0`
**Development interval:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Census code commit:** `bc1285c8277c37c93b76addfe83dcb50267c1f35`

---

## 1. Decision

Both candidates fail the pre-registered Stage 2J feasibility census:

| candidate | decision |
|---|---|
| B | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** |
| D | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** |

No candidate receives `FEASIBILITY PASS`. No candidate receives `INCONCLUSIVE — IMPLEMENTATION OR
DATA LIMITATION`; compliance and alignment passed for both.

Candidate D's concentration criterion is also met (Kish design effect 3.93), but the
`INSUFFICIENT OPPORTUNITIES` condition has higher pre-declared precedence and is independently met.
The decision therefore records the higher-precedence term for D.

---

## 2. Basis

### Candidate B

- Canonical 72 h non-overlapping opportunities: **24**, below the 150 project floor.
- Pre-gate median `cost_R`: **0.086505**, below the 0.20 condition.
- No capital-geometry violation.
- Concentration screen not met (largest share 10.34%, design effect 1.69).
- Compliance passed.

### Candidate D

- Canonical 24 h non-overlapping opportunities: **34**, below the 150 project floor.
- Pre-gate median `cost_R`: **0.322559**, above the 0.20 condition.
- No capital-geometry violation on the cost-feasible population.
- Concentration screen met (design effect 3.93); lower precedence than the opportunity failure.
- Compliance passed.

The 4 h supplied-bar exemption sensitivity preserves both verdict directions: B remains below the
floor; D remains below the floor and above the cost-median condition.

---

## 3. What this decision means

The census asked whether the frozen designs produce enough cost-feasible, non-overlapping,
deduplicated opportunities to justify proceeding. Under the pre-registered rule, neither does.

This is a **structural feasibility** decision. It is not a statement that either candidate is
unprofitable. The census observed no trade outcome and computed no P&L, return, expectancy, win
rate, drawdown, Sharpe, Sortino, CAGR, equity curve, bootstrap, Monte Carlo, or optimisation. It
does not establish an edge in either direction.

The 150 floor is a Stage 2C project choice, not a statistical standard. The 349 figure is an
independence-based planning reference, not a requirement and not a power result for this design.
Non-overlapping observations are not independent observations.

---

## 4. Change control

No frozen strategy parameter, signal rule, cost assumption, interval, population, or verdict
condition was changed during this census. The implementation choices fixed before counting were:

- **B-1:** regime-failed episode attempts still occupy the active slot and absorb later expansions.
- **C-1:** the capital-geometry verdict condition applies to the cost-feasible population.
- The 4 h supplied-bar exemption is used as ratified (M3); the non-decision sensitivity excludes
  the twelve registered gap-adjacent buckets and breaks the 4 h ATR at them.

No parameter tuning, sweep, threshold change, or post-count rule change occurred. No change
proposal CP-1…CP-5 was applied.

---

## 5. Stop point

**Stage 2K was not started.** No follow-on design, optimisation, backtest, paper trade, or live
trade is authorized by this decision.

Any next step that uses the development data for a new candidate, a new threshold, or a new
population would require a new pre-registration before counting. Reusing this census to select a
variant after seeing the counts would invalidate the pre-registration discipline.

---

## 6. Evidence

The decision is supported by:

- `CANDIDATE_B_CENSUS_REPORT.md`
- `CANDIDATE_D_CENSUS_REPORT.md`
- `CANDIDATE_COMPARISON.md`
- `DATA_ALIGNMENT_AND_METHOD_AUDIT.md`
- `STAGE2J_SUMMARY_AND_VERDICT.md`
- `CENSUS_METHODOLOGY_AND_EXECUTION.md`
- `machine_readable/candidate_b_census.json`
- `machine_readable/candidate_d_census.json`
- `machine_readable/verdict_inputs.json`
- `machine_readable/alignment_audit.json`
- `machine_readable/census_run.json`
- `machine_readable/resources.json`
- `FREEZE_MANIFEST.json`

All artifacts are committed under `docs/research/stage2j/` and their hashes are recorded in the
Stage 2J manifest.

---

## 7. Final statement

**Stage 2J is complete. Both Candidate B and Candidate D are recorded as `FEASIBILITY FAIL —
INSUFFICIENT OPPORTUNITIES` under the frozen rules and the pre-registered decision procedure.
Stage 2K is not started.**
