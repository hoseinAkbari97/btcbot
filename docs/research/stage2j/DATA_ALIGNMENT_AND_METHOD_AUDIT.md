# Stage 2J — Data Alignment and Method Audit

**Stage:** 2J
**Scope:** gap-aware data alignment and implementation audit for the Candidate B and Candidate D
census. This is an audit of data preparation and rule execution, not an outcome analysis.

---

## 1. Alignment summary

| check | result |
|---|---|
| registered gap locations match the frozen manifest | pass |
| missing-bar totals match the freeze (5m 213, 15m 70, 1h 14) | pass |
| grid checks (no off-grid present bar) | pass |
| 4h boundary-hour alignment | pass |
| price tolerance checks (0.1% complete-bucket high/low/close) | pass |
| any price mismatch in a field the design reads | none |
| any volume mismatch under relative tolerance `1e-9` | none |
| alignment failure flag | clear |

Alignment is gap-aware. A bucket enters the mismatch denominator only when it is complete:

- a 4h bucket is complete only when all four 1h bars are usable;
- a 1h bucket is complete only when all four 15m bars are usable;
- a 15m bucket is complete only when all three 5m members are usable.

Gap-affected buckets are reported separately and do not contaminate the denominator.

---

## 2. Bucket reconciliation

| comparison | complete buckets | gap-affected buckets | high/low/close mismatches | volume mismatches |
|---|---:|---:|---:|---:|
| 15m from 5m | 122,510 | 82 | 0 | 0 |
| 1h from 15m | 30,625 | 23 | 0 | 0 |
| 4h from 1h | 7,649 | 1 non-exempt (+12 exempt) | 0 | 0 |

The 15m-from-5m comparison has 122,510 complete buckets and 82 gap-affected buckets. The
1h-from-15m comparison has 30,625 complete buckets and 23 gap-affected buckets. The 4h-from-1h
comparison has 7,649 complete buckets, 12 exempt gap-adjacent buckets, and one non-exempt
gap-affected bucket. Every mismatch count is zero.

Partial-bucket counts: 15m below 3 members: 82; 1h below 12 members: 23; 4h exempt: 12.

---

## 3. Registered gaps

Seven gap runs are present in the 5m and 15m series, and seven in the 1h series. The per-gap
missing-bar counts match the frozen manifest exactly:

| gap | 5m missing | 15m missing | 1h missing |
|---|---:|---:|---:|
| 1 | 15 | 5 | 1 |
| 2 | 18 | 6 | 1 |
| 3 | 30 | 10 | 2 |
| 4 | 56 | 18 | 3 |
| 5 | 54 | 18 | 4 |
| 6 | 24 | 8 | 2 |
| 7 | 16 | 5 | 1 |
| **total** | **213** | **70** | **14** |

The 4h series has no missing bars; the twelve registered gap-adjacent 4h buckets are supplied bars
and are retained under the M3 exemption.

---

## 4. The twelve exempt 4h buckets

The frozen manifest registers these gap-adjacent 4h open times:

| # | open time (UTC) |
|---:|---|
| 1 | `2021-02-11T00:00:00Z` |
| 2 | `2021-02-11T04:00:00Z` |
| 3 | `2021-03-06T00:00:00Z` |
| 4 | `2021-04-20T00:00:00Z` |
| 5 | `2021-04-20T04:00:00Z` |
| 6 | `2021-04-25T04:00:00Z` |
| 7 | `2021-04-25T08:00:00Z` |
| 8 | `2021-08-13T00:00:00Z` |
| 9 | `2021-08-13T04:00:00Z` |
| 10 | `2021-09-29T04:00:00Z` |
| 11 | `2021-09-29T08:00:00Z` |
| 12 | `2023-03-24T12:00:00Z` |

All twelve are present and usable in the supplied 4h series. They are excluded from the 4h-from-1h
tolerance denominator and reported separately. The primary path uses them as supplied.

### 4.1 Extra zero-volume-driven 4h bucket

