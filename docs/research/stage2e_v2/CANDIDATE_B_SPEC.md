# Stage 2G / Stage 2E version 2 — Candidate B Frozen Specification

**Candidate:** B — volatility expansion + directional continuation + retest.
**Spec version:** `2.0.0`
**Supersedes:** `docs/research/STAGE2E_CANDIDATE_B_SPEC.md` version `1.0.0` (immutable historical freeze).
**Remediation basis:** `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`.
**Status:** Specification and protocol design only. No market data has been read, no signal has been
counted, no census has been run, and no trade outcome has been computed.
**Companion configuration:** `docs/research/stage2e_v2/CANDIDATE_B_CONFIG.json`
**Shared protocol:** `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md`

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
instead of two, and keeps the rejection visible in the pipeline (§9).

**Version 2 scope.** Version `2.0.0` changes no strategy parameter, no cost assumption, no
instrument, no direction, and no development interval. It resolves the Stage 2F findings C2, C3, C4,
M1–M3, M5, M7–M13, and m1–m11 as they apply to B. The only definition-level changes are causal and
accounting corrections: the cost-median population, the timestamp representation, the candle-
availability convention, the 4h ATR construction, entry-time validation, the 4h partial-bucket
exemption, the development-end guard, and the B pipeline stage labels. No change was selected by
looking at historical outcomes.

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

Dataset SHA256 values are recorded in the version 2 freeze manifest
(`docs/research/stage2e_v2/FREEZE_MANIFEST.json`). Row selection uses a **canonical integer UTC epoch
millisecond** representation of `open_time`, never a lexicographic ISO-string comparison:

```
dev_start_ms = 1609459200000   # 2021-01-01T00:00:00Z, inclusive
dev_end_ms   = 1719792000000   # 2024-07-01T00:00:00Z, exclusive
admit row  <=>  dev_start_ms <= open_time_ms < dev_end_ms
```

The runner must parse the dataset's `open_time` string (including its space separator and `+00:00`
offset) into an aware UTC datetime, convert to integer epoch milliseconds, and only then filter. A
candle whose `open_time_ms == dev_start_ms` is **included**. A candle whose `open_time_ms ==
dev_end_ms` is **excluded**. The run asserts, before producing any count, that
`min(open_time_ms) >= dev_start_ms` and `max(open_time_ms) < dev_end_ms` for every timeframe read. No
pre-development bar is used for warm-up. Validation and out-of-sample data are not read, parsed, or
summarised.

**Timestamp convention.** Every timestamp is UTC. Internally the runner uses integer epoch
milliseconds. A bar's `open_time` is the first instant of the bar; its `close_time` is the last
included instant, so `close_time_ms = open_time_ms + duration_ms - 1`. On the 1h grid,
`close_time_ms = open_time_ms + 3,599,999`; on the 4h grid, `+14,399,999`. The 4h grid opens at hours
`00`, `04`, `08`, `12`, `16`, `20` UTC and is therefore aligned to the 1h grid.

**Candle availability (C4).** A candle is **available** at decision instant `T` if and only if
`close_time_ms <= T`. A candle whose `close_time_ms == T` **is available**; the same-bar-close
equality is explicitly permitted. This single convention governs ATR, SMA, VWAP, percentile windows,
regime labels, and signal confirmation. A decision taken "at the close" of a bar uses values knowable
at that bar's `close_time` and is acted on at the next executable bar's `open_time`. Availability is
necessary but not sufficient: a candidate-specific selection rule may be stricter (for example B's 4h
regime rule requires the 4h bar to close before the 1h bar opens), but it may never be looser.

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

### 2.3 4h bar usability and the shared 4h exemption (M3)

The 4h vendor series is registered gap-free (12,414 bars = 12,414 expected, 0 gaps). A 4h bar is
usable if it is present, `is_closed == True`, and its close is positive. If a 4h bar is nevertheless
missing or unclosed at run time, the regime label is `Unknown` for every 1h bar that would have used
it, no primary signal is emitted there, and the 4h ATR segment is reset as defined in the shared
protocol §1.7. 4h buckets are never rebuilt from 1h or 5m data.

