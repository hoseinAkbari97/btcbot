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

## 7. Preservation of the Gate 1–6 sequence and the audit

### 7.1 Sequence unchanged

**Verified fact** (protocol §2.2): the order is Gate 0 → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5
→ Gate 6. The addendum does not reorder, split, merge, skip, or duplicate a gate. A research-leg
determination under §4.3 does not let a stage begin at any gate other than the one authorized.

### 7.2 Gate-specific preservation

| gate | preserved requirement |
|---|---|
| **Gate 1** — data and venue validity | protocol §4.2 inputs and §4.3 pass criteria unchanged, including the venue specification as a required input, the dataset hashes, the block separation, and the rule that cost evidence is "either measured or explicitly labelled as an assumption with a plan to replace it" |
| **Gate 2** — hypothesis registration | protocol §5.2 sixteen required inputs unchanged, including the sample-sufficiency calculation and the frozen hashes; no outcome may have been observed |
| **Gate 3** — feasibility | protocol §6.2 census unchanged: counts signals and opportunities, observes **no outcomes** |
| **Gate 4** — independent audit | protocol §7 unchanged; an independent reviewer is required; an implementer cannot audit their own work; `I-4` is still unresolved |
| **Gate 5** — controlled performance | protocol §8 unchanged; validation and OOS blocks separate, chronological, embargoed; one validation look |
| **Gate 6** — final decision | protocol §9 unchanged; "Advance to paper trading" requires all gates plus a **separate owner authorization** |

### 7.3 Audit preserved

The independent-audit requirement is not relaxed on either base. The reviewer identity
(`I-4`), the independence declaration, and the `R-22` Gate 4 item remain exactly as recorded
(`stage2m/OWNER_DECISION_REGISTER.md` D-13; `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 row `R-22`).
A research-leg result produced without a completed Gate 4 audit is not an acceptable confirmatory
result.

### 7.4 Venue specification at Gate 1 (disclosed, not changed)

**Verified fact** (protocol §4.2 versus §4.3): the venue specification is a required Gate 1 **input**,
but venue-specification completeness is not among the §4.3 **pass criteria**. This is conflict `C-4`.

The addendum does **not** add a pass criterion, because that would change a gate. It records one
disclosure rule for any future Gate 1 authorization: the gate record must state, item by item, whether
the venue specification is **known** or **UNKNOWN**, with the evidence that would resolve each unknown.
That is a reporting requirement for the stage authorization (proposed change `P-5`), not a change to
§4.3. The residual ambiguity remains until the owner decides otherwise.

---

## 8. Evidence required before T-4 may be reconsidered

### 8.1 The six items, unchanged

**Verified fact** (`stage2w/STAGE2W_OWNER_DECISION_PACKET.md` §4, verbatim list; adopted as the
revisit condition by `stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §1 and §3):

1. a validated net-of-cost expectancy from an authorized experiment;
2. measured fee, spread, and slippage distributions for the intended venue and order sizes;
3. verified minimum order/notional, lot step, tick size, and stop-order support;
4. an assessed tail-loss and gap/stop-failure distribution;
5. the strategy's actual trade frequency;
6. a restated annual objective reconciled with the above, or an explicit decision that the objective
   is aspirational and not a sizing input.

### 8.2 How each item could be produced (analysis, not authorization)

| item | class | route | requires real capital? |
|---|---|---|---|
| 1 — validated expectancy | research outcome | Gates 1–5 under separate authorization | no |
| 2 — fees, spread, slippage | documentary + sampling + measured execution | fee schedule and spread sampling are documentary/sampling; fills and slippage need order placement, which the protocol places after Gate 6 | no, for the documentary/sampling half; the execution half requires a separate owner decision (`C-6`) |
| 3 — venue constraints | documentary | venue documents and account screens under owner authorization | no |
| 4 — tails and gaps | research outcome / model | Gates 3 and 5 | no |
| 5 — trade frequency | research census | Gate 3, no outcomes | no |
| 6 — restated objective | owner decision | owner only | no |

### 8.3 Limits

1. Meeting the six items "does not itself approve a convention; it only makes the decision appropriate
   to take up again" (`stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §3 item 3).
2. No item above is satisfied by this addendum.
3. Item 2's execution half is not authorized by this addendum. The protocol defines no
   "measurement-only execution" category; creating one is an owner decision (conflict `C-6`).
4. Item 6 cannot be answered before items 1–5 exist in usable form.

---

## 9. Cost, venue, and claim boundary

### 9.1 The venue split is unchanged

**Verified fact** (`stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` §4; `stage2n` §7.1):
**Binance is the research data venue; Nobitex is the intended execution venue.** The cost-evidence
standard remains Nobitex-specific measurement.

### 9.2 The proxy rule is unchanged

