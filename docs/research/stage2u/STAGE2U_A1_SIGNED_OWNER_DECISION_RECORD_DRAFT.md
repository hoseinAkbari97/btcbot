# Stage 2U — A-1 Gate 0 Owner Decision Record (Draft for Signature)

**Corresponds to:** Stage 2P artifact `A-1` (Gate 0 owner decision record, required as a *signed*
instrument by `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3.4 and `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4)
**Status:** **DRAFT — owner decisions recorded verbatim; signature pending.** This record is not a
signed instrument until the owner explicitly affirms it (§6). `R-17` remains **P**
**Version:** 1.0.0-draft
**Record date:** 2026-11-11 (UTC)
**Provenance:** `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` (2026-11-09),
`stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` (2026-11-10), the Stage 2S record (2026-11-11), and the
owner's explicit written Stage 2U instruction (2026-11-11)
**Authorizes:** nothing

---

## 1. Record identification

| field | value |
|---|---|
| title | Gate 0 Owner Decision Record |
| scope | Gate 0 decisions D-01, D-02, D-03, D-07, D-08, D-09, D-12 (Stage 2P §4 core list), plus the Stage 2T ratification decisions T-1…T-6 |
| decision vs recommendation | every row below is an **owner decision**; the agent has added no decision, no threshold, and no value |
| rule | this record may restate recorded decisions and may not introduce new ones; conflicts are escalated, not resolved here |

---

## 2. Part A — Gate 0 decisions (Stage 2P §4 core list)

| ID | decision | recorded value (verbatim in substance) | date | source |
|---|---|---|---|---|
| **D-01** | minimum meaningful effect | Definition A — **net R per executed trade**; value **`0.10R` net per executed trade**; annual contribution target **`$250`/year** | 2026-11-09 (definition) / 2026-11-10 (values) | `stage2n` D-01; `stage2o` §2.1 |
| **D-02** | acceptable drawdown and risk | maximum drawdown **`15%`** of prior equity peak, net-of-cost mark-to-market; maximum realized net loss **`1.00R`** per executed trade; tail **`CVaR95 = 0.50R`**; maximum entry notional **`$2,500`** on the `$10,000` research reference; scope **research leg only** | 2026-11-09 (option C) / 2026-11-10 (limits) | `stage2n` D-02; `stage2o` §4–§8 |
| **D-03** | primary performance estimand | **A — net R per executed trade**, after all-in execution costs; co-estimand **D — net annual contribution** | 2026-11-09 | `stage2n` §3.1 |
| **D-07** | annual contribution as co-primary metric | **A — yes, co-primary**; annual target value `$250`/year (set through D-01, 2026-11-10) | 2026-11-09 / 2026-11-10 | `stage2n` §5.1; `stage2o` §2.1 |
| **D-08** | statistical confidence and error control | **A+B**: two-sided `α = 5%`, target power `80%`, **hierarchical** co-primary allocation (per-trade primary first), precision interval reported | 2026-11-09 | `stage2n` §9.1 |
| **D-09** | dependence treatment | **C — cluster-robust plus block bootstrap**; the two must agree; **disagreement ⇒ inconclusive** (not pass, not fail); episode definition and block/resampling scheme open to pre-registration | 2026-11-09 | `stage2n` §10.1 |
| **D-12** | validation/OOS access and one-look policy | **A — strict one-look**: one validation look, one OOS look, no changes after either look; access logging required (date, purpose, result); embargo between blocks; additional looks only as a new, separately authorized stage with a new pre-registration | 2026-11-09 | `stage2n` §13.1 |

---

## 3. Part A-addendum — other resolved decisions referenced for completeness

The `R-17` row describes this artifact as "a Gate 0 decision record consolidating **D-01…D-07**"
(`stage2p/GATE0_READINESS_ASSESSMENT.md` §5), while the Stage 2P §4 content list is
**D-01/D-02/D-03/D-07/D-08/D-09/D-12**. Both readings are served here: Part A is the operative §4
core list, and this addendum lists the remaining resolved decisions. The discrepancy itself is
documented in §7 and is **not** silently resolved.

| ID | recorded value | date | source |
|---|---|---|---|
| **D-04** | research leg: `$10,000` equity, `1%` fixed-fractional risk, one position, no leverage; real-capital basis: **Option A selected** 2026-11-10, **inputs complete** 2026-11-11 (`$100` all available capital; `$30` personal cumulative tolerance; `$1`–`$3` order notional; no known deposit/withdrawal/access restrictions; capital remains available) | 2026-11-09 / 2026-11-10 / 2026-11-11 | `stage2n` §2; `stage2q` §3; `stage2r` §3; `stage2s` clarification record §4 |
| **D-05** | staged A+B; **Binance** historical research data; **Nobitex** intended execution venue; Nobitex-specific cost-evidence standard | 2026-11-09 | `stage2n` §7 |
| **D-06** | conservative **p95** of the measured cost distribution primary; sensitivity reporting mandatory; optimistic-only pass prohibited | 2026-11-09 | `stage2n` §8 |
| **D-10** | methodology **A** — power for the MME; dependence inflation via D-09; execution-rate adjustment; numeric requirement pending `σ`, `DE`, `p_exec` | 2026-11-09 | `stage2n` §11 |
| **D-11** | **A+D** — one primary hypothesis, no multiple hypotheses, OOS confirmation required | 2026-11-09 | `stage2n` §12 |
| **D-13** | **B+E** — independent audit standard; specialist if feasible; residual disclosure required | 2026-11-09 | `stage2n` §14 |
| **D-14** | **C** — all three regimes; D-12 governs the OOS look; single-interval provisional | 2026-11-09 | `stage2n` §15 |
| **D-15** | **OPEN — deferred**; blocks only any new candidate, not Gate 0; unchanged | 2026-11-09 | `stage2m` register; `stage2n` |