**Explicit shared 4h supplied-bar exemption.** The supplied 4h series is exempt from the 5m
membership check in shared protocol §1.3. The twelve 4h buckets that straddle the seven registered 5m
gaps are retained **as supplied**, because the vendor close is a real last-trade price and the regime
filter is slow. This is an explicit protocol exception, not an accidental omission. The run reports
how many such buckets were used (expected: 12) and computes a **non-decision sensitivity** in which
those 12 buckets are excluded and the 4h ATR is segment-broken at them. The sensitivity is reported
as a diagnostic only; it cannot change the primary signal set, the verdict, or any denominator.

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

Because the expansion test reads `ATR[t-1]`, the first bar at which an expansion can be tested is
**local index 14**, the fifteenth bar of the segment. Bars at local index 0–13 are warm-up.

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

**Division ordering.** `range[t] > 0` is tested before `body[t] / range[t]` and `close_location` are
formed. An implementation that divides first and handles infinity afterwards is not compliant with
this specification.

**One definition only.** No alternative expansion measure (realised volatility, Bollinger width,
percentile-of-range) is permitted in the primary specification. The ATR multiple is fixed at `2.0`
and is not a tunable parameter. No ATR-multiple sensitivity is declared or permitted (m6).

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
ATR4h[.]   = Wilder ATR(14) on 4h true range, constructed exactly as shared protocol §1.7
pct[q]     = 100 * (count of ATR4h values in the 540-bar window [q-539 .. q]
                    that are strictly less than ATR4h[q]) / 540

permission[q] = (close[q] > SMA50[q])
                AND (slope24[q] > 0)
                AND (20.0 <= pct[q] <= 95.0)
```

**4h ATR construction (M1).** The 4h ATR is **not** merely "Wilder period 14"; its full construction
is frozen in shared protocol §1.7 and repeated here:

```
TR4h[0] = high[0] - low[0]                                   for the first bar of a 4h segment
TR4h[t] = max(high[t] - low[t],
              abs(high[t] - close[t-1]),
              abs(low[t]  - close[t-1]))                     for t > 0 in the same segment

ATR4h[13] = mean(TR4h[0 .. 13])
ATR4h[t]  = (ATR4h[t-1] * 13 + TR4h[t]) / 14                 for t > 13 in the same segment
```

`ATR4h[t]` is `Undefined` for `t < 13`. The first true range of a 4h segment uses `high - low`; the
previous close is not imported across a segment break. A missing or unusable 4h bar ends the 4h
segment and resets the ATR. The 4h series is gap-free in the registered dataset, so the primary path
has one 4h segment, but the reset rule is frozen so a future gap cannot be handled by an arbitrary
choice. The 540-value window is admitted only if all 540 `ATR4h` values are defined and the 4h bars
are usable; otherwise `pct[q]` is `Unknown`.

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

If **any** value in the window is undefined or missing, `pct[q]` is `Unknown` and permission is
`Unknown`; a percentile over a truncated window is never substituted.

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
| `Unknown` at `e` | episode attempt does not become regime-qualified; primary label `warmup_regime` |
| `False` at `e` | episode attempt does not become regime-qualified; primary label `regime_not_permitted` |
| `True` at `e`, `Unknown` or `False` at `c` | episode is structurally valid but fails at the confirmation-time regime check; primary label `regime_lost` |
| `True` at both | eligible, subject to §5 |

There is **no intermediate regime evaluation** between `e` and `c`. Permission is a state filter
evaluated only at the two bars above; no `regime_blip` diagnostic is computed (m11). A regime value at
any other bar cannot invalidate, rescue, or relabel an episode.

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

**Entry-time validation (M2).** The entry decision is made at the signal instant and executed at the
entry bar's open. Only properties knowable at that open may reject the signal:

| check at entry | requirement | failure label |
|---|---|---|
| present | a bar exists at the expected `open_time` | `no_entry_bar` |
| on grid | `open_time_ms` is exactly `open_time_ms[c] + 3,600,000` | `no_entry_bar` |
| inside interval | `open_time_ms < dev_end_ms` | `entry_outside_interval` |
| positive open | `open > 0` | `invalid_entry_price` |
| prior context | the confirmation bar `c` is closed and the signal is fixed | (guaranteed by construction) |

The entry bar's **close-time** properties — `is_closed`, `volume > 0`, `trade_count > 0`, complete
5m bucket, full-bar OHLC validity — are **not** selection criteria. They are recorded as
post-count data-quality diagnostics and cannot remove a signal that was executable at the open. A
real-time trader cannot reject an entry at the open because the bar later turns out to have a
zero-volume final member.

A missing entry bar **rejects the signal**; the run does not skip forward to the next available bar.
Skipping forward would price the trade at a moment that is not the first moment after the signal and
would make the fill assumption unauditable. Rejections are counted.

A confirmation bar that is the last bar of its 1h segment necessarily has no next bar in that
segment; the signal is then rejected as `no_entry_bar`, even if a bar exists after the gap. A new
segment after a gap is a different price history and is not a valid continuation of the setup.

**Development-end guard (M5).** If the entry bar would open at or after `dev_end_ms =
1719792000000` (`2024-07-01T00:00:00Z`), the signal is rejected with `entry_outside_interval`; it is
**not** silently dropped and **not** completed from a validation bar. The same guard applies to any
bar the signal would need at or after the boundary. A signal may use only bars whose `open_time_ms`
is inside `[dev_start_ms, dev_end_ms)`.

### 5.6 Structural stop

```
S = min(low[x]) for x in e .. c inclusive
D = entry_open - S
stop_fraction = D / entry_open          (dimensionless fraction; displayed as a percent only in prose)
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

