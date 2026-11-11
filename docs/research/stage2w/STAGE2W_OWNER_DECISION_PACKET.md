# Stage 2W — T-4 Owner Decision Packet

**Decision requested:** the real-capital per-trade risk-sizing convention (T-4)
**Current status:** **T-4 deferred** since 2026-11-11; `R-08` **P**; `R-15` **B**; Gate 0 **not
passed**
**Prepared:** 2026-11-11 (UTC) · analysis: `STAGE2W_T4_SIZING_ANALYSIS.md` (same directory)
**Nature:** options and a recommendation. It creates no decision, no risk amount, and no
authorization. Only the owner can decide T-4.

---

## 1. What is being decided

Whether to state a real-capital per-trade risk convention, and if so which one, on these recorded
constraints: `$100` available capital, `$30` personal cumulative loss tolerance, `$1`–`$3` practical
order notional, `$250` annual objective, Nobitex as intended venue with **all venue constraints
UNKNOWN**.

What is **not** being decided here: the strategy, its stop distance, its trade frequency, its
expectancy, the venue's rules, the annual objective, or any gate.

---

## 2. The arithmetic that constrains every option

From the analysis (`D = N × s`), with `$1`–`$3` notional:

- planned risk per trade is bounded at **`$0.005`–`$0.30`**, i.e. `0.005%`–`0.30%` of `$100`;
- a conventional `1%`-of-equity risk (`$1.00`/trade) needs `$50` notional at a `2%` stop — outside the
  practical range and `50×` the smallest order;
- a `2%` stop admits `$0.02`–`$0.06` of planned risk per trade;
- at any of those risk levels, the `$250` objective implies **8,333–500,000 trades per year** at the
  `0.10R` MME; reaching it in `25` trades would need `R = $100` per trade, which breaches the `$30`
  tolerance on the first full loss;
- costs in R are `c/s` for proportional costs and `2F/(N·s)` for fixed fees, so small notional is the
  worst case for fixed fees, and short stops make costs large relative to the `0.10R` MME.

None of this is a forecast; it is arithmetic on the recorded inputs.

---

## 3. Options

Option labels are local to Stage 2W. The mapping to the Stage 2T T-4 menu is given in brackets.

### W-A — Fixed dollar risk per trade [`2T T-4a`]

**Definition:** `D` constant; `notional = D/s`; `quantity = D/(price × s)`.

| | |
|---|---|
| **Advantages** | simplest to reason about; tolerance burn is exactly `30/D` losses; insensitive to equity noise; easy to audit |
| **Disadvantages** | risk fraction rises as equity falls; requires choosing an unjustifiable amount without an edge; notional must move inversely with stop distance, which the `$1`–`$3` range and **UNKNOWN** lot steps may not permit |
| **Risks** | a `D` chosen for the objective rather than for the tolerance; fixed fees can consume most of a small `D`; a stop gap realizes more than `D` |
| **Feasible band** | `D = $0.02`–`$0.06` at `2%` stops; `D > $0.10` needs stops wider than `3.3%` to stay inside `$1`–`$3` |
| **Evaluable now?** | arithmetic yes; amount no |

### W-B — Fixed percentage of current equity [`2T T-4b`]

**Definition:** `D_t = f × E_t`; `notional = f × E_t / s`.

| | |
|---|---|
| **Advantages** | scales with the account; drawdowns reduce risk automatically; standard institutional form |
| **Disadvantages** | at `$100`, conventional `0.5%`–`2%` fractions need `$25`–`$100` notional — incompatible with `$1`–`$3`; only `0.02%`–`0.10%` fits, which is an unusually fine granularity |
| **Risks** | the fraction is not justifiable without an edge; quantization at `$1`–`$3` makes small fractions coarse; risk falls exactly when recovery is needed |
| **Feasible band** | `f ≈ 0.02%`–`0.06%` at `2%` stops; `0.10%` needs stops of `3.3%` or wider |
| **Evaluable now?** | arithmetic yes; fraction no |

