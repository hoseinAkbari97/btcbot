# Stage 2O — D-01 / D-02 Numeric Owner-Decision Packet

**Stage:** 2O (owner-decision resolution only)
**Status:** **PENDING OWNER APPROVAL.** No numeric value in this packet is approved.
**Date:** 2026-11-10 (UTC)
**Starting repository state:** `main` at `f04b7246bd1c77b1d262a934dbde50b9cba66fce`, clean,
synchronized with `origin/main`.

**Scope:** this packet resolves **only** the outstanding numeric values of D-01 and D-02. It preserves
the definitions already selected in Stage 2N: D-01 definition **A** (net R per executed trade) and D-02
option **C** (drawdown, tail, and liquidity). It does not reopen any other decision.

**Source documents:** `stage2m/OWNER_DECISION_REGISTER.md`,
`stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md`,
`stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md`, `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`,
`stage2m/STAGE2M_FINAL_PROPOSAL.md`, `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`, and the historical
records cited below.

---

## 0. What this packet does and does not do

It presents, for each unresolved numeric value:

- the plain-language question;
- the metric, units, and measurement interpretation;
- the framework role and interactions;
- a small set of defensible alternatives, with exact values;
- the practical and statistical consequences;
- what is an owner preference and what is evidence-dependent;
- the documented recommendation, if one exists.

It does **not**:

- process market data, run a census, backtest, bootstrap, Monte Carlo, or optimization;
- compute P&L, expectancy, drawdown, Sharpe, Sortino, CAGR, or an equity curve;
- access validation or out-of-sample data;
- develop or evaluate a strategy;
- perform the Nobitex cost study or the D-13 audit;
- revisit D-15 or authorize Gate 0–5 progression;
- start Stage 2P.

**No numeric value is approved because it appears in this packet.** Only an explicit owner answer,
recorded in `STAGE2O_OWNER_RESPONSE_RECORD.md`, changes a status.

---

## 1. Starting state

### 1.1 Repository and integrity

| item | value |
|---|---|
| branch | `main` |
| HEAD at packet creation | `f04b7246bd1c77b1d262a934dbde50b9cba66fce` |
| remote tracking | `origin/main`, synchronized |
| working tree | clean before Stage 2O work |
| Stage 2M manifest self-hash | `6469d6a417681c9a6615d08ede9059a48aa104ab301c5bd42a17e4b24f54b0a9` — **matched** |
| Stage 2M deliverable hashes | six of six — **matched** |
| Stage 2M source-artifact hashes | twenty-one of twenty-one — **matched** |

The Stage 2M manifest was recomputed with the procedure recorded in its `hashing_procedure` field.
No Stage 2M file was modified.

### 1.2 Documents inspected

Stage 2M:

- `OWNER_DECISION_REGISTER.md` (complete);
- `ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` (complete);
- `STATISTICAL_SUFFICIENCY_FRAMEWORK.md` (complete);
- `RESEARCH_GOVERNANCE_PROTOCOL.md` (complete);
- `STAGE2M_FINAL_PROPOSAL.md` (complete);
- `FREEZE_MANIFEST.json` (structure and hashes).

Stage 2N:

- `OWNER_DECISION_RESOLUTION_RECORD.md` (complete).

Historical context:

- `stage2k/FAILURE_MODE_ANALYSIS.md` §7.3, §8.3;
- `stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §0, §4.3, §6.3, §7.3, §9.5;
- `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6, §6.7, §7;
- `stage2k/STAGE2K_FINAL_RECOMMENDATION.md` (as cited by Stage 2M).

### 1.3 Existing status of the in-scope and related decisions

| ID | existing status | what remains |
|---|---|---|
| **D-01** | **OPEN** — definition A selected | numeric `δ_R`; numeric annual contribution target; measurement interpretation |
| **D-02** | **OPEN** — option C selected | numeric maximum drawdown; per-trade loss; tail; liquidity; scope of application |
| **D-04** | resolved — research leg only | real-capital check remains open |
| **D-05** | resolved — staged A + B | Nobitex access remains unknown/open |
| **D-06** | resolved — conservative p95 | application pending a Nobitex cost distribution |
| **D-07** | resolved — co-primary | annual target pending D-01 |
| **D-15** | deferred | not in scope; remains deferred |

No carried qualification was upgraded, waived, or silently resolved in this packet.

### 1.4 Governing decisions not reopened

