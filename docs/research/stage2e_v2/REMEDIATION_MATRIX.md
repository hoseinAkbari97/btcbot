# Stage 2G — Remediation Matrix for the Stage 2F Audit

**Stage:** 2G (remediation only — no census).
**Version remediated to:** `2.0.0`.
**Remediation basis:** `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`.
**Original rejected freeze:** `docs/research/STAGE2E_*` version `1.0.0` (immutable).
**Remediated artifacts:** `docs/research/stage2e_v2/` — Candidate B spec and config, Candidate D spec
and config, shared protocol, this matrix, and the independent review.
**Status of this document:** remediation record, not an audit pass. A separate independent audit of
version `2.0.0` has not been performed and is not claimed.

> No market data was read to build this matrix. No signal was counted. No census, backtest, P&L,
> expectancy, win rate, portfolio simulation, bootstrap, Monte Carlo, or parameter optimisation was
> run. The corrections were derived from the specifications and the Stage 2F audit text only.

---

## 0. Status legend

| status | meaning |
|---|---|
| **resolved** | the defect is corrected in the version `2.0.0` artifacts, and the correction is stated in a frozen file |
| **resolved (choice)** | the defect was an undefined choice; version `2.0.0` freezes an explicit choice and reports a non-decision sensitivity where one is possible |
| **open — process** | not a defect in the artifacts, but a step that has not been performed (for example, a fresh independent audit) |

All four critical, all thirteen major, and all eleven minor Stage 2F findings are **resolved** in the
sense above. "Resolved" means corrected and documented; it does **not** mean the corrected freeze has
passed an independent audit.

---

## 1. Summary

| severity | ids | count | resolved | open |
|---|---|---:|---:|---:|
| critical | C1, C2, C3, C4 | 4 | 4 | 0 |
| major | M1–M13 | 13 | 13 | 0 |
| minor | m1–m11 | 11 | 11 | 0 |
| process | fresh v2 independent audit | 1 | 0 | 1 |

The Stage 2F decision was **FAIL — census not authorized**. Version `2.0.0` does not overturn that
decision; it supplies a remediated freeze for a future audit. The census remains unauthorized until a
fresh independent audit of version `2.0.0` returns a pass (or an explicitly approved conditional pass
with no critical finding and no material major ambiguity).

---

## 2. Critical findings

### 2.1 C1 — Candidate D used future session bars to decide a first-two-hour signal

| field | content |
|---|---|
| **defect** | D required all 32 session bars to be usable before a signal at the end of `b7` could exist. Bars `b8..b31` open after the signal instant, so the signal set was selected by future data. |
| **affected artifacts** | D spec §2.2; D config `bar_rules` / `sessions`; shared protocol §1.4 |
| **correction** | Signal eligibility now depends only on the measurement window `b0..b7`. A session is `signal-evaluable` iff those eight bars are usable and exactly 15 minutes apart. The 32-bar check is renamed `session_full_data` and is a **post-count diagnostic only**; it cannot remove, defer, or relabel a signal. Config sets `session_full_data_is_selector: false` and `full_session_is_post_count_diagnostic: true`. |
| **evidence** | D spec §2.2; D spec §10 (S2, `session_full_data`); D spec §11 item 2; D config `bar_rules.measurement_window_bars: 8`, `bar_rules.session_full_bars_diagnostic: 32`, `bar_rules.session_full_data_is_selector: false`; protocol §1.4 |
| **status** | **resolved** |

### 2.2 C2 — The primary median-cost verdict condition was vacuous in both candidates

| field | content |
|---|---|
| **defect** | The verdict median was computed over the post-gate population (`cost_R <= 0.20`), so `M <= 0.20` was true by construction and `M > 0.20` could never fail the design. |
| **affected artifacts** | B spec §9.1, §11.1; D spec §10.1, §12; shared protocol §2, §3, §4, §6; both configs `costs` and `verdict_thresholds` |
| **correction** | The verdict median is `M_all`, computed over the **pre-gate valid-entry/stop population** (B `S7`, D `S6`). The post-gate median `M_feasible` (B `S8`, D `S7`) is reported separately as a bounded diagnostic and cannot satisfy or fail the cost condition. If the pre-gate population is empty, `M_all` is undefined and the census is `INCONCLUSIVE`. Every cost statistic is labelled with its population. Proposed economic thresholds are also defined on `M_all`. |
| **evidence** | B spec §9.1 ("Cost-median populations"), §11.1; D spec §10.1 ("Cost-median populations"), §12; protocol §2 (third-denominator rule), §3 ("Cost populations are never mixed"), §4, §6.2; B config `costs.median_population_verdict: "S7 pre-gate valid entry/stop"`, `costs.empty_population_policy`; D config `costs.median_population_verdict: "S6 pre-gate valid entry/stop"` |
| **status** | **resolved** |

