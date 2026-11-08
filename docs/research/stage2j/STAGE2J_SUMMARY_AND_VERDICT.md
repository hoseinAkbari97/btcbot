# Stage 2J — Summary and Verdict

**Stage:** 2J
**Candidates:** B and D
**Frozen baseline:** `docs/research/stage2e_v2/`, version `2.0.0`
**Development interval:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Cost proxy:** 26 bp round trip; gate `cost_R <= 0.20`
**Census code commit:** `bc1285c8277c37c93b76addfe83dcb50267c1f35`

---

## 1. Verdicts

| candidate | verdict | canonical `N` | `M_all` | concentration criterion |
|---|---|---:|---:|---|
| B | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** | 24 | 0.086505 | not met |
| D | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** | 34 | 0.322559 | met (design effect 3.93) |

Both verdicts are stated with the exact authorized vocabulary. Candidate D's concentration
criterion is also met, but `INSUFFICIENT OPPORTUNITIES` has higher pre-declared precedence, so that
is the recorded verdict.

---

## 2. Why each verdict

### Candidate B

- `N_nonoverlap = 24 < 150` (project floor): failed.
- `M_all = 0.086505 <= 0.20`: passed.
- Capital geometry: no cost-feasible signal above 100% notional.
- Concentration: largest cluster share 10.34% (< 50%) and design effect 1.69 (< 2.00): not met.
- Compliance: passed.

The sole insufficient-opportunity sub-condition is the project floor. The frozen tier label is
`FAIL` because `N < 349`.

### Candidate D

- `N_nonoverlap = 34 < 150` (project floor): failed.
- `M_all = 0.322559 > 0.20`: failed.
- Capital geometry: no cost-feasible signal above 100% notional.
- Concentration: largest cluster share 17.78% (< 50%) but design effect 3.93 (>= 2.00): met.
- Compliance: passed.

Two independent insufficient-opportunity sub-conditions are met: the opportunity floor and the
frozen cost-median condition. The frozen tier label is `FAIL` because both `N < 349` and
`M_all > 0.20`.

---

## 3. Opportunity counts and non-overlap

| candidate | unique cost-feasible | short horizon | **canonical** | long horizon |
|---|---:|---:|---:|---:|
| B | 29 | 24 h: 29 | **72 h: 24** | 120 h: 23 |
| D | 45 | 12 h: 36 | **24 h: 34** | 48 h: 27 |

Every pre-registered non-overlap variant is below the 150 floor. Non-overlap is a construction
rule, not an independence claim. The 349 independence-based planning reference is not a
requirement and is not a power result for this design.

---

## 4. Cost and capital

| quantity | B | D |
|---|---:|---:|
| `M_all` | 0.086505 | 0.322559 |
| `M_feasible` | 0.074808 | 0.165085 |
| feasible share | 0.906250 | 0.152542 |
| max `notional_pct` (verdict population) | 0.696012 | 0.760891 |
| capital violation | no | no |

Candidate D's pre-gate population is much more expensive relative to its stops: 250 of 295 pre-gate
sessions fail the 26 bp gate. Candidate B's pre-gate population is cheaper: 3 of 32 fail.

The 26 bp figure is a Binance proxy, not a verified Nobitex execution cost.

---

## 5. Cluster diagnostics

| quantity | B primary S8 | D primary S7 |
|---|---:|---:|
| population | 29 | 45 |
| non-empty clusters | 21 | 20 |
| all regime runs | 171 | 212 |
| largest cluster share | 0.103448 | 0.177778 |
| Kish `n_eff` | 17.163265 | 11.440678 |
| design effect | 1.689655 | 3.933333 |

The cluster diagnostics are descriptive. Kish is not an estimate of serial dependence and not a
definitive effective sample size. The design-effect screen is not a statistical test.

---

## 6. Compliance and alignment

All compliance checks pass for both candidates:

- frozen manifest, artefact, dataset, and dataset-manifest hashes match;
- the frozen manifest self-hash matches;
- the Stage 2H and Stage 2I hashes match;
- all stage identities reconcile;
- causality checks pass;
- interval isolation passes with zero out-of-sample payloads decoded;
- alignment has zero high/low/close or volume mismatches in complete buckets;
- the registered gap counts (5m 213, 15m 70, 1h 14) match the freeze;
- the twelve registered 4 h buckets are present and usable.

No change proposal was applied. No validation or out-of-sample row was read, decoded, sliced, or
summarised.

---

## 7. 4 h exemption sensitivity

The non-decision sensitivity excludes the twelve registered gap-adjacent 4 h buckets and breaks the
4 h ATR at them:

| quantity | B | D |
|---|---:|---:|
| cost-feasible | 22 | 28 |
| canonical non-overlapping | 18 | 22 |
| `M_all` | 0.093452 | 0.356311 |
| largest cluster share | 0.136364 | 0.250000 |
| design effect | 1.727273 | 3.428571 |

Neither verdict direction changes. The sensitivity never replaces the primary signal set or
denominator.

---

## 8. Execution and reproducibility

- Peak RSS: 551.793 MiB (target 4 GiB, ceiling 6 GiB).
- Wall clock: 99.137 s.
- 5m stream: 367,563 records, 367,532 usable members, 31 zero-volume placeholders.
- Two runs with the same code produced identical analytical JSON; `resources.json` differs by
  design and is excluded from identity.
- Stage 2J and Stage 2I tests: 105 passed.
- `ruff check`: all checks passed.
- All machine-readable outputs are under `docs/research/stage2j/machine_readable/`.

---

## 9. What this summary does not say

The census does not show that either candidate is profitable or unprofitable, that either has an
edge, or that either should be traded. It does not estimate win rate, expectancy, returns,
drawdown, Sharpe, Sortino, or any other outcome statistic. It does not treat non-overlapping
signals as independent observations. It does not establish that the 150 floor or the 349 reference
is a statistical requirement.

It shows only that, under the frozen rules and the development interval, neither candidate
produced enough cost-feasible, non-overlapping opportunities to proceed under the pre-registered
Stage 2J decision rule.

---

## 10. Artifact map

| artifact | purpose |
|---|---|
| `CANDIDATE_B_CENSUS_REPORT.md` | Candidate B counts, labels, cost, non-overlap, clusters, verdict |
| `CANDIDATE_D_CENSUS_REPORT.md` | Candidate D counts, labels, cost, non-overlap, clusters, verdict |
| `CANDIDATE_COMPARISON.md` | Side-by-side structural comparison |
| `CENSUS_METHODOLOGY_AND_EXECUTION.md` | Implementation, memory, determinism, reproduction |
| `DATA_ALIGNMENT_AND_METHOD_AUDIT.md` | Gap-aware alignment and method audit |
| `STAGE2J_FINAL_DECISION.md` | Decision record and stop point |
| `FREEZE_MANIFEST.json` | SHA256 manifest for the Stage 2J artifacts |
| `machine_readable/` | Preflight, alignment, candidate, verdict-input, run, and resource JSON |

Stage 2K was not started.
