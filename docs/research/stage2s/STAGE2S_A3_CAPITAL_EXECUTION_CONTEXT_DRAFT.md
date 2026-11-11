# Stage 2S — Gate 0 Artifact Draft A-3: Capital and Execution Context Statement

**Corresponds to:** Stage 2P artifact `A-4` (capital and execution context statement),
`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4
**Status:** **DRAFT — NOT RATIFIED.** A proposal under the Stage 2Q Q4 Option A authorization. All
D-04 inputs are now supplied (Stage 2S clarifications, 2026-11-11); the final form additionally
requires owner ratification and the real-base sizing-convention decision (§3.6).
**Restates:** frozen decisions and recorded owner inputs only. It introduces no new decision and
resolves no conflict.
**Sources:** `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §2 and §7, `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3, `stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §3, `stage2s/STAGE2S_OWNER_CLARIFICATION_REQUEST_AND_RESPONSES.md` §3

---

## 0. Purpose and classification key

This statement records the capital and execution context for the research programme: the research
leg, the owner's stated real capital, the venue decision, and the evidence gaps. Classification
codes: **F** frozen owner decision · **O** owner-provided factual input · **C** calculated value with
formula · **E** external evidence (none cited; none collected) · **U** unresolved information ·
**I** agent interpretation requiring owner ratification.

---

## 1. The research leg (frozen, labelled comparison basis)

**F** (`stage2n` §2.2, D-04 option C of Stage 2N): equity `$10,000` research convention; risk per
trade `1%` of equity (`$100` at inception); position sizing fixed-fractional; one concurrent
position; no leverage; spot long-only; next-bar-open market entry. This is a **research construct and
a labelled comparison basis, not the owner's account**.

---

## 2. The owner's stated real capital

| element | value | class | recorded |
|---|---|---|---|
| strategy capital | **`$100` USD** | **O** | as of 2026-11-11 (`stage2r` §3.1) |
| allocation status | **all capital currently available for this strategy** — not a portion of a larger amount | **O** | Stage 2S clarification A, 2026-11-11 |
| personal cumulative loss tolerance | **`$30`** (30% of the stated `$100`), cumulative boundary, personal to the owner | **O** | `stage2r` §3.2 |
| practical order range | **`$1`–`$3`, confirmed as order notional in USD** | **O** | `stage2r` §3.3; Stage 2S clarification B |
| capital availability | the `$100` **remains available throughout the intended research period** | **O** | Stage 2S clarification E |

**C, restated from Stage 2R §4:** `$30 / $100 = 30%`; `$1 / $100 = 1%` and `$3 / $100 = 3%`, so the
order range is `1%`–`3%` of the stated capital as **notional, not risk**. Risk per order equals
`notional × stop_fraction`; no stop fraction is selected here and no per-trade risk limit exists on
the real base.

---

## 3. Capital restrictions

| category | recorded | class |
|---|---|---|
| deposits | **none known** | **O** (owner statement, 2026-11-11) |
| withdrawals | **none known** | **O** (owner statement, 2026-11-11) |
| exchange access and account capabilities | owner states an **operationally accessible Nobitex account** exists, with **no known account or geographic restrictions** | **O** (owner statement, 2026-11-11) |
| capital availability and transfer restrictions | **none known**; capital remains available for the intended research period | **O** (owner statement, 2026-11-11) |

**Explicitly not done:** these are owner statements of "no known restrictions," not verified facts,
and not venue evidence. They do not satisfy the `I-2` / `B-02` capability standard, which requires a
dated yes/no per capability (KYC tier, API credentials and permissions, order types, instrument
specifications, rate limits, regional restrictions) with supporting venue documentation
(`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §3.1). No Nobitex API access, venue contact, or
capability check occurred in this stage.

---

## 4. Venue decision (frozen)

**F** (`stage2n` §7.1, D-05 staged A+B): **Binance is the research data venue; Nobitex is the
intended execution venue.** The cost-evidence standard is Nobitex-specific measurement
(dated fee schedule, measured spread, depth, slippage, latency, fill evidence,
`stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §7.1). **F** (`stage2n` §8.1, D-06): the
conservative **p95** of the measured cost distribution is primary; sensitivity reporting is
mandatory; an optimistic-only pass is prohibited. The rule is defined but **cannot be applied until a
Nobitex cost distribution exists**, and none does.

**Verified fact:** no venue evidence of any kind exists in this repository. Exchange minimums,
minimum notionals, lot steps, fees, spread, liquidity, depth, slippage, and fill behaviour on Nobitex
are all **unverified (U)**.

**Explicit statement required by this artifact:** **Binance historical data does not establish
Nobitex execution feasibility.** The research venue's data, depth proxies, and the frozen `26 bp`
cost proxy are research constructs and are not evidence about Nobitex
(`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §8). The `$1`–`$3` order range is **not
validated against any Nobitex minimum order size, lot step, or technical limit**, and no such check
was performed in this stage.

---

## 5. Evidence gaps that remain

| gap | blocker | gate |
|---|---|---|
| Nobitex account capability evidence (per-capability, dated, documented) | `B-02` (narrowed by the owner's accessibility statement, standard unmet) | Gate 1 |
| Nobitex cost distribution (for the p95 rule) | `B-03` | Gate 1 |
| Nobitex liquidity and execution evidence (depth, minimums, lot step, slippage at the intended order size) | `B-04` | Gate 1 |
| executability of the `$2,500` research-leg notional cap and of the `$1`–`$3` real-base order range | `R-05` executability half | Gate 1 |

The `$2,500` notional cap is a **research-leg parameter** and is not re-expressed or scaled onto the
`$100` real base in this draft; real-base notional policy belongs to the future, separately governed
strategy risk policy.

---

## 6. Open items carried by this statement

1. **U — real-base per-trade sizing convention:** not set and not invented here (Stage 2S
   clarification record §5.1; `stage2q` §3.3 consequence 3).
2. **I — real-base expression of the `$250` annual target:** a ratification decision, not a
   derivation of this draft.
3. **U — venue evidence:** all items in §5, Gate 1 territory, untouched by this stage.

---

## 7. What this statement does not do

- It does not change D-04, D-05, D-06, D-01, or D-02, and does not reopen the research leg.
- It does not claim Nobitex can execute any order size, and does not convert the owner's statements
  into verified venue capability.
- It does not process data, contact any venue, pass Gate 0, or authorize any gate or trading.

---

## 8. Ratification

This draft requires explicit owner ratification to become Gate 0 artifact `A-4`. Ratifying it is
separate from ratifying the objective memo and the risk policy statement.
