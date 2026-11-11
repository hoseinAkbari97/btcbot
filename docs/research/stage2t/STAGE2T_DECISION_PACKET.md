# Stage 2T — Owner Decision Packet

**Stage:** 2T (owner ratification and remaining Gate 0 decisions)
**Status:** decision packet presented — **awaiting owner answers** — no choice recorded on the owner's behalf — Gate 0 **not passed**
**Depends on:** the full Stage 2M–2S chain (see the freeze manifest `source_artifacts` for the hashed list)
**Authorizes:** nothing. Stage 2U and all research remain unauthorized.

---

## 0. Purpose and rules

This packet presents six decisions, **T-1 … T-6**, each separately identified. The owner may answer
each independently; **silence, partial approval, or approval of one artifact is not approval of any
other**. Answers are recorded in `STAGE2T_OWNER_RESPONSE_RECORD.md` only when the owner gives them.
No frozen decision is modified here; D-01, D-02, and D-15 change only through separate explicit
authorization.

**Verified repository state:** branch `main`, HEAD `e4b3306`, clean, level with `origin/main`; the
Stage 2S manifest self-hash and all 21 entries re-verified; predecessor manifests (2R, 2Q, 2P)
re-verified; the repository matches the Stage 2S handoff with no discrepancy.

**Classification key:** **F** frozen owner decision · **O** owner-provided input · **C** calculated
value with formula · **E** external evidence (none cited, none collected) · **U** unresolved · **I**
agent interpretation requiring owner ratification.

---

## 1. Artifact numbering reconciliation

