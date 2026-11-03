# Stage 2G / Stage 2E version 2 — Candidate D Frozen Specification

**Candidate:** D — intraday continuation with a higher-timeframe volatility budget.
**Spec version:** `2.0.0`
**Supersedes:** `docs/research/STAGE2E_CANDIDATE_D_SPEC.md` version `1.0.0` (immutable historical freeze).
**Remediation basis:** `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`.
**Status:** Specification and protocol design only. No market data has been read, no signal has been
counted, no census has been run, and no trade outcome has been computed.
**Companion configuration:** `docs/research/stage2e_v2/CANDIDATE_D_CONFIG.json`
**Shared protocol:** `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md`

---

## 0. Scope and non-negotiables

This document defines Candidate D completely enough that a second engineer, working only from this
file and the shared protocol, can reproduce the same signal set. Every rule is a boolean test on
closed bars over explicit UTC windows. There is no visual judgement anywhere in the specification.

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
| Canonical non-overlap | 24 hours |
| Non-overlap sensitivities | 12 hours, 48 hours |

The cost gate is not relaxed. The 1.30% minimum stop is **not** imposed as a separate rule and stops
are **never widened** to reach it: the gate performs the exclusion arithmetically, and the pipeline
reports the rejected signals rather than hiding them.

**Version 2 scope.** Version `2.0.0` changes no strategy parameter, no cost assumption, no
instrument, no direction, no session definition, and no development interval. It resolves the Stage
2F findings C1–C4, M1–M4, M6, M10–M13, and m2–m5, m8–m11 as they apply to D. The only
definition-level changes are causal and accounting corrections: signal eligibility now uses only the
first eight bars, the timestamp representation is canonical epoch milliseconds, the candle-
availability convention is unified, the 4h ATR construction is fully specified, entry validation is
open-time-only, the 4h partial-bucket exemption is explicit, and the warm-up boundary is corrected.
No change was selected by looking at historical outcomes.

**Instrument, venue, timeframe, dataset, and interval are fixed.** Binance costs are a proxy. Nothing
here is a claim about verified Nobitex execution cost.

### 0.1 Sessions are a research convention

BTC trades continuously. There is no exchange open, no closing auction, and no settlement halt. The
three UTC sessions below are a **research convention** used to anchor an intraday decision, nothing
more. This specification explicitly does **not** claim that the equity-index intraday-momentum result
(Gao–Han–Li–Zhou) transfers to BTC. The session definition is a design choice that the census must
test, including a single-session sensitivity, and a null result is a genuine refutation of the
candidate rather than a failure of the convention.

### 0.2 The statistical framing is not a result

The 150-event threshold is the project's frozen protocol choice from Stage 2C. It is not derived from
a power calculation and does not guarantee adequate power. The 349-observation figure is a planning
estimate for a `0.15R` effect at 1R outcome standard deviation, 5% two-sided significance, 80% power,
and **independent** observations. Clustered signals are not independent observations. Kish's
effective sample size is a concentration diagnostic, not an estimate of serial dependence, and a
census cannot identify the dependence structure of outcomes it never observes.
`0.15 - median_cost_R` is a design-margin diagnostic under stated assumptions; it is not measured
expectancy and not profitability.

---

## 1. Data, interval, and timeframes

| item | value |
|---|---|
| Signal timeframe | 15m |
| Regime / volatility-budget timeframe | 4h |
| Stop-reference timeframe | 1h |
| Execution / entry timeframe | 15m |
| Alignment diagnostic timeframe | 5m |
| 15m dataset | `backend/data/datasets/BTCUSDT-15m-20210101-20260901.json` |
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
candle whose `open_time_ms == dev_start_ms` is **included**; a candle whose `open_time_ms ==
dev_end_ms` is **excluded**. The run asserts `min(open_time_ms) >= dev_start_ms` and
`max(open_time_ms) < dev_end_ms` for every timeframe read. No pre-development bar is used for
warm-up. Validation and out-of-sample data are not read, parsed, or summarised.

**Timestamp convention.** Every timestamp is UTC; internally the runner uses integer epoch
milliseconds. A bar's `open_time` is its first instant; its `close_time` is the last included
instant, so `close_time_ms = open_time_ms + duration_ms - 1`. On the 15m grid,
`close_time_ms = open_time_ms + 899,999`; on 1h, `+3,599,999`; on 4h, `+14,399,999`. The 15m, 1h, and
4h grids are mutually aligned.

**Candle availability (C4).** A candle is **available** at decision instant `T` if and only if
`close_time_ms <= T`. A candle whose `close_time_ms == T` **is available**; the same-bar-close
equality is explicitly permitted. This one convention governs ATR, VWAP, percentile windows, the
volatility budget, and signal confirmation. A decision taken at a bar's close uses only values
knowable at that `close_time` and is acted on at the next executable bar's `open_time`. Availability
is necessary but not sufficient: a candidate-specific selection rule may be stricter (for example the
4h budget requires the 4h bar to close before the signal instant), but never looser.

