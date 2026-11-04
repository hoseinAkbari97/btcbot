# Stage 2J — Pre-Registered Analysis Plan

**Stage:** 2J (controlled feasibility census for Candidate B and Candidate D).
**Status:** pre-registered before any candidate rule is evaluated and before any signal is counted.
**Authorization:** the owner's separate, explicit Stage 2J census authorization, which overrides the
Stage 2I instruction not to start Stage 2J.
**Frozen baseline:** `docs/research/stage2e_v2/` version `2.0.0`, manifest SHA256
`adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7`, self-hash verified.
**Stage 2I baseline:** `docs/research/stage2i/`, manifest SHA256
`a7a7df57ea19b550804f91767338902091826c0646277352a5d7bfbd3c81b294`.
**Preflight evidence:** `docs/research/stage2j/machine_readable/preflight.json`.

This plan is a reporting and implementation-discipline document. It does **not** change any frozen
strategy parameter, signal rule, cost assumption, interval, population, or verdict condition. Where
the frozen text leaves an implementation detail open, the choice below is fixed **before counting**
and is applied identically on every rerun. No choice was selected by looking at a signal count.

---

## 0. What this census is and is not

The census answers two questions:

1. **Protocol compliance:** did the frozen B and D specifications execute exactly?
2. **Structural feasibility:** does each candidate produce enough cost-feasible, non-overlapping,
   deduplicated opportunities?

It does **not** answer whether either candidate is profitable. It observes no trade outcome and
computes no P&L, return, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR, equity curve, or
bootstrap/Monte Carlo interval. It does not optimise or tune anything. It does not read, decode,
slice, or summarise validation or out-of-sample rows.

The **150-opportunity floor is a project protocol choice** first fixed at the Stage 2C freeze. It is
not statistically derived and does not guarantee power. The **349 figure is an independence-based
planning reference** for a `0.15R` effect at 1R outcome standard deviation, 5% two-sided and 80%
power. It is not a requirement and does not establish an edge. Cluster concentration diagnostics do
not estimate serial dependence, and non-overlapping observations are **not** described as
independent observations.

---

## 1. Frozen inputs and run identity

### 1.1 Inputs

| item | value |
|---|---|
| development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| start / end as epoch ms | `1609459200000` / `1719792000000` |
| Candidate B | `CANDIDATE_B_SPEC.md` + `CANDIDATE_B_CONFIG.json` version `2.0.0` |
| Candidate D | `CANDIDATE_D_SPEC.md` + `CANDIDATE_D_CONFIG.json` version `2.0.0` |
| shared protocol | `SHARED_CENSUS_PROTOCOL.md` version `2.0.0` |
| datasets | `backend/data/datasets/BTCUSDT-{5m,15m,1h,4h}-20210101-20260901.json` |
| dataset manifest | `backend/data/datasets/manifest.json` |
| cost | 26 bp round trip, `0.0026` |
| gate | `cost_R <= 0.20` |
| B non-overlap | canonical 72h; sensitivities 24h and 120h |
| D non-overlap | canonical 24h; sensitivities 12h and 48h |

### 1.2 Run-time checks

Before any count, the runner re-computes:

- each frozen artefact SHA256 against the frozen manifest;
- the frozen manifest self-hash;
- the Stage 2H audit hash and the Stage 2I manifest/artefact hashes;
- all four dataset SHA256 values and the dataset-manifest hash;
- the development-interval minimum and maximum `open_time_ms` for every timeframe;
- that no change proposal CP-1…CP-5 has been applied.

Any mismatch aborts counting and yields `INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION`. The
runner records its git HEAD and a SHA256 of the counting code in the result manifest.

### 1.3 Interval isolation

The bounded loader inspects only the `open_time` string of the first record at or after
`dev_end_ms` and stops. That record's payload is never decoded. No validation or out-of-sample row
is yielded, parsed, sliced, or summarised. The census never reads network data.

---

## 2. Bounded-memory execution

The 5m file is the only large file (about 256 MB). It is never passed to `json.load`, and no list of
5m candle objects is built.

