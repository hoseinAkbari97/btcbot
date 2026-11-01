# Strategy 2 — Candidate Comparison

**Status:** research design only. No strategy has been implemented, backtested, optimized, or
evaluated. No market data was ingested, no pipeline was run, and no validation/out-of-sample
result was read.

**Supersedes nothing.** Setup 1 remains frozen as a negative development experiment
(`stage6_rebuild_v2/DEVELOPMENT_EXPERIMENT_REGISTRY.md`, verdict
`PASS_WITH_LIMITATIONS` for accounting, conclusion
`NEGATIVE_GROSS_EXPECTANCY_UNDER_PRIMARY_STOP_FIRST_CONVENTION`).

**Companion document:** `docs/research/STRATEGY_2_RECOMMENDATION.md` (selects one candidate).

### Evidence tags

Every substantive claim below carries one of four tags. They are not decoration; the whole point
of the exercise is to keep the four kinds of statement apart.

| tag | meaning |
|---|---|
| **[F]** | Established fact in this repository, checkable in the named frozen artifact. |
| **[L]** | Literature-backed mechanism, with a citation in §9. Says nothing about BTCUSDT 2021–2026. |
| **[E]** | Engineering judgment or arithmetic on frozen assumptions. Defensible, but an opinion. |
| **[H]** | Unverified hypothesis. This is what the experiment would exist to test. |

A number computed from the frozen configuration (a cost ratio, a standard error) is **[E]**
arithmetic, not a research finding. Nothing in this document is a forecast.

---

## 1. Constraints inherited from the frozen Setup 1 baseline

These constraints are the reason Strategy 2 looks the way it does, so they are stated before any
candidate. They are not "lessons learned" in the vague sense; each one removes a class of design.

### 1.1 What Setup 1 established **[F]**

| fact | value | source |
|---|---|---|
| Resolved canonical trades | 101,789 | `stage6_v2_summary.json` → `signal.n_resolved` |
| Gross expectancy, stop-first | −0.2227R, CI −0.2290 to −0.2164R | `signal.primary_stop_first` |
| Ambiguous same-bar ties | 24,998 / 101,789 (24.6%) | `signal.ambiguous_resolved` |
| Funded portfolio trades | 2,711, final equity $4.98 | `portfolios.primary` |
| Entries bound by the spot cash cap | 2,559 / 2,711 (94.4%) | `independent_portfolio_audit.json` |
| Median actual / requested risk | 0.398 | same |
| Same-bar round trips among funded trades | 1,041 (38.4%), −$5,658.28, 56.6% of net loss | same |
| Candidates rejected as `cost_exceeds_1R` | 88,580 of 103,558 | `stage6_v2_summary.json` → `feasibility.counts` |
| Frozen cost per side | 0.1% fee + 3 bps adverse (2 bps spread + 1 bp slippage) | `config.json` |
| Feasibility ceiling used | `max_cost_to_risk = 1.0` | `config.json` |

### 1.2 The binding economic constraint: cost per R **[E]**

Round-trip cost under the frozen model is `2 × (0.001 + 0.0003) = 0.0026`, i.e. **26 bps of
notional**. In R units, where R is the entry-to-stop distance:

```
cost / R  =  0.0026 × price / stop_distance
```

Solve it for the stop distance that makes cost a small fraction of the risk unit:

| target `cost/R` | required stop distance | implied cost drag on a 1R win |
|---|---|---|
| 0.10 | 2.60% of price | 10% of the gross win |
| 0.15 | 1.73% | 15% |
| 0.20 | 1.30% | 20% |
| 0.50 | 0.52% | 50% |
| 1.00 | 0.26% | 100% (the Setup 1 ceiling) |

Setup 1's structural stop was the local swing low on a 5-minute chart, which is almost always
tighter than 0.26% on BTC. That is why 85.6% of its candidates were infeasible before the
portfolio even started **[F]**, and why the ceiling of `max_cost_to_risk = 1.0` was far too
generous: it permitted trades whose entire risk unit was consumed by costs.

The design consequence is blunt. **A 5-minute strategy with a 5-minute stop cannot pay for
itself on this venue.** Any Strategy 2 whose stop is under ~1% of price inherits Setup 1's
central failure. This rules out most intraday 5-minute setups before any hypothesis is
discussed, and it is the single most important constraint in this document.

### 1.3 The statistical constraint: how many independent trades? **[E]**

With a single instrument and long-only spot, sample size is the scarcest resource. For n
independent trades with R standard deviation near 1.0, the standard error of mean R is
approximately `1/√n`:

| n trades | SE of mean R | smallest edge distinguishable from zero at ~95% |
|---|---|---|
| 30 | 0.18 | ~0.36R |
| 100 | 0.10 | ~0.20R |
| 300 | 0.058 | ~0.11R |
| 1,000 | 0.032 | ~0.06R |

Overlapping signals are not independent, and clustered regimes reduce the effective count
further; Stage 6's episode clustering collapsed 101,789 trades to 22,971 episodes, a ratio of
4.4:1 **[F]**. Treat the table above as an optimistic upper bound on power.

A hypothesis whose true edge is 0.15R cannot be verified by a strategy that fires 30 times in
3.5 years, no matter how well the backtest is built. **Testability is therefore a selection
criterion, not a tiebreaker.**

### 1.4 The horizon constraint: what the 5-minute grid can and cannot resolve **[F]**

Five-minute OHLC cannot establish intrabar ordering. In Setup 1 that ambiguity touched 24.6% of
resolved observations because entry and exit lived on the same grid. The ambiguity is a property
of the *ratio of holding period to bar size*, not of the market: a strategy that holds for days
while resolving stops on 5-minute bars has ~1/48 the same-bar exposure of a strategy that holds
for an hour on the same grid **[E]**.

This suggests a design pattern that Setup 1 did not use: **define the signal on a coarse
timeframe, resolve the execution on the 5-minute grid.** The platform holds 5m, 15m, 1h and 4h
BTCUSDT series over the same coverage **[F]** (`backend/data/datasets/manifest.json`), so this
needs no new data.

### 1.5 What is *not* a constraint

- **Direction.** Setup 1 was long-only by construction (spot), and Strategy 2 will be too.
  Shorts require a margin/perp venue that this project does not model; pretending otherwise
  would be a new venue claim, not a new strategy.
- **The Setup 1 signal family.** Nothing here forbids low-side sweeps. It forbids *rescuing
  Setup 1 with new thresholds*: that is a completed experiment.

---

## 2. Candidate A — Trend following / momentum

### 2.1 The fourteen questions

**A1. What market behaviour is being exploited?** **[H]** Directional persistence at horizons of
days to weeks: once BTCUSDT begins a sustained move, the next several days are more likely to
continue in the same direction than to reverse, conditional on the move being large relative to
recent volatility. The traded object is continuation, not level.

**A2. Why might it persist?** **[L]** Two families of explanation, both with support outside
crypto: gradual information diffusion and herding, where investors underreact to news and adjust
positions over days (the classic momentum explanation), and risk-management flows, where
volatility-targeting and trend-following allocators mechanically add exposure after price rises
and reduce it after falls. **[L]** Moskowitz, Ooi & Pedersen (2012) document time-series momentum
across 58 liquid futures with predictability at 1–12 month horizons that partially reverses
beyond a year.

**A3. Who creates it?** **[L]** Underreacting discretionary and retail flow; mechanical
volatility-target and trend allocators; and, in crypto specifically, reflexive retail inflows
into an asset with no cash-flow anchor. **[H]** In crypto the mechanism may be stronger at short
horizons because the participant mix is more retail and more momentum-chasing than in futures.

**A4. When should it work?** **[H]** In persistent, low-to-moderate-volatility trends with
sustained participation, and when the entry does not require catching the first bar of the move.
**[E]** Long-only spot means the strategy can only express uptrends; it should therefore be
expected to work in sustained bull phases and to sit in cash during bear phases.

**A5. When should it fail?** **[H]** In choppy, range-bound markets, at trend exhaustion, and in
sharp V-shaped reversals where a breakout entry is immediately reversed. **[E]** It also fails
silently in the way that matters most here: a long-only single-asset trend strategy's returns
are dominated by BTC's own drift, so a profitable equity curve is not evidence of skill.

**A6. Simplest falsifiable version.** **[E]** On 4h closed bars: enter long at the next bar's open
when the close exceeds the highest high of the previous 20 bars *and* the close is above the
200-bar SMA; stop at 1.5 × ATR(20); exit on the first close below the 10-bar low, or after 30
bars. One entry per direction at a time. The falsifiable claim is: **net R per trade, after the
frozen cost model, is greater than zero, and greater than a random-entry arm with identical stop,
target and holding-period distribution.**

**A7. Required observables.** Bar OHLC; a 20-bar rolling high; a 200-bar SMA; ATR(20). All on 4h.