---

## 6. Episodes, duplicates, and identity

### 6.1 Episode lifecycle

An **episode** is the state machine that begins at an expansion bar and ends at the first of:

| end condition | label | signal emitted? |
|---|---|---|
| resumption confirmed and entry/stop valid | `signalled` | yes, exactly one |
| penetration or structure break | `invalidated` | no |
| retest window or confirmation window expires | `expired` | no |
| regime permission lost at confirmation | `regime_lost` | no |
| 1h segment ends | `segment_break` | no |
| entry bar or stop invalid | `rejected` | no |

The episode is closed by the **first** of these in evaluation order. Within a bar, the order is:
penetration/structure checks, then expiry checks, then confirmation, then entry/stop validity. An
invalidated episode is never re-opened.

**Exactly one active episode at a time.** A new expansion bar while an episode is active does **not**
start a second episode (§6.2). After an episode ends, the next qualifying expansion bar at a strictly
later index starts a new episode. There is no cooldown in the primary specification; the only spacing
rule is the canonical 72h non-overlap rule (§7.1), and shorter/longer spacings are diagnostics only
(§7.4).

### 6.2 Multiple expansions in one episode

While an episode is active, an expansion bar at index `x > e` is **absorbed**:

- it does not open a new episode;
- it does not move `L_e`, `A_e`, or the retest window;
- it is counted as `expansions_absorbed` and reported.

Reason: the hypothesis is one impulse followed by one retest. Re-anchoring the level on a second
expansion would let the setup drift toward whatever performed best, and opening a second episode would
double-count the same market move. The absorbed count makes the choice measurable.

### 6.3 Failed retest

An episode that expires or is invalidated produces **no signal**, and no later bar of that episode can
revive it. The market can produce a new signal only through a new expansion bar after the episode has
ended. This is the deterministic answer to the Stage 2D question "can a failed retest produce another
signal": no.

### 6.4 Regime interaction

A regime change interacts with an episode only at the two evaluation points in §4.3. A transition
during the retest is not itself an end condition; the confirmation-bar check is. Because the episode
is closed by the first failing condition, a regime loss at confirmation terminates the episode before
any further bars are evaluated.

### 6.5 Deterministic identity

Every episode has the key

```
B:{expansion_open_time in ISO 8601 with +00:00}
```

e.g. `B:2021-03-01T00:00:00+00:00`. The key depends only on the expansion bar, so it is stable across
reruns and implementations. Two episodes cannot share a key because a bar can begin at most one
episode.

**Duplicate rule.** Two signals are duplicates if they share the same `entry_time`. Under the
one-active-episode rule this cannot occur, but the census verifies it and reports the number of
duplicates removed. A signal is also rejected if its confirmation bar has already been used by another
signal; that is impossible for the same reason and is checked anyway.

---

## 7. Non-overlap policy

### 7.1 Canonical 72-hour rule

**Population:** unique cost-feasible signals (one per signalled episode), after the cost gate.

**Algorithm:**

1. Sort the population by `entry_time` ascending; ties broken by episode key ascending
   (ISO-string comparison).
2. Accept the first signal.
3. Accept each subsequent signal whose `entry_time` is **at least** 72 hours after the most recently
   accepted signal's `entry_time`. Exactly 72 hours qualifies.
4. Rejected signals are marked `non_overlap` and are retained in the output for audit.