### 2.3 C3 — The development-boundary string comparison could read validation data

| field | content |
|---|---|
| **defect** | Row selection compared `open_time` as an ISO string against `2024-07-01T00:00:00+00:00`. The dataset stores a space separator (`"YYYY-MM-DD HH:MM:SS+00:00"`), so lexicographic comparison is not a reliable instant comparison and can admit or reject the wrong boundary rows. |
| **affected artifacts** | B spec §1; D spec §1; shared protocol §1.2; both configs `data` |
| **correction** | All filtering uses **integer UTC epoch milliseconds** after parsing to an aware UTC datetime. Half-open interval: `dev_start_ms = 1609459200000` included, `dev_end_ms = 1719792000000` excluded. The run asserts `min(open_time_ms) >= dev_start_ms` and `max(open_time_ms) < dev_end_ms` before counting. Symbolic boundary examples are in the protocol; configs carry `dev_start_ms`, `dev_end_ms`, `interval_semantics`, `timestamp_normalization`, and both assertions. |
| **evidence** | Protocol §1.2 and its boundary table; B spec §1 ("canonical integer UTC epoch millisecond"), D spec §1; B config `data.dev_start_ms` / `dev_end_ms` / `assert_*`; D config same |
| **status** | **resolved** |

### 2.4 C4 — Strict causality conflicted with the inclusive 1h ATR and percentile rule

| field | content |
|---|---|
| **defect** | Protocol §1.5 required indicator inputs to close **strictly before** the decision instant, but D's `q` bar closes exactly at the signal instant and was required to be used, and the percentile window was inclusive of the current 4h bar. The two rules could not both hold. |
| **affected artifacts** | Protocol §1.5; B spec §2/§5.5; D spec §4.2; both configs |
| **correction** | One availability rule: a candle is available at decision instant `T` iff `close_time_ms <= T`. Same-bar-close equality is explicitly permitted. The next executable bar's open is used for entry. The percentile window is inclusive because its right-edge 4h bar is closed and therefore available, not because of a different operator. A symbolic table covers the D `q` equality case. |
| **evidence** | Protocol §1.5 and its boundary table; B spec §2 (candle availability); D spec §4.2 (explicit `close_time_ms[q] == T`); configs `candle_availability.same_bar_close_equality_allowed: true` |
| **status** | **resolved** |

---

## 3. Major findings

### 3.1 M1–M4

| id | defect | affected artifacts | correction | evidence | status |
|---|---|---|---|---|---|
| **M1** | The 4h ATR construction was undefined in both candidates (first TR, seed, recursion, segment reset, missing-bar handling). | Protocol; B spec §3.1/§4.2; D spec §6.2; both configs `atr_4h` | Added shared protocol §1.7: first TR `high-low`, seed = mean of first 14 TRs, recursion `(ATR[t-1]*13 + TR[t])/14`, defined from local index 13, segment reset on missing/unusable bar, no interpolation, supplied 4h bars only, 540-value window admitted only if all defined. Restated in both specs and mirrored in configs. | Protocol §1.7; B spec §3.1, §4.2; D spec §6.2; configs `atr_4h` | **resolved** |
| **M2** | Entry-bar validity was applied ex post: `is_closed`, volume, `trade_count`, partial-bucket status were checked at entry, although only the open is knowable when the entry executes. A future property could remove an executable signal. | B spec §5.5; D spec §7.1; both configs `entry` | Entry validation uses only open-time-known properties: bar present, on grid, positive open, prior confirmation fixed, entry open before `dev_end_ms`. Close-time properties (`unclosed_entry_bar`, `zero_volume_entry`, `partial_entry_bar`, `invalid_entry_ohlc`) are post-count diagnostics and cannot remove a signal. | B spec §5.5; D spec §7.1; protocol §1.5; configs `entry.validate_only_open_time_known_properties: true` | **resolved** |
| **M3** | The protocol's partial-bucket rule contradicted both specs at 4h: 4h needs 48 5m members, but the specs retained gap-adjacent 4h bars as supplied. | Protocol §1.3; B spec §2.3; D spec §2.3; both configs `four_hour_supplied_bar_exemption` | Added an explicit shared 4h supplied-bar exemption from the 5m membership check. The twelve gap-adjacent buckets are retained as supplied; the run reports the count and computes a **non-decision sensitivity** that excludes them and segment-breaks the 4h ATR. The sensitivity cannot change the primary signal set, verdict, or denominators. | Protocol §1.3; B spec §2.3; D spec §2.3; configs `four_hour_supplied_bar_exemption` | **resolved (choice)** |
| **M4** | The alignment check was not executable on gap-affected buckets; comparing partial aggregates against full-bucket denominators would force `INCONCLUSIVE` by construction. | Protocol §1.6 | Gap-aware alignment: classify every bucket complete or gap-affected; compare only complete buckets; report gap-affected buckets separately with missing-member counts; apply the 0.1% tolerance to complete buckets only; report complete, gap-affected, and mismatch counts. The twelve known 4h partial buckets are excluded from the 4h-from-1h denominator and reported separately. | Protocol §1.6 | **resolved** |