The following Stage 2N answers are treated as fixed inputs:

- **D-03:** primary **net R per executed trade**; co-primary **net annual contribution**.
- **D-04:** research leg `$10,000`, 1% risk per trade, fixed-fractional, one position, no leverage,
  spot long-only, next-bar-open market entry; real-capital check separate and open.
- **D-05:** Binance for research, Nobitex for execution; Nobitex access unknown/open.
- **D-06:** conservative primary at the **p95** of measured cost; sensitivity reporting mandatory;
  optimistic-only pass prohibited.
- **D-07:** annual contribution is **co-primary**.
- **D-08:** two-sided `α = 5%`, target power **80%**, **hierarchical** co-primary allocation.
- **D-09:** cluster-robust plus block bootstrap; disagreement is **inconclusive**; Kish and design
  effects descriptive only.
- **D-10:** power for the MME; dependence inflation; execution-rate adjustment; sensitivity to `DE`,
  `σ`, and `δ`.
- **D-11:** one primary hypothesis per stage; no multiple hypotheses; OOS confirmation required.
- **D-12:** strict one-look; access logging; embargo.
- **D-13:** separate reviewer plus external specialist if feasible; residual disclosure.
- **D-14:** volatility, trend, and liquidity regime coverage; later confirmation via the D-12 OOS look.

---

## 2. D-01 — Economic objective

### 2.1 What is already decided

**Definition A:** the minimum meaningful effect is expressed as **net R per executed trade**.

R is the initial stop risk of the trade. Net means after all-in execution costs under the D-06
conservative rule. The effect is per **executed trade**, not per identified opportunity.

### 2.2 Proposed measurement interpretation (not an owner decision)

The following interpretation is used so that the alternatives have exact units. The owner may amend it.

- **`δ_R`:** the smallest true average net profit per executed trade, divided by the trade's initial
  stop risk in currency, that would justify operating the rule.
- **Net:** gross P&L minus all-in entry and exit costs, using the D-06 p95 conservative cost when the
  cost distribution exists.
- **Initial R:** the currency loss that would occur if the initial stop were hit, before costs. Partial
  exits are aggregated into one trade P&L; that P&L is divided by the initial R.
- **Exit and holding policy:** frozen at Gate 2. D-01 does not choose it.
- **Annual contribution target:** net change in research-leg equity over a 12-month evaluation window,
  in USD per year, with fixed-fractional 1% risk, one position, no leverage, spot long-only, net of
  all-in costs, before taxes. It is also reported as a percentage of the `$10,000` starting equity.
  Compounding is part of the measured equity change; the arithmetic approximations below are
  pre-compounding illustrations only.

### 2.3 What remains unresolved

Two independent numeric values:

1. **D-01a — `δ_R`:** the minimum net R per executed trade.
2. **D-01b — annual contribution target:** the minimum net annual contribution to the research leg.

They are separate owner decisions. A per-trade MME does not imply an annual target, and an annual
target does not imply a per-trade MME.

### 2.4 Role and interactions

- **D-08** supplies `α = 5%` two-sided and 80% power.
- **D-09** supplies the dependence treatment; its parameters are still open.
- **D-10** turns `δ_R`, `σ`, `DE`, and `p_exec` into a required sample.
- **D-07** makes the annual contribution co-primary; the target is the missing half of D-07.
- **Gate 3** compares the cost-feasible, dependence-adjusted opportunity count with the derived
  requirement. A larger `δ_R` or a larger annual target raises the requirement and can make a
  hypothesis untestable on the available calendar.
- **D-14** governs whether the evidence can be extrapolated after the test.

The Stage 2M decision rule compares the **lower bound** of a dependence-adjusted interval with the MME.
An interval that contains the MME or zero is **inconclusive**, not a pass.

### 2.5 Preference versus evidence

- **Owner preference:** the values of `δ_R` and the annual target. They state what the owner considers
  worth doing. They can be declared before data.
- **Evidence-dependent parameters:** `σ` (outcome variance), `DE` (design effect), `p_exec`
  (execution/fill rate), and the realized opportunity frequency. These cannot be responsibly fixed
  without data or a pre-specified assumption set. They are not part of D-01a or D-01b.
- **Evidence-dependent compatibility:** whether a chosen annual target is reachable at a chosen `δ_R`
  depends on frequency and execution. The owner can set a target now, but Gate 3 may later show it is
  not testable. That is a finding, not a reason to change the target after seeing outcomes.

