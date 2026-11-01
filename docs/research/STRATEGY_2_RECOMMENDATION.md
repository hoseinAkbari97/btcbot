# Strategy 2 — Recommendation

**Status:** research design only. No code was written, no backtest was run, no parameter was
optimized, no bootstrap or Monte Carlo was executed, and no validation/out-of-sample result was
read, inspected, or used. Setup 1 is untouched.

**Companion document:** `docs/research/STRATEGY_2_CANDIDATE_COMPARISON.md` (full analysis, evidence
tags, comparison matrix, references).

Evidence tags as in the companion document: **[F]** repository fact, **[L]** literature-backed,
**[E]** engineering judgment, **[H]** unverified hypothesis.

---

## 1. Decision

**Selected: Candidate C — volatility compression and expansion**, registered as

```
SETUP_2_COMPRESSION_BREAKOUT_CONTINUATION
```

The hypothesis under test, in one sentence:

> On BTCUSDT, a sustained compression of realised volatility and volume that resolves with a
> confirmed close outside its own range produces long breakouts whose net expectancy, after the
> frozen cost model, is positive **and larger than the net expectancy of breakouts taken without
> that compression condition**.

Note the two-part claim. The strategy must clear two bars, not one: it must make money, and the
compression state must be doing identifiable work. A version that is profitable but not better
than unconditioned breakouts has failed the research question, even though it "worked".

**Why not simply Candidate A?** Candidate A is the better engineering choice and the weaker
experiment, for one reason: **it cannot be distinguished from BTC beta at this sample size.**
Details in §3.

**This recommendation is conditional.** §5 lists the gates that can and should overturn it before
any scoring begins. If the census shows fewer than 200 eligible events, C is untestable and
Candidate A becomes the fallback — not because A is better, but because it is the only remaining
candidate that clears the cost constraint.

---

## 2. Why C, in the terms the task asks for

### 2.1 Why it is preferable to the other two

| criterion | A — Trend | B — Mean reversion | C — Compression breakout |
|---|---|---|---|
| Clears the 26 bp cost constraint structurally | Yes | **No** — small realised wins vs wide stops | Yes, with an explicit `cost/R` gate |
| Enough independent events to falsify | **No** — ~15–50/yr **[E]** | Yes | Yes, ~100–250 over the split **[E]** |
| Distinguishable from buy-and-hold | **No** — long-only trend ≈ timed beta | Partly | Yes, via the unconditioned-breakout control |
| The hypothesis being tested is the interesting one | No — tests "does trend pay" | No — tests a half-removed effect | Yes — tests whether a *state* adds information |

C is the only candidate that is simultaneously affordable, testable, and identifiable. That is the
entire argument, and it is a conjunction: A fails the third column, B fails the first.

### 2.2 Why its economic hypothesis is independently defensible

The state half of the hypothesis is about the most robust regularity in the data: volatility
clusters **[L]** (Bollerslev 1986). Compression is the low-volatility state; expansion is the
transition out of it. That much is uncontroversial and needs no crypto-specific assumption.

The directional half is a separate claim and is *not* implied by clustering: volatility says how
much, not which way. So the design does not smuggle direction in through the volatility measure.
It adds an explicit, falsifiable directional claim — that a range break after a coil continues —
supported by breakout literature outside crypto **[L]** (Holmberg, Lönnbark & Lundström 2013) and
by a liquidity mechanism that is specific and checkable: resting liquidity accumulates at range
edges, and consuming it forces price to travel to the next level **[H]**.

Because the two halves are separate, the experiment can fail informatively: a null result on the
contrast says the state adds nothing, which is a real answer even if the level is positive.

### 2.3 Why it is sufficiently different from Setup 1

| dimension | Setup 1 (frozen) | Strategy 2 |
|---|---|---|
| State variable | A liquidity level being pierced (**price structure**) | Realised volatility and volume contracting (**volatility state**) |
| Directional logic | **Reversal** — fade the sweep, expect rejection | **Continuation** — buy the break, expect follow-through |
| Signal timeframe | 5m | 4h |
| Execution grid | 5m | 5m, resolving a 4h signal |
| Stop basis | Local swing low (tight) | Compression window low (wide) |
| Target | +1R | +2R |
| Holding period | ≤ 12 × 5m ≈ 1 hour | ≤ 18 × 4h ≈ 3 days |
| `cost/R` at entry **[E]** | frequently > 1.0; 85.6% of candidates infeasible **[F]** | 0.08–0.15, gated at 0.20 |
| Same-bar exposure **[F]** | 24.6% of observations ambiguous | expected well under 15%, and gated |