**Why 15m and not 5m.** Fifteen minutes gives 32 bars per eight-hour session and eight bars in the
two-hour measurement window. Five-minute bars would double the bar count without changing any
decision point in this specification, which only reads the window's first open and last close.

---

## 2. Bar usability and segments

### 2.1 15m bar usability

A 15m bar is **usable** if and only if all of the following hold:

| check | requirement | failure label |
|---|---|---|
| present | a bar exists at the expected `open_time` | `missing_bar` |
| closed | `is_closed == True` | `unclosed_bar` |
| on grid | `open_time` is a multiple of 15 minutes, seconds `0` | `offgrid_bar` |
| traded | `volume > 0` and `trade_count > 0` | `zero_volume_bar` |
| complete bucket | the bucket contains its full 3 members on the 5m grid (unless the 5m series is absent, in which case the check is skipped and recorded) | `partial_bar` |
| valid prices | `open > 0`, `high >= low`, `high >= max(open, close)`, `low <= min(open, close)` | `invalid_ohlc` |

Duplicate `open_time` values: keep the **first** in file order, discard the rest, report the count. No
averaging or merging.

### 2.2 Sessions are the segmentation unit, but signal eligibility is the first eight bars (C1)

A **session bucket** is exactly 32 consecutive 15m bars, beginning at a session start in §3. The
session is the episode unit for identity and deduplication, but it is **not** the eligibility test
for a signal.

A session is **signal-evaluable** only if its **measurement window** `b0 .. b7` — the eight 15m bars
opening from `s` through `s + 1h45m` — are all usable and exactly 15 minutes apart. If any of those
eight bars is missing or unusable, the session is marked `measurement_window_incomplete` and
produces no signal. Bars are never synthesised or forward-filled, and a partial measurement window is
never padded.

**The 32-bar completeness check is a diagnostic, not a selector (C1).** After the signal has been
determined from `b0 .. b7`, the run records a boolean `session_full_data` that is true only if all 32
session bars are usable and exactly 15 minutes apart. A false `session_full_data` **cannot** remove,
defer, or relabel a signal. The census reports how many signals came from sessions with late-session
gaps, so the data-quality conditioning is visible without allowing future bars (`b8 .. b31`, opening
up to `s + 7h45m`) to decide whether a signal at `s + 2h` exists.

This is a deliberate change from version `1.0.0`, which required all 32 bars and therefore selected
the signal set using future data. If a future hypothesis genuinely requires a full session, the
signal instant must move to `s + 8h`, which is a different candidate and requires a new specification;
it is not an option under this version.

### 2.3 1h and 4h bar usability and the shared 4h exemption (M3)

The 1h series has seven registered gaps (14 missing bars) and is segmented as in the shared protocol.
A 1h bar is usable under the same rules as §2.1 with a 12-member bucket requirement. The 4h series is
registered gap-free (12,414 bars = 12,414 expected) and is used as supplied; if a 4h bar is missing or
unclosed at run time, the volatility budget is `Unknown` for the affected span, no signal is emitted
there, and the 4h ATR segment resets as defined in shared protocol §1.7.

**Explicit shared 4h supplied-bar exemption.** The supplied 4h series is exempt from the 5m
membership check in shared protocol §1.3. The twelve 4h buckets that straddle the seven registered 5m
gaps are retained **as supplied**, because the vendor close is a real last-trade price and the budget
is slow. This is an explicit protocol exception, not an accidental omission. The run reports how many
such buckets were used (expected: 12) and computes a **non-decision sensitivity** in which those 12
buckets are excluded and the 4h ATR is segment-broken at them. The sensitivity is a diagnostic only;
it cannot change the primary signal set, the verdict, or any denominator.

---

## 3. UTC session boundaries

Three sessions per UTC day, each eight hours:

| session id | start (inclusive) | end (exclusive) | bars | measurement window | signal instant |
|---|---|---|---|---|---|
| `ASIA` | `00:00:00` | `08:00:00` | 32 | bars opening `00:00` … `01:45` | close of the `01:45` bar = `01:59:59.999` |
| `EUROPE` | `08:00:00` | `16:00:00` | 32 | bars opening `08:00` … `09:45` | close of the `09:45` bar = `09:59:59.999` |
| `US` | `16:00:00` | `24:00:00` | 32 | bars opening `16:00` … `17:45` | close of the `17:45` bar = `17:59:59.999` |

Rules:

- **Boundary ownership.** A bar belongs to the session that contains its `open_time` under
  `[start, end)`. The bar opening at `08:00` belongs to `EUROPE`, not `ASIA`; the bar opening at
  `16:00` belongs to `US`. No bar belongs to two sessions.