**Timestamp used:** `entry_time`, the open time of the entry bar — not the signal time, not the
expansion time. Entry time is what determines when capital would be committed.

**Boundary:** inclusive. `entry_time - last_accepted_entry_time >= 72h`.

**Simultaneous signals:** impossible in practice (one active episode), but if two signals ever share
an `entry_time`, the lexicographically smaller key is retained and the other is labelled
`duplicate_entry`.

**Order of application:** after deduplication and after the cost gate. Non-overlap never changes
whether a signal is cost-feasible; it only decides which feasible signals are separated enough to be
counted as distinct opportunities. Signals rejected here still appear in the cost distribution.

### 7.2 Sensitivities

The 24-hour and 120-hour counts use the identical greedy algorithm over the same population, changing
only the separation threshold. They are diagnostics. The canonical decision count is the 72-hour
count, and the sensitivities may not be substituted for it after the fact.

### 7.3 What the count means

`N_nonoverlap` answers: how many cost-feasible signals exist such that no two are less than 72 hours
apart? It is an interval-selection count, not a portfolio, not a sequence of trades, and not a claim
of independence. 72 hours is the maximum intended holding horizon, chosen in Stage 2D because it
leaves 425 calendar slots in a 1,277-day interval; it is a protocol convention, not an estimate of the
optimal exit.

### 7.4 Non-overlap spacing sensitivities

Pre-declared diagnostics only: the same greedy non-overlap rule at 24h, 72h, and 120h. No other
spacing may be tried. These numbers cannot alter the verdict. The word "cooldown" is not used: the
rule is a non-overlap spacing constraint on accepted entry times, not a trading cooldown, and
`canonical_hours` is the single source of truth (m7).

---

## 8. Cost model and feasibility gate

**Round-trip cost:** 26 basis points of notional, as a fraction `0.0026`. This is a Binance spot proxy
for fees plus adverse execution. It is **not** a Nobitex measurement.

For every signal with a valid stop:

```
cost_R = 0.0026 * entry_open / D
```

where `D = entry_open - S` (§5.6).

**Primary gate:** `cost_R <= 0.20`.

At 26 bp, `cost_R <= 0.20` is equivalent to `D / entry_open >= 0.013`, i.e. a 1.30% stop. The census
reports the full stop-distance distribution so the equivalence can be checked independently.

Reported buckets, with explicit endpoint inclusion (m2):

| bucket | lower | upper | lower inclusive | upper inclusive |
|---|---|---|---|---|
| `<= 0.10` | `-inf` | `0.10` | n/a | yes |
| `(0.10, 0.20]` | `0.10` | `0.20` | no | yes |
| `(0.20, 0.30]` | `0.20` | `0.30` | no | yes |
| `(0.30, 0.50]` | `0.30` | `0.50` | no | yes |
| `> 0.50` | `0.50` | `+inf` | no | n/a |

Signals failing the gate are counted as `cost_gate` and remain in the cost distribution. They are not
deleted from the economic evidence.

**Cost sensitivity:** the counts that would pass the same `0.20` gate at 10, 39, and 52 bp round-trip
are reported. The primary gate is not changed at any of them; only `cost_R` is recomputed.

---

## 9. Counting pipeline and exclusion accounting

Every stage is counted. Each rejection has exactly one **primary** reason, assigned in the order
below; the run also records secondary reasons and reports both.

```
S1  usable 1h bars in the development interval
S2  expansion-testable 1h bars          ATR[t-1] defined (local index >= 14)
S3  expansion bars
S4  episode attempts                    non-absorbed expansion bars, including regime failures at e
S5  regime-qualified episode attempts   permission == True at e
S6  structurally valid episodes          retest touch + resumption confirmed, before the regime-at-c check
S7  signals with valid confirmation regime and valid entry/stop   permission == True at c, D > 0
S8  cost-feasible signals                cost_R <= 0.20
S9  deduplicated signals                 one per episode (verified)
S10 non-overlapping signals              72h greedy, canonical
```

**Stage labels are explicit (M8, M9).** `S4` is an **episode attempt**, not a completed episode and
not merely an expansion bar: it is the first non-absorbed expansion bar that opens an attempt,
whether or not the regime at `e` permits it. `S5` is the subset that passes the regime at `e`.
`S6` is structural only (touch plus resumption); it deliberately does **not** include the regime check
at confirmation. `S7` applies the confirmation-time regime check and the entry/stop checks. This
makes `permission_share = S5/S4` a real share, gives `regime_lost` a unique stage, and keeps
`S7` as the pre-gate valid-entry/stop population used by the cost median (C2).

