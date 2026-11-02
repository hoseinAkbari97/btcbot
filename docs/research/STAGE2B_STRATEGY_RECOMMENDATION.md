# Stage 2B — Strategy Recommendation

**Status:** Research and design only. No implementation, no counting, no backtest.
**Selection basis:** economic rationale, plausible stop distance, potential frequency, testability, data availability, falsifiability, distinction from Setup 1 and Strategy 2 C.
**Gate:** If no candidate is defensible, recommend further research (do **not** force a choice).

## 1. Comparison matrix

| Dimension | A — MTF trend pullback continuation | B — Regime-conditioned mean reversion (long-only) | C — Structure change + HTF regime | D — HTF regime + liquidity zone reaction |
|---|---|---|---|---|
| Economic rationale | Trend persistence + pullback liquidity **[L][H]** | Short-term dislocation reversion **[L][H]** | Structure shift in trend direction **[H]** | Zone reaction in trend **[H]** |
| Falsifiability | Clear (HTF regime + pullback + resumption) **[H]** | Clear but easy to overfit regime filter **[H]** | Clear if structure defined objectively **[H]** | Clear if zone definition objective **[H]** |
| Expected frequency (unverified) | **moderate** **[E]** | **low-to-moderate** (range-dependent) **[E]** | **low-to-moderate** **[E]** | **low-to-moderate** **[E]** |
| Stop-distance potential | Good if pullback shallow, bad in volatility spikes **[E]** | Often tight; hard to satisfy >=1.3% consistently **[E]** | Moderate **[E]** | Moderate–good **[E]** |
| Cost sensitivity (26 bp) | Moderate; needs `cost/R <= 0.20` gate **[E]** | High; regime gating essential **[E]** | Moderate **[E]** | Moderate **[E]** |
| Expected holding period | Intraday–few days **[E]** | Hours–1-2 days **[E]** | Intraday–few days **[E]** | Intraday–few days **[E]** |
| Capital efficiency | Moderate **[E]** | Can be low (false signals) **[E]** | Moderate **[E]** | Moderate **[E]** |
| Regime dependence | High (needs trends) **[E]** | Very high (must avoid downtrends) **[E]** | High **[E]** | High **[E]** |
| Intrabar ambiguity | Yes (same as Stage 6) **[F]** | Yes **[F]** | Yes **[F]** | Yes **[F]** |
| Data requirements | 5m + 1h/4h (available) **[F]** | 5m + regime data **[F]** | 5m + HTF **[F]** | 5m + HTF structure **[F]** |
| Existing platform support | Partial (TFs exist) **[F]** | Partial **[F]** | Partial **[F]** | Partial **[F]** |
| Overfitting risk | Medium (need objective rules) **[E]** | **High** (many filters) **[E]** | Medium **[E]** | Medium (zone definition) **[E]** |
| Implementation complexity | Medium **[E]** | Medium–High **[E]** | Medium **[E]** | Medium **[E]** |
| Statistical testability (likely) | **Most plausible** if frequency holds **[E]** | Uncertain; regime clustering hurts power **[E]** | Uncertain **[E]** | Uncertain **[E]** |

## 2. Recommendation

**Recommended candidate: A — Multi-timeframe trend pullback continuation**

**Strongest economic rationale [L][H]:** Time-series momentum can persist **[L]** (Moskowitz et al. 2012), and pullbacks within trends offer entries with potentially wider structural stops than tight compression breakouts, while still being distinct from Setup 1 (reversal) and from pure HTF breakouts **[E]**. It targets continuation in the direction of HTF regime, not reversion **[H]**.

**Why different from previous experiments [F][E]:**
- **vs Setup 1:** opposite direction (continuation vs reversal), different trigger (pullback+resumption vs sweep+rejection), different timeframes/logic **[F]**.
- **vs Strategy 2 C:** entry is not contingent on a rare compression episode breaking out; it can fire on pullbacks in trending regimes, potentially increasing opportunities while still requiring HTF regime confirmation **[E]**. C failed due to episode scarcity (63 long-enough episodes) **[F]**; A-like pullbacks are a different condition **[E]**.

