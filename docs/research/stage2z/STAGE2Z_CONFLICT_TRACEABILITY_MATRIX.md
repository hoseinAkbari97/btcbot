# Stage 2Z — Conflict Traceability Matrix (C-1 to C-9)

**Stage:** 2Z (governance drafting and decision preparation only)
**Purpose:** trace each conflict identified in Stage 2Y to its original source and section, state the
inconsistency, state whether the proposed addendum would resolve it **if the owner adopts it**, and
record the residual ambiguity.
**Status:** analysis only. **No conflict is resolved by this document.** A drafting proposal has no
effect until O-1 is adopted.
**Addendum under review:** `stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md`,
version `1.0.0-draft`, SHA256 `b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc`
**Date:** 2026-11-11

---

## 0. Reading rule

Three words are used precisely:

- **Resolved (conditional)** — if the owner adopts the addendum, the inconsistency no longer has an
  operative effect on the matter described.
- **Partial (conditional)** — adoption removes the operative effect on one base or one question while
  a residual remains.
- **Not resolved** — adoption changes nothing about this conflict; it needs a separate owner decision.

No entry may be read as a claim that the historical record has been corrected. No historical document
is edited by Stage 2Z.

---

## 1. C-1 — Gate 0's own blocker list is satisfied, yet Gate 0 is recorded as not passed

| field | content |
|---|---|
| **Original sources** | `stage2p/GATE0_READINESS_ASSESSMENT.md` §8.1 (the three things needed); same document §9 ("would not pass it even if D-04 were answered tomorrow"); `stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §4 |
| **Inconsistency** | 2P §8.1 named only three blockers — D-04, the `R-17`–`R-20` artifacts, and the `R-21` acknowledgment. All three are now closed (D-04 resolved 2026-11-11; `R-17`–`R-21` all `S`; `R-13` `S`). Gate 0 is nonetheless recorded as not passed, on `R-08 P` and `R-15 B`, neither of which is on that blocker list — and `R-15` says on its face that it blocks only real-capital claims. |
| **Addendum clauses** | §4.2 (per-base applicability), §4.3 (research-leg readiness determination), §4.5 (global verdict unchanged), `P-1`, `P-2`, `P-4` |
| **Resolved if adopted?** | **Conditional yes, for the operative question.** The "not passed" verdict becomes explicitly a real-capital verdict; the research-leg rows are assessed on their own base; a research-leg determination is a different named status. |
| **Residual** | Gate 0 is still recorded **NOT PASSED**, and the addendum does not pass it on either base. An owner who wants Gate 0 itself passed on the research leg is asking for something this addendum deliberately does not do. |
| **Separate owner act?** | No for the representation; yes for any actual research (O-2). |

---

## 2. C-2 — `R-08`'s requirement was strengthened after the Gate 0 criteria were frozen

| field | content |
|---|---|
| **Original sources** | `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 row `R-08`; `stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §6.2; `stage2t/STAGE2T_DECISION_PACKET.md` §3 |
| **Inconsistency** | At 2P, `R-08`'s missing evidence was "the owner's real deployable capital, or an explicit statement that none is committed." From 2R/2T onward it also requires a real-basis per-trade sizing rule, and "T-4c keeps `R-08` **P**." The row therefore means more now than when Gate 0's criteria were frozen. |
| **Addendum clauses** | §5.1, `P-3` |
| **Resolved if adopted?** | **Conditional partial.** The addendum confines `R-08` to the real-capital base and states which reading governs there (the 2R/2T one). It preserves the 2P wording as history. |
| **Residual** | The two wordings still differ; they are not reconciled. For the real-capital base, the later reading governs only because the addendum says so and the owner adopts it. |
| **Separate owner act?** | T-4 remains deferred; the definitional drift can be closed later by a revision if the owner wants one reading formally fixed. |

---

## 3. C-3 — protocol §3.5 bars the evidence T-4 requires

| field | content |
|---|---|
| **Original sources** | `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3.5; `stage2w/STAGE2W_OWNER_DECISION_PACKET.md` §4 (items 1, 4, 5) |
| **Inconsistency** | §3.5 bars hypothesis registration and strategy data access while Gate 0 is incomplete. T-4's evidence needs a validated expectancy (item 1), a tail distribution (item 4), and trade frequency (item 5) — all outputs of Gates 2–5. Gate 0 is held incomplete by `R-08`, which waits on T-4. The loop controls access to its own evidence. |
| **Addendum clauses** | §6.1 (current text stated), §6.2 (`P-1` scoping), §6.3 (why the research leg does not need T-4) |
| **Resolved if adopted?** | **Conditional yes.** The prohibition is scoped to the base whose inputs are incomplete. The loop is broken by rule, not by exception. |
| **Residual** | The scoping takes effect only through a named stage authorization (O-2). Without O-2, no research may start even after adoption. The protocol text of §3.5 is not literally rewritten; the addendum supplies the scoped reading. |
| **Separate owner act?** | **Yes — O-2**, and it must name scope, data, prohibitions, and stop condition. |