The 4h-from-1h audit reports one non-exempt gap-affected bucket:
`2023-03-24T08:00:00Z`. It is caused by zero-volume 5m placeholders at `11:30`–`11:55`, which make
the `11:00` 1h bucket partial (6 of 12 usable members). The supplied 4h bar is itself present and
usable, so it remains in the primary series under the M3 exemption.

The non-decision 4h sensitivity excludes only the twelve registered buckets, not this extra
zero-volume-driven bucket. This is deliberate: the pre-registered sensitivity is defined over the
twelve registered gap-adjacent buckets.

---

## 5. 5m stream diagnostics

| quantity | value |
|---|---:|
| development 5m records | 367,563 |
| usable members | 367,532 |
| zero-volume placeholders | 31 |
| unclosed | 0 |
| off-grid | 0 |
| invalid OHLC | 0 |

The 31 zero-volume placeholders are not usable members. They are the reason for the partial 1h
bucket described above; they are not treated as missing bars and are not forward-filled.

---

## 6. Method audit

### 6.1 Candidate B

- Expansion, retest, resumption, and confirmation are evaluated on 1h bars in the frozen order.
- ATR is segment-scoped Wilder, seeded at local index 13; expansion is testable at local index 14.
- The 4h permission read is the most recent bar whose close is strictly before the signal instant.
- The active-episode slot absorbs later expansions (B-1); the absorbed count is 45.
- The touch phase rejects penetration greater than `0.50 * A_e` as `retest_too_deep`. A close below
  `L_e - 0.50 * A_e` would necessarily be the first touch with penetration greater than 0.50, so
  the missing explicit touch-phase `structure_broken` branch cannot admit a signal. The
  `structure_broken` label is emitted from the confirmation phase where it is reachable (8 events).
- Deduplication and non-overlap are applied only after the cost gate.
- Every stage identity reconciles; causality checks pass on all 32 pre-gate signals.

### 6.2 Candidate D

- Sessions are enumerated on the frozen UTC offsets; the 3,831 session count is asserted, not
  assumed.
- The measurement window is `b0..b7`; the entry bar is `b8`.
- The 1h `q` ATR is the stop distance; a missing or unusable `q` is `stop_atr_unavailable`.
- Session VWAP uses HLC3 and volume over the eight measurement bars. The frozen worked example
  reproduces `30,200.0` exactly in the test suite.
- The 4h budget read is the most recent bar whose close is strictly before the signal instant.
- The cost gate is applied to the valid entry/stop population; no stop is widened.
- `session_full_data` is a post-count diagnostic and never removes a signal.
- Every stage identity reconciles; causality checks pass on all 295 pre-gate signals.

### 6.3 Shared checks

- No candidate rule reads a validation or out-of-sample row.
- No rule uses a future bar: the 4h decision bar closes strictly before the signal instant, and
  the entry time is strictly after it.
- No parameter was tuned, swept, or changed after counting.
- No outcome, return, P&L, expectancy, drawdown, Sharpe, Sortino, CAGR, bootstrap, or Monte Carlo
  quantity exists in the output schema.

---

## 7. Reconciliation identities

Candidate B:

- `S3 = S4 + expansions_absorbed`
- `S4 = rejected_attempts + S7`
- `S7 = cost_gate + S8`
- `S8 = S9 + duplicate_entry`
- `S10 = S9 - non_overlap`

Candidate D:

- `S0 = S2 + measurement_window_incomplete`
- `S2 = S3 + threshold/ATR labels`
- `S3 = S4 + budget labels`
- `S4 = S5 + below_vwap`
- `S5 = S6 + entry labels`
- `S6 = S7 + cost_gate`
- `S7 = S8 + duplicate_session`
- `S8 = S9 + non_overlap`

All identities are true in the recorded run.

---

## 8. Method-audit conclusion

No material candidate-rule defect was found. The only implementation nuance is the touch-phase
`structure_broken` branch described in §6.1, which is logically subsumed by `retest_too_deep` and
cannot admit a signal. The alignment audit is clean in every field the design reads, and all
reconciliation identities pass.

This audit does not certify profitability. It certifies only that the frozen rules were executed
faithfully on the development interval and that the data-alignment evidence is internally
consistent.
