# Stage 2M — Economic Objective and Cost Framework

**Stage:** 2M (research-governance and methodology design only)
**Status:** proposal requiring owner approval. No strategy is developed, no market data is processed,
and no performance metric is calculated from historical data.
**Date:** 2026-11-09 (UTC)

**Evidence labels:** **Verified fact** (repository-supported, cited), **Interpretation** (reasoned
conclusion), **Proposal** (suggested methodology requiring approval), **Owner decision** (cannot be
made by the research agent).

---

## 0. Purpose

This document addresses the first question a research programme must answer before it counts
anything: **what economic result would make the research worth doing, and what would it cost to
obtain it?**

It proposes:

1. a structure for the research estimand;
2. a set of minimum-meaningful-effect definitions and their consequences;
3. a risk and capital context;
4. a component-by-component execution-cost framework;
5. venue-specific evidence requirements;
6. a rule for handling cost uncertainty.

It does **not** choose the owner's minimum effect, risk tolerance, capital base, or venue. Those are
recorded as owner decisions in `OWNER_DECISION_REGISTER.md`.

**Verified fact:** the historical programme used opportunity counts, a 26 bp Binance cost proxy, a
`0.15R` design assumption, and a 150-opportunity floor. It never declared an owner-approved minimum
net economic effect, an acceptable drawdown, a capital target, or a primary return estimand
(`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §7.3 and §8.3;
`docs/research/stage2k/STAGE2K_FINAL_RECOMMENDATION.md` §7).

---

## 1. The economic question

A defensible research programme should begin with a decision, not a detector. The decision is
whether to allocate capital, time, and risk to a trading rule. That decision requires four inputs:

1. **A target effect:** how much net economic benefit per unit of risk or capital would make the
   rule worth operating?
2. **A risk limit:** what loss, drawdown, or tail outcome would make the rule unacceptable even if
   its average return were attractive?
3. **An execution context:** at what capital, position size, venue, order type, and frequency would
   the rule actually be run?
4. **An evidence standard:** how much uncertainty about the target effect is tolerable before
   committing capital?

**Proposal:** no future experiment should be authorized until these four inputs are written down and
approved. A hypothesis that cannot be connected to them is a research curiosity, not an investment
candidate.

---

## 2. The research estimand

### 2.1 Definitions

The following quantities are often used as if they were interchangeable. They are not.

| quantity | definition | unit | what it captures | what it ignores |
|---|---|---|---|---|
| **Gross return** | price change from entry to exit before costs | % or R | directional accuracy and payoff | fees, spread, impact, slippage, latency |
| **Net return after execution costs** | gross return minus all-in execution costs | % or R | what the trader actually keeps | frequency, capital utilization, path risk |
| **Net return per opportunity** | net P&L divided by all opportunities identified by the rule, including those not executed or not filled | currency or R per opportunity | value of the signal stream | execution feasibility, position sizing |
| **Net return per executed trade** | net P&L divided by executed trades | currency or R per trade | value of a trade actually taken | how many opportunities were missed, capital idle time |
| **Opportunity frequency** | opportunities per unit time (year, month, regime) | count / time | how often the rule can act | whether each action is profitable |
| **Capital utilization** | deployed notional or time-in-market relative to available capital | ratio or % | how hard the capital works | whether the deployed risk is wise |
| **Risk-adjusted performance** | return per unit of a risk measure (volatility, downside deviation, drawdown) | ratio | return relative to path risk | the absolute return, the tail, the sample uncertainty |
| **Maximum adverse outcomes** | worst trade, maximum drawdown, CVaR/expected shortfall, maximum adverse excursion, time under water | % or R | survivability and psychological feasibility | average return |
| **Performance stability** | consistency of the above across regimes, subperiods, sessions, or instruments | distribution or range | robustness to changing conditions | in-sample average |

### 2.2 Why they are not interchangeable

**Interpretation:** each metric answers a different decision question, and a rule can look good on one
and unacceptable on another.

- **Gross versus net.** A rule with a small gross edge can be unprofitable after realistic costs.
  The historical Candidate D is the clearest repository example: its pre-gate median `cost_R` was
  `0.322559`, and 250 of 295 pre-gate sessions failed the 26 bp gate
  (`docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md` §2 and §4). A gross-return study would not
  have revealed that.
- **Per opportunity versus per executed trade.** If many signals are not filled, not fundable, or
  expire, the per-opportunity and per-trade values diverge. A rule that identifies many
  opportunities but executes few may be economically worse than a rule with fewer, executable ones.
- **Frequency versus per-trade edge.** Total contribution is approximately frequency multiplied by
  per-trade net edge, subject to capital and risk limits. A high-frequency, tiny-edge rule and a
  low-frequency, large-edge rule can have the same average contribution but very different
  testability, cost sensitivity, and operational burden.
- **Capital utilization versus return.** A rule that is idle most of the year can have an attractive
  per-trade return and a poor return on capital. A rule that is always invested can have a good
  return on capital and an unacceptable tail.
- **Risk-adjusted versus absolute.** Two rules with the same Sharpe ratio can have very different
  drawdowns, skew, and ruin risk. A ratio is not a substitute for a risk limit.
- **Maximum adverse outcomes versus average.** A positive average can coexist with a drawdown that
  the owner cannot tolerate or a tail that threatens the account.
- **Stability versus average.** A result driven by one regime or one cluster of episodes may not
  generalize. The historical concentration diagnostics are a warning: Candidate D's design effect
  was 3.93 and its cost-feasible signals were concentrated in 2021–2022
  (`docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md` §6;
  `docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §7.4).

