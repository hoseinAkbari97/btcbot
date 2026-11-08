# Stage 2K — Historical Research Synthesis

**Stage:** 2K (historical research review and next-hypothesis selection).
**Nature:** review and research design only. No strategy was developed, no candidate was specified,
no census was run, no market-data row was processed, no backtest or performance statistic was
computed, and no frozen artifact was modified.
**Review date:** 2026-11-08 (UTC).
**Repository HEAD at review start:** `3db4a7e86ba1cbaf872e83bbf2c745090d823352` (`main`, clean,
0 ahead / 0 behind `origin/main`).
**Frozen baseline reviewed:** `docs/research/stage2e_v2/`, version `2.0.0`, manifest SHA256
`adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7`.

Evidence labels used throughout Stage 2K:

- **Verified fact** — directly supported by an existing repository artifact, cited by path and section.
- **Interpretation** — a reasoned explanation of verified facts; not itself recorded history.
- **Hypothesis** — a possible explanation not established by the record.
- **Unknown** — not available in the existing research.

---

## 0. What this document is

This document reconstructs what the project actually measured, from the artifacts in the repository,
for the four candidate hypotheses named in the Stage 2K brief:

| short label | hypothesis named in the Stage 2K brief |
|---|---|
| **A** | Multi-timeframe trend pullback continuation |
| **B** | Expansion / displacement and retest |
| **C** | Compression breakout |
| **D** | Session-based momentum |

It preserves each historical verdict exactly, separates what was demonstrated from what was not, and
records artifact limitations rather than reconstructing missing evidence from memory.

It does **not** claim that any candidate is unprofitable. No artifact in the reviewed record contains
a trade outcome, a P&L figure, an expectancy, a win rate, a drawdown, a Sharpe or Sortino ratio, a
CAGR, an equity curve, a bootstrap interval, or a Monte Carlo result. **No candidate in this project
has ever been performance-tested** (Verified fact: all census artifacts state this explicitly, for
example `docs/research/stage2j/STAGE2J_FINAL_DECISION.md` §3 and
`docs/research/STAGE2C_FEASIBILITY_CENSUS.md` §12).

---

## 1. Repository state and artifact inventory

### 1.1 Verified repository state at review start

| item | observed value | source |
|---|---|---|
| branch | `main` | `git` |
| HEAD | `3db4a7e86ba1cbaf872e83bbf2c745090d823352` | `git rev-parse HEAD` |
| remote tracking | `origin/main`, 0 ahead / 0 behind | `git rev-list --left-right --count` |
| working tree | clean before Stage 2K work | `git status --porcelain` |
| last five commits | Stage 2J documentation commits | `git log` |

The repository was therefore **not** at the census-code commit `bc1285c8277c37c93b76addfe83dcb50267c1f35`
recorded for the Stage 2J run. HEAD `3db4a7e` is downstream of it and adds documentation only
(Verified fact: reverting to `bc1285c` would remove the Stage 2J reports and manifest).

### 1.2 Research stage lineage actually present

| stage | artifacts present | outcome recorded |
|---|---|---|
| 2A | `STAGE2A_FEASIBILITY_CENSUS.md/.json`, `STAGE2A_DATA_ALIGNMENT_AUDIT.md`, `stage2a_census/` | Candidate C failed |
| 2B | `STAGE2B_STRATEGY_DISCOVERY.md`, `STAGE2B_STRATEGY_RECOMMENDATION.md` | candidate A proposed for census; B, C, D only designed |
| 2C | `STAGE2C_FEASIBILITY_CENSUS.md/.json`, `STAGE2C_DATA_ALIGNMENT_AUDIT.md`, `stage2c_census/` | Candidate A failed |
| 2D | `STAGE2D_STRATEGY_REDESIGN.md`, `STAGE2D_STRATEGY_RECOMMENDATION.md` | candidates B and D recommended |
| 2E (v1) | `STAGE2E_*` specs, configs, protocol, `STAGE2E_FREEZE_MANIFEST.json` | freeze only |
| 2F | `STAGE2F_INDEPENDENT_FREEZE_AUDIT.md` | v1 freeze **FAIL**, 4 critical defects |
| 2G | `stage2e_v2/*` version `2.0.0`, `REMEDIATION_MATRIX.md`, `INDEPENDENT_REVIEW.md` | remediation, self-review only |
| 2H | `STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md` | conditional pass, self-audit limitation disclosed |
| 2I | `stage2i/*` | readiness + owner ratification of K0–K4 |
| 2J | `stage2j/*` | Candidates B and D failed |

### 1.3 Missing or unmeasured objects

The following are recorded as limitations, not reconstructed:

1. **No census exists for the Stage 2B definitions of B, C and D.** Stage 2B designed four hypotheses;
   only its Candidate A was censused (Stage 2C). The Stage 2B B/C/D designs were superseded by the
   Stage 2D relabelling before any count.
2. **No census exists for the Stage 2D definitions of A and C.** Stage 2D recommended B and D;
   its A (multi-day time-series momentum) and C (longer-horizon regime-conditioned mean reversion)
   were rejected on calendar arithmetic and mechanism, not measured.
3. **No outcome experiment exists for any candidate.** No trade was ever entered or resolved in the
   reviewed record.
4. **No Stage 2E version 1 census exists.** The v1 freeze was rejected by the Stage 2F audit before
   counting, so the v1 numbers do not exist and must not be inferred from v2.
5. **Stage 2J's `FREEZE_MANIFEST.json` records `"stage2k_started": false`** (Verified fact: tail of
   `docs/research/stage2j/FREEZE_MANIFEST.json`). Stage 2K begins from that stop point.

---

## 2. Naming provenance: the labels were reused

This is a material audit finding. The labels A, B, C and D do **not** identify one object each across
the project's history. Any comparison that ignores this will misattribute results.

### 2.1 The four objects reviewed in Stage 2K

| label | exact object | frozen / censused in |
|---|---|---|
| **A** | 4h SMA200 + 20-bar slope regime; 1h EMA20 crossunder pullback; strict close above the pre-crossunder high; structural stop at the pullback low; 120h non-overlap | specified Stage 2B §2.1 / Stage 2B recommendation §3; frozen and censused **Stage 2C** |
| **B** | 1h expansion (TR ≥ 2.0 × ATR(14), body ≥ 0.55 of range, close in top 25%); 4h permission (close > SMA50, 24h slope > 0, ATR percentile 20–95); retest within 1–6 bars; resumption confirmation; structural stop; **72h** canonical non-overlap | Stage 2D §1; frozen `stage2e_v2/` version `2.0.0`; censused **Stage 2J** |
| **C** | 4h compression (RV5/RV20 ≤ 0.60, volume ratio ≤ 0.80, duration ≥ 6 bars) then close above the episode high; structural stop at the episode low; 18-bar (3-day) hold | Strategy 2 recommendation §4; censused **Stage 2A** |
| **D** | 15m UTC-session first-two-hour return ≥ 0.5 × ATR(14, 1h) / P0 and P1 > session VWAP; 4h ATR percentile budget 25–80; stop = 1.0 × 1h ATR; **24h** canonical non-overlap | Stage 2D §1; frozen `stage2e_v2/` version `2.0.0`; censused **Stage 2J** |

### 2.2 Confusable prior labels that must not be merged

| label as used earlier | object it denoted | measured? |
|---|---|---|
| Stage 2B **B** | regime-conditioned mean reversion (long-only) | **never censused** |
| Stage 2B **C** | local market-structure change in HTF direction | **never censused** |
| Stage 2B **D** | HTF regime + liquidity-zone reaction | **never censused** |
| Stage 2D **A** | multi-day time-series momentum, 20–30 day horizon | **never censused**; rejected on a 63-episode calendar cap |
| Stage 2D **C** | longer-horizon regime-conditioned mean reversion | **never censused**; estimated 10–30 episodes |
| Strategy 2 **A** | Donchian(20) breakout above SMA200, 1.5×ATR(20) stop, 30-bar / 10-bar-low exit | counted only as a **fallback check** in Stage 2A §5 |
| Strategy 2 **B** | mean reversion | screened in Stage 2B, **never censused** |

**Verified fact:** Strategy 2 Candidate A's fallback check is reported in
`docs/research/STAGE2A_FEASIBILITY_CENSUS.md` §5: 271 raw, 237 cost-feasible, 170 unique, **76
non-overlapping** at a 5-day hold, median `cost_R` 0.122. It is a different hypothesis from the
Stage 2C Candidate A (71 non-overlapping at 120h), and the two must not be combined.**Interpretation:** the relabelling is a documentation hazard, not a computational error. It does,
however, mean that statements such as "Candidate B was tested" are only meaningful when the stage is
named. Stage 2K therefore always cites the stage together with the label.

---

## 3. Historical candidate comparison

Every row below is a **structural feasibility** result. None is a profitability result.