---

## 4. C-4 — Gate 1 requires a venue specification but its pass criteria do not test it

| field | content |
|---|---|
| **Original sources** | `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §4.2 (required input) versus §4.3 (pass criteria) |
| **Inconsistency** | The venue specification is a required Gate 1 input, but venue-specification completeness is not among the pass criteria. A Gate 1 could formally pass with the venue specification still `UNKNOWN`. |
| **Addendum clauses** | §7.4, `P-5` |
| **Resolved if adopted?** | **No.** The addendum adds a **disclosure** requirement for a future Gate 1 authorization, not a pass criterion. It deliberately does not change the gate. |
| **Residual** | The ambiguity survives: Gate 1 may still pass with venue facts unknown, provided they are disclosed. Closing that would require changing §4.3, which this addendum does not propose. |
| **Separate owner act?** | Yes — the O-2 Gate 1 authorization should carry the disclosure rule explicitly; a formal §4.3 change would be a separate amendment. |

---

## 5. C-5 — Binance-proxy cost allowed by §4.3 but forbidden as a venue cost by 2P §8

| field | content |
|---|---|
| **Original sources** | `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §4.3; `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §8; `stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §7.3 |
| **Inconsistency** | §4.3 permits cost evidence "explicitly labelled as an assumption with a plan to replace it". 2P §8 forbids "the frozen `26 bp` figure as a venue cost" because it is a Binance proxy, "explicitly not a measurement". The two are reconcilable only if the label is enforced. |
| **Addendum clauses** | §9.2, §9.3 |
| **Resolved if adopted?** | **Conditional partial.** The addendum restates both rules and fixes the permitted label: a research-leg cost assumption with a plan, never a venue cost and never a basis for an execution-feasibility claim. No text changes. |
| **Residual** | Compliance depends on the wording of future Gate 5 and Gate 6 reports. The required reporting sentence in §9.4 is the control, not a new gate. |
| **Separate owner act?** | No. |

---

## 6. C-6 — measured execution is required by T-4 item 2 and placed after Gate 6

| field | content |
|---|---|
| **Original sources** | `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §9.2 and §9.4; `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §3.2 |
| **Inconsistency** | T-4 item 2 asks for measured fee, spread, and slippage distributions. Fee schedules and spread sampling can be obtained without orders, but fills, partial fills, rejections, latency, and slippage require order placement. The protocol places measured execution after Gate 6 ("Advance to paper trading" requires all gates plus separate authorization) and §9.4 states that no decision authorizes a paper or live account. The framework defines no "measurement-only execution" category. |
| **Addendum clauses** | §8.2 (the split), §8.3 item 3 |
| **Resolved if adopted?** | **No.** The addendum records the split and states that the execution half is not authorized. It creates no measurement category. |
| **Residual** | T-4 item 2 remains part documentary/sampling and part execution-dependent. Unless the owner creates a measurement category (O-5), the execution half stays an assumption with a plan under §4.3. |
| **Separate owner act?** | **Yes — O-5**, an explicit owner decision. |

---

## 7. C-7 — `R-17` wording discrepancy (recorded, not a conflict to fix)