### 2.6 Documented recommendation

Stage 2M recommends stating **both** a per-trade MME and an annual target before outcomes. It does
**not** recommend a specific number. The register's framing is per-trade primary plus annual
co-primary, which Stage 2N already selects.

**No numeric MME and no numeric annual target are recommended by the framework.** The historical
`0.15R` is a design assumption, not an approved threshold
(`stage2k/FAILURE_MODE_ANALYSIS.md` §7.3; `STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §2.3).

---

## 3. D-01a — Numeric `δ_R` alternatives

### 3.1 Exact alternatives

All values are **net R per executed trade**. At the `$10,000` research leg and 1% risk, 1R = `$100`,
so the dollar equivalent per trade is shown for scale only.

| option | value | dollars per trade at 1R = `$100` | plain meaning |
|---|---:|---:|---|
| **M-10** | **0.10R** | `$10` | a thin edge; a small fraction of the risk unit |
| **M-15** | **0.15R** | `$15` | the historical design assumption; not approved |
| **M-20** | **0.20R** | `$20` | a middle economic threshold |
| **M-25** | **0.25R** | `$25` | a stricter economic threshold |
| **M-30** | **0.30R** | `$30` | the Stage 2M arithmetic illustration of a larger MME |
| **custom** | owner value | — | must be stated in R per executed trade |
| **open** | not set | — | D-01 remains open |

### 3.2 Illustrative sample implications

The following uses only the Stage 2M formula with `σ = 1R`, `α = 5%` two-sided, and 80% power under
independence:

```
N_ind ≈ (1.959964 + 0.841621)² × σ² / δ_R²
```

| `δ_R` | `N_ind` (DE = 1) | `N_obs` (DE = 2.0) | `N_obs` (DE = 3.93) |
|---:|---:|---:|---:|
| 0.10R | ≈ 785 | ≈ 1,570 | ≈ 3,085 |
| 0.15R | ≈ 349 | ≈ 698 | ≈ 1,371 |
| 0.20R | ≈ 196 | ≈ 392 | ≈ 771 |
| 0.25R | ≈ 126 | ≈ 251 | ≈ 494 |
| 0.30R | ≈ 87 | ≈ 174 | ≈ 343 |

**Labels:** this is arithmetic, not a market result. `DE = 3.93` is Candidate D's descriptive design
effect (`STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3.1); it is not a universal value. The actual `DE`
and `p_exec` are still open under D-09 and D-10. Required opportunities are `N_obs / p_exec`, so the
opportunity requirement is higher than `N_obs` whenever execution is imperfect.

### 3.3 Consequences of each choice

- **0.10R:** the smallest sample burden is actually the largest, because a small effect needs more
  evidence. It risks authorizing a rule whose annual contribution is negligible at 1% risk. It may be
  statistically detectable but economically thin.
- **0.15R:** the historical design assumption. It is not owner-approved and it is not a default. Under
  the historical 150 floor it was not even statistically supported; 150 is sufficient only for about
  `0.23R` under independence (`FAILURE_MODE_ANALYSIS.md` §7.3).
- **0.20R:** a moderate threshold; roughly half the independent sample of 0.15R, but still demanding
  after dependence and execution inflation.
- **0.25R:** a stricter economic threshold; lower sample requirement, but a plausible rule may fail on
  edge rather than on frequency.
- **0.30R:** the strongest economic relevance among the listed values; the smallest sample; the highest
  risk that no plausible rule in the intended family clears it. Stage 2M used 0.30R only as an
  arithmetic illustration, not as a recommendation.

**Trade-off:** a larger `δ_R` makes the economic bar higher and the sample requirement lower. A
smaller `δ_R` does the reverse. The owner is choosing which error is more acceptable: rejecting a
modestly profitable rule, or accepting a rule that is statistically detectable but economically thin.

### 3.4 What cannot be decided here

- `σ` and `DE` cannot be set from this packet; they require data or pre-specified assumptions.
- `p_exec` cannot be set without execution evidence.
- The realized opportunity frequency cannot be set without a census, which Stage 2O does not run.

---

## 4. D-01b — Numeric annual contribution target alternatives

### 4.1 Exact alternatives

All values are **net annual contribution to the `$10,000` research leg, in USD per year**, measured
over a 12-month evaluation window under the D-04 research convention. The percentage is of the
`$10,000` starting equity.