### 3.2 M5–M8

| id | defect | affected artifacts | correction | evidence | status |
|---|---|---|---|---|---|
| **M5** | Candidate B did not reject an entry bar opening at or after the development end; a `2024-06-30T23:00` confirmation would select an entry at `2024-07-01T00:00`, outside the interval. | B spec §5.5; D spec §7.1; both configs `entry` | Added an explicit interval-end guard. Any entry that would open at or after `dev_end_ms` is rejected with `entry_outside_interval`; it is not skipped forward and not completed from a validation bar. The same guard applies to any bar the signal would need at or after the boundary. | B spec §5.5 ("Development-end guard"); D spec §7.1; protocol §1.2 ("Events that would need a bar outside the interval"); configs `entry.reject_if_entry_open_time_at_or_after_dev_end: true` | **resolved** |
| **M6** | Candidate D's 1h ATR warm-up was off by one: `ATR1h[13]` is the first defined value, but the spec excluded the first 14 bars (local `0..13`). | D spec §4.2; D config `atr_1h` / `warmup` | Warm-up corrected to local indices `0..12` (13 bars). A `q` at local index 13 or later is testable. Config records `first_defined_local_index: 13`, `warmup_local_indices: [0, 12]`, `first_testable_local_index: 13`, `warmup_bars_per_segment: 13`. | D spec §4.2 ("Warm-up (M6)"); D config `atr_1h`, `warmup`; protocol §1.4 | **resolved** |
| **M7** | Candidate B's `Unknown` regime label contradicted its own exclusion table: `Unknown` at `e` was grouped with `False` even though the table had a separate `warmup_regime` label. | B spec §4.3, §9; B config `regime_4h` / pipeline | `Unknown` at `e` is now `warmup_regime`; `False` at `e` is `regime_not_permitted`. At `c`, `Unknown` or `False` is `regime_lost`. The config records the same mapping. | B spec §4.3; B spec §9 exclusion table; B config `regime_4h.evaluation_points`, pipeline | **resolved** |
| **M8** | Candidate B's S4/S5 episode-start definition was contradictory: S4 "episodes started" and S5 "regime-qualified" did not state whether regime failures at `e` were attempted. | B spec §9, §9.1; B config `pipeline` / `denominators` | S4 is now **episode attempts**: the first non-absorbed expansion bar that opens an attempt, including those that fail the regime at `e`. S5 is the subset with `permission == True` at `e`. `permission_share = S5/S4` is therefore a real share with a non-zero denominator. | B spec §9 ("Stage labels are explicit (M8, M9)"), §9.1; B config `pipeline` | **resolved** |
| **M9** | Candidate B assigned `regime_lost` to the "structurally valid" stage, mixing a confirmation-time regime check into S6. | B spec §9, §9.1; B config `pipeline` | S6 is structural only (retest touch + resumption), **before** the regime-at-`c` check. S7 applies the confirmation regime plus entry/stop validity. `regime_lost` is an S7 rejection. `signal_validity_share = S7/S6` is auditable, and S7 is the pre-gate population used by C2. | B spec §9, §9.1; B config `pipeline` | **resolved** |

### 3.3 M10–M13

