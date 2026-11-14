# Stage 2ZC — Data Provenance and Quality Report

**Stage:** 2ZC (O-2A, Gate 1 research leg, development block only)
**Date:** 2026-11-14
**Scope:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` only
**Machine-readable source:** `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json`
**Reproduction command:** `python3 -m stage2zc_gate1.validate_dev_block`

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

All four already-recorded Binance BTCUSDT files match the recorded dataset manifest byte for byte, and
the development block passes every data-side check this stage was authorized to run: no duplicate,
off-grid, unclosed, invalid-OHLC, or non-positive-price bar; all seven registered gap runs account for
every missing bar and match the manifest totals; every zero-volume bar is a flat-price, zero-trade
outage placeholder; every close-time anomaly is earlier than its grid close and is localized at an
outage boundary; and lower-to-higher-timeframe reconciliation reports zero OHLC or volume mismatches in
all complete buckets. The development block has its own SHA-256 per timeframe, computed over the exact
JSON objects inside the interval. No validation or OOS row was decoded: the bounded loader inspected
only the `open_time` string of the first record at or after the development end. The report also
records two provenance limitations that no amount of checking can cure here: the exact extraction date
was not recorded, and the source is Binance, not Nobitex.

---

## 1. What is verified, and against what

| item | value |
|---|---|
| dataset manifest | `backend/data/datasets/manifest.json` |
| manifest bytes | 1,484 |
| manifest SHA-256 | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` |
| files checked | `BTCUSDT-{5m,15m,1h,4h}-20210101-20260901.json` |
| file-level hash procedure | SHA-256 over the complete file bytes, streamed in 1 MiB chunks |
| development-block hash procedure | SHA-256 over the UTF-8 bytes of each development-interval JSON object in file order, concatenated without separators |
| manifest comparison | every file SHA-256 equals the manifest entry |
| development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| development start / end as epoch ms | `1609459200000` / `1719792000000` |
| timezone | UTC throughout; every timestamp carries an explicit UTC offset |
| boundary handling | one record per file inspected for `open_time` only; payload decoded = 0 |
| validation or OOS rows decoded | **0** |

The full-file hashes are the manifest's identity for the downloaded files. The development-block hashes
are a separate identity for the subset this stage was allowed to read. They are not interchangeable,
and no earlier artifact records the development-block hashes.

---

## 2. Source and provenance

### 2.1 Source

| field | recorded value | status |
|---|---|---|
| provider | Binance Spot | **recorded by the prior project record**, not re-established from a provider receipt |
| endpoint named by the project catalogue | `GET https://api.binance.com/api/v3/klines` | **recorded** in `URL_CATALOG.md` §"GET https://api.binance.com/api/v3/klines" |
| endpoint actually used at extraction | not recorded per file | **UNKNOWN** |
| instrument | `BTCUSDT` | **verified** in every decoded record and in the manifest |
| market type | Spot | **recorded**, not independently verified from the file |
| timeframes | 5m, 15m, 1h, 4h | **verified** in every decoded record |
| coverage | `2021-01-01T00:00:00Z` to `2026-08-31T23:59:59.999Z` | **manifest** |
| extraction date | **not recorded** | **UNKNOWN** |
| extraction tool or code version | **not recorded** | **UNKNOWN** |
| provider checksum or signature | **none retained** | **UNKNOWN** |

The dataset files are ignored by Git (`backend/data/datasets/*.json`); only `manifest.json` is tracked.
The manifest itself was first committed on **2026-10-04** with the 15m, 1h, and 4h hashes, and the 5m
entry was added on **2026-10-21**. Those commit dates are upper bounds on when the hashes were recorded.
They are **not** the extraction date and do not establish it.

### 2.2 Field contract

Each JSON array element carries the following fields:

| field | example | used by this stage |
|---|---|---|
| `symbol` | `BTCUSDT` | yes, contract check |
| `timeframe` | `15m` | yes, contract check |
| `open_time` | `2021-01-01 00:00:00+00:00` | yes, grid and interval |
| `close_time` | `2021-01-01 00:14:59.999000+00:00` | yes, close-time check |
| `open`, `high`, `low`, `close` | decimal strings | yes, validity and reconciliation |
| `volume` | decimal string | yes, zero-volume and reconciliation |
| `trade_count` | integer string | yes, zero-volume explanation |
| `is_closed` | `"True"` / `"False"` | yes, completeness |
| `quote_volume` | decimal string | not read |
| `taker_buy_base_volume` | decimal string | not read |
| `taker_buy_quote_volume` | decimal string | not read |

The bounded loader rejects a missing or ambiguous `is_closed`; it does not inherit the production
model's default-to-true behaviour. This stage used the existing `stage2i_readiness.loader.iter_candles`
implementation, not the Stage 2J census series module, because the latter computes indicators and is
outside this authorization.

