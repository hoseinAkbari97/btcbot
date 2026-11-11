# Stage 2S — Gate 0 Artifact Draft A-2: Risk Policy Statement

**Corresponds to:** Stage 2P artifact `A-3` (risk policy statement),
`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4
**Status:** **DRAFT — NOT RATIFIED.** A proposal under the Stage 2Q Q4 Option A authorization; it
becomes a Gate 0 artifact only if the owner explicitly ratifies it.
**Restates:** frozen decisions only. It introduces no new decision and resolves no conflict.
**Sources:** `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §6, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` §4–§8, `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §4–§5, `stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §3.2 and §4

---

## 0. Purpose and classification key

This statement consolidates the frozen research-leg risk policy so that a future experiment knows
which losses it may not exceed and how each limit is measured. Classification codes: **F** frozen
owner decision · **O** owner-provided factual input · **C** calculated value with formula · **E**
external evidence (none cited; none collected) · **U** unresolved information · **I** agent
interpretation requiring owner ratification.

---

## 1. The frozen research-leg risk limits

**Scope: the `$10,000` research leg only** (`stage2n` §2.2; `stage2o` — D-02 resolved "research leg
only"). All values are **F** unless marked otherwise.

| limit | value | unit | measurement rule |
|---|---|---|---|
| maximum drawdown | **`15%`** of prior equity peak | % of prior peak | net-of-cost, mark-to-market, peak-to-trough |
| maximum realized net loss per trade | **`1.00R`** | R (and `1%` of equity at entry on the research leg) | realized, net of all-in costs, per executed trade |
| tail limit | **`CVaR95 = 0.50R`** | R | conditional value-at-risk at 95%, per executed-trade loss distribution |
| maximum entry notional | **`$2,500`** | USD | per-entry position size, on the `$10,000` research reference |

**Unit compatibility** (R-16, satisfied): the per-trade and tail limits are in R, the primary
metric's unit; the drawdown is in % of prior peak; the notional cap is in USD — each in its natural
unit as recorded (`stage2p` §5).

**Explicit exclusions** (`stage2n` §6.1, option C; blocker `B-12`): time under water, ruin
probability, concentration, and **operational risk were not adopted** as required limits. The
omission of operational risk is a recorded, remaining exposure, not an oversight.

**Unresolved measurement detail (U):** the measurement definition of the `CVaR95` tail sample
(`stage2p` §5, R-04 note) is to be fixed at pre-registration, before any outcome is observed.

---

## 2. The `$2,500` cap and the definition of R (Stage 2Q Q3, embedded)

**F (owner interpretation, 2026-11-10):** `R = executed_notional × stop_fraction`. When the cap binds
(stops below `4%` on the research leg), the trade genuinely carries a smaller `R`; the `1.00R`
per-trade limit and the `0.50R` tail limit retain full force against that smaller `R`; the `1%`
sizing target is a **maximum intent the cap may reduce**, with realized risk below `1%` recorded as
expected behaviour, not a defect. The arithmetic degradation (fewer dollars per `0.10R` below a
`4%` stop) is **recorded, not measured** (`stage2q` §5).

**Frequency risk (Stage 2Q Q2, embedded):** the owner acknowledged that the objective may fail at
Gate 3 on frequency rather than on edge, as a pre-registered, foreseen outcome. A future Gate 3
frequency stop may not be presented as a surprise or used to lower the bar retrospectively
(`stage2q` §4).

---

## 3. Three layers that must not be merged

| layer | content | status |
|---|---|---|
| **1. Frozen research-leg limits** | §1 — `15%` drawdown, `1.00R` per-trade, `0.50R` `CVaR95`, `$2,500` notional, on the `$10,000` research leg | **F**, unchanged by this stage |
| **2. The owner's `$30` personal cumulative loss tolerance** | the owner's stated maximum acceptable **cumulative** loss: `$30`, i.e. `30%` of the stated `$100` strategy capital, recorded 2026-11-11 | **O**, personal to the owner |
| **3. Any future real-capital strategy risk policy** | does not exist | **U**, separately governed |

**Explicitly not done:**

- The research-leg limits in §1 are **not** scaled to `$100`, and this draft implies no real-base
  dollar amounts for them. Re-expressing them on the real base is a separately governed owner
  decision, not performed here.
- The `$30` / `30%` figure is **not** an authorization for a `30%` strategy drawdown. It is the
  owner's personal cumulative loss tolerance. It is **not** a replacement for, or a change to, the
  frozen `15%` drawdown policy, which stands unchanged on the research leg. The two percentages are
  different quantities on different bases (personal cumulative loss versus research-leg
  peak-to-trough drawdown); no conflict between them is created or resolved here.
- No per-trade risk limit on the real base is stated, implied, or invented. Order notional is not
  risk capital: risk per order equals `notional × stop_fraction` (**C**), and no stop fraction is
  selected in this draft.

---

## 4. What this statement does not do

- It does not change D-02 or any frozen limit, and does not adopt operational-risk limits.
- It does not claim any limit is attainable, coherent with the objective, or executable on any
  venue; `$2,500` remains a notional ceiling, not evidence of liquidity feasibility (`R-05`, `B-04`).
- It does not process data, run any computation, pass Gate 0, or authorize any gate or trading.

---

## 5. Ratification

This draft requires explicit owner ratification to become Gate 0 artifact `A-3`. Items the owner may
wish to decide while ratifying: whether the `CVaR95` tail-sample definition should be fixed now or
at pre-registration, and whether to begin the separately governed real-base risk policy. Ratifying
this statement is separate from ratifying the objective memo and the capital/execution context
draft.