| id | defect | affected artifacts | correction | evidence | status |
|---|---|---|---|---|---|
| **M10** | Capital-geometry units were undefined (`risk_usd / stop_pct` mixed a fraction and a percent) and the impracticability threshold was qualitative ("makes the design impracticable"). | Protocol §5; B spec §10 item 10; D spec §11 item 11; both configs `capital` | Defined `stop_fraction = D / entry_open` (dimensionless), `notional_usd = risk_usd / stop_fraction`, `notional_pct = notional_usd / equity_usd`. The numeric impracticability condition is `notional_pct > 1.00` for any signal; equality is fundable. Worked examples state whether they display the fraction or the percent. | Protocol §5; B spec §10 item 10 and §10.1; D spec §11 item 11 and §11.1; configs `capital.stop_fraction_definition`, `notional_formula`, `impracticability_threshold` | **resolved** |
| **M11** | The Kish cluster unit was undefined ("signal-producing regime episode"), so two runners could derive different clusters from the same bars. | Protocol §3.1; B spec §10 items 7–8; D spec §11 items 8–9; both configs `clustering` | Clusters are **maximal runs of consecutive usable 4h bars** satisfying the regime predicate (B `permission == True`, D `budget_ok == True`). `False`, `Unknown`, missing, or unusable breaks the run. Clusters are a property of the regime series, not of the emitted signal set. The Kish formula and `rho` sensitivity are fixed. | Protocol §3.1; B spec §10; D spec §11; configs `clustering.primary_view`, `cluster_boundary` | **resolved** |
| **M12** | The freeze record claimed "zero critical ambiguities", which was false, and the manifest did not carry forward the known-issue list. | Protocol §7; freeze manifest | Version `2.0.0` makes **no zero-critical claim**. The manifest records one resolution entry per Stage 2F finding and states that remediation is complete but a fresh independent audit has not been performed. | Protocol §7; `FREEZE_MANIFEST.json` `finding_resolutions`, `no_zero_critical_claim` | **resolved** |
| **M13** | The freeze manifest recorded a git HEAD that predated the manifest itself, so the recorded commit did not contain the manifest. | Protocol §7; freeze manifest | The manifest records `artifact_commit` (the commit that froze the remediated artifacts) and a canonical-JSON `self_hash` computed with the `self_hash` field removed; it also records `manifest_commit` (the commit that introduces the manifest). The manifest's integrity is given by `self_hash`, not by a self-referential commit field. | Protocol §7; `FREEZE_MANIFEST.json` `artifact_commit`, `manifest_commit`, `self_hash`, `self_hash_algorithm` | **resolved** |

---

## 4. Minor findings