### 2.3 Provenance limitations

1. **Extraction date missing.** Protocol §4.2 asks for it. It is not present in the manifest, the
   datasets, or any committed record available to this stage. The first-commit dates bound when the
   hashes were recorded, not when the data were downloaded. This is a disclosed provenance gap, not a
   hash or quality failure.
2. **Binance is not the execution venue.** Prices, liquidity, spread, fees, and outages are Binance's.
   Nothing here establishes that Nobitex quoted the same prices, had the same liquidity, or was open
   at the same times. The dataset is valid **as a Binance research dataset**, not as evidence of
   Nobitex execution.
3. **Klines are not quotes.** These files contain aggregated OHLCV, not order-book snapshots, trades,
   or quotes. They cannot support spread, depth, fill, rejection, latency, or slippage measurement.
4. **No provider-side integrity proof.** The hashes prove that the local files are the files the
   manifest describes. They do not prove that Binance produced those bytes.
5. **Independent timeframes.** The 15m, 1h, and 4h files are supplied series, not mechanically derived
   from the 5m file by this stage. Their agreement in §5 is evidence of consistency, not proof of a
   single derivation path.
6. **`close_time` semantics.** Five bars per timeframe carry a `close_time` earlier than the scheduled
   grid close. The frozen census implementation does not read `close_time`; a future implementation
   that does must treat the field as truncated at an outage, not as the bar boundary.

---

## 3. File identity and development-block identity

| timeframe | file bytes | full-file SHA-256 | matches manifest | dev records hashed | dev bytes hashed | development-block SHA-256 |
|---|---:|---|---:|---:|---:|---|
| 5m | 256,461,100 | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | **yes** | 367,563 | 157,550,142 | `3807c367ebb081dc8e6c82f9fb332f8201af2e294ae4e5d612497a8454a1a18c` |
| 15m | 86,193,949 | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | **yes** | 122,522 | 52,952,573 | `6fab3a704fe23f65078a1d29cbd9021b32037d6f39e8b0280f04bcb5849e8775` |
| 1h | 21,653,180 | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | **yes** | 30,634 | 13,302,076 | `e90bdab27a362e2b12feb106c8e752ffaa09943b877cc810a712a78b013941eb` |
| 4h | 5,455,039 | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | **yes** | 7,662 | 3,351,701 | `5bea6343cf5653ee00c76a1a331d5e17bded591b08c51d995141afa37b893735` |

For every file the first record at or after `2024-07-01T00:00:00Z` was inspected for `open_time` only.
Its payload was not decoded and its bytes are not in the development-block hash.

---

## 4. Development-block counts

The expected grid is the number of timeframe slots in the half-open development interval. Rows that
exist but are not usable are zero-volume placeholders; they are counted separately and are not treated
as missing.

| timeframe | expected grid slots | yielded records | usable records | missing bars | zero-volume bars | first open | last open |
|---|---:|---:|---:|---:|---:|---|---|
| 5m | 367,776 | 367,563 | 367,532 | 213 | 31 | `2021-01-01T00:00:00Z` | `2024-06-30T23:55:00Z` |
| 15m | 122,592 | 122,522 | 122,512 | 70 | 10 | `2021-01-01T00:00:00Z` | `2024-06-30T23:45:00Z` |
| 1h | 30,648 | 30,634 | 30,632 | 14 | 2 | `2021-01-01T00:00:00Z` | `2024-06-30T23:00:00Z` |
| 4h | 7,662 | 7,662 | 7,662 | 0 | 0 | `2021-01-01T00:00:00Z` | `2024-06-30T20:00:00Z` |

For every timeframe, `yielded + missing = expected grid slots`, and `yielded - usable = zero-volume
bars`. No record was dropped for any other reason.

---

## 5. Registered gaps

All seven registered gap runs are present in the 5m, 15m, and 1h series. The 4h series has no missing
bar. Per-run missing-bar counts are identical across timeframes after aggregation, and the totals match
`manifest.json` exactly.

| run | first missing open (UTC) | 5m missing | 15m missing | 1h missing | 4h missing |
|---:|---|---:|---:|---:|---:|
| 1 | `2021-02-11T03:45:00Z` | 15 | 5 | 1 | 0 |
| 2 | `2021-03-06T02:00:00Z` | 18 | 6 | 1 | 0 |
| 3 | `2021-04-20T02:00:00Z` | 30 | 10 | 2 | 0 |
| 4 | `2021-04-25T04:05:00Z` | 56 | 18 | 3 | 0 |
| 5 | `2021-08-13T02:00:00Z` | 54 | 18 | 4 | 0 |
| 6 | `2021-09-29T07:00:00Z` | 24 | 8 | 2 | 0 |
| 7 | `2023-03-24T12:40:00Z` | 16 | 5 | 1 | 0 |
| **total** | | **213** | **70** | **14** | **0** |

