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

## 5. Findings and historical-conclusion impact

| Severity | Count | IDs |
|---|---:|---|
| CRITICAL | 0 | — |
| MAJOR | 0 | — |
| MINOR | 6 | L-001, L-002, L-003, L-006, L-009, L-010 |
| OBSERVATION | 4 | L-004, L-005, L-007, L-008 |
| **Total** | **10** | |

**Candidate B:** the recorded verdict is `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`
with `N_nonoverlap=24`, `M_all=0.086505387877563`, largest-cluster share `0.103448`, and
design effect `1.689655`. The findings do not change any of those inputs or the verdict.
The `retest_timeout=0` count is accepted as recorded but not independently reproduced
(L-008).

**Candidate D:** the recorded verdict is `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`
with `N_nonoverlap=34`, `M_all=0.32255940800148175`, largest-cluster share `0.177778`, and
design effect `3.933333`. The pre-gate capital diagnostic has 208 of 295 signals above
`notional_pct=1.00`, but the verdict population has none (L-001). The concentration
criterion is met but has lower precedence than insufficient opportunities (L-002). The
verdict is unchanged.

**Stage 2K:** the decision to stop the current strategy family remains in force. Stage 2L
does not promote a candidate, revise a verdict, or reopen candidate selection.

All ten findings are **open**. Stage 2L records them; it does not repair them.

## 6. What this audit does not establish

1. It does not establish independence. The primary verdict is
   **SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED**.
2. It does not establish that either candidate has an edge, is profitable, or is
   unprofitable. No P&L, return, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR,
   equity curve, bootstrap, Monte Carlo, optimisation, or backtest was computed.
3. It does not reproduce the historical census. Counts and labels are accepted only as
   hash-verified Stage 2J records.
4. It does not read, decode, slice, or summarise development, validation, or out-of-sample
   market rows.
5. It does not exercise every real-data interaction of gaps, partial bars, and regime runs.
   The synthetic checks are unit-level evidence.
6. It does not certify that the absence of CRITICAL or MAJOR findings is itself independent.
   A self-review can share the original implementer's blind spots.

## 7. Recommended follow-ups (not performed)

1. Commission an independent auditor to repeat the trace and synthetic checks without the
   prior Stage 2J involvement, and to decide whether the self-review limitations are
   acceptable.
2. In a future frozen specification, state the capital-geometry evaluation population in the
   verdict table, define the status of the concentration term, and resolve the entry
   presence-versus-same-segment rule.
3. Retain second-run digests or a determinism receipt, and add `freeze_verify.py` to the
   hashed code set.
4. Correct the extra-4h-bucket wording in a future note without rewriting the historical
   report.
5. If the historical `retest_timeout=0` count matters, authorise a separate reproduction;
   do not treat Stage 2L as that reproduction.

## 8. Completion and stop

The required Stage 2L deliverables are present in `docs/research/stage2l/`:

- `AUDIT_SCOPE_AND_INDEPENDENCE.md`
- `SPECIFICATION_IMPLEMENTATION_TRACE.md`
- `TECHNICAL_FINDINGS.md`
- `STAGE2L_FINAL_AUDIT_REPORT.md`
- `FREEZE_MANIFEST.json`

Supporting evidence is preserved in `synthetic_audit_checks.py` and
`SYNTHETIC_TEST_LOG.md`. The manifest records the hashes of the documents and evidence,
the source hashes, the synthetic-check result, and the audit confirmations.

No historical file, application file, frozen specification, dataset, or Stage 2J verdict
was modified. The census was not rerun, no detector was run on historical data, and no
performance metric was computed. The audit stops here. It does not repair the
implementation, rerun the census, revise a verdict, create a candidate, or start Stage 2M.

---

**Prepared by:** Big Pickle, self-review  
**Independence status:** not established  
**Primary verdict:** **SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED**