**A8. Available in the platform.** **[F]** All of it. `SmaTrendStrategy` and
`DonchianBreakoutStrategy` already exist in `backend/app/services/backtest/baselines.py`,
including an ATR helper; `outcome_contract.resolve_barriers` resolves stops and targets; 4h
candles are in the dataset. This candidate needs the least new code of the three.

**A9. Requires new data.** **[F]** None for the core version. A cross-sectional version (rank
several crypto assets, long the strongest) would need additional instruments and would be a
different, likely stronger, experiment.

**A10. Expected trading frequency.** **[E]** 15–50 entries per year on 4h Donchian(20) with a
200-SMA filter — i.e. roughly **50–170 trades across the 3.5-year development split**. **[H]**
Must be measured by a pre-scoring event census; this is an estimate, not a fact.

**A11. Expected holding period.** **[E]** 2–15 days. Wide by construction, since the exit is a
channel break rather than a fixed target.

**A12. Cost sensitivity.** **[E]** **Low, structurally.** A 1.5 × ATR(20) stop on 4h bars is
typically 2–4% of price, giving `cost/R` of roughly 0.07–0.13 — an order of magnitude better than
Setup 1. Turnover is low. **[F]** The platform's cost model already distinguishes fee from
adverse spread/slippage and can be scaled for sensitivity.

**A13. Bias and overfitting vulnerability.** **[E]** Low parameter count (three: channel length,
SMA length, ATR multiple) but **high confounding risk**: with one asset and a long-only spot
book, "trend edge" and "BTC beta" are nearly collinear. A 200-SMA filter is, functionally, a
regime-timed buy-and-hold. **[E]** The most likely way this experiment lies is not by fitting
noise but by reporting a beta exposure as alpha. Mitigation is a mandatory buy-and-hold and
random-entry comparison, not more parameters.

**A14. What would show it is wrong?** **[E]** Net R per trade with a block-bootstrap CI whose
upper bound is below zero; or net R indistinguishable from the random-entry arm; or performance
that disappears once the comparison is made against buy-and-hold with matched time in market.

---

## 3. Candidate B — Mean reversion

### 3.1 The fourteen questions

**B1. What market behaviour is being exploited?** **[H]** Short-horizon overextension: when price
deviates from a recent reference by a large amount relative to current volatility, part of that
deviation is transitory and reverses. The traded object is the transitory component, not a trend.

**B2. Why might it persist?** **[L]** Liquidity provision. Someone must absorb impatient flow,
and the compensation for doing so is a reversal. **[L]** Nagel (2012) interprets short-term
reversal returns as a proxy for liquidity-provision returns and shows they are strongly
time-varying and predictable with a volatility index. **[L]** Wen, Bouri, Xu & Zhao (2022) report
both intraday momentum and intraday reversal in cryptocurrency markets, i.e. the effect is
present but not uniform across horizons.

**B3. Who creates it?** **[L]** Impatient or uninformed flow — liquidation cascades, stop runs,
large market orders — that pushes price away from fair value and is then partially absorbed by
liquidity providers. **[H]** Crypto's leverage-driven liquidation cascades are a plausible
generator of exactly this flow, possibly a stronger one than in equities.

**B4. When should it work?** **[H]** In liquid, range-bound, mean-reverting regimes, and when the
deviation is caused by flow rather than information. **[L]** Nagel's result implies it works best
when liquidity provision is well compensated — i.e. in stressed, high-volatility periods — which
is also when it is most dangerous.

**B5. When should it fail?** **[H]** When the deviation is informational: a genuine repricing that
never reverts. In crypto those episodes are crashes. **[E]** The failure mode is a short-volatility
payoff: many small wins and rare large losses, which is precisely the shape that a 3.5-year window
containing May 2021, May 2022 and November 2022 will exercise.

**B6. Simplest falsifiable version.** **[E]** On 4h closed bars: enter long at the next bar's open
when `close` is at least 2.0 standard deviations below its 48-bar mean; exit at the mean, at a
1.5 × ATR(20) stop, or after 12 bars. The claim: **net R per trade after costs is greater than
zero, and greater than a random-entry arm.**

**B7. Required observables.** Bar OHLC; 48-bar mean and standard deviation of close (or an
equivalent volatility-normalised deviation); ATR(20); a regime variable if a filter is used.

**B8. Available in the platform.** **[F]** The arithmetic is trivial and the resolution machinery
exists, but **there is no mean-reversion strategy in `baselines.py`** and no reference-price
module. **[F]** `detect_regime_changes` exists and could supply a regime label. This candidate
needs the most new signal code of the three, though it is still small.