**Verified fact** (`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §8): "the frozen `26 bp` figure
as a venue cost" is an unacceptable substitution, because it is "documented as a Binance spot proxy,
explicitly not a measurement." **Verified fact** (`stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md`
§7.3): the proxy "may be too high or too low for Nobitex."

A research-leg result may use the proxy only as an explicitly labelled **research-leg cost
assumption with a plan to replace it** (protocol §4.3). It may never be described as a Nobitex cost,
and no result computed with it may be described as execution-feasible.

### 9.3 Claim boundary

| claim | research leg | real capital |
|---|---|---|
| a dependence-adjusted net effect of X R on historical Binance data | permitted at Gates 5–6, with intervals and deviations | no |
| distinguishable from zero at the pre-registered error control | permitted under D-08/D-09 | no |
| not feasible at the recorded frequency | permitted — a Gate 3 stop is a valid result | no |
| the strategy is profitable | no — profitability is not an estimand and no P&L is produced | no |
| the strategy will earn `$250` per year | no | no |
| Nobitex can execute this strategy | no | not until Gate 1 venue evidence **and** measured execution |
| the real-capital objective is achievable | no | not until T-4 is decided |
| the account should risk `$X` per trade | no | only after T-4 |

### 9.4 Required reporting sentence

Every Gate 5 and Gate 6 report produced on the research-leg track must contain:

> *"This result is research-leg evidence on historical Binance data under a labelled cost assumption.
> It is not evidence of Nobitex execution feasibility, not a real-capital return, and not a sizing
> recommendation."*

---

## 10. Statistical sufficiency and data separation preserved

### 10.1 Frozen statistical decisions

**Verified fact** (`stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §9–§13; `stage2p/GATE0_READINESS_ASSESSMENT.md`
§5 rows `R-11`, `R-12`, `R-16`): `α = 5%` two-sided; power `80%`; hierarchical co-primary allocation;
cluster-robust plus block bootstrap, disagreement ⇒ inconclusive; `R`-denominated primary metric.

### 10.2 Sample sufficiency unchanged

**Verified fact** (protocol §5.2 item 11; `stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §5.2): the
registration must carry `N_ind`, `N_obs`, `required_opportunities`, assumptions, and sensitivity, with
`N_ind ≈ (z_{1-α/2} + z_{1-β})² σ² / δ²`, `N_obs ≈ N_ind × DE`, and
`required_opportunities ≈ N_obs / p_exec`. Step 5 states that an unattainable requirement is
"a legitimate outcome, not a reason to lower the requirement."

The addendum changes none of this. It adds no relaxation for the research-leg base.

### 10.3 The recorded arithmetic is not a forecast

`N_ind ≈ 785` at `δ = 0.10R`, `σ = 1R`, `α = 5%`, power `80%`, against `12`–`71` opportunities per
family over 1,277 days (`stage2p/GATE0_READINESS_ASSESSMENT.md` §7.2–§7.3). That is arithmetic on
recorded values, not a prediction and not a reason to lower any bar.

### 10.4 Data separation and one-look

**Verified fact** (`stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §13; protocol §8.2): D-12 is
**strict one-look with logging and an embargo**. Development, validation, and OOS blocks are
chronological and non-overlapping. No validation or OOS row may be read before its gate. The
addendum does not change the one-look rule, the embargo, or the block definitions.

---

## 11. Owner values preserved, and not treated as evidence

### 11.1 Values restated as unchanged

| item | value | status | source |
|---|---|---|---|
| research reference capital | `$10,000` | research construct, not the owner's account | `R-07`; `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` §1 |
| research risk per trade | `1%` fixed-fractional | frozen research-leg rule | D-02; `R-07` |
| drawdown limit | `15%` of prior peak | frozen research-leg rule | D-02; `R-02` |
| per-trade limit | `1.00R` | frozen research-leg rule | D-02; `R-03` |
| tail limit | `CVaR95 = 0.50R` | frozen research-leg rule | D-02; `R-04` |
| entry notional cap | `$2,500` | research-leg parameter | `R-05`; `stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md` §2 |
| real capital | `$100` | owner-stated, deployable | D-04; `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` §2 |
| personal cumulative loss tolerance | `$30` | **personal, cumulative; not a per-trade or drawdown limit** | `stage2r` §3.2; `stage2s` A-3 §2 |
| practical order-notional range | `$1`–`$3` | owner-stated **notional, not risk** | `stage2r` §3.3; `stage2s` clarification B |
| annual objective | `$250` net on `$100` = `250%/yr` | **unvalidated owner objective** | T-5; `stage2u/STAGE2U_STAGE_COMPLETION_REPORT.md` §7 |

### 11.2 What none of these values establish

1. `$250` on `$100` is **250% per year**. It is an owner objective, not evidence, not a forecast, and
   not a sizing input.
2. A return target does not justify higher risk. With no validated edge, higher risk converts a small
   expected loss into a larger one faster (`stage2w/STAGE2W_OWNER_DECISION_PACKET.md` §4).
3. `$30` is a personal cumulative tolerance, not an authorized strategy drawdown limit, and it does
   not scale D-02.
4. `$1`–`$3` order notional caps planned risk at `$0.005`–`$0.30` per trade
   (`stage2w/STAGE2W_T4_SIZING_ANALYSIS.md` §3.1). A research-leg result at `$10,000` does not
   automatically translate to that base.
5. No value in §11.1 is changed, reinterpreted, or reopened by this addendum.

---

## 12. Proposed changes, enumerated