| option | value | % of `$10,000` per year | plain meaning |
|---|---:|---:|---|
| **A-250** | **`$250`/year** | 2.5% | a modest annual contribution |
| **A-500** | **`$500`/year** | 5% | a low but non-trivial annual target |
| **A-750** | **`$750`/year** | 7.5% | a middle annual target |
| **A-1000** | **`$1,000`/year** | 10% | a demanding annual target at this capital |
| **A-1500** | **`$1,500`/year** | 15% | a high annual target |
| **A-2000** | **`$2,000`/year** | 20% | a very high annual target |
| **custom** | owner value | — | must be stated in USD per year |
| **open** | not set | — | D-01 remains open |

**No monthly return assumption is used in this packet.** The values are annual. A `$1,000` annual
target is **10% per year**, not 10% per month.

### 4.2 Frequency implication

Under fixed-fractional 1% risk and the pre-compounding approximation:

```
annual net contribution ≈ δ_R × $100 × executed_trades_per_year
```

so the required executed trades per year is:

```
required_trades_per_year ≈ annual_target / (δ_R × $100)
```

| annual target | `δ_R = 0.10R` | `δ_R = 0.15R` | `δ_R = 0.20R` | `δ_R = 0.25R` | `δ_R = 0.30R` |
|---|---:|---:|---:|---:|---:|
| `$250` | 25 | ≈ 17 | ≈ 13 | 10 | ≈ 9 |
| `$500` | 50 | ≈ 34 | 25 | 20 | ≈ 17 |
| `$750` | 75 | 50 | ≈ 38 | 30 | 25 |
| `$1,000` | 100 | ≈ 67 | 50 | 40 | ≈ 34 |
| `$1,500` | 150 | 100 | 75 | 60 | 50 |
| `$2,000` | 200 | ≈ 134 | 100 | 80 | ≈ 67 |

**Labels:** arithmetic illustration, not a forecast. It assumes every trade earns exactly the MME and
ignores compounding, idle capital, and the difference between opportunities and executed trades. Real
requirements are higher because `p_exec < 1` and because the interval lower bound must clear the MME.

### 4.3 Consequences of each choice

- **`$250`–`$500`/year:** reachable at lower frequency; a sparse rule has a chance. The economic
  objective is modest relative to the risk and effort.
- **`$750`/year:** a middle target; at 0.20R it requires about 38 executed trades per year.
- **`$1,000`/year:** at 0.20R it requires about 50 executed trades per year; at 0.15R about 67. This
  is demanding at the historical opportunity frequencies (see §5).
- **`$1,500`–`$2,000`/year:** requires either a high per-trade edge, high frequency, or both. At the
  historical frequencies, these targets are likely to fail Gate 3 on frequency before any outcome is
  observed.

### 4.4 Interaction with D-07 and D-08

D-07 makes the annual contribution **co-primary**. D-08 makes the allocation **hierarchical**: the
per-trade primary is tested first; the annual co-primary is tested only if the primary passes. The
annual target therefore cannot rescue a failed per-trade result, but a failed annual target can block
promotion after a per-trade pass.

---

## 5. Cross-consistency of D-01a and D-01b

### 5.1 Annual target versus MME

The two values are linked by frequency. A per-trade MME and an annual target are compatible only if the
required frequency is plausible for the intended hypothesis. The table in §4.2 gives the arithmetic.

### 5.2 Historical frequency context

**Verified counts** from the historical censuses, over the `1,277`-day interval:

| candidate | non-overlapping opportunities | approximate per year |
|---|---:|---:|
| A | 71 | ≈ 20 |
| B | 24 | ≈ 7 |
| C | 12 | ≈ 3 |
| D | 34 | ≈ 10 |

These are **opportunities**, not executed trades, and the historical counts are not outcome evidence.
They are still a useful reality check on the annual target.

### 5.3 Flagged tension

At `δ_R = 0.20R` and a `$1,000` annual target, about **50 executed trades per year** are required.
That is roughly 2.5 times Candidate A's historical opportunity frequency and five times Candidate D's,
before applying `p_exec < 1`. At `δ_R = 0.15R`, the requirement is about 67 per year.

**Interpretation:** some combinations of `δ_R` and annual target are internally inconsistent with the
historical frequency record. The owner may still choose them, but the likely Gate 3 outcome is a
frequency failure, not an edge failure. This packet flags the tension; it does not resolve it and does
not lower the target to fit the history.