| item | implementation |
|---|---|
| JSON parsing | the Stage 2I `iter_object_texts` / `iter_candles` bounded loader |
| read buffer | 1 MiB (`CHUNK_SIZE`) |
| 5m handling | one streaming pass that increments compact per-bucket usable-member counters |
| retained candle objects | at most one typed `Candle` per active stream, never a full list |
| derived series | compact primitive arrays/lists (floats, small ints, booleans), not candle objects |
| signals | metadata for counted signals only; no outcome field exists |
| target / ceiling | 4 GiB target, 6 GiB hard ceiling |
| evidence | peak RSS, wall time, records yielded per timeframe, maximum raw object size, temp disk |

The 15m and 1h OHLC series are retained only as compact primitive arrays indexed by grid slot so the
session and episode rules can look up a bounded window. The 5m candle objects are never retained.
This is a deliberate memory trade: primitive arrays for 122,592 15m slots and 30,648 1h slots are a
few megabytes, while the 5m stream is discarded record by record.

---

## 3. Shared data-preparation decisions

### 3.1 Usable 5m members

A 5m record counts as a **usable member** of its 15m and 1h bucket only if it is:

- present at an on-grid 5m open time;
- `is_closed == True`;
- `volume > 0` and `trade_count > 0`;
- valid OHLC (`high >= low`, `high >= max(open, close)`, `low <= min(open, close)`).

Zero-volume 5m placeholders are therefore **not** members. This is the literal reading of "usable
members" in shared protocol §1.3 and is the reason a 1h bucket can be partial even when a record
exists at every expected 5m timestamp.

### 3.2 Partial buckets

- 15m usability requires exactly 3 usable 5m members.
- 1h usability requires exactly 12 usable 5m members.
- The check is skipped and recorded only if the 5m series is absent. It is present, so it is applied.
- 4h is exempt under the ratified M3 supplied-bar rule: it is **not** rebuilt from 1h or 5m and is
  retained as supplied, including the twelve registered gap-adjacent buckets.

### 3.3 4h usability

The supplied 4h series is usable when the record is present, `is_closed == True`, on-grid, has
positive close, positive volume/trade count, and valid OHLC. The actual supplied 4h series has no
missing, unclosed, off-grid, zero-volume, or invalid-OHLC records, so the shared §1.3 rules and the
narrower B/D §2.3 wording produce the same primary series. A missing or unusable 4h bar makes the
regime/budget `Unknown` and breaks the 4h segment.

### 3.4 Segments and warm-up

A segment is a maximal run of consecutive **usable** bars exactly one timeframe interval apart. Any
missing or unusable bar breaks the segment. No bar is synthesised, forward-filled, or interpolated.

- B 1h ATR: first defined at local index 13; expansion is testable at local index 14.
- B 4h regime: first computable permission at 4h index 552 (`2021-04-03T00:00:00Z`); first 1h open
  permitted to read it is `2021-04-03T04:00:00Z`.
- D 1h ATR: first defined at local index 13; a `q` at local index 13 or later is testable.
- D 4h budget: first computable at 4h index 552; the first actual eligible session is EUROPE
  `2021-04-03T09:59:59.999Z`.

Warm-up losses are reported, not treated as failures.

### 3.5 ATR construction

The shared Wilder construction is used at 1h and 4h:

```
TR[0] = high[0] - low[0]
TR[t] = max(high[t]-low[t], abs(high[t]-close[t-1]), abs(low[t]-close[t-1]))
ATR[13] = mean(TR[0..13])
ATR[t] = (ATR[t-1]*13 + TR[t]) / 14, t > 13
```

The recursion is segment-scoped. `ATR[t]` is undefined for `t < 13`. The seed and recursion are
verified against the frozen worked arithmetic check.

### 3.6 4h percentile and rolling windows

`pct[q]` is `100 * count(ATR4h values strictly less than ATR4h[q]) / 540` over the inclusive window
`[q-539, q]`. The window is admitted only if all 540 ATR values are defined and usable. The window is
segment-aware: a value from a different segment, or an undefined value, makes the percentile
`Unknown`. `SMA50` and `slope24` are likewise admitted only when their entire windows lie inside one
usable segment.

### 3.7 4h bar selection