Exclusion labels:

| label | stage |
|---|---|
| `warmup_atr` | S2: `ATR[t-1]` undefined (local index <= 13) |
| `warmup_regime` | S5: no computable 4h permission at `e` (`Unknown`) |
| `regime_not_permitted` | S5: permission `False` at `e` |
| `retest_timeout` | S6: no touch within `e+1 .. e+6` |
| `retest_too_deep` | S6: touch penetration > 0.50 ATR |
| `structure_broken` | S6: close below `L_e - 0.50*A_e` before confirmation |
| `resumption_timeout` | S6: no confirmation within 3 bars of the touch |
| `segment_break` | S6: 1h segment ended before structural completion |
| `regime_lost` | S7: permission `Unknown` or `False` at the confirmation bar |
| `no_entry_bar` | S7: entry bar absent, off-grid, or not the next 1h bar |
| `entry_outside_interval` | S7: entry bar opens at or after `dev_end_ms` |
| `invalid_entry_price` | S7: entry open <= 0 |
| `invalid_stop` | S7: `S <= 0` or `D <= 0` |
| `cost_gate` | S8: `cost_R > 0.20` |
| `duplicate_entry` | S9: entry timestamp already used (expected 0) |
| `non_overlap` | S10: within 72h of an accepted signal |

The following are **post-count data-quality diagnostics**, never primary rejection labels (M2):
`unclosed_entry_bar`, `zero_volume_entry`, `partial_entry_bar`, and `invalid_entry_ohlc`. They are
reported as counts and cannot remove a signal.

### 9.1 Denominator definitions

Ambiguous denominators are the commonest way two implementations diverge. These are frozen:

| reported quantity | numerator | denominator |
|---|---|---|
| `expansion_test_share` | S3 expansion bars | S2 expansion-testable bars |
| `permission_share` | S5 regime-qualified attempts | S4 episode attempts |
| `retest_conversion` | S6 structurally valid episodes | S5 regime-qualified attempts |
| `signal_validity_share` | S7 confirmation-regime + entry/stop valid | S6 structurally valid episodes |
| `feasible_share` | S8 cost-feasible | S7 valid entry/stop |
| `unique_share` | S9 unique signals | S8 cost-feasible |
| `nonoverlap_share` | S10 at 72h | S9 unique |

Within `S6 → S7`, the run reports `regime_lost` and each entry/stop rejection as separate counts so
the combined `signal_validity_share` is auditable. `feasible_share` is the share that matters
economically, and it is always measured against S7, never against S3 or S4. A high expansion count
with a low feasible share is a rejected design, not a large sample.

**Cost-median populations (C2).** Three populations are kept separate and named explicitly:

| symbol | population | use |
|---|---|---|
| `S4` | episode attempts | raw-candidate denominator |
| `S7` | valid confirmation regime + valid entry/stop, **before** the cost gate | **`M_all`**, the verdict median |
| `S8` | cost-feasible, `cost_R <= 0.20` | **`M_feasible`**, reported separately |

`M_all = median(cost_R over S7)` includes signals that fail the gate. `M_feasible = median(cost_R
over S8)` is bounded above by `0.20` by construction and is **not** used in the verdict. Every
cost-related statistic (mean, quartiles, percentiles, bucket shares, sensitivity medians) is labelled
with the population it uses. If `S7` is empty, `M_all` is **undefined**, the census is
`INCONCLUSIVE` for lack of an economic population, and the verdict cannot be `PASS` or `PASS WITH
LIMITATIONS`.

---

## 10. Required diagnostics

Every future B census must report, at minimum:

1. **Pipeline counts** S1–S10 with all exclusion labels, primary and secondary.
2. **Cost_R distribution** of all S7 signals: count and percentage in each bucket, `M_all` (median),
   mean, p25, p75, p90, min, max, plus the count passing at 10, 26, 39, and 52 bp. Report
   `M_feasible` over S8 separately, labelled as the post-gate diagnostic.
3. **Stop-distance distribution** in USDT and as a percentage of entry: median, p25, p75, p90, min,
   max, and the share below 1.30%.
