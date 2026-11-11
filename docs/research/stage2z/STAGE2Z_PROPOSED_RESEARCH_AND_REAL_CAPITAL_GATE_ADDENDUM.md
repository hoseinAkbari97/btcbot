# Stage 2Z — Proposed Addendum: Research-Leg Readiness and Real-Capital Readiness

**DRAFT — NOT ADOPTED — NO RESEARCH AUTHORIZATION**

**Stage:** 2Z (governance drafting and decision preparation only)
**Instrument type:** proposed addendum to `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`, prepared for the
owner's **O-1** decision in `STAGE2Z_O1_OWNER_DECISION_PACKET.md`
**Status:** draft text only. It has no force. It amends nothing, passes no gate, satisfies no
requirement, authorizes no stage, and creates no owner decision.
**Date:** 2026-11-11
**Version:** 1.0.0-draft
**Prepared under:** the Path C recommendation in
`stage2y/STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` §4, and the boundary in
`stage2y/STAGE2Y_AUTHORIZATION_BOUNDARY.md` §1–§5

---

## 0. Status, purpose, and authority

### 0.1 Status

This document is a **proposal**. Until the owner adopts it by the mechanism in §14, the protocol in
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` applies exactly as written, including the unconditional
prohibition in its §3.5. Nothing in this document may be cited as current authority.

### 0.2 Purpose

To remove one defect identified in Stage 2Y: Gate 0's **inputs** are scoped by capital base, while
Gate 0's **failure rule** (protocol §3.5) is not. The result is a closed loop:

> Gate 0 is recorded as not passed → §3.5 bars hypothesis registration and strategy data access → the
> evidence T-4 requires cannot be produced → T-4 stays deferred → R-08 stays `P` and R-15 stays `B` →
> Gate 0 stays recorded as not passed.

**Verified fact** (`stage2y/STAGE2Y_GOVERNANCE_DEPENDENCY_MAP.md` §3–§4): the loop is
scoping-induced, not evidence-induced, and no additional evidence can break it.

This addendum proposes to make the failure rule as scoped as the inputs already are. It does **not**
propose to pass Gate 0, to authorize research, or to decide T-4.

### 0.3 Authority and hierarchy

1. The addendum is subordinate to explicit owner decisions. Where an owner decision and this
   addendum differ, the owner decision governs.
2. If adopted, the addendum is read together with the protocol. It changes only the matters stated in
   §12 (proposed changes). Every other provision of the protocol continues in force unchanged.
3. The addendum does not amend, replace, reinterpret, or reopen D-01 through D-15, A-1 through A-4, or
   T-1 through T-6. Those instruments keep their recorded values, dates, and statuses.
4. No clause of this addendum may be read to satisfy a requirement, close a blocker, or advance a
   gate.

---

## 1. The problem, stated from the sources

### 1.1 Gate 0's inputs are already scoped by base

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §5):

| row | scope as recorded |
|---|---|
| `R-07` | "Capital and sizing context, **research leg**" — `S` |
| `R-08` | "Capital and sizing context, **real capital**" — `O` at 2P, `P` from Stage 2Q onward |
| `R-15` | "**S** for the research leg; **B** for any real-capital claim" |

**Verified fact** (`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4, artifact `A-4`): the
capital and execution context statement is required to contain "**the open real-capital item**". The
Gate 0 artifact is therefore *defined* to record real capital as open, not to close it.

**Verified fact** (`stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §4): under the research-only
option, `R-08` "is answered *as a scope statement* rather than as a figure: the requirement is
satisfied for the research stage and explicitly deferred for any live stage."

### 1.2 Gate 0's failure rule is not scoped

**Verified fact** (protocol `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3.5, verbatim):

> "If Gate 0 is incomplete, no hypothesis may be registered and no data may be accessed for a
> strategy experiment. A research stage may still review documentation or design methodology, but it
> may not count signals or outcomes."

