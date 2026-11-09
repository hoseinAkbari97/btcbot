# Stage 2L — Final Audit Report

**Stage:** 2L  
**Audit target:** Stage 2J Candidate B and Candidate D feasibility census implementation  
**Audit date:** 2026-11-09  
**Baseline branch / HEAD:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Census execution commit:** `bc1285c8277c37c93b76addfe83dcb50267c1f35`  
**Stage 2J artifact commit:** `737bf90f32b3c49f72008040696c07f9ce326d84`

## 1. Primary verdict

**SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED**

This is the single primary Stage 2L audit verdict. It is not a PASS, CONDITIONAL PASS, FAIL,
or INCONCLUSIVE finding about the implementation. It states that the audit was performed by
a party that participated in the prior Stage 2J implementation review and reporting work,
so arms-length independence was not achieved.

## 2. Executive summary

The Stage 2L audit traced the frozen Candidate B, Candidate D, and shared census
requirements into the `stage2j_census` implementation, recomputed the Stage 2J integrity
values, inspected the published machine-readable outputs at the aggregate level, and ran an
independent synthetic harness. The harness executed **98 checks, all 98 passed**, without
opening any repository market-data file.

The audit found **no CRITICAL and no MAJOR** defects. It found **six MINOR** findings and
**four OBSERVATION** items:

- the D capital-geometry verdict condition is narrowed to the cost-feasible population by
  pre-registration (L-001);
- the concentration FAIL criterion is a Stage 2J plan extension not present in the frozen
  verdict tables (L-002);
- entry validation checks presence, not same-usable-segment continuity (L-003);
- B's pre-touch deep break uses `retest_too_deep` rather than `structure_broken` (L-004);
- D's `budget_ok` is unnecessarily coupled to SMA/slope availability (L-005);
- the D report misattributes one extra non-exempt 4h bucket to the M3 exemption (L-006);
- the `rho=1` sensitivity uses the arithmetic mean cluster size, not the exact Kish weight
  (L-007);
- the recorded B `retest_timeout=0` is not independently reproduced (L-008);
- the determinism claim has no retained second-run artifacts (L-009);
- the code hash omits `freeze_verify.py` and test files (L-010).

None of these findings changes a Stage 2J verdict. Both candidates remain
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`. The Stage 2K decision to stop the current
strategy family remains in force.

## 3. Integrity and provenance results

| Check | Result |
|---|---|
| Stage 2J manifest self-hash | Recomputed and matched `d12de357a8032a123bd0efaea156f26aa71c707061204cc058011bbc4e5df96a` |
| Frozen Stage 2E v2 manifest self-hash | Recomputed and matched `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93` |
| Frozen Stage 2E v2 manifest file SHA256 | Matched the Stage 2J baseline value `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` |
| Stage 2J artifact hashes and byte counts | All matched |
| Stage 2J supporting-file hashes and byte counts | All matched |
| Census code hash | Matched the current repository files |
| Census execution commit | Recorded HEAD `bc1285c8277c37c93b76addfe83dcb50267c1f35` matched |
| Frozen specifications | Candidate B, Candidate D, and shared protocol matched the recorded hashes and were unmodified |
| Commit ancestry | Census execution and artifact commits are ancestors of the audit baseline |
| Code drift after census | No code difference in `stage2j_census`, `stage2i_readiness`, or `backend/app/schemas/market_data.py` between `bc1285c` and the baseline |

Integrity is strong for the analytical files. The reproducible-provenance gaps are narrower:
the determinism claim has no retained second-run artifacts (L-009), and the code identity
omits `freeze_verify.py` (L-010).

## 4. Specification and implementation results

| Audit question | Result | Findings |
|---|---|---|
| Are canonical epoch-millisecond timestamps, the half-open interval, and grid alignment implemented? | Yes. Synthetic boundary checks pass, including the `dev_end` exclusion and naive-timestamp rejection. | None |
| Is lookahead avoided in regime reads and entries? | Yes for the traced paths. Regime reads use the previous closed 4h bar; entries use the next bar's open, not its close. Synthetic boundary checks at 03:00/04:00/07:59/08:00 and the D session reads pass. | None |
| Are segments, Wilder ATR resets, and 4h warm-up handled correctly? | Yes for the exercised paths. Synthetic ATR reset and first-known-index checks pass. | L-005 (latent budget coupling) |
| Is gap-aware alignment correct? | Yes for the exercised path. The synthetic gap-affected bucket is excluded from the comparison denominator; the recorded audit has 7,649 complete, 12 exempt, and 1 non-exempt gap-affected bucket. | L-006 (report wording) |
| Are cost, stop, and capital arithmetic correct? | Yes. The 26 bp constant, stop arithmetic, and inclusive 0.20 gate pass. Capital geometry matches the recorded distributions. | L-001 (population narrowing) |
| Is non-overlap logic correct? | Yes. Exact 72h spacing is accepted; greedy selection compares against the last accepted signal; duplicate ties are deterministic. | None |
| Are concentration and statistical diagnostics correct? | Yes for the verdict screen. Exact Kish, design effect, and largest-cluster share match the synthetic values. | L-002 (added criterion), L-007 (rho mean) |
| Is the verdict logic faithful to the pre-registered plan? | Yes. Compliance gates, precedence, subconditions, and verdict names match. | L-001, L-002 |
| Are provenance and reproducibility adequate? | Partially. Hashes are strong; determinism and code coverage are incomplete. | L-009, L-010 |
