# Stage 2I — Runner Readiness Test Report

**Stage:** 2I.
**Test date:** 2026-11-04.
**Scope:** loader-only data-contract, bounded-memory, entry-guard, and completeness tests. No strategy
condition was evaluated; no signal, opportunity, cost-feasible count, non-overlap selection, return,
or performance statistic was calculated.

**Environment:** Intel/Linux workstation, Python 3.12.14 in `.venv312`, 4 GiB target / 6 GiB hard
ceiling. Actual dataset files under `backend/data/datasets/`.

---

## 1. Files exercised

| timeframe | path | size (bytes) | SHA256 (computed) | matches freeze |
|---|---|---:|---|---|
| 5m | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | 256,461,100 | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | yes |
| 15m | `backend/data/datasets/BTCUSDT-15m-20210101-20260901.json` | 86,193,949 | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | yes |
| 1h | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` | 21,653,180 | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | yes |
| 4h | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | 5,455,039 | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | yes |

Hashes were recomputed by streaming 1 MiB byte chunks before parsing. No hash was derived by parsing
records.

---

## 2. Commands

```text
PYTHONPATH=.:backend .venv312/bin/python -m pytest stage2i_readiness/tests -q
PYTHONPATH=. .venv312/bin/python stage2i_readiness/run_loader_test.py \
    --output /tmp/stage2i/loader_test.json
PYTHONPATH=. .venv312/bin/python stage2i_readiness/run_loader_test.py \
    --output /tmp/stage2i/loader_test_run2.json
```

The first command reports **29 passed**. The loader-only test was run twice to check determinism.

---

## 3. Actual-dataset loader-only result

### 3.1 Per-file scan

| timeframe | records yielded in dev interval | records seen to boundary | before interval | duplicates | first open (ms) | last open (ms) | off-grid | invalid OHLC | unclosed | seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m | 367,563 | 367,564 | 0 | 0 | 1,609,459,200,000 | 1,719,791,700,000 | 0 | 0 | 0 | 17.26 |
| 15m | 122,522 | 122,523 | 0 | 0 | 1,609,459,200,000 | 1,719,791,100,000 | 0 | 0 | 0 | 5.84 |
| 1h | 30,634 | 30,635 | 0 | 0 | 1,609,459,200,000 | 1,719,788,400,000 | 0 | 0 | 0 | 1.44 |
| 4h | 7,662 | 7,663 | 0 | 0 | 1,609,459,200,000 | 1,719,777,600,000 | 0 | 0 | 0 | 0.36 |

The one extra record per file is the first record at/after `dev_end_ms`; only its `open_time` was
inspected, and its payload was not decoded. Last open times are all `< dev_end_ms`.

### 3.2 Timeframe alignment / bucket membership (bounded streaming comparison)

| lower → upper | upper buckets | complete buckets | gap-affected buckets | missing members | max missing | lower buckets without upper |
|---|---:|---:|---:|---:|---:|---:|
| 5m → 15m (expected 3) | 122,522 | 122,520 | 2 | 3 | 2 | 0 |
| 15m → 1h (expected 4) | 30,634 | 30,627 | 7 | 14 | 3 | 0 |
| 1h → 4h (expected 4) | 7,662 | 7,653 | 9 | 14 | 3 | 0 |

The gap-affected counts are consistent with the seven registered gaps. Missing 15m bars are absent
from the 15m file, so only two existing 15m buckets have a partial 5m membership. The 4h series is
supplied and exempt under M3; the 1h→4h comparison is a data-alignment check, not a 4h usability
rule.

### 3.3 Memory and batch measurements

| measurement | value |
|---|---:|
| baseline process RSS | 18,743,296 bytes (17.88 MiB) |
| hash-only peak RSS | 20,983,808 bytes (20.01 MiB) |
| peak process RSS (hash + parse + alignment) | **30,593,024 bytes (29.18 MiB) worst observed** |
| peak above baseline | 11,849,728 bytes (11.30 MiB) |
| 4 GiB target | 4,294,967,296 bytes |
| 6 GiB hard ceiling | 6,442,450,944 bytes |
| within 4 GiB target | **yes** |
| within 6 GiB hard ceiling | **yes** |
| configured batch/read size | 1,048,576 bytes (1 MiB) |
| largest raw object | 444 characters |
| maximum typed records held simultaneously | 1 |
| temporary disk used | 0 bytes |
| total wall time | 60.75 seconds (worst of repeated runs) |

Repeated runs measured a peak in the range **28.19–29.18 MiB**. `/usr/bin/time -v` independently
reported a maximum resident set size of **28,868 KiB** (29,560,832 bytes) on one run, matching that
run's in-process measurement. The conservative worst observed value is reported above.

### 3.4 Development-interval isolation

| check | result |
|---|---|
| OOS records yielded to the development stream | **0** |
| OOS payloads decoded | **0** |
| boundary `open_time` values inspected | 4 (one per file, for termination only) |
| every yielded `open_time_ms` inside `[dev_start_ms, dev_end_ms)` | yes |
| validation/OOS values used in any rule | no |

The loader terminates at the first record at/after `dev_end_ms`. It does not expose that record's
candle fields. No validation or OOS candle was used for any calculation.

### 3.5 Determinism

A second full run produced identical values for every deterministic field: same hashes, record
counts, first/last timestamps, boundary counts, alignment counts, and batch sizes. Only wall-clock
timings and peak RSS varied by measurement noise (RSS range 28.19–29.18 MiB). Deterministic content
is reproducible.

---

## 4. Unit-test results

Command: `PYTHONPATH=.:backend .venv312/bin/python -m pytest stage2i_readiness/tests -q` → **29 passed**.

### 4.1 Entry-boundary tests (K2)

All tests use the frozen interval `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.

