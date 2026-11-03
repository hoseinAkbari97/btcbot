# Stage 2F — Independent Freeze Audit: Candidates B and D

**Audit date:** 2026-11-03
**Auditor:** Independent Stage 2F pass
**Scope:** the frozen Candidate B and Candidate D specifications, their JSON configurations, the shared census protocol, the freeze manifest, and the dataset identity metadata recorded by Stage 2E.
**Method:** adversarial documentation and repository audit. No census was run, no signal was counted, no backtest or performance calculation was performed, and no parameter was optimized.

**Decision: FAIL — the Stage 2E freeze is not authorized for a census.**

> Hash integrity passes. The frozen decision rules do not.

---

## 0. Decision

The six documented Stage 2E files and the four dataset files are byte-identical to the hashes recorded in `STAGE2E_FREEZE_MANIFEST.json` and `backend/data/datasets/manifest.json`. That is the only part of the freeze that passes cleanly.

The audit finds **four critical defects**, **thirteen major defects**, and **eleven minor defects**. The critical defects are not documentation nits: one introduces look-ahead selection into Candidate D, one makes the primary cost condition of both candidates logically unable to fail, one can silently include validation data at the development boundary, and one makes the protocol's causality check unsatisfiable as written.

| id | severity | short finding |
|---|---|---|
| **C1** | critical | D requires all 32 session bars through `s+8h` before emitting a signal whose signal instant is `s+2h`; bars `b8..b31` are future data. |
| **C2** | critical | Both candidates compute the verdict median `M` over the post-gate cost-feasible population, so `M > 0.20` is impossible and `M <= 0.20` is always true. |
| **C3** | critical | The frozen "ISO-string comparison" uses `T`-separated bounds while the dataset stores space-separated timestamps; a literal comparison excludes 2021-01-01 and includes 2024-07-01 validation rows. |
| **C4** | critical | Protocol §1.5 #1 requires indicator inputs with `close_time` strictly less than the decision instant, but D uses a 1h bar that closes exactly at the signal instant; protocol §1.5 #5 simultaneously requires an inclusive window. |

A freeze with any unresolved critical defect cannot be authorized. The decision is therefore **FAIL**, not "conditional pass" and not "pass with limitations." No Stage 2G work, census, backtest, or outcome computation is authorized by this audit.

The correct remedy is a **new versioned freeze** after explicit approval, not an in-place edit of any Stage 2E artifact. Section 9 lists the minimum remediation set.

---

## 1. Repository and freeze identity

### 1.1 Git state

| item | observed | expected | status |
|---|---|---|---|
| branch | `main` | `main` | pass |
| HEAD | `6f8db24a4cdb3b41d1a485517911acf4b166bd68` | `6f8db24a4cdb3b41d1a485517911acf4b166bd68` | pass |
| `origin/main` | `6f8db24a4cdb3b41d1a485517911acf4b166bd68` | equal to HEAD | pass |
| working tree | clean | clean | pass |
| commits since `845078a` | 15 | 15 | pass |
| HEAD commit content | adds only `docs/research/STAGE2E_FREEZE_MANIFEST.json` (+198 lines) | manifest-only freeze commit | pass |

The Stage 2E series is a clean, linear sequence. The freeze manifest is the last commit in the series (`6f8db24`), whose parent is the independent-review commit (`f8000e0`).

The table records the repository state observed at the start of the audit. The audit commit adds only this report on top of `6f8db24`, so HEAD after publication is the audit commit, not the freeze target. The hash comparison in §1.2 is against the files as they existed at `6f8db24` and is unaffected by the publication commit. The "commits since `845078a`" count likewise refers to the pre-audit state.

### 1.2 Document hashes

Recomputed with `sha256sum` against the values in `STAGE2E_FREEZE_MANIFEST.json`:

| document | recorded SHA256 | recomputed SHA256 | status |
|---|---|---|---|
| `STAGE2E_CANDIDATE_B_SPEC.md` | `13762985a31ecb3364c4fd7c2c66d1bafdc627d526177fbdb04601ef619c3104` | same | pass |
| `STAGE2E_CANDIDATE_B_CONFIG.json` | `4253b32b4305434fec196c6e9c720c144b4572a109958d4bd5f1125f78086574` | same | pass |
| `STAGE2E_CANDIDATE_D_SPEC.md` | `49668b4ff377c913a6c70027813bbbd0b39d57b7eaa94954130e32319a7e7277` | same | pass |
| `STAGE2E_CANDIDATE_D_CONFIG.json` | `97dee773afe996dd179f015b9c787db4a5bd578ffaeb6881f5808c5fc92c6765` | same | pass |
| `STAGE2E_SHARED_CENSUS_PROTOCOL.md` | `3afd1e915b3ce27966673d30d25ea59763192b5869e8857712668ec94a7f1f78` | same | pass |
| `STAGE2E_INDEPENDENT_REVIEW.md` | `3f59a8c2365676fc15b8a069e78600776aa4ecd1a176d3245ca9f1f2c6738cc9` | same | pass |