### 2.3 Proposed primary and secondary metrics

**Proposal (not an owner decision):** the following hierarchy is offered for review. It is designed
to be scale-free, comparable to the historical risk unit, and connected to the owner's capital
decision.

| role | metric | rationale | required companion reporting |
|---|---|---|---|
| **Primary** | **net return per executed trade in R**, after all-in execution costs, with a frozen exit and holding policy | R is the risk unit already used by the historical specifications; it is scale-free across volatility and directly comparable to the stop | net return in % of notional; number of executed trades; execution/fill rate; cost estimate used |
| **Co-primary (decision)** | **net annual contribution to the owner's capital** at the declared capital, risk-per-trade, and position-sizing policy | captures frequency, utilization, and the owner's actual objective; prevents a high per-trade edge with negligible annual contribution from passing | capital base; risk per trade; average concurrent positions; idle-capital assumption; compounding convention |
| **Secondary** | net expectancy per opportunity | distinguishes signal quality from execution and funding | opportunity definition; fill/expiry/rejection rates |
| **Secondary** | opportunity frequency and capital utilization | determines whether the annual contribution is achievable | by year, regime, session, and cluster |
| **Secondary** | maximum drawdown, worst trade, CVaR/expected shortfall, maximum adverse excursion, time under water | captures survivability and tail risk | confidence level; sample size; dependence treatment |
| **Secondary** | performance stability across regimes and subperiods | tests robustness and representativeness | regime definitions; subperiod results; dependence-adjusted uncertainty |
| **Diagnostic** | gross return, win rate, average win/loss, profit factor, turnover, Sharpe/Sortino | familiar descriptive statistics | explicitly labelled descriptive; not the decision rule |

**Interpretation:** the primary metric should answer "is a trade worth taking after costs?" The
co-primary decision metric should answer "is the resulting annual contribution worth the capital and
risk?" Neither alone is sufficient. A rule that passes the primary but fails the co-primary is a
research result, not an investment candidate. A rule that passes the co-primary but fails the
primary is likely benefiting from frequency or leverage rather than per-trade edge, which is fragile.

**Owner decision:** the owner must approve or replace this hierarchy. In particular, the owner must
decide whether the primary estimand is R-based, notional-based, or annual-return-based. The
consequences are set out in §3.

---

## 3. Minimum meaningful effect

### 3.1 Why a minimum effect is required