**Verified fact** (`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §4): Gate 0 does not
pass because `R-08` is `P` and `R-15` is `B`, and "It cannot pass on the research leg alone while the
owner's stated objective is the real-capital one."

### 1.3 The consequence

Because §3.5 attaches a single global prohibition to a single global status, an incomplete
real-capital context blocks a research-leg experiment whose own inputs are complete. The addendum
addresses exactly that asymmetry.

---

## 2. Definitions used in this addendum

These definitions are normative **only if the addendum is adopted**. They introduce no new
requirement and no new gate.

| term | definition |
|---|---|
| **Capital base** | one of two recorded bases: the `$10,000` **research leg** (`R-07`) or the `$100` **real capital** (`R-08`) |
| **Research leg** | the `$10,000` research construct: `1%` fixed-fractional risk, one position, no leverage, spot long-only (`stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` §1) |
| **Real capital** | the owner's stated `$100`, with the `$30` personal cumulative tolerance and the `$1`–`$3` practical order-notional range (`stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` §2) |
| **Gate 0 status** | the single recorded verdict on Gate 0. It remains **NOT PASSED**. |
| **Research-leg readiness determination** | a record, made under §4.3, that every Gate 0 requirement applicable to the research-leg base is satisfied. It is **not** Gate 0 passage, **not** a gate, and **not** an authorization. |
| **Real-capital readiness** | the state in which every Gate 0 requirement applicable to the real-capital base is satisfied. It does not exist today: `R-08` is `P` and `R-15` is `B`. |
| **Deployment claim** | any statement about real-capital return, drawdown, sizing, funding, execution feasibility, or deployability |
| **Authorized stage** | a stage authorized in writing by the owner under protocol §2.1 |

---

## 3. Scope

### 3.1 What this addendum addresses

Only two things:

1. the **scope of the failure rule** in protocol §3.5; and
2. the **representation of Gate 0 status** for each capital base.

### 3.2 What this addendum does not address

It does not alter:

- the Gate 0 pass criteria (protocol §3.3) or required artifacts (§3.4);
- any Gate 1–6 input, pass criterion, artifact, or failure rule;
- the freeze policy (§10), the data-block separation (§8.2), or the audit governance (§7, §11);
- any threshold, metric, decision value, or date in D-01–D-15, A-1–A-4, or T-1–T-6;
- any recorded status code, including `R-08 P` and `R-15 B`;
- the `$100`, `$30`, `$1`–`$3`, `$250`, or `$10,000` values;
- any blocker in `stage2p/OPEN_BLOCKER_REGISTER.md`.

### 3.3 What it does not create

It creates no gate, no requirement, no reviewer, no authorization, no evidence, and no readiness. It
closes nothing.

---

## 4. Gate 0 assessment per capital base

### 4.1 One gate, one recorded status

Gate 0 remains a single gate with a single recorded verdict. That verdict is **NOT PASSED** and may
not be recorded as passed on either base. The per-base assessment below explains *which requirements
apply to which base*; it does not create a second gate and does not change the verdict.

### 4.2 Applicability of the requirements

**Verified fact:** this table is a reading of the requirement titles and scopes as recorded in
`stage2p/GATE0_READINESS_ASSESSMENT.md` §5 and `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md`
§5. It changes no status code.

| requirement | research-leg base | real-capital base |
|---|---|---|
| `R-01` MME | applies — `S` | applies — `S` |
| `R-02` drawdown limit | applies — `S` | applies — `S` |
| `R-03` per-trade limit | applies — `S` | applies — `S` |
| `R-04` tail limit | applies — `S` | applies — `S` |
| `R-05` liquidity / position size | Gate 1 item — `P` | Gate 1 item — `P` |
| `R-06` operational risk | N/A (not adopted) | N/A (not adopted) |
| `R-07` research-leg capital context | applies — `S` | not applicable (its own title scopes it to the research leg) |
| `R-08` **real-capital** capital context | **not applicable** (its own title scopes it to real capital) | applies — `P` |
| `R-09` estimands | applies — `S` | applies — `S` |
| `R-10` venue / cost standard | Gate 1 item — `P` | Gate 1 item — `P` |
| `R-11` error control | applies — `S` | applies — `S` |
| `R-12` dependence treatment | applies — `S` | applies — `S` |
| `R-13` blocking decisions resolved | applies — `S` | applies — `S` (D-04 resolved; T-4 is not a register decision — see §5.4) |
| `R-14` no silent default | applies — `S` | applies — `S` |
| `R-15` objective in testable form | applies — **S** (its own text) | applies — **B** (its own text) |
| `R-16` unit compatibility | applies — `S` | applies — `S` |
| `R-17`–`R-20` artifacts | apply — `S` | apply — `S` |
| `R-21` frequency acknowledgment | applies — `S` | applies — `S` |
| `R-22` independent reviewer | Gate 4 item — `P` | Gate 4 item — `P` |
| `R-23` deferred D-15 | N/A | N/A |

### 4.3 The research-leg readiness determination

When every requirement marked "applies — `S`" for the research-leg base in §4.2 is satisfied, and
`R-15` is satisfied for that base per its own text, the record may state:

> **"Gate 0 research-leg inputs complete"** — a **research-leg readiness determination**, not Gate 0
> passage.

Limits of that determination:

1. It is **not** a Gate 0 pass and may never be written as one.
2. It satisfies no requirement that is not already marked `S` for the research-leg base.
3. It does **not** authorize any stage. A named stage authorization under protocol §2.1 remains
   separately required.
4. It does **not** apply to `R-05`, `R-10`, or `R-22`, which remain the Gate 1 and Gate 4 items they
   already are.
5. It says nothing about real capital.

### 4.4 The real-capital status

For the real-capital base, `R-08` is `P` and `R-15` is `B`. Gate 0 is therefore **NOT PASSED** for
real capital, and no real-capital claim of any kind may be made. This is unchanged from
`stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §4 and from the owner's W-F statement.

### 4.5 The global verdict

> **Gate 0: NOT PASSED.**

The addendum does not alter that line. It permits, at most, a separately named research-leg readiness
determination to sit beside it, with the meaning and limits in §4.3.

---

## 5. `R-08` and `R-15` per base

### 5.1 `R-08` — real-capital capital and sizing context

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §5): `R-08` is titled "Capital and sizing
context, **real capital**" and its missing evidence is "the owner's real deployable capital, or an
explicit statement that none is committed."

