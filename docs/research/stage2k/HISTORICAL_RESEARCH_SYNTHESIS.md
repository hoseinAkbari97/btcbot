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
Stage 2C Candidate A (71 non-overlapping at 120h), and the two must not be combined.

**Interpretation:** the relabelling is a documentation hazard, not a computational error. It does,
however, mean that statements such as "Candidate B was tested" are only meaningful when the stage is
named. Stage 2K therefore always cites the stage together with the label.
