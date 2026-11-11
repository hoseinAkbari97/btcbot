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
