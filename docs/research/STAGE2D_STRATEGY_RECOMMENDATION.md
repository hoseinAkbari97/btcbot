# Stage 2D — Strategy Recommendation

**Status:** Research and design only. No implementation, no counting, no backtest.
**Companion document:** [STAGE2D_STRATEGY_REDESIGN.md](STAGE2D_STRATEGY_REDESIGN.md)
**Scope:** Recommend no more than two candidates for a future feasibility census. Do not promote the previous control arm.
**Floor under consideration:** 150 non-overlapping events (frozen Stage 2C floor). Not treated as a pre-registered standard.

---

## 1. Recommendation

### Recommended candidates

1. **B — Volatility expansion with directional continuation (and retest)**  
   - *Timeframe:* 1h entry with 4h regime permission  
   - *Non-overlap horizon:* 72 hours (sensitivities at 24h and 120h)  
   - *Rationale:* Genuinely distinct from Strategy 2 C (expansion-after-event, not compression-before-breakout), plausible microstructure mechanism, 72h horizon leaves room under the calendar ceiling, and a clear falsification path.
2. **D — Intraday continuation with a higher-timeframe volatility budget**  
   - *Timeframe:* 15m entry with 1h/4h/daily context, UTC-session-based  
   - *Non-overlap horizon:* 24 hours (sensitivities at 12h and 48h)  
   - *Rationale:* The only candidate with a credible path to the 150 floor; tests a genuinely new family (session-relative intraday momentum) not explored in prior stages.

**What this recommendation does not claim.** Neither candidate has demonstrated sufficient independent
opportunity frequency, and neither has demonstrated profitability. This is a recommendation to *test*,
not a promotion: it names the two designs worth spending a census on under the existing floor, and
nothing more. If a pre-count argument shows that a candidate cannot plausibly produce enough
independent episodes, or that its structural stop cannot clear `cost_R <= 0.20`, the correct output is
a documented rejection before counting, not a count that fails for reasons already known. If neither
survives the census, the honest conclusion is that no candidate in this programme is testable on this
interval, and that must be reported as the result rather than resolved by lowering the floor after
seeing the counts.

**Do not recommend A or C for a census under the existing floor.** A is the strongest mechanism but cannot reach 150 (20-day cap 63). C is weakest on mechanism and falsifiability and is structurally rare. Both are retained as alternatives if the floor is revised or the interval extended.

---

## 2. Why these differ from previous experiments

| candidate | difference from Setup 1 / Strategy 2 C | novelty |
|---|---|---|
| B | Strategy 2 C needed a low-volatility compression and traded the breakout. B needs a realized expansion, trades continuation after a retest, uses 4h permission, and floors the stop at 1.30% for cost reasons. The state is the inverse. | Genuine inversion of the previous trend-breakout hypothesis. |
| D | No prior stage tested intraday/session-relative momentum on 24/7 BTC spot. Prior work was daily/multi-day trend or zone-based pullbacks. | New family. Uses a higher-timeframe volatility budget to avoid the known failure mode (crisis conditions). |
| A (not recommended now) | Same trend family as Stage 2C but continuous long/flat daily state rule with 20–30 day horizon, not discrete pullback events. Mechanistically cleaner, but overlaps the family. | Different construction, same family. |
| C (not recommended now) | Long-only dip-buying with regime/stabilization filters. Shares "dislocation" logic with Setup 1 but is longer-horizon and more filter-heavy. | Different construction, related to Setup 1's failed idea. |

---

## 3. Strongest economic arguments for the recommendation

**For B:**
- **Volatility clustering is real.** Large directional moves cluster; the question is whether a subset continues rather than reverses (Engle, 1982; Bollerslev, 1986).
- **Microstructure plausible.** Fades of the first expansion and late entrants can create a continuation, and a retest filters for confirmation.
- **Calendar feasible.** 72h horizon gives a 425-episode ceiling, so the floor is not structurally impossible.
- **Genuinely testable falsification.** If expansions predominantly reverse or median `cost_R > 0.12`, the hypothesis fails clearly.
- **Distinct from C.** The failure mode is different, so a B failure would not be a re-test of C's compression hypothesis.

