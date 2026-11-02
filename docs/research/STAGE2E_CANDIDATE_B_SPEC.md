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

---

## 4. 4h regime permission

### 4.1 Which 4h bar a 1h bar may read

A 1h bar opening at `T` reads the **most recent 4h bar whose `close_time` is strictly less than `T`**.
Because the 4h grid is aligned to the 1h grid, that bar is the one opening at
`floor(T, 4h) - 4h`. For example, a 1h bar opening at `04:00` reads the 4h bar that opened at `00:00`
and closed at `03:59:59.999`. A 1h bar opening at `03:00` reads the 4h bar that opened at `20:00` on
the previous day.

**No unfinished 4h candle is ever read.** There is no partial-bar fallback. If the required 4h bar is
missing or unclosed, the label is `Unknown` and no signal may be emitted on that 1h bar.

### 4.2 Permission formula

Using closed 4h bars only, at 4h bar `q`:

```
SMA50[q]   = mean(close[q-49 .. q])
slope24[q] = SMA50[q] - SMA50[q-6]
ATR4h[.]   = Wilder ATR(14) on 4h true range
pct[q]     = 100 * (count of ATR4h values in the 540-bar window [q-539 .. q]
                    that are strictly less than ATR4h[q]) / 540

permission[q] = (close[q] > SMA50[q])
                AND (slope24[q] > 0)
                AND (20.0 <= pct[q] <= 95.0)
```

All comparisons are strict where written strict. `permission` is three-valued: `True`, `False`, or
`Unknown` (before the first computable value, or on a missing/unclosed 4h bar).

**Why SMA50 and a 24-hour slope.** Fifty 4h bars is about 8.3 days: slow enough not to flip on one
4h bar, fast enough to react within the 72h horizon the candidate trades. The slope over 6 bars is
exactly 24 hours, which is a single day's change in the mean. The Stage 2D design proposed
"`close > SMA50` **or** `10-bar return > 0`"; that disjunction is rejected because it would count an
upward 40-hour return as permission even while price sits below its mean, and because an OR is harder
to audit than a conjunction. Both conditions are now required.

**Why the ATR percentile band.** The lower bound (20th percentile) excludes dead markets where an
"expansion" is a rounding artefact. The upper bound (95th) excludes crisis states where a large 1h
bar is more likely a jump than a tradable impulse, which is the failure mode Stage 2D identified.
The band is a design choice, not a fitted parameter; it is the same kind of ex ante conditioning the
Stage 2D candidate D budget proposed.

**Percentile construction.** The window is 540 consecutive 4h bars ending at `q` **inclusive**, so the
current bar participates in its own percentile. This is causal (the bar is closed before any 1h bar
reads it) and it is the definition that makes the upper bound behave as intended: a crisis 4h ATR
lands near the top of its own window. A leading-edge count `(count strictly less than x) / 540` is
used rather than interpolation, so the value is an exact rational number reproducible in any language.

**Warm-up.** `SMA50` first exists at 4h index 49; `slope24` at index 55; `ATR4h` at index 13, so the
540-value window is fully populated at index 552. The first computable permission is therefore at 4h
index 552, which opens at `2021-04-03T00:00:00Z`. The first 1h bar permitted to read it opens at
`2021-04-03T04:00:00Z`. The 552 preceding 4h bars are a warm-up exclusion and are reported as such.

### 4.3 Permission is evaluated twice

Permission is evaluated at exactly two 1h bars:

1. the **expansion bar** `e` — the setup must exist in a permitted regime;
2. the **confirmation bar** `c` — the regime must still permit the trade when it is taken.

Rules:

| case | outcome |
|---|---|
| `Unknown` or `False` at `e` | episode never starts; counted `regime_not_permitted` |
| `True` at `e`, `Unknown` or `False` at `c` | episode ends without a signal; counted `regime_lost` |
| `True` at both | eligible, subject to §5 |
| transient failure between `e` and `c` only | does **not** invalidate; counted as `regime_blip` diagnostic |

A transient regime failure between the two evaluation points is treated as noise rather than as
evidence, because permission is a state filter and a one-bar dip inside an eight-hour setup is not a
different market. The `regime_blip` count is reported so the choice is visible and can be challenged.

---

## 5. Retest, resumption, entry, and stop