The manifest itself has SHA256 `b26ef6d56665908aaf74e72e56aff0a6f36fab2a682b5de7926d5fc3385eac65`. It is not recorded inside the manifest (the manifest's closing note says so explicitly; see `STAGE2E_FREEZE_MANIFEST.json` line 197). That is a provenance gap, discussed as major finding **M13**.

### 1.3 Dataset identity

Recomputed with `sha256sum` against `backend/data/datasets/manifest.json` and the freeze manifest:

| timeframe | recorded SHA256 | recomputed SHA256 | status |
|---|---|---|---|
| 15m | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | same | pass |
| 1h | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | same | pass |
| 4h | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | same | pass |
| 5m | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | same | pass |
| dataset manifest | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | same | pass |

Dataset metadata agrees between the dataset manifest and the freeze manifest:

| timeframe | bars | expected | gap_count | gap_bars_total |
|---|---:|---:|---:|---:|
| 15m | 198,554 | 198,624 | 7 | 70 |
| 1h | 49,642 | 49,656 | 7 | 14 |
| 4h | 12,414 | 12,414 | 0 | 0 |
| 5m | 595,659 | 595,872 | 7 | 213 |

The development-interval row counts used later in this audit are derived from the calendar interval, not from a census: 1,277 days gives 7,662 expected 4h bars, 30,648 expected 1h bars, and 122,592 expected 15m bars. The 4h series is the only one registered gap-free.

### 1.4 Freeze metadata

| item | recorded | audit |
|---|---|---|
| protocol version | `1.0.0` | matches both configs |
| specification versions | B `1.0.0`, D `1.0.0` | matches both configs |
| development interval | `[2021-01-01T00:00:00+00:00, 2024-07-01T00:00:00+00:00)` | matches both configs and protocol |
| development days / years | 1,277 / 3.496 | arithmetically correct (`1277/365.25 = 3.496`) |
| round-trip cost | 26 bp, fraction `0.0026` | matches both configs and protocol |
| cost gate | `cost_R <= 0.20` | matches both configs and protocol |
| implied minimum stop | 1.30% | algebraically correct at 26 bp |
| freeze timestamp | `2026-11-02T08:40:03Z` | recorded |
| `git_head_at_freeze` | `f8000e042c5b1238312317bd4decefae4f1c4438` | does **not** contain the manifest commit `6f8db24`; see **M13** |
| `unresolved_critical_ambiguities` | 0 | contradicted by this audit; see **M12** |
| pre-development data used | false | matches the specs' intent |
| validation/OOS accessed | false | matches the specs' intent, but see **C3** |

### 1.5 What hash equality proves

Hash equality proves that the files being audited are exactly the files Stage 2E froze. It does **not** prove that the frozen rules are internally consistent, causal, or implementable. The findings below are defects in the frozen content, not evidence of file substitution or tampering. A runner that verifies only hashes will pass the integrity check and then execute a defective rule set.

---

## 2. Specification-to-configuration comparison

### 2.1 Candidate B

| parameter group | Markdown source | JSON key(s) | value | status |
|---|---|---|---|---|
| stage / strategy / version | B header | `stage`, `strategy_id`, `spec_version` | `2E`, `CANDIDATE_B_VOLATILITY_EXPANSION_RETEST_CONTINUATION`, `1.0.0` | match |
| paths | B §1 | `data.paths` | 1h, 4h, 5m, manifest | match |
| development interval | B §0, §1 | `data.dev_start`, `data.dev_end`, `data.dev_days`, `data.dev_years` | 2021-01-01, 2024-07-01, 1277, 3.496 | match |
| timeframes | B §1 | `timeframes` | signal 1h, regime 4h, execution 1h, alignment 5m | match |
| bar usability | B §2.1 | `bar_rules` | closed, volume/trade count positive, 12-member bucket, valid OHLC, first duplicate, no synthesis | match |
| segment rule | B §2.2 | `bar_rules.segment_rule`, `segment_break_ends_episode` | consecutive 1h bars, gap ends episode | match |
| 1h ATR | B §3.1 | `atr_1h` | Wilder 14, segment-scoped, first TR `high-low`, mean of first 14, recursion, undefined before index 13 | match |
| expansion | B §3.2 | `expansion` | `ATR[t-1]`, 2.0, body/range 0.55, close location 0.75, close > open, `>=` | match |
| 4h regime formula | B §4.2 | `regime_4h` | SMA50, slope 6, ATR14, 540-bar percentile, band [20, 95], current bar included | match |
| 4h ATR construction | B §4.2 line 224 | `regime_4h.atr_period`, `atr_method` | period 14, Wilder, but no first-TR/seed/reset rule | **incomplete — M1** |
| 4h bar selection | B §4.1 | `regime_4h.bar_selection` | most recent 4h close strictly before the 1h open | match |
| retest | B §5.1–§5.4 | `retest` | close[e], ATR[e], 0.25, window 1..6, penetration 0.50, confirmation 3, same-bar false | match |
| entry | B §5.5 | `entry` | open of 1h bar at confirmation + 1h; reject missing/unclosed/zero/partial/non-positive | match (semantic issue **M2**) |
| stop | B §5.6 | `stop` | min low e..c, no floor, invalid if `S <= 0`, `entry <= 0`, `entry <= S` | match |
| episodes | B §6 | `episodes` | one active, absorb later expansions, failed retest no signal, key `B:{e}` | match |
| non-overlap | B §7 | `overlap` | 72h canonical, [24, 120], entry_time, inclusive, after cost gate | match; extra `cooldown_primary_hours: 0` — **m7** |
| costs | B §8 | `costs` | 26 bp, 0.0026, gate 0.20, implied min 1.30%, buckets, [10, 26, 39, 52] | match; bucket inclusivity ambiguous — **m2** |
| warm-up | B §3.1, §4.2 | `warmup` | 14 1h bars, 552 4h bars, no pre-dev, first 1h `2021-04-03T04:00:00Z` | match |
| clustering | B §10 items 7–8 | `clustering` | "signal-producing 4h permission episodes" | **undefined cluster unit — M11** |
| capital | B §10 item 10 | `capital` | $10,000, 1%, $100 risk, `risk_usd / stop_pct`, $5 minimum, `1e-5` lot | match (unit ambiguity **M10**) |
| power reference | B §0.1, §11.3 | `power_reference` | 0.15R, 1R, 5%, 80%, 349 | match |
| verdict | B §11.1 | `verdict_thresholds` | 150, 349, `max_median_cost_r 0.20`, proposed 0.25 / 0.12 | numeric match, **population defect C2** |
| pipeline | B §9 | `pipeline` | S1–S10 | match |
| denominators | B §9.1 | `denominators` | S3/S2, S5/S4, S6/S5, S7/S6, S8/S7, S9/S8, S10/S9 | numeric match; **m1, M8, M9** |
| reporting | B §10 | `reporting` | required and forbidden lists | match |
| confirmations | B §13 | `confirmations` | all false | match |

### 2.2 Candidate D

| parameter group | Markdown source | JSON key(s) | value | status |
|---|---|---|---|---|
| stage / strategy / version | D header | `stage`, `strategy_id`, `spec_version` | `2E`, `CANDIDATE_D_INTRADAY_CONTINUATION_VOL_BUDGET`, `1.0.0` | match |
| paths | D §1 | `data.paths` | 15m, 1h, 4h, 5m, manifest | match |
| development interval | D §0, §1 | `data.dev_start`, `data.dev_end`, `data.dev_days`, `data.dev_years` | 2021-01-01, 2024-07-01, 1277, 3.496 | match |
| timeframes | D §1 | `timeframes` | signal 15m, budget 4h, stop 1h, execution 15m, alignment 5m | match |
| bar usability | D §2.1 | `bar_rules` | closed, volume/trade count positive, 3-member bucket, valid OHLC, first duplicate | match |
| session completeness | D §2.2 | `bar_rules.session_requires_all_32_bars`, `session_contiguity` | all 32 bars, exactly 15 minutes apart | match; **look-ahead C1** |
| sessions | D §3 | `sessions.definitions` | ASIA 00–08, EUROPE 08–16, US 16–24, signal at +2h | match |
| signal | D §4.1–§4.2 | `signal` | 8 bars, P0/P1/r2, `0.5*ATR1h/P0`, q `<=` signal instant, VWAP required, one per session | match; **C4**, **m9** |
| VWAP | D §5 | `vwap` | session, HLC3, volume, reset, no seed, `P1 > VWAP` | match |
| volatility budget | D §6 | `volatility_budget` | 4h ATR14, 540-bar percentile, band [25, 80], inclusive current bar, close `<` signal instant | match |
| 4h ATR construction | D §6.2 line 268 | `volatility_budget.atr_period`, `atr_method` | period 14, Wilder, no first-TR/seed/reset rule; text points to a protocol that has no ATR formula | **incomplete — M1** |
| 1h stop ATR | D §4.2, config | `atr_1h` | Wilder 14, segment-scoped, first TR `high-low`, mean first 14, recursion | match in config; spec's "same as protocol" reference is wrong — **M1** |
| entry | D §7.1 | `entry` | open of 15m bar at confirmation + 15m; reject missing/unclosed/zero/partial/non-positive | match (semantic issue **M2**) |
| stop | D §7.2 | `stop` | `entry - 1.0*ATR1h`, fixed at signal, no floor, no widening | match |
| episodes | D §8 | `episodes` | session unit, one per session, no retry, key `D:{session_start}\|{session_id}` | match |
| non-overlap | D §9 | `overlap` | 24h canonical, [12, 48], entry_time, inclusive, after cost gate | match |
| costs | D §7.3 | `costs` | 26 bp, 0.0026, gate 0.20, implied min 1.30%, buckets, [10, 26, 39, 52] | match; bucket inclusivity ambiguous — **m2** |
| warm-up | D §4.2, §6.2 | `warmup` | 14 1h bars, 552 4h bars, no pre-dev, `first_session_signal_after 2021-04-03T00:00:00Z` | **imprecise — m4** |
| clustering | D §11 items 8–9 | `clustering` | "signal-producing budget episodes" | **undefined cluster unit — M11** |
| capital | D §11 item 11 | `capital` | $10,000, 1%, $100 risk, `risk_usd / stop_pct`, $5 minimum, `1e-5` lot | match (unit ambiguity **M10**) |
| power reference | D §0.2, §12.2 | `power_reference` | 0.15R, 1R, 5%, 80%, 349 | match |
| verdict | D §12 | `verdict_thresholds` | 150, 349, `max_median_cost_r 0.20`, proposed 0.30 / 0.17 / 0.02 | numeric match, **population defect C2** |
| pipeline | D §10 | `pipeline` | S1–S9 | match |
| denominators | D §10.1 | `denominators` | S2/all, S3/S2, S4/S3, S5/S4, S6/S5, S7/S6, S8/S7, S9/S8 | numeric match; **m8** |
| reporting | D §11 | `reporting` | required and forbidden lists | match |
| confirmations | D §13 | `confirmations` | all false | match |

### 2.3 Comparison conclusion

No numeric transcription mismatch was found. Every value that both the Markdown and the JSON state is the same value. The JSON configurations are faithful transcriptions of the Markdown.

That is exactly why the freeze passes a hash check and still fails the audit: the defects are in the **meaning** of the frozen values, not in the transcription. The configs faithfully encode the same look-ahead session rule (**C1**), the same post-gate median population (**C2**), the same undefined 4h ATR construction (**M1**), and the same ambiguous pipeline labels (**M7–M9**).

---

## 3. Temporal and causality audit

### 3.1 Candidate B symbolic walkthrough

The example is symbolic; the concrete timestamps are only an instantiation. Let `T` be the `open_time` of the expansion bar `e`, and suppose `T = 2021-06-01T00:00:00Z`. All times are UTC.

| step | bar / instant | timestamp | rule applied | knowledge at the step |
|---|---|---|---|---|
| 1 | expansion bar `e` | opens `T = 00:00:00`, closes `00:59:59.999` | expansion test on `TR[e]`, `ATR[e-1]`, body, close location, close > open | all inputs are at or before `e`'s close |
| 2 | 4h regime at `e` | 4h bar opening `2021-05-31T20:00:00Z`, closing `23:59:59.999Z` | most recent 4h close strictly before `T` | closed before `e` opens |
| 3 | fix levels | `L_e = close[e]`, `A_e = ATR[e]` | fixed at episode start | known at `e`'s close |
| 4 | retest bar `r = e+1` | opens `01:00:00`, closes `01:59:59.999` | `low[r] <= L_e + 0.25*A_e`, penetration `<= 0.50` | known at `r`'s close |
| 5 | confirmation bar `c = e+2` | opens `02:00:00`, closes `02:59:59.999` | `close[c] > L_e` and `close[c] > open[c]` | known at `c`'s close |
| 6 | 4h regime at `c` | 4h bar opening `2021-05-31T20:00:00Z` again | most recent 4h close strictly before `02:00:00` | closed before `c` opens |
| 7 | signal instant | `close_time[c] = 02:59:59.999` | signal exists only now | no `c+1` data used |
| 8 | entry bar `e+3` | opens `03:00:00` | entry price `open[03:00]` | entry is strictly after the signal |
| 9 | stop | min of `low[e]`, `low[r]`, `low[c]` | `S`, `D = entry_open - S` | all lows known by `c`'s close |
| 10 | cost | `cost_R = 0.0026 * entry_open / D` | gate `<= 0.20` | arithmetic only |

The core temporal chain is causal. The expansion uses only bars through `e`; the retest uses `r`; the confirmation uses `c`; entry is one bar later. The 4h regime reads a bar that closed before the relevant 1h bar opened. There is no later-row read in the signal, stop, or cost path.

There are two temporal defects:

1. **Entry-bar validity is ex-post (M2).** At step 8 the entry price is the entry bar's open, but the validity test in §5.5 also requires the entry bar to be `is_closed`, to have `volume > 0` and `trade_count > 0`, to be a complete 5m bucket, and to have valid OHLC. Those properties are only known at the entry bar's close (`03:59:59.999` in the example), which is after the entry decision. A real-time trader cannot reject an entry at `03:00` because the bar later turns out to have a zero-volume final member.
2. **Development-end entry is not rejected (M5).** If the confirmation bar were `2024-06-30T23:00:00Z`, the entry bar would open at `2024-07-01T00:00:00Z`, outside the development interval. The spec only rejects a confirmation bar that is the last bar of its 1h segment; it does not mention the interval boundary. That can read a validation/OOS bar or silently drop the signal; either way the boundary is not frozen.

### 3.2 Candidate D symbolic walkthrough

Let the ASIA session start be `s = 2021-06-01T00:00:00Z`. The measurement window is `b0..b7`, opening `00:00` through `01:45`, and the signal instant is `T = 01:59:59.999`.

| step | bar / instant | timestamp | rule applied | knowledge at the step |
|---|---|---|---|---|
| 1 | `b0` | opens `00:00:00` | `P0 = open[b0]` | known at `b0`'s open |
| 2 | `b7` | opens `01:45:00`, closes `01:59:59.999` | `P1 = close[b7]`, `r2 = P1/P0 - 1` | known at `b7`'s close |
| 3 | 1h stop ATR `q` | 1h bar opening `01:00:00`, closing `01:59:59.999` | last 1h close `<= T`; `thr = 0.5*ATR1h[q]/P0` | bar closes exactly at `T` |
| 4 | session VWAP | `b0..b7` | `sum(HLC3*volume)/sum(volume)` | all eight bars closed by `T` |
| 5 | 4h budget | 4h bar opening `2021-05-31T20:00:00Z`, closing `23:59:59.999Z` | most recent 4h close strictly before `T`; `pct` in [25, 80] | closed before `T` |
| 6 | signal instant | `T = 01:59:59.999` | `r2 >= thr` and `P1 > VWAP` | all signal inputs known at `T` |
| 7 | entry bar `b8` | opens `02:00:00` | entry price `open[b8]` | entry is strictly after `T` |
| 8 | stop | `entry_open - 1.0*ATR1h[q]` | `D = ATR1h[q]` | fixed at the signal |
| 9 | cost | `cost_R = 0.0026 * entry_open / D` | gate `<= 0.20` | arithmetic only |
| 10 | session completeness | `b0..b31`, through `07:45:00` | all 32 bars must be usable | **future data relative to `T`** |

Steps 1–9 are causal in intent. Step 10 is not: the session is declared evaluable only if all 32 bars, including `b8..b31` (opening `02:00` through `07:45`, closing up to `07:59:59.999`), are present and usable. The signal at `T = 01:59:59.999` therefore depends on bars that do not exist until nearly six hours later. If `b20` (opening `05:00`) is missing, the session is marked `session_data_incomplete` and the fully determined first-two-hour signal is discarded. That is **C1**.

The 1h `q` equality is also the source of **C4**: protocol §1.5 #1 requires the indicator input's `close_time` to be strictly less than the decision instant, but `q` closes exactly at `T`. D §4.2 deliberately uses `<=` and argues that the bar is complete at `T`. The intent is causal, but the protocol's literal check is not satisfied.

### 3.3 Causality table

| candidate | decision | inputs | earliest/latest close | causal? | issue |
|---|---|---|---|---|---|
| B | expansion `e` | 1h bars through `e`; 4h close before `open[e]` | `e` close; 4h before `e` open | yes | — |
| B | retest `r` | `low[r]`, `L_e`, `A_e` | `r` close | yes | — |
| B | confirmation `c` | `close[c]`, `open[c]`; 4h close before `open[c]` | `c` close; 4h before `c` open | yes | — |
| B | entry | `open[c+1]`; entry bar close-time validity | entry open; entry close for validity | **no** | **M2** |
| B | stop / cost | lows `e..c`; `D` | `c` close | yes | — |
| D | `r2` / VWAP | `b0..b7` | `b7` close = `T` | yes | — |
| D | 1h ATR `q` | 1h bar closing `<= T` | `T` (equality) | intent yes, protocol literal **no** | **C4** |
| D | 4h budget | 4h close `< T` | before `T` | yes | — |
| D | entry | `open[b8]`; entry bar close-time validity | entry open; entry close for validity | **no** | **M2** |
| D | stop / cost | `ATR1h[q]`; `entry_open` | `T` / entry open | yes (given C4) | — |
| D | session eligibility | `b0..b31` | `s+8h` | **no** | **C1** |

### 3.4 Boundary findings

- **Session boundaries (D).** The three sessions partition the UTC day under `[start, end)` ownership; the bar opening at `08:00` belongs to EUROPE and the bar at `16:00` to US. The spec is internally consistent here.
- **4h reads (B).** `floor(T, 4h) - 4h` is correct: `04:00` reads the `00:00` bar, `03:00` reads the previous day's `20:00` bar. No unfinished 4h candle is read.
- **4h reads (D).** ASIA `01:59:59.999` reads the previous day's `20:00` bar; EUROPE `09:59:59.999` reads `04:00`; US `17:59:59.999` reads `12:00`. Correct.
- **Non-overlap boundary.** Both specs use `entry_time` and an inclusive boundary (`>= 72h`, `>= 24h`). Correct and consistent with the worked examples.
- **Development interval boundary.** The frozen string-comparison rule is not safe against the dataset's timestamp encoding. This is **C3**, and it is the most concrete boundary defect in the freeze.

---

## 4. Stop and cost arithmetic

### 4.1 Formulas

Candidate B:

```
S = min(low[x]) for x in e..c
D = entry_open - S
stop_pct = D / entry_open
cost_R = 0.0026 * entry_open / D
```

Candidate D:

```
S = entry_open - 1.0 * ATR1h[q]
D = entry_open - S = ATR1h[q]
stop_pct = D / entry_open
cost_R = 0.0026 * entry_open / D
```

Both formulas are algebraically correct. The gate equivalence is also correct:

```
cost_R <= 0.20
0.0026 * entry_open / D <= 0.20
D / entry_open >= 0.0026 / 0.20 = 0.013
stop_pct >= 1.30%
```

### 4.2 Arithmetic check

| case | entry | stop | D | stop_pct | cost_R | gate |
|---|---:|---:|---:|---:|---:|---|
| B worked example (B §10.1) | 104.00 | 99.50 | 4.50 | 4.3269% | 0.06009 | pass |
| B exact boundary | 100.00 | 98.70 | 1.30 | 1.3000% | 0.20000 | pass (inclusive) |
| B just below | 100.00 | 98.71 | 1.29 | 1.2900% | 0.20155 | fail |
| D worked example (D §11.1) | 30,610.00 | 29,610.00 | 1,000.00 | 3.2669% | 0.07959 | pass |
| D tight stop | 30,610.00 | 30,410.00 | 200.00 | 0.6534% | 0.39793 | fail |
| D exact boundary | 100.00 | 98.70 | 1.30 | 1.3000% | 0.20000 | pass (inclusive) |

Both worked examples reproduce. The stop-widening prohibition is stated correctly in both specs, and the gate is not silently relaxed.

### 4.3 Capital-geometry unit defect (M10)

Both specs instruct the census to report:

```
notional_usd = 100 / stop_pct
```

But `stop_pct` is defined as `D / entry_open`, a **fraction** (for example, `4.5/104 = 0.043269`), while the worked examples display it as a **percentage** (`4.33%`, `3.267%`). The formula is only correct if the fraction is used:

| interpretation | B example | D example |
|---|---:|---:|
| fraction `0.043269` / `0.032669` | `100/0.043269 = $2,311` (23.1% of equity) | `100/0.032669 = $3,061` (30.6% of equity) |
| percent `4.33` / `3.267` | `100/4.33 = $23.09` (0.23% of equity) | `100/3.267 = $30.61` (0.31% of equity) |

The two readings differ by 100×. The spec does not say which representation the formula consumes. Separately, the FAIL condition "a capital-geometry result that makes the design impracticable under spot cash" has no numeric threshold in either spec. A runner cannot apply it deterministically. This matters because the cost condition is vacuous (**C2**), so capital geometry is one of the few remaining FAIL triggers.

---

## 5. Episodes, deduplication, and non-overlap

### 5.1 Candidate B

The normal-path episode machine is deterministic:

- one active episode at a time;
- a later expansion inside an active episode is absorbed and does not move `L_e`, `A_e`, or the retest window;
- an episode ends at the first of signalled, invalidated, expired, regime lost, segment break, or rejected;
- after an episode ends, the next qualifying expansion at a strictly later index starts a new episode;
- the key is `B:{expansion_open_time}`.

Deduplication is also sound in the normal path: under one active episode, two signals cannot share an entry time or a confirmation bar; the census still checks and reports zero removals.

Non-overlap is correctly specified: population is unique cost-feasible signals after the cost gate, sort by `entry_time`, accept if `entry_time - last_accepted >= 72h`, inclusive, rejected signals retained. The 24h and 120h variants use the same greedy algorithm and are diagnostics only.

The problems are in the **accounting**, not the state machine:

1. **S4/S5 episode start (M8).** `S4` is "episodes started (raw expansion episodes)" (B §9 line 552), but §4.3 says a regime failure at `e` means the episode "never starts" (B §4.3 line 274). If S4 excludes regime-failed expansions, `permission_share = S5/S4` is 1 by construction; if S4 includes them, S4 is really "expansion bars," not "episodes started." The denominator is undefined.
2. **S6/regime_lost (M9).** `S6` is "structurally valid episodes (retest touch + resumption confirmed)" (B §9 line 554), but `regime_lost` is assigned to S6 (B §9 line 572). An episode with a touch and resumption but a regime failure at confirmation is not "structurally valid" for a signal. Either S6 includes a non-valid subset, or `regime_lost` has no stage.
3. **Unknown label (M7).** §4.3 maps `Unknown` or `False` at `e` to `regime_not_permitted` (line 274); §9 maps `Unknown` to `warmup_regime` and `False` to `regime_not_permitted` (lines 566–567). S5 is unchanged (both fail), but the primary exclusion label is contradictory.
4. **S2/S3 denominator (m1).** S2 is "1h bars with ATR(14) defined" (line 550), i.e. local index `t >= 13`. The expansion test needs `ATR[t-1]`, so the first testable bar is `t = 14` (B §3.1 line 155). S2 therefore includes one bar per segment that cannot be an expansion. `expansion_test_share = S3/S2` has an unmapped bar.

None of these changes the normal-path signal set, but they make the required pipeline unreconcilable and the exclusion accounting ambiguous. A census report could not be checked against the frozen definitions.

### 5.2 Candidate D

The session-as-episode design is deterministic:

- one opportunity per session;
- no retry inside a session;
- adjacent sessions are distinct opportunities;
- key `D:{session_start}|{session_id}`;
- duplicate session keys are expected to be zero and are checked.

Non-overlap is correctly specified: population is unique cost-feasible signals after the cost gate, sort by `entry_time`, accept if `entry_time - last_accepted >= 24h`, inclusive, rejected signals retained. The 12h and 48h variants are diagnostics only.

The defects are:

1. **Session completeness look-ahead (C1).** The session is the episode, but the episode is declared evaluable only after all 32 bars through `s+8h` are known. The signal at `s+2h` is therefore conditional on future bars. This is not an episode/dedup defect in the normal path; it is a selection defect that changes which sessions enter the population.
2. **Warm-up off-by-one (M6).** D §4.2 says a session whose `q` falls in the first 14 bars of a 1h segment is `warmup_atr` (lines 211–212). `ATR[13]` is the first defined value (mean of `TR[0..13]`), so the first **13** bars are warm-up and local index 13 is testable. The spec and config both say 14, over-excluding one `q` bar per segment.
3. **`q` fallback (m9).** The rule "last 1h bar whose `close_time <= signal instant`" silently selects an earlier bar if the expected `01:00` / `09:00` / `17:00` bar is missing or unusable. D §4.2 asserts those bars are the selected ones, but does not define a fallback. In the registered development gaps, none of those three hours is missing or zero-volume, so this is a latent ambiguity rather than a demonstrated count change. It still needs an explicit rule.

### 5.3 Cross-candidate non-overlap finding

Both specs correctly say non-overlap is **not** independence. A 24h or 72h spacing rule prevents overlapping holding windows; it does not make the signals causally independent. The specs state this, and the statistical caveats are correct. The problem is that the verdict's cost dimension is vacuous (**C2**), so the count `N` is doing almost all the decision work while the dependence caveats remain unresolved. That is a reason to be conservative about any "PASS" label, not a reason to treat `N` as an effective sample size.

---

## 6. Data integrity, gaps, and alignment

### 6.1 Dataset hashes and metadata

All four dataset hashes match `backend/data/datasets/manifest.json`. The bar counts and gap totals match the freeze manifest. The 4h series is genuinely gap-free by vendor count: 12,414 bars = 12,414 expected, 0 gaps. The 1h series has 7 registered gaps totalling 14 missing bars. The 15m series has 7 gaps totalling 70 missing bars. The 5m series has 7 gaps totalling 213 missing bars.

### 6.2 Known partial buckets

The Stage 2A and Stage 2C alignment audits establish, without a census:

| series | development bars | partial buckets | known location |
|---|---:|---:|---|
| 15m | 122,592 expected | 70 missing bars across 7 gaps | registered 5m gaps |
| 1h | 30,648 expected | 7 partial buckets + 14 missing bars | gap-adjacent |
| 4h | 7,662 | 12 partial buckets | all gap-adjacent |

The 4h partial buckets are the binding case for the protocol's "partial bucket unusable" rule. They occur at `2021-02-11 00:00`, `2021-02-11 04:00`, `2021-03-06 00:00`, `2021-04-20 00:00`, `2021-04-20 04:00`, `2021-04-25 04:00`, `2021-04-25 08:00`, `2021-08-13 00:00`, `2021-08-13 04:00`, `2021-09-29 04:00`, `2021-09-29 08:00`, and `2023-03-24 12:00` (Stage 2C §5.1). All twelve are exact on `close`; the audit records them but does not force a 4h segment break.

### 6.3 The protocol/spec conflict on 4h partial buckets (M3)

Protocol §1.3 says the bar-validity rules are "applied identically at every timeframe" and that a partial bucket is "unusable" (lines 79–92). It gives the expected membership counts as 12 at 1h and 3 at 15m, and by extension 48 at 4h. Candidate B §2.3 says the 4h vendor series is gap-free and "A 4h bar whose bucket straddles a 5m gap is retained as supplied" (lines 121–127). Candidate D §2.3 says the 4h series "is used as supplied" (lines 121–127). Neither spec performs a 48-member check on 4h.

A literal protocol runner therefore excludes 12 4h bars and segment-breaks the 4h series; a literal B/D runner uses them. The two implementations will compute different 4h ATR values and different 540-bar percentiles around the 12 buckets. The effect is probably small because the 4h ATR is slow and the buckets are exact on close, but "probably small" is not a frozen rule. This is a direct contradiction, not a documented sensitivity.

### 6.4 Alignment check is not executable on gap-affected buckets (M4)

Protocol §1.6 requires:

- each 4h `open/high/low/close` to equal the aggregate of its **four** 1h bars;
- each 1h bar to equal the aggregate of its **four** 15m bars;
- each 15m bar to have its **three** 5m members.

The 1h series has 14 missing bars and 7 partial buckets; the 15m series has 70 missing bars. On gap-affected buckets, the "four members" or "three members" do not all exist. The protocol does not say whether to skip the bucket, aggregate the available members, or count a mismatch.

The arithmetic is sensitive to that undefined choice:

| check | development population | known gap-affected buckets | rate | 0.1% tolerance |
|---|---:|---:|---:|---|
| 4h from 1h | 7,662 | 12 partial 4h buckets | 12/7,662 = 0.1566% | **exceeds** if counted as failures |
| 1h from 15m | 30,648 | 7 partial + 14 missing 1h bars | 21/30,648 = 0.0685% | below |
| 15m from 5m | 122,592 | 70 missing 15m bars | 70/122,592 = 0.0571% | below |

If the 12 gap-affected 4h buckets are counted as alignment failures, the 4h-from-1h rate is 0.1566%, above the protocol's 0.1% threshold, and the protocol's own rule yields **INCONCLUSIVE**. If they are skipped, the check silently changes populations. Either way, the compliance outcome is not frozen. The Stage 2C audit says the 12 buckets are exact on `close`, which may make the close comparison pass, but the check still assumes four 1h bars and does not define high/low handling for missing members. The audit cannot certify an alignment result that depends on an undefined convention.

### 6.5 Timestamp encoding and the development boundary (C3)

This is the most concrete integrity defect. The specs and protocol say:

> Row filtering to the development interval happens by ISO-string comparison on `open_time` before any numeric conversion. (B §1; D §1; protocol §1.2)

The bounds are written with a `T` separator:

```
2021-01-01T00:00:00+00:00   (inclusive)
2024-07-01T00:00:00+00:00   (exclusive)
```

The dataset stores `open_time` with a **space** separator:

```
"2021-01-01 00:00:00+00:00"
"2024-07-01 00:00:00+00:00"
```

Lexicographic comparison is byte comparison. Because `' '` (0x20) sorts before `'T'` (0x54):

- `"2021-01-01 00:00:00+00:00" < "2021-01-01T00:00:00+00:00"`, so a literal `>= dev_start` comparison **excludes** the 2021-01-01 development bars;
- `"2024-07-01 00:00:00+00:00" < "2024-07-01T00:00:00+00:00"`, so a literal `< dev_end` comparison **includes** the 2024-07-01 validation/OOS bars.

The dataset contains records whose `open_time` falls on `2024-07-01` in the 15m, 1h, and 4h files (96, 24, and 6 records respectively, including one record at `2024-07-01 00:00:00+00:00` in each). Including them directly violates the non-negotiable "validation and out-of-sample data are never read." The same rule excludes the entire first development day, which shifts the 4h ATR/percentile warm-up and the S1 counts.

The defect is not hypothetical: it is a property of the frozen text and the on-disk encoding. A runner must normalize the separator (or compare parsed aware datetimes) and assert that the maximum `open_time` read is strictly below `2024-07-01T00:00:00Z`. The freeze currently does neither.

### 6.6 String-typed fields (m10)

The dataset stores `is_closed` as the JSON string `"True"`, and stores prices, volumes, and `trade_count` as strings. A runner that reads raw JSON and evaluates `row["is_closed"] == True` will get `False` for every bar and mark the entire dataset unusable. The existing `CandleData` schema coerces the values, so the repository has a correct parser, but the protocol does not require its use. This is an implementation note, not a freeze defect; it reinforces the need for a typed loader in the runner.

---

## 7. Statistical interpretation audit

### 7.1 Correct labels

The statistical framing in both specs is unusually careful and is, in the main, correct:

| claim | location | audit |
|---|---|---|
| 150 is a project protocol choice, not derived from a power calculation | B §0.1; D §0.2; protocol §6.2 | correct |
| 349 is an independent-observation planning estimate, optimistic under clustering and fat tails | B §0.1; D §0.2; protocol §6.2 | correct |
| 349 is a tier label, not a requirement | B §11.1; D §12 | correct |
| Kish `n_eff` is a concentration diagnostic, not a dependence estimate | B §10 item 8; D §11 item 9; protocol §3.1 | correct |
| non-overlap enforces spacing, not independence | B §7.3; D §9.2 | correct |
| `0.15 - median_cost_R` is a design-margin diagnostic, not expectancy or profitability | B §0.1, §11.1; D §0.2, §12 | correct label, but see **C2** |
| 26 bp is a Binance proxy, not verified Nobitex execution cost | B §0, §8; D §0, §7.3; protocol §4 | correct |
| a census cannot establish a positive edge | B §11; D §12; protocol §0, §6.1 | correct |
| detectable-effect reference `2.801585 / sqrt(N)` is a planning calculation under independence | protocol §3.1; B §10 item 9; D §11 item 10 | correct |

The numeric identity `(1.959964 + 0.841621) = 2.801585` and `(2.801585/0.15)^2 = 348.84 ≈ 349` checks out. The 150 floor is correctly not presented as a statistical requirement.

### 7.2 The median-cost population is wrong (C2)

The verdict definitions are:

- B §11.1: `M = median cost_R` over **S8** (cost-feasible signals).
- D §12: `M = median cost_R` over **S7** (cost-feasible signals).

In both pipelines, the cost-feasible stage is defined by `cost_R <= 0.20` (B §9 line 556; D §10 line 461). Every member of the median population therefore satisfies the gate by construction. It follows that:

```
M <= 0.20   always true
M > 0.20    impossible
```

The FAIL condition `M > 0.20` can never fire, and the PASS conditions `M <= 0.20` are always satisfied. The cost dimension is removed from the verdict. The verdict reduces to `N` and the undefined capital-geometry condition. This is not a cosmetic issue: a candidate whose median cost is `0.199` (essentially at the gate, with no design margin) would pass the cost condition just as easily as one at `0.05`.

The correct population for the stated economic test is the **pre-gate structurally valid** population: B S7 (valid entry and stop, before the cost gate) and D S6 (valid entry and stop, before the cost gate). Those populations include the signals that fail the gate, which is exactly what a median cost distribution must include if the gate is supposed to be tested. The proposed economic thresholds (`M <= 0.12` for B, `M <= 0.17` for D) are also conditional on the post-gate population, so they do not fix the problem; they merely tighten a median that is already bounded above by 0.20.

The same defect makes `E = 0.15 - M` a weak diagnostic. Because `M <= 0.20`, `E >= -0.05` by construction, and `E` can never reveal a raw opportunity set whose median cost is above the gate. It is correctly labelled "not expectancy," but it is also not the margin the verdict claims to use.

### 7.3 What the audit does not do

The audit did not compute any statistic from market outcomes, did not estimate a signal count, and did not test a P&L, expectancy, win rate, drawdown, Sharpe, CAGR, or profitability hypothesis. The statistical audit is a review of the frozen definitions, not a census.

---

## 8. Findings

Severity is defined as follows:

- **Critical** — violates a non-negotiable or causal rule, or makes a primary verdict condition logically inoperative, or makes a compliant run impossible as written. Any critical finding blocks the census.
- **Major** — can change the signal set, counts, compliance outcome, or a required diagnostic, but has a plausible deterministic reading. Any unresolved major ambiguity that could materially change results also blocks a PASS.
- **Minor** — documentation, provenance, or accounting clarity with no demonstrated effect on the signal set or verdict.

### 8.1 Critical findings

#### C1 — Candidate D uses future session bars to decide whether a first-two-hour signal exists

**Evidence:** D §2.2 (lines 112–119): "A session is evaluable only if all 32 bars are usable and exactly 15 minutes apart. If any bar is missing or unusable, the session is marked `session_data_incomplete` and produces no signal." D §3 (line 137): the measurement window is bars opening `00:00`…`01:45`, signal at `01:59:59.999`; the session runs to `08:00`. D §4.2 (line 208): "Signal instant: the `close_time` of `b7`." D §10 (line 456): S2 is "evaluable sessions 32/32 usable bars, contiguous." Protocol §1.5 #1/#4 (lines 114–119): no indicator may use a bar whose `close_time` is not before the decision instant; no computation may read a row with index greater than the decision bar.

**Mechanism:** The signal is fully determined at `s+2h` from `b0..b7`. The evaluability test, however, requires `b8..b31`, which open from `s+2h` to `s+7h45` and close up to `s+8h`. A missing or unusable bar at, say, `b20` (opening `s+5h`) discards the `s+2h` signal. The signal set is therefore selected using information that did not exist at the signal instant.

**Consequence:** Look-ahead selection. The counted D sample is conditional on late-session data quality; sessions with late gaps are removed even though their first-two-hour signals were determined. This violates the protocol's causal rule and invalidates the prior review's answer to its own question 5 ("Can a signal use future data? No", `STAGE2E_INDEPENDENT_REVIEW.md` line 19). It also means the D census cannot claim to count signals that a real-time implementation could have taken.

**Required fix:** Define signal eligibility using only `b0..b7`. Move the 32-bar completeness check to a post-count diagnostic (for example, a `session_full_data` flag) that cannot remove a signal, and report how many signals come from sessions with late gaps. If the design genuinely requires a full session, then the signal instant must move to `s+8h`, which changes the hypothesis and requires a new specification.

#### C2 — The primary median-cost verdict condition is vacuous in both candidates

**Evidence:** B §9 (line 556): S8 is "cost-feasible signals cost_R <= 0.20." B §11.1 (line 664): "`M = median cost_R` over S8." D §10 (line 461): S7 is "cost-feasible cost_R <= 0.20." D §12 (line 574): "`M = median cost_R` over S7." Both verdict tables then use `M > 0.20` as a FAIL condition and `M <= 0.20` as a PASS condition (B §11.1 lines 669–672; D §12 lines 579–582).

**Mechanism:** A median of a set whose every member satisfies `cost_R <= 0.20` also satisfies `M <= 0.20`. Therefore `M > 0.20` is impossible and `M <= 0.20` is always true. The cost test cannot fail.

**Consequence:** The verdict collapses to `N` (the non-overlap count) and the undefined capital-geometry condition. A candidate with every surviving signal at `cost_R = 0.199` passes the cost condition exactly like one at `0.05`. The `E = 0.15 - M` design margin is also bounded below by `-0.05` and cannot expose a raw opportunity set above the gate. The prior review's claim that "the decision thresholds [are] justified and correctly labelled" (line 26) does not catch this because the labels are correct; the population is not.

**Required fix:** Compute `M` over the pre-gate structurally valid population: B S7 (valid entry and stop, before cost) and D S6 (valid entry and stop, before cost). Report both `M_all` (pre-gate) and `M_feasible` (post-gate); use `M_all` in the verdict. Re-freeze before any counting.

#### C3 — The development-boundary string comparison can read validation data

**Evidence:** B §1 (lines 69–72), D §1 (lines 76–78), and protocol §1.2 (lines 69–77) all require "row filtering ... by ISO-string comparison on `open_time`" against `2021-01-01T00:00:00+00:00` and `2024-07-01T00:00:00+00:00`. The dataset stores `open_time` as `"2024-07-01 00:00:00+00:00"` (space separator). The dataset files contain 96 15m, 24 1h, and 6 4h records whose `open_time` falls on `2024-07-01`, one of each at `2024-07-01 00:00:00+00:00`.

**Mechanism:** Lexicographic comparison of the mixed formats: `"2024-07-01 00:00:00+00:00" < "2024-07-01T00:00:00+00:00"` because space sorts before `T`. A literal `< dev_end` includes the 2024-07-01 rows. The same comparison excludes `"2021-01-01 00:00:00+00:00"` from a `>= dev_start` filter.

**Consequence:** Direct violation of the non-negotiable "validation and out-of-sample data are never read." The D budget/regime and the B 1h/4h indicators can read a 2024-07-01 bar; the first development day is silently dropped. The error is deterministic and is not cured by hash verification, because the hashes match the files that contain the space-separated encoding.

**Required fix:** Normalize the separator (or compare parsed aware datetimes) before any filtering. Add an explicit assertion that the maximum `open_time` read is strictly below `2024-07-01T00:00:00Z`, and a fixture test using the actual dataset strings. Do not rely on raw lexicographic comparison of mixed formats.

#### C4 — The protocol's causality rule conflicts with D's inclusive 1h ATR and its own inclusive percentile rule

**Evidence:** Protocol §1.5 #1 (lines 114–115): "Every indicator value used at a decision instant is computable from bars whose `close_time` is **strictly less than** the decision instant." Protocol §1.5 #5 (line 120): "The percentile window for a 4h decision ends at the 4h bar being used, **inclusive**." D §4.2 (lines 186–191): `q` is the last 1h bar whose `close_time` is **less than or equal to** the signal instant; the `01:00` bar closes exactly at `01:59:59.999`, the signal instant. D §6.2 (lines 296–298): the 4h percentile window includes the current bar.

**Mechanism:** At the D signal instant `T`, `ATR1h[q]` is taken from a bar whose `close_time` equals `T`. Under #1, that bar's close is not strictly less than the decision instant, so the input is inadmissible. Under #5, the 4h window is inclusive, which is also not "strictly less." The protocol does not define whether the "decision instant" is the signal instant or the next executable open; if it were the latter, the strict inequality would hold for the signal bar but the wording would need to say so.

**Consequence:** A strict implementation of #1 fails D's causality check and yields **INCONCLUSIVE**; a lenient implementation passes. Two careful engineers can produce different compliance verdicts from the same frozen files. That is precisely the divergence the protocol exists to prevent.

**Required fix:** Amend #1 to "less than or equal to the decision instant" when a bar closes exactly at that instant, or define the decision instant as the next executable open and state that all signal-bar values are known at the prior close. Reconcile #1 and #5 in a new protocol version and add a boundary worked example.

### 8.2 Major findings

#### M1 — The 4h ATR construction is undefined in both candidates

**Evidence:** B §4.2 (line 224) says only "`ATR4h[.] = Wilder ATR(14) on 4h true range`." D §6.2 (line 268) says "same construction rules as the shared protocol." The shared protocol contains no ATR formula. The 1h ATR is fully defined in B §3.1 and in both configs' `atr_1h`, but the 4h ATR has no first-TR rule, no seed rule, no segment-reset rule, and no missing-bar rule. The configs only give `atr_period: 14` and `atr_method: "wilder"`.

**Consequence:** The first 4h true range, the seed (simple mean of the first 14 vs another initialization), and the treatment of the first bar's previous close are all open. Different choices shift `ATR4h`, the 540-bar percentile, and therefore `permission`/`budget_ok`. The signal set can differ. The 4h series is gap-free, which removes one ambiguity, but not the first-TR/seed one.

**Required fix:** Add the complete 4h ATR construction to the protocol (or to each spec) with a worked example, matching the 1h construction's explicitness.

#### M2 — Entry-bar validity is an ex-post filter

**Evidence:** B §5.5 (lines 356–364) and D §7.1 (lines 320–328) require the entry bar to be usable under §2.1, including `is_closed`, `volume > 0`, `trade_count > 0`, a complete 5m bucket, and valid OHLC. The entry price is the entry bar's **open**. The close-time properties are not known at the open.

**Consequence:** The counted entry set is conditional on the entry bar's full-bar properties. A bar that opens valid but later has a zero-volume final member is rejected after the fact. A real-time trader could have entered at the open. This is an ex-post selection, even though it does not read a later row index.

**Required fix:** At entry, validate only open-time-known properties (present, on grid, open > 0, prior bar closed). Treat close-time properties as a post-count data-quality diagnostic, or explicitly label the entry rule as "enter at the open only if the bar later proves complete," which is not live-implementable.

#### M3 — The protocol's partial-bucket rule contradicts both specs at 4h

**Evidence:** Protocol §1.3 (lines 79–92) says the rules apply identically at every timeframe and that a partial bucket is unusable; the expected membership is 12 at 1h and 3 at 15m, which implies 48 at 4h. B §2.3 (lines 121–127) retains the 12 gap-adjacent 4h buckets as supplied; D §2.3 (lines 121–127) uses the 4h series as supplied. Stage 2C §5.1 confirms 12 partial 4h buckets.

**Consequence:** A literal protocol runner excludes the 12 bars and segment-breaks the 4h series; a literal candidate runner uses them. The 4h ATR/percentile and the regime/budget labels can differ around the gaps. The candidate's own rationale (the vendor close is a real last-trade price and the regime is slow) is reasonable, but it is not written as an explicit protocol exception.

**Required fix:** Either apply the 48-member check and segment-break the 4h series (reporting the warm-up loss), or add an explicit 4h exemption to §1.3 with the rationale and a sensitivity using the excluded variant. Re-freeze.

#### M4 — The alignment check is not executable on gap-affected buckets

**Evidence:** Protocol §1.6 (lines 124–140) requires each 4h bar to equal the aggregate of its four 1h bars, each 1h bar to equal the aggregate of its four 15m bars, and each 15m bar to have its three 5m members. The 1h series has 14 missing bars and 7 partial buckets; the 15m series has 70 missing bars. The protocol does not define skip/aggregate/mismatch handling for missing members. The 0.1% tolerance is applied to "bars," not to complete bars.

**Consequence:** If the 12 gap-affected 4h buckets are counted as failures, 12/7,662 = 0.1566% > 0.1%, and the protocol yields **INCONCLUSIVE**. If they are skipped, the check silently changes populations. The compliance outcome is implementation-dependent.

**Required fix:** Define a gap-aware alignment procedure: compare only complete buckets, report missing-member buckets separately, and apply the 0.1% tolerance to complete buckets only. Add the seven gap locations to the dataset manifest (see **m3**).

#### M5 — Candidate B does not reject an entry at the development-interval end

**Evidence:** B §5.5 (lines 370–372) rejects a confirmation bar that is the last bar of its 1h segment, because the next bar would be after a gap. It does not reject a confirmation bar whose next bar is at or after `2024-07-01T00:00:00Z`. If `c` is the `2024-06-30T23:00` bar, the entry bar opens at `2024-07-01T00:00`, outside the development interval. The spec says validation/OOS data are never read (B §1, §12).

**Consequence:** A runner can read a validation bar or silently drop the signal; either way the boundary is not frozen. This is a specific instance of the boundary problem in **C3**, but it survives even if the string comparison is fixed, because the entry bar is selected by `open_time[c] + 1h`.

**Required fix:** Add an explicit interval-end guard and an `entry_outside_interval` label. State that any signal requiring a bar at or after the boundary is rejected, not skipped forward.

#### M6 — Candidate D's 1h ATR warm-up is off by one

**Evidence:** D §4.2 (lines 211–212): "`ATR1h` needs 14 bars of its segment. A session whose `q` falls in the first 14 bars of a 1h segment is counted `warmup_atr`." But `ATR[13]` is defined as the mean of `TR[0..13]` (D config `atr_1h`; B §3.1 lines 146–147), so the first 13 bars are warm-up and local index 13 is testable. The config's `warmup.atr_1h_bars_per_segment: 14` repeats the same off-by-one.

**Consequence:** Up to one `q` bar per 1h segment is excluded unnecessarily. With 8 segments, this is at most 8 `q` bars and up to 24 sessions. The magnitude is bounded, but the rule contradicts the ATR definition and the config's own "14 bars" label.

**Required fix:** State the warm-up as 13 bars (or "ATR is defined from local index 13") and update the config.

#### M7 — Candidate B's `Unknown` regime label contradicts its own exclusion table

**Evidence:** B §4.3 (line 274): "`Unknown` or `False` at `e` → episode never starts; counted `regime_not_permitted`." B §9 (lines 566–567): `warmup_regime` is "S5: no computable 4h permission at `e`"; `regime_not_permitted` is "S5: permission `False`." Direct contradiction for the `Unknown` case.

**Consequence:** The primary exclusion reason for an `Unknown` at `e` is ambiguous. S5 is unchanged (both fail), but the pipeline accounting cannot be reconciled to the frozen labels.

**Required fix:** Assign `warmup_regime` to `Unknown` and `regime_not_permitted` to `False`; update §4.3 to match §9.

#### M8 — Candidate B's S4/S5 episode-start definition is contradictory

**Evidence:** B §9 (line 552): S4 is "episodes started (raw expansion episodes)." B §4.3 (line 274): a regime failure at `e` means the episode "never starts." If the episode never starts, it cannot be in S4; if S4 counts raw expansion bars, it is not "episodes started."

**Consequence:** `permission_share = S5/S4` is either 1 by construction or a real share, depending on an undefined reading. The denominator is not frozen.

**Required fix:** Define S4 explicitly as "expansion bars that begin an episode attempt" (including regime failures) or as "episodes that pass the regime at `e`," and rename the stage and denominator accordingly.

#### M9 — Candidate B assigns `regime_lost` to the "structurally valid" stage

**Evidence:** B §9 (line 554): S6 is "structurally valid episodes (retest touch + resumption confirmed)." B §9 (line 572): `regime_lost` is assigned to S6. An episode with a touch and a resumption but a regime failure at `c` is not structurally valid for a signal.

**Consequence:** If `regime_lost` is in S6, then `retest_conversion = S6/S5` includes episodes that cannot signal; if it is not, the label has no stage. The S6 count is ambiguous.

**Required fix:** Put `regime_lost` in a separate stage (for example, S5b) or define S6 as "touch + resumption confirmed, before the regime-at-confirmation check" and add a separate regime filter.

#### M10 — Capital-geometry units and the impracticability threshold are undefined

**Evidence:** B §10 item 10 (line 622) and D §11 item 11 (line 525) use `notional = 100 / stop_pct`. B §5.6 (line 379) and D §7.2 (line 338) define `stop_pct = D / entry_open`, a fraction. The worked examples display `4.33%` and `3.267%` (B §10.1 line 646; D §11.1 line 554). The two readings differ by 100× (see §4.3). The FAIL condition "a capital-geometry result that makes the design impracticable under spot cash" has no numeric threshold (B §11.1 line 670; D §12 line 580).

**Consequence:** The capital FAIL condition is not testable as written, and a runner could understate notional by 100×.

**Required fix:** Define `stop_fraction = D/entry_open`, `notional = risk_usd / stop_fraction`, and a numeric impracticability threshold (for example, notional > equity or notional_pct > 100%). State the units explicitly in the diagnostics.

#### M11 — The cluster unit for the Kish diagnostic is undefined

**Evidence:** B §10 items 7–8 (lines 615–619) refer to "signal-producing 4h regime episodes" and "signal-producing 4h permission episodes." D §11 items 8–9 (lines 519–522) refer to "signal-producing budget episodes." Protocol §3.1 (line 204) says "a cluster is the candidate's declared regime episode." Neither spec defines the episode boundaries (a maximal run of `permission == True`? a 540-bar window? a session?), nor how gaps/`Unknown` break a cluster.

**Consequence:** The required Kish `n_eff` and cluster-concentration diagnostics cannot be computed unambiguously; two implementations can produce different values. The verdict does not depend on them, but the required output is undefined.

**Required fix:** Define the cluster unit explicitly, including gap/`Unknown` handling, and add a worked example.

#### M12 — The freeze record's "zero critical ambiguities" claim is false

**Evidence:** `STAGE2E_FREEZE_MANIFEST.json` line 48 records `"unresolved_critical_ambiguities": 0`. `STAGE2E_INDEPENDENT_REVIEW.md` lines 6–7 and 101 say "No critical ambiguity remains." This audit finds at least four critical defects (C1–C4). The manifest's `statement` (line 6) is otherwise accurate: no census was run and no market data was processed beyond the dataset manifest.

**Consequence:** The authorization record is internally inconsistent. A reader could rely on the review's conclusion and skip the audit. The freeze's hash integrity is intact, but its "no critical" assertion is not.

**Required fix:** Correct the claim in a new versioned freeze. Do not alter the existing frozen artifacts. Add this audit's finding IDs to the new manifest's known-issues section.

#### M13 — The freeze manifest's recorded git HEAD predates the manifest itself

**Evidence:** `STAGE2E_FREEZE_MANIFEST.json` line 5 records `git_head_at_freeze: f8000e042c5b1238312317bd4decefae4f1c4438`. The manifest is committed at `6f8db24`, whose parent is `f8000e0`. At the recorded HEAD, the manifest does not exist. The manifest also does not record its own SHA256 (line 197).

**Consequence:** A runner that checks out `git_head_at_freeze` cannot find the manifest it is supposed to verify. The manifest can be edited without hash detection (though the spec/config hashes would still catch parameter changes in those files).

**Required fix:** Record the commit that contains the manifest (or add the manifest to its own `documents` entry in a new freeze) and state the exact provenance chain. This is a provenance defect, not a signal-set defect, but it matters for reproducibility.

### 8.3 Minor findings

These do not independently block a census, but they should be corrected in the same new freeze because they affect reproducibility or accounting clarity.

| id | location | finding | effect | required clarity |
|---|---|---|---|---|
| **m1** | B §9 line 550; B §3.1 line 155 | S2 is "1h bars with ATR(14) defined" (`t >= 13`), but the expansion test consumes `ATR[t-1]`, so the first testable expansion bar is `t = 14`. | S2 includes one untestable bar per 1h segment; `expansion_test_share = S3/S2` has an unmapped bar. | Define S2 as bars with `ATR[t-1]` defined, or report the S2/S3 off-by-one explicitly. |
| **m2** | B §8 line 533; D §7.3 line 358; B config line 142; D config line 185 | The Markdown buckets are `cost_R <= 0.10`, `(0.10, 0.20]`, `(0.20, 0.30]`, `(0.30, 0.50]`, `> 0.50`; the JSON encodes them as `[[null, 0.10], [0.10, 0.20], …]`, which does not state endpoint inclusion. | A generic bucketizer can place a boundary value in the wrong bucket; bucket counts would not reconcile. | Encode each bucket as an explicit interval with `lower_inclusive` / `upper_inclusive` flags, or require the Markdown intervals verbatim. |
| **m3** | `backend/data/datasets/manifest.json`; protocol §1.3–§1.4, §1.6 | The protocol refers to "registered gaps," but the dataset manifest records only `gap_count` and `gap_bars_total`; it does not list gap start/end locations. The locations exist only in earlier prose audits. | A runner cannot independently verify which buckets are gap-affected from the frozen manifest alone. | Add the seven gap intervals per timeframe to the dataset manifest, or to the new freeze manifest. |
| **m4** | D config line 193; D §6.2 lines 300–302 | `first_session_signal_after: 2021-04-03T00:00:00+00:00` is earlier than the first instant at which a 540-value 4h window is complete. The first complete window ends with the 4h bar opening `2021-04-03T00:00`, which closes at `03:59:59.999`; an ASIA session on 2021-04-03 therefore still reads a budget bar without a full window and is excluded as `warmup_budget`. | The label is imprecise by one 4h bar. It does not admit an extra signal because `warmup_budget` still filters, but the reported warm-up boundary and the config disagree. | State the boundary as "first signal instant strictly after the close of 4h index 552," or use `2021-04-03T04:00:00Z`. |
| **m5** | Protocol §1.4 lines 107–108 | The protocol lists "32 usable 15m bars per session" under "Warm-up exclusions that are *expected* and *not* failures." A 32-bar session-completeness requirement is not an indicator warm-up; it is a session-eligibility rule (and the source of **C1**). | The classification hides a selection rule inside a warm-up allowance, which makes the look-ahead easier to miss. | Move the 32-bar rule out of §1.4 and into the session-eligibility section, with its causality treatment stated. |
| **m6** | B §3.2 lines 198–200; B §7.4 lines 508–511; B §8 lines 538–539 | B says "Sensitivities may vary the ATR multiple only as a pre-declared diagnostic," but no ATR-multiple sensitivity is actually pre-declared. The only pre-declared sensitivities are non-overlap hours and cost bps. | A runner cannot tell which ATR multiples are permitted; adding one would be an undeclared degree of freedom. | Either declare the permitted ATR-multiple sensitivity values, or delete the sentence and state that the ATR multiple is fixed. |
| **m7** | B config line 130; B §7.3–§7.4 lines 500–511 | The config carries `cooldown_primary_hours: 0` beside `canonical_hours: 72`, and the Markdown calls the non-overlap spacing a "cooldown." A runner reading the former literally would apply no spacing. | Potentially material if the key is read instead of `canonical_hours`; the term also conflates a spacing rule with a trading cooldown. | Remove `cooldown_primary_hours` or set it to 72, rename the section "non-overlap spacing," and keep `canonical_hours` as the single source of truth. |
| **m8** | D §10.1 line 491; D config line 247 | The `session_completeness` denominator is "all session buckets in the interval after warm-up." "After warm-up" is undefined: it could mean after the 32-bar session rule, after the 1h ATR warm-up, or after the 540-value 4h budget window. | The diagnostic denominator can change by roughly the first 92 days of sessions, so the reported completeness rate is not unique. | Define the denominator as a concrete timestamp or as `all sessions whose signal instant is inside the development interval and after the budget warm-up`. |
| **m9** | D §4.2 lines 186–191; D config `signal` block | `q` is "the last 1h bar whose `close_time <= signal instant`." If the expected `01:00` / `09:00` / `17:00` bar is missing or unusable, the rule silently selects an earlier 1h bar, but D §4.2 asserts that the expected bar is the selected one and defines no fallback. | Latent. None of those three hours is missing or zero-volume in the registered development gaps, so no demonstrated count change; a future gap could change `ATR1h[q]` without an explicit rule. | State whether a missing expected bar makes the session `warmup_atr` / `unusable_bar`, or selects the prior bar; add a diagnostic count for the fallback. |
| **m10** | Dataset JSON; `backend/app/schemas/market_data.py` line 42 | The dataset stores `is_closed` as the string `"True"` and stores prices, volumes, and `trade_count` as strings. A raw-JSON runner evaluating `row["is_closed"] == True` marks every bar unusable. | Implementation hazard, not a freeze defect: the repository's typed `CandleData` parser coerces the values, but the protocol does not require that parser. | Require a typed loader in the protocol and add a fixture test on the actual on-disk representation. |
| **m11** | B §4.3 lines 275–281; B config line 76 | The `regime_blip` row says a "transient failure between `e` and `c` only" does not invalidate, but permission is evaluated at exactly two 1h bars (`e` and `c`). "Between" does not define an intermediate evaluation cadence, whether `e`/`c` are included, or how a multi-bar failure is counted. | The `regime_blip` diagnostic count is not uniquely computable. It does not change the primary signal set. | Define the intermediate evaluation grid and the exact `regime_blip` condition (for example, any 1h bar in `e+1 .. c-1` with permission not `True`, counted once per episode). |

### 8.4 Severity reconciliation

| severity | count | ids |
|---|---:|---|
| critical | 4 | C1, C2, C3, C4 |
| major | 13 | M1–M13 |
| minor | 11 | m1–m11 |

The presence of any critical finding is sufficient for FAIL under the stated rule. The major findings independently prevent a PASS because several of them can change the signal set or the compliance outcome. The minor findings are listed so that a future freeze does not have to rediscover them.

---

## 9. Minimum remediation for a new freeze

This section is a specification for a **new versioned freeze**, not an instruction to edit the Stage 2E artifacts. The existing files must remain byte-identical so that this audit's hashes continue to identify exactly what was rejected.

### 9.1 Blocking changes

1. **C1 — D session eligibility.** Make signal eligibility depend only on `b0..b7`. Move the 32-bar check to a non-selecting `session_full_data` diagnostic. If the hypothesis genuinely requires a full session, move the signal instant to `s+8h`, rename the latency assumption, and re-derive the entry and stop rules.
2. **C2 — median population.** Compute the verdict median over the pre-gate structurally valid population (B S7, D S6), not over the post-gate population (B S8, D S7). Report `M_all` and `M_feasible` separately, and use `M_all` for the `M > 0.20` / `M <= 0.20` condition. Re-check that the proposed economic thresholds are defined on the same population.
3. **C3 — boundary filtering.** Replace the ISO-string comparison with parsed aware datetimes (or normalize the separator first). Add an executable assertion that every read `open_time` is `>= 2021-01-01T00:00:00Z` and `< 2024-07-01T00:00:00Z`, and a fixture test built from the actual dataset strings.
4. **C4 — causality wording.** Reconcile protocol §1.5 #1 and #5. Define the decision instant explicitly (signal instant or next executable open), state whether a bar closing exactly at that instant is admissible, and add a boundary worked example for D's `q` bar.
5. **M1 — 4h ATR.** Write the complete 4h ATR construction into the protocol: first true range, seed, recursive update, segment reset, and missing-bar handling. Match the explicitness of the 1h ATR.
6. **M2 — entry validity.** Validate only open-time-known properties at entry. Report close-time properties as a post-count data-quality diagnostic. Do not let a future bar property remove a signal that was executable at the open.
7. **M3 — 4h partial buckets.** Either apply the 48-member rule to 4h and segment-break, or add an explicit 4h exemption to protocol §1.3 with a sensitivity using the excluded variant.
8. **M4 — alignment.** Define gap-aware alignment: compare only complete buckets, report missing-member buckets separately, and apply the 0.1% tolerance to complete buckets only.
9. **M5 — B interval end.** Reject any signal whose entry bar opens at or after `2024-07-01T00:00:00Z`, with a dedicated `entry_outside_interval` label.
10. **M6 — D ATR warm-up.** Change "first 14 bars" to "first 13 bars" (or "ATR defined from local index 13") in both the spec and the config.
11. **M7–M9 — B accounting.** Assign `Unknown` to `warmup_regime`; define S4 as episode attempts (including regime failures) or as regime-passed episodes, and rename `permission_share` accordingly; separate `regime_lost` from the structurally valid stage or define S6 before the regime-at-confirmation check.
12. **M10 — capital units.** Define `stop_fraction = D / entry_open`, `notional = risk_usd / stop_fraction`, state the units, and give a numeric impracticability threshold. Recompute the worked examples under the chosen convention.
13. **M11 — cluster unit.** Define the Kish cluster explicitly (boundaries, gap handling, `Unknown` handling) and add a worked example.
14. **M12–M13 — freeze record.** Do not claim zero unresolved critical ambiguities. Record the commit that actually contains the manifest, include the manifest's own SHA256, and carry forward the known-issue list with this audit's finding IDs.
15. **Minor findings m1–m11.** Correct them in the same new freeze; none requires a design change except the `cooldown_primary_hours` removal in **m7**, which should be treated as a safety fix.

### 9.2 Re-freeze procedure

1. Create new documents with a new version (for example `2F.1` or `3.0`); do not edit the Stage 2E files.
2. Recompute SHA256 for every document and dataset after the changes.
3. Write a new manifest that records the containing commit, the manifest's own hash, the dataset gap locations, and the known-issue list.
4. Run a fresh independent audit against the new manifest. This audit cannot be reused as a pass for changed content.
5. Only after that audit returns PASS (or an explicitly approved conditional pass with no critical finding and no material major ambiguity) may a census be authorized.

---

## 10. Audit hygiene and non-modification statement

### 10.1 What was changed

The only repository change made by this audit is the creation of this file, `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`. No Stage 2E artifact, no Stage 2A/2B/2C/2D artifact, no Stage 6/6A artifact, and no Setup 1 artifact was modified, renamed, deleted, or reformatted. The frozen hashes in §1 remain the hashes of the files on disk because those files were not touched.

### 10.2 What was not done

- No census was run.
- No signal was counted or enumerated.
- No backtest, P&L, expectancy, win-rate, drawdown, Sharpe, CAGR, or profitability calculation was performed.
- No parameter was optimized, swept, or tuned.
- No validation or out-of-sample row was used to produce a result.
- No Stage 2G work was started.

### 10.3 Dataset access, stated precisely

The audit did perform the following bounded data operations:

- `sha256sum` over each of the four dataset files and the dataset manifest. This reads every byte of the files but does not parse or interpret market values.
- JSON parsing of `backend/data/datasets/manifest.json` to read counts, hashes, and metadata.
- A **timestamp-encoding check** that inspected only the `open_time` strings of the first record, the `2024-07-01` boundary records, and the last record of the affected files, to confirm the space separator and the presence of boundary rows. No `open`/`high`/`low`/`close`, volume, or `trade_count` value from those records was read, printed, or used.
- No row after the `2024-07-01T00:00:00Z` boundary was inspected for content, and no validation/OOS outcome was computed.

This is a narrower statement than "no dataset row was read." The distinction is deliberate: the audit needed to confirm the on-disk timestamp encoding to establish **C3**, and it did so without processing market data.

### 10.4 Reproducibility

The hash and metadata checks can be reproduced with:

```bash
sha256sum docs/research/STAGE2E_CANDIDATE_B_SPEC.md \
          docs/research/STAGE2E_CANDIDATE_B_CONFIG.json \
          docs/research/STAGE2E_CANDIDATE_D_SPEC.md \
          docs/research/STAGE2E_CANDIDATE_D_CONFIG.json \
          docs/research/STAGE2E_SHARED_CENSUS_PROTOCOL.md \
          docs/research/STAGE2E_INDEPENDENT_REVIEW.md \
          docs/research/STAGE2E_FREEZE_MANIFEST.json \
          backend/data/datasets/manifest.json
sha256sum backend/data/datasets/BTCUSDT-15m-20210101-20260901.json \
          backend/data/datasets/BTCUSDT-1h-20210101-20260901.json \
          backend/data/datasets/BTCUSDT-4h-20210101-20260901.json \
          backend/data/datasets/BTCUSDT-5m-20210101-20260901.json
```

The line references in this report are to the frozen files at the hashes in Appendix A. If a future edit changes a line number, the finding ID, not the line number, is the stable identifier.

### 10.5 Limitations

This is a documentation and repository-identity audit. It establishes that the frozen rules are inconsistent, under-specified, or non-causal in the ways listed. It does **not** estimate how many signals would be affected, because that would require the census this audit is withholding. It also does not guarantee that correcting the listed items is sufficient; a new freeze needs its own independent audit.

---

## Appendix A — Frozen hash record

| artifact | SHA256 |
|---|---|
| `STAGE2E_CANDIDATE_B_SPEC.md` | `13762985a31ecb3364c4fd7c2c66d1bafdc627d526177fbdb04601ef619c3104` |
| `STAGE2E_CANDIDATE_B_CONFIG.json` | `4253b32b4305434fec196c6e9c720c144b4572a109958d4bd5f1125f78086574` |
| `STAGE2E_CANDIDATE_D_SPEC.md` | `49668b4ff377c913a6c70027813bbbd0b39d57b7eaa94954130e32319a7e7277` |
| `STAGE2E_CANDIDATE_D_CONFIG.json` | `97dee773afe996dd179f015b9c787db4a5bd578ffaeb6881f5808c5fc92c6765` |
| `STAGE2E_SHARED_CENSUS_PROTOCOL.md` | `3afd1e915b3ce27966673d30d25ea59763192b5869e8857712668ec94a7f1f78` |
| `STAGE2E_INDEPENDENT_REVIEW.md` | `3f59a8c2365676fc15b8a069e78600776aa4ecd1a176d3245ca9f1f2c6738cc9` |
| `STAGE2E_FREEZE_MANIFEST.json` | `b26ef6d56665908aaf74e72e56aff0a6f36fab2a682b5de7926d5fc3385eac65` |
| `backend/data/datasets/manifest.json` | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` |
| `BTCUSDT-15m-20210101-20260901.json` | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` |
| `BTCUSDT-1h-20210101-20260901.json` | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` |
| `BTCUSDT-4h-20210101-20260901.json` | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` |
| `BTCUSDT-5m-20210101-20260901.json` | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` |

## Appendix B — Finding-to-evidence map

| finding | primary evidence |
|---|---|
| C1 | D §2.2 lines 112–119; D §3 line 137; D §4.2 line 208; D §10 line 456; protocol §1.5 #1/#4 lines 114–119 |
| C2 | B §9 line 556; B §11.1 line 664; D §10 line 461; D §12 line 574; verdict tables B §11.1 lines 669–672, D §12 lines 579–582 |
| C3 | B §1 lines 69–72; D §1 lines 76–78; protocol §1.2 lines 69–77; dataset `open_time` encoding and boundary rows |
| C4 | protocol §1.5 #1 lines 114–115 and #5 line 120; D §4.2 lines 186–191; D §6.2 lines 296–298 |
| M1 | B §4.2 line 224; D §6.2 line 268; configs' `atr_period` / `atr_method` |
| M2 | B §5.5 lines 356–364; D §7.1 lines 320–328; protocol §1.3 |
| M3 | protocol §1.3 lines 79–92; B §2.3 lines 121–127; D §2.3 lines 121–127; Stage 2C §5.1 |
| M4 | protocol §1.6 lines 124–140; dataset gap counts; Stage 2C §5.1 |
| M5 | B §5.5 lines 370–372; B §1, §12 |
| M6 | D §4.2 lines 211–212; D config `atr_1h` / `warmup`; B §3.1 lines 146–147 |
| M7 | B §4.3 line 274; B §9 lines 566–567 |
| M8 | B §9 line 552; B §4.3 line 274; B §9.1 `permission_share` |
| M9 | B §9 line 554; B §9 line 572; B §9.1 `retest_conversion` |
| M10 | B §10 item 10 line 622; D §11 item 11 line 525; B §5.6 line 379; D §7.2 line 338; worked examples |
| M11 | B §10 items 7–8 lines 615–619; D §11 items 8–9 lines 519–522; protocol §3.1 line 204 |
| M12 | `STAGE2E_FREEZE_MANIFEST.json` line 48; `STAGE2E_INDEPENDENT_REVIEW.md` lines 6–7, 101 |
| M13 | `STAGE2E_FREEZE_MANIFEST.json` line 5, line 197; commit `6f8db24` parent `f8000e0` |
| m1 | B §9 line 550; B §3.1 line 155 |
| m2 | B §8 line 533; D §7.3 line 358; B config line 142; D config line 185 |
| m3 | `backend/data/datasets/manifest.json`; protocol §1.3–§1.4, §1.6 |
| m4 | D config line 193; D §6.2 lines 300–302 |
| m5 | protocol §1.4 lines 107–108 |
| m6 | B §3.2 lines 198–200; B §7.4 lines 508–511; B §8 lines 538–539 |
| m7 | B config line 130; B §7.3–§7.4 lines 500–511 |
| m8 | D §10.1 line 491; D config line 247 |
| m9 | D §4.2 lines 186–191; D config `signal` |
| m10 | dataset JSON; `backend/app/schemas/market_data.py` line 42 |
| m11 | B §4.3 lines 275–281; B config line 76 |

---

**Final determination: FAIL.** The Stage 2E freeze is hash-intact but not decision-ready. No census is authorized. A new versioned freeze is required after explicit approval, followed by a new independent audit.