**For D:**
- **Intraday momentum has published evidence.** First-half/first-two-hour return predicts later return in equity indices (Gao et al., 2018), with plausible explanations (late-informed trading, infrequent rebalancing).
- **Only realistic path to 150.** Three sessions/day with a 24h non-overlap cap of 1,277 makes 150 episodes plausible if filters are not too strict.
- **Clear mechanism to falsify.** Either BTC shows session-relative continuation in normal-vol conditions, or it does not. The vol budget makes the test conditional on a stated regime.
- **Uses existing data.** 15m/1h/4h are present with known gaps; no new dataset required.

---

## 4. Strongest objections to the recommendation

**For B:**
- **Thin cost-adjusted edge.** Stop floor is 1.30% (gate boundary), median `cost_R` likely ~0.12, leaving only ~0.03R of a 0.15R target. A few basis points of slippage kill it.
- **Jump reversal is the competing mechanism.** BTC has large jumps (Scaillet et al., 2018); many expansions are exhaustion, and a retest may select the reversals.
- **Capital intensive.** 50–67% of a $10k account per position; cash-limited to 1–2 concurrent positions.
- **Frequency risk.** The conjunction (permission + retest + 1.30% floor) could yield <150 non-overlapping episodes.

**For D:**
- **Session is a convention.** BTC trades 24/7; UTC sessions have no exchange close. The analogy to equity closes is weak.
- **Cost is the binding constraint.** Stops must be ≥1.30% to clear the gate, making them wide for an "intraday" strategy. At 1.30%, the entire round trip consumes the gate.
- **Multiple parameters and overfit risk.** Session definition, first-two-hour threshold, vol-budget percentiles, and VWAP all invite tuning. The vol budget helps but increases degrees of freedom.
- **No direct published BTC evidence.** The evidence is transferred from equities; this is an analogy, not replication.
- **Cash-limited to one position.** At 1.30% stops, two positions would require >150% of $10k equity.

**Global objections:**
- **Both are conditional on a 0.15R target.** If the true effect is 0.10R, D is almost certainly dead on costs and B is marginal. The cost-adjusted screen is non-negotiable.
- **Venue is unverified.** All costs are Binance proxies; Nobitex fees/spreads/slippage are unknown.
- **Single cycle.** 2021–2024 is one bull–bear pair; results could be regime-luck.

---

## 5. Why A and C are not recommended (and when they might be)

**A — multi-day TSMOM:**
- **Calendar impossible under floor.** 20-day non-overlap caps at 63 episodes; 30-day caps at 42. Cannot reach 150. Tightening to 8 days would change the hypothesis to short-horizon continuation.
- **When it becomes viable:** If the 150 floor is revised to match the mechanism (e.g., 50–80) or the development interval is extended to ~10 years making the 20-day ceiling ~180.
- **Strength:** Best mechanism, cheapest per trade, most robust in literature. It should be the first candidate if the constraints change.

**C — regime-conditioned mean reversion:**
- **Weak for BTC spot.** BTC's dominant behaviour is momentum; long-only reversals fight that. The regime and stabilization filters are necessary but make falsification hard.
- **Frequency:** Realistic 10–30 episodes, far below floor.
- **Risk profile:** Structurally short crash risk; capped upside, fat left tail.
- **When it becomes viable:** Only with a cross-sectional universe or a short leg, neither of which is available here.

---

## 6. Exact census counts to report for each recommended candidate

For any future feasibility census of B or D, the report must include the following counts. None of these should be omitted.

### For B (volatility expansion + retest, 72h non-overlap canonical)

| count | definition | notes |
|---|---|---|
| `raw_expansions` | 1h bars meeting expansion criteria | Before 4h permission, retest, stop floor |
| `after_4h_permission` | Expansions with 4h regime + vol-percentile in range | Regime filter |
| `retest_candidates` | After permission, enter retest window 1–6 bars | Retest required |
| `before_cost_floor` | Retest valid | Before 1.30% stop floor |
| `valid_entries` | Have valid entry/stop | Non-missing bars |
| `cost_feasible` | `cost_R <= 0.20` | Gate |
| `unique_feasible` | After deduplication | If multiple expansions nearby |
| `nonoverlap_24h` | Greedy separation >= 24 hours | Sensitivity |
| `nonoverlap_72h` | Greedy separation >= 72 hours | **Canonical** |
| `nonoverlap_120h` | Greedy separation >= 120 hours | Sensitivity |
| `clusters_regime` | By 4h regime episode | Clustering view |
| `clusters_month` | By calendar month | Clustering view |
| `feasible_share` | `cost_feasible / valid_entries` | Must be reported |
| `median_cost_r` | Median `cost_R` among cost_feasible | For cost-adjusted screen |

