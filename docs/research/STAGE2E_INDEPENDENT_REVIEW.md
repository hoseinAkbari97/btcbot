# Stage 2E — Independent Specification Review

**Scope:** `STAGE2E_CANDIDATE_B_SPEC.md`, `STAGE2E_CANDIDATE_D_SPEC.md`,
`STAGE2E_SHARED_CENSUS_PROTOCOL.md`, and their JSON configurations.
**Method:** documentation-level adversarial review. No market data was read and no signal was counted.
**Outcome:** four critical/major defects were found and corrected **before** the freeze hashes were
computed. The remaining open items are design limitations, not ambiguities, and are listed in §5.

---

## 1. Review questions and answers

| # | question | answer | evidence |
|---|---|---|---|
| 1 | Can two independent engineers implement the exact same signal? | Yes for the specified rules, with the caveats in §4. Both specs give closed-bar boolean formulas, a worked synthetic example, exact counts, and exclusion labels. | B §3–§5, §10.1; D §4–§7, §11.1 |
| 2 | Is any rule discretionary? | No. Both specs state that visual interpretation is prohibited and that a condition which cannot be expressed as a closed-bar boolean is removed rather than judged. | B §0, §12; D §0, §13; protocol §8 |
| 3 | Is any timestamp ambiguous? | Was **yes** in D (finding R1). Now every decision instant is pinned: B uses the expansion bar, the confirmation bar's `close_time`, and the next bar's `open_time`; D uses the eighth measurement bar's `close_time`. | B §5.4–§5.5; D §4.2, §7.1 |
| 4 | Is any indicator allowed to use an unfinished candle? | No. B reads the last 4h bar with `close_time <` the 1h bar's open; D reads the last 4h bar with `close_time <` the signal instant; D's 1h stop ATR uses `close_time <=` the signal instant, which is still a completed bar. | B §4.1; D §4.2, §6.1 |
| 5 | Can a signal use future data? | No. Every input is a closed bar at or before the decision instant, and entry is strictly later. The protocol requires a causality check that fails the run rather than warning. | protocol §1.5 |
| 6 | Are episode and deduplication rules deterministic? | Yes. B: one active episode, later expansions absorbed, key `B:{expansion_open_time}`. D: one opportunity per session, key `D:{session_start}|{session_id}`. | B §6; D §8 |
| 7 | Are cost and stop calculations unambiguous? | Yes. Both define `cost_R = 0.0026 * entry_open / D`, forbid stop widening, and treat a sub-1.30% stop as a gate failure rather than a special case. | B §5.6, §8; D §7.2–§7.3 |
| 8 | Are all denominators defined? | Yes. Each spec has a frozen denominator table; no share may be computed against an unnamed population. | B §9.1; D §10.1 |
| 9 | Can the same signal be counted twice? | No. B asserts one signal per episode and checks duplicate entry times / confirmation bars. D asserts one signal per session and checks duplicate session keys, which must be zero. | B §6.5; D §8.1 |
| 10 | Can a gap create an artificial signal? | Mitigated. Partial buckets are unusable, segments break at gaps, nothing is synthesised, and B refuses entry across a segment break. A gap can still delete signals, which is reported as warm-up/gap loss rather than repaired. | B §2, §5.5; D §2.2; protocol §1.3–§1.4 |
| 11 | Can the same market event be counted as independent opportunities? | Partly, and this is a real limit. Non-overlap enforces spacing, not causal independence; two 72h-separated B signals can belong to one multi-week move. This is stated, not solved. | B §7.3; D §9.2; §5 U7 below |
| 12 | Are the decision thresholds justified and correctly labelled? | The 150 floor is labelled a project protocol choice with no statistical derivation; 349 is labelled a planning reference that does not guarantee power; the design margin is labelled a diagnostic, not expectancy. Additional candidate-specific thresholds are marked *proposed, requiring approval*. | B §11.3; D §12.2; protocol §6 |

---

## 2. Defects found and corrected

All corrections were applied to the specifications and configurations **before** the hashes in
`STAGE2E_FREEZE_MANIFEST.json` were computed. Each is a separate commit in the Stage 2E series.