| Candidate | Original hypothesis | Research stage | Main feasibility result | Principal failure or limitation | Final status |
|---|---|---|---|---|---|
| **A** | In a higher-timeframe uptrend, price pulls back to a lower-timeframe reference and resumes; enter on resumption with a structural stop | specified Stage 2B, censused Stage 2C | 644 crossunder episodes → 445 confirmed → 195 regime-eligible → 151 cost-feasible unique → **71 non-overlapping (120h)**; median `cost_R` 0.1032 pre-gate / 0.0898 feasible; feasible share 0.774 | Frequency. 71 is below the 150 floor and far below 349; the 4h regime filter removes 250 of 445 confirmed triggers and the 120h overlap rule removes 80 of 151 feasible signals | **FAIL — insufficient non-overlapping opportunity frequency** |
| **B** | A directional volatility expansion continues after a shallow retest, permitted only in a qualified 4h regime | Stage 2D design; Stage 2E v1 freeze → 2F audit FAIL → 2G v2; Stage 2J census | 30,625 usable 1h bars → 503 expansions → 458 episode attempts → 117 regime-qualified → 34 structurally valid → 32 pre-gate → 29 cost-feasible → **24 non-overlapping (72h)**; `M_all` 0.086505; feasible share 0.906 | Frequency, not cost. Only 24 canonical opportunities; the regime gate removes 341 of 458 attempts and structural validation removes 83 of 117 regime-qualified attempts | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** |
| **C** | A sustained volatility and volume compression resolves with a confirmed breakout that continues | Strategy 2 selection; censused Stage 2A | 7,662 4h bars → 461 compression episodes → **63** with duration ≥ 6 bars → 17 breakouts → **12 cost-feasible unique**; median `cost_R` 0.124; 3.4 events/year | Frequency, and it is structural: the 63-episode duration floor is below the 200 gate even before breakout and cost rejection | **FAIL — insufficient economic or statistical feasibility** |
| **D** | BTC shows session-relative intraday continuation in normal-volatility conditions; the first two hours of a UTC session predict the rest of the session | Stage 2D design; frozen in `stage2e_v2/` v2; Stage 2J census | 3,829 evaluable sessions → 927 directional → 332 budget-qualified → 296 above VWAP → 295 pre-gate → **45 cost-feasible** → **34 non-overlapping (24h)**; `M_all` 0.322559; feasible share 0.153 | Two independent failures: frequency (34 < 150) and cost geometry (`M_all` 0.3226 > 0.20). 250 of 295 pre-gate sessions fail the 26 bp gate; no cost-feasible signal occurs after 2022-09 | **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES** (concentration criterion also met, lower precedence) |

**Verified fact — threshold drift across stages.** Stage 2A gated Candidate C on **≥ 200** economically
feasible unique events (`STAGE2A_FEASIBILITY_CENSUS.md` §1). Stage 2C onwards used **150** as the
project floor (`STAGE2C_FEASIBILITY_CENSUS.md` §13; `stage2e_v2/CANDIDATE_B_SPEC.md` §11.1). The
Stage 2D provenance audit records 150 as first appearing in the Stage 2C freeze, with no statistical
derivation (`STAGE2D_STRATEGY_RECOMMENDATION.md` §9 item 1). The two floors are not interchangeable
and Stage 2K does not reinterpret either.

**Verified fact — calendar ceilings were not the binding limit for B, C or D.** The development
interval is 1,277 days (`STAGE2C_FEASIBILITY_CENSUS.md` §2.1). At the frozen horizons the maximum
numbers of non-overlapping windows are 425 (72h), 1,277 (24h) and 255 (120h). B reached 24 of 425
(5.6%), D 34 of 1,277 (2.7%), C 12 of an episode ceiling of 63, and A 71 of 255 (27.8%). Only A loses
a large share of its feasible population to the overlap rule (80 of 151).

---

## 4. Candidate A — multi-timeframe trend pullback continuation

### 4.1 What the hypothesis intended to capture

A higher-timeframe uptrend offers continuation entries on a lower-timeframe pullback that resumes in
the trend direction, with a structural stop beyond the pullback extreme. The proposed economic
mechanism was gradual information diffusion and risk-management flows producing shallow pullbacks
inside trends (`STAGE2B_STRATEGY_DISCOVERY.md` §2.1; `STAGE2B_STRATEGY_RECOMMENDATION.md` §2). The
design deliberately differed from Setup 1 (a sweep-and-rejection reversal) and from a pure breakout.

### 4.2 What the frozen rules actually required

From `docs/research/STAGE2C_FEASIBILITY_CENSUS.md` §2:

- 4h regime: `close > SMA200` **and** `SMA200[t] > SMA200[t-20]`, read from the most recent 4h bar
  closing before the 1h bar opens.
- Pullback: 1h close crosses below EMA20; reference high `R` is the last 1h high at or above the EMA.
- Resumption: strict 1h close above `R`, strictly after the crossunder.
- Invalidation: regime flip before confirmation, 72-bar pullback age, or 15% pullback depth.
- Entry: open of the 5m bar one hour after the confirmation bar.
- Stop: the pullback low `L`; `cost_R = 0.0026 × entry / (entry − L) ≤ 0.20`.
- Deduplication: one signal per pullback episode; canonical overlap rule 120h (24h and 168h as
  diagnostics).