| case | expected primary | observed |
|---|---|---|
| entry exactly at start (`dev_start_ms`) | accepted | accepted |
| entry immediately before start (`dev_start_ms - 1`) | `entry_outside_interval` | `entry_outside_interval` |
| entry immediately before end (`dev_end_ms - 1`) | accepted | accepted |
| entry exactly at exclusive end (`dev_end_ms`) | `entry_outside_interval` | `entry_outside_interval` |
| missing bar inside interval | `no_entry_bar` | `no_entry_bar` |
| missing bar outside interval | `entry_outside_interval` (secondary `no_entry_bar`) | `entry_outside_interval` |
| off-grid bar inside interval | `no_entry_bar` | `no_entry_bar` |
| zero open | `invalid_entry_price` | `invalid_entry_price` |
| zero/negative/equal-to-entry ATR | `invalid_stop` | `invalid_stop` |

The implementation evaluates the interval guard first, then presence/grid, then price/stop. It
returns a secondary label when an out-of-interval entry is also missing.

### 4.2 Completeness tests (N4)

| case | expected | observed |
|---|---|---|
| explicit `is_closed=True` | closed | closed |
| explicit `is_closed=False` | not closed | not closed |
| explicit `"True"` / `"False"` dataset strings | coerced correctly | coerced correctly |
| missing `is_closed` | schema error | schema error |
| null `is_closed` | schema error | schema error |
| numeric `is_closed` (1 / 0 / 1.0) | schema error | schema error |
| malformed `is_closed` (`"yes"`, `"malformed"`) | schema error | schema error |
| final incomplete candle (`"False"`) | represented as not closed | represented as not closed |

The production `CandleData` model was also checked: a **missing** field defaults to `True` (the N4
risk); a null field is rejected by pydantic. The runner does not use that default and requires an
explicit field. Missing or invalid completeness metadata therefore cannot silently turn an incomplete
candle into an eligible input in the runner-readiness loader.

### 4.3 Loader contract tests

| case | expected | observed |
|---|---|---|
| small array with a boundary record | only interval records yielded; stop at boundary | pass |
| duplicate `open_time` | keep first in file order | pass |
| unordered records | reject | pass |
| missing `is_closed` | reject | pass |
| streamed hash with different chunk sizes | identical hash | pass |

---

## 5. Candidate D cluster-diagnostic populations (K3)

Owner decision: **S7 primary; S6 and S9 also reported.** All three use the fixed protocol §3.1
clusters (maximal runs of usable 4h bars with `budget_ok == True`).

| population | definition | inclusion / exclusion | grouping key | missing grouping value | descriptive or inferential | independent sample size? |
|---|---|---|---|---|---|---|
| S6 | valid entry and stop, pre-cost-gate | includes S6 signals regardless of cost; excludes earlier rejections | Kish cluster, calendar month, calendar quarter, session id | reported as `unassigned`; never dropped | descriptive | **no** |
| S7 (primary) | cost-feasible, `cost_R <= 0.20` | subset of S6; still pre-dedup and pre-non-overlap | same | same | descriptive | **no** |
| S9 | canonical non-overlapping set, 24h greedy | subset of S8; excludes `non_overlap` rejections | same | same | descriptive | **no** |

Every table in a future census must state which population it uses. A single unlabelled "signals per
cluster" number is non-compliant.

