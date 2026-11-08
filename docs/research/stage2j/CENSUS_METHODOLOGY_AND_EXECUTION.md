# Stage 2J — Census Methodology and Execution

**Stage:** 2J
**Candidates:** B and D
**Frozen baseline:** `docs/research/stage2e_v2/`, version `2.0.0`
**Pre-registered plan:** `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md`
**Execution date:** 2026-11-08 (UTC)
**Census code commit used for the recorded run:** `bc1285c8277c37c93b76addfe83dcb50267c1f35`

This document records how the census was executed. It is an implementation and reproducibility
record, not a strategy result. No outcome, P&L, return, expectancy, drawdown, Sharpe, Sortino,
Monte Carlo, optimisation, parameter sweep, backtest, paper trade, or live trade was produced.

---

## 1. Frozen inputs and preflight

The runner re-verified, before counting:

- the frozen Stage 2E v2 manifest SHA256
  `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` and its canonical self-hash
  `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93`;
- all frozen artefact hashes (`CANDIDATE_B_SPEC.md`, `CANDIDATE_B_CONFIG.json`,
  `CANDIDATE_D_SPEC.md`, `CANDIDATE_D_CONFIG.json`, `SHARED_CENSUS_PROTOCOL.md`,
  `REMEDIATION_MATRIX.md`, `INDEPENDENT_REVIEW.md`);
- the Stage 2I manifest SHA256
  `a7a7df57ea19b550804f91767338902091826c0646277352a5d7bfbd3c81b294` and the Stage 2H audit
  SHA256 `c91a3486e26f06af7523d47aacfe4ee56ee6e88a12b6d2262aea191f5a3feddf`;
- the four dataset SHA256 values and the dataset-manifest SHA256
  `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25`;
- the development interval on every timeframe;
- that no change proposal CP-1…CP-5 was applied.

All checks passed. The full recheck is in `machine_readable/census_run.json` and
`machine_readable/preflight.json`.

Dataset hashes used:

| timeframe | SHA256 |
|---|---|
| 5m | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` |
| 15m | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` |
| 1h | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` |
| 4h | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` |

---

## 2. Interval and isolation

The analysis interval is half-open on candle `open_time_ms`:

`[1609459200000, 1719792000000)` = `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.

The bounded loader inspects only the `open_time` string of the first record at or after
`dev_end_ms`, then stops. That record's payload is never decoded. The recorded isolation checks
all pass:

- zero out-of-sample payloads decoded;
- at most one boundary open time inspected per stream;
- every stream stopped at the boundary;
- no out-of-sample record yielded;
- every yielded record is inside the development interval.

`census_run.json` records `validation_or_oos_accessed: false`, `oos_payloads_decoded: 0`, and
`signals_counted: true`.

---

## 3. Bounded-memory implementation

The 5m file (about 256 MB) is never passed to `json.load`, and no list of 5m candle objects is
built. The Stage 2I `iter_object_texts` / `iter_candles` loader reads with a 1 MiB buffer.

- 5m: one streaming pass retaining only per-bucket member counters and 15m aggregates.
- 15m / 1h / 4h: compact primitive arrays indexed by grid slot, not candle objects.
- At most one typed `Candle` object is held per active stream.
- Signal metadata is retained only for counted signals; no outcome field exists.
- No temporary spill file was used (`temporary_disk_bytes = 0`).

Measured on the recorded run:

| measurement | value |
|---|---:|
| peak RSS | 551.793 MiB |
| target | 4 GiB |
| hard ceiling | 6 GiB |
| wall clock | 99.137 s |
| maximum raw object size | 444 characters |
| typed records held per stream | 1 |

Peak RSS is about 13% of the 4 GiB target and about 9% of the 6 GiB ceiling. Timing and RSS are
measurements and are excluded from deterministic output identity.

Phase times from the recorded run:

| phase | seconds |
|---|---:|
| preflight (hashing) | 46.267 |
| 5m support | 35.033 |
| 15m/1h/4h series | 15.119 |
| 4h regimes | 1.920 |
| alignment | 0.349 |
| candidates | 0.107 |
| 4h exemption sensitivity candidates | 0.288 |
| analysis | 0.016 |

---

## 4. Data preparation

### 4.1 Usable 5m members

A 5m record is a usable member of its 15m/1h bucket only when it is on-grid, closed, has positive
volume and trade count, and has valid OHLC. The development interval contains 367,563 5m records,
367,532 usable members, and 31 zero-volume placeholders. The placeholders are not members. This is
why a bucket can be partial even when a record exists at every expected timestamp.

### 4.2 Partial buckets and segments

- 15m usability requires exactly 3 usable 5m members.
- 1h usability requires exactly 12 usable 5m members.
- 4h is used as supplied under the ratified M3 supplied-bar exemption.
- A missing or unusable bar breaks the segment; nothing is forward-filled or interpolated.
- Wilder ATR is segment-scoped with the frozen seed at local index 13.

Observed series:

| timeframe | present | usable | missing slots | partial | segments |
|---|---:|---:|---:|---:|---:|
| 15m | 122,522 | 122,510 | 70 | 12 | 8 |
| 1h | 30,634 | 30,625 | 14 | 9 | 8 |
| 4h | 7,662 | 7,662 | 0 | 0 | 1 |

The supplied 4h series has no missing, unclosed, off-grid, zero-volume, or invalid-OHLC record.

### 4.3 4h regime and budget

For a decision instant `T`, the 4h bar read is the most recent bar whose close is strictly before
`T`; on the aligned grid this is `floor(T, 4h) - 4h`. The 4h percentile uses the inclusive
540-bar ATR window, segment-aware. `SMA50` and the 24 h slope are admitted only when their windows
lie inside one usable segment.

Primary regime counts:

| series | true | false | unknown | maximal true runs |
|---|---:|---:|---:|---:|
| B `permission` | 1,826 | 5,284 | 552 | 171 |
| D `budget_ok` | 2,863 | 4,247 | 552 | 212 |

The first computable 4h state is at index 552 (`2021-04-03T00:00:00Z`), after the 540-bar
percentile warm-up. Warm-up losses are reported, not treated as failures.

---

## 5. Candidate implementation decisions

The census follows the frozen text and the pre-registered implementation choices. The two choices
that affect interpretation are:

- **B-1:** an episode whose 4h permission at `e` is false or unknown still occupies the active
  episode slot and absorbs later expansions until its structural end. It cannot advance past S5.
- **C-1:** the capital-geometry verdict condition is evaluated on the cost-feasible population
  (B S8, D S7); the pre-gate distribution is reported as a labelled diagnostic.

The B touch phase does not carry a separate explicit `structure_broken` check. Any close below
`L_e - 0.50*A_e` necessarily makes that bar the first touch with penetration greater than 0.50, so
the `retest_too_deep` branch already rejects it. The frozen label `structure_broken` is retained and
is emitted from the confirmation phase where it is reachable; no signal can be admitted through the
missing branch.

Candidate B uses 1 h bars; Candidate D uses 15m session bars and the 1h `q` ATR. Neither candidate
observes an outcome. The entry bar's close-time properties are checked only as diagnostics; the
frozen entry price is the entry bar open.

---

## 6. Aggregation

- Signal lists are sorted by entry time then key.
- Stage ladders and label counts reconcile by construction; every reconciliation identity is
  asserted and recorded.
- Cost sensitivity is computed on the same pre-gate population for 10, 26, 39, and 52 bp with the
  gate fixed at 0.20.
- Non-overlap is the frozen greedy algorithm on entry time, sorted by entry time then key,
  inclusive boundary.
- Cluster analysis uses maximal `True` 4h runs; false, unknown, missing, or unusable bars break a
  run. Kish is computed over non-empty clusters. The rho sensitivity is reported alongside it.
- Capital geometry uses `$10,000` equity and `$100` risk; the D holding window is entry to session
  end (6 h), with the 8 h session bound reported separately.
- No P&L, return, expectancy, drawdown, Sharpe, Sortino, CAGR, equity curve, bootstrap, or Monte
  Carlo statistic exists in the outputs.

---

## 7. Determinism

Two runs with the same code and HEAD were compared. The analytical outputs were byte-identical:

| file | SHA256 (identical across runs) |
|---|---|
| `alignment_audit.json` | `0205d76da6eecb1aa9f78a52d4bcb486c6d7ba0f993a02b29869edeaf275e099` |
| `candidate_b_census.json` | `a0c74d7d5124dc6afd7c11f5fcccd86e4bd76d363563597e616b11c997c69db7` |
| `candidate_d_census.json` | `cc9d0191b83b6d4a2bab4e5213dc72131c354217aa1c443eceb22f7402d0effa` |
| `verdict_inputs.json` | `100cfb496739b4610b27f52e20b1dbb000cde4170ba50a952c897e67c39de8f7` |
| `census_run.json` (recorded run at `bc1285c`) | `0c4005dfdb0abe19081ef411caa635faf324059fd6fa3208cf99653669778722` |

`resources.json` is excluded from the identity comparison because it contains wall time and RSS.
The two runs produced different `resources.json` hashes, as expected. `census_run.json` also
contains the run-time git state; two runs at the same HEAD were identical.

All JSON is written with sorted keys, indent 2, `allow_nan=False`, and a trailing newline.

---

## 8. Tests, lint, and formatting

Commands run from the repository root:

```
python -m pytest stage2j_census/tests stage2i_readiness/tests -q
ruff check stage2j_census
```

Results:

- `pytest`: 105 tests passed (Stage 2J and Stage 2I suites).
- `ruff check`: all checks passed.
- `ruff format --check`: reports formatting differences across the existing Stage 2J module set.
  Those differences predate this census increment; no mass reformat was applied because it would
  create unrelated churn and make the census diff harder to audit. New code follows the surrounding
  style and passes lint.

Focused tests added for this increment cover:

- the frozen Candidate D worked example VWAP `30,200.0` exactly;
- `compute_regime_4h(exempt_slots=...)` segment breaking, ATR reset, and percentile `Unknown`
  windows;
- D three-valued budget-state counts;
- secondary entry-diagnostic labels for B and D;
- the sensitivity block's labelling and primary-denominator separation.

---

## 9. Reproduction

From the repository root, with the frozen datasets present:

```
python -m stage2j_census.run_census \
  --output-dir docs/research/stage2j/machine_readable