**B9. Requires new data.** **[F]** None for the core version. **[E]** A serious version would
benefit from order-flow or liquidation data (taker imbalance is available as a bar-level
`taker_buy_*` field; true liquidation prints are not), and from a perp/funding venue to test the
short side, which the spot proxy cannot.

**B10. Expected trading frequency.** **[E]** On 4h bars with a ±2σ trigger, 100–400 events across
the split. High enough to be testable.

**B11. Expected holding period.** **[E]** Hours to ~2 days. Short by construction: the exit is the
mean, which is near the entry.

**B12. Cost sensitivity.** **[E]** **High, and structurally so.** Mean reversion earns small moves:
a 2σ excursion on 4h bars might be 3–5% from the mean, but the *profit* is the retracement, and a
conservative exit near the mean captures most of the distance while a realistic exit captures
less. With a 1.5 × ATR stop (2–4%), `cost/R` can look acceptable while the *realised win* is a
fraction of R. Worse, the natural ratio is asymmetric: many +0.4R wins against −1R losses. A 26 bp
round trip is a large fraction of a 0.4R win. **[E]** This is the Setup 1 disease in a different
organ.

**B13. Bias and overfitting vulnerability.** **[E]** Moderate parameter count (lookback, z
threshold, exit reference, stop multiple, max hold) with **strong** risk of retrofitting a regime
filter until the 2022 crashes are excluded. Regime filters are the most seductive degrees of
freedom in this family because they can be justified after the fact by any drawdown period.
**[E]** Also sample-selection risk: a 3.5-year window with two enormous crashes and a strong
recovery is a specific regime mix, and a mean-reversion strategy's measured edge is a statement
about that mix.

**B14. What would show it is wrong?** **[E]** Net R ≤ 0 with the CI entirely negative; or a
positive mean driven entirely by a small number of trades; or a distribution whose left tail
(largest losses) accounts for more than the total net gain, i.e. an edge that exists only until
it doesn't.

### 3.2 The decisive problem for B on this venue **[E]**

Spot-only, long-only removes half the strategy. The canonical mean-reversion pair is long the
oversold and short the overbought; here only the long leg exists. That converts a
market-neutral-ish liquidity-provision strategy into **a leveraged bet that dips recover**, with
a short-volatility payoff and no short leg to hedge the crash regimes that dominate crypto. The
literature cited in B2 does not support the long leg alone being profitable after costs; it
supports reversal as a two-sided phenomenon.

This is not a parameter problem and cannot be fixed by tuning. B is the weakest candidate on the
constraint that matters most (economic feasibility under spot-only execution), and it is
discussed here mainly because it must be ruled out explicitly rather than by omission.

---

## 4. Candidate C — Volatility compression and expansion

### 4.1 The fourteen questions

**C1. What market behaviour is being exploited?** **[H]** A specific *state transition*: when
realised volatility has been unusually low relative to its own recent history and volume has dried
up, the market is coiled; the first sustained break out of that compressed range tends to continue
rather than immediately fail. The traded object is the interaction of a volatility state with a
directional trigger — not volatility, and not trend, alone.

**C2. Why might it persist?** **[L]** Volatility clustering is one of the most robust empirical
regularities in financial time series — the motivation for ARCH/GARCH (Bollerslev 1986): large
changes tend to be followed by large changes, small by small. A compression is the low-volatility
state of that process, and the transition out of it is where the clustering is observable.
**[L]** Breakout continuation after a range has its own literature: Holmberg, Lönnbark &
Lundström (2013) assess intraday opening-range breakout profitability and report significant
positive average returns, with the effect concentrated in volatile periods.
**[H]** The *specific* claim — that compression conditions the continuation — is not established
by either source. Volatility clustering predicts that expansion follows compression; it says
nothing about direction. That is exactly why C needs a directional hypothesis of its own.

**C3. Who creates it?** **[L]/[H]** Volatility clustering is usually attributed to information
arriving in clusters and to heterogeneous trader horizons. The mechanism specific to a breakout is
order-flow: resting liquidity accumulates at the edges of a well-defined range, and once it is
consumed, price must move further to find the next liquidity. **[H]** In crypto, stop clusters and
liquidation levels just outside a tight range are a plausible amplifier, making the post-breakout
move larger than the range that preceded it.

**C4. When should it work?** **[H]** When the compression is genuine (both realised volatility and
volume contract), the break is confirmed by a close outside the range rather than a wick, and the
broader market is not already in a violent trend that makes the range an artifact. **[E]** It
should work in transitions from quiet to active, which is most of the time in crypto.