### 4.3 What the research measured

| quantity | value | source |
|---|---:|---|
| crossunder episodes / confirmed triggers | 644 / 445 | Stage 2C §4 |
| primary-eligible triggers after the 4h regime filter | 195 | Stage 2C §4 |
| cost-feasible unique signals | 151 | Stage 2C §4 |
| canonical non-overlapping (120h) | **71** | Stage 2C §13 |
| per active year | 20.9 | Stage 2C §6 |
| median `cost_R`, valid triggers (n=195) | 0.1032 | Stage 2C §5.1 |
| median `cost_R`, feasible only (n=151) | 0.0898 | Stage 2C §5.1 |
| feasible share | 0.774 | Stage 2C §1 |
| median stop, valid triggers | 2.520% | Stage 2C §5.2 |
| largest regime-episode share | 13.9% | Stage 2C §8.1 |
| Kish `n_eff` / design effect | 12.69 / 11.9 | Stage 2C §8.1 |

### 4.4 What the evidence demonstrated

**Verified fact:** this frozen instantiation produced 71 non-overlapping cost-feasible opportunities
over 3.396 active years. That is below the 150 floor on every pre-registered view: 151 raw feasible
signals, 71 non-overlapping at 120h, 24 signal-producing regime episodes, and a Kish effective size
of 12.69. Even the most generous count implies a smallest detectable effect of 0.228R at 80% power,
above the 0.15R target (Stage 2C §8.3).

**Verified fact:** cost geometry was not the binding failure. The feasible share was 0.774 and the
feasible median `cost_R` was 0.0898.

**Verified fact:** the 4h regime filter roughly halved frequency (445 → 195 confirmed triggers;
342 → 151 feasible; 156 → 71 non-overlapping in the control comparison), and the 120h non-overlap
rule removed 80 of 151 feasible signals (Stage 2C §7).

### 4.5 What the evidence did not demonstrate

- It did not show that trend pullbacks fail to continue. No outcome was observed.
- It did not show the control (unconditioned 1h pullback stream) is profitable. The control reached
  150 non-overlapping signals on the matched window, but the report explicitly states it is **not
  promoted** and is a selectivity diagnostic, not an alternative strategy (Stage 2C §1, §7).
- It did not identify the dependence structure of outcomes, because no outcome was computed.
- It did not establish that a different 4h regime definition, pullback definition, or 120h horizon
  would produce more opportunities. Those variants were not counted.

### 4.6 Why the candidate failed its applicable criteria

The decision rule required `N_non_overlapping ≥ 150`. The measured count was 71. Median `cost_R`
and feasible share both passed. The recorded verdict is therefore **FAIL — insufficient
non-overlapping opportunity frequency** (Stage 2C §13), and the stated next action was a new
hypothesis selection, not a gate relaxation or a pullback parameter search.

---

## 5. Candidate C — compression breakout

### 5.1 What the hypothesis intended to capture

A sustained contraction in realised volatility and volume identifies a coiled state whose upward
resolution continues. The registered claim had two parts: the breakout must be profitable after the
frozen cost model, **and** it must beat unconditioned 20-bar-high breakouts, so that the compression
state is doing identifiable work (`STRATEGY_2_RECOMMENDATION.md` §1).

### 5.2 What the frozen rules actually required

From `STAGE2A_FEASIBILITY_CENSUS.md` §2.4:

- 4h closed bars only.
- `compression_ratio = RV5 / RV20 ≤ 0.60`, using the platform's realised-volatility definition
  (sample standard deviation of trailing price differences).
- `volume_ratio = volume / mean(volume, 20) ≤ 0.80`, mean over the 20 bars strictly before the bar.
- A compression episode is a maximal run of tight bars; eligible only if `duration_bars ≥ 6`.
- Trigger: at the bar the episode ends, `close > max(high)` over the episode.
- Entry: open of the first 5m bar after the trigger bar closes.
- Stop: the episode's `min(low)`.
- Cost gate: `cost_R ≤ 0.20` at 26 bp.
- Target 2R and an 18-bar (72h) maximum hold were recorded but never simulated.

### 5.3 What the research measured

| quantity | value | source |
|---|---:|---|
| valid 4h bars | 7,662 | Stage 2A §3.1 |
| compression episodes | 461 | Stage 2A §3.1 |
| episodes with duration ≥ 6 bars | **63** | Stage 2A §3.1 |
| confirmed upside breakouts | 17 | Stage 2A §3.1 |
| cost-feasible unique events | **12** | Stage 2A §3.1 |
| events per year (feasible) | 3.4 | Stage 2A §3.2 |
| median `cost_R`, all triggers | 0.124 | Stage 2A §3.3 |
| median stop, all triggers | 2.10% | Stage 2A §3.3 |
| control non-overlapping (3-day hold) | 136 | Stage 2A §4.2 |