For a decision instant `T`, the 4h bar read is the most recent one whose `close_time_ms < T`, which
on the aligned grid is `floor(T, 4h) - 4h`. A 4h bar whose close equals `T` is **not** read by the
regime/budget rule because both candidate rules require a strict close before the decision; this is
stricter than the general `close_time <= T` availability convention and is permitted because the
candidate rule is allowed to be stricter. If the required bar is absent or `Unknown`, the label is
`Unknown` and no signal is emitted under that rule.

### 3.8 4h supplied-bar sensitivity

The primary path uses the twelve registered gap-adjacent 4h buckets as supplied. A **non-decision
sensitivity** reruns the regime/budget series with those twelve slots marked unusable and the 4h ATR
segment-broken at them; rolling windows and percentiles become `Unknown` until their windows are
again complete. The sensitivity is reported as a diagnostic. It never changes the primary signal
set, denominator, or verdict.

### 3.9 Alignment audit

Completeness is gap-aware:

- a 4h bucket is complete only when all four 1h bars are usable;
- a 1h bucket is complete only when all four 15m bars are usable;
- a 15m bucket is complete only when all three 5m members are usable.

Only complete buckets enter the mismatch denominator. Gap-affected buckets are reported separately.
OHLC prices are compared exactly; volume sums use a relative tolerance of `1e-9`. The twelve
gap-adjacent 4h buckets are excluded from the 4h-from-1h denominator and reported under the ratified
exemption. A mismatch in `high`, `low`, or `close` on more than 0.1% of complete buckets, or any
mismatch in a bar the design reads, yields `INCONCLUSIVE`.

---

## 4. Candidate B implementation decisions

### 4.1 Episode state machine and absorption

An **episode attempt** begins at an expansion bar when no episode is active. While an episode is
active, a later expansion bar is absorbed: it does not re-anchor the level, does not move the retest
window, and does not start a second episode. `S3 - S4` is reported as `expansions_absorbed`.

**Pre-registered interpretation (B-1).** An episode attempt whose 4h permission at `e` is `False` or
`Unknown` still occupies the single active-episode slot and still absorbs later expansions until its
structural end. It is not regime-qualified, so it cannot advance to `S5` or beyond, but its lifecycle
blocks a new expansion from starting a second episode. This follows the literal §6 state machine,
which is defined independently of the regime filter, and keeps `S4` a real denominator for
`permission_share = S5/S4`.

### 4.2 Within-bar order

For each usable 1h bar in a segment, in order:

1. update the running setup low for the stop;
2. if no touch yet, test the retest window `e+1..e+6`, then penetration, then expiry;
3. if a touch exists, test the structure break, then resumption confirmation `r < c <= r+3`;
4. if confirmed, evaluate the confirmation-time regime, then entry, then stop, then cost;
5. if an episode is active at the start of the bar and the bar is an expansion bar, the expansion is
   absorbed.

An episode ends at the first failing condition. An episode that ends on a bar cannot start a new
episode on that same bar; a new episode requires a strictly later expansion bar.

### 4.3 Retest, penetration, resumption

- Touch: `low[r] <= L_e + 0.25*A_e`, first qualifying bar in `e+1..e+6`.
- Deep touch: `(L_e - low[r]) / A_e > 0.50` -> `retest_too_deep`.
- Structure break after a touch and before confirmation: `close[x] < L_e - 0.50*A_e` ->
  `structure_broken`.
- Confirmation: first `c` with `r < c <= r+3`, `close[c] > L_e`, and `close[c] > open[c]`.
- No touch in the window -> `retest_timeout`; no confirmation within three bars -> `resumption_timeout`.
- A missing or unusable bar ends the segment and the episode -> `segment_break`.

**Pre-registered interpretation (B-2).** `structure_broken` is checked on bars after the touch and
before confirmation. A pre-touch bar whose close is below `L_e - 0.50*A_e` necessarily has a low
below that bound, so it is a deep touch at that bar and receives `retest_too_deep`, not
`structure_broken`. This follows the frozen labels rather than inventing a second pre-touch label.

### 4.4 Entry presence versus entry usability