| field | content |
|---|---|
| **Original sources** | `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 (content list: D-01, D-02, D-03, D-07, D-08, D-09, D-12) versus `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 row `R-17` ("consolidating D-01…D-07"); recorded in `stage2u/STAGE2U_A1_SIGNED_OWNER_DECISION_RECORD_DRAFT.md` §7 |
| **Inconsistency** | The two requirement texts name different decision lists. The signed A-1 resolved the content by carrying the §4 list in Part A and the remainder in Part A-addendum. |
| **Addendum clauses** | None — deliberately untouched. |
| **Resolved if adopted?** | **No, and none is intended.** The signed instrument's own resolution stands unchanged. |
| **Residual** | The discrepancy remains on the record exactly as documented. Editing it would rewrite a signed artifact. |
| **Separate owner act?** | None. Preserving it is the correct treatment. |

---

## 8. C-8 — `R-08` status evolution `O → P`

| field | content |
|---|---|
| **Original sources** | `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 row `R-08` (`O`); `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §4 (`P`); `stage2r` §6.2; `stage2x/STAGE2X_GOVERNANCE_STATUS_RECORD.md` §5 |
| **Inconsistency** | Not a conflict: the row moved from `O` to `P` when the owner supplied the `$100` figure, leaving only the sizing convention open. It is the visible trace of C-2. |
| **Addendum clauses** | §5.1 |
| **Resolved if adopted?** | **Preserved, not resolved.** The addendum records the evolution as history and does not rewrite the 2P baseline. |
| **Residual** | None beyond C-2's. |
| **Separate owner act?** | None. |

---

## 9. C-9 — the register's blocking marks do not name T-4

| field | content |
|---|---|
| **Original sources** | `stage2m/OWNER_DECISION_REGISTER.md` §1 (D-04 **BLOCKING**; no decision ID for a real-capital per-trade sizing convention); `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3.3; `stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §2 (`R-13` stays `S`) |
| **Inconsistency** | Gate 0 §3.3 tests whether "every decision in the owner register that is marked **blocking** is resolved". D-04 is resolved and `R-13` is `S`. T-4 is a Stage 2T decision attached to D-04, not a register decision — yet it is cited as a Gate 0 blocker through `R-08`. |
| **Addendum clauses** | §5.4 |
| **Resolved if adopted?** | **Conditional yes, as a clarification.** The addendum records that T-4 is not a register blocking decision and affects Gate 0 only through `R-08` on the real-capital base. |
| **Residual** | T-4 remains deferred and `R-08` remains `P` for real capital. The clarification does not decide T-4. |
| **Separate owner act?** | T-4 itself, later (O-7). |

---

## 10. Summary matrix

| conflict | severity | effect if addendum adopted | depends on | residual |
|---|---|---|---|---|
| `C-1` blocker list vs status | material | **resolved (conditional)** — verdict is real-capital-specific; research-leg determination is separate | O-1 | Gate 0 still NOT PASSED |
| `C-2` `R-08` drift | material | **partial (conditional)** — confined to real capital; both wordings preserved | O-1 | wordings not reconciled |
| `C-3` §3.5 loop | material / circular | **resolved (conditional)** — prohibition scoped by base | O-1 **and O-2** | no research without O-2 |
| `C-4` Gate 1 venue spec | minor | **not resolved** — disclosure only | O-1 + O-2 wording | Gate 1 may still pass with unknowns disclosed |
| `C-5` proxy cost | minor | **partial (conditional)** — rule restated, label fixed | O-1 | depends on report wording |
| `C-6` measured execution | material | **not resolved** — split recorded, category not created | **O-5** | execution half stays an assumption |
| `C-7` `R-17` wording | recorded | **preserved** | — | none |
| `C-8` `R-08` `O → P` | recorded | **preserved** | — | none beyond C-2 |
| `C-9` register vs T-4 | observation | **resolved (conditional)** — clarification only | O-1 | T-4 still deferred |

**Count if adopted:** 3 resolved conditionally (C-1, C-3, C-9), 2 partial (C-2, C-5), 2 not resolved
(C-4, C-6), 2 preserved (C-7, C-8). No conflict is resolved by the act of drafting.

---

## 11. What this matrix does not do

- It does not rewrite, correct, or supersede any Stage 2M–2Y document.
- It does not resolve a conflict; it records what adoption **would** do, and what it would not.
- It does not treat the addendum's own text as authority. The authority is the owner's O-1 decision.
- It does not create, close, or alter any blocker, requirement, gate, decision, or threshold.
- It does not authorize research, data access, venue contact, sizing, or trading.