| id | severity | defect | effect if shipped | correction |
|---|---|---|---|---|
| **R1** | critical | D selected the stop-ATR hour with `close_time < signal instant`, but the 1h bar opening at `01:00` closes at exactly `01:59:59.999`, the signal instant. The spec text nevertheless claimed `q` was that bar. | The prose and the rule contradicted each other, and a literal implementation would use a two-hour-stale ATR while claiming a one-hour ATR, changing every `cost_R` in D. | Comparison changed to `close_time <= signal instant`, with the equality case stated explicitly. Config updated to match. |
| **R2** | major | B never stated the first local index at which an expansion is testable. `ATR[t-1]` needs `ATR` defined at `t-1`, i.e. `t-1 >= 13`, so the first testable bar is local index 14, not 13. | Off-by-one divergence between implementations, shifting the entire B count. | Explicit statement added: first testable expansion is local index 14, the fifteenth bar of the segment. |
| **R3** | major | Both specs computed a 540-bar percentile over a window that could be partially undefined after a gap, without saying what to do. | Two implementers could report different percentiles, or silently drop early bars. | Incomplete window now yields `Unknown` and suppresses the signal; truncated-window percentiles are forbidden. |
| **R4** | major | B did not say what happens when the confirmation bar is the last bar of its 1h segment, so the entry bar sits across a gap. | An implementation could enter after a data break at a price that is not a contiguous continuation. | Now explicitly rejected as `no_entry_bar`; a post-gap segment is not a valid continuation. |
| **R5** | minor | B's expansion test divided by `range[t]` before establishing `range[t] > 0`. | Division by zero or an infinity comparison in some implementations. | Evaluation order frozen: positivity first, division second. |
| **R6** | minor | The top verdict tier used `N >= 349`, which reads as a requirement. | Reintroduces the exact misreading Stage 2D corrected. | Added: 349 is a tier label carried from Stage 2C, not a requirement and not a power guarantee. |

No defect was found in the shared protocol's data-integrity or freeze sections.

---

## 3. Ambiguities inherited from Stage 2D and how they were resolved

| # | Stage 2D ambiguity | resolution | where |
|---|---|---|---|
| 1 | B regime permission written as `close > SMA50` **or** `10-bar return > 0` | Replaced by a conjunction: `close > SMA50` **and** the SMA is higher than 6 bars ago, **and** the 4h ATR percentile is in [20, 95] | B §4.2 |
| 2 | B retest "1–6 bar window" | Frozen as indices `e+1 … e+6`, first touch only; the expansion bar cannot be the retest | B §5.2 |
| 3 | B retest tolerance not tied to a bar's ATR | Tolerance and penetration measured in units of `ATR[e]`, the expansion bar's ATR | B §5.1–§5.3 |
| 4 | B episode definition undefined | Full lifecycle: one active episode, later expansions absorbed, first failing condition ends it, key `B:{expansion open_time}` | B §6 |
| 5 | B stop floor as a skip rule | Removed; the cost gate performs the exclusion, so there is one threshold rather than two | B §5.6 |
| 6 | D deduplication unit undefined | The session is the episode; one opportunity per session; `duplicate_session` must be zero | D §8 |
| 7 | D two VWAP definitions | Session VWAP only, typical price, reset per session; rolling variant rejected | D §5 |
| 8 | D two volatility-budget definitions | One: 4h ATR(14) percentile over 540 bars, band [25, 80]; the 0.5×–1.5× median variant rejected | D §6.2 |
| 9 | D session/day boundaries vs rolling non-overlap | Sessions fixed on UTC with `[start, end)` ownership; non-overlap is a rolling 24h rule, explicitly not a UTC-calendar-day rule | D §3, §9.1 |
| 10 | D threshold mixing a price distance with a return | Threshold made dimensionless: `0.5 * ATR1h[q] / P0` | D §4.2 |
| 11 | Both: widening stops to reach feasibility | Forbidden in both; the gate does the work | B §5.6; D §7.2 |

---

## 4. Residual implementability risks (not defects)

These do not make the specification ambiguous, but they are places where two careful implementations
could still differ and should therefore be validated against each other before counting:

1. **Floating-point equality.** Comparisons such as `cost_R <= 0.20` and `TR >= 2.0 * ATR` sit exactly
   on boundaries for some bars. The specs fix the operator but not the numeric type. A cross-check run
   should confirm the two implementations agree on the count of boundary cases.
2. **`quote_volume` availability.** D's VWAP deliberately uses `volume` only, and `quote_volume` is a
   diagnostic. If the field is absent the census must not fail; the diagnostic is simply omitted.
   (If `volume` itself is absent, the run aborts with `schema_error`.)
3. **Segment-local ATR initialisation.** Both candidates re-initialise ATR per segment. An
   implementation that carries state across a gap will diverge on bars immediately after each of the
   seven registered 1h gaps.
4. **Rounding of reported statistics.** Medians and percentiles of `cost_R` depend on the interpolation
   convention. The protocol fixes the percentile construction only for the 4h regime window, not for
   sample statistics. Reports should state the convention used.
5. **Timestamp string comparison.** Interval filtering is by ISO string. All timestamps in the dataset
   use a fixed `+00:00` format; an implementation that uses a different offset form would filter
   incorrectly.

---

## 5. Known unresolved issues (documented, not blocking the freeze)