A statistical test can detect a non-zero effect that is too small to matter. The historical programme
assumed a `0.15R` effect of interest but never established that this was the owner's economic
threshold, and its 150 floor was sufficient only for an effect near `0.23R` under independence
(`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §7.3). That is a design inconsistency, not a market
finding.

**Proposal:** before any future experiment, the owner declares a **minimum meaningful effect (MME)**.
The MME is the smallest true net effect that would justify the cost, risk, and effort of operating
the rule. It is a decision input, not an estimate from data.

### 3.2 Options

| option | definition | advantages | disadvantages | what the owner must also specify |
|---|---|---|---|---|
| **M1 — net R per executed trade** | `δ_R`: minimum average net profit per trade, expressed in units of initial stop risk | scale-free; comparable across volatility; directly tied to the stop; simple to pre-register | ignores frequency and capital; a high `δ_R` with two trades a year may be irrelevant; R depends on the stop definition | exit/holding policy; whether R is based on initial or trailing stop; treatment of partial exits |
| **M2 — net expectancy per opportunity** | `δ_O`: minimum average net profit per identified opportunity, including unfilled or unfunded ones | captures signal quality and execution losses; penalizes rules that identify many unusable opportunities | depends on the opportunity definition; can be diluted by opportunities the rule would never trade | opportunity definition; treatment of expired/rejected signals; fill assumptions |
| **M3 — net return on notional per trade** | `δ_N`: minimum average net return as a percentage of entry notional | intuitive; independent of stop size; comparable to funding costs | ignores risk; a high notional return with a wide stop can be poor risk-adjusted value | position-sizing rule; leverage; cost basis |
| **M4 — annualized net return on capital** | `δ_A`: minimum average annual net return on the owner's capital | directly answers the owner's capital question; captures frequency and utilization | depends on compounding, idle capital, position sizing, and the sample period; noisy and regime-sensitive | capital base; compounding convention; treatment of idle cash; risk limit |
| **M5 — net annual contribution (currency)** | `δ_C`: minimum average annual net profit in the owner's currency | avoids percentage ambiguity; directly spendable | depends on capital scale; not comparable across owners; ignores risk | capital base; currency; risk limit |
| **M6 — risk-adjusted ratio** | e.g., minimum Sharpe, Sortino, or Calmar | captures return per unit of risk | ratios are unstable in small samples, sensitive to the risk measure, and can hide tail risk; not a complete objective | risk measure; benchmark; sample period; tail treatment |
| **M7 — certainty-equivalent utility** | minimum certainty-equivalent return under an owner-specified utility function | incorporates risk aversion directly | requires a utility specification the owner may not be able to defend; sensitive to assumptions | utility function; risk aversion; horizon |

### 3.3 Consequences of different choices

**Interpretation:**

- Choosing **M1** makes the experiment about per-trade edge. It is the cleanest statistical target,
  but it can authorize a rule that is economically negligible because it trades too rarely.
- Choosing **M2** makes the experiment about the full signal stream. It is stricter than M1 when
  execution losses are material, but it depends on a contestable opportunity definition.
- Choosing **M3** makes the experiment about notional return. It can favour tight-stop, high-turnover
  rules and can obscure the risk taken to earn the return.
- Choosing **M4 or M5** makes the experiment about the owner's capital outcome. It is the most
  decision-relevant, but it requires a capital and position-sizing policy and is the noisiest in a
  short sample.
- Choosing **M6** makes the experiment about risk-adjusted efficiency. It is useful as a secondary
  metric but risky as a primary target because ratio estimators have poor small-sample properties
  and can be improved by reducing measured volatility rather than improving returns.
- Choosing **M7** is the most theoretically complete but the least practical without a stable utility
  specification.

**Proposal:** use **M1 as the primary statistical estimand** and **M4 or M5 as a co-primary economic
constraint**, with M2, M3, M6, and tail metrics as secondary. This combination answers both "is a
trade worth taking?" and "is the annual outcome worth the capital?" without reducing the decision to
a single ratio. It is a proposal; the owner may choose otherwise.

**Owner decision:** the MME definition and value. The research agent must not invent a number. A
number chosen after seeing outcomes would invalidate the pre-registration.

### 3.4 Relationship between per-trade effect and annual contribution

**Interpretation (conceptual, not a historical calculation):** under fixed-fractional risk, the
approximate annual net return before compounding is:

```
annual net return ≈ δ_R × risk_per_trade × executed_trades_per_year
```

where `δ_R` is net R per trade and `risk_per_trade` is the fraction of equity risked per trade. This
relationship is why frequency and position sizing cannot be omitted from the objective. A rule with
`δ_R = 0.15R` and 20 trades per year at 1% risk per trade implies roughly 3% annual gross
contribution before compounding and before any allowance for idle capital, while the same `δ_R` with
200 trades implies roughly 30%. The numbers are illustrative arithmetic, not a forecast and not a
recommendation. They show that the owner's MME must be stated in a way that makes the frequency
requirement visible.

**Proposal:** the owner should state the MME in the primary metric **and** state a minimum annual
contribution or annual return. The two together define the opportunity-frequency requirement that
Gate 3 will test.

---

## 4. Risk, drawdown, and unacceptable outcomes

### 4.1 Why a return target is not enough

A rule can have a positive expected return and still be unacceptable if its path includes a drawdown
the owner cannot survive, a tail loss that threatens the account, or a period of underperformance
that forces abandonment at the worst time.

**Verified fact:** the historical capital geometry assumed `$10,000` equity, 1% risk per trade, one
position, spot long-only, and no leverage
(`docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6). Those are research conventions, not
an owner-declared risk policy.

