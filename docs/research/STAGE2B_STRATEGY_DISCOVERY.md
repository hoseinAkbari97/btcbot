# Stage 2B — Strategy Discovery

**Status:** Research and design only. No code, no market-data processing, no backtest, no simulation, no optimization.
**Dependencies read:** `docs/research/STRATEGY_2_CANDIDATE_COMPARISON.md`, `docs/research/STRATEGY_2_RECOMMENDATION.md`, `docs/research/STAGE2A_FEASIBILITY_CENSUS.md`, `docs/research/STAGE2A_DATA_ALIGNMENT_AUDIT.md`, `stage6_rebuild_v2/STAGE6_INTERPRETATION_ADDENDUM.md`, `stage6_rebuild_v2/DEVELOPMENT_EXPERIMENT_REGISTRY.md`. Platform inspected for architecture/schemas only.
**Evidence tagging:** **[F]** = repository fact; **[L]** = literature-backed; **[E]** = engineering judgment; **[H]** = unverified hypothesis.

**Historical outcomes (for context):** Setup 1 was negative under stop-first and became unfundable on 2021-06-19 **[F]**. Strategy 2 Candidate C produced only **12 unique feasible events** at 0.20R over 3.5y due to episode scarcity (only 63 long-enough compressions) despite reasonable `cost/R` medians **[F]**. Candidate A was more frequent but still insufficient for 0.15R at its proposed non-overlapping count **[F]**.

## 1. Non-negotiable constraints