**Pre-registered interpretation (B-3).** Entry uses the raw 1h record whose `open_time` is exactly
`open_time[c] + 1h`. The record must be present, on-grid, inside the interval, and have `open > 0`.
Its close-time properties (`is_closed`, volume, trade count, 5m bucket completeness, full-bar OHLC
validity) are **not** selection criteria; they are recorded as post-count diagnostics
(`unclosed_entry_bar`, `zero_volume_entry`, `partial_entry_bar`, `invalid_entry_ohlc`). A record that
exists at the expected time but is unusable for a close-time reason is still a valid entry bar under
M2.

If the confirmation bar is the last bar of its 1h segment, or no record exists at the expected next
open, the signal is rejected as `no_entry_bar`; the runner never skips forward. If the expected entry
open is at or after `dev_end_ms`, the signal is rejected as `entry_outside_interval` and the
interval guard is evaluated before the presence check, following K2.

### 4.5 Stop and cost

`S = min(low[e..c])`, `D = entry_open - S`. Invalid stop if `S <= 0`, `entry_open <= 0`, or `D <= 0`.
`cost_R = 0.0026 * entry_open / D`. No floor, widening, trailing, or rounding is applied.

### 4.6 Stage mapping

| stage | count |
|---|---|
| S1 | usable 1h bars in the development interval |
| S2 | usable 1h bars with local index >= 14 (`ATR[t-1]` defined) |
| S3 | expansion bars |
| S4 | started episode attempts (non-absorbed expansion bars), including regime failures at `e` |
| S5 | S4 attempts with permission `True` at `e` |
| S6 | S5 attempts with a touch and resumption confirmation, before the regime-at-`c` check |
| S7 | S6 with permission `True` at `c` and a valid entry and stop (pre-gate) |
| S8 | S7 with `cost_R <= 0.20` |
| S9 | deduplicated signals (one per episode; expected equal to S8) |
| S10 | canonical 72h non-overlapping signals |

Primary rejection labels follow the frozen order in §9 of the B specification. A secondary table
records other failure conditions that were observed before the primary termination; a secondary
label never changes the primary.

### 4.7 Development-end handling

**Pre-registered interpretation (B-4).** An episode still active at the end of the development
interval is terminated as `segment_break` for accounting. The census does not read the next
validation bar to complete it. This affects only episodes that cannot reach structural completion
inside the frozen interval and is reported separately as `development_end_truncation` so it is not
hidden inside ordinary gap breaks.

---

## 5. Candidate D implementation decisions

### 5.1 Sessions and S0

A session bucket is one of `ASIA` (`[00:00,08:00)`), `EUROPE` (`[08:00,16:00)`), or `US`
(`[16:00,24:00)`) UTC, with the boundary owned by the session that contains the bar's open time.
`S0` is every session bucket whose signal instant (`s + 1h59m59.999s`) lies in
`[dev_start_ms, dev_end_ms)`. With 1,277 development days and three sessions per day, the expected
`S0` is 3,831; the runner asserts the enumeration rather than assuming it.

`S1` is usable 15m bars. `S2` is signal-evaluable sessions: `b0..b7` are all usable and exactly
15 minutes apart. A missing or unusable measurement bar yields `measurement_window_incomplete`.
The 32-bar `session_full_data` flag is computed after the signal and cannot remove or relabel it.

### 5.2 Signal

`P0 = open[b0]`, `P1 = close[b7]`, `r2 = P1/P0 - 1`.

`q` is the expected 1h bar opening at `s + 1h`. It must be present, usable under the 1h rules, and
have a defined `ATR1h[q]`. A missing or unusable `q` is `stop_atr_unavailable`; a usable `q` at 1h
local index `0..12` is `warmup_atr`. There is no fallback to an earlier hour.

`thr = 0.5 * ATR1h[q] / P0`. `S3` is `r2 >= thr`, evaluated on the raw directional condition.

`VWAP` is the typical-price session VWAP over the eight measurement bars:
`sum((high+low+close)/3 * volume) / sum(volume)`. `S5` requires `P1 > VWAP`. The zero-total-volume
case cannot occur in an S2 session; the runner asserts it and aborts on violation.

