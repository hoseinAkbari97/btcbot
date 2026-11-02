# Stage 2C — Frozen Signal Specification

**Strategy identifier:** `CANDIDATE_A_MTF_TREND_PULLBACK_CONTINUATION`
**Specification version:** `1.0.0`
**Status:** frozen before any Stage 2C counting run.
**Scope:** development interval only, `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.
**Machine configuration:** `stage2c_census/stage2c_config.json` — this document and that file
must agree. If they disagree, the run is invalid.

**Evidence tags:** **[F]** repository fact, **[L]** literature-backed mechanism, **[E]** engineering
judgment, **[H]** unverified hypothesis. The Stage 2B recommendation is the primary source for the
hypothesis; every concrete number this document adds is an **[E]** instantiation of a definition
that Stage 2B left qualitative. No parameter below was chosen by looking at Stage 2C counts.

---

## 0. Why this document exists

Stage 2B selected multi-timeframe trend pullback continuation for a feasibility census but defined
it with placeholders (`e.g.`, "a simple pre-definable rule", "recent swing area or MA zone"). A
census cannot be replicated against placeholders. This document resolves each placeholder with the
minimum objective rule that (a) preserves the Stage 2B mechanism, (b) uses only data the platform
already holds, and (c) can be implemented without a discretionary chart judgement.

**This is a feasibility census, not a backtest.** It counts opportunities and measures their cost
geometry. It does not resolve a trade, compute P&L, or estimate an edge.

**Ambiguities resolved here, not discovered after counting:**

| Stage 2B wording | resolution in this specification |
|---|---|
| HTF regime "price above/below a moving average with slope/structure" | 4h close above a rising 200-bar SMA; slope measured over 20 bars |
| Pullback "to a defensible reference (recent swing area or MA zone)" | 1h close crossing below the 20-bar EMA; reference high is the last 1h high before the crossunder |
| Resumption "close above pullback high / structure shift" | 1h close strictly above the pre-crossunder high |
| Stop "beyond pullback extreme" | lowest 1h low from the crossunder bar through the confirmation bar |
| Invalidation "break of structure / HTF regime flip" | HTF regime flip, 72-bar pullback age, or 15% pullback depth, whichever occurs first |
| Cooldown/overlap "one position logic or explicit rules" | one signal per pullback episode; no cooldown; 120h greedy non-overlap as the conservative view |
| "LTF (e.g., 15m or 1h)" | 1h signal timeframe |
| "HTF (e.g., 4h or daily)" | 4h regime timeframe |

The choice of 1h rather than 15m is deliberate: a 15m pullback range is usually too narrow to
produce a stop of at least ~1.30% of price, which is the stop the 0.20R gate requires at 26 bp.
A 1h timeframe is the coarsest LTF that still plausibly produces more opportunities than the 4h
breakout that was already censused, while giving pullbacks room to reach the cost gate. This is an
**[E]** judgment, made before counting.

---

## 1. Data and interval

| item | value | tag |
|---|---|---|
| Instrument | BTCUSDT spot | **[F]** |
| Side | long only, no leverage | **[F]** |
| Development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` | **[F]** |
| Regime timeframe | 4h | **[E]** |
| Signal timeframe | 1h | **[E]** |
| Execution timeframe | 5m | **[F]** |
| 5m dataset | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | **[F]** |
| 1h dataset | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` | **[F]** |
| 4h dataset | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | **[F]** |
| Dataset manifest | `backend/data/datasets/manifest.json` | **[F]** |
| Validation / OOS | **not read, not parsed, not summarised** | **[F]** |

Rows outside the development interval are discarded by ISO-string comparison **before** any numeric
field is converted. No pre-development bar is used for warm-up. Indicators are initialised only
from development bars, and the warm-up exclusions in §10 are reported.

### 1.1 Candle conventions

All timestamps are UTC with an explicit `+00:00`. A bar's `open_time` is the first instant of the
bar; its `close_time` is the last instant. A decision made "at the close" of a bar uses a value
that is knowable at `close_time` and is acted on at the next executable bar's `open_time`.

| timeframe | open_time alignment | close_time | `is_closed` requirement |
|---|---|---|---|
| 5m | every 5 minutes, seconds `00` | open + 4:59.999 | `True` |
| 1h | every hour, minutes/seconds `00` | open + 59:59.999 | `True` |
| 4h | hours `00/04/08/12/16/20` | open + 3:59:59.999 | `True` |

A bar that is not flagged `is_closed` is excluded and counted. A bar that is duplicated,
off-grid, or (at 1h/5m) zero-volume is handled by §9.

---

## 2. Higher-timeframe trend regime

**Timeframe:** 4h, closed bars.
**Inputs:** 4h `close` only.
**Definition:** at 4h bar `t`,

```
SMA200[t] = mean(close[t-199 .. t])
slope[t]  = SMA200[t] - SMA200[t-20]
regime_up[t] = (close[t] > SMA200[t]) AND (slope[t] > 0)
```

Both comparisons are strict. `regime_up` is a three-valued label: `True`, `False`, or `Unknown`
(before the first computable value). A 4h bar must be closed before its label is used.

**Warm-up:** `SMA200` first exists at 4h index 199; `slope` first exists at index 219. Therefore the
first valid regime label is at 4h index 219, whose bar opens at `2021-02-06T12:00:00Z` and closes at
`2021-02-06T15:59:59.999Z`. The first 1h bar that may use that label opens at
`2021-02-06T16:00:00Z`. The 219 preceding 4h bars are a warm-up exclusion, not a signal window.

**Confirmation timing:** a 1h bar opening at `T` uses the most recent 4h bar whose `close_time` is
strictly less than `T`. Because the 4h grid is aligned to the 1h grid, that is the 4h bar opening at
`floor(T, 4h) - 4h`; for example, a 1h bar at `04:00` uses the 4h bar that opened at `00:00` and
closed at `03:59:59.999`. A 1h bar at `03:00` uses the 4h bar that opened at `20:00` on the previous
day. No 4h label is ever read before that 4h bar closes.

**Why a slope condition:** `close > SMA200` alone is satisfied by a price bouncing inside a falling
trend. Requiring the 200-bar mean itself to be higher than it was 20 bars ago removes that case
without adding a second indicator. Twenty 4h bars is 80 hours; it is long enough not to be a
one-bar artefact and short enough to react within the intended holding horizon. **[E]**

**Why 200 bars:** it is the same slow-trend reference used by the previously censused 4h Candidate A
and by `SmaTrendStrategy` **[F]**. Reusing it avoids inventing a new trend parameter and makes the
regime filter comparable to prior work. It is not evidence that 200 is optimal.

**Missing 4h bars:** the vendor 4h series has zero registered gaps **[F]**. If a 4h bar is
nevertheless missing at run time, the regime label is `Unknown` for the affected span and no
primary signal is emitted there. It is never synthesised.

**Partial 4h buckets:** twelve 4h buckets straddle registered 5m gaps and are built from fewer than
48 5m bars, but their vendor `high`, `low`, `close`, `volume`, `quote_volume`, `trade_count` and
`close_time` match the partial 5m aggregate exactly **[F]** (Stage 2A audit). The regime uses the
vendor close, which is a real last-trade price. They are retained, and the run re-verifies the
alignment. This is a slow filter; twelve partial buckets cannot determine a 200-bar mean.

---

## 3. Lower-timeframe pullback definition

**Timeframe:** 1h, closed bars.
**Inputs:** 1h `high`, `low`, `close`.
**EMA:** `EMA20` on 1h closes, with `alpha = 2 / (20 + 1)`. Initialisation is the simple mean of the
first 20 closes of a contiguous 1h segment; thereafter `EMA[t] = alpha * close[t] + (1-alpha) *
EMA[t-1]`. A segment is a maximal run of usable 1h bars whose `open_time` differs by exactly one
hour. Warm-up is 20 bars per segment; see §9 for segment breaks and §10 for the exclusion.

**Crossunder (pullback start):** at 1h bar `i`, with `i >= 1` within its segment,

```
close[i] < EMA20[i]  AND  close[i-1] >= EMA20[i-1]
```

The bar `i` is the **crossunder bar**. The **reference high** is

```
R = high[i-1]
```

the high of the last bar that closed at or above the EMA. The **pullback low** is initialised at
`L = low[i]` and updated over subsequent bars.

**Why the pre-crossunder high, not the EMA:** the entry must be a *resumption* of the prior
structure, not merely a re-touch of a moving average. Using `R` means the market has to recover the
price level from which the pullback began before a signal exists. The EMA is used only to locate
the start of the pullback; it is not the entry trigger.

**One active pullback at a time:** while a pullback is active, a new crossunder does not start a new
episode. This is the duplicate-signal rule (§7).

**Pullback lifecycle:** from bar `i` onward, for each closed 1h bar `j >= i`:

1. update `L = min(L, low[j])`;
2. if an invalidation condition (§5) is met, close the episode without a signal;
3. otherwise, if the confirmation condition (§4) is met, emit a signal and close the episode;
4. otherwise continue.

Invalidation is evaluated **before** confirmation. A bar that both breaches the 15% depth guard and
closes above `R` is a violent reversal, not a pullback resumption; it is invalidated, not signalled.
The episode is closed by the first of invalidation, confirmation, or the end of its 1h segment.

**Minimum pullback duration:** a confirmation cannot occur on the crossunder bar itself. The
earliest confirmation is `j = i+1`. This prevents a same-bar start-and-confirm and guarantees that
the pullback contains at least one full bar of post-crossunder price action. It does not impose a
minimum stop distance; the cost gate does that (§6).

---

## 4. Resumption confirmation and signal timestamp

**Confirmation condition:** at the close of 1h bar `j`, with `j > i` and the episode still active,
and after invalidation checks have passed,

```
close[j] > R
```

strictly. A close exactly equal to `R` is not a confirmation. A wick above `R` that closes at or
below `R` is not a confirmation. The comparison is close-versus-level, not high-versus-level,
because a wick through a level that closes back below it is the failed-retest case this design is
trying to exclude.

**Signal timestamp:** the `close_time` of confirmation bar `j`, i.e. `open_time[j] + 1h - 1ms`.
This is the instant at which the signal becomes knowable. Nothing about the signal uses a later bar.

**Signal identity:** `(open_time[j], entry_time)`, where `entry_time` is defined in §5.

**Why this is a resumption and not a breakout:** `R` is a *local* pre-pullback high, not the highest
high of a 20-bar channel. The 1h bar that set `R` may be well below the 4h or 1h 20-bar high. The
signal therefore can fire before a new 20-bar high and is not the prior 4h Donchian definition.
It is also not Strategy 2 C: there is no volatility-compression or volume-dry-up condition, and the
entry level is a recovered local high rather than the upper edge of a compressed range.

---

## 5. Entry, stop, and invalid-stop rules

### 5.1 Entry reference

**Entry rule:** buy at the **open of the 5m bar whose `open_time` equals `open_time[j] + 1h`** — the
first 5m bar after the confirmation 1h bar closes. This is the next eligible candle open. The entry
is not the 1h close and is not a 5m close.

The entry bar must satisfy all of:

| check | requirement | failure label |
|---|---|---|
| exists | a 5m bar at exactly `open_time[j] + 1h` | `no_entry_bar` |
| closed | `is_closed == True` | `unclosed_entry_bar` |
| traded | `volume > 0` and `trade_count > 0` | `zero_volume_entry` |
| valid price | `open > 0` | `invalid_entry_price` |

If the exact next 5m bar is missing (a data gap), the signal is rejected. The run does **not** skip
forward to the next available 5m bar: doing so would enter at a price that is not the price
immediately after the signal and would make the fill assumption unauditable. The rejection is
counted and reported.

### 5.2 Structural stop

**Stop rule:** the stop is `L`, the lowest 1h low from the crossunder bar `i` through the
confirmation bar `j`, inclusive. This is the structural extreme of the pullback. It is fixed at the
signal and never widened.

**Stop distance:** `D = entry_open - L`, in USDT per BTC.
**Stop percentage:** `D / entry_open`.

### 5.3 Invalid-stop rejection

A signal is rejected as `invalid_stop` if any of:

- `L <= 0`;
- `entry_open <= 0`;
- `D <= 0` (the entry is at or below the pullback low).

No separate minimum stop distance is imposed. The economic gate in §6 already implies
`D / entry_open >= 0.013` at 26 bp and `cost_R <= 0.20`. Adding a second, venue-specific floor
would duplicate the gate and would make the census depend on a number that is not yet known for
Nobitex. Stop distances below the gate are therefore **counted and reported**, not silently
discarded, so the gate's work is visible.

### 5.4 Target, exit, and holding horizon (recorded only)

The census does **not** simulate exits. For comparability with prior designs it records:

| element | value | status |
|---|---|---|
| target | `entry + 2R` | design only, never resolved |
| maximum holding horizon | 120 hours (5 days) | used only for the non-overlap definition |
| invalidation after entry | stop, target, or 120h | not simulated |

The 120h horizon is the conservative overlap window, not a claim about the optimal exit. It is
inside the "intraday–few days" range Stage 2B anticipated and matches the 30 × 4h (5-day) exit of
the previously censused 4h Candidate A. **[E]**

---

## 6. Cost model and feasibility gate

**Round-trip cost:** 26 basis points of notional, Binance spot proxy
(`2 × (0.1% fee + 3 bps adverse)`); 0.0026 as a fraction. **[F]**

For every valid signal:

```
cost_R = 0.0026 * entry_open / D
```

The primary feasibility gate is:

```
cost_R <= 0.20
```

This is not relaxed. It is reported alongside the descriptive buckets
`<=0.10`, `(0.10,0.20]`, `(0.20,0.30]`, `(0.30,0.50]`, `>0.50`.

At 26 bp, `cost_R <= 0.20` is equivalent to `D / entry_open >= 0.013` (1.30%). The census reports the
actual stop percentages, so the equivalence can be checked independently.

**Costs are a Binance proxy, not a Nobitex measurement.** No claim is made that Nobitex execution
would pass this gate. The Nobitex facts that would be required before deployment are listed in the
feasibility report.

---

## 7. Duplicate signals, episodes, cooldown, and overlap

**Pullback episode:** the interval from a crossunder bar `i` to the first of confirmation,
invalidation, or segment end. Only one signal can be emitted per episode. A new episode can begin
only after the prior one closes.

**Duplicate-signal definition:** two signals are duplicates if they share the same `entry_time`.
This cannot occur under the state machine (one signal per episode, episodes are non-overlapping in
time within a segment, segments are disjoint), but the run verifies it and reports the number of
duplicates removed. A signal is also considered duplicate if the same confirmation 1h bar is used
twice; the run checks that too.

**Primary cooldown:** **none** beyond the one-signal-per-episode rule. This is the primary
specification because a cooldown is an additional filter that Stage 2B did not define, and adding
one would reduce the count for a reason unrelated to the hypothesis. Cooldown is a sensitivity
variable (§11), not part of the primary count.

**Conservative non-overlapping view:** signals are sorted by `entry_time`; a signal is accepted if
its `entry_time` is at least **120 hours** after the last accepted signal's `entry_time`. This is a
greedy interval selection, not a portfolio simulation. It answers: "how many opportunities are
separated by at least the maximum intended holding horizon?"

**Episode clustering view:** see §8.

**Cooldown sensitivities:** 24h, 72h, and 168h, applied greedily to the feasible unique signals,
after the cost gate. These are diagnostics only and cannot change the primary decision.

---

## 8. Episode clustering and effective sample size

Two transparent views are reported; neither is a substitute for an outcome-based dependence
analysis, which this stage cannot perform.

### 8.1 View 1 — higher-timeframe regime episodes (primary clustering view)

A **regime episode** is a maximal run of consecutive 4h bars with `regime_up == True`. Because the
4h series is gap-free, the run is unambiguous. Each primary signal is assigned to the regime
episode that contains the 4h bar used for its crossunder decision.

Reported:

- number of up-regime episodes in the development interval;
- number with at least one primary signal;
- duration distribution (4h bars and days);
- signals per signal-producing regime episode (median, p90, maximum);
- days between regime-episode starts;
- the share of all primary signals that fall in the largest regime episode.

This view captures the obvious dependence: pullback signals are not spread uniformly through time;
they occur while the market is in an up-regime, and a single long bull phase can contain many
signals.

### 8.2 View 2 — greedy 120h non-overlap (conservative event view)

The count from §7 after the 120h separation rule, with its own spacing distribution. This is the
most conservative event count and is the count used in the decision rule (§12).

### 8.3 Approximate effective sample size

Three design diagnostics are reported, with their assumptions stated:

1. **Kish effective size across signal-producing regime episodes:**
   `n_eff = (Σ n_k)^2 / Σ n_k^2`, where `n_k` is the number of primary signals in regime episode
   `k` (only episodes with `n_k > 0`). This treats signals within one regime episode as perfectly
   dependent and signals in different episodes as independent. It is an upper bound on the
   effective sample if regimes are the only dependence structure, and a lower bound if they are not.
2. **Cluster count:** the number of signal-producing regime episodes. This is the most conservative
   cluster-based count.
3. **Non-overlapping count:** from §8.2, used for the verdict.

The design effect `N / n_eff` is reported for (1) and (3). No bootstrap, Monte Carlo, or
outcome-based dependence estimate is run.

**Power reference, not a result:** for a two-sided 5% test, 80% power, a 0.15R minimum effect and a
provisional outcome standard deviation of 1R, the independent-sample requirement is
`(1.959964 + 0.841621)^2 / 0.15^2 = 348.8 ≈ 349`. At `n` independent observations the smallest
detectable effect at the same α and power is `2.801585 / sqrt(n)` R. The census reports the
detectable effect implied by the non-overlapping count, but does **not** claim that count is
independent or that 349 raw signals satisfy the requirement.

---

## 9. Missing data, gaps, and segment handling

### 9.1 5m series

The run verifies duplicate timestamps, off-grid bars, unclosed bars, gaps, and zero-volume/flat
bars. A 5m gap is a hole between two available bars; no bar is synthesised or forward-filled. Entry
bars are looked up by exact timestamp; a missing entry bar rejects the signal (§5.1).

### 9.2 1h series

The 1h vendor series has seven registered gaps and fourteen missing bars over the full dataset
**[F]**. A 1h bar is **unusable** if any of:

- it is not present;
- it is not flagged `is_closed`;
- `volume == 0` or `trade_count == 0` (a placeholder, not a price observation);
- it is **partial**, meaning its 1h bucket contains fewer than 12 of the 12 expected 5m bars. This
  is the gap-adjacent case; a partial 1h bar is not a complete hour of price action;
- its **final 5m member has zero volume**, because the 1h close would then be a placeholder price
  rather than a traded price. (An earlier zero-volume member inside the hour is flagged but does not
  by itself make the bar unusable; the design reads the close, not every intrahour print.)

A maximal run of consecutive, usable 1h bars is a **segment**. Segments are separated by any
unusable or missing bar. The EMA is re-initialised at the start of every segment and needs 20 bars
of that segment. A pullback cannot span a segment break: the episode is closed without a signal at
the break, and the break is counted as `segment_break`.

This is deliberately conservative. It removes a small number of gap-adjacent signals rather than
allowing a stop or a confirmation to be set from an incomplete hour.

### 9.3 4h series

The 4h vendor series has zero registered gaps **[F]**. It is used as supplied. Partial 4h buckets
are retained for the slow regime filter, for the reason in §2. If a 4h bar is missing or unclosed at
run time, `regime_up` is `Unknown` for the affected span and no primary signal is emitted there.

### 9.4 Alignment verification

Before counting, the run independently verifies:

- 5m duplicates, grid alignment, `is_closed`, gaps, and zero-volume runs;
- 1h duplicates, grid alignment, `is_closed`, missing hours, and every vendor 1h bar against the
  aggregate of its constituent 5m bars (open, high, low, close, volume, quote_volume, trade_count,
  close_time);
- 4h duplicates, grid alignment, `is_closed`, missing buckets, and every vendor 4h bar against the
  aggregate of its constituent 5m bars, including the twelve gap-adjacent partial buckets;
- for every signal, that the entry timestamp exists on the 5m grid, is traded, and is the first 5m
  bar after the confirmation close;
- that every regime lookup uses only a 4h bar whose `close_time` is strictly before the 1h bar's
  `open_time`.

A failure in a field the design reads (1h high/low/close; 4h close) makes the census
`INCONCLUSIVE` unless the failure is fully explained by a registered gap or a zero-volume
placeholder and affects no signal. The audit document records every exception.

---

## 10. Warm-up

| indicator | warm-up | first usable point |
|---|---|---|
| 4h SMA200 + slope | 200 + 20 bars = 219 4h bars | 4h bar opening `2021-02-06T12:00:00Z`; first 1h bar allowed to use it opens `2021-02-06T16:00:00Z` |
| 1h EMA20 | 20 bars per segment | 21st bar of the segment; a crossunder can first be detected at the 21st bar |

No pre-development bar is used. The cost of this choice is a shorter primary window
(approximately 3.39 years rather than 3.50) and a short re-warm after each 1h segment break. Both
are reported. The control arm does not require the 4h warm-up, but it is also reported on the
**matched window** beginning at the first 4h regime label, so the regime contrast is not confounded
by a longer control window.

---

## 11. Control arm

**Definition:** both arms are evaluated on **one shared lower-timeframe episode stream**. That
stream is generated without any higher-timeframe condition: the same 1h EMA20, crossunder,
reference high, pullback low, confirmation, entry timing, stop, cost model, and validity rules for
both arms.

- **Control:** every confirmation on the shared LTF stream.
- **Primary:** the subset of confirmations for which (a) `regime_up` was `True` at the crossunder
  bar and (b) `regime_up` was `True` at every 1h bar from the crossunder through the confirmation
  bar. A regime flip removes primary eligibility; it does not reset or alter the shared LTF stream.

This is the exact meaning of "remove only the HTF directional-regime condition": the LTF signal
stream is identical in both arms; only the eligibility filter differs. The primary therefore cannot
start a different episode count merely because the regime flipped.

**Consequence:** every primary signal is also a control signal by construction. The run verifies
the subset relation and reports:

- primary count;
- control count, all;
- control count on the matched (regime-labelled) window;
- overlap (should equal the primary count);
- primary-only (should be 0);
- control-only, split by the regime label at the crossunder (`False` or `Unknown`) and by
  `regime_flip` (started up, flipped before confirmation).

The control is **not** an alternative strategy and is **not** promoted if the primary fails. It
measures the regime filter's contribution to frequency and stop geometry. The contrast is about
*frequency and geometry*, not profitability; no outcome is computed.

---

## 12. Pre-registered decision rule

This rule is fixed before counting. The verdict is computed from the **primary** arm only.

Let:

- `N_nonoverlap` = primary feasible signals after deduplication and the 120h non-overlap rule;
- `M_cost` = median `cost_R` of primary feasible signals;
- `S_feasible` = primary feasible signals / primary valid triggers (after entry and stop validity);
- alignment = the audit verdict in §9.4.

| verdict | condition |
|---|---|
| **INCONCLUSIVE** | alignment fails in a field the design reads and the failure is not fully explained; or the specification/config hashes do not match the freeze record; or dataset hashes do not match the manifest; or a causal-timing check fails. |
| **PASS** | `N_nonoverlap >= 349`, `M_cost <= 0.20`, `S_feasible >= 0.50`, alignment passes. |
| **PASS WITH LIMITATIONS** | `150 <= N_nonoverlap < 349`, `M_cost <= 0.20`, `S_feasible >= 0.25`, alignment passes; **or** `N_nonoverlap >= 349` with `S_feasible < 0.50` or a documented unresolved execution/geometry issue. |
| **FAIL** | `N_nonoverlap < 150`; **or** `M_cost > 0.20`; **or** `S_feasible < 0.25`; **or** the capital geometry makes the design impracticable under the stated spot assumptions. |

**Interpretation of the thresholds (fixed now):**

- 349 is the independent-sample reference for a 0.15R effect at 80% power. Passing it is necessary,
  not sufficient: the actual dependence structure can reduce the effective sample.
- 150 non-overlapping events can detect an effect of about `2.801585 / sqrt(150) = 0.229R` at the
  same α and power. Below 150, the design cannot answer a question of the size the programme cares
  about, even before dependence is considered.
- `S_feasible >= 0.50` guards against a result where the median is acceptable but the gate is
  rejecting most of the sample, which would make the surviving events a selected and possibly
  unrepresentative subset.
- `S_feasible < 0.25` is an economic failure regardless of the median.

No threshold may be changed after seeing counts. If the result is borderline, it is reported as
borderline, not re-specified.

---

## 13. Counting pipeline and exclusion accounting

Every stage is counted for both arms. Every rejection has exactly one primary reason, assigned in
the order below; the run also reports secondary reasons where a signal fails more than one check.

```
1. usable 1h bars in development interval
2. bars with EMA20 defined
3. crossunder episodes identified
4. episodes with a valid regime label at the crossunder     [primary only]
5. episodes confirmed (raw triggers)
6. triggers with a valid entry bar
7. triggers with a valid stop
8. triggers passing cost_R <= 0.20
9. unique signals after deduplication
10. non-overlapping signals (120h greedy)
```

Exclusion reasons:

| reason | stage |
|---|---|
| `warmup_ema` | 1h EMA not yet defined |
| `segment_break` | episode open when its 1h segment ended |
| `regime_unknown` | primary only: no valid 4h label at the crossunder |
| `regime_not_up` | primary only: `regime_up` was false at the crossunder |
| `regime_flip` | primary only: `regime_up` became false before confirmation |
| `max_pullback_bars` | 72-bar age exceeded |
| `max_pullback_depth` | 15% depth exceeded |
| `no_entry_bar` | exact next 5m bar absent |
| `unclosed_entry_bar` | next 5m bar not closed |
| `zero_volume_entry` | next 5m bar has no trade |
| `invalid_entry_price` | next 5m open <= 0 |
| `invalid_stop` | stop <= 0, entry <= stop |
| `cost_gate` | `cost_R > 0.20` |
| `duplicate_entry` | same entry timestamp already used |
| `non_overlap` | within 120h of an accepted signal (conservative view only) |

A trigger that fails `cost_gate` is still reported in the cost distribution; it is not deleted from
the economic evidence. `non_overlap` is a view, not a validity failure.

---

## 14. Cost, stop, and capital reporting

For both arms, report:

- counts and percentages in each `cost_R` bucket;
- `cost_R` median, mean, p25, p75, p90, min, max;
- stop distance in USDT and as a percentage of entry: median, mean, p25, p75, p90, min, max;
- events per calendar year and per active year;
- median and p10/p90 days between signals, before and after the non-overlap rule;
- overlap between arms and the regime-label breakdown.

**Capital geometry (no simulation):** at a fixed risk budget of 1% of a $10,000 equity, the implied
position notional is `100 / stop_pct`. Report the distribution of implied notional and implied
percentage of equity, and count signals whose implied notional exceeds 100% of equity (not fundable
in spot at that risk budget); the minimum-notional and lot-step checks at `$5` and `1e-5 BTC`; and
the maximum number of signals whose 120h windows overlap, which bounds how often a one-position
policy would have to skip a signal. No cash path, no portfolio, no P&L.

---

## 15. Sensitivity analyses (diagnostic only)

Permitted and pre-declared:

1. **Cost multiples:** 1×, 1.5×, 2×, 3× the 26 bp base (26, 39, 52, 78 bps), plus 10 bps and 100 bps
   as venue-context diagnostics. Counts passing `cost_R <= 0.20` at each.
2. **Cooldowns:** 24h, 72h, 168h, greedy, after the cost gate.
3. **Conservative episode view:** 120h non-overlap (already the decision count).
4. **Alignment diagnostics:** 1h and 4h reconstruction, gap-adjacent buckets, entry-bar existence.
5. **Per-year counts.**

Not permitted: parameter optimization, selecting a definition after seeing counts, changing the
primary signal, sweeping the EMA/SMA windows, searching for profitable configurations, or
outcome-based filtering. The frozen primary specification is the only decision basis.

---

## 16. What this census does not do

- No trade is entered, resolved, or marked to market.
- No P&L, return, expectancy, win rate, drawdown, Sharpe, CAGR, or profitability figure is computed.
- No backtest, portfolio simulation, bootstrap, Monte Carlo, or performance inference is run.
- No parameter is optimized.
- No validation or OOS observation is read, parsed, summarised, or used.
- No frozen Stage 2A, Stage 2B, Stage 6, Stage 6A, or Setup 1 artifact is modified.
- The control is not promoted if the primary fails.

## 17. Freeze record

The specification and `stage2c_config.json` are hashed by `stage2c_census/census.py` at startup and
compared with `stage2c_census/freeze.json`. A mismatch aborts the run. The freeze record is created
before the first counting run; its git commit timestamp is the external evidence of ordering.

**Frozen by:** Stage 2C census run, 2026-11-02.
**Spec version:** `1.0.0`.
