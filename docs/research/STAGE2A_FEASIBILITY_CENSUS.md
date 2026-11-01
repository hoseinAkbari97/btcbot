# Stage 2A — Strategy 2 Feasibility Census

**Status:** pre-implementation feasibility study. Counting only.
**Result:** **`FAIL — INSUFFICIENT ECONOMIC OR STATISTICAL FEASIBILITY`** for
`SETUP_2_COMPRESSION_BREAKOUT_CONTINUATION`.

No strategy performance was evaluated. No P&L, win rate, expectancy, drawdown, CAGR, or
profitability figure was computed. No backtest, portfolio simulation, bootstrap, Monte Carlo,
optimization, or validation/OOS analysis was run. No barrier was resolved and no trade was
simulated.

**Companion artifacts:**
`docs/research/STAGE2A_FEASIBILITY_CENSUS.json` (machine-readable results),
`docs/research/STAGE2A_DATA_ALIGNMENT_AUDIT.md` (timeframe integrity),
`stage2a_census/census.py` (the census itself).

---

## 1. Decision

### `C. FAIL — INSUFFICIENT ECONOMIC OR STATISTICAL FEASIBILITY`

The registered hypothesis does not survive its own pre-registered gate:

| requirement | pre-registered threshold | measured | verdict |
|---|---|---|---|
| Economically feasible unique events | ≥ 200 | **12** | **FAIL** |
| Median `cost_R` | ≤ 0.20 | 0.124 (17 events) | pass |
| Reliable timeframe alignment | exact reconstruction | 7,650/7,662 exact, 12 gap-consistent, 1 tick explained | pass |
| No material look-ahead | causal trigger, next-bar entry | structurally causal; all 17 entries on the next 5m bar | pass |
| Meaningful control-arm distinction | distinct event set | 13 of 17 triggers are not 20-bar-high breakouts | pass, but moot |

The gate is not close. Twelve events is 6% of the required sample, and — critically — the ceiling
is structural: **only 63 compression episodes in 3.5 years satisfy the 6-bar duration floor**, so
even a 100% breakout rate with zero cost rejection could not reach 200. No definitional
reinterpretation rescues this; §6.4 quantifies the variants.

**Candidate A was evaluated independently and is not promoted** (§7). It clears 200 on raw
feasible events but not on unique or non-overlapping events, and it remains underpowered for the
0.15R hypothesis.

---

## 2. Method and provenance

### 2.1 What was processed

Development interval only: `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` — 1,277 days (3.496
years). No validation or out-of-sample bar was read. The script filters on the ISO timestamp
string before parsing any value, so out-of-window rows are never converted.

### 2.2 Datasets (hashes recomputed at run time, **match the manifest**)

| dataset | path | SHA-256 | dev bars |
|---|---|---|---|
| 5m BTCUSDT | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | 367,563 |
| 4h BTCUSDT | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | 7,662 |
| dataset manifest | `backend/data/datasets/manifest.json` | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | — |

Both dataset hashes equal the values recorded in the manifest, so the inputs are the frozen
development series and not a re-download.

### 2.3 Processing configuration

| item | value |
|---|---|
| Script | `stage2a_census/census.py` |
| Script SHA-256 | `db117bae057c2d7ee50a78ff2f153a00785e4d2245d5628578bd47046ad28348` |
| Runtime | 8.56 s wall clock |
| Peak RSS | **585 MiB** (target 4 GB, ceiling 6 GB) |
| Reading strategy | chunked `json.JSONDecoder.raw_decode` over a 32 MiB buffer; only dev-window bars retained; no full-file object graph |
| Resumability | not required: single pass, 8.6 s, no intermediate state |
| Randomness | none (no bootstrap, no sampling) |

### 2.4 Definitions used, and where each came from

The census uses the recommendation document's definitions verbatim. Nothing was simplified or
retuned.

