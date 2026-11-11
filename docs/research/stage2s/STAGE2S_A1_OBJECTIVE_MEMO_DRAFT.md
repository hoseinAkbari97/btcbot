# Stage 2S — Gate 0 Artifact Draft A-1: Objective Memo

**Corresponds to:** Stage 2P artifact `A-2` (economic objective memo),
`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4
**Status:** **DRAFT — NOT RATIFIED.** This is a proposal prepared under the Stage 2Q Q4 Option A
authorization. It becomes a Gate 0 artifact only if the owner explicitly ratifies it.
**Restates:** frozen decisions only. It introduces no new decision and resolves no conflict.
**Sources:** `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §3 and §5, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` §2, `stage2o/STAGE2O_D01_D02_DECISION_PACKET.md` §4, `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §4, `stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §3.1

---

## 0. Purpose and classification key

This memo consolidates the frozen economic objective for the research leg, so that a future
experiment knows what it must detect. Every value below carries exactly one classification:

| code | meaning |
|---|---|
| **F** | frozen owner decision |
| **O** | owner-provided factual input |
| **C** | calculated value, with formula |
| **E** | external evidence (none is cited in this draft; none has been collected) |
| **U** | unresolved information |
| **I** | agent interpretation requiring owner ratification |

---

## 1. The objective

| element | value | class | source |
|---|---|---|---|
| primary estimand | **net R per executed trade**, after all-in execution costs | **F** | `stage2n` §3.1 (D-03 option A) |
| co-primary estimand | **net annual contribution** (currency) | **F** | `stage2n` §3.1 (D-03 option D), §5.1 (D-07 option A) |
| minimum meaningful effect (MME) | **`0.10R` net per executed trade** | **F** | `stage2o` §2.1 (D-01) |
| annual contribution target | **`$250` per year**, net | **F** | `stage2o` §2.1 (D-01) |
| research equity reference | **`$10,000`** | **F** | `stage2n` §2.2 (D-04 research leg) |
| error control | `α = 5%` two-sided; power `80%`; hierarchical co-primary allocation | **F** | `stage2n` §9.1 (D-08) |
| dependence treatment | cluster-robust plus block bootstrap; disagreement ⇒ inconclusive | **F** | `stage2n` §10.1 (D-09) |

**Owner-selected, not verified.** Every value in this table is an owner preference selected before
any test. None has been tested against data; whether `0.10R` net is attainable is **not** claimed or
implied here (`stage2p/GATE0_READINESS_ASSESSMENT.md` §3.3).

---

## 2. Frequency arithmetic, disclosed

**Label:** arithmetic on recorded values only (**C**). No data was processed and no forecast is made.

1. On the `$10,000` research leg at fixed-fractional `1%` risk, `1R = $100`
   (`$10,000 × 1%`), and the MME is worth `$10` per executed trade (`0.10R × $100`).
2. Under **full `1R` realized risk per trade**, the annual target implies
   `$250 / ($10 per trade) = 25 executed trades per year`
   (`stage2p/GATE0_READINESS_ASSESSMENT.md` §7.1).
3. This count assumes every executed trade earns exactly the MME, ignores compounding, idle capital,
   and `p_exec < 1` — each of which pushes the true requirement **up**.
4. When the `$2,500` research-leg notional cap binds (stops below `4%` on the research leg), `R` is
   defined on executed notional and each trade contributes fewer dollars, raising the required count
   to `50`–`100` at `2%`–`1%` stops (`stage2p` §7.4; Stage 2Q Q3 selection).

**Historical opportunity-frequency concern — acknowledged, unresolved (U).** The frozen censuses
recorded approximately 20 (Candidate A), 10 (D), 7 (B), and 3 (C) non-overlapping opportunities per
year over the `1,277`-day development interval — *opportunities, not executed trades and not outcome
evidence* (`stage2p` §7.2). The owner acknowledged on 2026-11-10 (Stage 2Q Q2) that Gate 3 may
therefore stop on frequency rather than on edge, and that this is a pre-registered, foreseen
outcome that no later document may present as a surprise or as a reason to lower the bar
retrospectively. **D-01 is unchanged by this memo.**

**No achievability claim.** This memo does not claim that `$250`, `0.10R`, or any trade count is
historically or prospectively achievable.

---

## 3. Real-capital context (recorded, not merged into the objective)

| element | value | class | source |
|---|---|---|---|
| stated strategy capital | **`$100` USD as of 2026-11-11 — all capital currently available for this strategy** | **O** | `stage2r` §3.1; Stage 2S clarification A (2026-11-11) |
| owner's maximum acceptable loss | `$30` cumulative, personal tolerance (`30%` of stated capital) | **O** | `stage2r` §3.2 |
| practical order range | `$1`–`$3`, confirmed as order notional in USD | **O** | `stage2r` §3.3; Stage 2S clarification B |

**I — flagged for owner ratification, not decided here:** the `$250` annual target is frozen on the
`$10,000` research reference. Its expression on the `$100` real base is a separate owner decision;
this draft neither scales the target to the real base nor treats the research reference as the real
account. The research leg remains a labelled comparison basis
(`stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3.3).

---

## 4. What this memo does not do

- It does not change D-01, D-03, D-07, or D-08, and does not reopen any frozen value.
- It does not claim the target is achievable, and does not rank or evaluate any candidate.
- It does not process data, access validation or out-of-sample rows, or run any computation beyond
  the arithmetic restated above from frozen documents.
- It does not pass Gate 0 or authorize any gate, experiment, or trading.

---

## 5. Ratification

This draft requires explicit owner ratification to become Gate 0 artifact `A-2`. Items the owner may
wish to correct or decide while ratifying: the real-base expression of the annual target (§3), and
any wording that misstates a frozen decision. Ratification of this memo is separate from
ratification of the risk policy and capital/execution context drafts.