If adopted, this addendum changes exactly the following. **No threshold, metric, decision value,
requirement status, gate criterion, or owner-supplied number changes.**

| # | proposed change | why it is necessary | what it does not do |
|---|---|---|---|
| `P-1` | protocol §3.5's prohibition is scoped to the capital base whose Gate 0 inputs are incomplete | removes the loop identified in Stage 2Y §4–§5 (`C-3`) | does not authorize any stage; does not pass Gate 0 |
| `P-2` | Gate 0 status is accompanied by a per-base assessment, and a **research-leg readiness determination** may be recorded when §4.2's research-leg rows are satisfied | makes Gate 0's representation match the scoping of its inputs (`C-1`) | does not create a gate, does not change the verdict, does not mark any row `S` |
| `P-3` | `R-08` is read as applying to the real-capital base only, consistent with its own title | confines an already real-capital-specific row to its base (`C-2`) | does not change `R-08`'s status, wording, or requirement |
| `P-4` | `R-15` is applied per its own text: `S` for the research leg, `B` for real-capital claims | applies the row as written (`C-1`, `C-9`) | does not change the `B` code or mark it satisfied |
| `P-5` | a future Gate 1 stage authorization must require the gate record to disclose venue-specification completeness item by item | makes an existing input auditable without changing §4.3 (`C-4`) | does not add a pass criterion; does not change Gate 1 |

`C-5` requires no change: the rule in `stage2p` §8 and protocol §4.3 is restated, not amended. `C-7`
and `C-8` are preserved as recorded. `C-6` is deliberately **not** addressed: it needs a separate owner
decision, not a drafting change.

---

## 13. Prohibitions

Nothing in this addendum, and nothing in the act of preparing it, permits any of the following. They
remain prohibited until a separate, explicit, written owner authorization says otherwise:

- market-data access, download, or processing of any kind;
- a feasibility census or any signal or opportunity count;
- strategy or candidate design, selection, naming, or revision;
- parameter selection, fitting, or optimisation;
- backtesting, simulation, or performance evaluation;
- expectancy, return, profitability, or P&L calculation or claim;
- validation or out-of-sample data access;
- venue research, contact, or capability checking;
- cost, spread, depth, liquidity, fill, slippage, or latency measurement;
- real-capital sizing, a sizing convention, or sizing implementation in code;
- paper trading, live trading, leverage, or bot execution;
- changes to D-01–D-15, A-1–A-4, or any frozen artifact;
- Gate 0 passage, or progression to any gate;
- treating Binance proxy data as verified Nobitex execution evidence;
- treating a research-leg result as a real-capital return or as a reason to size real capital.

---

## 14. Adoption, effect, and non-effects

### 14.1 Adoption mechanism

The addendum becomes effective only if the owner issues a written statement that:

1. identifies this document by path and by the SHA256 recorded in
   `STAGE2Z_O1_OWNER_DECISION_PACKET.md` §4;
2. states **adopt** (or adopt with the changes listed under **revise**);
3. carries a date; and
4. is recorded verbatim, without agent paraphrase, in a new record created for that purpose.

A statement that does not name the hash adopts nothing, because the text could otherwise change after
the decision. The agent may not create, infer, or pre-fill that statement.

### 14.2 Effects of adoption

Only these:

1. `P-1` through `P-5` become part of the governance text.
2. A research-leg readiness determination may be recorded under §4.3 once its conditions hold.
3. The failure rule is scoped as described in §6.2.

### 14.3 Explicit non-effects of adoption

Adoption does **not**:

- pass Gate 0, on either base, or change the recorded verdict;
- authorize Gate 1 or any other gate;
- authorize market-data access, a census, a backtest, or strategy design;
- authorize venue contact or measurement;
- approve a real-capital sizing convention or decide T-4;
- mark `R-08` or `R-15` satisfied, or close a blocker;
- resolve `C-4`, `C-6`, `C-7`, or `C-8`;
- authorize paper or live trading;
- create an O-2 decision. A named stage authorization is still required before any research begins.

### 14.4 Rejection or revision

- **Reject:** the protocol and all current restrictions continue unchanged.
- **Revise:** the owner lists the changes; this draft is revised and re-issued with a new hash; the
  O-1 decision then applies to the revised text, not this one.
- **No response:** nothing changes. Silence is not adoption.

### 14.5 Severability and interpretation

1. If a clause is rejected or revised, the remaining clauses stand only if the owner adopts them
   explicitly; the draft is not partially effective by default.
2. No clause may be read to pass Gate 0, to lower a threshold, or to authorize a stage.
3. Where this addendum is silent, the protocol governs.

### 14.6 Version

`1.0.0-draft`. Any edit changes the hash and voids the hash binding in the O-1 packet.

---

## 15. What this draft does not do

It does not adopt itself; it does not sign, ratify, or affirm anything; it does not create an owner
decision; it does not pass Gate 0; it does not authorize O-2, Gate 1, or any research; it does not
change D-01–D-15, A-1–A-4, or any frozen document; it does not access data, contact a venue, measure a
cost, design a strategy, size real capital, or trade. It is a proposal awaiting O-1.