### For D (intraday continuation, 24h non-overlap canonical)

| count | definition | notes |
|---|---|---|
| `session_candidates` | First-two-hour signals per UTC session | Before vol budget |
| `after_vol_budget` | Pass daily/4h vol percentile range | Vol budget filter |
| `after_vwap` | Price above session VWAP | Entry condition |
| `valid_entries` | Have valid entry/stop (>=1.30% floor) | Stop floor applied |
| `cost_feasible` | `cost_R <= 0.20` | Gate |
| `unique_feasible` | Deduplicated | One per session context |
| `nonoverlap_12h` | >= 12 hours | Sensitivity |
| `nonoverlap_24h` | >= 24 hours | **Canonical** |
| `nonoverlap_48h` | >= 48 hours | Sensitivity |
| `by_session_asia/europe/us` | Split by UTC session | Session sensitivity |
| `by_session_excl_asia` | Without Asia session | Sensitivity |
| `clusters_month` | By calendar month | Clustering view |
| `clusters_regime` | By 4h up/down regime | Clustering view |
| `feasible_share` | `cost_feasible / valid_entries` | Must be reported |
| `median_cost_r` | Median `cost_R` among cost_feasible | For cost-adjusted screen |

**Decision rule:** Both candidates must pass the same structural checks as Stage 2C: alignment passes, `median_cost_r` reasonable, `feasible_share >= 0.25` (or justified), and `nonoverlap_72h >= 150` (B) or `nonoverlap_24h >= 150` (D). But the **cost-adjusted edge screen** must also pass: `0.15 - median_cost_r > 0` with a margin. A candidate can meet the floor numerically but fail the economic screen — that is a failure, not a limitation to overlook.

**What the cost-adjusted screen does and does not mean.** `0.15 - median_cost_r` is a *design-margin
diagnostic*, not a net expectancy and not a profitability estimate. `0.15R` is an assumed minimum
effect of interest, not an empirically established gross expectancy for B or D; no outcome is
observed in a census, so no net edge can be computed. The subtraction is only a conservative statement
of how much room a design would have if that assumed effect were real. It assumes: `0.15R` is the true
effect of interest, `cost_R` captures the full round-trip friction, and no other friction matters.
Every future report must state all three assumptions alongside the number. A positive value does not
demonstrate viability; a negative value is a genuine warning. Viability itself can only be assessed in
a later outcome stage, not from signal counts.

---

## 7. Future census design per recommended candidate

### 7.1 Census design for B

**Pre-freeze requirements:**
1. Write `STAGE2D_CENSUS_B_SPEC.md` and `stage2d_census_b_config.json` with all parameters frozen before counting. Compute hashes and record in `freeze_b.json`.
2. Define expansion criteria exactly (ATR period/multiple, body/range, close location). Do not sweep these.
3. Define 4h permission (SMA period, slope, ATR percentile window) exactly.
4. Define retest (window 1–6 bars, tolerance, confirmation) exactly.
5. Define stop rule and the 1.30% floor exactly.
6. Use 72h non-overlap as canonical; pre-register the sensitivities.

**Data and alignment:**
- Use 1h BTCUSDT for signals, 4h for regime permission, 5m/15m only for sanity checks (not to fit parameters).
- Apply the same gap policy as Stage 2C; record unusable bars/segments.
- Aggregate if needed, but do not create a new dataset.

**Counts and diagnostics:**
- Report all counts in §6.
- Clustering by 4h regime episode and by calendar month.
- Kish as a concentration diagnostic only (correct bound language), with rho-sensitivity (0.25, 0.5, 0.75, 1.0).
- Cost sensitivity at 10, 26, 39, 52 bp.
- Capital geometry at $10k (notional distribution, max concurrent under 72h hold).
- Feasible share and median `cost_R`.
- **Cost-adjusted edge:** `0.15 - median_cost_r`; require > 0 with margin, else FAIL on economics.