| element | value | source |
|---|---|---|
| Signal timeframe | 4h, closed bars | recommendation §4.1 |
| Realised volatility | platform `_realized_volatility`: sample stdev (ddof=1) of trailing **price differences** | `events.py` |
| Compression ratio | `RV5 / RV20 ≤ 0.60` | recommendation §4.2 |
| Volume dry-up | `volume / mean(volume, 20) ≤ 0.80`, mean taken over the **20 bars strictly before** the bar | recommendation §4.2 + platform `_trailing` |
| Episode | maximal run of bars meeting both conditions | recommendation §4.2 |
| Minimum duration | `≥ 6` bars (24 h) | recommendation §4.2 |
| Trigger | at the bar the episode ends, `close > max(high)` over the episode | recommendation §4.3 |
| Entry | open of the first 5m bar after the trigger bar closes | recommendation §4.4 |
| Structural stop | episode's `min(low)` | recommendation §4.4 |
| Round-trip cost | 26 bps (`0.0026 × entry / stop_distance`) | recommendation §4.5 |
| Gate | `cost_R ≤ 0.20` | recommendation §4.5 |
| Target / max hold | 2R / 18 bars — **recorded only, never simulated** | recommendation §4.4 |
| Candidate A | Donchian(20) + 200-SMA, stop 1.5×ATR(20), 30-bar / 10-bar-low exit | comparison §2.1 A6 (the recommendation delegates to it) |

---

## 3. Candidate C — compression breakout funnel

Measured on 4h closed bars, development split only.

### 3.1 Stage counts (primary reading)

| # | stage | count | % of previous |
|---|---|---:|---:|
| 1 | Valid 4h bars | 7,662 | — |
| 2 | Compression episodes detected | **461** | — |
| 3 | Episodes satisfying duration ≥ 6 bars | **63** | 13.7% |
| 4 | Episodes with a confirmed upside breakout | **17** | 27.0% |
| 5 | Breakouts with a valid positive stop distance | **17** | 100% |
| 6 | Events passing `cost_R ≤ 0.20` | **12** | 70.6% |
| 7 | Unique events after deduplication | **12** | 100% |
| 8 | Events after cooldown restrictions | **12** | 100% |

Stage 7 equals stage 6 because the design's deduplication rule is one event per compression
episode and each episode contributes at most one trigger. Stage 8 equals stage 7 because the
design defines **no cooldown** — this is a design gap, not a measurement (§10).

Context for stage 2: 1,292 of 7,662 bars (16.9%) met the tight condition; 461 maximal runs is what
that produces, and most runs are very short (208 last a single bar).

### 3.2 Rates and spacing

| metric | all triggers (17) | feasible (12) |
|---|---:|---:|
| Events per year | 4.9 | **3.4** |
| Median days between events | 56.3 | 84.2 |
| 10th / 90th percentile gap, days | 7.2 / 154.3 | 34.5 / 154.3 |
| Events closer than the 3-day hold | 0 | 0 |
| Non-overlapping events (greedy, 3-day hold) | 17 | 12 |

By year (triggers): 2021: 2, 2022: 3, 2023: 9, 2024: 3. Feasible: 2 / 3 / 6 / 1.
The events are not clustered in time — there simply are very few of them.

### 3.3 Stop distance and cost

Stop distance as a percentage of entry price (all 17 triggers):

| | median | p10 | p25 | p75 | p90 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| stop % of entry | 2.10% | 1.00% | 1.11% | 3.31% | 4.68% | 0.54% | 7.56% |

`cost_R` at the primary 26 bps assumption (all 17 triggers):

