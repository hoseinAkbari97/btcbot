# Stage 2I — Runner Readiness Specification

**Stage:** 2I.
**Status:** runner-readiness requirements only. No census is authorized by this document.
**Applies to:** a future, separately authorized Candidate B / Candidate D feasibility census governed
by `docs/research/stage2e_v2/` version `2.0.0`.
**Implementation:** `stage2i_readiness/` (loader, entry guard, tests, loader-only test runner).

This specification adds operational requirements. It does not change any frozen strategy definition,
parameter, cost assumption, interval, or verdict rule.

---

## 1. Bounded-memory requirements (N5)

| id | requirement |
|---|---|
| R1 | The 5m JSON file must never be passed to `json.load`, `json.loads` on the whole file, or any equivalent unrestricted full-file parse. |
| R2 | The top-level JSON array must be processed one record at a time with a bounded read buffer. The configured batch/read size is **1 MiB**. |
| R3 | At most **one typed candle object** may be retained per timeframe stream. Do not build a full in-memory list of `CandleData`/`Candle` objects for any timeframe. |
| R4 | Do not create an additional full-size in-memory copy of raw text, parsed records, or intermediate rows. Buffer compaction must discard consumed bytes. |
| R5 | Intermediate state must be bounded by the processing window, not by total dataset size: one current bucket, one current candle, one higher-timeframe current bar/window per consumer. |
| R6 | Target maximum process RSS is **4 GiB**; the hard ceiling is **6 GiB**. The runner must abort with a clear error if a configured memory ceiling is exceeded where the platform makes that check technically feasible. |
| R7 | The census must use the actual dataset for the loader-only proof. A small synthetic fixture is necessary for contract tests but is **not sufficient** evidence of bounded-memory behaviour. |
| R8 | Repeated executions on the same inputs must produce identical deterministic content. Timing and RSS values may vary and must be reported as measurements, not as frozen data. |

**Why 1 MiB is sufficient.** The largest observed record in the actual files is 444 characters. A
1 MiB buffer holds at least ~2,300 such records, but only one is decoded at a time. The buffer and the
current object are the only per-read allocations. 1 MiB is therefore large enough to amortise I/O and
small enough that a full-file copy is impossible.

**Memory growth.** Loader memory is `O(buffer + largest record + one bucket state + current higher-
timeframe window)`. It does **not** grow with total dataset size or with the number of records. The
actual-dataset test measured 28.19–29.18 MiB peak RSS across repeated runs while reading the
256,461,100-byte 5m file.

---

## 2. Data-access contract

A census may read only:

| timeframe | path | role |
|---|---|---|
| 15m | `backend/data/datasets/BTCUSDT-15m-20210101-20260901.json` | Candidate D signal and entry; Candidate B alignment input |
| 1h | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` | Candidate B signal/entry; Candidate D stop reference |
| 4h | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | B/D regime and volatility budget |
| 5m | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | 15m and 1h bucket-membership input; alignment checks |
| manifest | `backend/data/datasets/manifest.json` | identity and expected counts |

### 2.1 5m is an input, not "diagnostics only" (N3)

For Candidate D, a 15m bar is usable only if its 3-member 5m bucket is complete (unless the 5m series
is absent, in which case the check is skipped and recorded). Therefore 5m membership can remove a
15m bar and hence a session. The 5m series is:

- **an input** to 15m and 1h bucket-membership validation;
- **a validation source** for the gap-aware alignment checks;
- **not** an independent source of 15m OHLC values (the 15m bar is the supplied aggregate);
- **not** used to rebuild the 4h series, which is supplied and exempt under M3.

The stale role-table wording in protocol §1.1 is addressed by change proposal CP-1. The operative
rules in §1.3 and D §2.1 already determine the behaviour.

### 2.2 Identity and hash checks

Before any counting, the runner must:

1. recompute each dataset SHA256 by streaming bytes (do not parse to hash);
2. recompute each frozen artifact SHA256;
3. recompute the Stage 2G manifest self-hash;
4. abort as `INCONCLUSIVE` on any mismatch.

---

## 3. Development interval enforcement

Frozen interval: `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`, integer epoch milliseconds:

```
dev_start_ms = 1_609_459_200_000   # inclusive
dev_end_ms   = 1_719_792_000_000   # exclusive
```

Rules:

- parse timestamps to aware UTC and convert to integer epoch milliseconds before comparison;
- never compare ISO strings lexicographically;
- admit a record iff `dev_start_ms <= open_time_ms < dev_end_ms`;
- filter on candle **open** time, not close time;
- assert `min(open_time_ms) >= dev_start_ms` and `max(open_time_ms) < dev_end_ms` for every stream;
- no pre-development bar may be used for warm-up;
- no validation/OOS bar may complete, confirm, price, or label a development event.

### 3.1 Boundary isolation

The loader stops at the first record whose `open_time_ms >= dev_end_ms`. It inspects only that
record's `open_time` string to know it has reached the boundary; it does **not** decode or yield the
record's candle payload. In the actual-dataset test: OOS records yielded = 0, OOS payloads decoded = 0.

---

## 4. Candle completeness and typing rules (N4)

- The dataset stores prices, volumes, and counts as JSON strings and `is_closed` as `"True"`/`"False"`.
  The runner must coerce them before evaluating any rule.
- `is_closed` must be **present and explicit**. The runner accepts a JSON boolean or the exact dataset
  strings `"True"`/`"False"`. It rejects missing, null, numeric, and other malformed values with a
  schema error.
- The runner must **not** rely on `CandleData.is_closed: bool = True` for a missing field. That
  production default would silently turn an incomplete candle into a closed one.
- A record that cannot be coerced aborts the run as `schema_error`; it is not silently dropped.
- A bar is unusable if `is_closed != True`, volume/trade count is zero, its bucket is partial under
  the applicable rule, its OHLC is invalid, or it is missing/off-grid. The 4h supplied-bar exemption
  is the only timeframe-specific exception.
- Duplicate `open_time` values keep the first record in file order and count the rest.
- Missing bars are never synthesised, interpolated, forward-filled, or padded.

Change proposal CP-2 covers hardening the production model; it is not applied in Stage 2I.

---

## 5. Entry-classification precedence (K2)

The entry classifier must apply this order:

1. **Interval guard** on the expected entry open:
   `expected_entry_open_ms < dev_start_ms or expected_entry_open_ms >= dev_end_ms`
   → primary label `entry_outside_interval`.
2. **Presence / exact next-bar grid** for an in-interval timestamp:
   absent or not exactly the next bar → primary label `no_entry_bar`.
3. **Positive open** → `invalid_entry_price`.
4. **Valid stop** (`ATR > 0`, `stop > 0`, `D > 0`) → `invalid_stop`.

If the interval guard fires and the bar is also missing, the primary label remains
`entry_outside_interval`; `no_entry_bar` is recorded as a secondary reason. Entry-time validation uses
only properties knowable at the entry open; close-time properties are post-count diagnostics.

---

## 6. Higher-timeframe access and synchronisation

- Each timeframe is read as an independent chronological stream.
- A higher-timeframe value is available at decision instant `T` only when
  `close_time_ms <= T` (equality permitted).
- Entry uses the next bar's **open**, which is strictly later than the signal instant.
- The runner must retain only the current higher-timeframe bar/window needed by the consumer, not the
  full series.
- 4h labels must not be read before the 4h bar closes; 1h values must not be read before the 1h bar
  closes; 15m values must not be read before the 15m bar closes.
- Percentile windows are inclusive at the right edge because that 4h bar is closed at `T`, not
  because a different comparison operator is used.
- The stage-2I loader test verifies stream alignment and bucket membership only. It does **not**
  verify strategy-level look-ahead behaviour; that remains to be verified when the separately
  authorized runner is implemented.

---

## 7. Determinism and reproducibility

- Records are consumed in file order; duplicate timestamps keep the first.
- The loader rejects a record whose `open_time_ms` is lower than the previous admitted record.
- Equal-timestamp ordering must be deterministic: keep first in file order and sort equal entry
  timestamps by the candidate's stable key.
- The run must record its git HEAD, the SHA256 of the counting code, the frozen artifact hashes, and
  the dataset hashes in its output manifest.
- Outputs must be machine-readable and human-readable; counts must be reproducible from the same
  frozen inputs.
- Repeated loader executions must produce identical deterministic content. Only timing/RSS
  measurements may vary.
- Restart/checkpoint behaviour is **not specified** by the frozen protocol. A single development-
  interval pass is feasible within the measured memory budget; no checkpoint requirement is added.

---

## 8. Candidate D diagnostic populations (K3)

Cluster definitions are fixed by protocol §3.1: maximal runs of consecutive usable 4h bars with
`budget_ok == True`; `False`, `Unknown`, missing, or unusable bars break a run.

| diagnostic population | definition | inclusion/exclusion | grouping key | missing grouping value | interpretation |
|---|---|---|---|---|---|
| **S6 (primary? no — required view)** | valid entry and stop, pre-cost-gate | includes signals that later fail cost gate; excludes signals rejected before entry/stop | Kish cluster id / calendar month / quarter / session id | unassigned only if the signal has no cluster; reported as `unassigned`, never silently dropped | descriptive |
| **S7 (primary)** | cost-feasible, `cost_R <= 0.20` | subset of S6; still pre-dedup and pre-non-overlap | same | same | descriptive |
| **S9 (required view)** | canonical non-overlapping set, 24h greedy | subset of S8; excludes signals rejected by non-overlap | same | same | descriptive |

- Every cluster statistic must name its population (`S6`, `S7`, or `S9`).
- Calendar-month, calendar-quarter, and session-id views use the same population labels.
- Cluster count, median, p90, maximum, largest-cluster share, design effect, and `rho` sensitivity are
  descriptive concentration diagnostics.
- **Kish effective sample size is not a serial-dependence estimator and is not proof of independent
  observations.** It does not establish an independent sample size for returns. The `rho` values are
  assumed design-effect adjustments, not estimated dependence.
- No cluster diagnostic changes the verdict.

---

## 9. Resource ceilings and failure behaviour

| resource | requirement |
|---|---|
| process RSS target | `< 4 GiB` |
| process RSS hard ceiling | `< 6 GiB` |
| read buffer | `1 MiB` |
| typed records held | `1` per stream |
| temporary disk | `0` bytes for the loader-only test; any future spill must be declared and bounded |
| failure on ceiling | abort with an explicit error where technically feasible; do not silently continue |

Passing a synthetic fixture is not evidence for these ceilings. The actual-dataset test in
`RUNNER_READINESS_TEST_REPORT.md` is the required evidence.

---

## 10. Explicit non-goals

This specification does not authorize or describe:

- counting Candidate B or D signals;
- cost-feasible opportunity counts;
- non-overlap selection over real signals;
- expectancy, returns, P&L, drawdown, or any performance metric;
- Monte Carlo, bootstrap, or parameter optimisation;
- access to validation/OOS candles for strategy research;
- any change to a frozen Stage 2E/2F/2G/2H artifact.
