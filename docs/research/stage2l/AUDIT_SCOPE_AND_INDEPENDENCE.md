# Stage 2L — Audit Scope and Independence

**Stage:** 2L  
**Audit target:** Stage 2J Candidate B and Candidate D feasibility census implementation  
**Audit date:** 2026-11-09  
**Baseline branch / HEAD:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Audit status:** complete, self-review

## 1. Purpose

This document defines the scope, exclusions, evidence standard, and independence status of
the Stage 2L audit. The audit asks a narrow question: **did the Stage 2J implementation
faithfully execute the frozen Candidate B, Candidate D, and shared census specifications,
and are the resulting structural verdicts traceable and reproducible?**

The audit is not a new test of either trading hypothesis. It does not estimate an edge,
does not price a trade, and does not convert counts into a performance claim. Its product
is a finding set, a trace from written requirement to code, and exactly one primary audit
verdict.

## 2. Baseline and integrity state

The audit began from a clean working tree on `main` at
`69f78a8b14429b4d32daa54976653e3b51a832ec` (`stage2k: refresh the manifest after the
label note`), aligned with `origin/main`. The Stage 2J census was executed at
`bc1285c8277c37c93b76addfe83dcb50267c1f35`; the final Stage 2J artifacts were introduced
at `737bf90f32b3c49f72008040696c07f9ce326d84`. Both commits are ancestors of the audit
baseline, and the census package, readiness loader, and market-data schema have no code
difference between the execution commit and the audit baseline.

The following integrity facts were recomputed during Stage 2L:

| Check | Result |
|---|---|
| Stage 2J `FREEZE_MANIFEST.json` self-hash | `d12de357a8032a123bd0efaea156f26aa71c707061204cc058011bbc4e5df96a` — recomputed and matched |
| Frozen Stage 2E v2 manifest self-hash | `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93` — recomputed and matched |
| Frozen Stage 2E v2 manifest file SHA256 | `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` — matched the Stage 2J baseline record |
| Stage 2J artifact SHA256 and byte counts | All entries in `artifact_hashes` matched |
| Stage 2J supporting-file SHA256 and byte counts | All entries in `supporting_files` matched |
| Census code identity | Recorded per-file hashes and aggregate `code_sha256` matched the current repository files |
| Recorded census git HEAD | `bc1285c8277c37c93b76addfe83dcb50267c1f35` — matched the manifest |
| Frozen specification files | Candidate B, Candidate D, and shared protocol hashes matched the Stage 2J record and were not modified |

Integrity verification establishes that the audit inspected the same files that produced
the recorded census. It does **not** establish that the implementation is correct; that
question is addressed by the trace and the independent synthetic checks.

## 3. In scope

The audit covers the implementation path from frozen specification to recorded census
output:

1. **Frozen-specification fidelity** for Candidate B, Candidate D, and the shared census
   protocol, including labels, stage ladders, denominators, gates, and verdict terms.
2. **Temporal correctness and lookahead safety**: canonical epoch-millisecond timestamps,
   the half-open development interval, previous-closed-bar regime reads, confirmation
   sequencing, and entry-at-open execution.
3. **Data alignment and gap handling**: series construction, segment boundaries, Wilder ATR
   resets, warm-up windows, missing/partial/zero-volume bars, 4h regime construction, and
   the gap-aware upper-timeframe alignment denominator.
4. **Cost, stop, and capital arithmetic**: 26 bp cost, `cost_R`, the 0.20 gate boundary,
   stop distance and stop validity, and notional/equity geometry.
5. **Non-overlap and deduplication**: canonical horizons, inclusive boundary behaviour,
   greedy acceptance against the last accepted signal, and deterministic duplicate ties.
6. **Concentration and statistical diagnostics**: Kish effective sample size, design
   effect, largest-cluster share, `rho` sensitivity, quantiles, cost buckets, and the
   detectable-effect reference.
7. **Verdict logic**: compliance gates, precedence, the pre-registered concentration
   criterion, capital-geometry population, and the exact verdict names recorded.
8. **Reproducibility and provenance**: manifest hashes, code identity, deterministic-output
   claims, retained evidence, and the completeness of the recorded code set.

## 4. Out of scope and prohibited actions

The audit deliberately does **not** do any of the following:

- rerun the Stage 2J census or any detector over historical market data;
- run a backtest, paper trade, live trade, or any strategy simulation;
- compute P&L, returns, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR, an equity
  curve, or any other performance metric;
- run bootstrap, Monte Carlo, optimisation, parameter tuning, or model selection;
- read, decode, inspect, or summarise development, validation, or out-of-sample market
  rows beyond the already-published aggregate census evidence;
- modify historical Stage 2J files, application code, frozen specifications, the dataset
  manifest, or any Stage 2J verdict;
- create a new candidate, promote a candidate, or begin Stage 2M.

The audit does not repair the implementation. Findings are recorded; remediation is left
to a separately authorised stage.