**Kish interpretation.** The Kish value is a concentration diagnostic only. It is not a
serial-dependence estimator, not a definitive effective sample size of returns, and not proof of
independent observations. The `rho` values are assumed design-effect adjustments.

---

## 6. N3 — 5m dependency result

The frozen protocol's role table calls 5m "diagnostics only", but D §2.1 and protocol §1.3 make 5m
membership a bar-validity input: a 15m bar with fewer than 3 usable 5m members is partial and
unusable (unless 5m data is absent, in which case the check is skipped and recorded).

Result for runner readiness:

- 5m is treated as an **input** to 15m/1h membership validation and as a **validation source** for
  alignment, not as diagnostics-only.
- The 15m series remains the authoritative source of 15m OHLC; 5m does not rebuild it.
- The 4h series remains independently authoritative and is never rebuilt from 5m/1h.
- If 5m and 15m disagree, the 15m bar is marked partial/unusable under the membership rule and the
  disagreement is reported, not silently repaired.
- If 5m data were absent, the check is skipped and recorded, as D §2.1 states.
- Change proposal CP-1 corrects the stale role-table wording. The operative behaviour is unambiguous.

---

## 7. N4 — Completeness result

See §4.2. Missing, null, numeric, or malformed `is_closed` is rejected by the runner-readiness loader.
The frozen `CandleData` default remains a production-contract risk outside this runner; CP-2 proposes
hardening it separately. No frozen artifact was changed in Stage 2I.

---

## 8. N5 — Bounded-memory requirement result

The actual-dataset test used the required bounded loader and stayed far below the 4 GiB target
(worst peak 29.18 MiB). It did not parse validation/OOS payloads, did not evaluate candidate logic, and did
not count signals. The formal requirements are recorded in `RUNNER_READINESS_SPEC.md` §1.

---

## 9. Additional readiness checks

Status vocabularies are used exactly: **PASS**, **FAIL**, **NOT TESTED**, **NOT APPLICABLE**. A
successful loader test is not evidence that strategy logic is correct.

| check | status | evidence / limitation |
|---|---|---|
| timezone normalization | **PASS** | loader parses aware timestamps to integer UTC ms; actual files had zero off-grid timestamps |
| half-open interval enforcement | **PASS** | unit boundary tests and actual loader stop before `dev_end_ms` |
| completed-candle semantics (data contract) | **PASS** | explicit `is_closed` required; false rejected; no missing-field default used |
| completed-candle semantics (strategy rules) | **NOT TESTED** | would require the census runner; out of scope |
| look-ahead prevention (strategy logic) | **NOT TESTED** | no candidate condition evaluated in Stage 2I |
| higher-timeframe availability at decision timestamps | **NOT TESTED** | readiness spec states the rule; no strategy-level test run |
| deterministic ordering of equal timestamps | **PASS** | loader keeps first duplicate and rejects descending timestamps; unit test |
| duplicate timestamp handling | **PASS** | first kept, count recorded; actual files had zero duplicates |
| missing candle handling | **PASS** | gaps observed and classified as gap-affected; no synthesis in loader |
| segment-boundary behavior | **NOT TESTED** | requires the candidate runner's segment state machine |
| restart / checkpoint behavior | **NOT APPLICABLE** | no checkpoint requirement is frozen; single pass fits the memory budget |
| reproducible output generation | **PASS** | two actual-dataset runs produced identical deterministic fields |
| explicit development vs validation/OOS separation | **PASS** | 0 OOS records yielded; 0 OOS payloads decoded |
| strategy-level entry classification beyond the guard | **NOT TESTED** | only the shared guard was unit-tested; candidate predicates were not run |
| actual-dataset bounded-memory behavior | **PASS** | worst peak 29.18 MiB on the 256 MB 5m file |

---

## 10. Remaining limitations

1. The test is loader-only. It does not prove Candidate B or D strategy logic, look-ahead safety,
   segment state, or verdict calculations. Those remain untested until a separately authorized
   runner exists.
2. One boundary `open_time` per file is inspected to terminate the stream. Its candle payload is
   never decoded or exposed. This is the minimum read needed to enforce the half-open interval
   without a full-file pre-scan.
3. The production `CandleData.is_closed` default remains `True` outside the runner. CP-2 proposes a
   separate contract hardening; the frozen artifacts were not modified.
4. The 5m role-table wording is stale. CP-1 proposes a documentation-only correction; the operative
   rule is implemented as an input/validation dependency.
5. Venue costs remain a Binance proxy; no Nobitex execution measurement is claimed.
6. No census, signal count, backtest, or performance calculation was performed.