The two share only the venue proxy, the cost model and the accounting machinery — which is
exactly what should be shared.

### 2.4 Why it is testable with available data

**[F]** The dataset already contains 4h and 5m BTCUSDT series over identical coverage
(`backend/data/datasets/manifest.json`; the 4h series has zero registered gaps). The compression
definition already exists as a detector with repository defaults
(`detect_compression` in `backend/app/services/research/events.py`), the barrier resolution
contract exists (`outcome_contract.resolve_barriers`), the cost and sizing models are frozen and
audited, and the cluster/block bootstrap machinery is accepted. No new data, no new dependency, no
new venue.

---

## 3. The most serious objection to this recommendation

**That C is Candidate A wearing a filter, and the filter is a fitted story.**

This is the objection I would make if reviewing it, and it deserves a direct answer rather than a
reassurance.

A breakout of a 20-bar high *is* a momentum entry. If compressions cluster where trends begin, C
would inherit A's beta exposure while appearing to be something more specific. The defence is not
rhetorical; it is structural:

1. **The control arm is mandatory.** Every result is reported as a contrast against unconditioned
   20-bar-high breakouts with identical stop, target, time exit and costs. If the compression adds
   nothing, the contrast is indistinguishable from zero and C is rejected — even if the level is
   positive. A cannot be tested this way, because "trend, but only when it is trending" has no
   comparable control.
2. **The stop is structural, not fitted.** It is the compression window's low. No ATR multiple is
   chosen.
3. **The parameters come from the repository, not from the results.** volatility window 20,
   compression ratio 0.60, volume ratio 0.80, minimum history 20 — all are the existing detector's
   defaults **[F]**. They were chosen before this task and are not free.

A second, more practical objection: **the gate and the power requirement may be mutually
exclusive.** A compression is, by definition, a narrow range, so the structural stop can be small,
`cost/R` can exceed 0.20, and the eligible-event count can collapse below 200. If that happens, C
is not testable on this venue, and no amount of cleverness fixes it — the honest outcome is to
report that and fall back. §5 makes this a pre-registered gate rather than a post-hoc discovery.

A third: **the 4h signal / 5m execution split is new machinery**, and new machinery is where
silent look-ahead bugs live. It is also the part that most needs the existing look-ahead harness.

---

## 4. Falsifiable definition (pre-registration draft)

To be frozen and hashed **before** any scoring run, in the manner of `STAGE6_V2_PROTOCOL.md`. No
value below may be changed after seeing a result; a change requires a new numbered protocol.

### 4.1 Scope

| item | value |
|---|---|
| Instrument | BTCUSDT |
| Signal timeframe | 4h, closed bars only |
| Execution grid | 5m |
| Split | development only: `2021-01-01T00:00:00Z` inclusive → `2024-07-01T00:00:00Z` exclusive **[F]**, identical to Setup 1 for comparability |
| Side | long only (spot) |
| Concurrent positions | one |
| Venue model | Binance spot proxy — **not** a Nobitex claim **[F]** |
| Validation / OOS | not read, not authorized |

### 4.2 State definition (compression)

All inputs are 4h closed bars; every window is trailing and ends at the signal bar.

- `RV_k` = trailing realised volatility over `k` bars, using the platform's existing definition
  (`_realized_volatility`), so the measure is the same one `detect_compression` and
  `detect_displacement` already use.
- `compression_ratio = RV_5 / RV_20`
- `volume_ratio = volume / mean(volume, 20)`
- A bar is **tight** when `compression_ratio ≤ 0.60` **and** `volume_ratio ≤ 0.80`.
- A **compression episode** is a maximal run of tight bars.
- A compression is **eligible as a state** only if `duration_bars ≥ 6` (i.e. at least 24 hours).
  This is one pre-registered guard, not a tunable: a single quiet bar is not a coil.