| id | defect | affected artifacts | correction | evidence | status |
|---|---|---|---|---|---|
| **m1** | B S2 was "1h bars with ATR(14) defined" (`t >= 13`), but the expansion test consumes `ATR[t-1]`, so the first testable bar is `t = 14`. | B spec §9; B config `pipeline` | S2 is now "expansion-testable 1h bars: `ATR[t-1]` defined, local index `>= 14`". Config `atr_1h.first_expansion_testable_local_index: 14` and pipeline label `S2_expansion_testable_bars_atr_t_minus_1_defined`. | B spec §9; B config `atr_1h`, `pipeline` | **resolved** |
| **m2** | Markdown buckets were explicit but JSON buckets `[[null,0.10],[0.10,0.20],…]` did not state endpoint inclusion. | B spec §8; D spec §7.3; both configs `costs.buckets` | Both specs now give a table with `lower_inclusive` / `upper_inclusive`. Every config bucket carries explicit flags: upper endpoint belongs to the lower bucket; `(-inf, 0.10]`, `(0.10, 0.20]`, `(0.20, 0.30]`, `(0.30, 0.50]`, `(0.50, +inf)`. | B spec §8; D spec §7.3; configs `costs.buckets[].lower_inclusive` / `upper_inclusive` | **resolved** |
| **m3** | The dataset manifest recorded only `gap_count` / `gap_bars_total`, not gap start/end locations, so a runner could not verify gap-affected buckets from the frozen manifest alone. | Freeze manifest; protocol §1.6 | The version `2.0.0` freeze manifest records the seven 5m gap intervals, the derived missing 1h and 15m bars, and the twelve gap-adjacent 4h buckets under `dataset_identity.gap_locations`. | `FREEZE_MANIFEST.json` `dataset_identity.gap_locations`; protocol §1.6 | **resolved** |
| **m4** | D config `first_session_signal_after: 2021-04-03T00:00:00+00:00` was one 4h bar earlier than the first complete 540-value window. | D spec §5.2 (regime warm-up); D config `warmup` / `volatility_budget` | The boundary is now the first signal instant strictly after the close of 4h index 552: `2021-04-03T04:00:00Z`. Config records `first_eligible_signal_instant: "2021-04-03T04:00:00+00:00"` and D spec §6.2 states the same. | D spec §6.2 ("Warm-up and incomplete windows (m4)"); D config `volatility_budget.first_eligible_signal_instant`, `warmup.first_session_signal_at_or_after` | **resolved** |
| **m5** | Protocol §1.4 listed "32 usable 15m bars per session" as a warm-up exclusion, hiding a selection rule inside a warm-up allowance. | Protocol §1.4 | The 32-bar rule is removed from warm-up and carried only as the post-count `session_full_data` diagnostic. Warm-up now lists D's 13 1h bars and 552 4h bars only. | Protocol §1.4; D spec §2.2 | **resolved** |
| **m6** | B said an ATR-multiple sensitivity was permitted as a diagnostic, but none was declared, leaving an undeclared degree of freedom. | B spec §3.2, §7.4; B config `expansion` | The sentence is deleted. The ATR multiple is fixed at `2.0`; no ATR-multiple sensitivity is declared or permitted. Config `expansion.atr_multiple_tunable: false`, `single_primary_definition: true`. | B spec §3.2; B config `expansion` | **resolved** |
| **m7** | B config carried `cooldown_primary_hours: 0` beside `canonical_hours: 72`; a runner reading the former would apply no spacing. | B spec §7.3–§7.4; B config `overlap` | `cooldown_primary_hours` is removed. `canonical_hours: 72` is the single source of truth. The term "cooldown" is removed; the rule is named "non-overlap spacing on accepted entry times". | B spec §7.3, §7.4; B config `overlap` | **resolved** |
| **m8** | D's `session_completeness` denominator ("all session buckets in the interval after warm-up") was undefined. | D spec §10.1; D config `denominators` | The denominator is now the concrete `S0`: all session buckets whose signal instant lies in `[dev_start_ms, dev_end_ms)`. Warm-up exclusions are counted separately at S3/S4. The `session_full_data` diagnostic is reported against `S0`. | D spec §10.1; D config `denominators.session_completeness` | **resolved** |
| **m9** | D's `q` selection ("last 1h bar whose `close_time <=` signal instant") silently fell back to an earlier bar if the expected `01:00` / `09:00` / `17:00` bar was missing. | D spec §4.2; D config `signal` | `q` is the **expected** 1h bar opening at `session_start + 1h`, admissible by close-time equality. If it is missing, unclosed, off-grid, zero-volume, or unusable, the session is rejected with `stop_atr_unavailable`; there is no fallback. | D spec §4.2; D config `signal.q_selection`, `q_missing_or_unusable_label` | **resolved** |
| **m10** | The dataset stores `is_closed` as the string `"True"` and prices/volumes/counts as strings; a raw-JSON runner would mark every bar unusable. | Protocol §1.1 | The protocol now requires a typed loader (repository `CandleData` or equivalent) that coerces `is_closed` to boolean and numeric fields to numbers before any rule, plus a fixture test on the actual on-disk representation. An uncoercible record aborts as `schema_error`. | Protocol §1.1 ("Typed loader (m10)") | **resolved** |
| **m11** | B's `regime_blip` diagnostic was not computable: "transient failure between `e` and `c`" did not define an evaluation grid, inclusion of endpoints, or multi-bar counting. | B spec §4.3; B config `regime_4h` | `regime_blip` is removed entirely. Permission is evaluated only at `e` and `c`; no intermediate evaluation is defined or reported. Config `intermediate_regime_evaluation: false`, `regime_blip_diagnostic: false`. | B spec §4.3; B config `regime_4h` | **resolved** |

---

## 5. Definition-changing decisions

These are the only changes that can change the set of signals, the verdict, or a reported number. None
was selected by looking at historical outcomes.