- **No overlapping sessions.** The three sessions partition the UTC day exactly; their union is
  `[00:00, 24:00)`.
- **No session crosses midnight.** `US` ends exactly at `24:00`, which is the next day's `00:00`
  start of `ASIA`. Because the measurement window is the first two hours, no return, VWAP, or
  threshold calculation ever spans a UTC date change.
- **No signal at a session boundary.** A signal exists only at the close of the eighth measurement
  bar. The boundary instant itself produces nothing.
- **DST.** Sessions are fixed UTC offsets and do not shift with daylight saving. A DST-shifted
  alternative is a sensitivity at most, and is not in the primary specification.

**Why these three.** They are the conventional Asia/Europe/US windows and they divide the day evenly,
which keeps the first-two-hour rule identical across sessions. Nothing in the repository or the
literature implies these exact hours are economically special for BTC; that is precisely what the
per-session split and the `US`-only sensitivity are designed to expose. A finding that the effect
exists only in one arbitrary eight-hour window would be evidence of data mining, and must be reported
as such.

---

## 4. First-two-hour directional signal

### 4.1 Return

For a session with start `s`, let bar `b0` be the 15m bar opening at `s`, and bar `b7` the 15m bar
opening at `s + 1h45m`. Define:

```
P0 = open[b0]
P1 = close[b7]
r2 = (P1 / P0) - 1
```

The measurement window is exactly the eight bars `b0` … `b7`, i.e. `[s, s + 2h)`.

**Why the open of the first bar, not the prior close.** The prior close belongs to the previous
session and would make `r2` partly a cross-session gap return, which is a different hypothesis (an
overnight-gap effect). Using the session's own first open keeps `r2` a within-session quantity.

### 4.2 Threshold

Let `q` be the **expected 1h bar opening at `s + 1h`** (the `01:00`, `09:00`, or `17:00` bar for the
three sessions). Its `close_time` is exactly the signal instant `T = s + 1h59m59.999s`, so the
availability convention permits equality: `close_time_ms[q] == T`. No later bar is read. The
selection is **not** a search or a fallback: if the expected `q` bar is missing, unclosed, off-grid,
zero-volume, or otherwise unusable under §2.3, the session is rejected with `stop_atr_unavailable`
rather than silently using an earlier, stale hour (m9). Define:

```
ATR1h[q]  = Wilder ATR(14) on 1h true range, segment-scoped, constructed exactly as shared protocol §1.7
thr       = 0.5 * ATR1h[q] / P0
```

The signal condition is:

```
r2 >= thr        AND        P1 > VWAP_session
```

`thr` is dimensionless because it is expressed relative to `P0`. The Stage 2D text wrote the
threshold as "`+0.5 x ATR(14, 1h)`", which mixes a price distance with a return; dividing by `P0` is
the only reading that makes the comparison well defined, and it is frozen here.

**Signal instant:** the `close_time` of `b7`. The signal does not exist before the two hours are
complete: `r2` cannot be computed from a partial window, and no partial-window variant is permitted.

**Warm-up (M6).** `ATR1h[13]` is the first defined value (the mean of `TR[0..13]`). The first **13**
bars of a 1h segment (local indices `0..12`) are warm-up. A `q` at local index `13` or later is
testable. A session whose `q` is at local index `0..12` is counted `warmup_atr` and produces no
signal. Version `1.0.0` said "first 14 bars", which over-excluded one `q` bar per segment; version
`2.0.0` corrects this to 13.

---

## 5. Session VWAP

**One definition only.** The alternative rolling VWAP from Stage 2D is rejected, because a rolling
24-hour VWAP would mix the previous session's prices into a session-relative decision and would make
the "intraday" claim depend on an arbitrary lookback. The choice is session VWAP.

For the session beginning at `s`, over the closed 15m bars `i` in `[s, s + 2h)` (the same eight bars
as the measurement window):

```
HLC3[i]  = (high[i] + low[i] + close[i]) / 3
VWAP     = Σ_i (HLC3[i] * volume[i]) / Σ_i volume[i]
```

Requirements and edge cases:

| case | rule |
|---|---|
| any `volume[i] == 0` | bar is unusable (§2.1), so the session is not evaluable |
| total volume over the window `== 0` | cannot occur in a signal-evaluable session, because every measurement bar requires `volume > 0`; the run asserts this and aborts on a violation (`schema_error`) |
| missing `volume` field | the specification is not applicable; abort the census (`schema_error`) |
| `quote_volume` present | recorded as an alignment diagnostic only; it is **not** the primary VWAP input |
| reset | the accumulator starts at each session start; nothing is carried across sessions |
| initialization | no seed value; VWAP exists from the first bar of the window |

**Condition:** `P1 > VWAP` is evaluated at the confirmation bar (`b7`, the signal bar) and nowhere
else. It is not re-evaluated at the entry bar, because entry happens one bar later and re-testing
would introduce a second decision point that Stage 2D did not define.