### 5.4 Sample requirement

`δ_R` drives `N_ind`; the annual target does not enter the sample-size formula directly. The annual
target enters through the co-primary decision and through Gate 3's frequency check. A high annual
target can therefore fail even when the per-trade sample is sufficient.

### 5.5 What remains evidence-dependent

`σ`, `DE`, `p_exec`, and realized frequency. The owner's `δ_R` and annual target are preferences; their
feasibility is evidence-dependent. No evidence was generated in Stage 2O.

---

## 6. D-02 — Risk constraints

### 6.1 What is already decided

**Option C:** the risk policy includes a **maximum drawdown**, a **per-trade loss limit**, a **tail
measure**, and a **liquidity/position-size constraint**. Time under water, ruin probability,
concentration, and operational risk (option D) were **not** adopted as required limits.

### 6.2 Proposed measurement interpretation (not an owner decision)

- **Maximum drawdown:** largest peak-to-trough decline in **net-of-cost equity**, measured on the
  research leg, using mark-to-market equity, expressed as a percentage of the prior equity peak.
- **Per-trade loss:** realized net loss on a single executed trade, expressed in R and as a percentage
  of equity at entry. It includes adverse gap and slippage, not only the planned stop distance.
- **Tail risk:** **CVaR at 95%** (average loss in the worst 5% of executed trades), expressed in R.
  The worst observed trade is reported alongside it.
- **Liquidity:** order notional as a percentage of **visible top-of-book depth** at the decision and
  exit times, with the venue's minimum notional and lot step checked arithmetically.
- **Sample period:** frozen at Gate 2; the limits are not re-chosen after outcomes.
- **Scope:** research leg, real capital, or both — **unresolved** and asked separately as D-02e.

### 6.3 What remains unresolved

Five independent items:

1. **D-02a** — maximum drawdown (% of equity).
2. **D-02b** — per-trade loss limit (R and % of equity).
3. **D-02c** — tail-risk limit (CVaR95, in R).
4. **D-02d** — liquidity/position-size limit (% of visible depth).
5. **D-02e** — scope of application (research leg, real capital, or both).

They are separate decisions. A drawdown limit does not imply a tail limit, and a tail limit does not
imply a liquidity limit.

### 6.4 Interaction with the `$10,000` / 1% convention

At `$10,000` equity and 1% risk:

- 1R = `$100` = 1% of equity.
- A 10% drawdown is `$1,000`, or about 10 full 1R losses before compounding and before gaps.
- A 20% drawdown is `$2,000`, or about 20 full 1R losses.
- A CVaR95 of 2R is an average `$200` loss in the worst 5% of trades.
- The historical capital geometry allowed notional up to about 0.769 of equity for cost-feasible
  signals at 26 bp (`stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6); a `$10,000` position can therefore
  be a large fraction of equity even at 1% risk.

These are translations, not approved limits.

### 6.5 Preference versus evidence

- **Owner preference:** the drawdown, per-trade, and tail limits, and the scope. They state what the
  owner will tolerate.
- **Evidence-dependent:** whether a rule actually stays within the limits; the tail estimate; the
  liquidity check; the real-capital translation. These require Gate 5 outcomes, Nobitex depth/fill
  evidence (D-05), and the real-capital disclosure (D-04).
- **Not evidence:** any Monte Carlo drawdown or ruin value. Stage 2O runs no simulation and treats no
  simulated outcome as empirical proof.

---

## 7. D-02 numeric alternatives

### 7.1 D-02a — Maximum drawdown

| option | value | dollars at `$10,000` | simple interpretation |
|---|---:|---:|---|
| **DD-10** | **10%** | `$1,000` | about 10 full 1R losses |
| **DD-15** | **15%** | `$1,500` | about 15 full 1R losses |
| **DD-20** | **20%** | `$2,000` | about 20 full 1R losses |
| **DD-25** | **25%** | `$2,500` | about 25 full 1R losses |
| **custom** | owner value | — | stated as % of equity peak |
| **open** | not set | — | D-02 remains open |

**Consequences:** a strict drawdown limit protects survivability but can reject a positive-expectancy
rule whose path is merely uncomfortable. A loose limit may permit a rule the owner cannot actually
hold through. The simple "N full losses" reading ignores compounding, partial losses, gaps, and the
fact that a tail event can consume several R at once.

**Prohibited assumption:** no 30% drawdown and no Monte Carlo drawdown value is treated as approved.

### 7.2 D-02b — Per-trade loss limit

| option | value | dollars at 1R = `$100` | plain meaning |
|---|---:|---:|---|
| **PT-075** | **0.75R** | `$75` | a tight single-trade cap |
| **PT-100** | **1.00R** | `$100` | the planned 1% risk, with no overshoot allowance |
| **PT-125** | **1.25R** | `$125` | allows limited gap/slippage overshoot |
| **PT-150** | **1.50R** | `$150` | allows more slippage or gap risk |
| **PT-200** | **2.00R** | `$200` | a loose cap; double the planned risk |
| **custom** | owner value | — | stated in R and % of equity |
| **open** | not set | — | D-02 remains open |

**Consequences:** the 1% risk convention sizes positions from the stop distance. A realized loss can
exceed 1R if the market gaps through the stop or slippage is material. A limit at 1R requires the
position size to include expected slippage, or requires accepting that a gap is a policy breach. A
limit above 1R tolerates overshoot but weakens the meaning of the 1% convention. A limit below 1R
forces smaller positions and lowers the annual contribution at a given `δ_R`.

### 7.3 D-02c — Tail-risk limit

| option | value | dollars at 1R = `$100` | plain meaning |
|---|---:|---:|---|
| **CV-15** | **CVaR95 ≤ 1.5R** | `$150` | tight tail; worst 5% average loss is 1.5R |
| **CV-20** | **CVaR95 ≤ 2.0R** | `$200` | moderate tail |
| **CV-25** | **CVaR95 ≤ 2.5R** | `$250` | looser tail |
| **CV-30** | **CVaR95 ≤ 3.0R** | `$300` | loose tail |
| **custom** | owner value | — | stated in R |
| **open** | not set | — | D-02 remains open |

CVaR95 is the average loss in the worst 5% of executed trades. It is not the worst trade and not a
drawdown. A small sample makes the 5% tail unreliable; the estimate must be reported with a
dependence-adjusted interval, and an interval that cannot establish the limit is **inconclusive**.

**Consequences:** a tight CVaR limit forces small positions or narrow stops and may reject a rule with
a positive average. A loose limit permits a tail that could breach the drawdown limit in a few trades.

### 7.4 D-02d — Liquidity / position-size limit

| option | value | plain meaning |
|---|---|---|
| **LQ-01** | **≤ 1% of visible top-of-book depth** | strict; preserves exit capacity |
| **LQ-05** | **≤ 5% of visible top-of-book depth** | moderate |
| **LQ-10** | **≤ 10% of visible top-of-book depth** | loose |
| **LQ-V01** | **≤ 1% of average 1-minute traded volume** | volume-based alternative |
| **custom** | owner value | must state the metric and threshold |
| **open** | not set | D-02 remains open |

The order notional is checked at both entry and exit. The venue's minimum notional (`$5` in the
historical arithmetic) and lot step (`1e-5 BTC`) must also pass. Visible depth on Nobitex is **not
measured**; the historical record contains no Nobitex depth evidence. Therefore the liquidity limit can
be **chosen** now but cannot be **verified** until D-05 evidence exists.

**Consequences:** a strict limit caps position size and can make `$10,000` infeasible for wide-stop
signals. A loose limit can produce a statistically valid but unexecutable rule. A volume-based metric
is less sensitive to momentary book thinning but ignores the actual price impact at the intended size.

### 7.5 Dependencies between the limits

- **Per-trade and tail:** a per-trade cap at 1R makes a CVaR95 above 2R unusual but not impossible; a
  loose per-trade cap makes the tail limit the binding constraint.
- **Tail and drawdown:** several tail events can consume the drawdown budget. With a 10% drawdown and a
  2R CVaR95, about five tail-average events reach the limit before other losses.
- **Drawdown and frequency:** a higher-frequency rule has more chances to hit the drawdown limit, even
  with the same per-trade edge.
- **Liquidity and capital:** a strict depth limit reduces the feasible notional, which reduces the
  annual contribution at a given `δ_R` and can make the annual target unreachable.
- **Scope:** if the limits apply to a real capital base smaller than `$10,000`, the position sizes and
  the liquidity check change; if they apply only to the research leg, a separate real-capital
  translation is still required.

---

## 8. Cross-consistency of D-02 and D-01

### 8.1 Risk limits versus the economic objective

A strict risk policy can reject a rule that meets the MME. A loose policy can authorize a rule that
meets the MME but cannot be held. The owner is choosing the acceptable trade-off between opportunity
and survivability.

### 8.2 Research leg versus real capital

D-04 chose the research leg for comparability and left the real-capital check open. If D-02 limits are
set on the `$10,000` research leg only, they are **not automatically the owner's live limits**. If they
are set on real capital, the research-leg translation must be stated and the `$10,000` comparability
may change. The scope question (D-02e) is therefore part of the decision, not a technical detail.

### 8.3 Arithmetic tensions to flag

1. **10% drawdown + 2R CVaR95:** about five tail-average events reach the drawdown budget. This is
   tight, not impossible; it may reject rules with fat tails.
2. **10% drawdown + 1R per-trade cap:** about ten consecutive full losses reach the limit. A single
   gap can shorten that count. The limit is meaningful only if gaps are bounded or disclosed.
3. **Strict liquidity + `$10,000`:** if the order notional is limited to 1% of visible depth, the
   required depth is 100 times the order size. At a `$7,690` notional (the historical geometry upper
   range), that requires `$769,000` of visible depth at the touch. Nobitex depth is unmeasured; the
   feasibility of this combination is unknown.
4. **High annual target + strict risk limits:** the target may require more trades, while the drawdown
   limit penalizes frequency. The two can be jointly infeasible even if each is acceptable alone.

These are flags, not resolutions. None of them changes a historical verdict or a Stage 2N answer.

### 8.4 Owner preference versus evidence-dependent parameter

| item | classification | why |
|---|---|---|
| `δ_R` | **owner preference** | states what is worth doing |
| annual contribution target | **owner preference** | states the capital objective |
| maximum drawdown | **owner preference** | states survivability tolerance |
| per-trade loss limit | **owner preference** | states single-trade tolerance |
| tail limit | **owner preference** | states acceptable tail |
| liquidity limit | **owner preference** | states execution tolerance |
| `σ` | **evidence-dependent** | outcome variance |
| `DE` | **evidence-dependent** | dependence structure |
| `p_exec` | **evidence-dependent** | fill/execution rate |
| realized drawdown, CVaR, depth | **evidence-dependent** | requires Gate 5 and D-05 evidence |
| real-capital translation | **evidence-dependent** | requires the D-04 real-capital disclosure |

---

## 9. Decision sequence presented to the owner

Each item is asked separately. A combined "approve all" answer is not accepted as approval of
independent numeric decisions.

1. **D-01a** — numeric `δ_R`.
2. **D-01b** — numeric annual contribution target.
3. **D-02e** — scope of the D-02 limits.
4. **D-02a** — numeric maximum drawdown.
5. **D-02b** — numeric per-trade loss limit.
6. **D-02c** — numeric tail-risk limit.
7. **D-02d** — numeric liquidity limit.

For each item the owner may:

- select a listed value;
- enter a custom value with units;
- leave the item open.

An item left open remains open. It is not defaulted, and it continues to block its dependent gate.

---

## 10. Scope restrictions and stop condition

**This stage does not and must not:**

- process historical market data;
- run a feasibility census, backtest, bootstrap, Monte Carlo, or optimization;
- calculate or report new performance metrics;
- access validation or OOS data;
- develop or evaluate a trading strategy;
- implement code or modify the research framework;
- perform the Nobitex cost study;
- perform the D-13 independent audit;
- revisit D-15;
- authorize Gate 0–5 progression;
- start Stage 2P.

**Stop condition:** stop immediately after this packet and the explicitly supplied owner responses are
recorded. No subsequent stage is authorized.

---

## 11. Source references

- `docs/research/stage2m/OWNER_DECISION_REGISTER.md` §2 D-01, D-02; §3 dependencies.
- `docs/research/stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §3, §4, §5, §6.
- `docs/research/stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §2, §3, §4, §5.
- `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3, §6, §8.
- `docs/research/stage2m/STAGE2M_FINAL_PROPOSAL.md` §2, §3.
- `docs/research/stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §4, §5, §6, §9–§17.
- `docs/research/stage2k/FAILURE_MODE_ANALYSIS.md` §7.3, §8.3.
- `docs/research/stage2k/HISTORICAL_RESEARCH_SYNTHESIS.md` §4.3, §6.3, §7.3, §9.5.
- `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §6.6, §6.7.