| # | decision | previous | version `2.0.0` | finding |
|---|---|---|---|---|
| D1 | D signal eligibility window | all 32 session bars | `b0..b7` only; 32-bar completeness is a diagnostic | C1 |
| D2 | Verdict median population | post-gate (B S8, D S7) | pre-gate (B S7, D S6), symbol `M_all` | C2 |
| D3 | Interval filtering | lexicographic ISO string | integer epoch ms, half-open `[start, end)` | C3 |
| D4 | Candle availability | strict `<` in one place, inclusive in another | `close_time_ms <= T` everywhere; equality allowed | C4 |
| D5 | 4h ATR | unspecified | shared §1.7 construction, segment reset | M1 |
| D6 | Entry validation | any entry-bar property | open-time-known properties only | M2 |
| D7 | 4h gap-adjacent buckets | ambiguous | explicit supplied-bar exemption plus non-decision sensitivity | M3 |
| D8 | Alignment denominator | full calendar count | complete buckets only, gap-affected reported separately | M4 |
| D9 | Development-end entry | not guarded | `entry_outside_interval` rejection | M5 |
| D10 | D 1h ATR warm-up | first 14 bars | first 13 bars (local `0..12`) | M6 |
| D11 | B regime labels at `e` | `Unknown` grouped with `False` | `warmup_regime` vs `regime_not_permitted` | M7 |
| D12 | B S4/S5 semantics | ambiguous | S4 episode attempts, S5 regime-qualified | M8 |
| D13 | B S6/S7 semantics | `regime_lost` at S6 | S6 structural, S7 confirmation regime + entry/stop | M9 |
| D14 | Capital units | `risk_usd / stop_pct` | `risk_usd / stop_fraction`; numeric `notional_pct > 1.00` | M10 |
| D15 | Kish cluster | signal-producing episode | maximal regime run, independent of signals | M11 |
| D16 | ATR-multiple sensitivity | ambiguously permitted | none permitted; ATR multiple fixed | m6 |
| D17 | B cooldown key | `cooldown_primary_hours: 0` | removed; `canonical_hours` only | m7 |
| D18 | D completeness denominator | "after warm-up" | concrete `S0` session population | m8 |
| D19 | D missing `q` bar | silent earlier-bar fallback | `stop_atr_unavailable` rejection | m9 |
| D20 | `regime_blip` diagnostic | undefined | removed | m11 |

No cost assumption, instrument, market, direction, dataset, development interval, leverage choice, or
signal parameter (ATR multiple, retest tolerance, confirmation window, percentile band, VWAP rule,
session boundaries, non-overlap canonical horizon) was changed.

---

## 6. Parameters added or renamed

### 6.1 Added (with actual values)

| artifact | key | value |
|---|---|---|
| B/D config | `data.dev_start_ms` | `1609459200000` |
| B/D config | `data.dev_end_ms` | `1719792000000` |
| B/D config | `data.interval_semantics` | half-open on `open_time_ms`; start included, end excluded |
| B/D config | `data.timestamp_normalization` | parse aware UTC, convert to integer epoch ms, never lexicographic |
| B/D config | `candle_availability.rule` | `close_time_ms <= T` |
| B/D config | `candle_availability.same_bar_close_equality_allowed` | `true` |
| B config | `atr_1h.first_expansion_testable_local_index` | `14` |
| D config | `atr_1h.first_defined_local_index` | `13` |
| D config | `atr_1h.warmup_local_indices` | `[0, 12]` |
| D config | `atr_1h.first_testable_local_index` | `13` |
| B/D config | `atr_4h` block | period 14, Wilder, segment-scoped, first defined at 13 |
| B/D config | `bar_rules.four_hour_supplied_bar_exemption` | enabled; expected 12 buckets; non-decision sensitivity |
| B config | `regime_4h.intermediate_regime_evaluation` | `false` |
| B config | `regime_4h.regime_blip_diagnostic` | `false` |
| B/D config | `entry.validate_only_open_time_known_properties` | `true` |
| B/D config | `entry.close_time_diagnostics` | four named diagnostics |
| B/D config | `costs.median_population_verdict` | B `S7`, D `S6` |
| B/D config | `costs.median_population_diagnostic` | B `S8`, D `S7` |
| B/D config | `costs.empty_population_policy` | `M_all` undefined => `INCONCLUSIVE` |
| B/D config | `verdict_thresholds.median_symbol` | `M_all` |
| B/D config | `capital.stop_fraction_definition` | `D / entry_open` (dimensionless) |
| B/D config | `capital.notional_formula` | `risk_usd / stop_fraction` |
| B/D config | `capital.notional_pct_formula` | `notional_usd / equity_usd` |
| B/D config | `capital.impracticability_threshold` | any signal with `notional_pct > 1.00` |
| B/D config | `clustering.cluster_boundary` | `False`/`Unknown`/missing/unusable breaks the run |
| D config | `denominators.session_completeness` | `S2/S0` with `S0` defined concretely |
| D config | `volatility_budget.first_eligible_signal_instant` | `2021-04-03T04:00:00+00:00` |
| D config | `signal.q_missing_or_unusable_label` | `stop_atr_unavailable` |

### 6.2 Renamed or removed