```

The runner aborts with `INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION` on any preflight, hash,
schema, interval, alignment, causality, or reconciliation failure. The recorded run exited 0.

Machine-readable outputs:

- `preflight.json`
- `alignment_audit.json`
- `candidate_b_census.json`
- `candidate_d_census.json`
- `verdict_inputs.json`
- `census_run.json`
- `resources.json`

Human-readable outputs:

- `CANDIDATE_B_CENSUS_REPORT.md`
- `CANDIDATE_D_CENSUS_REPORT.md`
- `CANDIDATE_COMPARISON.md`
- `DATA_ALIGNMENT_AND_METHOD_AUDIT.md`
- `STAGE2J_SUMMARY_AND_VERDICT.md`
- `STAGE2J_FINAL_DECISION.md`
- `CENSUS_METHODOLOGY_AND_EXECUTION.md`
- `FREEZE_MANIFEST.json`

---

## 10. Limitations

- The 26 bp cost is a Binance proxy, not a verified Nobitex execution cost.
- The 150 floor is a project protocol choice, not a statistical standard.
- The 349 reference assumes independence and is not a power result for this design.
- Non-overlapping observations are not independent observations.
- Cluster diagnostics are descriptive, not dependence estimates.
- The census cannot establish profitability or an edge, and does not attempt to.
- No validation or out-of-sample row was read, decoded, sliced, or summarised.