4. **Non-overlap counts** at 24h, 72h (canonical), and 120h, with the spacing distribution.
5. **Calendar counts** by year and by month, for S8 and S10.
6. **Regime counts** by 4h permission state at `e`, by 4h permission state at `c`, and by `pct[q]`
   decile. No `regime_blip` diagnostic is computed (m11).
7. **Cluster concentration**: the distribution of S8 signals across **Kish clusters** as defined in
   the shared protocol §3.1 (maximal runs of consecutive usable 4h bars with `permission == True`),
   reporting count, median, p90, maximum, and share in the largest cluster; plus calendar-month and
   calendar-quarter views.
8. **Kish diagnostic** `n_eff = (Σ n_k)^2 / Σ n_k^2` over the same `permission == True` clusters,
   reported with the cluster count, the design effect, and an `n_eff` sensitivity to assumed
   `rho` in {0.25, 0.50, 0.75, 1.00}. It is a concentration diagnostic, not a dependence estimate. A
   cluster is a maximal run; `Unknown` or `False` breaks it; a missing/unusable 4h bar breaks it.
9. **Detectable-effect reference** `2.801585 / sqrt(N_nonoverlap)` in R, labelled as a planning
   calculation under independence.
10. **Capital geometry** at $10,000 equity and 1% risk. With `stop_fraction = D / entry_open` (a
    dimensionless fraction, not a percent),
    `notional_usd = risk_usd / stop_fraction = 100 / stop_fraction`. Report the distribution of
    `notional_usd` and `notional_pct = notional_usd / equity_usd`, the maximum number of concurrently
    open 72h windows, and the count of signals whose implied notional exceeds equity. The numeric
    impracticability condition is `notional_pct > 1.00` for any signal; if it occurs, the
    capital-geometry FAIL condition is met. Worked examples state whether they display the fraction
    or the percent (M10).
11. **Data-alignment audit** (gap-aware, shared protocol §1.6) and **resource usage**.

No outcome-based metric is reported.

### 10.1 Worked synthetic example (arithmetic check only)

The numbers below are **invented** to make the rules checkable; they are not market data.

| bar | open | high | low | close | note |
|---|---:|---:|---:|---:|---|
| `e-1` | 100.0 | 100.4 | 99.9 | 100.2 | ATR[e-1] = 2.0000 |
| `e` | 100.0 | 104.0 | 99.5 | 103.5 | expansion |
| `e+1` | 103.5 | 103.8 | 102.9 | 103.0 | retest touch |
| `e+2` | 103.0 | 104.2 | 103.0 | 103.9 | resumption |
| `e+3` | 104.0 | — | — | — | entry at open |

Checks: range 4.5 > 0; TR 4.5 ≥ 2.0 × 2.0; body/range = 3.5/4.5 = 0.7778 ≥ 0.55; close location
(103.5 − 99.5)/4.5 = 0.8889 ≥ 0.75; close > open. `L_e = 103.5`;
`ATR[e] = (2.0 × 13 + 4.5)/14 = 2.178571`; touch bound `= 103.5 + 0.25 × 2.178571 = 104.044643`, and
`low[e+1] = 102.9` qualifies; penetration `= (103.5 − 102.9)/2.178571 = 0.2754 ≤ 0.50`; confirmation at
`e+2` because `103.9 > 103.5` and `103.9 > 103.0`. Stop `= min(99.5, 102.9, 103.0) = 99.5`;
`D = 104.0 − 99.5 = 4.5`; `stop_fraction = D / entry_open = 4.5 / 104.0 = 0.043269` (displayed as
`4.3269%`); `cost_R = 0.0026 × 104.0/4.5 = 0.06009` (passes); `notional_usd = 100 / 0.043269 =
$2,311.11` (23.11% of $10,000 equity). Key: `B:{open_time[e]}`.

---

## 11. Acceptance criteria and decision rule

Three concepts are kept separate and must be reported separately:

1. **Protocol compliance** — did the census execute this specification exactly? Hash match, alignment
   pass, duplicate/unusable-bar accounting reconciled, causal-timing checks passed.
2. **Structural feasibility** — does the candidate produce enough cost-feasible, non-overlapping,
   deduplicated opportunities?
3. **Economic viability** — has a positive net edge been demonstrated? **A census cannot answer this.**
   It observes no outcome. It must never be reported as evidence of profitability.

### 11.1 Verdicts