### 5.4 What the evidence demonstrated

**Verified fact:** the sample ceiling is 63, because only 63 episodes in 3.5 years clear the six-bar
duration floor. Even a 100% breakout rate with no cost rejection could not reach 200 (Stage 2A §7).

**Verified fact:** the failure is not an artifact of the cost assumption. At 10 bp all 17 triggers
pass the 0.20 gate; the best case is still 17 events. Relaxing the gate to 1.00R also yields 17
(Stage 2A §3.3, §6.1).

**Verified fact:** the conditioning does select a different event set from unconditioned 20-bar-high
breakouts: 13 of 17 triggers were not 20-bar-high breakouts (Stage 2A §4.3). The mechanism was
observable; it was not observable often enough to support inference.

### 5.5 What the evidence did not demonstrate

- It did not show that compression breakouts are unprofitable.
- It did not establish a clean comparison with the control: the control arm's structural stop was
  undefined in the design and a provisional 20-bar-low stop was substituted, which is generous to
  the control because its stops are about four times wider (Stage 2A §4.1).
- It did not measure the 4h-signal / 5m-execution machinery under an outcome experiment; causality
  was argued structurally, and the look-ahead harness was not run (Stage 2A §9).
- It did not characterise regime composition; with 12 events that analysis would be meaningless.

### 5.6 Why the candidate failed its applicable criteria

The Stage 2A gate required ≥ 200 economically feasible unique events and `median cost_R ≤ 0.20`. The
cost condition passed (0.124) and the count failed by a factor of about 17 (12 vs 200). The recorded
verdict is **FAIL — insufficient economic or statistical feasibility** (Stage 2A §1).

---

## 6. Candidate B — expansion / displacement and retest

### 6.1 What the hypothesis intended to capture

A large directional 1h expansion, taken only when a 4h regime permits it, continues after a shallow
retest. The mechanism proposed was that fades of the first expansion and late entrants create
continuation, while a retest filters for confirmation (`STAGE2D_STRATEGY_RECOMMENDATION.md` §3). It
was deliberately the inverse state of Candidate C: expansion-after-event rather than
compression-before-breakout.

### 6.2 What the frozen rules actually required

From `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md`:

- Expansion bar: `TR[t] ≥ 2.0 × ATR(14)[t-1]`, `body/range ≥ 0.55`, close location ≥ 0.75, close > open.
- 4h permission at the expansion bar and again at confirmation: `close > SMA50`, `SMA50[q] − SMA50[q−6] > 0`,
  and 4h ATR percentile in `[20, 95]` over a 540-bar window.
- Retest: first bar in `e+1 … e+6` with `low ≤ L_e + 0.25 × A_e`; penetration limited to `0.50 × A_e`.
- Resumption: first bar `c` with `r < c ≤ r+3`, `close > L_e`, `close > open`.
- Stop: lowest low from `e` through `c`; entry at the next 1h open.
- Cost gate `cost_R ≤ 0.20` at 26 bp; canonical non-overlap **72h**.
- One active episode at a time; a permission failure at `e` still occupies the slot (implementation
  choice B-1, recorded before counting in `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md`).

### 6.3 What the research measured

| quantity | value | source |
|---|---:|---|
| usable 1h bars / expansion-testable | 30,625 / 30,513 | Stage 2J B report §2 |
| expansion bars / episode attempts | 503 / 458 | Stage 2J B report §2 |
| regime-qualified attempts | 117 | Stage 2J B report §2 |
| structurally valid episodes / pre-gate | 34 / 32 | Stage 2J B report §2 |
| cost-feasible / deduplicated | 29 / 29 | Stage 2J B report §2 |
| canonical 72h non-overlapping | **24** | Stage 2J B report §2 |
| `M_all` (pre-gate median `cost_R`, n=32) | 0.086505 | Stage 2J B report §4 |
| `M_feasible` (n=29) | 0.074808 | Stage 2J B report §4 |
| feasible share | 0.906250 | Stage 2J B report §4 |
| largest cluster share / design effect | 0.103448 / 1.689655 | Stage 2J B report §6 |
| max notional on verdict population | 0.696012 (69.60% of equity) | Stage 2J B report §7 |

### 6.4 What the evidence demonstrated

**Verified fact:** the candidate produced 24 canonical non-overlapping opportunities, below the 150
floor on every pre-registered non-overlap variant (24h: 29; 72h: 24; 120h: 23).

**Verified fact:** cost was not the binding constraint. `M_all = 0.086505` is comfortably below 0.20,
the feasible share is 0.906, and at 10 bp all 32 pre-gate signals would pass.