**C5. When should it fail?** **[H]** When compression is a pause inside a larger move and the break
is a continuation that immediately reverses; when the break is a single wick with no follow-through
(false break); when the range is so tight that the stop distance cannot pay for costs (see §1.2);
and in persistent one-way trends, where a compression is just a rest and a breakout is late.

**C6. Simplest falsifiable version.** **[E]** See §7.4 for the pre-registered definition. In one
sentence: on 4h closed bars, when a compression state (short-window volatility ≤ 0.6 × long-window
volatility, with volume dry-up) lasting at least 6 bars resolves with a close above the highest
high of that compression window, enter long at the next 5m open, stop at the compression window's
low, target 2R, time-exit after 18 4h bars. The falsifiable claim is a **contrast**, not a level:
conditioned breakouts have higher net R per trade than unconditioned breakouts of the same 20-bar
high over the same window, and that difference is positive.

**C7. Required observables.** 4h OHLC and volume; trailing realised volatility at 5 and 20 bars;
trailing volume means; the compression window's high and low; entry-bar fill; 5m bars for
execution.

**C8. Available in the platform.** **[F]** Substantially. `detect_compression` in
`backend/app/services/research/events.py` already implements the coil-and-release definition with
`compression_ratio`, volume dry-up, `duration_bars`, `start_index`, and direction. `detect_displacement`
and `detect_volatility_expansions` cover the expansion side. **Gap [F]:** the detector emits
`range_5/10/20` (mean true ranges) but **not the compression window's high and low**, and it emits
on the *release* bar rather than on a range break. Both are small additions, but they are
additions: the existing detector cannot be used unchanged as a Strategy 2 trigger.

**C9. Requires new data.** **[F]** None. 4h and 5m series both exist. **[E]** A better version
would use order-book depth data to identify liquidity clusters at the range edges; that data is
not collected.

**C10. Expected trading frequency.** **[E]** A compression lasting ≥6 4h bars (≥24 hours) happens
often, plausibly on the order of **once every 5–15 days**, i.e. roughly **100–250 events across the
3.5-year split**. This is the highest-frequency candidate that still clears the cost constraint.
**[H]** Estimate only; must be measured by the pre-scoring census in §8.

**C11. Expected holding period.** **[E]** 1–5 days. The 2R target and 18-bar time exit bound it.

**C12. Cost sensitivity.** **[E]** **Moderate, and controllable by construction.** The structural
stop (compression window low) is wide because the window spans days, so `cost/R` is typically
0.08–0.15. The genuine risk is the opposite: a very tight compression produces a *narrow* range
and therefore a *small* R, which is the Setup 1 failure in miniature. The design answers this with
an explicit feasibility gate — reject any signal whose `cost/R` exceeds 0.20 — rather than by
hoping.

**C13. Bias and overfitting vulnerability.** **[E]** Moderate. The definition has five
pre-registerable numbers (volatility window, compression ratio, volume ratio, minimum duration,
stop reference) but every one of them has a *default already in the repository* — a rare and
valuable property, because it lets the design be adopted rather than fitted. **Main risk [E]:**
the temptation to tune the compression ratio after seeing which events "look like" good
breakouts. Second risk: the control arm (unconditioned breakouts) is essential and must be
pre-declared, since without it C is just breakout trading with a filter and cannot distinguish
conditioning value from generic long beta.

**C14. What would show it is wrong?** **[E]** Any of: conditioned net R ≤ 0 with a CI entirely
negative; conditioned net R positive but **not** different from the unconditioned control
(demonstrating the compression state adds nothing); a cost/R median above 0.20 after the gate; a
same-bar share above 15%; or a portfolio that exhausts capital on a minority of the window.

---

## 5. Economic feasibility and execution analysis

The three levels must be kept apart. Setup 1 is the cautionary example: its signal level was
−0.2227R, its funded-subset gross R was −0.0665 **[F]** (a 70% selection effect from feasibility),
and its portfolio lost essentially all capital in six months.

### 5.1 Level A — signal-level statistical expectancy

Gross R per resolved observation, unconstrained by capital. This level answers "is there
information?" and nothing else.

| candidate | plausibility of a gross edge **[H]** | main threat at this level |
|---|---|---|
| A | Moderate; the least ambiguous literature support | Long-only spot cannot express the short leg that most TSMOM evidence depends on |
| B | Moderate; well documented two-sided | Half the documented effect is unavailable long-only |
| C | Moderate; conditioning claim unproven | Without the control arm, any measured edge is unattributable |

### 5.2 Level B — executable trade-level expectancy