Let `N = N_nonoverlap` (72h canonical), `M_all = median cost_R over S7` (the pre-gate valid
entry/stop population), `M_feasible = median cost_R over S8` (post-gate diagnostic), `F =
feasible_share = S8/S7`, and `E = 0.15 − M_all` (the design-margin diagnostic).

| verdict | condition |
|---|---|
| **INCONCLUSIVE** | hash mismatch; dataset hash mismatch; alignment failure in a field the design reads; a causality check fails; S9 ≠ S8 for an unexplained reason; or the S7 population is empty so `M_all` is undefined |
| **FAIL** | `N < 150`; or `M_all > 0.20`; or any signal has `notional_pct > 1.00` (capital geometry impracticable under spot cash) |
| **PASS WITH LIMITATIONS** | `150 <= N < 349` and `M_all <= 0.20`, all compliance checks passed |
| **PASS** | `N >= 349` and `M_all <= 0.20`, all compliance checks passed |

`M_all` is the verdict median because S7 includes the signals that fail the cost gate. Using S8 would
make `M_all <= 0.20` true by construction and `M_all > 0.20` impossible (C2). `M_feasible` is
reported for transparency but cannot satisfy or fail the cost condition. Both medians are labelled
with their population in every report.

The `349` boundary in the top tier is the independent-sample planning reference carried forward from
Stage 2C, used as a tier label for comparability. It is not a requirement, it does not guarantee
power, and reaching it does not establish an edge. A `PASS` here means only that the structural count
clears the larger reference; it says nothing about profitability.

`E` is reported alongside every verdict, with its assumptions: it uses an **assumed** `0.15R` effect
of interest and a Binance-proxy cost. It is not a net expectancy and not a profitability estimate. A
negative `E` is a warning that the design has no room left under the assumption; a positive `E` is not
proof of viability.

### 11.2 Proposed additional thresholds (require approval before counting)

These come from Stage 2D and are **not** yet approved protocol:

| proposed threshold | rationale | status |
|---|---|---|
| `F >= 0.25` | below this, the survivors are a selected minority of structurally valid signals and the median can be unrepresentative | **proposed, requires approval** |
| `M_all <= 0.12` | keeps at least `0.03R` of the assumed `0.15R` effect before other friction; defined on the same pre-gate S7 population as the verdict median | **proposed, requires approval** |

Neither is part of the primary verdict above. If either is adopted, it must be written into a new
version of this specification and frozen **before** counting. No threshold may be added after seeing
counts. The proposed economic median is defined on `M_all`, not on `M_feasible`; the post-gate median
is already bounded by `0.20` and cannot carry an economic threshold (C2).

### 11.3 What 150 and 349 do and do not mean

150 is the project's frozen protocol threshold, introduced at the Stage 2C freeze with no
statistical derivation; it is not a universal requirement and does not guarantee power. 349 is an
independent-observation planning estimate and is optimistic under clustering and fat tails. Neither
number converts a census count into evidence of an edge.

---

## 12. What this census does not do

- No trade is entered, resolved, or marked to market.
- No P&L, return, expectancy, win rate, drawdown, Sharpe, CAGR, or profitability figure is computed.
- No backtest, portfolio simulation, bootstrap, or Monte Carlo is run.
- No parameter is optimized or swept in the decision path; the ATR multiple, tolerance, and windows
  are frozen here and may not be tuned.
- No validation or out-of-sample observation is read, parsed, summarised, or used.
- No frozen Stage 2A, 2B, 2C, 2D, Stage 6, Stage 6A, or Setup 1 artifact is modified.
- No discretionary visual interpretation is permitted at any stage.

---

## 13. Freeze record

**Spec version:** `2.0.0`.
**Frozen artefact:** `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md`.
**Configuration:** `docs/research/stage2e_v2/CANDIDATE_B_CONFIG.json` (values here and in the JSON
are identical; the JSON is the machine-readable source for the runner).
**Manifest:** `docs/research/stage2e_v2/FREEZE_MANIFEST.json` records the SHA256 of this file, the
configuration, the shared protocol, the dataset files, the original Stage 2E hashes, the Stage 2F
audit hash, the development interval, the cost assumptions, the protocol version, the freeze
timestamp, every Stage 2F finding's resolution status, and an explicit statement that no census has
been run.

Any change to any parameter requires a new spec version, a new configuration, a new manifest, and
explicit approval. A runner must abort when the file hashes do not match the manifest.