### 4.2 Risk dimensions the owner must address

| dimension | definition | example framing (not a recommendation) | why it matters |
|---|---|---|---|
| **Maximum drawdown** | largest peak-to-trough decline in equity | "I will not tolerate a drawdown greater than X% of equity" | determines survivability and whether the owner can stay with the rule |
| **Per-trade loss limit** | maximum loss on a single trade, in R or % of equity | "no single trade may lose more than 1R / X% of equity" | controls tail risk and position sizing |
| **Tail loss** | CVaR/expected shortfall at a stated confidence level, or worst observed trade | "the average loss in the worst 5% of outcomes must not exceed XR" | captures the losses that averages hide |
| **Maximum adverse excursion** | worst unrealized loss during a trade | "I must be able to hold through X R of adverse movement" | tests psychological and margin feasibility |
| **Time under water** | longest period below a prior equity high | "I will not accept more than X months below the high-water mark" | tests patience and opportunity cost |
| **Probability of ruin** | probability of losing a stated fraction of capital under the assumed distribution | "probability of losing 50% of capital must be below X%" | connects risk to capital survival |
| **Concentration** | share of risk or exposure in one episode, regime, session, or instrument | "no single episode may contribute more than X% of risk" | prevents a single market event from dominating the result |
| **Liquidity and position size** | ability to enter and exit at the intended size | "position size must be no more than X% of visible depth" | prevents a statistically valid rule from being unexecutable |
| **Operational risk** | venue outage, withdrawal restriction, API failure, regulatory change | "the rule must survive X hours of venue unavailability" | captures risks outside the price series |

**Proposal:** the owner should declare at least a maximum drawdown, a per-trade loss limit, a tail
measure, and a liquidity/position-size constraint before any experiment. The others can be added if
the owner considers them binding.

**Owner decision:** the acceptable risk profile. A framework cannot choose it, because it depends on
the owner's capital, obligations, and tolerance.

### 4.3 Relationship between risk and the MME

**Interpretation:** the MME should be stated net of the risk taken. A `0.15R` net effect with a 1R
stop is not the same as a `0.15R` effect with a 2R stop. The framework therefore requires the primary
metric to be R-based and the risk limits to be stated in the same R units, so that the return and the
risk are commensurable.

---

## 5. Capital, position sizing, and execution context

### 5.1 Why the capital base matters

A per-trade effect is independent of capital; an annual return is not. The same rule can be viable
on one capital base and impossible on another because of minimum notional, lot size, fees, and the
number of concurrent positions.

### 5.2 Context the owner must declare