All thresholds are the existing detector defaults **[F]**; the duration floor is the only new
number, and it is justified by the state needing to span more than one bar to have edges.

### 4.3 Trigger

At the close of a 4h bar, if a compression episode has just ended (the bar is no longer tight) and

```
close > highest_high(compression episode)
```

then the trigger fires. The comparison is **close versus the episode's high**, not wick-versus-high:
a wick outside the range that closes back inside is a failed break, and treating it as a break is
the error that `detect_compression` already documents for releases.

### 4.4 Entry, stop, target, exits

| element | rule |
|---|---|
| Entry | open of the first 5m bar after the triggering 4h bar closes (causally clean; no same-bar signal use) |
| Stop | the compression episode's lowest low |
| Target | entry + 2 × (entry − stop) |
| Primary exit | target or stop, resolved on 5m bars by the frozen `resolve_barriers` contract |
| Time exit | close of the 18th 4h bar after entry (≈3 days) |
| Tie convention | **stop-first**, primary, matching the frozen baseline; tie-win reported as sensitivity only |
| Invalidation | none beyond the stop: no discretionary exits |

### 4.5 Sizing, feasibility and costs

Frozen, reused unchanged from Stage 6 **[F]**: $10,000 initial equity, 1% nominal risk, lot `1e-5`,
tick `0.01`, minimum notional `$5`, spot cash cap, 0.1% fee per side, 3 bps adverse per side,
`cost_scenarios` 0.5×/1×/1.5×/2×/3× in both refiltered and fixed universes.

One pre-registered addition:

- **Feasibility gate:** reject any signal whose `cost/R > 0.20`. This is the same kind of envelope
  as Stage 6's `max_cost_to_risk`, set far tighter because the evidence says 1.0 was far too
  permissive **[E]**.

### 4.6 Metrics and controls

| item | definition |
|---|---|
| Primary metric | **net R per executable trade**, after the frozen cost model |
| Primary contrast | conditioned (C) minus unconditioned (control) net R per trade, with bootstrap CI on the difference |
| Control arm | 20-bar-high breakouts **without** the compression condition, identical stop/target/time/cost rules |
| Secondary | portfolio realisation under capital constraints; final equity is diagnostic only |
| Dependence | episode-cluster bootstrap **and** 14-day block bootstrap, 10,000 resamples, seed `20240101` **[F]** |
| Ambiguity | report same-bar share and tie-win sensitivity |
| Additional controls | random-entry arm with matching stop/target/holding distribution; buy-and-hold for time-in-market context |
| Diagnostics | `cost/R` distribution, episode-to-trade ratio, funded-trade count, capital-exhaustion date if any |

### 4.7 What would make me reject it

Pre-registered. Each is a **stop**, not a discussion point.

1. **No power.** Fewer than 200 eligible events in the development split after the feasibility
   gate. → Untestable on this data; report as such and do not proceed.
2. **Negative level.** Net R per trade ≤ 0 with a 95% interval entirely below zero.
3. **No conditioning value.** Positive net R, but the conditioned-minus-unconditioned contrast is
   ≤ 0 or indistinguishable from zero. → The compression state is not doing research work; C is
   rejected regardless of profitability.
4. **The edge is a tail artifact.** Net R > 0 driven by fewer than ~5% of trades, such that
   removing the top decile flips the sign.
5. **Costs dominate.** Median `cost/R` above 0.20 after the gate, or the 3× scenario turning the
   sign while the 0.5× scenario is flat — i.e. the result lives inside the cost assumption.
6. **Ambiguity dominates.** Same-bar share above 15%, or the conclusion flips between stop-first
   and tie-win conventions.
7. **Capital infeasibility.** The portfolio cannot fund a majority of eligible signals, or exhausts
   capital before half the window, replicating Setup 1's terminal condition.
8. **Regime dependence.** The contrast is positive only inside one calendar regime (e.g. only in
   2021, or only after a specific crash), with no signal in the remainder of the split.

Any of 1–3 is a clean rejection of the hypothesis. 4–8 are rejections of the *implementation's
claim to evidence*, and should be reported as such rather than quietly patched.