| previous | version `2.0.0` | reason |
|---|---|---|
| `stop_pct` | `stop_fraction` | M10 units |
| `cooldown_primary_hours` | **removed**; `canonical_hours` only | m7 |
| "cooldown" wording | "non-overlap spacing on accepted entry times" | m7 |
| `entry_validity_share` (B) | `signal_validity_share` | M9 |
| `M` (single median) | `M_all` (verdict) and `M_feasible` (diagnostic) | C2 |
| "signal-producing 4h regime episode" | "Kish cluster" (maximal regime run) | M11 |
| B S2 "ATR(14) defined" | "`ATR[t-1]` defined, local index `>= 14`" | m1 |
| D S2 "evaluable sessions" | "signal-evaluable sessions (`b0..b7`)" | C1 |
| `session_data_incomplete` | `measurement_window_incomplete` plus `session_full_data` diagnostic | C1 |
| `first_session_signal_after` | `first_eligible_signal_instant` | m4 |
| `regime_blip` | **removed** | m11 |
| B "first 14 bars" ATR warm-up | "14 bars per segment; `ATR[t-1]` first defined at local index 14" | m1 clarification |

---

## 7. Cross-candidate consistency

The two candidates now share every element that the audit found divergent or ambiguous.

| element | B | D | consistent? |
|---|---|---|---|
| protocol version | `2.0.0` | `2.0.0` | yes |
| interval representation | integer epoch ms, half-open | integer epoch ms, half-open | yes |
| development interval | `[1609459200000, 1719792000000)` | same | yes |
| candle availability | `close_time_ms <= T` | same | yes |
| shared 4h ATR | protocol §1.7 | protocol §1.7 | yes |
| 4h supplied-bar exemption | explicit, sensitivity | explicit, sensitivity | yes |
| gap-aware alignment | complete buckets only | complete buckets only | yes |
| entry validation | open-time-known only | open-time-known only | yes |
| development-end guard | `entry_outside_interval` | `entry_outside_interval` | yes |
| verdict median population | `S7` pre-gate | `S6` pre-gate | yes, mapped by pipeline |
| post-gate median | `S8` `M_feasible` | `S7` `M_feasible` | yes, mapped by pipeline |
| empty pre-gate population | `INCONCLUSIVE` | `INCONCLUSIVE` | yes |
| Kish cluster | maximal `permission == True` run | maximal `budget_ok == True` run | yes, predicate differs by design |
| capital units | `stop_fraction = D / entry_open` | same | yes |
| impracticability | `notional_pct > 1.00` | same | yes |
| non-overlap wording | spacing, not cooldown | spacing, not cooldown | yes |
| prohibited outputs | identical list | identical list | yes |

Deliberate differences that are **not** inconsistencies: B is long-only 1h execution with a 4h regime
filter, retest, and 72h non-overlap; D is long-only 15m execution with a 4h volatility budget, session
VWAP, and 24h non-overlap. Their pre-gate stages are B S7 and D S6 because B has an extra
confirmation-regime stage; the protocol maps both.

---

## 8. Symbolic causality and boundary walkthroughs

All examples use invented numbers. No historical row is read.

### 8.1 C1 — D signal at `b7` must not depend on `b8..b31`

Take an ASIA session opening `2021-06-01T00:00:00Z`. Measurement bars `b0..b7` open at
`00:00, 00:15, …, 01:45`; `b7` closes at `01:59:59.999`. The signal uses only those eight closes and
the session VWAP over them. Suppose `b8..b31` are all missing. The session is still
**signal-evaluable**: on the invented numbers `r2 = 2.0%`, `thr = 1.6%`, `P1 > VWAP`, `budget_ok`, so a
signal exists at `01:59:59.999`. The run then records `session_full_data = false` as a diagnostic and
does not remove the signal. Reading `b8` or later would be a causality failure (`INCONCLUSIVE`).

### 8.2 C3 — interval boundary at the development end

| row | `open_time_ms` | admitted? | consequence |
|---|---:|---|---|
| `2024-06-30 23:00:00+00:00` | `1719791999999` | yes (`< 1719792000000`) | may be the confirmation bar |
| its entry bar would open `2024-07-01 00:00:00+00:00` | `1719792000000` | no | signal rejected as `entry_outside_interval` |
| `2024-07-01 00:00:00+00:00` | `1719792000000` | no | never read |

The signal is neither silently dropped nor completed from a validation bar.

### 8.3 C4 — D `q` bar closes exactly at the signal instant

At ASIA, `q` opens `01:00:00` and closes `01:59:59.999`, which equals the signal instant `T`. Under
the availability rule `close_time_ms <= T`, `q` is available and `ATR1h[q]` may be used. Entry is at
the open of `b8`, `02:00:00`, strictly after `T`. If `q` is missing, the session is rejected as
`stop_atr_unavailable`; the run does not read the `00:00` bar as a fallback.

### 8.4 M1 — shared ATR arithmetic