| | median | p10 | p25 | p75 | p90 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cost_R` | 0.124 | 0.057 | 0.079 | 0.235 | 0.260 | 0.034 | 0.478 |

Among the 12 that pass: stop median 2.46% (p10 1.66%, p90 5.56%). The binding failures are the
narrow compressions: at stop distances of 0.5–1.0% the cost is a quarter to a half of the risk
unit. **This is exactly the trap the recommendation predicted** — a compression is a narrow range,
so a structural stop at its low can be too tight to pay for a round trip.

Descriptive thresholds (counts of the 17 triggers, primary stop, 26 bps):

| threshold | 0.10 | **0.20 (gate)** | 0.30 | 0.50 | 1.00 |
|---|---:|---:|---:|---:|---:|
| events passing | 5 | **12** | 16 | 17 | 17 |

Note the shape: the count saturates at 17. **No threshold, however permissive, produces more than
17 events from the 63 episodes.** Relaxing the gate to 1.00R — which would admit trades whose
entire risk unit is consumed by costs — yields 17, not 200.

### 3.4 Interpreting the 27% breakout rate

Stage 4 → 5 loses nothing, so the funnel's real bottlenecks are the duration floor (63 of 461) and
the trigger (17 of 63). The low trigger rate is not a bug: the design requires the breakout to
occur on the single bar at which the compression state stops being true. Bars that end a
compression by going quiet-to-busy *without* closing above the episode high produce no event. That
is the design, and §6.4 shows the alternative readings do not change the conclusion.

---

## 4. Control arm — unconditioned 20-bar-high breakouts

### 4.1 The definition gap

The recommendation defines the control as "20-bar-high breakouts without the compression
condition, identical stop/target/time/cost rules". **A control event has no compression episode, so
it has no episode low, and the stop rule is therefore undefined for the control arm.** The design
gap is recorded in §10 and in the JSON (`ambiguities[0]`).

For counting only, the primary control uses the symmetric structural rule — the lowest low of the
same 20-bar window whose high was broken — because it substitutes a window for the episode while
keeping the rule "stop at the far structural edge of the range that was broken". This is a
**provisional interpretation, not the design**, and it is *generous* to the control: a 20-bar range
is wider than a compressed episode, so control stops are wider and `cost_R` lower. The control
count is therefore an upper bound.

### 4.2 Counts

| metric | value |
|---|---:|
| Raw control triggers | **344** |
| With valid positive stop | 343 |
| Passing `cost_R ≤ 0.20` | **343** |
| Unique after collapsing consecutive triggers | 247 |
| Unique and feasible | 246 |
| Non-overlapping (3-day hold, greedy) | 136 |
| Events per year (feasible) | 98.1 |
| Median stop % of entry | 8.26% |
| Median `cost_R` | 0.031 |

By year: 2021: 111, 2022: 77, 2023: 102, 2024: 54.

The control passes the cost gate almost trivially (343/344) precisely because its structural stop
is four times wider than C's. **The two arms are not matched on stop tightness**, which is the
substantive warning for any later comparison: control events carry a much lower cost burden per
trade, so a like-for-like net-R contrast would flatter the control. This is not a reason to reject
the control; it is a reason to state the asymmetry explicitly if the comparison is ever scored.

### 4.3 Event-set distinction

| relation | count |
|---|---:|
| C trigger bars | 17 |
| Control trigger bars | 344 |
| Both (same 4h bar) | 4 |
| Compression-only | 13 |
| Control-only | 340 |

The conditioning does select a different set: 13 of 17 C triggers are not 20-bar-high breakouts at
all, because a compressed episode's high is often below the 20-bar high. So the *mechanism* the
recommendation relies on — that compression adds an event-selection distinction — is observable.
It is simply not observable **enough times** to support inference.

---

## 5. Candidate A — independent fallback check

Definitions from comparison §2.1 A6, unchanged. Counting only.

| stage | count |
|---|---:|
| Raw Donchian(20) breakouts above the 200-SMA | **271** |
| With valid positive stop (1.5 × ATR(20)) | 271 |
| Passing `cost_R ≤ 0.20` | **237** |
| Unique after collapsing consecutive triggers | 192 |
| Unique and feasible | **170** |
| Non-overlapping (3-day hold, greedy) | **91** |
| Events per year (raw) | 77.5 |

By year (raw): 2021: 93, 2022: 52, 2023: 82, 2024: 44.
Stop distance median 2.14% of entry (p10 1.23%, p90 3.71%); `cost_R` median 0.122.

**Assessment:** A is roughly twenty times more frequent than C and its cost profile is acceptable
(median `cost_R` 0.12, comparable to C). On raw feasible count it clears the 200 threshold; on
*unique* (170) and *non-overlapping* (91) counts it does not. A is materially the more viable
census target — but see §8: 91 independent events only support detecting an edge of ~0.29R, so A
does not automatically become testable for the 0.15R hypothesis either.

Candidate B was not censused, as instructed.

---

## 6. Cost sensitivity

### 6.1 Candidate C, counts passing each gate (17 triggers, primary stop)

| round-trip cost | label | 0.10 | 0.20 | 0.30 | 0.50 | 1.00 |
|---|---|---:|---:|---:|---:|---:|
| 10 bps | sensitivity | 15 | **17** | 17 | 17 | 17 |
| **26 bps** | **PRIMARY** | 5 | **12** | 16 | 17 | 17 |
| 40 bps | sensitivity | 2 | 9 | 12 | 16 | 17 |
| 60 bps | sensitivity | 1 | 5 | 9 | 12 | 16 |
| 100 bps | sensitivity | 0 | 2 | 4 | 9 | 15 |

The primary assumption is retained. At a 10 bps venue all 17 triggers would pass the 0.20R gate; at
40 bps only 9 would. **The conclusion does not depend on this choice**: the best case is 17 events,
which is still 183 short of the gate. That robustness is the useful finding here — the failure is
not an artifact of the cost assumption.

### 6.2 Candidate A, for context

237 of 271 pass at 26 bps. Because A's stops are wider, its count is less cost-elastic than C's,
but it would still lose roughly a third of its sample at 40–60 bps.

### 6.3 Nobitex facts that would change the conclusion

Not invented, not estimated. If any of these is materially worse than the Binance proxy, event
counts fall further, never rise:

- maker/taker fee tiers and whether a resting limit order is even feasible;
- realised bid-ask spread on BTCUSDT (the 2 bps assumption is a proxy, not a measurement);
- tick size and whether a 0.01 tick is achievable at the venue;
- lot step and minimum notional (Stage 6 assumed `1e-5` BTC and `$5`);
- order-book depth at the range edges the strategy trades into;
- outage and maintenance behaviour, which matters because two of the seven data gaps sit inside
  the development window.

---

## 7. The single most important number

Not the 12. The **63**.

Only 63 compression episodes in 3.5 years clear the 6-bar duration floor. Breakout confirmation
(27%) and cost feasibility (71%) then cut that to 12. But even if every one of the 63 had broken
out and passed the cost gate, the sample would be 63 — still less than a third of the 200 required.
The hypothesis as specified is not limited by economics or execution; it is limited by how rarely
the state occurs at a duration the design accepts.

---

## 8. Statistical feasibility

### 8.1 The claim under review

The comparison document asserted that ~100–250 events might be enough to test an approximately
0.15R edge. That claim is **too optimistic and should be withdrawn as stated.**

### 8.2 The assumptions it requires

A detectable-effect calculation needs four things. None is available from this census, because no
outcome was ever computed:

| assumption | status |
|---|---|
| Outcome standard deviation | **unavailable** — would require resolving trades, which is not authorized |
| Significance level | design choice: 0.05 two-sided |
| Desired power | design choice: 0.80 (0.90 for a stricter standard) |
| Event dependence | measurable in part: 0/16 inter-event gaps are under 3 days for C, so the events are temporally separated, but regime dependence is unknown |

### 8.3 Arithmetic under stated assumptions

Normal approximation, σ = 1.0R, α = 0.05 two-sided. This is a design calculation, not a result.

| true edge | n for 80% power | n for 90% power |
|---|---:|---:|
| 0.10R | 785 | 1,051 |
| **0.15R** | **349** | **467** |
| 0.20R | 196 | 263 |
| 0.30R | 87 | 117 |

So a 0.15R edge needs ~349 *independent* trades, not 100–250. The comparison document's range was
wrong by a factor of 1.4–3.5, and it should not be used to justify a minimum sample size.

### 8.4 What the measured samples can detect

Rearranged, at 80% power, σ = 1R:

| sample | n | smallest detectable edge |
|---|---:|---:|
| C, strict feasible | 12 | **0.81R** |
| C, most permissive reading | 30 | 0.51R |
| Candidate A, non-overlapping | 91 | 0.29R |
| Candidate A, unique feasible | 170 | 0.22R |
| Control, non-overlapping | 136 | 0.24R |

A 12-event sample cannot distinguish a 0.15R edge from zero under any conventional power standard;
it would need an edge near 0.8R to show up at all. And these are best cases: they assume
independence, which overlapping regimes violate.

**A minimum event count is a design constraint, not proof of power.** Passing 200 would not by
itself have established that the experiment could answer the question; failing to reach 12 settles
that it cannot.

---

## 9. Look-ahead and causality status

- Every signal input is trailing and ends at the trigger bar's close: `RV5`, `RV20`, the 20-bar
  volume mean (strictly prior bars), and the episode high/low (bars before entry). No future bar
  enters any calculation.
- The trigger is evaluated at a **close**, and entry is the **open of the next 5m bar**, verified
  for all 17 events to exist on the 5m grid and to carry positive volume.
- The episode high is a maximum over the episode; the trigger compares a later close to it, so the
  comparison is causal.
- This is a structural argument, not a harness run: `lookahead.py` was **not** executed, because
  that belongs to implementation, not the census.

No material look-ahead contamination was found in the signal construction.

---

## 10. Ambiguities and unresolved questions

Recorded rather than resolved. None of them can rescue the sample: the ceiling is 63 episodes.

### 10.1 Control-arm stop (blocking for any future comparison)

Undefined in the design. Primary count uses the 20-bar low; §4.1 explains why that is a
provisional, control-favouring reading. **A design clarification is required before the control arm
could be scored**, but the distinction is already observable in event selection (13 of 17).

### 10.2 Deduplication and cooldown

The design says one position at a time but defines no rule for a second trigger while the 18-bar
hold is open. Stage 7 is therefore episode-level deduplication and stage 8 is identical. Reported
as a design gap, not invented.

### 10.3 Trigger window

"Has just ended" was read strictly: the breakout must occur on the bar that ends the episode.
Two looser readings were counted as sensitivities (§3.5 below). The choice matters for the count
(17 vs 28 vs 38) but not for the decision.

### 10.4 Duration floor sensitivity

Not a design change — a demonstration that the bottleneck is structural. Episode counts by floor:

| duration floor | episodes |
|---|---:|
| ≥ 6 (design) | **63** |
| ≥ 5 | 85 |
| ≥ 4 | 122 |
| ≥ 3 | 164 |
| ≥ 2 | 253 |

Only a floor of 2 bars (8 hours) exceeds 200, and that is no longer a "compression state" in the
designed sense.

### 10.5 Trigger-readings table (§3.5)

| reading | triggers | feasible (0.20R) |
|---|---:|---:|
| strict (primary) | 17 | **12** |
| first breakout within 6 bars | 28 | 21 |
| first breakout before a new episode | 38 | 30 |

Even the most permissive reading yields 30 — 15% of the gate.

### 10.6 Other unresolved items

- Nobitex execution facts (§6.3) remain unknown; every `cost_R` here is a Binance proxy.
- Whether the 4h series is *complete* during the seven 5m gaps is not fully answerable: the vendor
  4h bars match the partial 5m sums exactly, which suggests both series omit the same intervals
  (consistent with no-trade outages), but the underlying cause is inferred, not verified.
- Regime composition of the 3.5-year window is not characterised. Given a 12-event sample, a
  regime-contrast analysis would be meaningless.

---

## 11. Confirmations

- **No P&L, win rate, expectancy, drawdown, CAGR, or profitability** was computed anywhere.
- **No backtest or portfolio simulation** was run; no barrier was resolved; the 2R target and
  18-bar hold exist only as recorded design parameters.
- **No optimization** was performed; the 0.20R gate was not relaxed, and the primary reading was
  reported even where it produced the smallest count.
- **No validation/OOS data was read**; the loader filters to the development interval before
  parsing values.
- `stage6_rebuild_v2/` and `stage6_acceptance_audit/` were not modified. The census imported no
  Stage 6 module and reimplemented only the two indicator formulas it needed, matching the
  platform definitions exactly (verified by independent recomputation of one event).
- Nothing was committed or pushed.
- Peak memory 585 MiB, runtime 8.6 s, single pass, no resumability required.
