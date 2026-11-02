# Stage 2E — Candidate B Frozen Specification

**Candidate:** B — volatility expansion + directional continuation + retest.
**Spec version:** `1.0.0`
**Status:** Specification and protocol design only. No market data has been read, no signal has been
counted, no census has been run, and no trade outcome has been computed.
**Companion configuration:** `docs/research/STAGE2E_CANDIDATE_B_CONFIG.json`
**Shared protocol:** `docs/research/STAGE2E_SHARED_CENSUS_PROTOCOL.md`

---

## 0. Scope and non-negotiables

This document defines Candidate B completely enough that a second engineer, working only from this
file and the shared protocol, can reproduce the same signal set. Every rule below is a boolean test
on closed bars. There is no visual judgement anywhere in the specification.

| constraint | value |
|---|---|
| Instrument | BTCUSDT |
| Market | spot |
| Direction | long only |
| Leverage | none |
| Data source | existing Binance BTCUSDT dataset in `backend/data/datasets/` |
| Development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| Round-trip cost | 26 basis points (primary) |
| Cost gate | `cost_R <= 0.20` |
| Implied minimum stop at the gate | 1.30% of entry |
| Canonical non-overlap | 72 hours |
| Non-overlap sensitivities | 24 hours, 120 hours |

The cost gate is not relaxed, and the minimum stop is not imposed as a separate rule: it is an
arithmetic consequence of `0.20R` at 26 bp. A structural stop tighter than 1.30% is **not widened
and not skipped by special rule**; it is counted and fails the cost gate like any other signal whose
`cost_R` exceeds `0.20`. This differs from Stage 2D §4.1 step 4, which proposed skipping such
signals. The reason for the change is that a skip rule and the gate would give the same survivors
while hiding how much of the sample the gate removes; letting the gate do it keeps one threshold
instead of two, and keeps the rejection visible in the pipeline (§10).

**Instrument, venue, timeframe, dataset, and interval are fixed.** Binance costs are a proxy. Nothing
in this document is a claim about verified Nobitex execution cost.

### 0.1 The statistical framing is not a result

The 150-event threshold is the project's frozen protocol choice from Stage 2C. It is not derived
from a power calculation and does not guarantee adequate power. The 349-observation figure is a
planning estimate for a `0.15R` effect at 1R outcome standard deviation, 5% two-sided significance,
80% power, and **independent** observations. Clustered signals are not independent observations.
Kish's effective sample size is a concentration diagnostic, not an estimate of serial dependence, and
a census that counts signals cannot identify the dependence structure of outcomes it never observes.
`0.15 - median_cost_R` is a design-margin diagnostic under stated assumptions; it is not measured
expectancy and not profitability.

---

## 1. Data, interval, and timeframes