Each run is a contiguous sequence of missing grid slots bounded by present bars. No run is open-ended at
the development boundary. `manifest_gap_count` and `manifest_gap_bars_total` match the observed counts
for every timeframe, so `unaccounted_gap_runs = 0`.

---

## 6. Quality checks

### 6.1 Per-timeframe summary

| check | 5m | 15m | 1h | 4h | result |
|---|---:|---:|---:|---:|---|
| duplicate `open_time` | 0 | 0 | 0 | 0 | pass |
| off-grid `open_time` | 0 | 0 | 0 | 0 | pass |
| `is_closed` false | 0 | 0 | 0 | 0 | pass |
| invalid OHLC | 0 | 0 | 0 | 0 | pass |
| non-positive price | 0 | 0 | 0 | 0 | pass |
| zero-volume bars | 31 | 10 | 2 | 0 | explained |
| zero-trade bars | 31 | 10 | 2 | 0 | explained |
| `close_time` earlier than grid close | 5 | 5 | 5 | 5 | explained |
| `close_time` later than grid close | 0 | 0 | 0 | 0 | pass |

### 6.2 Zero-volume bars

Every zero-volume bar is also zero-trade and flat-priced. The bars occur in exactly two runs per
timeframe, both at outage boundaries:

| run | timeframe | bars | price (all bars) | start open (UTC) | end open (UTC) |
|---|---|---:|---:|---|---|
| A | 5m | 17 | `44582.07` | `2021-02-11T02:20:00Z` | `2021-02-11T03:40:00Z` |
| A | 15m | 5 | `44582.07` | `2021-02-11T02:30:00Z` | `2021-02-11T03:30:00Z` |
| A | 1h | 1 | `44582.07` | `2021-02-11T03:00:00Z` | `2021-02-11T03:00:00Z` |
| B | 5m | 14 | `28080.0` | `2023-03-24T11:30:00Z` | `2023-03-24T12:35:00Z` |
| B | 15m | 5 | `28080.0` | `2023-03-24T11:30:00Z` | `2023-03-24T12:30:00Z` |
| B | 1h | 1 | `28080.0` | `2023-03-24T12:00:00Z` | `2023-03-24T12:00:00Z` |

The 4h series has no zero-volume bar because each 4h bucket contains at least one hour with volume. The
frozen census design labels these bars `zero_volume_bar` and treats them as unusable members
(`volume > 0` and `trade_count > 0` are required). They are **not** missing bars, **not** forward-filled,
and **not** deleted by this report.

### 6.3 `close_time` anomalies

Five bars per timeframe have a `close_time` earlier than the scheduled grid close. In every case the
delta is negative, so the bar closes **before** its grid end, never after it. The anomalies cluster at
the same outage boundaries as the zero-volume runs:

| open (UTC) | 5m delta (s) | 15m delta (s) | 1h delta (s) | 4h delta (s) |
|---|---:|---:|---:|---:|
| `2021-02-11T03:40:00Z` / `03:30` / `03:00` / `00:00` | -245.226 | -245.226 | -1,145.226 | -1,145.226 |
| `2021-04-25T04:00:00Z` | -241.853 | -841.853 | -3,541.853 | -14,341.853 |
| `2021-08-13T01:55:00Z` / `01:45` / `01:00` / `00:00` | -0.999 | -0.999 | -0.999 | -7,200.999 |
| `2021-12-24T04:55:00Z` / `04:45` / `04:00` | -5.637 | -5.637 | -5.637 | not present |
| `2023-03-24T12:35:00Z` / `12:30` / `12:00` | -18.353 | -318.353 | -1,218.353 | not present |
| `2021-04-20T00:00:00Z` (4h only) | not present | not present | not present | -7,200.000 |
| `2021-09-29T04:00:00Z` (4h only) | not present | not present | not present | -3,600.000 |

The pattern is consistent with a provider that timestamped the close at the last trade before an
outage rather than at the scheduled grid close. The frozen census implementation indexes bars by
`open_time` and does not read `close_time`; this stage's checks are therefore unaffected. The anomaly is
**explained and localized**, not ignored. A future implementation that reads `close_time` must not
assume it equals `open_time + timeframe`.

### 6.4 Segment boundaries

Contiguous segments are maximal runs of adjacent present grid slots. The 5m, 15m, and 1h series each
have **8 contiguous segments** and **7 segment boundaries**, exactly at the seven gap runs. The 4h
series is **one contiguous segment** because no 4h grid slot is missing. Partial buckets at segment
boundaries are excluded from reconciliation denominators by the complete-bucket rule in §7.