Net R after the frozen cost model, with feasibility applied per trade (`cost/R ≤ ceiling`, minimum
notional, lot step). This is where Setup 1 died: 85.6% of candidates failed before the portfolio
existed **[F]**.

| candidate | `cost/R` at a typical stop **[E]** | feasible share of events **[E]** |
|---|---|---|
| A | 0.07–0.13 | High (most stops are wide) |
| B | 0.15–0.35, but realised wins are a fraction of R | Moderate, and the survivors are the widest-deviation (most dangerous) events |
| C | 0.08–0.15 after the 0.20 gate | Moderate; the gate is doing real work |

### 5.3 Level C — capital-constrained portfolio

Net results with $10,000 equity, minimum order $5, 1% nominal risk, spot cash cap, one position at
a time. Setup 1's portfolio never had a chance: 94.4% of entries were cash-cap bound and median
realised risk was 39.8% of nominal **[F]**.

**[E]** A wide-stop design changes this materially. With a stop 2% from entry, a 1%-of-equity risk
budget implies a position notional of ~50% of equity — inside the cash cap. The cash cap should
therefore bind far less often, and the nominal 1% figure should describe something closer to real
risk. That is a *prediction to be checked*, not an established result.

### 5.4 Can each candidate avoid Setup 1's specific weaknesses?

| Setup 1 weakness **[F]** | A | B | C |
|---|---|---|---|
| `cost/R` too high (85.6% infeasible) | Avoided: wide ATR stops | **Not avoided**: small realised wins vs wide stops | Avoided: wide structural stop + explicit gate |
| Cash cap binds (94.4%) | Mostly avoided at 2–4% stops | Partly avoided | Mostly avoided |
| Same-bar ambiguity (24.6% / 38.4% of P&L) | Avoided by days-long holds | Partly: exits are near entries | Avoided: 4h signal, 5m resolution, days-long hold |
| Cost > gross loss | Avoided by low turnover | **At risk**: high turnover, small edges | Avoided by low turnover |
| Beta confounding | **Severe**: long-only trend ≈ timed beta | Moderate | Moderate, mitigated by control arm |
| Statistical power | **Weak**: ~50–170 trades | Adequate | Adequate |

Only candidate B fails to address the central economic failure. Candidate A addresses it and
introduces a confounding failure. Candidate C addresses both, at the cost of more new code and a
narrower, less-certain premise.

---

## 6. Experimental design

Common to all three, because the mistakes it prevents are common:

**Pre-registration.** The protocol (signal definition, parameters, metrics, rejection criteria) is
written and hashed *before* any scoring run, exactly as `STAGE6_V2_PROTOCOL.md` was. Nothing is
changed after seeing results; a change requires a new numbered protocol and a fresh run.

**Three levels, reported separately.** Gross signal R, net executable R, capital-constrained
portfolio. Never interchange them, never report a portfolio number as a signal result.

**Primary metric.** Net R per trade at the executable level, with the frozen cost model. Portfolio
equity is a secondary, diagnostic output — Setup 1's $4.98 demonstrates how uninformative a
terminal equity can be.

**Dependence.** Report both an episode-cluster bootstrap (overlapping windows collapsed) and a
14-day block bootstrap, matching Stage 6's frozen block length so results are comparable **[F]**.
Report the episode-to-trade ratio; if it is below ~3:1, the effective sample is much smaller than
the trade count suggests.

**Same-bar ambiguity.** Primary convention stop-first, identical to the frozen baseline for
comparability. Always report the share of ambiguous resolutions and the tie-win sensitivity. A
design whose conclusion flips between tie conventions has not established its result, and should
say so.

**Cost sensitivity.** The same ten scenarios (0.5×–3×, refiltered and fixed universes) and the same
accounting identities. Do not rank scenarios by final equity **[F]**.

**Controls (non-negotiable).** For every candidate: (i) a random-entry arm with the same stop,
target and holding-period distribution; (ii) buy-and-hold over the same window, for time-in-market
comparison; (iii) for C only, the unconditioned-breakout arm, which is the whole point of the
experiment.

**Look-ahead.** Reuse `backend/app/services/research/lookahead.py` on every detector; require it
to pass before scoring. Every event must carry the bar at which it became knowable, and entries
must happen at or after the next bar's open.

**Multiplicity.** Three candidate families were compared; only one is pre-registered for testing.
If the others are ever run, the result is exploratory and cannot be reported as confirmatory
without a correction.

---

## 7. Comparison matrix

Qualitative by design. A numeric score would imply a precision that this analysis does not have;
column entries say *why* the ranking is what it is.