### W-C — Fixed percentage of the `$30` personal budget [`new; no 2T equivalent`]

**Definition:** `D = g × 30`; `notional = g × 30 / s`.

| | |
|---|---|
| **Advantages** | transparent tie to the stated tolerance; exactly `1/g` losses to consume the budget |
| **Disadvantages** | does not adapt to equity at all; to fit `$1`–`$3` it requires stops of `5%`–`30%`, i.e. very wide; treats a personal cumulative tolerance as a strategy parameter |
| **Risks** | risk fraction rises after losses; a wide stop makes `1R` losses rare and the `0.10R` MME hard to distinguish; conceptually conflates the owner's tolerance with risk policy |
| **Feasible band** | `g = 0.5%` (`$0.15`/trade) needs a `5%`–`15%` stop; `g = 1%` (`$0.30`) needs `10%`–`30%` |
| **Evaluable now?** | arithmetic yes; amount no |

### W-D — Fractional Kelly (theoretical only) [`no 2T equivalent; requires a validated edge`]

**Definition:** `f* = p − (1−p)/b`; `risk = k × f* × E`.

| | |
|---|---|
| **Advantages** | growth-optimal in theory *if* `p`, `b`, stationarity and independence are known and costs are included |
| **Disadvantages** | every input is unknown; the formula converts an unvalidated guess into a precise-looking number; requires continuous sizing that `$1`–`$3` cannot express |
| **Risks** | severe over-betting if `p` is optimistic; Kelly is far more sensitive to estimation error than fixed sizing; incompatible with the notional band at any plausible `f*` |
| **Feasible band** | none in practice: even quarter-Kelly at `p = 0.55`, `b = 1` needs `$125` notional at a `2%` stop |
| **Evaluable now?** | **no** — should not be used before a validated edge exists |

### W-E — No real risk: research-only [`related to 2T T-4c, but a positive scoping decision`]

**Definition:** `D = 0` for real capital until explicit evidence conditions are met; research leg
continues under frozen D-02 rules.

| | |
|---|---|
| **Advantages** | zero real-capital risk; fully evaluable now; removes an unjustifiable decision from the critical path; no venue constraints needed yet |
| **Disadvantages** | no real-capital learning; the `$250` objective stays untested on the real base; requires a clear statement of what "until" means |
| **Risks** | if treated as permanent, the real-capital objective is silently abandoned — it must be recorded as a scope statement, not a default |
| **Feasible band** | not applicable |
| **Evaluable now?** | yes |

### W-F — Continue deferral (status quo) [`2T T-4c`]

**Definition:** no convention selected; the question remains open and explicitly deferred.

| | |
|---|---|
| **Advantages** | honest given the evidence; preserves optionality; no default is created; `R-08` stays visibly open rather than being resolved by assumption |
| **Disadvantages** | the real-capital objective remains untestable; Gate 0 stays unpassed; repeated deferral risks the decision drifting |
| **Risks** | deferral could be misread as permission to size later without a decision — it is not; it must be re-opened explicitly |
| **Feasible band** | not applicable |
| **Evaluable now?** | yes |

---

## 4. Recommendation (agent; not an owner decision)

**Recommend W-F — continue deferral — and re-open T-4 only when the evidence below exists.** If the
owner wants a positive statement rather than an open item, **W-E** is acceptable and better than any
numeric convention. If the owner insists on a number now, the least-harm choice is **W-A at the
bottom of the feasible band (`$0.02`–`$0.05` per trade)** — but it should be labelled provisional and
not treated as validated.

**Why not approve a numeric amount yet:**

1. **No validated edge exists.** Any `D`, `f`, or `g` chosen now is a guess about an unknown payoff
   distribution. Sizing cannot substitute for an edge.