---

## 7. Lower-to-higher-timeframe reconciliation

Reconciliation is gap-aware: a bucket enters the mismatch denominator only when every lower-timeframe
member is usable. A bucket with any unusable member is reported as gap-affected and is not compared.
Aggregation uses the first member's open, the maximum high, the minimum low, the last member's close,
and the sum of volumes.

| comparison | members per bucket | complete buckets | gap-affected buckets | missing members | max missing per bucket | upper bucket missing | OHLC mismatch buckets | volume mismatches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m → 15m | 3 | 122,510 | 82 | 244 | 3 | 0 | **0** | **0** |
| 15m → 1h | 4 | 30,625 | 23 | 80 | 4 | 0 | **0** | **0** |
| 1h → 4h | 4 | 7,652 | 10 | 16 | 3 | 0 | **0** | **0** |

Price tolerance is relative `1e-3` (0.1%) on open, high, low, and close, the Stage 2J complete-bucket
tolerance. Volume tolerance is relative `1e-9`. Open, high, low, close, and volume mismatch counts are
each zero across every complete bucket.

### 7.1 Relationship to the Stage 2J audit

The 5m→15m and 15m→1h counts reproduce the Stage 2J audit exactly (122,510 / 82 and 30,625 / 23). The
1h→4h comparison differs in presentation, not in outcome:

| item | Stage 2J audit | this report |
|---|---|---|
| complete 4h buckets | 7,649 | 7,652 |
| exempt registered 4h buckets removed from denominator (M3) | 12 | 0 |
| non-exempt gap-affected 4h buckets | 1 | included in 10 gap-affected |
| gap-affected 4h buckets | 13 total, split 12 exempt + 1 non-exempt | 10 |
| 4h buckets accounted | 7,662 | 7,662 |
| mismatches | 0 | 0 |

The Stage 2J census removed the twelve registered gap-adjacent 4h buckets from the denominator under
its frozen M3 exemption. This Gate 1 check does not apply that census-specific exemption. It keeps every
bucket with four usable 1h members in the denominator; three of the twelve exempt buckets are complete
and therefore enter it, and the other nine join the one non-exempt bucket in the gap-affected count.
`7,649 + 3 = 7,652` and `12 - 3 + 1 = 10`. Both views account for all 7,662 buckets and both report zero
mismatches. The difference is a denominator convention, not a data disagreement.

---

## 8. Gate 1 data-side criteria

| criterion | result | evidence |
|---|---|---|
| every dataset hash matches the recorded manifest | **pass** | §3 |
| every registered gap is accounted for | **pass** | §5 |
| alignment mismatches in fields the design reads are zero | **pass** | §7 |
| development interval separated from validation and OOS | **pass with recorded limitation** | exact development boundary; remainder undecoded; internal split deferred to Gate 2 by protocol §8.2 |
| no validation or OOS row read during the gate | **pass** | boundary payload decoded = 0 |
| duplicate, off-grid, unclosed, invalid-OHLC, non-positive checks | **pass** | §6.1 |
| zero-volume and close-time anomalies explained, not ignored | **pass** | §6.2, §6.3 |
| segment boundaries accounted | **pass** | §6.4 |
| no signal, indicator, outcome, return, or P&L computed | **pass** | `prohibited_computations` all zero |

`all_required_checks_pass` is `true` in `DEV_BLOCK_VALIDATION.json`.

---

## 9. What this report does not establish

1. It does not establish Nobitex execution feasibility, liquidity, spread, depth, fills, or cost.
2. It does not establish that the Binance files are complete with respect to Binance. It establishes
   that they are internally consistent and match the recorded manifest.
3. It does not establish the extraction date, the extraction tool, or a provider-side checksum.
4. It does not read or characterize validation or OOS data.
5. It does not compute a signal, indicator, opportunity count, outcome, return, expectancy, or P&L.
6. It does not change any frozen rule, threshold, tolerance, dataset, or manifest.

---

## 10. Integrity of this report

1. Every count and hash in this report is taken from `DEV_BLOCK_VALIDATION.json`, produced by
   `stage2zc_gate1/validate_dev_block.py` over the committed files.
2. The validation script reuses the bounded, development-only loader from `stage2i_readiness`.
3. The script decodes no record at or after `2024-07-01T00:00:00Z`; it inspects one boundary
   `open_time` per file and stops.
4. No dataset file, manifest, frozen artifact, threshold, or tolerance was modified.
5. The Stage 2J census-specific M3 exemption is disclosed and not silently applied or rejected.

---

**Data-side result: PASS. Hash identity: PASS. Gap accounting: PASS. Alignment: PASS with zero mismatches. Provenance limitation: extraction date unrecorded. Execution-feasibility claim: none.**