---

## 4. Part B — Stage 2T ratification decisions (owner, 2026-11-11)

Recorded exactly as supplied; provenance: the owner's explicit written Stage 2U instruction
(2026-11-11). Decision **T-1 … T-6** identifiers follow `stage2t/STAGE2T_DECISION_PACKET.md`.

| ID | owner decision |
|---|---|
| **T-1** | **RATIFY** — A-2 economic objective memo |
| **T-2** | **RATIFY** — A-3 risk policy |
| **T-3** | **RATIFY** — A-4 capital/execution context |
| **T-4** | **DEFER** — real-capital per-trade sizing convention |
| **T-5** | Preserve **`$250` annually on `$100` capital**, equivalent to **`250%` annually** |
| **T-6** | Wait condition (T-1…T-5 resolved) satisfied; **draft the A-1 signed owner decision record** |

**Effect of T-1…T-3:** the three Stage 2S draft files are ratified **as they stand**; their contents
were not edited. The authoritative artifacts are: `A-2` =
`stage2s/STAGE2S_A1_OBJECTIVE_MEMO_DRAFT.md`, `A-3` =
`stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md`, `A-4` =
`stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md`. **Effect of T-6:** this document is the
drafted `A-1`; its signature is the one remaining act (§6).

---

## 5. Part C — qualifications recorded with the decisions

1. **T-5 is an unvalidated owner objective.** `$250` annual contribution on `$100` starting capital
   is a **`250%` annual contribution target before any compounding interpretation**. It is not a
   forecast, expected return, demonstrated edge, or claim of feasibility.
2. **The `$10,000` research-reference objective is not substituted.** `$250 / $10,000 = 2.5%`
   remains the research-reference framing; `$250 / $100 = 250%` is the real-capital expression. The
   `$100` real capital and the `$10,000` research reference remain distinct.
3. **T-4 is deferred.** No real-capital per-trade risk amount or percentage has been invented or
   approved. Order notional (`$1`–`$3`) is **not** dollar risk per trade.
4. **D-02's limits remain research-leg limits** (`$10,000` research leg). They are not approved
   live-trading limits.
5. **Ratification does not establish Nobitex execution feasibility.** Fees, spread, slippage, tick
   size, lot size, minimum order, settlement, and operational constraints still require venue
   evidence (`B-02`, `B-03`, `B-04`, `R-05`).
6. **Owner statements are not venue evidence.** The owner's statements about the account and about
   deposit/withdrawal restrictions are not independently verified.
7. **No achievability claim.** The `$250` objective is retained, not demonstrated; Gate 3 may still
   fail on frequency.

---

## 6. Part D — owner approval and signature

**Signature status: UNSIGNED.** The agent does not sign this record and does not fabricate a
signature. The record becomes a signed Gate 0 instrument only when the owner explicitly affirms it
in writing, dated, recorded verbatim.

| field | value |
|---|---|
| owner affirmation | *(pending — the owner states: ratify / reject / revise this consolidated record)* |
| date | *(pending)* |
| verbatim statement | *(pending)* |

**Effect of signing:** `A-1` exists as a signed Gate 0 instrument and `R-17` can be recorded as
satisfied in the record that captures the signature. **Until then:** `R-17` remains **P**, `B-07`
remains **open**, and Gate 0 remains unpassed.

---

## 7. R-17 wording discrepancy (documented, not reconciled)

- `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 (authoritative content definition):
  `A-1` must contain **D-01, D-02, D-03, D-07, D-08, D-09, D-12** as resolved, each with its date
  and verbatim value.
- `stage2p/GATE0_READINESS_ASSESSMENT.md` §5, row `R-17` (requirement wording): "a Gate 0 decision
  record consolidating **D-01…D-07**".

The two are not identical: §4 adds D-08, D-09, D-12 and omits D-04, D-05, D-06 from its core list.
Per the Stage 2T packet and the Stage 2U instruction (§3.7), the **§4 list governs content**. This
record therefore carries the §4 core list in Part A and the additional resolved decisions
(D-04, D-05, D-06, D-10, D-11, D-13, D-14) in Part A-addendum. No interpretation is silently
chosen: if the owner requires a different content list, the record is revised before signature.

---

## 8. What this record does not do

It does not sign or ratify itself; it does not introduce any decision, threshold, risk amount,
sizing convention, or objective; it does not change D-01, D-02, D-15, or any prior-stage artifact;
it does not process data, pass Gate 0, or authorize any gate, research, or trading.