2. **Execution costs are unmeasured.** With `cost_R = c/s`, an unmeasured `c` can exceed the `0.10R`
   MME at short stops; a sizing decision made before `c` is known can be wrong by multiples.
3. **Venue constraints are UNKNOWN.** Minimum notional, lot step, tick size, fees, and stop support
   can each invalidate a convention that looks fine arithmetically.
4. **Tail and stop behavior are unassessed.** Planned risk is not realized loss; gaps and
   non-filling stop-limits change the loss distribution, and `$30` is a cumulative tolerance, so a
   single gap can absorb a large share of it.
5. **Trade frequency is unknown.** The objective's required frequency (`8,333`–`500,000` trades/year
   at feasible risk) is far above the recorded historical opportunity frequency; the annual
   objective, not the risk per trade, is the item that needs revisiting.
6. **Ordering matters.** Sizing is a downstream parameter: strategy → validated net expectancy →
   measured costs → verified venue constraints → frequency → *then* sizing. Approving sizing first
   inverts the evidence chain.

**Why the `$250` objective cannot justify higher risk:** a return target is not evidence. Raising
per-trade risk raises the probability of consuming the `$30` tolerance and does not raise the
expectancy per trade. With no validated edge, higher risk converts a small expected loss into a
larger one faster. The objective is retained as the owner's stated goal, unvalidated; it is a reason
to reconsider the capital base or the target, not to increase risk.

**Evidence gate before any numeric convention is approved** (each item is currently missing):

- a validated net-of-cost expectancy from an authorized experiment;
- measured fee, spread, and slippage distributions for the intended venue and order sizes;
- verified minimum order/notional, lot step, tick size, and stop-order support;
- an assessed tail-loss and gap/stop-failure distribution;
- the strategy's actual trade frequency;
- a restated annual objective reconciled with the above, or an explicit decision that the objective
  is aspirational and not a sizing input.

---

## 5. Owner decision fields

Record one of the four outcomes below. **The agent will not choose for the owner.**

| field | entry |
|---|---|
| decision | ☐ approve · ☐ reject · ☐ revise · ☐ defer |
| option (if approve/revise) | ☐ W-A · ☐ W-B · ☐ W-C · ☐ W-D · ☐ W-E · ☐ W-F |
| parameter (if approve/revise) | `D = $____` / `f = ____%` / `g = ____%` / other: ____________ |
| conditions | |
| date | |
| verbatim statement | |
| signature | |

**Shortest valid approval statement** (for W-A, as an example — substitute your choice and date):

```
I approve option W-A, D = $0.03 per trade, as the T-4 real-capital sizing convention, dated 2026-11-11.
```

**If you choose W-F or W-E**, a statement such as "I defer T-4" or "I commit no real capital until
the evidence gate is met" is sufficient; the exact wording will be recorded verbatim.

---

## 6. Consequences of each choice (for the record)

| choice | T-4 | R-08 | R-15 | Gate 0 |
|---|---|---|---|---|
| W-A / W-B / W-C | decided | reassessed; would close only if the convention is complete and recorded | still needs a stop distance and frequency before the objective is testable | still not passed; R-05/R-10/R-22 unaffected |
| W-D | decided but unusable without an edge | reassessed | stays blocked | still not passed |
| W-E | decided (scope) | reassessed against its "no real capital committed" branch | research-leg testability unchanged | still not passed |
| W-F | remains deferred | stays **P** | stays **B** | still not passed |

No choice in this packet passes Gate 0, and none authorizes research, venue work, or trading.

---

## 7. Questions the owner may want to answer alongside the decision

1. Is `$250`/year on `$100` intended as a hard objective, or as an aspirational direction that may be
   restated once cost and frequency evidence exists?
2. Is the `$30` tolerance intended to remain a personal, non-transferable limit if the account grows
   beyond `$100`?
3. If a strategy eventually validates an edge, is additional real capital a possibility, or is `$100`
   the permanent ceiling?

These are recorded as open questions, not decisions.