| item | why it matters | historical value (for reference only) |
|---|---|---|
| **Equity base** | determines position size and the meaningfulness of percentage returns | `$10,000` research convention (`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6) |
| **Risk per trade** | converts R into capital and determines the position size | 1% (`$100`) research convention |
| **Position sizing** | fixed fractional, fixed notional, volatility-targeted, or other | fixed fractional implied by the 1% rule |
| **Concurrent positions** | affects capital utilization and concentration | one position |
| **Leverage** | amplifies both return and risk; may be unavailable | none; spot long-only |
| **Direction** | long-only, short-only, or both | long-only |
| **Venue** | determines fees, spread, depth, and operational constraints | Binance data; Nobitex execution mentioned but unverified |
| **Order type** | market, limit, stop, IOC/FOK; determines fill and cost | next-bar-open entry assumed |
| **Minimum notional and lot size** | can make small positions infeasible | not measured |
| **Funding and withdrawal** | affects available capital and operational risk | not measured |
| **Taxes and regulatory costs** | affect net return | not measured |

**Verified fact:** the historical framework did not model order-book depth, partial fills, latency,
or venue-specific minimum notional. It used a simple capital-geometry check and a next-bar-open
entry assumption (`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6;
`docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §8.2).

**Proposal:** the owner should distinguish between a **research capital basis** (used to make the
experiment comparable and to check fundability) and the **actual capital** that would be deployed.
The research basis can remain `$10,000` and 1% risk if the owner approves it, but it must be labelled
as a convention, not as the owner's real account.

**Owner decision:** the capital and execution context. If the owner intends to deploy a different
amount, the annual-contribution calculation changes and the liquidity constraint must be re-checked.

### 5.3 Capital utilization

**Proposal:** report at least three utilization measures:

1. **Notional utilization:** average deployed notional divided by equity.
2. **Time utilization:** fraction of time with at least one open position.
3. **Concurrency:** distribution of simultaneous positions and the maximum.

**Interpretation:** a high per-trade edge with low time utilization can produce a low return on
capital. A high notional utilization with one position can concentrate risk. Neither is inherently
good or bad; the owner must decide which trade-off is acceptable.

---

## 6. Statistical detectability versus economic usefulness

### 6.1 The distinction

| concept | question | typical evidence | failure mode |
|---|---|---|---|
| **Statistical detectability** | is the estimated effect distinguishable from zero at the declared error rate? | confidence interval excluding zero; hypothesis test | a tiny effect can be "significant" with enough data |
| **Economic usefulness** | is the effect at least the owner's MME, after costs and risk? | lower confidence bound at or above the MME; risk constraints satisfied | a large point estimate with a wide interval can be inconclusive |

**Interpretation:** the historical framework conflated the two. It used a count floor (150) that was
neither derived from the MME nor sufficient for the stated `0.15R` effect, and it never tested an
outcome. A future framework must require both:

1. the effect is distinguishable from zero; and
2. the evidence is strong enough that the effect is at least the MME, not merely non-zero.

**Proposal:** the decision rule should be based on the **lower bound of a dependence-adjusted
confidence interval** for the primary metric, compared with the MME, plus the risk constraints. A
result whose interval includes both zero and the MME is **inconclusive**, not a pass.

### 6.2 Why a statistically significant result may be economically useless

**Interpretation:** with a large enough sample, a `0.01R` edge can be statistically significant. If
the owner's MME is `0.15R`, that result is economically irrelevant. Conversely, a `0.30R` point
estimate with a confidence interval of `[-0.10R, 0.70R]` is not evidence of a useful effect, because
it cannot rule out zero or an unacceptable loss. The decision must be based on the interval relative
to the MME, not on the p-value alone.

---

## 7. Execution-cost framework

Cost is not a single number. It is the sum of several components, each with a different data source,
uncertainty, and failure mode. The historical 26 bp figure is a proxy for the sum, not a measurement
of any component (`docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §1 and §7).

### 7.1 Components