### 5.3 Budget

`S4` requires `budget_ok == True` at the 4h bar whose close is strictly before the session signal
instant. An uncomputable budget is `warmup_budget`; a computable percentile outside `[25, 80]` is
`budget_out_of_band`.

### 5.4 Entry and stop

**Pre-registered interpretation (D-1).** Entry uses the raw 15m record at `open_time[b7] + 15m`.
It must be present, on-grid, inside the interval, and have `open > 0`. Its close-time properties are
post-count diagnostics only, exactly as in B. A missing record is `no_entry_bar`; no skip-forward is
allowed. If the expected open is at or after `dev_end_ms`, the interval guard yields
`entry_outside_interval` before the presence check.

`S = entry_open - ATR1h[q]`, `D = ATR1h[q]`. Invalid stop if `ATR1h[q] <= 0`, `stop <= 0`,
`entry_open <= 0`, or `D <= 0`. `cost_R = 0.0026 * entry_open / D`.

### 5.5 Stage mapping

| stage | count |
|---|---|
| S0 | session buckets whose signal instant is in the development interval (diagnostic denominator) |
| S1 | usable 15m bars |
| S2 | signal-evaluable sessions (`b0..b7` usable and contiguous) |
| S3 | directional signals (`r2 >= thr`; includes `q` availability and ATR warm-up labels) |
| S4 | budget-qualified (`budget_ok == True`) |
| S5 | structurally valid (`P1 > VWAP`) |
| S6 | valid entry and stop (pre-cost-gate) |
| S7 | cost-feasible (`cost_R <= 0.20`) |
| S8 | deduplicated (one per session; expected equal to S7) |
| S9 | canonical 24h non-overlapping |

Primary rejection labels follow the frozen order in §10 of the D specification. Secondary labels are
recorded with the same convention as B.

### 5.6 Development-end handling

A session whose signal instant is in the interval but whose entry bar would open at or after
`dev_end_ms` is rejected as `entry_outside_interval`, not dropped. A session whose measurement
window cannot complete inside the interval is `measurement_window_incomplete`; the runner never
reads a validation bar to complete it.

---

## 6. Diagnostic populations

Every statistic is labelled with its population. The following populations are never mixed.

### 6.1 Candidate B

| symbol | population | use |
|---|---|---|
| S4 | episode attempts | raw-candidate denominator |
| S7 | valid confirmation regime + valid entry/stop, pre-gate | **`M_all`**, verdict median |
| S8 | cost-feasible | **`M_feasible`**, post-gate diagnostic; capital and cluster primary population |
| S10 | canonical 72h non-overlapping | opportunity count |

`M_all = median(cost_R over S7)` includes gate failures. `M_feasible = median(cost_R over S8)` is
bounded by the gate and is never used in the verdict.

### 6.2 Candidate D

| symbol | population | use |
|---|---|---|
| S6 | valid entry/stop, pre-gate | **`M_all`**, verdict median; cluster secondary view |
| S7 | cost-feasible | **`M_feasible`**, post-gate diagnostic; cluster **primary** population per K3 |
| S9 | canonical 24h non-overlapping | opportunity count; cluster secondary view |

`M_all = median(cost_R over S6)` includes gate failures. `M_feasible = median(cost_R over S7)` is
bounded by the gate and is never used in the verdict.

### 6.3 Quantiles

Medians are the arithmetic mean of the two middle values for an even count. Other quantiles use
linear interpolation at position `(n-1)*p` (the type-7 / common spreadsheet definition). All
quantiles are diagnostics. Bucket endpoints use the frozen endpoint inclusion:
`(-inf,0.10]`, `(0.10,0.20]`, `(0.20,0.30]`, `(0.30,0.50]`, `(0.50,+inf)`.

### 6.4 Calendar and regime counts

Calendar year/month/quarter is the UTC calendar of the **entry time** for signals. Regime counts use
the 4h bar read at the decision point. Percentile deciles are `[0,10)`, `[10,20)`, …, `[90,100]`;
`pct = 100` is placed in the last decile. Every decile table states whether it is over the pre-gate
or the cost-feasible population.

### 6.5 Cluster assignment