**Rejection criteria (pre-registered):**
- `nonoverlap_72h < 150` → FAIL (frequency)
- `median_cost_r > 0.12` → FAIL (economics, even if gate passes; can be adjusted if justified before counting, but must be stated)
- `feasible_share < 0.25` → FAIL or serious limitation
- Median stop < 1.30% after floor and unfixable → FAIL
- Stop execution/gap rate suggests proxy is insufficient and cannot be quantified → limitation or FAIL

### 7.2 Census design for D

**Pre-freeze requirements:**
1. Write `STAGE2D_CENSUS_D_SPEC.md` and `stage2d_census_d_config.json`, freeze with hashes.
2. Define UTC session boundaries exactly (Asia/Europe/US, and whether boundaries are inclusive/exclusive).
3. Define first-two-hour return, VWAP calculation (session or rolling), and threshold exactly.
4. Define vol-budget percentiles (window 90 days) and bounds exactly.
5. Define stop rule and 1.30% floor exactly.
6. Use 24h non-overlap as canonical.

**Data and alignment:**
- Use 15m BTCUSDT for intraday signals; 1h for ATR; 4h/daily for vol budget.
- Handle 15m and 1h gaps explicitly (document affected sessions).
- Be careful about session boundaries at day transitions.

**Counts and diagnostics:**
- Report all counts in §6, including per-session splits.
- Clustering by calendar month and by 4h regime.
- Kish diagnostic with rho-sensitivity.
- Cost sensitivity at 10, 26, 39, 52 bp.
- Capital geometry (emphasize the 76% notional at 1.3% stop and one-position cash constraint).
- **Cost-adjusted edge:** critical here because margin is thinnest.
- Session sensitivity (drop Asia, different session lengths).

**Rejection criteria (pre-registered):**
- `nonoverlap_24h < 150` → FAIL
- `median_cost_r > 0.15` is dangerous; require `median_cost_r <= 0.17` at most with justification, and `0.15 - median_cost_r > 0` → prefer `> 0.02` margin
- `feasible_share < 0.30` → concerning (tight stops mean most signals may fail gate)
- If 1.30% floor is hit by >50% of signals → document heavily; if unfixable without widening beyond what gate allows → FAIL
- Vol-budget is too permissive/crisis-filter is missing and costs spike → FAIL

### 7.3 Shared requirements for both