| item | value |
|---|---|
| Signal timeframe | 1h |
| Regime timeframe | 4h |
| Execution / entry timeframe | 1h |
| Alignment diagnostic timeframe | 5m |
| 1h dataset | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` |
| 4h dataset | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` |
| 5m dataset | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` |
| Dataset manifest | `backend/data/datasets/manifest.json` |

Dataset SHA256 values are recorded in the freeze manifest
(`docs/research/STAGE2E_FREEZE_MANIFEST.json`). Row filtering to the development interval happens by
ISO-string comparison on `open_time` **before** any numeric conversion. No pre-development bar is
used for warm-up. Validation and out-of-sample data are not read, parsed, or summarised.

**Timestamp convention.** Every timestamp is UTC with an explicit `+00:00`. A bar's `open_time` is the
first instant of the bar. A decision taken "at the close" of a bar uses a value knowable at that
bar's `close_time` and is acted on at the next executable bar's `open_time`. On the 1h grid,
`close_time = open_time + 59:59.999`; on the 4h grid, `close_time = open_time + 3:59:59.999`. The 4h
grid opens at hours `00`, `04`, `08`, `12`, `16`, `20` UTC and is therefore aligned to the 1h grid.

**Why entry is on the 1h grid, not the 5m grid.** The previous Stage 2C census priced entry from the
5m bar at `open_time[j] + 1h`, which is the same price as the 1h bar opening at that instant. Reading
the 1h open removes a second dataset from the primary path and removes a class of failure (a missing
5m bar) that is not part of the hypothesis. The 5m series is used only as an alignment diagnostic in
the shared protocol.

---

## 2. Bar usability and segments

### 2.1 1h bar usability

A 1h bar is **usable** if and only if all of the following hold:

| check | requirement | failure label |
|---|---|---|
| present | a bar exists at the expected `open_time` | `missing_bar` |
| closed | `is_closed == True` | `unclosed_bar` |
| on grid | `open_time.minute == 0` and `open_time.second == 0` | `offgrid_bar` |
| traded | `volume > 0` and `trade_count > 0` | `zero_volume_bar` |
| complete bucket | the 1h bucket contains its full 12 members on the 5m grid (unless the 5m series itself is absent, in which case this check is skipped and recorded) | `partial_bar` |
| valid prices | `open > 0`, `high >= low`, `high >= max(open, close)`, `low <= min(open, close)` | `invalid_ohlc` |

A bar that is `partial_bar` is excluded because its close is not the close of a full hour of price
action, and because a gap-adjacent bar can otherwise manufacture a large true range that the
expansion rule would read as a real expansion. This is the same convention as Stage 2C §9.2.

Duplicate `open_time` values are resolved deterministically: keep the **first** occurrence in file
order, discard the rest, and report the count. There is no averaging or merging.

### 2.2 Segments

A **segment** is a maximal run of consecutive usable 1h bars whose `open_time` differs by exactly one
hour. Any unusable or missing bar ends the current segment and begins the next one. Segments are
disjoint and never span a gap.

No bar is synthesised, forward-filled, or interpolated across a segment break. An episode in progress
when its segment ends is terminated without a signal and counted as `segment_break` (§9.4).

### 2.3 4h bar usability

The 4h vendor series is registered gap-free (12,414 bars = 12,414 expected, 0 gaps). A 4h bar is
usable if it is present, `is_closed == True`, and its close is positive. If a 4h bar is nevertheless
missing or unclosed at run time, the regime label is `Unknown` for every 1h bar that would have used
it, and no primary signal is emitted there. 4h buckets are never rebuilt from 1h or 5m data.

A 4h bar whose bucket straddles a 5m gap is retained as supplied, because the vendor close is a real
last-trade price and the regime filter is slow. The run reports how many such buckets were used.

---

## 3. Volatility expansion

### 3.1 ATR construction

**Inputs:** 1h `high`, `low`, `close`, within a single segment.
**Period:** 14. **Method:** Wilder.

For local index `t` within a segment, with `t >= 0`:

```
TR[t] = high[t] - low[t]                                     if t == 0
TR[t] = max(high[t] - low[t],
            abs(high[t] - close[t-1]),
            abs(low[t]  - close[t-1]))                        if t > 0

ATR[t] = mean(TR[0 .. 13])                                    if t == 13
ATR[t] = (ATR[t-1] * 13 + TR[t]) / 14                         if t > 13
```

`ATR[t]` is `Undefined` for `t < 13`. It is re-initialised from the first 14 true ranges of every
segment; no state is carried across a segment break. The first bar of a segment uses `high - low`
because its previous close belongs to the previous segment and would misstate a gap as volatility.

**Why the ATR excludes the expansion bar.** The expansion test compares a bar's true range with
`ATR[t-1]`, not `ATR[t]`. Including the bar in its own denominator would make the test partly
self-referential and would understate the ratio for exactly the bars the rule is looking for.

### 3.2 Expansion bar definition

Bar `t` is an **expansion bar** if all of:

```
range[t]        = high[t] - low[t]
body[t]         = abs(close[t] - open[t])
close_location  = (close[t] - low[t]) / range[t]

range[t]        > 0
ATR[t-1]        > 0
TR[t]           >= 2.0 * ATR[t-1]
body[t] / range[t] >= 0.55
close_location  >= 0.75
close[t]        > open[t]
```

The last three conditions are the **directional confirmation**, and they are satisfied on the
expansion bar itself. There is no separate confirmation bar: a bullish expansion is a single closed
1h bar that moves at least twice its recent average range, closes in the top quarter of its own
range, and closes up. The close-location test is the same condition as "closes in the top 25% of the
bar's range"; the body test rejects bars that opened, wandered, and closed up by a few dollars.

**Volume is not required.** Liquidity confirmation was considered and rejected as a primary
condition: volume can spike on both continuation and exhaustion, it would add a parameter with no
mechanism that distinguishes the two, and zero-volume bars are already excluded as unusable (§2.1).
Relative volume is recorded as a diagnostic only and cannot change any count.

**Zero-range and abnormal bars.** A bar with `range == 0` cannot satisfy `range > 0` and is not an
expansion. A bar whose `ATR[t-1]` is undefined (fewer than 14 bars into its segment) is not testable
and is excluded under `warmup_atr`. There is no rounding tolerance: all comparisons are on the
stored floating-point values, with strict `>=` as written.

**One definition only.** No alternative expansion measure (realised volatility, Bollinger width,
percentile-of-range) is permitted in the primary specification. Sensitivities may vary the ATR
multiple only as a pre-declared diagnostic, and never in the decision count.

<!-- PART2 -->
