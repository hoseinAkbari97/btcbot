# Stage 2E — Candidate D Frozen Specification

**Candidate:** D — intraday continuation with a higher-timeframe volatility budget.
**Spec version:** `1.0.0`
**Status:** Specification and protocol design only. No market data has been read, no signal has been
counted, no census has been run, and no trade outcome has been computed.
**Companion configuration:** `docs/research/STAGE2E_CANDIDATE_D_CONFIG.json`
**Shared protocol:** `docs/research/STAGE2E_SHARED_CENSUS_PROTOCOL.md`

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

Dataset SHA256 values are recorded in the freeze manifest. Row filtering to the development interval
happens by ISO-string comparison on `open_time` before any numeric conversion. No pre-development bar
is used for warm-up. Validation and out-of-sample data are not read, parsed, or summarised.

**Timestamp convention.** Every timestamp is UTC with an explicit `+00:00`. A bar's `open_time` is its
first instant; its `close_time` is its last. A decision taken at a bar's close uses only values
knowable at that `close_time` and is acted on at the next executable bar's `open_time`. On the 15m
grid, `close_time = open_time + 14:59.999`; on 1h, `+59:59.999`; on 4h, `+3:59:59.999`. The 15m, 1h,
and 4h grids are mutually aligned.

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

### 2.2 Sessions are the segmentation unit

A **session bucket** is exactly 32 consecutive 15m bars, beginning at a session start in §3. A session
is **evaluable** only if all 32 bars are usable and exactly 15 minutes apart. If any bar is missing or
unusable, the session is marked `session_data_incomplete` and produces no signal. Bars are never
synthesised or forward-filled, and a partial session is never padded.

This is stricter than Stage 2C, which allowed an episode to end at a segment break. Here the whole
session is the unit, because both the measurement window and the signal definition assume a full
eight-hour bucket.

### 2.3 1h and 4h bar usability

The 1h series has seven registered gaps (14 missing bars) and is segmented as in the shared protocol.
A 1h bar is usable under the same rules as §2.1 with a 12-member bucket requirement. The 4h series is
registered gap-free (12,414 bars = 12,414 expected) and is used as supplied; if a 4h bar is missing or
unclosed at run time, the volatility budget is `Unknown` for the affected span and no signal is
emitted there.

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

Let `q` be the **last closed 1h bar whose `close_time` is strictly less than the signal instant**. At
the ASIA signal instant `01:59:59.999`, `q` is the 1h bar opening at `01:00`; at `EUROPE` it opens at
`09:00`; at `US` it opens at `17:00`. Define:

```
ATR1h[q]  = Wilder ATR(14) on 1h true range, segment-scoped, same construction as the shared protocol
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

**Warm-up:** `ATR1h` needs 14 bars of its segment. A session whose `q` falls in the first 14 bars of a
1h segment is counted `warmup_atr` and produces no signal.

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
| total volume over the window `== 0` | session not evaluable, `zero_volume_window` |
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

<!-- D_PART2 -->