**Strongest argument against this recommendation [E]:**
- Frequency is unverified and could be regime-limited (trends not constant); clustering could reduce effective sample size below what's needed for 0.15R.
- Stop distances must satisfy `cost/R <= 0.20` (>=~1.3%); in some regimes stops may be too tight or regime filter may cut frequency dramatically.
- HTF regime classification can be subjective/overfit if not strictly objective.
- Candidate A from Strategy 2 used a different definition (Donchian breakout above SMA) and was insufficient; **this is a pullback variant, not that definition** — it must not be conflated.

**If no candidate is defensible:** Do not force selection; recommend further research. However, A has the clearest path to distinguishable events and plausible stop geometry among the options **[E]**.

## 3. Exact definition to count in next feasibility census (no counting performed)

Do **not** optimize parameters. Use objective, pre-definable rules:

### Scope
- Instrument: BTCUSDT spot, long-only **[F]**
- Signal TF: LTF (e.g., 15m or 1h) for pullback/resumption; HTF regime (e.g., 4h or daily) **[E]**
- Execution: 5m for entry timing (causal) **[E]**
- Interval: `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` dev only **[F]**
- Costs: 26 bp round-trip, gate `cost/R <= 0.20` **[F]**

### HTF regime (objective)
- Define HTF trend regime by a simple, pre-definable rule (e.g., price above/below a moving average with slope/structure) **[E]**. Must be computable from available data without look-ahead **[E]**. Avoid discretionary labels.

### Pullback definition (objective)
- Identify pullback to a defensible reference (e.g., recent swing area or MA zone) on LTF while HTF regime is uptrend **[E]**. Depth measured objectively (e.g., % retracement) **[E]**.

### Entry/resumption confirmation (objective)
- Enter long on LTF resumption confirmation (e.g., close above pullback high / structure shift) with entry at open of next 5m bar after confirmation **[E]**. No same-bar signal use **[E]**.

### Stop, target, exits (design)
- **Structural stop:** beyond pullback extreme (objective) **[E]**
- **Target:** record 1R/2R as design only (do not require simulation in census) **[E]**
- **Time exit:** define if needed, record only **[E]**
- **Invalidation:** break of structure / HTF regime flip **[E]**

### Feasibility metrics to count
1. Valid bars by TF
2. HTF regime periods
3. Pullback setups identified
4. Resumption confirmations (triggers)
5. Triggers with valid positive stop
6. Events passing `cost/R <= 0.20`
7. Unique events (episode/dedup)
8. Events after cooldown/overlap restrictions
9. Cost/R distribution at 0.10/0.20/0.30/0.50
10. Stop distance % distribution
11. Time between events, clustering
12. Overlap with unconditioned entries (control) **[E]**

### Controls and safeguards
- **Control:** unconditioned entries meeting some baseline (define objectively) to test if pullback conditioning adds distinction **[E]**
- **Dedup/cooldown:** one position logic or explicit rules **[E]**
- **Same-bar ambiguity:** track share **[E]**
- **Cost sensitivity:** 10/26/40/60/100 bp **[E]**
- **Look-ahead:** enforce closed-bar + next-bar entry **[E]**
- **Causality:** HTF regime known at LTF time **[E]**

### Statistical assessment (no computation)
- Assess effective sample size given clustering **[E]**
- Reference 0.15R / σ=1 / α=0.05 / 80% power needs ~349 independent; effective likely lower **[E]**
- Do not require >200 as guarantee; require credible argument if borderline **[E]**

## 4. Rejection criteria for future census
- < required events after `cost/R <= 0.20` with no path to sufficiency **[E]**
- Median `cost/R > 0.20` despite rules **[E]**
- No distinction from control **[E]**
- Alignment/look-ahead issues **[E]**
- Costs dominate under sensitivity **[E]**

## 5. Notes
- All event counts marked unverified **[E]**
- Nobitex terms unknown **[H]**
- This recommendation does **not** promote Strategy 2 Candidate A; it proposes a pullback variant with different conditioning **[E]**