**Verified fact:** the conjunction, not the overlap rule, removed most of the population. Of 458
episode attempts, 341 were rejected by the 4h regime condition at the expansion bar; of the 117
regime-qualified attempts, 83 failed structural validation (Stage 2J B report §3).

**Verified fact:** protocol compliance passed, no capital-geometry violation was found on the
cost-feasible population, and the concentration screen was not met (largest share 10.34%, design
effect 1.69). The non-decision 4h supplied-bar sensitivity reduced the canonical count to 18 without
changing the verdict direction (Stage 2J B report §9).

### 6.5 What the evidence did not demonstrate

- It did not show that expansion continuation is unprofitable or has no edge.
- It did not show that a different ATR multiple, retest window, percentile band, or 4h permission
  rule would pass. No such variant was counted in the decision path; a variant search after seeing
  24 would be a new, post-hoc hypothesis.
- It did not establish independence between the 24 opportunities. They are non-overlapping by
  construction, not independent.
- It did not validate the 26 bp cost against any venue.

### 6.6 Why the candidate failed its applicable criteria

`N_nonoverlap = 24 < 150`, so the frozen decision rule returns `FAIL`; the tier label is `FAIL`
because `N < 349`. The recorded Stage 2J verdict is **FEASIBILITY FAIL — INSUFFICIENT
OPPORTUNITIES** (`stage2j/STAGE2J_FINAL_DECISION.md` §1).

---

## 7. Candidate D — session-based momentum

### 7.1 What the hypothesis intended to capture

BTC shows session-relative intraday continuation in normal-volatility conditions: a strong first two
hours of a UTC session predicts the remainder of that session. The design was explicitly a
**research convention**, not a claim that the equity-index intraday-momentum result transfers to BTC
(`stage2e_v2/CANDIDATE_D_SPEC.md` §0.1). A 4h volatility budget was added to exclude crisis and dead
states.

### 7.2 What the frozen rules actually required

From `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md`:

- Three fixed UTC sessions of eight hours: ASIA `[00:00, 08:00)`, EUROPE `[08:00, 16:00)`, US
  `[16:00, 24:00)`.
- Measurement window: the first eight 15m bars. `r2 = open[b0] → close[b7]`.
- Threshold: `r2 ≥ 0.5 × ATR1h(14)[q] / P0`, where `q` is the 1h bar closing at the signal instant.
- Direction filter: `P1 > session VWAP`, VWAP from HLC3 and volume over the same eight bars.
- Volatility budget: 4h ATR percentile in `[25, 80]` over a 540-bar window.
- Entry: next 15m open. Stop: `entry − 1.0 × ATR1h[q]`.
- Cost gate `cost_R ≤ 0.20` at 26 bp; canonical non-overlap **24h**; one signal per session.

### 7.3 What the research measured

| quantity | value | source |
|---|---:|---|
| session buckets / signal-evaluable | 3,831 / 3,829 | Stage 2J D report §2 |
| directional signals | 927 | Stage 2J D report §2 |
| volatility-budget-qualified | 332 | Stage 2J D report §2 |
| VWAP-valid / pre-gate valid entry-stop | 296 / 295 | Stage 2J D report §2 |
| cost-feasible | **45** (250 rejected by the gate) | Stage 2J D report §2–§4 |
| canonical 24h non-overlapping | **34** | Stage 2J D report §2 |
| `M_all` (pre-gate, n=295) | 0.322559 | Stage 2J D report §4 |
| `M_feasible` (n=45) | 0.165085 | Stage 2J D report §4 |
| feasible share | 0.152542 | Stage 2J D report §4 |
| largest cluster share / design effect | 0.177778 / 3.933333 | Stage 2J D report §6 |
| canonical signals by year | 2021: 18, 2022: 16, then none | Stage 2J D report §6 |
| max notional on verdict population | 0.760891 (76.09% of equity) | Stage 2J D report §7 |

### 7.4 What the evidence demonstrated

**Verified fact:** the candidate failed two independent insufficient-opportunity sub-conditions:
`N = 34 < 150`, and `M_all = 0.322559 > 0.20`. The cost gate rejected 250 of 295 pre-gate sessions.

**Verified fact:** the concentration criterion was also met on the primary S7 population (design
effect 3.93 ≥ 2.00), although the largest-cluster share was 17.78%, below the 50% component. Because
`INSUFFICIENT OPPORTUNITIES` has higher pre-declared precedence, that is the recorded verdict.

**Verified fact:** the canonical signal set is concentrated in 2021–2022; no cost-feasible signal
occurs after 2022-09 under the frozen rules. The additional views are also concentrated: session id
largest share 35.6% (design effect 15.13), calendar quarter 37.8% (design effect 11.62).