Clusters are protocol §3.1 maximal runs of consecutive usable 4h bars with `permission == True` (B)
or `budget_ok == True` (D). A `False`, `Unknown`, missing, or unusable bar breaks the run. A signal
is assigned to the run containing the 4h bar read at its **signal instant** (B: confirmation bar;
D: session signal instant). All counted B S8 and D S7 signals have a `True` regime/budget at that
instant, so every one has a cluster.

Reported views:

- B: primary S8; additional calendar-month, calendar-quarter, and `pct[q]` decile views.
- D: primary S7; required additional S6 and S9; calendar-month, calendar-quarter, and session-id
  views, per K3.

The cluster-size distribution is reported over **non-empty** clusters (clusters with at least one
signal); the number of all regime runs is reported separately. Kish uses non-empty clusters:
`n_eff = (Σ n_k)^2 / Σ n_k^2`. The design effect is `N / n_eff`. The `rho` sensitivity uses
`m̄ = N / K_nonempty` and `n_eff(rho) = N / (1 + (m̄-1) rho)` for `rho ∈ {0.25,0.50,0.75,1.00}`,
reported alongside the exact Kish value. Kish is a concentration diagnostic, not an estimate of
serial dependence and not a definitive effective sample size.

### 6.6 Capital geometry

At `$10,000` equity and 1% risk (`$100`):

```
stop_fraction = D / entry_open          (dimensionless)
notional_usd  = 100 / stop_fraction
notional_pct  = notional_usd / 10000
```

**Pre-registered interpretation (C-1).** The capital-geometry **verdict condition**
(`notional_pct > 1.00` for any signal) is evaluated on the cost-feasible population (B S8, D S7).
The same distribution is also reported on the pre-gate population (B S7, D S6) as a labelled
diagnostic. This follows the Stage 2J planning decision that the verdict applies to cost-feasible
signals; it does not change the frozen arithmetic. Cost-feasible signals have
`stop_fraction >= 0.013` at 26 bp, so their `notional_pct` is at most about `0.769`; a violation can
only arise if the arithmetic is different from the frozen gate, which the report would surface.

The distribution reports median, p25, p75, p90, and maximum for `notional_usd` and `notional_pct`,
the count and share above `1.00`, the largest number of overlapping holding windows, and the implied
capital at that peak. B uses a 72h holding window. D uses the window from entry to the session end
(entry is at `s+2h`, session end at `s+8h`, so at most 6h; the 8h session bound is also reported).
The one-position cash-policy skip count is computed by greedy scanning of the cost-feasible
population at the holding horizon; the canonical non-overlap rejection count is reported separately.
Minimum-notional (`$5`) and lot-step (`1e-5 BTC`) checks are arithmetic only.

### 6.7 Cost sensitivity

For each of 10, 26, 39, and 52 bp, with the gate fixed at `0.20`:

- count passing and feasible share on the pre-gate population;
- median `cost_R` on that **same pre-gate population**;
- design margin `0.15 - M_all`;
- `M_feasible` on the post-gate population, labelled as a diagnostic.

The primary verdict uses 26 bp only.

### 6.8 Non-overlap and detectable-effect reference

Canonical and sensitivity counts use the frozen greedy algorithm on entry time, sorted by entry time
then key, inclusive boundary. The spacing distribution is reported. The detectable-effect reference
is `2.801585 / sqrt(N_nonoverlap)` in R, labelled as a planning calculation under independence and
not as a power result.

---

## 7. Verdict procedure (pre-declared)

The Stage 2J verdict uses exactly the four authorized terms. The procedure is evaluated in order.

### 7.1 `INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION`

If any of the following is true:

- a frozen artefact, manifest self-hash, Stage 2H/2I hash, dataset hash, or dataset-manifest hash
  mismatch;
- a schema error, interval violation, or unexplained duplicate record;
- an alignment mismatch in a field the design reads, or more than 0.1% complete-bucket
  high/low/close mismatch;
- a causality assertion failure;
- an empty pre-gate population (B S7, D S6), making `M_all` undefined;
- an unexplained deduplication removal (B S9 != S8, D S8 != S7);
- any other implementation or data limitation that prevents a faithful run.

