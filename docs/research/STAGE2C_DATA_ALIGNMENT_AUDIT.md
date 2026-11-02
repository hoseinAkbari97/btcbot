# Stage 2C — Data Alignment Audit

**Scope:** BTCUSDT spot, development interval `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.
**Purpose:** verify that the 5m, 1h, and 4h series used by the Stage 2C census are internally
consistent, that the 1h and 4h series are reconstructible from the 5m series, that higher-timeframe
labels are causal, and that every signal entry and stop is checkable.

This audit is part of the feasibility census. It does not compute P&L or access validation/OOS
observations. The full machine output is in `stage2c_census/census_result.json` under
`alignment`; the curated summary is in `docs/research/STAGE2C_FEASIBILITY_CENSUS.json`.

---

## 1. Verdict

**PASS WITH DOCUMENTED EXCEPTIONS.**

- Every mismatch is explained by a registered vendor gap, a zero-volume placeholder, or a field the
  Stage 2C design does not read.
- On the bars the design actually uses, the 1h `high`, `low`, and `close` fields and the 4h `close`
  field match the 5m reconstruction exactly.
- Every signal entry timestamp exists on the 5m grid and is the first 5m bar after the confirmation
  close.
- The structural stop recomputes exactly from the 1h bars for every trigger.
- The `cost_R` formula recomputes exactly for every trigger.
- Every 4h regime lookup uses a 4h bar that closed strictly before the 1h bar's open.

No condition was found that would make the census `INCONCLUSIVE`.

---

## 2. Method

The audit reconstructs each higher-timeframe bar from its constituent 5m bars:

- **1h bucket:** all 5m bars with the same `YYYY-MM-DDTHH` prefix.
- **4h bucket:** all 5m bars whose hour falls in the same four-hour block
  (`00/04/08/12/16/20`).

For each bucket it compares the vendor bar against the aggregate of its 5m members on `open`, `high`,
`low`, `close`, `volume`, `quote_volume`, `trade_count`, and `close_time`. It separately records
buckets built from fewer than the expected number of 5m members (12 for 1h, 48 for 4h), buckets
containing a zero-volume 5m member, and buckets whose final 5m member has zero volume.

The design reads only:

- 1h `high`, `low`, `close` (pullback, reference high, stop, confirmation);
- 4h `close` (regime).

Therefore a mismatch in a field the design does not read is documented but does not invalidate the
census; a mismatch in a field the design reads on a **usable** bar would.

---

## 3. 5m series

| item | value |
|---|---:|
| Bars in development interval | 367,563 |
| Expected on a complete 5m grid | 367,776 |
| Missing | 213 (0.058%) |
| Gap count | 7 |
| Duplicates | 0 |
| Off-grid timestamps | 0 |
| Unclosed bars | 0 |
| Out-of-order rows | 0 |
| Non-positive prices | 0 |
| Negative volume | 0 |
| Zero-volume / zero-trade bars | 31 |
| Flat bars (`high == low`) | 31 |

The 31 zero-volume bars form two runs, both adjacent to vendor gaps:

| run start | run end | bars |
|---|---|---:|
| `2021-02-11 02:20:00Z` | `2021-02-11 03:40:00Z` | 17 |
| `2023-03-24 11:30:00Z` | `2023-03-24 12:35:00Z` | 14 |

These are placeholder prices around a data outage, not traded prices. They are not synthesised or
forward-filled.

### 3.1 Gap register

| after | resumes at | missing 5m bars | missing minutes |
|---|---|---|---:|
| `2021-02-11 03:40:00Z` | `2021-02-11 05:00:00Z` | 15 | 75 |
| `2021-03-06 01:55:00Z` | `2021-03-06 03:30:00Z` | 18 | 90 |
| `2021-04-20 01:55:00Z` | `2021-04-20 04:30:00Z` | 30 | 150 |
| `2021-04-25 04:00:00Z` | `2021-04-25 08:45:00Z` | 56 | 280 |
| `2021-08-13 01:55:00Z` | `2021-08-13 06:30:00Z` | 54 | 270 |
| `2021-09-29 06:55:00Z` | `2021-09-29 09:00:00Z` | 24 | 120 |
| `2023-03-24 12:35:00Z` | `2023-03-24 14:00:00Z` | 16 | 80 |

The 5m gaps explain all 213 missing 5m bars. No gap is created by the reader; the reader stops at
the last development bar (`2024-06-30 23:55:00Z`) and never decodes the first out-of-window
observation.

---

## 4. 1h series

| item | value |
|---|---:|
| Bars in development interval | 30,634 |
| Expected on a complete 1h grid | 30,648 |
| Missing | 14 |
| Duplicates | 0 |
| Off-grid timestamps | 0 |
| Unclosed bars | 0 |
| Vendor bars with no 5m members | 0 |
| 5m buckets with no vendor 1h bar | 0 |
| Complete 1h buckets exact on all compared fields | 30,627 |
| Partial buckets | 7 |
| Partial buckets exact on used fields | 7 |
| Field mismatches on used fields (`high`, `low`, `close`) | 0 |
| Mismatches on usable 1h bars | 0 |
| Unusable 1h bars | 9 |
| Usable 1h bars | 30,625 |
| Contiguous 1h segments | 8 |

### 4.1 Missing 1h bars

Fourteen 1h bars are absent. They are the full hours covered by the seven 5m gaps; the missing hours
are not synthesised. A missing hour breaks the 1h segment.

### 4.2 Partial 1h buckets

Seven 1h buckets contain fewer than 12 of the expected 12 5m bars:

| 1h open | reason |
|---|---|
| `2021-02-11 03:00:00Z` | gap-adjacent; also zero-volume |
| `2021-03-06 03:00:00Z` | gap-adjacent |
| `2021-04-20 04:00:00Z` | gap-adjacent |
| `2021-04-25 04:00:00Z` | gap-adjacent |
| `2021-04-25 08:00:00Z` | gap-adjacent |
| `2021-08-13 06:00:00Z` | gap-adjacent |
| `2023-03-24 12:00:00Z` | gap-adjacent; also zero-volume |

All seven are exact on the fields the design reads (`high`, `low`, `close`). They are nevertheless
excluded from the 1h signal stream because a partial hour is not a complete hour of price action.
Excluding them is conservative: it removes a few gap-adjacent signals rather than allowing a
confirmation or stop to be set from an incomplete hour.

### 4.3 Zero-volume 1h bars and unusable set

Two 1h bars are zero-volume placeholders:

- `2021-02-11 03:00:00Z`
- `2023-03-24 12:00:00Z`

Both are also partial. In addition, two complete 1h bars are unusable because their **final 5m
member** has zero volume, which would make the 1h close a placeholder rather than a traded price:

- `2021-02-11 02:00:00Z` (`last_member_zero_volume`)
- `2023-03-24 11:00:00Z` (`last_member_zero_volume`)

The nine unusable 1h bars decompose as:

| reason set | bars |
|---|---:|
| `partial` only | 5 |
| `last_member_zero_volume` only | 2 |
| `zero_volume + partial + last_member_zero_volume` | 2 |
| **Total** | **9** |

The eight contiguous segments (usable 1h bar counts) are:

`986, 549, 1078, 119, 2633, 1128, 12986, 11146` — total `30,625`.

The EMA20 is re-initialised at the start of every segment and needs 20 bars of that segment. A
pullback cannot span a segment break; an open episode is closed without a signal at the break and is
counted as `segment_break`. The census records 7 such episode terminations.

---

## 5. 4h series

| item | value |
|---|---:|
| Bars in development interval | 7,662 |
| Expected on a complete 4h grid | 7,662 |
| Missing | 0 |
| Duplicates | 0 |
| Off-grid timestamps | 0 |
| Unclosed bars | 0 |
| Vendor bars with no 5m members | 0 |
| 5m buckets with no vendor 4h bar | 0 |
| Complete 4h buckets exact on all compared fields | 7,650 |
| Partial buckets | 12 |
| Partial buckets exact on `close` | 12 |
| Field mismatches on `close` | 0 |
| Mismatches on usable 4h bars | 0 |
| Usable 4h bars | 7,662 |

### 5.1 Partial 4h buckets

Twelve 4h buckets straddle the registered 5m gaps and are built from fewer than 48 5m members. They
occur at:

`2021-02-11 00:00`, `2021-02-11 04:00`, `2021-03-06 00:00`, `2021-04-20 00:00`,
`2021-04-20 04:00`, `2021-04-25 04:00`, `2021-04-25 08:00`, `2021-08-13 00:00`,
`2021-08-13 04:00`, `2021-09-29 04:00`, `2021-09-29 08:00`, `2023-03-24 12:00`.

All twelve are exact on `close`. They are retained for the slow 4h regime filter: the regime uses
the vendor close, which is a real last-trade price, and twelve partial buckets cannot determine a
200-bar mean. The audit records them but does not force a segment break in the 4h series.

### 5.2 Single `open` mismatch

One field mismatch exists:

| bucket | field | vendor | reconstructed from 5m | 5m members |
|---|---|---|---:|---:|
| `2023-03-24T3` (12:00–15:59Z) | `open` | `28079.99` | `28080.00` | 32 |

The design does not read 4h `open`; it reads 4h `close`, which is exact. The mismatch is therefore
documented and has no effect on any regime label. It is the same open-tick discrepancy recorded in
the Stage 2A alignment audit.

---

## 6. Cross-timeframe and causal checks

### 6.1 Regime timing

For a 1h bar opening at `T`, the regime lookup uses the most recent 4h bar whose `close_time` is
strictly before `T`. Because the 4h grid is aligned to the 1h grid, that is the 4h bar opening at
`floor(T, 4h) - 4h`. The census asserts both:

```
last_4h_open + 4h <= T
vendor_4h_close_time < T
```

No 4h label is read before the 4h bar closes. The first valid regime label is at 4h bar
`2021-02-06T12:00:00Z`, closing `2021-02-06T15:59:59.999Z`; the first 1h bar allowed to use it opens
`2021-02-06T16:00:00Z`.

### 6.2 Entry timing

For every confirmed trigger, the entry is the open of the 5m bar at
`open_time[confirmation] + 1h`. The census verifies:

- the entry timestamp exists on the 5m grid;
- it is exactly one hour after the confirmation bar's open;
- it is exactly one millisecond after the confirmation bar's `close_time`;
- it is not a later bar chosen after a gap;
- the entry bar is closed, traded (`volume > 0`, `trade_count > 0`), and has a positive open.

All 195 primary and 445 control triggers passed these checks. No trigger used a forward-filled or
synthesised entry bar.

### 6.3 Stop and cost

For every trigger, the census recomputes the structural stop as the minimum 1h low from the
crossunder bar through the confirmation bar, inclusive. It matches the state-machine stop for every
trigger. It also recomputes:

```
cost_R = 0.0026 * entry_open / (entry_open - stop)
```

and matches the reported value to machine precision. The 0.20 gate is exactly equivalent to a stop
of at least 1.30% of entry at 26 bp: 44 of 195 primary triggers have a stop below 1.30%, and the same
44 have `cost_R > 0.20`.

---

## 7. Warm-up and exclusions

| item | value |
|---|---:|
| 4h regime warm-up (SMA200 + 20-bar slope) | 219 bars |
| First valid 4h regime label | `2021-02-06T12:00:00Z` |
| First 1h bar allowed to use a regime label | `2021-02-06T16:00:00Z` |
| 1h EMA warm-up | 20 bars per segment |
| 1h segments | 8 |
| Usable 1h bars | 30,625 |
| Primary active window | `2021-02-06T16:00:00Z` → `2024-06-30T23:59:59.999Z` |
| Primary active years | 3.396 |

No pre-development bar is used for warm-up. The 4h warm-up excludes the first 219 4h bars from
regime labelling; the 1h EMA warm-up excludes the first 20 bars of every segment. Both exclusions
are reported rather than hidden. The control arm does not need the 4h warm-up, but it is also
reported on the matched window beginning at the first regime label, so the regime contrast is not
confounded by a longer control window.

---

## 8. Signal-level verification summary

| check | result |
|---|---|
| Entry timing equals confirmation close + 1 ms | PASS (all 445 unique confirmed triggers; primary is a subset) |
| Entry timestamp exists on the 5m grid | PASS (all 445) |
| Stop recomputes from 1h bars | PASS (all 445) |
| `cost_R` recomputes from entry and stop | PASS (all 445) |
| Entry timestamps unique | PASS |
| 4h close strictly before 1h open | PASS (asserted on every lookup) |
| Primary is a strict subset of control | PASS |
| Episode funnel accounting | PASS (`445 + 170 + 22 + 7 = 644`) |

The verification is run on the shared LTF stream (445 confirmed triggers). The 195 primary triggers
are a subset of those 445, so the same checks cover both arms.

---

## 9. Exceptions and residual risks

1. **5m vendor gaps.** Seven gaps, 213 missing bars. They are acknowledged and never filled. Entry
   bars are looked up by exact timestamp; a missing entry bar would reject the signal. No trigger in
   this run hit a missing entry bar.
2. **Zero-volume placeholder runs.** Two runs of 5m zero-volume bars and four 1h bars whose final
   5m member is zero-volume (two complete, two partial) are excluded from the 1h signal stream. This
   is conservative.
3. **Partial 1h buckets.** Seven gap-adjacent partial 1h bars are excluded even though their used
   fields match. This avoids setting a confirmation or stop from an incomplete hour.
4. **Partial 4h buckets.** Twelve gap-adjacent partial 4h buckets are retained for the slow regime
   filter because their `close` is a real last-trade price and the filter is a 200-bar mean.
5. **One 4h `open` mismatch.** Documented; `open` is not read.
6. **The 1h/4h vendor series are not independent sources.** The audit reconstructs them from 5m;
   it does not prove that the vendor generated them correctly. It proves that the values the design
   reads are consistent with the 5m tape and with the vendor's own timestamps.
7. **No order-book or trade-level fill model.** The entry is a bar open, not a measured fill. The
   cost model is a proxy. This is a feasibility census, not an execution study.

---

## 10. Artifacts

- Machine alignment output: `stage2c_census/census_result.json` → `alignment`
- Curated summary: `docs/research/STAGE2C_FEASIBILITY_CENSUS.json` → `data_alignment`
- Census report: `docs/research/STAGE2C_FEASIBILITY_CENSUS.md`
- Manifest with dataset/spec/config/code/output hashes: `stage2c_census/manifest.json`

No validation or OOS observation was used in this audit. The reader stops at the final development
bar and does not decode the first out-of-window observation.