---

## 5. Before any scoring: the census gate

Milestone 0 of implementation is **counting only** — no P&L, no exits simulated, no outcome data
touched:

1. Count compression episodes with `duration_bars ≥ 6` in the development split.
2. Count how many produce a valid trigger (close above the episode high).
3. Apply the `cost/R ≤ 0.20` gate using entry price and the episode low.
4. Report the resulting eligible-event count, the `cost/R` distribution, and the episode-to-trade
   ratio.

**Gate:** ≥ 200 eligible events, median `cost/R` ≤ 0.20. If it fails, the recommendation falls to
Candidate A and this document is superseded, not amended.

The census is cheap and it is the highest-value step in the plan, because it converts the two
biggest unknowns (frequency and affordability) into measured facts before any effort is spent on
execution machinery.

---

## 6. Architecture fit

The long-term goal is a modular research platform: shared data, execution modelling, risk and
portfolio accounting, statistics, robustness and reporting, with pluggable signal generators. That
framework **should not be built now.** What follows is the minimum that this specific experiment
requires, and nothing more.

### 6.1 Reuse unchanged (do not re-implement)

| capability | existing component |
|---|---|
| Candle stream, gap index, split boundaries | `research/setup1.py` (`GapIndex`, `split_bounds`), `research/split_filter.py` |
| Causal event/confirmation discipline | `research/events.py` (`ResearchEvent`, `confirmation_index`) |
| Compression state | `research/events.py` (`detect_compression`) — needs the two additions below |
| Barrier resolution | `services/outcome_contract.py` (`resolve_barriers`) — the single source of truth |
| Costs and sizing | `stage6_rebuild_v2/portfolio.py` / `accounting.py` (`assess_trade`, `size_position`) |
| Statistics | `accounting.py` (`cluster_bootstrap`, `block_bootstrap`) |
| Look-ahead testing | `research/lookahead.py` |
| Determinism and hashing pattern | `stage6_rebuild_v2/verify_determinism.py`, `code_version.json` |
| Segmented, checkpointed execution | `research/segmented_runner.py`, `research/streaming.py` |

### 6.2 Three minimal additions, each justified by this experiment

1. **Compression range boundaries.** `detect_compression` emits `range_5/10/20` but not the
   episode's highest high and lowest low, and it emits on *release* rather than on a range break.
   Add `episode_high`, `episode_low` and `episode_end_index` to its event features. This is a
   feature addition to an existing detector, not a new abstraction — and Setup 1 does not read
   those keys, so it cannot change Setup 1 behaviour.
2. **Causal timeframe aggregation.** A `resample_closed(candles, target_timeframe)` that emits only
   completed higher-timeframe bars, plus an index map from a 4h bar to the first 5m bar after it
   closes. Justified because the signal grid and execution grid genuinely differ here; this is a
   function, not a framework.
3. **Execution-on-finer-grid helper.** A single shared routine that resolves a position defined on
   a coarse grid by walking finer bars, honouring data gaps (no invented bars, as in Setup 1).
   Justified because it is the one genuinely new execution pattern, and the next strategy will need
   it too; putting it in one place prevents two divergent implementations.

### 6.3 Explicitly do not build

- A strategy registry or plugin system — there is one strategy.
- A generic parameter-search or walk-forward engine — parameters are frozen and few.
- A multi-instrument portfolio layer — there is one instrument.
- Any change to `stage6_rebuild_v2/`, `stage6_acceptance_audit/`, or the frozen Setup 1 protocol.

### 6.4 Where the code should live

A new directory (for example `stage7_setup2/`) mirroring the `stage6_rebuild_v2/` layout: the
protocol, the implementation, the verification script, and a determinism record alongside the
artifacts. Keeping it beside — never inside — the frozen v2 directory preserves the immutability
guarantees the manifest pins.

---

## 7. Implementation milestones

No code is written in this task. The order below is designed so that each milestone can *stop* the
project cheaply.