If `TR[0..13] = 2.0`, then `ATR[13] = 2.0`. If `TR[14] = 4.5`, then
`ATR[14] = (2.0 × 13 + 4.5) / 14 = 2.178571`. A missing bar after index 14 ends the segment; the next
segment starts again with `TR = high - low` and a fresh 14-bar seed.

### 8.5 M4 — gap-aware alignment

Suppose a 4h bucket has only three of its four 1h members because of a registered 1h gap. The bucket is
classified **gap-affected**, not compared against a full four-bar aggregate, and excluded from the
4h-from-1h tolerance denominator. The run reports it with a missing-member count of one. The twelve
known gap-adjacent 4h buckets are handled the same way and are additionally reported under the §1.3
supplied-bar exemption.

### 8.6 M5 — B entry at the development end

If B's confirmation bar `c` is the `2024-06-30T23:00` bar, the nominal entry bar opens
`2024-07-01T00:00`. The guard rejects the signal as `entry_outside_interval` before any price is read.
The count of such rejections is reported.

### 8.7 M10 — capital geometry units

If `D = 4.5` and `entry_open = 104.0`, then `stop_fraction = 4.5 / 104.0 = 0.043269` (4.3269%).
At `risk_usd = 100`, `notional_usd = 100 / 0.043269 = 2,311.11` and
`notional_pct = 2,311.11 / 10,000 = 0.2311`, which is below `1.00` and therefore fundable at this
equity. Writing `100 / 4.3269` would be wrong by a factor of 100. For D's worked example,
`stop_fraction = 1000 / 30610 = 0.032669`, `notional_usd = 3,060.99`, `notional_pct = 0.3061`.

### 8.8 M11 — Kish cluster boundary

If 4h `permission` is `[True, True, False, True, Unknown, True]`, the clusters are the runs `{1,2}`,
`{4}`, and `{6}`. The `False` at position 3 and the `Unknown` at position 5 each break the run. A
missing 4h bar would break it as well. Only runs with at least one emitted signal contribute to the
Kish numerator; signal-free runs still exist as clusters but have `n_k = 0`.

---

## 9. Remaining unresolved issues and limitations

These are stated so that a fresh auditor does not have to rediscover them. None is a secret; none is
claimed closed.

1. **No independent audit of version `2.0.0` has been performed.** This matrix and the accompanying
   review are a remediation and a self-review, not an independent pass. The census remains
   unauthorized until a fresh audit of the new freeze returns a pass or an approved conditional pass.
2. **Proposed economic thresholds still require approval.** B's `F >= 0.25` / `M_all <= 0.12` and D's
   `F >= 0.30` / `M_all <= 0.17` / `E >= 0.02` are marked proposed, not part of the primary verdict.
   They must be approved and frozen in a new version before counting if they are to be used.
3. **The 4h supplied-bar exemption is a deliberate choice.** Retaining the twelve gap-adjacent 4h
   buckets is defensible because the vendor close is a real last-trade price and the regime filter is
   slow, but an auditor may still prefer the excluded variant. The non-decision sensitivity is
   reported so the choice is visible; it cannot change the primary result.
4. **Venue facts remain unknown.** Binance-proxy cost of 26 bp is not a verified Nobitex execution
   cost. Margin, fee tiers, and settlement rules are not invented. The census does not claim
   executable economics.
5. **`session_full_data` may be unavailable for some sessions** if late session bars are absent. It is
   then reported as false/unknown and still cannot remove a signal. This is a diagnostic-coverage
   limitation, not a selection rule.
6. **Dataset hashes are copied from `backend/data/datasets/manifest.json`.** They must be recomputed
   and checked at census time; this document and the manifest do not re-read the datasets.
7. **The manifest cannot contain its own final commit hash in a single commit.** Integrity is provided
   by `self_hash` over canonical JSON; `artifact_commit` and `manifest_commit` are provenance
   pointers. A verifier should recompute `self_hash` and compare it to the file on disk.
8. **Gap locations are transcribed from the Stage 2A audit.** If the dataset file were regenerated,
   the frozen manifest would need a new version; the current hashes pin the file that was audited.

---

## 10. No-data and no-census statement

- No historical dataset row was read to produce this matrix.
- No signal was counted, enumerated, or listed.
- No B or D census was run.
- No backtest, P&L, return, expectancy, win rate, drawdown, Sharpe, CAGR, equity curve, portfolio
  simulation, bootstrap, Monte Carlo, or parameter optimisation was performed.
- No validation or out-of-sample row was read or used.
- No Stage 2E version `1.0.0` artifact, Stage 2F audit, Stage 2A/2B/2C/2D artifact, Stage 6/6A
  artifact, or Setup 1 artifact was modified by Stage 2G.