**Why typical price rather than quote-volume VWAP.** `Σ quote_volume / Σ volume` is an exact traded
VWAP and is preferred when the field is trustworthy, but this project's Stage 2A/2C audits did not
verify `quote_volume` on the 15m series. Typical-price VWAP needs only `volume`, is a standard
approximation, and is reproducible from the documented schema. The exact variant is recorded as a
diagnostic so the approximation is measurable.

---

## 6. Higher-timeframe volatility budget

### 6.1 Which 4h bar a session may read

A session whose signal instant is `T` reads the **most recent 4h bar whose `close_time` is strictly
less than `T`**. At the ASIA signal instant `01:59:59.999` that is the 4h bar opening at `20:00` on
the previous day; at `EUROPE` (`09:59:59.999`) it is the bar opening at `04:00`; at `US`
(`17:59:59.999`) it is the bar opening at `12:00`. An unfinished 4h candle is never read. If the
required 4h bar is missing or unclosed, the budget is `Unknown` and the session produces no signal.

### 6.2 Formula

Using closed 4h bars, at 4h bar `q`:

```
ATR4h[.] = Wilder ATR(14) on 4h true range, constructed exactly as shared protocol §1.7
pct[q]   = 100 * (count of ATR4h values in the 540-bar window [q-539 .. q]
                  that are strictly less than ATR4h[q]) / 540

budget_ok[q] = (25.0 <= pct[q] <= 80.0)
```

**4h ATR construction (M1).** The 4h ATR is fully specified in shared protocol §1.7:

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

All comparisons are inclusive exactly as written. `budget_ok` is `True`, `False`, or `Unknown`
(before the first computable value, or on a missing/unclosed 4h bar).

**The two Stage 2D formulations are resolved in favour of one.** Stage 2D offered (a) daily ATR(14)
inside its trailing-90-day percentile band and (b) 4h realised volatility between 0.5× and 1.5× its
30-day median. Option (b) is rejected here: a ratio band around a median can be satisfied in both a
dead market and a crisis market if the median itself has moved, it adds a second lookback, and it
does not say where the current regime sits in its own distribution. Option (a) is adopted in
**4h** form rather than daily, because daily bars are not in the dataset and aggregating them would
introduce a new synthetic series that the architecture review flagged as an open gap. The 4h ATR
percentile is causal, uses a supplied timeframe, and is the same construction the B regime filter
uses, so the two candidates share one volatility definition.

**Why this band.** The lower bound (25th percentile) removes dead markets where a two-hour move
cannot clear costs. The upper bound (80th percentile) removes crisis states in which the first move
is a liquidity shock and the remainder of the session tends to revert — the failure mode the
volatility budget exists to address. The band is a design choice, not a fitted parameter. It is
wider at the bottom and tighter at the top than B's band because D trades a shorter horizon and is
more exposed to whipsaw.

**Percentile construction.** The window is 540 consecutive 4h bars ending at `q` inclusive, so the
current bar participates in its own percentile. This is causal, and it makes the upper bound behave
as intended: a crisis 4h ATR ranks near the top of its own window. The leading-edge count is an exact
rational number and is reproducible without interpolation.

**Warm-up and incomplete windows (m4).** `ATR4h` first exists at 4h index 13; the 540-value window is
fully populated at index 552, the 4h bar opening `2021-04-03T00:00:00Z` and closing at
`2021-04-03T03:59:59.999Z`. The eligibility boundary is therefore
`2021-04-03T04:00:00Z`: a session whose signal instant is **at or after** that instant may read a
complete window, and a session whose signal instant is earlier is excluded as `warmup_budget`. Because
D's signal instants are `01:59:59.999`, `09:59:59.999`, and `17:59:59.999`, the first **actual**
eligible session is `EUROPE` on 2021-04-03 at `09:59:59.999Z`; `ASIA` on the same date (signal instant
`01:59:59.999Z`) is still excluded. `2021-04-03T04:00:00Z` is a threshold, not a signal instant. This
is 92 days of the 1,277-day interval. If any value inside the window is undefined or missing — which
can only happen after a 4h gap — the percentile is `Unknown` and the session produces no signal. A
percentile computed over a truncated window is never reported.

**No intra-session re-evaluation.** The budget is evaluated once, at the signal instant, and is fixed
for that session's decision. It is not re-checked at entry, because entry follows one 15m bar later
and a second evaluation would be a second, undefined decision point.

---

## 7. Entry, stop, and cost

### 7.1 Entry

**Entry bar:** the 15m bar whose `open_time` equals `open_time[b7] + 15m`.
**Entry price:** that bar's `open`.

**Entry-time validation (M2).** The entry decision is made at the signal instant and executed at the
entry bar's open. Only properties knowable at that open may reject the signal:

| check at entry | requirement | failure label |
|---|---|---|
| present | a bar exists at the expected `open_time` | `no_entry_bar` |
| on grid | `open_time_ms` is exactly `open_time_ms[b7] + 900,000` | `no_entry_bar` |
| inside interval | `open_time_ms < dev_end_ms` | `entry_outside_interval` |
| positive open | `open > 0` | `invalid_entry_price` |
| prior context | the measurement window and signal are fixed | (guaranteed by construction) |

The entry bar's **close-time** properties — `is_closed`, `volume > 0`, `trade_count > 0`, complete
5m bucket, full-bar OHLC validity — are **not** selection criteria. They are recorded as post-count
data-quality diagnostics and cannot remove a signal that was executable at the open.

A missing entry bar **rejects the signal**; the run never skips forward. Skipping would price the
trade at a moment that is not the first moment after the signal.

**Development-end guard (M5).** If the entry bar would open at or after `dev_end_ms =
1719792000000` (`2024-07-01T00:00:00Z`), the signal is rejected with `entry_outside_interval`; it is
**not** silently dropped and **not** completed from a validation bar. The same guard applies to any
bar the signal would need at or after the boundary. A signal may use only bars whose `open_time_ms`
is inside `[dev_start_ms, dev_end_ms)`.

### 7.2 Structural stop

```
S      = entry_open - 1.0 * ATR1h[q]
D      = entry_open - S = ATR1h[q]
stop_fraction = D / entry_open          (dimensionless fraction; displayed as a percent only in prose)
```

`ATR1h[q]` is the value fixed at the signal instant (§4.2) and is **not** recomputed at entry. The
resulting stop is the only structural stop in the specification; there is no session low, VWAP, or
swing-low variant.

**No artificial minimum stop and no widening.** The Stage 2D text proposed "or a hard 1.30% floor,
whichever is farther", which would widen a tight stop to clear the cost gate. That is rejected: it
lowers `cost_R` arithmetically while increasing notional per unit of risk, and it turns an execution
constraint into a parameter. A stop tighter than 1.30% is counted and fails the gate as `cost_gate`.

**Invalid stop** (`invalid_stop`) if `ATR1h[q] <= 0`, `stop <= 0`, `entry_open <= 0`, or `D <= 0`.

### 7.3 Cost

```
cost_R = 0.0026 * entry_open / D
```

**Primary gate:** `cost_R <= 0.20`, equivalent at 26 bp to `stop_fraction >= 0.013` (1.30%). Buckets
and cost sensitivities are identical to the shared protocol: `(-inf, 0.10]`, `(0.10, 0.20]`,
`(0.20, 0.30]`, `(0.30, 0.50]`, `(0.50, +inf)`, recomputed at 10, 26, 39, and 52 bp with the gate
unchanged. Endpoint inclusion is explicit: the upper endpoint belongs to the lower bucket in every
case (m2).

Because `D = ATR1h[q]`, D's `cost_R` is determined almost entirely by the 1h ATR relative to price.
At a 1.30% stop the gate is exactly at its boundary, which is the central economic tension of this
candidate and must be reported, not smoothed: the median `cost_R` is expected to sit near the gate
rather than comfortably below it.

---

## 8. Deduplication and episode identity

### 8.1 The session is the episode

Candidate D has **one opportunity per session**, by construction:

- the measurement window is fixed at the first two hours, so there is exactly one signal instant;
- no second measurement window exists inside a session;
- a session that fails any filter produces no signal and is not retried later in the same session.

Therefore "deduplication" for D is not a selection among competing signals; it is the assertion that
the session key is unique and that each key appears at most once. The census verifies it and reports
`duplicate_session` removals, which must be zero.

### 8.2 Adjacent sessions and midnight

Adjacent sessions are **distinct opportunities**, not duplicates. A `EUROPE` signal is six hours after
an `ASIA` signal and both are valid pre-non-overlap; the 24h non-overlap rule (§9), not deduplication,
decides which survives. The same applies across midnight: a `US` signal at 18:00 and the next day's
`ASIA` signal at 02:00 are eight hours apart and both are counted before non-overlap.

A signal never straddles midnight: the measurement window is the first two hours of its session, and
the `US` session ends at `24:00` with its signal at `18:00`.

### 8.3 Deterministic identity

```
D:{session_start_iso8601_utc}|{session_id}
```

e.g. `D:2021-06-01T00:00:00+00:00|ASIA`. The key depends only on the session start and its id, so it
is stable across reruns and implementations. Because sessions partition the day and ids are unique
within a day, no two sessions can share a key.

**Conflict resolution** is therefore only needed for the hypothetical case of two signals sharing an
`entry_time`; the lexicographically smaller key is retained and the other is labelled
`duplicate_entry`. Under the one-signal-per-session rule this cannot occur.

