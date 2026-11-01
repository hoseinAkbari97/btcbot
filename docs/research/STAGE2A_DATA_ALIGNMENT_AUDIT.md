# Stage 2A — Data Alignment Audit (5m vs 4h BTCUSDT)

**Status:** read-only data-integrity audit. Development interval only,
`[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.
**Verdict:** **PASS WITH ONE DOCUMENTED EXCEPTION** — the 4h series is reconstructible from the 5m
series for every field the Strategy 2 design uses. One 1-tick open discrepancy is explained by
zero-volume placeholder bars and affects no census calculation.
**No P&L or strategy outcome was computed.** No backtest was run.

**Related:** `docs/research/STAGE2A_FEASIBILITY_CENSUS.md`,
`stage2a_census/census.py`, `docs/research/STAGE2A_FEASIBILITY_CENSUS.json`.

---

## 1. Why this audit is mandatory

Strategy 2 defines its state and trigger on **4h closed bars** and its entry on the **first 5m bar
after that 4h bar closes**. That design is only sound if:

1. every 4h bar is the exact aggregate of its 48 constituent 5m bars;
2. the 4h bar's high, low, close and volume are not knowable before it completes;
3. the entry candle can be mapped causally to the first executable 5m bar; and
4. missing 5m intervals do not silently create a 4h bar that the market never produced.

A failure in any of these would mean the census counted events on a timeline that does not exist.

---

## 2. Method

- Both files are streamed with a chunked `raw_decode` reader; rows outside the development window
  are discarded by ISO-string comparison **before** any value is converted.
- Bars are bucketed into 4h slots by timestamp string: `(date, hour // 4)`. No timezone
  arithmetic is performed on the raw strings; all timestamps carry `+00:00`.
- For each 4h slot, the constituent 5m bars are aggregated with `Decimal` arithmetic
  (exact, not float):
  - `open` = first member's open;
  - `high` = max of members' highs;
  - `low` = min of members' lows;
  - `close` = last member's close;
  - `volume` = sum of members' volumes;
  - `close_time` = last member's close_time.
- Each reconstructed field is compared to the vendor 4h value for equality, not tolerance.
- Missing candles are **never** synthesized: a gap is recorded as a gap between two available bars
  and the aggregate is taken over whatever bars exist.

### Timestamp conventions observed

| property | 5m series | 4h series |
|---|---|---|
| Format | `YYYY-MM-DD HH:MM:SS+00:00` | same |
| Timezone | UTC, explicit `+00:00` | same |
| `open_time` alignment | every 5 minutes, seconds `00` | hours `00/04/08/12/16/20`, minutes `00` |
| `close_time` | open + 4:59.999 | open + 3:59:59.999 |
| Completeness flag | `is_closed: True` on every row | same |

---

## 3. Results

### 3.1 Coverage

| check | result |
|---|---|
| 5m bars in development interval | **367,563** |
| 4h bars in development interval | **7,662** |
| Expected 4h bars (1,277 days × 6) | 7,662 — exact match |
| 5m duplicate timestamps | **0** |
| 5m bars off the 5-minute grid | **0** |
| 4h bars off the 4-hour grid | **0** |
| 4h buckets with no 5m data at all | **0** |
| 5m buckets with no 4h bar | **0** |
| 4h bars exactly reconstructed (48/48 bars, all fields equal) | **7,650 / 7,662 (99.84%)** |
| 4h buckets with partial 5m coverage | **12** (all gap-adjacent) |

### 3.2 Field-level equality across all 7,662 4h bars

| field | mismatches |
|---|---:|
| high | **0** |
| low | **0** |
| close | **0** |
| volume | **0** |
| quote_volume | **0** |
| trade_count | **0** |
| close_time | **0** |
| **open** | **1** |

This is the key result for Strategy 2: **every field the design reads — highs that define the
episode high, lows that define the stop, closes that define the trigger, and volumes that define
the dry-up condition — agrees exactly.** The single disagreement is in `open`, which the design
reads only through the 5m entry price.

---

## 4. Registered gaps

Seven 5m gaps, 1,065 missing minutes in total (213 bars × 5 min, consistent with the dataset
manifest's `gap_bars_total`):

| # | last bar before gap | resumes at | missing minutes |
|---|---|---|---:|
| 1 | 2021-02-11 03:40 | 2021-02-11 05:00 | 75 |
| 2 | 2021-03-06 01:55 | 2021-03-06 03:30 | 90 |
| 3 | 2021-04-20 01:55 | 2021-04-20 04:30 | 150 |
| 4 | 2021-04-25 04:00 | 2021-04-25 08:45 | 280 |
| 5 | 2021-08-13 01:55 | 2021-08-13 06:30 | 270 |
| 6 | 2021-09-29 06:55 | 2021-09-29 09:00 | 120 |
| 7 | 2023-03-24 12:35 | 2023-03-24 14:00 | 80 |

Twelve 4h buckets straddle these gaps and are therefore built from fewer than 48 5m bars:

```
2021-02-11 00:00, 2021-02-11 04:00, 2021-03-06 00:00, 2021-04-20 00:00,
2021-04-20 04:00, 2021-04-25 04:00, 2021-04-25 08:00, 2021-08-13 00:00,
2021-08-13 04:00, 2021-09-29 04:00, 2021-09-29 08:00, 2023-03-24 12:00
```

For all twelve, the vendor 4h high, low, close and volume still match the partial 5m aggregate
exactly. That is consistent with the missing intervals containing **no trades at all** (an exchange
outage), so both series omit the same intervals rather than one series being derived from the
other. The cause is inferred; the arithmetic agreement is measured.

---

## 5. The one exception: a 1-tick open at 2023-03-24 12:00

| source | open |
|---|---|
| 5m bar at 2023-03-24 12:00 | `28080.00000000` |
| 4h bar at 2023-03-24 12:00 | `28079.99000000` |

Cause, established by inspection of the surrounding bars:

- The 5m series contains **zero-volume, flat bars** from 11:30 to 12:35 at a constant `28080.00`
  with `high == low` and volume `0`. No trade occurred in those intervals.
- The gap then runs 12:35 → 14:00.
- The first actual trade of the 4h window is at 14:00, at `28079.99`.
- The vendor 4h `open` is therefore the **first traded price**, while the 5m `open` at 12:00 is a
  placeholder price on a bar with no trades.

The 5m placeholder is not a traded price, so the vendor value is the more faithful "open" of the
4h window. Neither value is used by the census: C's trigger reads 4h highs and closes (both exact),
its stop reads 4h episode lows (exact), and its entry reads the 5m open — and no event occurs in
this bucket.

### Related data-quality measurements

| check | result |
|---|---:|
| Zero-volume 5m bars in the development interval | 31 of 367,563 (0.008%) |
| Zero-volume runs | 2 |
| Run 1 | 2021-02-11 02:20 → 03:40, 17 bars |
| Run 2 | 2023-03-24 11:30 → 12:35, 14 bars |
| Flat 5m bars (`high == low`) | 31 (the same bars) |
| Zero-volume **4h** bars | **0** |
| Zero-trade **4h** bars | **0** |

This matters for the compression detector, which reads volatility and volume: a flat bar
contributes zero range and zero volume, and could manufacture a false "quiet" state. It does not
here, because **the 4h series has no zero-volume or zero-trade bars** — the anomalies exist only at
5m resolution, in two short runs adjacent to registered gaps.

---

## 6. Causal mapping of a trigger to the first executable 5m bar

The design requires entry at the open of the first 5m bar after the triggering 4h bar closes. For a
signal bar opening at `T`, its close is `T + 4h − 1 ms`, so the first executable 5m bar is the one
opening at `T + 4h`.

Checks performed for all 17 Candidate C triggers:

| check | result |
|---|---:|
| Entry timestamp `T + 4h` exists in the 5m series | **17 / 17** |
| Entry bar has positive volume (a real trade exists) | **17 / 17** |
| Trigger bucket is one of the 12 gap-affected buckets | **0** |
| Events affected by missing or incomplete underlying 5m data | **0** |

No 4h bar is used before it completes: the trigger is evaluated at the bar's close and the entry is
strictly after that close. No missing candle was synthesized at any point.

---

## 7. Independent verification of the event pipeline

One event was re-derived with a separate code path (direct `json.load` of a window of the 4h file),
recomputing volatility, volume ratios, episode bounds and the trigger without reusing the census
functions:

| item | census | independent recomputation |
|---|---|---|
| Episode | 2021-10-02 16:00 → 2021-10-03 12:00 | same |
| Bars in episode | 6 | 6 |
| All bars tight | — | **true** |
| Bar before episode tight | — | **false** (episode boundary correct) |
| Episode high | `48300.00` | `48300.00` |
| Episode low | `47088.00` | `47088.00` |
| Resolution close | `48774.76` | `48774.76` |
| Trigger (`close > episode high`) | true | **true** |
| Entry reference | `48774.76` | `48774.76` |
| `cost_R` | `0.0752` | `0.0026 / (1686.76/48774.76) = 0.0752` |

The two implementations agree exactly, including the episode boundary — which is the place an
off-by-one error would hide.

---

## 8. Verdict and consequences

**PASS WITH ONE DOCUMENTED EXCEPTION.** The 4h series is a faithful aggregate of the 5m series for
every field the design depends on; the exception is a single `open` tick with a benign,
now-explained cause.

Consequences for Stage 2A:

1. **Event counting is sound.** The 461 episodes, 63 duration-eligible episodes and 17 triggers are
   counted on a timeline that reconstructs exactly.
2. **The stop and `cost_R` are sound.** Episode lows and entry prices both come from verified
   fields.
3. **No event is contaminated by missing data.** All 17 triggers sit outside gap-affected buckets
   and all 17 entry bars are real, traded bars.
4. **A caution for implementation, not a blocker:** the 5m series contains zero-volume placeholder
   bars in two short runs. Any future intraday strategy that sizes, stops, or measures volatility at
   5m resolution must exclude them, because a flat zero-volume bar is not a price observation. The
   4h series is unaffected, which is why the census is unaffected.
5. **A venue caveat that this audit cannot address:** all of the above describes the data, not
   Nobitex execution. Whether these same intervals were tradeable at the venue remains unknown.

---

## 9. Confirmations

- Read-only: no dataset was modified, no candle was synthesized, no file outside
  `stage2a_census/` and `docs/research/` was written.
- No P&L, backtest, simulation, bootstrap, or optimization was performed.
- No validation/OOS bar was read.
- Datasets hashed at run time; both match the manifest:
  5m `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681`,
  4h `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa`.