| # | milestone | exit criterion |
|---|---|---|
| 0 | **Pre-registration** — freeze this definition as `STAGE7_V2_PROTOCOL.md` with a SHA-256, before any scoring | Protocol hash recorded |
| 1 | **Census** — counting only, per §5 | ≥ 200 eligible events and median `cost/R` ≤ 0.20, or stop |
| 2 | **Compression range features** — add `episode_high/low/end_index` to the detector; unit tests; confirm Setup 1 outputs unchanged | Existing Stage 6 determinism hashes unchanged |
| 3 | **Timeframe aggregation + causality tests** — closed-bar resampling and 4h→5m index map, proven against synthetic fixtures and the look-ahead harness | Look-ahead suite passes |
| 4 | **Signal-level scoring** — gross and net R per trade for the conditioned arm and the control arm, with cluster intervals | Primary contrast computed, ambiguities reported |
| 5 | **Executable and portfolio levels** — capital-constrained realisation, cost scenarios, accounting identities | All identities pass; no negative cash |
| 6 | **Robustness** — tie convention, block length, one pre-declared compression-ratio sensitivity (0.50 and 0.70), random-entry arm | Conclusion stable or explicitly qualified |
| 7 | **Verdict and registry entry** — accept, reject, or untestable, with a freeze record | Registry entry written; artifacts hashed |

Milestones 2–3 are the only substantial engineering. If milestone 1 fails, none of it is needed.

---

## 8. What would change this recommendation

Stated up front so the decision is auditable rather than post-hoc:

- **If the census fails** (< 200 eligible events), C is untestable and Candidate A becomes the
  fallback. A is the weakest to interpret but it is affordable and buildable, and a properly
  benchmarked A is still a better experiment than no experiment.
- **If a second instrument becomes available**, candidate A's beta confound weakens substantially
  (a cross-sectional trend comparison across assets is a genuinely different, and stronger,
  experiment). That would reopen the A-versus-C decision on new grounds.
- **If Nobitex execution data becomes available** and shows materially wider spreads than 3 bps per
  side, every candidate's `cost/R` worsens; C's explicit gate would reject more events, and B would
  become even less viable.
- **If the conditioning contrast fails at milestone 4**, the honest conclusion is that volatility
  compression is a description, not an edge — and the next experiment should not be a third
  variation on continuation.

---

## 9. Important missing information

These are unresolved and they limit confidence in the recommendation. None was guessed at.

1. **Nobitex execution terms.** Fees, tick/lot/min-notional, realised spread, liquidity, outages.
   Every cost figure here is a Binance proxy **[F]**, and `cost/R` is the central design parameter.
   This is the largest single gap.
2. **Event frequency is unmeasured.** The 100–250 estimate, the 5–15 day cadence and the 1–5 day
   holding period are all **[E]** engineering estimates. Milestone 1 exists because of this.
3. **4h/5m alignment.** The 4h manifest reports zero gaps while the 5m series has 7 gaps / 213 bars
   **[F]**. Whether the two series agree bar-for-bar at every boundary has not been checked, and
   the multi-timeframe design depends on it.
4. **No order-book or trade-tape data**, so the range-edge liquidity mechanism (C3) cannot be
   measured, only assumed. It is tagged **[H]** for that reason.
5. **No short side.** Spot-only is a hard constraint that materially weakens B and limits A; it
   also means no candidate can hedge, so all results are long-exposure results.
6. **No cross-sectional universe.** With one instrument, beta confounding cannot be eliminated, only
   benchmarked.
7. **The literature is not about this dataset.** All **[L]** claims come from other markets, other
   periods, and (for the crypto papers) cross-sectional weekly/monthly studies — not from
   5-minute-to-4h BTCUSDT spot execution under a 26 bp round trip.

---

## 10. Confirmation

- No strategy was implemented. No file outside `docs/research/` was created or modified.
- No backtest, simulation, optimization, bootstrap, or Monte Carlo was run.
- No market data was ingested, parsed, or processed; dataset and manifest files were inspected for
  schema and metadata only.
- No validation or out-of-sample data was read, scored, or used to select a candidate.
- Setup 1 and its frozen artifacts, including `stage6_rebuild_v2/` and
  `stage6_acceptance_audit/`, are byte-identical.
- No dependency was installed, no data was downloaded.
- Nothing was committed or pushed.

**Awaiting explicit authorization before implementation.**