- **Development interval only:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`. No reading beyond.
- **Long-only spot, no leverage:** Enforce.
- **Cost gate:** `cost_R <= 0.20`, equivalent min stop ~1.30%. Do not weaken.
- **Cost-adjusted screen:** Add and enforce.
- **Clustering:** Report >=3 views; use Kish as diagnostic with correct language.
- **Alignment:** Run alignment audit like Stage 2C.
- **Freeze discipline:** Spec + config hashed before counting; abort on change.
- **No outcome simulation:** Count episodes only; do not compute P&L/expectancy/win-rate/backtest equity.
- **Report honestly:** If neither reaches 150 or both fail the cost-adjusted screen, recommend further research, not a pick.
- **Architecture:** Review gaps but do not implement; note multi-position need for B outcome stage if pursued later.

### 7.4 Candidate B — mandatory frozen definitions

No B census may count a single signal until every row below has a sentence in the frozen spec.
"Objective" means computable from closed OHLC bars with no chart reading and no analyst judgement.

| item | what the frozen spec must state | ambiguity to resolve now |
|---|---|---|
| Volatility expansion | ATR construction (Wilder or simple), ATR period, multiple, and the exact bar-level test | Whether "true range" includes the prior close; how zero-range or gap bars are handled |
| Directional confirmation | The body fraction formula and the close-location formula, with the denominator defined | Whether the bar's range is `high - low` or includes the prior close; whether body is `abs(close - open)` |
| 4h regime permission | Exact 4h bar used at each 1h decision (strictly the last **closed** 4h bar), SMA period, ATR percentile window, and whether conditions are AND or OR | The design text uses "or" for close-above-SMA / positive-return; AND vs OR changes the count materially |
| Retest window | The bar index at which the window opens and closes, relative to the expansion bar | Whether the expansion bar itself is bar 0; whether a new expansion restarts the window |
| Retest tolerance | Which bar's ATR the tolerance uses, and whether a touch or a close inside the band is required | Whether touching the level intra-bar suffices, and whether the tolerance is measured from the expansion close or the expansion high |
| Resumption confirmation | The exact close-based condition and whether the retest bar can also be the confirmation bar | Whether a single bar may satisfy retest and resumption, which would make the retest meaningless |
| Structural stop | Which ATR, measured at which bar, and how "farther" is resolved after an entry gap | Whether the stop is anchored to the expansion low only, or also to the confirmation bar's low |
| Entry timing | Fill assumption (next-bar open, market order) and behaviour when the next bar opens through the level | Whether a gap beyond the retest band cancels the signal |
| Episode definition | What separates one episode from a second expansion inside the same move | Undefined in the design; without it, deduplication and non-overlap are not reproducible |
| 72h non-overlap policy | Greedy earliest-first acceptance, measured entry-to-entry or entry-to-exit, and what happens to skipped signals | Whether a skipped signal is re-eligible after 72h or discarded permanently |

These are not refinements. Each one can change the episode count, so freezing them in the wrong
order — after seeing counts — would invalidate the census.

### 7.5 Candidate D — mandatory frozen definitions

| item | what the frozen spec must state | ambiguity to resolve now |
|---|---|---|
| UTC session boundaries | Exact start/end instants, inclusive/exclusive convention, and which session a boundary bar belongs to | Whether a bar stamped 08:00:00 belongs to Asia or Europe; whether sessions are fixed or DST-shifted |
| First-two-hour return | The two anchor bars (open of the first, close of the eighth 15m bar) and the behaviour when either is missing | Whether the return uses the session open or the prior close; gap handling at session start |
| Session VWAP | Reset rule, price input (typical price or close), and whether the first two hours are included | §7.2 allows "session or rolling"; these are different signals and only one may be frozen |
| Volatility budget | Which series (daily ATR or 4h realized volatility), the percentile window, and the lower/upper bounds | The design offers two alternative definitions joined by "or"; choosing both creates two strategies |
| Volatility percentile | Percentile method (rank vs interpolation), whether it uses closed bars only, and whether it is trailing-calendar or trailing-bar | Whether the current bar is included in its own percentile, which is a look-ahead risk |
| Structural stop | ATR timeframe, the bar at which ATR is measured, and the floor interaction | Whether the 1h ATR is from the entry bar or the signal bar |
| Entry timing | Fill assumption at the next 15m open and behaviour when the open is already beyond the threshold | Whether a gap invalidates the signal or enters at the gapped price |
| Deduplication | The exact unit — one per session, one per UTC day, or one per cluster | "Deduplicated" is undefined; the choice sets the maximum count |
| 24h non-overlap policy | Whether non-overlap is a UTC-calendar-day rule or a rolling 24h rule | A day rule and a rolling rule give different counts on the same signals |

### 7.6 Shared rule against discretion

Neither candidate may be counted with discretionary visual interpretation. A signal is a boolean result
of the frozen rules evaluated on closed bars; no chart review, no "clear expansion" judgement, no
manual rejection of signals that look like exhaustion, and no manual override of a retest or a VWAP
breach is permitted. If a condition cannot be expressed as a closed-bar boolean, it is removed from the
test rather than judged by eye. Any residual ambiguity that survives the freeze must be reported as an
ambiguity in the census output, with its magnitude, not resolved silently.

---

## 8. Alternative ranking if the floor is revised

If the programme revises the frozen floor (with a stated derivation, registered before counting):

| priority | candidate | reasoning |
|---|---|---|
| 1 | **A — multi-day TSMOM** | Best mechanism, best cost economics, strongest literature support. Becomes testable at 20–30 day horizons if floor is 60–80 or interval extended. |
| 2 | **B — volatility expansion + retest** | Still genuinely distinct and plausible; good compromise if A needs longer interval. |
| 3 | **D — intraday continuation + vol budget** | Loses advantage if frequency is not the constraint; cost-adjusted edge is weakest. |
| 4 | **C — regime-conditioned mean reversion** | Remains weakest; only viable with a short leg. |

The companion redesign document explains the calendar arithmetic that makes this ordering flip. The current recommendation follows the testability-first ordering because the floor is currently frozen at 150.

---

## 9. Final answer to the required report items

The user requires reporting these eight items. Here is the answer:

### (1) Audit findings (provenance of decision criteria)
- **150 floor:** First appears in `201831b` (Stage 2C freeze, before script/results at `cd161e4`). No antecedent in Stage 2A/2B (Stage 2A used `>= 200`; Stage 2B referenced 349 and said not to require `> 200` as guarantee). Lower than earlier language. Not derived; not independently pre-registered. It was pre-specified before counting, but calling it "pre-registered" overstates the record.
- **349:** Derived arithmetically in Stage 2A from 0.15R/1R/5%/80% power assuming independence; correct, carried forward. Becomes unattainable for multi-day strategies in 1,277 days (needs H ≤ 3.66 days).
- **0.15R:** Design target from `e5f495f` before all censuses; not derived from cost/capital. The 0.20R gate is not an economic sufficiency bound for 0.15R.
- **120h:** Introduced at Stage 2C freeze, no antecedent; design choice for non-overlap, not optimal exit.
- **Kish:** Formula correct for perfect within-cluster dependence, but bound language in frozen spec is inverted. It is a concentration diagnostic, not a dependence estimate. Report with multiple clustering views and rho-sensitivity.

### (2) Candidates evaluated
Evaluated **A, B, C, D** against twelve questions each. Screened ten additional alternatives (cross-sectional momentum, funding/basis, on-chain flows, options VRP, market making, prior-day breakout, ORB, pairs trading, seasonality, sentiment) — none advanced due to missing data/instruments, duplication, or weak mechanisms. No fifth candidate advanced.

### (3) Recommended candidates
**B (volatility expansion + retest, 72h non-overlap)** and **D (intraday continuation with HTF volatility budget, 24h non-overlap)**. Both can be tested with existing data primitives; B is genuinely distinct from Strategy 2 C; D is a new family with a path to 150.

### (4) Strongest economic arguments
- **B:** Volatility clustering + plausible fade-continuation microstructure; different state from C's compression breakout; feasible under calendar ceiling if conjunction not too strict; clear falsification.
- **D:** Documented intraday momentum in equities (transfer plausible); three sessions/day provides frequency; vol budget states regime of validity; only candidate that can realistically hit 150 under current floor.

### (5) Strongest objections
- **B:** Thin cost-adjusted edge (median ~0.12R cost, leaves ~0.03R), jump reversal competing mechanism, 50–67% capital utilisation, frequency uncertain.
- **D:** Session is arbitrary on 24/7 market, costs consume gate at minimum stop (1.30%), heavy parameterisation/overfit risk, no direct BTC published evidence, cash-limited to one position.
- **Global:** 26 bp is Binance proxy (Nobitex unknown), single 3.5-year cycle, cost-adjusted screen may fail both.

### (6) Why recommended differ from previous experiments
- **vs Strategy 2 C:** B inverts the state (expansion vs compression) and requires retest; different mechanism and failure modes.
- **vs Setup 1:** C shares dip-buying logic but is more filter-heavy and still rejected here due to mechanism/frequency; no pick from that family.
- **vs Stage 2C approach:** D is intraday/session-based, not multi-timeframe pullback continuation. B is event-based but opposite of C. Neither is a parameter tweak of Candidate A.
- **Methodological:** Explicitly use calendar arithmetic as a filter, add cost-adjusted edge screen, correct Kish interpretation, and do not mislabel 150 as pre-registered.

### (7) Exact deliverable paths
- `docs/research/STAGE2D_STRATEGY_REDESIGN.md` — full redesign, provenance audit, twelve-question tables for A–D, 14-dimension matrix, screened alternatives, architecture gaps, limitations, references
- `docs/research/STAGE2D_STRATEGY_RECOMMENDATION.md` — this document (recommendation, exact counts, census designs, strongest objections, alternative ranking)

### (8) Confirmation no prohibited processing occurred
No market-data processing, signal counting, backtesting, P&L, expectancy, win-rate, portfolio simulation, bootstrap, Monte Carlo, optimization, strategy implementation, validation/OOS access, dependency installation, or dataset downloads were performed. Frozen artifacts (Setup 1, Stage 2A/2B/2C, Stage 6/6A) were not modified. Shared production strategy logic was not modified. All existing untracked files were preserved. Frequency estimates are qualitative and unverified. Literature citations are tagged by evidence type and their limitations are stated.

---

**Repository state.** The design work is committed in small logical units on `main`. The earlier
recommendation that this work had already been pushed was incorrect: at the start of the resumption
run the redesign's cost/capital, architecture, limitations, and references sections were uncommitted
and this document was untracked. Both were committed during the resumption, together with the
methodological corrections recorded in §1, §6, §7.4–7.6, and above.