| Dimension | A — Trend following | B — Mean reversion | C — Volatility compression/expansion |
|---|---|---|---|
| **Economic rationale** | Strongest literature: time-series momentum across 58 futures **[L]**, crypto cross-sectional momentum **[L]**, though Grobys & Sapkota (2019) find the crypto cross-section less supportive **[L]**. Mechanism is behavioural and flow-based. | Coherent: liquidity provision earns the reversal **[L]**. But the documented effect is two-sided, and this venue is long-only, so only the crash-exposed half is tradable. | Clustering of volatility is the most robust regularity available **[L]**, but it predicts *expansion*, not direction. The directional claim is a genuinely new hypothesis — which is both its weakness and its value. |
| **Falsifiability** | Moderate. "Net R > 0" is falsifiable but nearly untestable at this sample size, and confounded by beta. | Good. Mean R > 0 is falsifiable and the sample is large. | Best. The claim is a *contrast* against an unconditioned control, so a null result is informative rather than ambiguous — it isolates the state variable. |
| **Required data** | 4h OHLC. Existing. | 4h OHLC; optional regime variable. Existing. | 4h OHLC + volume, plus 5m for execution. Existing, including taker-buy volume if needed. |
| **Existing platform support** | Highest: `SmaTrendStrategy`, `DonchianBreakoutStrategy`, ATR helper already implemented **[F]**. | Lowest: no mean-reversion strategy or reference-price module **[F]**; `detect_regime_changes` exists. | High but incomplete: `detect_compression` implements the state with repository defaults **[F]**, but emits on release and does not expose the range high/low — two small additions. |
| **Expected turnover** | Lowest: ~15–50 entries/yr **[E]**. | Highest: ~100–400 over the split **[E]**. | Middle: ~100–250 over the split **[E]**. All subject to the §8 census. |
| **Expected holding period** | 2–15 days. | Hours to ~2 days. | 1–5 days. |
| **Cost sensitivity** | **Low.** Wide ATR stop; `cost/R` ~0.07–0.13. | **High.** Small realised wins against wide stops; high turnover; the surviving trades are the most extreme deviations. | **Low–moderate**, with a structural trap (narrow ranges → small R) closed by an explicit `cost/R ≤ 0.20` gate. |
| **Capital efficiency** | Good: 1% risk with a 2–4% stop implies ~25–50% of equity per position, inside the spot cap. Long flat periods in cash. | Poor-to-moderate: frequent entries, small risk per trade, cash cap binds less often than Setup 1 but the payoff is small. | Good, similar to A; one position at a time and days-long holds mean the spot cap rarely binds. |
| **Intrabar ambiguity** | Low. Days-long holds resolved on 5m bars. | Moderate. Exits near entries, so same-bar resolution is plausible. | Low. 4h signal / 5m resolution; same-bar share should be a small fraction, and is a stated rejection criterion if it exceeds 15%. |
| **Overfitting risk** | Low parameter count, **high confounding risk** (beta). The likely error is misinterpretation, not curve-fitting. | Moderate parameters, **high** retrofitting risk (regime filters), and moderate selection risk from a crash-heavy window. | Moderate parameters, all with prior repository defaults; main risk is post-hoc tuning of the compression ratio, and omission of the control arm. |
| **Implementation complexity** | Lowest: baselines exist; needs only a strategy wrapper and the standard resolution path. | Low–moderate: new signal arithmetic, but single timeframe and no new resolution pattern. | Highest: needs multi-timeframe aggregation (4h state → 5m execution) plus range-boundary exposure from the compression detector. |
| **Robustness potential** | Good in the sense of surviving parameter perturbation, poor in the sense of surviving a benchmark comparison. | Poor: the edge is regime-conditional and the left tail is the dominant risk. | Good: a state-conditioning claim can be probed by perturbing the compression threshold and checking that the *contrast*, not just the level, survives. |
| **Verdict** | Safest to build, weakest to interpret. | Ruled out on economic grounds under spot-only execution. | Best balance of testability and independence; costs the most new code. |

---

## 8. The census that must precede any scoring

Before a single P&L number is computed, each candidate should be run in **counting mode only**:
how many events occur in the development split, how long they last, how many survive the
feasibility gate, and what the `cost/R` distribution looks like. This is cheap, uses no outcome
data, and it kills designs that cannot be tested before any effort is spent on them.

Pre-declared gates **[E]**:

| gate | threshold | why |
|---|---|---|
| Eligible events in the dev split | ≥ 200 | Below this, a 0.15R edge is not distinguishable from noise (§1.3) |
| Median `cost/R` | ≤ 0.20 | Above this, costs are a fifth of the risk unit — the Setup 1 disease |
| Episode-to-trade ratio | ≥ 3:1 | Otherwise effective n is far below nominal n |
| Same-bar share (if measurable at census time) | ≤ 15% | Keeps the OHLC ambiguity from dominating the sample |

A candidate that fails a gate is reported as **untestable on this data**, which is a result. It is
not a licence to relax the gate.

---

## 9. What this analysis does not establish

- No claim that any candidate is profitable. No expectancy, win rate, or return is estimated.
- **[H]** Turnover, holding period, event counts and `cost/R` ranges are engineering estimates.
  The §8 census exists precisely because they are unverified.
- **[L]** The literature is cited for *mechanisms*, on other markets and other sample periods.
  None of it establishes an edge on BTCUSDT 2021–2026 under a Binance spot proxy.
- **[E]** The cost model (0.1% fee, 3 bps adverse per side) is a frozen assumption, not a Nobitex
  measurement. Every `cost/R` figure here inherits that.
- **[F]** The 5-minute grid cannot resolve intrabar ordering. Nothing in this document changes
  that; it only proposes designs where the ambiguity touches a smaller share of the P&L.
- **[F]** No short leg is available in a spot-only implementation, which is a binding constraint on
  B and a limitation on A.

### Open questions that require data or sources, not opinion

1. **Nobitex fee tiers, tick/lot/min-notional rules, and realised spread.** Without these, every
   cost figure is a Binance proxy, and `cost/R` may be materially worse on the actual venue.
2. **Whether BTCUSDT 4h and 5m series align bar-for-bar** (the 4h manifest reports zero gaps, the
   5m reports 7 gaps / 213 bars **[F]**). A multi-timeframe design must resolve this before it can
   claim a clean execution grid.
3. **Order-book depth at range edges**, which is what would make the C3 liquidity mechanism
   measurable rather than asserted.
4. **A second instrument**, which would allow a cross-sectional comparison and remove the
   single-asset beta confound that limits A.

---

## 10. References

Cited for mechanisms only. Each was checked against its publisher or repository page; none was
read as evidence about this dataset.

1. Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of
   Financial Economics*, 104(2), 228–250.
   https://www.sciencedirect.com/science/article/pii/S0304405X11002613
2. Liu, Y., Tsyvinski, A., & Wu, X. (2022). Common risk factors in cryptocurrency. *Journal of
   Finance*, 77(2), 1133–1177. https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119
3. Grobys, K., & Sapkota, N. (2019). Cryptocurrencies and momentum. *Economics Letters*, 180,
   6–10. https://www.sciencedirect.com/science/article/pii/S0165176519301077
4. Nagel, S. (2012). Evaporating liquidity. *Review of Financial Studies*, 25(7), 2005–2039.
   https://academic.oup.com/rfs/article-abstract/25/7/2005/1602153
5. Wen, Z., Bouri, E., Xu, Y., & Zhao, Y. (2022). Intraday return predictability in the
   cryptocurrency markets: Momentum, reversal, or both. *North American Journal of Economics and
   Finance*, 62, 101733. https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833
6. Holmberg, U., Lönnbark, C., & Lundström, C. (2013). Assessing the profitability of intraday
   opening range breakout strategies. *Finance Research Letters*, 10(1), 27–33.
   https://www.sciencedirect.com/science/article/abs/pii/S1544612312000438
7. Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of
   Econometrics*, 31(3), 307–327. https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf
8. Shen, D., Urquhart, A., & Wang, P. (2022). Bitcoin intraday time series momentum. *Financial
   Review*. https://onlinelibrary.wiley.com/doi/10.1111/fire.12290

**Repository artifacts referenced** (all read-only, none modified):
`stage6_rebuild_v2/STAGE6_INTERPRETATION_ADDENDUM.md`,
`stage6_rebuild_v2/DEVELOPMENT_EXPERIMENT_REGISTRY.md`,
`stage6_rebuild_v2/DEVELOPMENT_FREEZE_MANIFEST.json`,
`stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md`,
`stage6_rebuild_v2/config.json`,
`stage6_rebuild_v2/stage6_v2_summary.json`,
`stage6_acceptance_audit/acceptance_audit.json`,
`stage6_acceptance_audit/independent_portfolio_audit.json`,
`backend/app/services/research/events.py`,
`backend/app/services/backtest/baselines.py`,
`backend/app/services/research/lookahead.py`,
`backend/data/datasets/manifest.json`,
`docs/ARCHITECTURE.md`.