---

## 9. Non-overlap policy

### 9.1 Canonical 24-hour rule

**Population:** unique cost-feasible signals after the cost gate and deduplication.

**Algorithm:**

1. Sort by `entry_time` ascending; ties broken by session key ascending (ISO string, then session id
   in the order `ASIA < EUROPE < US`).
2. Accept the first signal.
3. Accept each subsequent signal whose `entry_time` is **at least** 24 hours after the most recently
   accepted signal's `entry_time`. Exactly 24 hours qualifies.
4. Rejected signals are labelled `non_overlap` and retained for audit.

**Timestamp used:** `entry_time`, not the signal instant and not the session start. Entry time is
what determines when capital would be committed.

**Boundary:** inclusive.

**Order of application:** after cost feasibility. Non-overlap never changes whether a signal is
cost-feasible; rejected signals remain in the cost distribution.

### 9.2 Why 24 hours, and what it costs

The maximum intended holding period is the session, at most eight hours, so a 24-hour separation is
stricter than the holding period requires. It is retained because the candidate's claim is
"intraday continuation", and counting three signals in one day as three independent opportunities
would overstate frequency in exactly the dimension the census is trying to measure. The rule is a
frequency-conservatism choice, not an exit rule, and it is frozen before counting.

### 9.3 Sensitivities

The 12-hour and 48-hour counts use the identical greedy algorithm over the same population, changing
only the threshold. They are diagnostics; the canonical decision count is the 24-hour count. A
48-hour count that falls below the project floor while the canonical count passes does **not**
rescue or condemn the candidate by itself; both are reported, and the canonical number governs.

---

## 10. Counting pipeline and exclusion accounting

Each rejection has exactly one **primary** reason, assigned in the order below; secondary reasons are
also recorded and reported.

```
S1  usable 15m bars in the development interval
S2  signal-evaluable sessions          b0..b7 all usable and exactly 15m apart
S3  directional signals                r2 >= thr                       (raw signal candidates)
S4  volatility-budget qualified        budget_ok == True
S5  structurally valid                 P1 > VWAP_session
S6  valid entry and stop               entry-bar open known, D > 0      (pre-cost-gate)
S7  cost-feasible                      cost_R <= 0.20
S8  deduplicated                       one per session (verified; expected unchanged)
S9  non-overlapping                    greedy 24h, canonical
```

`S0` is a reported diagnostic denominator, not a pipeline stage: the count of session buckets whose
signal instant lies in `[dev_start_ms, dev_end_ms)`. `session_full_data` is a separate post-count
diagnostic over all 32 bars; it never removes a signal (C1).

Exclusion labels:

| label | stage |
|---|---|
| `measurement_window_incomplete` | S2: any of `b0..b7` missing or unusable, or not 15m apart |
| `stop_atr_unavailable` | S3: expected 1h `q` bar missing, unclosed, off-grid, zero-volume, or otherwise unusable (m9) |
| `warmup_atr` | S3: `q` at 1h local index `0..12`; `ATR1h[q]` undefined (M6) |
| `below_threshold` | S3: `r2 < thr` |
| `warmup_budget` | S4: no computable 4h budget at the signal instant |
| `budget_out_of_band` | S4: `pct[q] < 25` or `pct[q] > 80` |
| `below_vwap` | S5: `P1 <= VWAP` |
| `no_entry_bar` | S6: entry bar absent or not the next 15m bar |
| `entry_outside_interval` | S6: entry bar opens at or after `dev_end_ms` |
| `invalid_entry_price` | S6: entry open <= 0 |
| `invalid_stop` | S6: `ATR1h[q] <= 0`, `stop <= 0`, or `D <= 0` |
| `cost_gate` | S7: `cost_R > 0.20` |
| `duplicate_session` | S8: repeated session key (expected 0) |
| `non_overlap` | S9: within 24h of an accepted signal |

The following are **post-count data-quality diagnostics**, never primary rejection labels (M2):
`unclosed_entry_bar`, `zero_volume_entry`, `partial_entry_bar`, and `invalid_entry_ohlc`.

### 10.1 Denominator definitions

| reported quantity | numerator | denominator |
|---|---|---|
| `session_completeness` | S2 | `S0` = all session buckets whose signal instant is in the development interval |
| `threshold_pass_share` | S3 | S2 |
| `budget_pass_share` | S4 | S3 |
| `vwap_pass_share` | S5 | S4 |
| `entry_validity_share` | S6 | S5 |
| `feasible_share` | S7 | S6 |
| `unique_share` | S8 | S7 |
| `nonoverlap_share` | S9 | S8 |

The `session_completeness` denominator is `S0`, a concrete population. It is **not** "after
warm-up": warm-up exclusions (`warmup_atr`, `warmup_budget`, `stop_atr_unavailable`) are counted
separately at S3/S4 from the full `S0` population, so the reported rate cannot change with an
implementation's reading of "warm-up" (m8). The `session_full_data` diagnostic is reported separately
against `S0`.