| # | component | required information | how it should be measured | observable or estimated? | uncertainty representation | adequate evidence | unacceptable assumptions |
|---|---|---|---|---|---|---|---|
| 1 | **Trading fees** | maker and taker fee schedule, tier, effective dates, payment-token discounts, taxes | venue fee schedule; account tier; historical effective dates | directly observable from the venue | schedule version; range if tier changes | a dated fee schedule for the venue and account tier, with a version history | assuming Binance fees apply to Nobitex; using a current schedule for a historical period without effective-date evidence; ignoring maker/taker mix |
| 2 | **Bid-ask spread** | top-of-book bid/ask at the decision and exit times; distribution by session and volatility | historical quote/tick data or concurrent collection; sample at signal times | observable if quote data exists; otherwise estimated | distribution (median, p90, p99); by regime/session | measured spread distribution at the strategy's actual decision times, not a daily average | assuming zero spread; using a single average for all sessions; using the research venue's spread for the execution venue |
| 3 | **Market impact** | order size relative to visible depth; price response to the order | order-book depth snapshots; size-depth curve; controlled small live orders if authorized | observable with order-book/fill data; otherwise model-estimated | impact curve with confidence range; stress at larger sizes | evidence that the intended order size can be executed within a stated price band | assuming zero impact; assuming the top-of-book size is available; ignoring the strategy's own market effect |
| 4 | **Slippage** | difference between decision/arrival price and actual fill | paper/live fill logs; replay with order-book data; broker reports | observable from fills; estimated otherwise | distribution and worst-case; by order type and volatility | fill data at the intended size and order type, with a documented measurement method | assuming the signal price is the fill price; using best-case fills; ignoring latency |
| 5 | **Order type and execution assumptions** | market vs limit; IOC/FOK; post-only; stop order; cancellation policy | pre-specified execution policy; venue documentation; fill simulation | policy is a choice; fills are observed/estimated | fill probability and adverse-selection cost | a documented order policy with measured fill rates and rejection rates | assuming a limit order always fills at the touch; ignoring queue position; changing order type after seeing results |
| 6 | **Liquidity and depth** | order-book depth at multiple levels; minimum notional; lot size; typical volume | order-book snapshots; venue instrument specification | observable | depth distribution; maximum executable size at a price limit | evidence that the intended size is a small fraction of visible depth | assuming unlimited liquidity; ignoring minimum notional; ignoring lot-size rounding |
| 7 | **Partial fills and rejections** | fill rate, partial-fill distribution, rejection reasons | fill logs; venue reports; simulation | observable from logs; estimated otherwise | distribution of filled fraction; rejection probability | a documented fill model calibrated to observed data | assuming every order fills completely; ignoring rejected orders; dropping partial fills from the sample |
| 8 | **Latency and market movement** | signal-to-order latency; venue processing time; price movement during latency | timestamped logs; network measurements; replay | observable with instrumentation; estimated otherwise | latency distribution and its cost distribution | measured latency at the intended infrastructure and venue | assuming zero latency; using a research timestamp as the execution timestamp |
| 9 | **Entry/exit asymmetry** | different costs for entry and exit; stop orders vs limit exits; gap risk | separate measurement for entry and exit; stress scenarios | observed/estimated separately | separate entry and exit cost distributions | evidence for both legs, including forced exits | applying the entry cost to the exit; ignoring gap risk on stops |
| 10 | **Venue operational restrictions** | KYC, account limits, API rate limits, maintenance windows, withdrawal restrictions, regional access, taxes | venue documentation; account records; outage logs | documented/observed | scenario list and probability where possible | a documented operating envelope and outage history | assuming 24/7 availability; ignoring withdrawal or API limits; ignoring tax/regulatory costs |

### 7.2 How the components combine

**Proposal:** the all-in round-trip cost should be modelled as:

```
all_in_cost = entry_fee + entry_spread + entry_impact + entry_slippage
            + exit_fee  + exit_spread  + exit_impact  + exit_slippage
            + latency_cost + rejection_cost + operational_cost
```

where each term is expressed in the same unit (currency, % of notional, or R) and the sum is applied
to the same trade. The framework should report the distribution, not only the mean, because the
strategy's viability may depend on the upper tail.

**Interpretation:** the historical `cost_R` formulation treated cost as a fixed fraction of notional
and divided by the stop distance. That is a useful simplification, but it cannot represent
size-dependent impact, partial fills, or exit asymmetry. A future framework should retain the
`cost_R` view for comparability while reporting the component breakdown and the distribution.

### 7.3 What the historical proxy does and does not establish