| id | issue | why it is unresolved | status |
|---|---|---|---|
| **U1** | The numeric design values (2.0× ATR, body 0.55, close location 0.75, six-bar retest, 0.25 tolerance, 0.50 penetration, three-bar confirmation; 0.5× ATR threshold, [25, 80] budget band) have no empirical derivation. | Deriving them requires market data, which this stage prohibits. They are frozen as priors, not fitted. | accepted; must not be tuned after counting |
| **U2** | UTC sessions are arbitrary on a 24/7 market. | Cannot be resolved without evidence, and using evidence would be optimisation. | accepted; per-session split and `US`-only sensitivity are mandatory |
| **U3** | The 150 floor has no statistical derivation. | It is inherited protocol from Stage 2C; deriving a replacement is out of scope and would itself need approval. | accepted; labelled everywhere |
| **U4** | B's retest filter conditions on post-event price action, so the counted sample is a selected subset. | Only an outcome study can measure the selection effect. | accepted; disclosed in B §4.3 and §0 |
| **U5** | Nobitex fees, spreads, slippage, order types, and lot rules are unknown. | No venue data exists in the repository and none may be downloaded. | accepted; Binance proxy labelled; venue facts listed as required before deployment |
| **U6** | Whether D's sessions represent independent opportunities is unverifiable from counts. | Requires outcome dependence analysis. | accepted; Kish reported as a concentration diagnostic only |
| **U7** | Spacing rules do not make two opportunities causally independent. | Structural limitation of any signal census. | accepted; stated in both specs |

No critical ambiguity remains. The two specifications are therefore frozen as version `1.0.0`.

---

## 6. Specification-to-configuration consistency

Each frozen parameter in the Markdown has a value entry in the JSON. The mapping verified row by row:

| parameter | B spec | B config | D spec | D config |
|---|---|---|---|---|
| signal timeframe | 1h | `timeframes.signal = 1h` | 15m | `timeframes.signal = 15m` |
| regime / budget timeframe | 4h | `timeframes.regime = 4h` | 4h | `timeframes.volatility_budget = 4h` |
| expansion multiple | 2.0 | `expansion.tr_multiple_min = 2.0` | n/a | n/a |
| body / range minimum | 0.55 | `expansion.body_range_min = 0.55` | n/a | n/a |
| close location minimum | 0.75 | `expansion.close_location_min = 0.75` | n/a | n/a |
| regime SMA / slope | 50 / 6 | `regime_4h.sma_window = 50`, `slope_lookback_bars = 6` | n/a | n/a |
| 4h percentile window / band | 540 / [20, 95] | `percentile_window_bars = 540`, `percentile_bounds = [20.0, 95.0]` | 540 / [25, 80] | `percentile_window_bars = 540`, `percentile_bounds = [25.0, 80.0]` |
| retest window | 1..6 | `window_start_offset_bars = 1`, `window_end_offset_bars = 6` | n/a | n/a |
| retest tolerance | 0.25 × ATR[e] | `touch_tolerance_atr_multiple = 0.25` | n/a | n/a |
| penetration limit | 0.50 × ATR[e] | `max_penetration_atr_multiple = 0.50` | n/a | n/a |
| confirmation window | 3 bars | `confirmation_window_bars_after_touch = 3` | n/a | n/a |
| session table | n/a | n/a | 3 × 8h UTC | `sessions.definitions` |
| first-two-hour threshold | n/a | n/a | 0.5 × ATR1h / P0 | `signal.threshold_atr_multiple = 0.5` |
| VWAP | n/a | n/a | session, typical price | `vwap.type = session`, `price_input = typical` |
| stop | min low e..c | `stop.rule` | entry − 1.0 × ATR1h | `stop.atr_multiple = 1.0` |
| stop floor | none (gate only) | `stop.floor_pct = null` | none (gate only) | `stop.floor_pct = null` |
| cost | 26 bp, gate 0.20 | `costs.*` | 26 bp, gate 0.20 | `costs.*` |
| non-overlap canonical | 72h | `overlap.canonical_hours = 72` | 24h | `overlap.canonical_hours = 24` |
| non-overlap sensitivities | 24h, 120h | `sensitivity_hours = [24, 120]` | 12h, 48h | `sensitivity_hours = [12, 48]` |
| development interval | 2021-01-01 → 2024-07-01 | `data.dev_start`, `data.dev_end` | same | same |
| 150 floor | 150 | `verdict_thresholds.project_floor_non_overlapping = 150` | 150 | same |
| proposed thresholds | 0.25 / 0.12 | `proposed_requiring_approval` | 0.30 / 0.17 / 0.02 | `proposed_requiring_approval` |

A machine check of JSON validity was run for both configurations. No placeholder or prose-only
parameter remains in either JSON.

---

## 7. Freeze statement

With the corrections in §2 applied, both specifications are deterministic, causal, and free of
discretionary rules. Their configurations mirror them. The freeze manifest records the SHA256 of the
specifications, configurations, shared protocol, and this review, together with the dataset hashes, the
development interval, the cost assumptions, the protocol version, and the freeze timestamp.

**No census has been run. No market data has been processed. No signal has been counted.**

**Reviewer:** Stage 2E authoring pass, 2026-11-02.