`feasible_share` is measured against S6 (structurally valid signals with a valid entry and stop),
never against S2 or S3. A large session count with a small feasible share is a rejection, not a large
sample.

**Cost-median populations (C2).** `M_all = median(cost_R over S6)` is the verdict median and
includes signals that fail the cost gate. `M_feasible = median(cost_R over S7)` is a post-gate
diagnostic bounded above by `0.20` by construction. If `S6` is empty, `M_all` is undefined, the
census is `INCONCLUSIVE`, and the verdict cannot be `PASS` or `PASS WITH LIMITATIONS`.

---

## 11. Required diagnostics

Every future D census must report, at minimum:

1. **Pipeline counts** S1–S9 with all exclusion labels, primary and secondary.
2. **Session accounting:** `S0` total sessions, flag-evaluable sessions, per session id, the `US`-only
   variant, and the post-count `session_full_data` counts (including signals from sessions with late
   gaps). The 32-bar completeness diagnostic cannot remove a signal (C1).
3. **`cost_R` distribution** of all S6 signals: bucket counts and percentages, `M_all` (median), mean,
   p25, p75, p90, min, max, and the count passing at 10, 26, 39, and 52 bp. Report `M_feasible` over
   S7 separately, labelled as the post-gate diagnostic.
4. **Stop-distance distribution** in USDT and as a percentage of entry, plus the share below 1.30%
   (expected to be large; this is the candidate's central economic risk).
5. **Non-overlap counts** at 12h, 24h (canonical), and 48h, with spacing distribution.
6. **Calendar counts** by year and by month, for S7 and S9.
7. **Regime counts** by 4h percentile decile, by `budget_ok` state, and by session id.
8. **Cluster concentration**: signals per **Kish cluster** as defined in shared protocol §3.1
   (maximal runs of consecutive usable 4h bars with `budget_ok == True`), reporting count, median,
   p90, maximum, largest-cluster share; plus calendar-month, calendar-quarter, and session-id views.
9. **Kish diagnostic** over the same `budget_ok == True` clusters, with cluster count, design effect,
   and an `n_eff` sensitivity to assumed `rho` in {0.25, 0.50, 0.75, 1.00}. A cluster is a maximal
   run; `False` or `Unknown` breaks it; a missing/unusable 4h bar breaks it. Concentration diagnostic
   only.
10. **Detectable-effect reference** `2.801585 / sqrt(N_nonoverlap)`, labelled as a planning
    calculation under independence.
11. **Capital geometry** at $10,000 and 1% risk. With `stop_fraction = D / entry_open` (a
    dimensionless fraction, not a percent),
    `notional_usd = risk_usd / stop_fraction = 100 / stop_fraction`. Report the distribution of
    `notional_usd` and `notional_pct = notional_usd / equity_usd`, the count whose notional exceeds
    equity, the maximum number of concurrently open session windows, and the count of signals a
    one-position cash policy would have to skip. The numeric impracticability condition is
    `notional_pct > 1.00` for any signal (M10).
12. **Data-alignment audit** (gap-aware, shared protocol §1.6) and **resource usage**.

No outcome-based metric is reported.

### 11.1 Worked synthetic example (arithmetic check only)

The numbers are **invented**; they are not market data.

Session: `ASIA`, start `2021-06-01T00:00:00Z`.

| quantity | value |
|---|---:|
| `P0` = open of the `00:00` bar | 30,000.0 |
| `P1` = close of the `01:45` bar | 30,600.0 |
| `r2` = `P1/P0 - 1` | 2.00% |
| `ATR1h[q]`, `q` = the `01:00` bar | 1,000.0 |
| `thr` = `0.5 * 1000 / 30000` | 1.6667% |
| threshold check | 2.00% ≥ 1.6667% ✓ |
| `VWAP` over the eight bars | 30,200.0 |
| VWAP check | 30,600 > 30,200 ✓ |
| `pct[q]` | 63 → inside [25, 80] ✓ |
| signal instant | `2021-06-01T01:59:59.999Z` |
| entry bar / price | `02:00` bar, open 30,610.0 |
| stop = `30610 - 1000` | 29,610.0 |
| `D` | 1,000.0 |
| `stop_fraction` = `1000 / 30610` | 0.032669 (displayed as 3.2669%) |
| `cost_R = 0.0026 * 30610 / 1000` | 0.0796 (passes) |
| `notional_usd = 100 / 0.032669` | $3,060.99 (30.61% of $10,000 equity) |
| key | `D:2021-06-01T00:00:00+00:00\|ASIA` |

Had `ATR1h` been 200, `stop_fraction` would be `200/30610 = 0.006534` (0.6534%) and `cost_R` 0.398,
failing the gate. That contrast is the candidate's economic risk in one line.

---

## 12. Acceptance criteria and decision rule

Three concepts are kept separate:

1. **Protocol compliance** — did the census execute this specification exactly? Hash match, alignment
   pass, session accounting reconciled, causality checks passed.
2. **Structural feasibility** — does the candidate produce enough cost-feasible, non-overlapping,
   deduplicated opportunities?
3. **Economic viability** — has a positive net edge been demonstrated? **A census cannot answer this.**
   It observes no outcome and must never be reported as evidence of profitability.

Let `N = N_nonoverlap` (24h canonical), `M_all = median cost_R over S6` (the pre-gate valid
entry/stop population), `M_feasible = median cost_R over S7` (post-gate diagnostic), `F =
feasible_share = S7/S6`, and `E = 0.15 - M_all`.

| verdict | condition |
|---|---|
| **INCONCLUSIVE** | hash mismatch; dataset hash mismatch; alignment failure in a field the design reads; a causality check fails; S8 ≠ S7 for an unexplained reason; or the S6 population is empty so `M_all` is undefined |
| **FAIL** | `N < 150`; or `M_all > 0.20`; or any signal has `notional_pct > 1.00` (capital geometry impracticable under spot cash) |
| **PASS WITH LIMITATIONS** | `150 <= N < 349` and `M_all <= 0.20`, all compliance checks passed |
| **PASS** | `N >= 349` and `M_all <= 0.20`, all compliance checks passed |

`M_all` is the verdict median because S6 includes the signals that fail the cost gate. Using S7 would
make `M_all <= 0.20` true by construction and `M_all > 0.20` impossible (C2). `M_feasible` is
reported for transparency but cannot satisfy or fail the cost condition.

The `349` boundary in the top tier is the independent-sample planning reference carried forward from
Stage 2C, used as a tier label for comparability. It is not a requirement, it does not guarantee
power, and reaching it does not establish an edge. A `PASS` here means only that the structural count
clears the larger reference; it says nothing about profitability.

`E` is reported with its assumptions: an **assumed** `0.15R` effect of interest and a Binance-proxy
cost. It is not net expectancy and not profitability.

### 12.1 Proposed additional thresholds (require approval before counting)

From Stage 2D, **not** yet approved protocol:

| proposed threshold | rationale | status |
|---|---|---|
| `F >= 0.30` | D's stops are near the gate; a low feasible share would mean the surviving sample is a narrow, possibly unrepresentative slice | **proposed, requires approval** |
| `M_all <= 0.17` | leaves at least `0.03R` of the assumed effect, and `0.15 - M_all > 0` with a margin; defined on the same pre-gate S6 population as the verdict median | **proposed, requires approval** |
| design margin `E >= 0.02` | the workbook preference for a positive margin rather than a coin flip | **proposed, requires approval** |

None is part of the primary verdict above. Adoption requires a new spec version frozen before
counting. No threshold may be added after seeing counts. The proposed economic median is defined on
`M_all`, not `M_feasible`; the post-gate median is already bounded by `0.20` and cannot carry an
economic threshold (C2).

### 12.2 What 150 and 349 do and do not mean

150 is the project's frozen protocol threshold from Stage 2C with no statistical derivation; it is
not a universal requirement and does not guarantee power. 349 is an independent-observation planning
estimate and is optimistic under clustering and fat tails. Neither converts a census count into
evidence of an edge.

---

## 13. What this census does not do

- No trade is entered, resolved, or marked to market.
- No P&L, return, expectancy, win rate, drawdown, Sharpe, CAGR, or profitability figure is computed.
- No backtest, portfolio simulation, bootstrap, or Monte Carlo is run.
- No parameter is optimized or swept in the decision path; thresholds, session ids, and the budget
  band are frozen here and may not be tuned.
- No validation or out-of-sample observation is read, parsed, summarised, or used.
- No frozen Stage 2A, 2B, 2C, 2D, Stage 6, Stage 6A, or Setup 1 artifact is modified.
- No discretionary visual interpretation is permitted at any stage.

---

## 14. Freeze record

**Spec version:** `2.0.0`.
**Frozen artefact:** `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md`.
**Configuration:** `docs/research/stage2e_v2/CANDIDATE_D_CONFIG.json` (values identical to this file;
JSON is the runner's source).
**Manifest:** `docs/research/stage2e_v2/FREEZE_MANIFEST.json` records the SHA256 of this file, the
configuration, the shared protocol, the dataset files, the original Stage 2E hashes, the Stage 2F
audit hash, the development interval, the cost assumptions, the protocol version, the freeze
timestamp, every Stage 2F finding's resolution status, and an explicit statement that no census has
run.

Any parameter change requires a new spec version, a new configuration, a new manifest, and explicit
approval. A runner must abort when file hashes do not match the manifest.