### 5.1 Levels fixed at the expansion bar

At expansion bar `e`:

```
L_e  = close[e]            (retest reference level)
A_e  = ATR[e]              (tolerance unit)
```

`L_e` and `A_e` are fixed when the episode begins. They are never updated by later bars, including by
a second expansion bar absorbed into the same episode (§6.2).

### 5.2 Retest window and touch

The retest window is the six 1h bars `e+1 .. e+6` inclusive. A bar `r` in that window is a **retest
touch** if:

```
low[r] <= L_e + 0.25 * A_e
```

The first qualifying bar is taken; later bars are not searched. The window is frozen as indices
`1..6`, which is the Stage 2D proposal "1–6 bars" made explicit: the expansion bar itself cannot be
the retest (`r >= e+1`), and a seventh bar is a new day of price action, not a pullback of the same
impulse. Six bars and a 0.25× ATR tolerance are design values, not optimized ones.

### 5.3 Penetration limits

```
penetration[r] = (L_e - low[r]) / A_e
```

| condition | outcome |
|---|---|
| `penetration[r] <= 0.50` (equivalently `low[r] >= L_e - 0.50*A_e`) | valid touch |
| `penetration[r] > 0.50` | episode invalidated, `retest_too_deep` |
| any bar `x` in `e+1 .. r-1` has `close[x] < L_e - 0.50*A_e` | episode invalidated, `structure_broken` |
| no touch in `e+1 .. e+6` | episode expires, `retest_timeout` |

The asymmetry is intentional: price may trade **above** the level by the full tolerance (the touch
condition), but may only breach **below** it by half an ATR before the expansion is treated as failed.
A retest that gives back more than half the impulse's ATR is not a retest, it is a reversal.

### 5.4 Resumption confirmation

After a touch at `r`, let `c` be the first 1h bar with

```
r < c <= r + 3    and    close[c] > L_e    and    close[c] > open[c]
```

| condition | outcome |
|---|---|
| such a `c` exists | signal candidate at `c` |
| any bar `x` with `r < x < c` has `close[x] < L_e - 0.50*A_e` | invalidated, `structure_broken` |
| no such `c` within 3 bars | episode expires, `resumption_timeout` |

The confirmation bar is strictly after the retest bar, so a single bar can never be both the touch and
the resumption. That is the rule Stage 2D left open, resolved here in the conservative direction: a
bar that dips to the level and closes green is a wick, not a confirmed retest.

**The signal timestamp is `close_time[c]`.** Nothing about the signal uses information from bar
`c+1` or later. Entry is at the next bar's open (§5.5).

### 5.5 Entry

**Entry bar:** the 1h bar whose `open_time` equals `open_time[c] + 1h`.
**Entry price:** that bar's `open`.

The entry bar must be usable under §2.1. Failure labels:

| failure | label |
|---|---|
| bar absent | `no_entry_bar` |
| bar not closed | `unclosed_entry_bar` |
| zero volume / no trades | `zero_volume_entry` |
| partial bucket | `partial_entry_bar` |
| invalid or non-positive open | `invalid_entry_price` |

A missing entry bar **rejects the signal**; the run does not skip forward to the next available bar.
Skipping forward would price the trade at a moment that is not the first moment after the signal and
would make the fill assumption unauditable. Rejections are counted.

### 5.6 Structural stop

```
S = min(low[x]) for x in e .. c inclusive
D = entry_open - S
stop_pct = D / entry_open
```

The stop is the lowest low of the setup, from the expansion bar through the confirmation bar. It is
fixed at entry and never widened, trailed, or rounded.

**No artificial minimum stop.** The Stage 2D text proposed skipping signals whose stop was tighter
than 1.30%. That rule is not adopted as a separate filter: `1.30%` is exactly what
`cost_R <= 0.20` at 26 bp implies, so the cost gate performs the same exclusion and the pipeline
reports it as `cost_gate` rather than as a hidden stop adjustment. In particular the stop is **never
widened** to reach 1.30%; widening a stop would lower `cost_R` arithmetically while increasing
notional per unit of risk, which is an accounting trick, not an improvement.

**Invalid stop** (`invalid_stop`) if any of: `S <= 0`; `entry_open <= 0`; `D <= 0` (entry at or below
the setup low).

<!-- PART3 -->