**Verified fact:** the 26 bp figure is described in the frozen specifications as a Binance spot proxy
for fees plus adverse execution, not a Nobitex measurement
(`CANDIDATE_B_SPEC.md` §0.1; `CANDIDATE_D_SPEC.md` §0.1;
`SHARED_CENSUS_PROTOCOL.md` §1).

**Verified fact:** Candidate D's cost gate rejected 250 of 295 pre-gate sessions at 26 bp
(`stage2j/CANDIDATE_D_CENSUS_REPORT.md` §2 and §4). Candidate B's gate rejected 3 of 32
(`stage2j/CANDIDATE_B_CENSUS_REPORT.md` §4). The proxy therefore mattered much more for D than for
B.

**Interpretation:** the proxy may be too high or too low for Nobitex. Stage 2M does not assume either
direction. A verified cost study is required before any candidate is re-evaluated.

---

## 8. Venue-specific requirements

### 8.1 Binance BTCUSDT research data

**Verified fact:** the historical datasets are Binance BTCUSDT files under
`backend/data/datasets/` (`CANDIDATE_B_SPEC.md` §1; `CANDIDATE_D_SPEC.md` §1).

**Interpretation:** Binance is a legitimate research data source if its prices and liquidity are
representative of the execution venue. It is not automatically the execution venue. The following
must be distinguished:

- **Market-data venue:** where the candles and quotes come from.
- **Execution venue:** where orders would actually be placed.
- **Cost basis:** which venue's fees, spread, depth, and latency are used.

A study that uses Binance data and Binance costs but executes on Nobitex is measuring a different
market from the one it would trade.

### 8.2 Nobitex execution

**Verified fact:** Nobitex is named as the intended execution venue in the historical specifications,
but no Nobitex fee schedule, spread measurement, depth record, fill data, or outage record exists in
the repository (`CANDIDATE_B_SPEC.md` §0.1; `stage2j/STAGE2J_SUMMARY_AND_VERDICT.md` §4;
`STAGE2K_FINAL_RECOMMENDATION.md` §7 U1).

**Proposal:** before any Nobitex-executed experiment, obtain and document:

1. the current fee schedule and its effective dates, including maker/taker and any account-tier or
   payment-token effects;
2. top-of-book spread distribution at the strategy's decision times, by session and volatility
   regime;
3. order-book depth at the sizes implied by the declared capital and risk per trade;
4. minimum notional, lot size, and any maximum order size;
5. API latency and rate limits;
6. maintenance windows and outage history;
7. deposit, withdrawal, and settlement constraints;
8. any tax, regulatory, or account-level restrictions;
9. a paper-trading or small-size live measurement of fills and slippage, if the owner authorizes it.

**Do not assume:** that Nobitex costs are lower or higher than 26 bp; that Binance liquidity is
available on Nobitex; that the same order type behaves the same way; that the venue is continuously
available; that historical fees still apply.

### 8.3 Other venues

**Proposal:** any other venue can be considered only if the owner authorizes it explicitly. It must
meet the same evidence standard as Nobitex. A venue comparison must be pre-registered and must not
be used to rescue a candidate that failed on the primary venue. The primary venue should be declared
before the experiment, not chosen after seeing which venue makes the candidate pass.

### 8.4 Cost study protocol for a future stage

**Proposal:** a future cost study should follow this sequence:

1. **Freeze the decision times and order sizes.** Use the strategy's signal timestamps and the
   declared capital/risk policy. Do not sample convenient times.
2. **Collect venue fee evidence.** Dated schedules, account tier, maker/taker mix.
3. **Collect quote and depth evidence.** Top-of-book and multi-level depth at the decision times, or
   a pre-declared sampling plan that covers sessions and volatility regimes.
4. **Measure spread.** Report the distribution, not only the average.
5. **Estimate impact.** Use the size-depth curve; if live orders are authorized, use controlled
   small-size experiments and report the results.
6. **Measure fill and slippage.** Paper or live fills, with latency instrumentation.
7. **Model partial fills and rejections.** Calibrate to observed data; report the fill-rate
   distribution.
8. **Construct a conservative all-in cost distribution.** Include entry and exit asymmetry, latency,
   and operational costs.