| constraint | value | source |
|---|---|---|
| Instrument | BTCUSDT spot, long-only, no leverage | **[F]** |
| Underlying | 5m; higher TFs available (15m, 1h, 4h, daily) | **[F]** `backend/data/datasets/manifest.json` |
| Cost model (proxy) | 0.1% fee/side + 3 bps adverse/side = **26 bps round-trip** | **[F]** Stage 6 config |
| Cost relation | `cost/R = 0.0026 * P / D`, D = structural stop distance in USDT/BTC | **[F]** |
| Primary gate | `cost/R <= 0.20` → D >= ~1.30% of price | **[F]** |
| Descriptive thresholds | 0.10R, 0.20R, 0.30R, 0.50R | design |
| Execution proxy | Binance spot (not Nobitex-verified) | **[F]** |
| Development interval (for any future census) | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` | **[F]** Stage 2A |
| Data gaps (5m) | 7 gaps, 213 bars; 4h has 0 registered gaps | **[F]** Stage 2A alignment |

Costs are **Binance-proxy estimates**, not verified Nobitex execution costs **[F]**. Minimum notional/lot/tick/spread/slippage/liquidity/outages remain unverified for Nobitex **[H]**.

## 2. Candidate families evaluated

### 2.1 Candidate A — Multi-timeframe trend pullback continuation
**Hypothesis [H]:** In a higher-timeframe directional regime, price retraces toward a defensible reference (e.g., prior structure/zone or a moving average) on a lower timeframe and resumes in the dominant direction; enter on resumption confirmation with a structural stop beyond the pullback extreme.

**Mechanisms:** gradual information diffusion and risk-management flows can create shallow pullbacks within trends **[L]** (Moskowitz et al. 2012); resting liquidity and orderflow can produce predictable retracements **[H]**. This is **not** the previous 4h Donchian breakout **[E]** — entry is conditional on (a) HTF regime, (b) LTF pullback depth/structure, (c) resumption confirmation, which can fire between HTF breakouts and does not require a new 20-bar high at the trigger TF **[E]**.

**Stop feasibility:** depends on regime; in clean trends pullbacks often give 1.5–3% structural stops, but in choppy regimes stops widen or become invalid **[E]**. Must gate by `cost/R <= 0.20` **[E]**.

**Frequency class (unverified):** **moderate** **[E]** — potentially higher than C's 63 eligible states but likely regime-limited; could still be <200 in development split **[E]**.

### 2.2 Candidate B — Regime-conditioned mean reversion (long-only)
**Hypothesis [H]:** Short-term dislocations relative to a stable reference can revert when not in persistent directional expansion, traded long-only with tight structural invalidation.

**Mechanisms:** short-horizon mean reversion is documented in some equity contexts **[L]** (Jegadeesh 1990; Lehmann 1990), but effects are often small, regime-dependent, and can reverse in strong trends/crashes **[L]**. Crypto exhibits different microstructure **[H]**.

**Critical restrictions:** long-only spot only; **cannot** assume short-side liquidity provision **[F]**; not every dip recovers **[H]**; must exclude strong downtrends/expansion regimes **[H]**. Adverse selection is severe in falling markets **[H]**.

**Stop feasibility:** structural invalidation can be tight but costs are punishing; likely requires careful regime gating to keep stops wide enough or to avoid trading in bad regimes **[E]**. Risk of catching falling knives **[H]**.

**Frequency class (unverified):** **moderate to high in ranges, very low in trends** **[E]** — overall likely **low-to-moderate** and highly regime-clustered **[E]**.

### 2.3 Candidate C — Multi-timeframe directional continuation after local market structure change
**Hypothesis [H]:** A local structure transition (e.g., shift in short-term swing structure) in the direction of a higher-timeframe regime can produce continuation before a conventional HTF range breakout.

**Mechanisms:** structure-based entries differ from simple range breakouts **[H]**; liquidity can accumulate around structure and cause continuation on break/shift **[H]**. Must be **distinct from Setup 1** — Setup 1 is low-side sweep/rejection (fade/reversion logic) **[F]**, whereas this is directional continuation in HTF regime direction with different invalidation **[H]**.

**Stop feasibility:** structural stop can be placed beyond the structure that invalidated (often wider than a tight compression low) **[E]**, but depends on structure definition **[E]**.

**Frequency class (unverified):** **low-to-moderate** **[E]** — likely more frequent than pure compression episodes if definition is reasonable, but could still be constrained **[E]**.

### 2.4 Additional candidate — HTF regime + liquidity-zone reaction (long-only)
**Hypothesis [H]:** In an established HTF uptrend, price approaches a prior swing/zone area and shows acceptance/reaction on LTF; enter long on confirmation with stop below the zone invalidation. Focuses on reaction at pre-existing structure rather than random dips or range compression.

**Mechanisms:** zones can attract liquidity and produce reactions **[H]**; trend persistence supports continuation **[L]** (Moskowitz et al. 2012). Distinct from Setup 1 (Setup 1 looks for sweep+rejection; this looks for reaction within HTF trend) **[E]**.

**Stop feasibility:** zone-based invalidation can be reasonably wide if zones are well-defined **[E]**, but zone quality varies **[H]**.

**Frequency class (unverified):** **low-to-moderate** **[E]** — likely regime-limited **[E]**.

## 3. Economic rationale, falsifiability, and failure modes (summary)

For all candidates: edge could disappear if trends become mean-reverting/choppy, if costs rise (Nobitex worse than Binance), if liquidity dries up, if regime classification fails, or if the behavior becomes arbitraged **[H]**. Overfitting risk is high if parameters proliferate **[E]**. Intrabar ambiguity exists (same-bar ties) as in Setup 1/Stage 6 **[F]**.

**Falsification examples:** (A) pullback entries lose money or underperform random entries in HTF uptrends; (B) mean reversion fails in downtrends and overall negative/indistinguishable from random; (C)/(D) structure entries not distinguishable from unconditioned entries or negative after costs **[H]**.

## 4. Trade-offs (frequency vs feasibility)

| Candidate | Frequency (unverified) | Stop feasibility | cost/R sensitivity | Holding period | Clustering risk | Regime dependence |
|---|---|---|---|---|---|---|
| A (MTF pullback) | moderate **[E]** | moderate–good if HTF trend clear **[E]** | moderate **[E]** | intraday–few days **[E]** | moderate **[E]** | high (needs trends) **[E]** |
| B (regime-conditioned mean reversion, long-only) | low-to-moderate **[E]** | tricky; needs regime gating **[E]** | high (can need tight stops or avoid bad regimes) **[E]** | short (hours–1-2 days) **[E]** | high in ranges, low in trends **[E]** | very high **[E]** |
| C (structure change + HTF regime) | low-to-moderate **[E]** | moderate **[E]** | moderate **[E]** | intraday–few days **[E]** | moderate **[E]** | high **[E]** |
| D (HTF regime + liquidity zone) | low-to-moderate **[E]** | moderate–good if zone valid **[E]** | moderate **[E]** | intraday–few days **[E]** | moderate **[E]** | high **[E]** |

No numerical counts estimated (forbidden to process market data). All marked unverified.

## 5. Minimal architecture implications

Existing components can be reused where applicable: data loading/gap handling, causal event discipline, barrier resolution (`outcome_contract.resolve_barriers`), costs/sizing/accounting patterns, bootstrap, lookahead testing **[F]**. For MTF strategies, need careful **causal TF alignment/resampling and entry timing** (avoid look-ahead) **[E]**. **Do not** build a general strategy framework now; add only minimal pieces if implementation is later authorized **[E]**. Do not touch `stage6_rebuild_v2/`, `stage6_acceptance_audit/`, or Setup 1 **[F]**.

## 6. References (credible)
- Jegadeesh, N. (1990), J. Finance, short-term reversal **[L]**
- Lehmann, B. (1990), J. Finance, weekly reversals **[L]**
- Moskowitz, T.J., Ooi, Y.H., Pedersen, L.H. (2012), J. Financial Economics, time-series momentum **[L]**
- Bollerslev, T. (1986), J. Econometrics, volatility clustering **[L]** (contextual)

Citations are to mechanisms, not to BTCUSDT 5m spot results **[L]**.