**Verified fact:** protocol compliance passed, the capital-geometry check passed on the cost-feasible
population (the pre-gate diagnostic shows 208 of 295 above 100% notional), and the 4h supplied-bar
sensitivity preserved both failure directions (22 canonical, `M_all` 0.356311, design effect 3.43).

### 7.5 What the evidence did not demonstrate

- It did not show that session-relative continuation is absent in BTC.
- It did not show that a cheaper venue would make D testable. The 10 bp sensitivity shows 253 of 295
  pre-gate sessions would pass the gate, but the non-overlap count at that cost was not computed, so
  the opportunity consequence is **Unknown**.
- It did not show that the 1h-ATR stop is the wrong stop. It shows that at 26 bp the stop is too
  tight for the gate in 84.7% of pre-gate sessions.
- It did not establish independence among the 34 canonical signals, and the concentration diagnostics
  suggest the opposite risk.

### 7.6 Why the candidate failed its applicable criteria

The Stage 2J decision rule fails a candidate if `N < 150` **or** `M_all > 0.20`. D satisfies both.The recorded verdict is **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES**; the concentration criterion is
reported but does not change the verdict because of precedence (`stage2j/STAGE2J_SUMMARY_AND_VERDICT.md`
§1–§2).

---

## 8. Cross-candidate structural comparison

The four censuses counted different objects and must not be read as a leaderboard. The table records
where each population was lost.

| item | A | B | C | D |
|---|---|---|---|---|
| counting unit | 1h pullback episode | 1h expansion episode | 4h compression episode | UTC session |
| primary population | 644 crossunders | 458 episode attempts | 461 episodes | 3,829 evaluable sessions |
| dominant loss | 4h regime: 250 of 445 confirmed (56.2%) | 4h regime: 341 of 458 attempts (74.5%) | duration floor: 398 of 461 episodes (86.3%) | cost gate: 250 of 295 pre-gate (84.7%) |
| second loss | 120h overlap: 80 of 151 feasible (53.0%) | structural validation: 83 of 117 regime-qualified (70.9%) | trigger: 46 of 63 episodes (73.0%) | threshold: 2,902 of 3,829 sessions (75.8%) |
| canonical `N` | 71 | 24 | 12 | 34 |
| pre-gate median `cost_R` | 0.1032 (n=195) | 0.086505 (n=32) | 0.124 (n=17) | 0.322559 (n=295) |
| cost gate binding? | no (44 of 195 failed) | no (3 of 32 failed) | no (5 of 17 failed) | **yes** (250 of 295 failed) |
| reported rate | 20.9 / active year | ≈ 7.4 / year (derived) | 3.4 / year | ≈ 10.5 / year (derived) |
| calendar ceiling at frozen horizon | 255 (120h) | 425 (72h) | 63 episodes (state cap) | 1,277 (24h) |
| verdict | FAIL — frequency | FAIL — insufficient opportunities | FAIL — economic/statistical feasibility | FAIL — insufficient opportunities |

The B and D per-year rates are derived by Stage 2K from the reported canonical counts and the
92-day 4h warm-up (`stage2e_v2/CANDIDATE_B_SPEC.md` §4.2), not reported by the censuses. They are
**Interpretation**, not historical fact.

**Interpretation:** the funnels differ in where they lose the population, but all four lose it before
the opportunity floor. Two candidates (A, B) are throttled mainly by a regime conjunction; one (C)
by the rarity of the state itself; one (D) by stop geometry against the cost proxy. That pattern is
more consistent with a family-level opportunity-density problem than with a single faulty rule.

---

## 9. Evidence limitations

1. **No outcome was ever observed.** Every verdict is a structural feasibility verdict. None
   establishes or refutes an edge, and none is a profitability statement.
2. **The v2 freeze was self-audited.** Stage 2H was written by the same agent that performed the
   Stage 2G remediation (`STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md` independence disclosure). Stage 2I
   accepted it as the audit of record with that limitation explicit; no third-party audit exists
   (`stage2i/OWNER_RATIFICATION.md` §1).
3. **Version 1 of the freeze was rejected.** Stage 2F found four critical defects, including future
   data in D's eligibility rule and a vacuous cost condition (`STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`
   §0). Version 2 remediated them and was audited at Stage 2H. Version 1 was never counted.
4. **The cost model is a proxy.** 26 bp round trip is a Binance estimate of fees plus adverse
   execution, not a measured Nobitex cost (all candidate specs; `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md`
   §4).
5. **One development interval, one market path.** `[2021-01-01, 2024-07-01)` covers a bull phase, a
   bear phase and a recovery, but it is a single realised history and no resampling or outcome-based
   dependence estimate exists.