9. **Freeze the cost model before the performance experiment.** Record hashes, versions, and data
   provenance. Subject the cost model to independent review if it is decision-critical.

**Resource note:** steps 1–3 and 5–7 may require external data or account access that the project does
not currently have. That is a reason to treat the cost study as a separately authorized stage, not a
reason to substitute an assumption.

---

## 9. Cost uncertainty policy

### 9.1 Principles

**Proposal:**

1. **Observed versus assumed.** Every cost input must be labelled as observed, estimated, or assumed.
   An assumed input cannot be presented as a measurement.
2. **Conservative primary.** The primary verdict should use a conservative estimate of all-in cost,
   such as a pre-specified upper percentile of the measured distribution or the upper bound of a
   documented range. The mean is not conservative.
3. **Documented range.** Report the full range and the component breakdown, not only the primary
   number.
4. **Sensitivity.** Report the result across a pre-specified set of cost scenarios. The scenarios
   should be derived from the measured range, not chosen to make the candidate pass.
5. **Anti-optimism rule.** A candidate that passes only under an optimistic cost scenario is not
   admissible. The primary decision uses the conservative estimate.
6. **No rescue by assumption.** A failed historical candidate cannot be revived by substituting a
   lower cost assumption without a measured venue-specific study and a new pre-registration.

### 9.2 How to represent uncertainty

| method | what it provides | limitation |
|---|---|---|
| **Point estimate plus range** | simple, transparent | does not give a probability statement |
| **Confidence interval for the mean cost** | sampling uncertainty | may understate tail and model uncertainty |
| **Predictive distribution** | full uncertainty for a future trade | requires a model and assumptions |
| **Scenario analysis** | decision robustness across plausible costs | scenario choices can be arbitrary |
| **Stress test** | worst-case viability | not a probability |

**Proposal:** report at least a conservative point estimate, a range, and a scenario table. If a
probabilistic model is used, state its assumptions and validate it against observed fills.

### 9.3 What would be unacceptable

- Using the 26 bp proxy as if it were a Nobitex measurement.
- Using a lower cost solely because it makes a candidate pass.
- Ignoring spread, impact, slippage, latency, partial fills, or exit asymmetry.
- Using a maker rebate without a measured fill probability.
- Using a current fee schedule for a historical period without effective-date evidence.
- Presenting a single average cost as if it described all trades.
- Omitting operational and venue restrictions because they are hard to quantify.

---

## 10. Owner decisions arising from this document

The following decisions are recorded in `OWNER_DECISION_REGISTER.md`. They are repeated here so that
this document is self-contained.

| ID | decision | why it cannot be made by the research agent |
|---|---|---|
| D-01 | minimum meaningful effect (definition and value) | depends on the owner's economic objectives and alternatives |
| D-02 | acceptable drawdown, loss, tail, and liquidity risk | depends on the owner's capital and tolerance |
| D-03 | primary performance estimand | determines what the experiment is allowed to conclude |
| D-04 | capital, position-sizing, and execution context | depends on the owner's actual resources and constraints |
| D-05 | execution venue and cost evidence standard | depends on the owner's access and willingness to collect evidence |
| D-06 | cost-uncertainty rule and whether to require a venue-specific study before any experiment | determines whether the primary verdict is conservative or assumption-driven |
| D-07 | whether annual contribution or annual return is a co-primary decision metric | connects per-trade edge to the owner's capital objective |

---

## 11. Summary

The historical framework measured opportunity counts and applied a cost proxy. It did not define the
economic result it was trying to establish, the risk it was unwilling to take, the capital context in
which the result would matter, or the execution cost of the venue it intended to use.

Stage 2M proposes a structure:

- **primary:** net R per executed trade after all-in costs;
- **co-primary:** net annual contribution at the declared capital and risk policy;
- **secondary:** expectancy per opportunity, frequency, utilization, drawdown, tail, and stability;
- **cost:** a component-by-component, venue-specific, uncertainty-aware measurement;
- **decision:** the lower confidence bound on the primary metric must meet the owner's MME, and the
  risk constraints must hold.

The structure is a proposal. The owner must supply the numbers, the risk limits, the capital
context, and the venue evidence standard before any experiment is authorized.