### 7.2 `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`

If the compliance gate passes and any of:

- `N_nonoverlap < 150` (the project floor, a project choice, not a statistical standard);
- `M_all > 0.20` (the frozen cost-median condition);
- any cost-feasible signal has `notional_pct > 1.00` (the frozen capital-geometry condition,
  applied to the cost-feasible population per C-1).

The report names the exact sub-condition(s). Cost and capital conditions are reported under this
category because they mean the cost-feasible/fundable opportunity set is not usable at the frozen
constraints; no separate verdict term exists in the authorized vocabulary. The frozen spec's own
tier label is also reported separately for transparency.

### 7.3 `FEASIBILITY FAIL — EXCESSIVE CONCENTRATION`

If the compliance and insufficient-opportunity gates pass, and the pre-declared descriptive
concentration criterion holds on the candidate's frozen primary cluster population
(B S8, D S7):

- the largest non-empty 4h regime cluster contains **more than 50%** of that population, **or**
- the Kish design effect `N / n_eff` is **at least 2.00**.

This is a **pre-declared descriptive screening criterion**, not a statistical test, not a
dependence estimate, and not a claim that the signals are independent or dependent. Both components
are reported with the full cluster distribution. The same metrics are also reported on the canonical
non-overlapping set as a labelled sensitivity; they do not replace the frozen primary population.

### 7.4 `FEASIBILITY PASS`

If none of the above applies. The report separately states the frozen tier label:

- `PASS` if `N >= 349` and `M_all <= 0.20`;
- `PASS WITH LIMITATIONS` if `150 <= N < 349` and `M_all <= 0.20`;
- otherwise the frozen `FAIL` reason.

A `FEASIBILITY PASS` means only that the design produced enough cost-feasible, non-overlapping
opportunities under the frozen rules. It is **not** evidence of profitability, an edge, or
independent observations.

---

## 8. Required outputs

### 8.1 Human-readable reports

1. `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` (this file).
2. `docs/research/stage2j/CANDIDATE_B_CENSUS_REPORT.md`.
3. `docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md`.
4. `docs/research/stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md`.
5. `docs/research/stage2j/STAGE2J_SUMMARY_AND_VERDICT.md`.
6. `docs/research/stage2j/FREEZE_MANIFEST.json`.

### 8.2 Machine-readable intermediates

Under `docs/research/stage2j/machine_readable/`: the preflight result, Candidate B counts and signal
metadata, Candidate D counts and signal metadata, alignment results, resource usage, and the final
manifest inputs. Signal metadata contains entry/signal times, prices, stop distance, `cost_R`,
regime/budget state and percentile, cluster id, and stage labels. It contains **no outcome field**
and no P&L, return, or expectancy.

### 8.3 Determinism

All JSON is written with sorted keys. Signal lists are sorted by entry time then key. Wall time and
RSS are reported in a separate resource section and excluded from the count-identity comparison. Two
runs with the same code must produce identical counts, signal keys, and `cost_R` values.

---

## 9. Prohibitions carried into the run

- No validation or out-of-sample row is read, parsed, sliced, summarised, or used.
- No P&L, return, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR, equity curve, bootstrap,
  Monte Carlo, or optimisation.
- No parameter tuning, sweep, or post-count threshold change.
- No trade entry, resolution, mark-to-market, fill model, order book, or portfolio simulation.
- No modification of frozen Stage 2A/2B/2C/2D, Stage 2E v1, Stage 2F, Stage 2G v2, Stage 2H, or
  Stage 2I artifacts.
- No discretionary visual interpretation.
- No claim that Binance-proxy costs are verified Nobitex execution costs.
- No claim that non-overlapping observations are independent observations.
- No claim that a passing count demonstrates an edge.

---

## 10. Change control

This plan is committed before counting. If an implementation ambiguity is discovered during coding
and the frozen text does not resolve it, the resolution is added to this plan **before** the signal
count is produced, with the reason and the affected label/population. No threshold, population, or
verdict rule may be changed after counts are observed. If a change is unavoidable after counting,
the run is void and a new pre-registration is required.