6. **The decision thresholds are project choices.** The 150 floor was fixed at the Stage 2C freeze
   with no derivation; the 349 figure assumes independent observations at 0.15R, 1R standard
   deviation, 5% two-sided and 80% power; `cost_R ≤ 0.20` and the concentration screen are protocol
   choices. None is a market fact (Verified fact: `stage2e_v2/CANDIDATE_B_SPEC.md` §0.1, §11.3;
   `stage2j/machine_readable/verdict_inputs.json` fields `project_floor_status` and
   `reference_status`).
7. **Thresholds drifted between stages.** Stage 2A used ≥ 200; Stage 2C onwards used 150. The two
   cannot be compared directly, and Stage 2K does not restate either as a standard.
8. **Labels drifted between stages** (Section 2). Cross-stage summaries that omit the stage name are
   uninterpretable.
9. **Implementation choices were made after the freeze but before counting.** B-1 (a regime-failed
   episode still occupies the active slot), C-1 (capital geometry evaluated on the cost-feasible
   population), and M3 (twelve gap-adjacent 4h buckets retained as supplied) are recorded in
   `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` and the Stage 2I ratification. They are legitimate
   because they preceded counting, but they are choices, not forced readings.
10. **The data is not perfectly contiguous.** There are 7 registered gaps (213 5m bars, 70 15m bars,
    14 1h bars), 31 zero-volume 5m placeholders, and one extra non-exempt 4h bucket caused by those
    placeholders (`stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md` §3–§5). The handling is documented and
    the alignment audit is clean, but the gaps are real.
11. **The diagnostics are descriptive.** Kish `n_eff` assumes perfect within-cluster dependence; the
    design-effect screen is not a statistical test; non-overlap is a construction rule, not an
    independence claim (`stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §3.1;
    `stage2j/CANDIDATE_COMPARISON.md` §7).
12. **Two hypotheses were compared with controls; two were not.** A and C have unconditioned control
    arms, and neither control was promoted. B and D have no outcome control arm.
13. **Several designed hypotheses were never measured** (Section 1.3). Absence of a census is not
    evidence against them.

---

## 10. What the historical record does not say

- It does not say that any of the four strategies is unprofitable.
- It does not say that any of the four has no edge.
- It does not say that BTC offers too few opportunities in general; it says these frozen
  conjunctions, on this interval, under this cost proxy, produced too few.
- It does not say that the 26 bp cost is wrong, only that it is unverified and that it dominates D.
- It does not say that 150 is the right or wrong number; it says 150 is an undelivered project
  choice that no candidate met.
- It does not say that a different venue, timeframe or filter would pass. Those are untested
  hypotheses.
- It does not say that the frozen rules were implemented incorrectly. Compliance and alignment
  passed for B and D, and Stage 2C's alignment audit passed for A; C's look-ahead status is a
  structural argument, not a harness run.

---

## 11. Verified-fact index

| claim | artifact |
|---|---|
| A: 71 non-overlapping, 151 feasible, median `cost_R` 0.0898 feasible | `STAGE2C_FEASIBILITY_CENSUS.md` §1, §5, §13 |
| A: regime removes 250 of 445; overlap removes 80 of 151 | `STAGE2C_FEASIBILITY_CENSUS.md` §4, §7 |
| B: 24 canonical 72h; `M_all` 0.086505; feasible share 0.90625 | `stage2j/CANDIDATE_B_CENSUS_REPORT.md` §2, §4 |
| B: 341 of 458 attempts fail regime at `e`; 83 of 117 fail structure | `stage2j/CANDIDATE_B_CENSUS_REPORT.md` §3 |
| C: 63 episodes ≥ 6 bars; 17 breakouts; 12 feasible | `STAGE2A_FEASIBILITY_CENSUS.md` §3.1, §7 |
| C: 10 bp yields at most 17 events; 1.00R gate yields 17 | `STAGE2A_FEASIBILITY_CENSUS.md` §3.3, §6.1 |
| D: 34 canonical 24h; `M_all` 0.322559; 250 of 295 fail cost | `stage2j/CANDIDATE_D_CENSUS_REPORT.md` §2, §4 |
| D: no cost-feasible signal after 2022-09; design effect 3.93 | `stage2j/CANDIDATE_D_CENSUS_REPORT.md` §6 |
| 26 bp is a Binance proxy, not a Nobitex measurement | `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §4 |
| 150 is a project choice; 349 is a planning reference | `stage2j/machine_readable/verdict_inputs.json` |
| Stage 2H self-audit limitation; K0 accepted with disclosure | `stage2i/OWNER_RATIFICATION.md` §1 |
| Stage 2F rejected v1 on four critical defects | `STAGE2F_INDEPENDENT_FREEZE_AUDIT.md` §0 |
| Stage 2J census code commit and determinism | `stage2j/CENSUS_METHODOLOGY_AND_EXECUTION.md` §7 |
| Stage 2K not started as of Stage 2J | `stage2j/FREEZE_MANIFEST.json` tail |