**Verified fact** (`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4) — the four Gate 0
artifacts, their required content, and the Stage 2S drafts mapped to them:

| Stage 2P artifact | required content (Stage 2P §4) | Stage 2S instruction label | Stage 2S file | status |
|---|---|---|---|---|
| `A-1` Gate 0 owner decision record | D-01, D-02, D-03, D-07, D-08, D-09, D-12 as resolved, each with its date and verbatim value | *(absent — the instruction's list omitted it)* | none | **not drafted** |
| `A-2` economic objective memo | MME definition, `0.10R` value, `$250` annual target, `$10,000` research equity, the two estimands, owner-selected vs verified distinction | `A-1` | `stage2s/STAGE2S_A1_OBJECTIVE_MEMO_DRAFT.md` | draft, unratified |
| `A-3` risk policy statement | `15%` drawdown of prior peak, `1.00R` per-trade cap, `0.50R` `CVaR95`, `$2,500` notional cap, scope, measurement rules, explicit operational-risk exclusion (`B-12`) | `A-2` | `stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md` | draft, unratified |
| `A-4` capital and execution context statement | research-leg capital, sizing rule, the open real-capital item, the venue decision, the evidence gaps that remain | `A-3`; the instruction's `A-4` meant this artifact's final form | `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` | draft, unratified |

- The **signed decision record is a distinct required artifact (`A-1`)** and does not exist.
- **Effect on R-17–R-20:** none from numbering. `R-17` is **P** because `A-1` is not drafted;
  `R-18`, `R-19`, `R-20` are **P** because the corresponding drafts (`A-2`, `A-3`, `A-4`) are
  unratified. No checklist status was changed to make the numbering consistent, and no Stage 2S
  file was renamed or rewritten. **The Stage 2P definitions take precedence.**

---

## 2. Decisions T-1 … T-3 — ratification of the three drafts

Each decision is independent: **ratify / reject / request revisions** (specify the revisions).

### T-1 — Economic objective memo (authoritative artifact `A-2`)

1. **Identifier:** Stage 2P `A-2`; file `stage2s/STAGE2S_A1_OBJECTIVE_MEMO_DRAFT.md`.
2. **Purpose:** consolidate the frozen economic objective so a future experiment knows what it must detect.
3. **Key statements (all F, restated):** primary estimand net R per executed trade; co-primary net
   annual contribution; MME `0.10R` net per executed trade; target `$250`/year on the `$10,000`
   research equity; `α = 5%` two-sided, power `80%`, hierarchical allocation (D-08); cluster-robust
   plus block bootstrap, disagreement ⇒ inconclusive (D-09); disclosed arithmetic `$250 / ($10 per
   trade) = 25` executed trades/year under full `1R` risk; the historical opportunity-frequency
   concern (~20/10/7/3 opportunities per year) acknowledged and unresolved; no achievability claim.
4. **Unresolved qualifications:** owner-selected values, none verified; the real-base expression of
   the `$250` target is flagged **I** (decision T-5); the frequency concern is **U**.
5. **Inconsistencies with frozen decisions:** none found — it restates D-01, D-03, D-07, D-08, D-09
   as recorded in `stage2n`/`stage2o`.
6. **Consequences of ratification:** `A-2` exists as a ratified Gate 0 artifact; `R-18` can move to
   **S** when the ratification is recorded. Gate 0 does not pass by itself.
7. **Consequences of rejection/revision:** `R-18` stays **P**; the memo returns to revision; Gate 0
   remains blocked on the artifact.

### T-2 — Risk policy statement (authoritative artifact `A-3`)

1. **Identifier:** Stage 2P `A-3`; file `stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md`.
2. **Purpose:** consolidate the frozen research-leg risk limits, scope, and measurement rules.
3. **Key statements (all F):** `15%` drawdown of prior peak, net-of-cost mark-to-market; `1.00R`
   maximum realized net loss per trade; `0.50R` `CVaR95`; `$2,500` maximum entry notional on the
   `$10,000` research reference; scope **research leg only**; operational risk explicitly excluded
   (`B-12`, recorded exposure); the three-layer separation — research-leg limits, the owner's `$30`
   **personal cumulative** loss tolerance (not a strategy drawdown authorization), and any future
   real-capital policy (does not exist).
4. **Unresolved qualifications:** the `CVaR95` tail-sample measurement definition is to be fixed at
   pre-registration; no real-capital risk policy exists.
5. **Inconsistencies with frozen decisions:** none found — D-02 is unchanged and unscaled.
6. **Consequences of ratification:** `A-3` exists as a ratified Gate 0 artifact; `R-19` can move to
   **S** when recorded. Gate 0 does not pass by itself.
7. **Consequences of rejection/revision:** `R-19` stays **P**; Gate 0 remains blocked on the artifact.

### T-3 — Capital and execution context statement (authoritative artifact `A-4`)

1. **Identifier:** Stage 2P `A-4`; file `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md`.
2. **Purpose:** record the research leg, the owner's stated real capital and restrictions, the venue
   decision, and the evidence gaps.
3. **Key statements:** research leg **F** (`$10,000`, `1%` fixed-fractional, one position, no
   leverage); real capital **O** (`$100`, all available capital, `$30` personal cumulative
   tolerance, `$1`–`$3` confirmed order notional, capital remains available); restrictions **O**
   (owner statements of "no known restrictions" — not venue evidence); venue **F** (Binance
   research / Nobitex execution, D-05; p95 conservative cost rule, D-06); **Binance historical data
   does not establish Nobitex execution feasibility**; all venue capability/cost/liquidity items
   unverified (**U**).
4. **Unresolved qualifications:** the real-base sizing convention (decision T-4); the real-base
   expression of the annual target (decision T-5); `B-02`, `B-03`, `B-04` (Gate 1).
5. **Inconsistencies with frozen decisions:** none found — D-04, D-05, D-06 unchanged.
6. **Consequences of ratification:** `A-4` exists as a ratified Gate 0 artifact with the open
   real-capital item *recorded as open* (Stage 2P §4 requires the artifact to state the open item,
   not to close it); `R-20` can move to **S** when recorded; `R-08` stays **P** until T-4 is decided.
   The owner may alternatively prefer to decide T-4 first and ratify a revised statement.
7. **Consequences of rejection/revision:** `R-20` stays **P**; Gate 0 remains blocked on the artifact.

---

## 3. Decision T-4 — real-capital per-trade sizing convention

**Background (all O, recorded 2026-11-11):** capital `$100` (total available); personal cumulative
loss tolerance `$30`; order notional `$1`–`$3`. **The `$30` is not an authorized strategy drawdown
limit and not a per-trade risk.** D-02's frozen research-leg limits (1% of `$10,000`, etc.) are not
modified by this decision.

**The six quantities, distinguished:**

| quantity | meaning |
|---|---|
| order notional | USD size of the order placed (owner-confirmed `$1`–`$3`) |
| position notional | total USD market value of the open position (equals order notional for a single entry without adds) |
| stop distance | fractional price decline from entry to the stop (a hypothetical `2%` stop = `0.02`) |
| dollar loss at the stop | `position notional × stop-distance fraction` |
| risk per trade as % of equity | `dollar risk ÷ current equity × 100` |
| cumulative strategy drawdown | peak-to-trough decline of the strategy equity curve over many trades, net of cost |

**Identity:** `dollar risk = position notional × stop-distance fraction`.

**Illustrative arithmetic only (**C**), hypothetical stops, not recommendations:**

| position notional | hypothetical stop | dollar risk at stop | % of `$100` equity |
|---|---|---|---|
| `$1` | 1% | `$0.01` | 0.01% |
| `$1` | 2% | `$0.02` | 0.02% |
| `$1` | 5% | `$0.05` | 0.05% |
| `$1` | 10% | `$0.10` | 0.10% |
| `$3` | 1% | `$0.03` | 0.03% |
| `$3` | 2% | `$0.06` | 0.06% |
| `$3` | 5% | `$0.15` | 0.15% |
| `$3` | 10% | `$0.30` | 0.30% |

Notes: the maximum possible loss on a spot long is the notional itself (`$1`–`$3` = 1%–3% of
equity); realized losses can exceed the stop arithmetic through gaps, fees, and slippage; reaching
the `$30` cumulative tolerance would take, for example, one hundred maximum `$0.30` stop losses —
arithmetic, not a plan.

**Alternatives presented, not chosen (I — the owner selects or defines another):**

- **T-4a — fixed maximum dollar risk per trade:** the owner states a dollar amount (e.g. `$1`);
  orders are then sized as `risk ÷ stop fraction`, bounded by the `$1`–`$3` order range.
- **T-4b — fixed percentage of current equity per trade:** the owner states a percentage (e.g. 1%);
  dollar risk = equity × percentage, again bounded by the order range.
- **T-4c — defer:** declare that the convention must be determined in a separately authorized
  decision before any strategy is tested on real capital; `R-08` remains **P** until then.
- **T-4d — custom:** the owner defines the convention.

**Consequences:** selecting T-4a/T-4b/T-4d supplies the real-base sizing context that `R-08` waits
on (it can move to **S** when recorded); T-4c keeps `R-08` **P**. None of the options modifies D-02,
and none implies the `$30` may be risked in a single trade or as a drawdown.

---

## 4. Decision T-5 — real-capital expression of the annual objective

**Frozen D-01 (F):** MME `0.10R` net per executed trade; primary metric net R per executed trade;
co-primary net annual contribution in currency; target `$250`/year; research reference `$10,000`.

**The difference, explicitly shown (C):**

- `$250 / $10,000 = 2.5%` — the target as a share of the research reference.
- `$250 / $100 = 250%` — the same target as a share of the stated real capital.

**Alternatives presented, not chosen:**

- **T-5a — preserve the `$250` absolute target.** The target stays `$250`/year although it is 250%
  of real capital. Implication: in R units the requirement remains 25 executed trades/year at the
  MME under full `1R` risk (R arithmetic is capital-invariant), but in dollars this implies a very
  large number of executed trades at any small per-trade expectancy (the count depends on T-4; e.g.
  at `$1` risk per trade, `0.10R = $0.10`, so `$250` implies 2,500 executed trades/year), against a
  recorded historical opportunity frequency of ~20/10/7/3 per year. No feasibility claim is made.
  D-01 unchanged.
- **T-5b — preserve the 2.5% ratio.** The real-capital expression becomes `$2.50`/year on `$100`.
  This is a proposed change to the **real-capital expression only**, not an automatic amendment to
  D-01; it takes effect only by explicit owner authorization. In R units the requirement is the same
  25 trades/year; in dollars it is `2.5%` of capital.
- **T-5c — keep `$250` exclusively as the research-reference objective.** No real-capital annual
  objective exists until a separately authorized decision defines one; `R-15`'s real-capital half
  stays blocked until then.
- **T-5d — custom owner-defined objective.**

D-01 is not changed by any option without separate explicit authorization.

---

## 5. Decision T-6 — signed owner decision record (`A-1`)

**Exact Stage 2P requirement (§4, verified):** `A-1` Gate 0 owner decision record containing
**D-01, D-02, D-03, D-07, D-08, D-09, D-12** as resolved, **each with its date and verbatim
value**, sourced from `stage2n` and `stage2o`; it may restate recorded decisions and may not
introduce new ones; conflicts are escalated, not resolved by the author. *(Minor wording
difference flagged, not reconciled: the R-17 row says "consolidating D-01…D-07" while §4 lists
D-01/D-02/D-03/D-07/D-08/D-09/D-12; §4 governs content.)*

**Proposed record structure (a template, not the artifact):**

| field | content |
|---|---|
| identification | title, version, date, scope: Gate 0 decisions D-01, D-02, D-03, D-07, D-08, D-09, D-12 |
| decision table | per decision: ID, verbatim value, date decided, source record path (`stage2n`/`stage2o`) |
| decision vs recommendation | each row marked **owner decision** or **agent recommendation**; agent text never presented as owner text |
| qualifications & deferrals | recorded qualifications; deferred decisions (e.g. D-15; the T-4/T-5 outcomes) |
| approval mechanism | the owner states per clause: ratify / reject / revise, dated, recorded verbatim; a signature statement slot the owner fills — no signature is fabricated by the agent |

**Authorization status:** Stage 2Q Q4 Option A authorized the agent to draft all four artifacts in
principle; Stage 2S did not draft `A-1` (no slot in its instruction). **T-6 asks the owner:**
authorize drafting the signed decision record now (under the existing or a fresh authorization),
wait until T-1…T-5 are decided, or do not authorize. `R-17` remains **P** until a signed record
exists; a template alone does not satisfy it.

---

## 6. What this packet does not do

No market-data access or processing; no backtests, simulations, or census; no strategy design; no
Nobitex access or venue contact; no cost or liquidity study; no audit; no paper or live trading; no
Gate 0 passage; no Gate 1/2 progression; no changes to D-01, D-02, D-15, or any prior-stage
artifact; no owner choice recorded on the owner's behalf; Stage 2U not started.