**Verified fact** (`stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §6.2; `stage2t/STAGE2T_DECISION_PACKET.md`
§3): from Stage 2R onward, `R-08` also carries the real-base per-trade sizing rule, and "T-4c keeps
`R-08` **P**."

**Proposed reading.** `R-08` applies to the real-capital base only. It is not an input to the
research-leg readiness determination. It remains `P`, and its requirement is the one recorded from
Stage 2R/2T onward: the real-capital capital context **and** the real-base per-trade sizing
convention (T-4). The narrower Stage 2P baseline wording is preserved as history and is not rewritten
or declared wrong.

**Residual, disclosed.** The 2P and 2R/2T wordings still differ. This addendum does not reconcile them
for the real-capital base; it confines their effect to that base. See conflict `C-2` in
`STAGE2Z_CONFLICT_TRACEABILITY_MATRIX.md`.

### 5.2 `R-15` — objective in testable form

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §5, verbatim): "**S** for the research
leg; **B** for any real-capital claim".

**Proposed reading.** `R-15` is applied exactly as its own text states, on each base. It is satisfied
for the research-leg base and remains blocked for the real-capital base. Its recorded status code
`B` is unchanged; the research-leg determination relies on the row's own `S` half, not on a
reinterpretation of `B`.

### 5.3 What this does not do

It does not mark `R-08` or `R-15` satisfied, does not change their status codes, and does not close
any blocker. `B-07` stays closed only in the consolidation sense recorded in
`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §3.

### 5.4 `T-4` is not a Gate 0 blocking decision

**Verified fact** (`stage2m/OWNER_DECISION_REGISTER.md` §1): the register marks `D-04` **BLOCKING**
and has no decision ID for a real-capital per-trade sizing convention. T-4 is a Stage 2T decision
attached to D-04.

**Verified fact** (`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §2): "`R-13` stays
**S** because it concerns the decisions D-01…D-15, all resolved; the deferred item is the Stage 2T
decision **T-4**, which is tracked by `R-08`, not by `R-13`."

**Proposed reading.** Protocol §3.3 tests whether "every decision in the owner register that is marked
**blocking** is resolved". T-4 is not such a decision. It affects Gate 0 only through `R-08` on the
real-capital base. This records the register's own construction; it does not resolve T-4.

---

## 6. Does an unresolved T-4 prevent research-leg authorization?

### 6.1 The position under the current protocol

**Verified fact** (protocol §3.5): the prohibition is unconditional. Under the protocol as written
today, an incomplete Gate 0 — including one held incomplete only by `R-08` — bars hypothesis
registration and strategy data access on any base. **Today, therefore, the unresolved T-4 does
prevent a research-leg experiment.** That is a statement of current text, not a recommendation.

### 6.2 The proposed position

If the addendum is adopted:

1. The prohibition in protocol §3.5 is scoped to the capital base whose Gate 0 inputs are incomplete.
2. An incomplete **real-capital** context bars real-capital work and real-capital claims.
3. It does not bar a **research-leg** stage whose own inputs are complete under §4.3 — but only if a
   separate, named stage authorization under protocol §2.1 exists, with its own scope, data,
   prohibitions, and stop condition.
4. The determination in §4.3 is a precondition, not an authorization.

### 6.3 Why the research leg does not need T-4

**Verified fact** (`stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md` §1; `stage2p/GATE0_READINESS_ASSESSMENT.md`
§5 row `R-07`): the research-leg risk rule is already frozen — `1%` fixed-fractional of `$10,000`,
`1.00R` per-trade cap, `15%` drawdown of prior peak, `CVaR95 = 0.50R`, `$2,500` entry-notional cap.
None of these references a real-capital sizing convention.

`T-4` answers a different question: how real capital, not research capital, would be sized. Its
evidence requirements include research outputs (`stage2w/STAGE2W_OWNER_DECISION_PACKET.md` §4), which
is why the unscoped failure rule creates the loop.

### 6.4 What this section does not do

It does not decide T-4, does not approve any real-capital risk amount or percentage, and does not
authorize the research leg. T-4 remains **deferred** exactly as recorded in
`stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §1 and §4.

---
