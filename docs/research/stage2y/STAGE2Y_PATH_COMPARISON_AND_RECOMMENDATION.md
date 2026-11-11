# Stage 2Y — Path Comparison and Recommendation

**Stage:** 2Y (governance audit and decision preparation only)
**Companion:** `STAGE2Y_GOVERNANCE_DEPENDENCY_MAP.md` (the requirement-level analysis and the six
circularity tests); `STAGE2Y_AUTHORIZATION_BOUNDARY.md` (the boundary any next authorization must
respect)
**Status:** recommendation to the owner. **Not an owner decision. Not an authorization. No gate is
passed.**
**Date:** 2026-11-11

---

## 1. The decision this document addresses

The dependency map establishes that the project is in a closed loop:

> Gate 0 is recorded as **not passed** → protocol §3.5 bars hypothesis registration and strategy data
> access → the T-4 evidence items E-1, E-4 and E-5 cannot be produced → T-4 stays deferred → R-08
> stays `P` and R-15 stays `B` → Gate 0 stays recorded as not passed.

The loop cannot be exited by collecting more evidence, because it controls access to the evidence. It
can only be exited by deciding **what Gate 0 is being judged against** — the `$10,000` research leg or
the `$100` real-capital account. That is the question this document puts to the owner.

Constraints on any answer, from the owner's W-F decision of 2026-11-11
(`stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §1, verbatim):

> "I choose W-F — continue deferral of T-4. No real-capital per-trade risk amount or sizing convention
> is approved. Keep R-08 partially satisfied, R-15 blocked, and Gate 0 NOT PASSED. Revisit T-4 only
> after the evidence requirements in the Stage 2W decision packet are met."

Any path that contradicts that statement is not available. That rules out declaring Gate 0 passed.

---

## 2. The four paths

Each path is assessed on the seven criteria set by the owner: (1) preserve owner-approved thresholds
and signed records; (2) do not weaken statistical standards; (3) keep research-reference capital
distinct from deployable capital; (4) never treat a research-leg result as proof of Nobitex execution
feasibility; (5) avoid unnecessary governance stages; (6) do not authorize work whose results cannot
change a future decision; (7) prefer a clear, testable path over indefinite procedural activity.

### Path A — keep the entire project frozen until T-4 can be resolved

**Mechanism.** Do nothing. Wait for the T-4 evidence to appear.

**What actually happens.** It cannot appear. E-1, E-4 and E-5 require a strategy experiment; §3.5 bars
the experiment while Gate 0 is incomplete; Gate 0 is held incomplete by R-08/R-15, which wait on T-4.
The wait is therefore not a wait — it is a permanent stop with an open file.

**Assessment.**

| criterion | result |
|---|---|
| 1. preserves thresholds/records | **pass** — nothing changes |
| 2. no weakened statistics | **pass** — trivially |
| 3. research vs deployable capital | **pass** — trivially |
| 4. no research-as-execution-proof | **pass** — trivially |
| 5. unnecessary stages | **pass** — no stages at all |
| 6. work that can change a decision | **pass** — no work |
| 7. clear, testable path | **fail** — there is no path; the stop is permanent |

**Verdict.** Compliant but non-viable. If the owner intends this, the honest record is "programme
closed pending a scope decision", not "deferred". Calling it a deferral would be a silent default of
the exact kind protocol §3.3 forbids. **Rejected as a recommendation**, but it is the only compliant
path if the owner's intent is that no research of any kind may precede real-capital sizing.

### Path B — authorize a separately governed research-leg strategy-validation stage, leave real capital blocked

**Mechanism.** One owner stage authorization that names the research leg, the gates it may traverse,
its data, its artifacts and its stop condition — and explicitly leaves R-08 `P`, R-15 `B` and Gate 0
not passed.

**Assessment.**

| criterion | result |
|---|---|
| 1. preserves thresholds/records | **pass** — D-01, D-02, D-12 untouched |
| 2. no weakened statistics | **pass** — same gates, same MME, same sufficiency rule |
| 3. research vs deployable capital | **pass** — stage scoped to `$10,000` |
| 4. no research-as-execution-proof | **pass if stated** — must be written into the authorization |
| 5. unnecessary stages | **partial** — adds nothing new, but leaves the contradiction standing |
| 6. decision-relevant | **pass** — produces E-1/E-4/E-5 |
| 7. clear, testable path | **partial** — clear for one stage, unclear for every stage after it |

**Verdict.** Workable, and better than A. Its weakness is structural: §3.5 says no hypothesis may be
registered while Gate 0 is incomplete. A stage authorization that permits one is either (a) an
implicit amendment — an exception created without amending the text — or (b) an invalid authorization.
Either way the governance record becomes ambiguous at exactly the point where it must be auditable:
who authorized the first experiment, and under what rule? Every subsequent stage re-litigates the same
question. **Not recommended**, but it is the correct fallback if the owner will not amend the text.

### Path C — formally separate the research-leg track from the real-capital track by owner addendum

**Mechanism.** A short owner addendum that (i) leaves Gate 0 **NOT PASSED** for the real-capital
objective exactly as W-F requires, (ii) records that the Gate 0 pass criteria are assessed per capital
base, and (iii) defines a separate, explicitly named research-leg determination that does not
constitute Gate 0 passage. The addendum changes no threshold, no gate, no data rule and no decision
value.

**Why this is not a new framework.** The separation already exists in the frozen record:

- `R-07` (research-leg capital, `$10,000`, `1%`, one position, no leverage) is a separate row from
  `R-08` (real capital), and R-07 is `S` (2P §5).
- `R-15` already reads "**S** for the research leg; **B** for any real-capital claim" (2P §5).
- `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 requires the Gate 0 capital artifact to
  contain "**the open real-capital item**" — the artifact is defined to record real capital as open.
- `stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §4 already states that under the research-only option
  R-08 is "satisfied for the research stage and explicitly deferred for any live stage".
- `stage2p/GATE0_READINESS_ASSESSMENT.md` §10 says the objective "is now fully specified for the
  `$10,000` research leg".

The addendum makes explicit a distinction the evidence structure already draws but the failure rule
(§3.5) does not.

**Assessment.**

| criterion | result |
|---|---|
| 1. preserves thresholds/records | **pass** — no D, A, T, or threshold value changes |
| 2. no weakened statistics | **pass** — same `0.10R`, same `α`/power, same D-12 one-look, same embargo |
| 3. research vs deployable capital | **pass** — the addendum's central purpose |
| 4. no research-as-execution-proof | **pass** — stated as a formal boundary, not a caveat |
| 5. unnecessary stages | **pass** — one owner decision replaces an unbounded series of exceptions |
| 6. decision-relevant | **pass** — every gate output feeds T-4 or a real-capital go/no-go |
| 7. clear, testable path | **pass** — Gate 1 → … → Gate 6 with named artifacts and stop conditions |

**Risks and their mitigations.**

| risk | mitigation required in the addendum |
|---|---|
| "research leg" becomes a back door to real-capital work | explicit prohibition list; no real order, no real capital, no sizing, no deployment claim |
| status semantics — "Gate 0 NOT PASSED" is quietly reinterpreted | the addendum states Gate 0 remains **NOT PASSED**; the research-leg determination is a *different named status*, not a Gate 0 pass |
| amendment inflation / re-litigation later | the addendum defines the boundary once, in the same units as R-15's existing `S`/`B` split |
| the research result is over-read as deployment evidence | a required reporting sentence in every Gate 5/6 output (see §6) |

**Verdict.** **Recommended.**

### Path D — abandon the framework and design a new one

**Mechanism.** Discard the protocol, the register and the frozen gate structure; start over.

**Assessment.**

| criterion | result |
|---|---|
| 1. preserves thresholds/records | **fail** — by construction |
| 2. no weakened statistics | **fail in practice** — a new framework written after seeing the historical failures invites threshold-fitting |
| 3. research vs deployable capital | **unknown** — would have to be rebuilt |
| 4. no research-as-execution-proof | **unknown** |
| 5. unnecessary stages | **fail** — total restart |
| 6. decision-relevant | **fail** — the historical failures and their causes would be forgotten |
| 7. clear, testable path | **fail in the near term** |

**Verdict.** Rejected. The framework's problem is one unscoped failure rule, not a defective
statistical design. Discarding validated thresholds to fix a scoping clause would destroy the only
asset the project has: a conservative, fully recorded standard. It would also make the historical
failures un-auditable, which is the one outcome the project has consistently refused.

---

## 3. Comparison at a glance

| criterion | A (freeze) | B (one-off stage) | **C (addendum)** | D (new framework) |
|---|---|---|---|---|
| 1. preserves thresholds and signed records | pass | pass | **pass** | fail |
| 2. statistical standards unchanged | pass | pass | **pass** | fail/unknown |
| 3. research vs deployable capital distinct | pass (vacuously) | pass | **pass** | unknown |
| 4. no research-as-execution-proof | pass (vacuously) | pass if stated | **pass (structural)** | unknown |
| 5. avoids unnecessary stages | pass | partial | **pass** | fail |
| 6. results can change a decision | fail | pass | **pass** | fail |
| 7. clear, testable path | fail | partial | **pass** | fail |
| **breaks the circularity** | **no** | **yes, by exception** | **yes, by rule** | yes, destructively |

---

## 4. Recommendation

**Path C — an owner addendum that separates the research-leg track from the real-capital track, while
Gate 0 remains NOT PASSED for real capital.**

**Why C over B.** B and C permit the same next action. They differ in what the record says afterwards.
Under B, the first research stage rests on an authorization that contradicts §3.5 and is defensible
only as an implicit exception; every later stage inherits the ambiguity. Under C, the rule is written
once, in the same terms the frozen rows already use (`R-07` vs `R-08`, `R-15`'s `S`/`B`), and every
later stage is judged against a stated boundary. Since the framework's entire value is auditability,
the difference is decisive.

**Why C over A.** A is a permanent stop presented as patience. It also fails the owner's own criterion
6: it authorizes no work, so no future decision can change. If the owner's real intent is "no research
until real-capital sizing exists", the correct record is a closure, and A should be chosen explicitly
— not by default.

**Why C over D.** D fixes a one-clause defect by discarding a validated statistical framework and the
audit trail of four failed candidates. That is the largest possible change for the smallest possible
defect.

**Why the research leg is worth authorizing at all.** Not because a positive result is likely — the
recorded arithmetic points the other way (`N_ind ≈ 785` against `12`–`71` opportunities over 1,277
days; `stage2p` §7.3). It is worth authorizing because it can produce a **decisive negative** cheaply
and early: Gate 3 is a census that observes no outcomes, so a frequency stop can be reached without
spending the single validation look or the OOS look. That result would resolve T-4's E-5, inform E-1
and E-6, and tell the owner whether venue measurement is worth funding. A path that can fail fast and
informatively is exactly what criterion 7 asks for.

The scale gap is already quantified and must not be hidden: at `$1`–`$3` order notional the real
account can express only `$0.005`–`$0.30` of planned risk per trade
(`stage2w/STAGE2W_T4_SIZING_ANALYSIS.md` §3.1), so a research-leg result is relevant to the real
account only if the percentage edge survives fixed-cost drag at that size. The research leg can be
asked to report that gap explicitly; it can never close it. That is why the research-leg result is
**necessary but not sufficient** for a real-capital decision, and why criterion 4 is structural rather
than rhetorical.

---

## 5. What the addendum would have to contain (proposed scope, not adopted)

This is a specification for an owner instrument, not the instrument. Nothing here is in force.

1. **Status restatement.** Gate 0 remains **NOT PASSED**. The addendum does not pass it and does not
   record it as passed on any base.
2. **Scoping clause.** The Gate 0 pass criteria (protocol §3.3) are assessed against a named capital
   base. Two bases exist: the `$10,000` research leg (R-07) and the `$100` real-capital account
   (R-08).
3. **Research-leg determination.** A separate, explicitly named status — not called "Gate 0" — records
   that the research-leg inputs are complete by composition: R-01–R-04, R-07, R-09, R-11–R-14, R-16,
   R-17–R-21, with R-15 satisfied for the research leg. It is a determination, not a gate passage.
4. **Failure rule scoping.** Protocol §3.5's prohibition is scoped to the base whose Gate 0 inputs are
   incomplete. An incomplete real-capital context bars real-capital work; it does not bar a
   research-leg experiment whose own inputs are complete.
5. **Invariant list.** D-01 (`0.10R`), D-02 (`15%`, `1.00R`, `0.50R CVaR95`, `$2,500`), D-03, D-07,
   D-08 (`α = 5%`, power `80%`), D-09, D-12 (strict one-look, logging, embargo), D-13, D-14, T-5
   (`$250` on `$100`), the `$30` tolerance, and `$1`–`$3` order notional are restated as unchanged.
6. **Prohibition list.** No real order, no real capital, no paper trading, no live trading, no
   leverage, no sizing convention, no deployment claim, no gate advance without separate
   authorization.
7. **Boundary statement.** A research-leg result is a statement about Binance-data historical evidence
   under a labelled cost assumption. It is never evidence of Nobitex execution feasibility and never a
   real-capital return claim.

**What the addendum must not do:** change any threshold; change any decision value; mark R-08 or R-15
satisfied; close a blocker; reopen D-15 or promote Candidate A; lower the MME; alter the one-look or
embargo rules; or authorize any stage. Stage authorizations remain separate under protocol §2.1.

---

## 6. The boundary the recommendation depends on

| dimension | research leg | real capital |
|---|---|---|
| capital | `$10,000` reference, a research construct | `$100` owner-stated, deployable |
| risk rule | D-02: `1%` fixed-fractional, `1.00R` cap, `15%` drawdown, `CVaR95 0.50R`, `$2,500` notional cap | **none approved** (T-4 deferred) |
| objective | `$250` on `$10,000` = `2.5%/yr`, testable (R-15 S) | `$250` on `$100` = `250%/yr`, **not testable** (R-15 B) |
| data | Binance historical, frozen blocks, one-look and embargo | none; no market data for real capital |
| cost basis | Binance proxy, labelled an assumption with a plan (Gate 1 §4.3) | **UNKNOWN**; requires venue measurement |
| orders | none | none |
| permitted claims | statistical evidence about the frozen hypothesis on historical data | **none** |
| result feeds | T-4 E-1, E-4, E-5, E-6; venue-work justification | a future T-4 decision only |
| gate status | separate determination, **not** Gate 0 passage | Gate 0 **NOT PASSED** |

**Required reporting sentence** in every Gate 5 and Gate 6 output under this path: *"This result is
research-leg evidence on historical Binance data under a labelled cost assumption. It is not evidence
of Nobitex execution feasibility, not a real-capital return, and not a sizing recommendation."*

---

## 7. Owner decisions that remain necessary

The recommendation does **not** decide any of these.

| # | decision | owner act required | why the agent cannot decide it |
|---|---|---|---|
| O-1 | Adopt, reject, or revise the Path C addendum | signed statement with date | it changes a status interpretation the owner set in W-F |
| O-2 | If adopted, authorize a **named** next stage with scope, artifacts, data, prohibitions and stop condition (protocol §2.1) | separate written stage authorization | §2.1 forbids implied authorization |
| O-3 | Whether to authorize venue **documentary** evidence collection (T-4 E-3, 2P `I-3`) | written authorization | external access is the owner's to permit |
| O-4 | Whether to authorize **quote sampling** for spread (part of T-4 E-2) | written authorization | market-data access |
| O-5 | Whether to create a **measurement-only execution** category for fill/slippage (T-4 E-2) or to defer it as an assumption | written decision | the protocol does not define this category (Conflict C-6) |
| O-6 | Appoint the independent reviewer (`I-4`, D-13) before Gate 4 | written appointment + independence statement | protocol §7.3 |
| O-7 | T-4 itself, when E-1…E-6 exist | written decision | the deferred decision |
| O-8 | Reaffirm or restate `$250` on `$100` after the arithmetic (T-5) | written decision | the objective is the owner's |

---

## 8. What this recommendation does not authorize

Adopting Path C would authorize **no work**. It would change what the framework permits; it would not
itself permit anything. The following remain prohibited until separately authorized, and are
prohibited in this stage regardless:

market-data access, download or processing; historical opportunity census; candidate or strategy
design; parameter selection or optimisation; backtesting or simulation; expectancy, return or P&L
calculation; validation or OOS data access; venue research, contact, or measurement; cost or liquidity
measurement; real-capital sizing; paper or live trading; leverage; bot execution; changes to D-01–D-15;
changes to A-1–A-4; Gate 0 passage; progression to any gate.

---

## 9. What would change this recommendation

| trigger | effect |
|---|---|
| Owner states the real-capital objective is the only objective and no research may precede T-4 | **Path A**, recorded explicitly as a closure — the loop is otherwise unbreakable |
| Owner refuses any text amendment but will authorize one research stage | **Path B**, with the exception recorded in the authorization itself |
| New evidence shows a research-leg result could not inform any real-capital decision (e.g. the `$1`–`$3` order range makes the strategy unexpressible regardless of edge) | reconsider **A** or a redesign; authorizing the research leg would fail criterion 6 |
| The recorded arithmetic is later shown to be wrong and the research leg becomes clearly affordable in time and data | the Path C case strengthens; the recommendation is unchanged |
| A material protocol defect beyond scoping is found | stop and re-audit; do not amend around an unknown defect |

---

## 10. Limitations of this analysis

- It is document-based. No data was read, no venue was contacted, no cost was measured, no strategy was
  designed, no backtest or simulation was run, and no expectancy, return or P&L was computed.
- It resolves no conflict it identifies. Conflicts C-1, C-2, C-3 and C-6 are escalated to the owner.
- It does not assert that the research leg will produce a positive result, that Gate 3 will pass, that
  `$250` on `$100` is achievable, that the `$30` tolerance is adequate, or that Nobitex can execute any
  strategy.
- The recommendation is an agent judgement about sequencing, offered under the owner's delegation of
  ordinary analytical decisions. It is not an owner decision and does not bind the owner.
