# Stage 2ZE — Path C Owner Decision Briefing

**Stage:** 2ZE (decision preparation only)
**Date:** 2026-11-14 (UTC)
**To:** the project owner
**From:** the research agent
**Status:** **briefing. It authorizes nothing, selects nothing, and records no owner decision.**

**Source instrument:** `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`,
14,986 bytes, SHA-256 `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`.

**Recommended path in that packet:** **C** — Stage 2ZD scored C 37/40, D 33/40, B 32/40, A 11/40.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 1. Verification performed before briefing

| item | value | result |
|---|---|---|
| branch | `main` | as expected |
| HEAD | `b9d809c2af0af41c8b131eaade4193ceb4a2c18b` | as expected |
| `origin/main` | `b9d809c2af0af41c8b131eaade4193ceb4a2c18b` | equals HEAD |
| worktree | clean before this file was created | no pending change |
| Stage 2ZD packet bytes | 14,986 | matches the recorded byte count |
| Stage 2ZD packet SHA-256 | `042f0497…e8e42` | **matches** the supplied hash |
| Stage 2ZD freeze manifest | self-hash `b902597e…d58c` | recomputes |
| Stage 2ZD deliverable hashes | all six | recompute |
| Stage 2ZC package | unchanged since `c452b01` | no diff |
| validation/OOS rows read by this stage | **0** | none |

The packet was read in full, together with the protocol sections it cites (§4.2, §4.3, §5.2, §8.2,
§8.3, §15), the addendum (§7.4, §8, §10.4), D-08…D-15, the blocker register (B-09, B-10, B-11), and
the Stage 2ZD requirement matrix and readiness assessment.

---

## 2. The decisions, exactly as the packet poses them

The packet asks for **six** recorded decisions and leaves a **seventh question** outside them.

| id | packet section | question, as the packet states it | options |
|---|---|---|---|
| **2ZD-0** | §5 | which path is selected | `A`, `B`, `C`, `D` |
| **2ZD-1** | §6.1 | "is computing a SHA-256 over a reserved validation or OOS block a 'read' that D-12 forbids, or a permitted hash-only contact?" | `R-a`, `R-b`, `R-c`, `R-d` |
| **2ZD-2** | §6.2 | "which single candidate is the Gate 2 primary hypothesis?" | `C-B`, `C-D`, `C-N` |
| **2ZD-3** | §6.3 | when the `$2,500` cap binds a stop distance below `4%`, "does `1R` shrink with the cap, or is the cap exceeded?" | `S-1`, `S-2`, `S-3` |
| **2ZD-4** | §6.4 | the numeric parameters D-09/D-12 leave open: episode definition, block length, embargo length, who holds the validation split, when it may be opened | owner values |
| **2ZD-5** | §6.5 | "how are the three sample-sufficiency inputs obtained?" (`σ`, `DE`, `p_exec`) | `E-1`…`E-4` |
| **Q-1** | not in §6 | whether measured venue cost is required before Gate 2 — Stage 2ZD's interpretation issue I-2 | no packet option; confirmation only |

Each remains **undecided**. A blank field is not a decision; the packet's §0 rule is that silence,
"continue", or accepting this commit selects nothing.

---

## 3. Decision by decision

### 3.1 2ZD-0 — which path is selected

**What is being decided.** Which of four next moves the programme takes. Nothing else on this page
takes effect until this is recorded.

**Why it is necessary.** Gate 2 cannot be executed today: Stage 2ZD found two inputs `SATISFIED` of
sixteen, four `BLOCKED`, ten `PARTIAL`, no §5.4 artifact complete, and a textual gap it cannot close
itself. Without a selection, the programme simply stops at the end of Stage 2ZD.

| option | exact meaning in the packet | authorizes | restricts |
|---|---|---|---|
| **A** | Authorize Gate 2 execution now | a Gate 2 stage that attempts to freeze the registration and record a verdict | "does not waive the four blocked inputs"; would force guesses or an implicit amendment |
| **B** | Prepare a Gate 2 specification only | a template, the 16-input table, artifact skeletons, decision list | no voting, no sample-sufficiency numbers, no split, no Gate 2 verdict, no data access |
| **C** | Resolve the protocol interpretation and owner decisions first | the §8.2/D-12 ruling plus the four non-data Gate 2 decisions, and a Gate 2 specification reflecting them | no census, no data access, no Gate 2 execution, no parameter chosen without an authorized route |
| **D** | Defer | nothing; the programme pauses | closes no blocker; authorizes nothing |

**Recommendation in the packet.** Path C, with Path B as its permitted output and the `σ`/`DE`/`p_exec`
route posed separately.

**What no option does.** No option passes Gate 0, authorizes real capital, revisits T-4, or changes any
frozen value. Option A does not make the blocked inputs exist.

### 3.2 2ZD-1 — the §8.2 / D-12 block-hash interpretation

**What is being decided.** Whether computing a SHA-256 over a reserved validation or OOS block is a
forbidden "read", or a permitted hash-only contact.

**What the adopted text says explicitly** — quoted, not paraphrased:

| source | text | what it settles |
|---|---|---|
| protocol §8.2 | "The exact dates and hashes are frozen at Gate 2." | block hashes must be fixed **at Gate 2** |
| protocol §8.2 | "An embargo or purge period separates them so that overlapping holding periods do not leak information across the boundary." | the split needs an embargo |
| protocol §5.2 #14 | "**Data-access plan:** development, validation, OOS, and the one-look rule." | the plan must name all three blocks |
| protocol §15 | "reading, decoding, or summarizing validation or OOS rows outside an authorized Gate 5 stage" (prohibited) | the prohibition is written about **rows** |
| D-12 (strict one-look) | one validation look, one OOS look, access logged, embargo required, extra looks only as a new stage | no row may be read before its gate |
| addendum §10.4 | "No validation or OOS row may be read before its gate." | same, restated |

**What the text does not settle.** It never defines "read". Every clause above speaks of *rows*. None
addresses streaming a block's bytes through a hash function without decoding any row. That is the gap —
not a missing artifact, and not a data problem.

**The four readings, labelled as readings rather than text.** None of these is adopted. `R-a` through
`R-d` are the packet's options; the right-hand columns are consequences, not rulings.

| option | reading | §8.2 satisfiable? | enables Gate 2? | cost or residual risk |
|---|---|---|---|---|
| **R-a** | hash-only contact is not a "read"; hashing without decoding is permitted | yes, block hashes can be recorded | yes, with the contact logged | the log must be exact; a hash reveals length, not content |
| **R-b** | any byte contact is a "read" | **no** — §8.2 cannot be met as written | only after an amendment | requires amending §8.2, which the protocol permits only through its own change control |
| **R-c** | a custodian computes the hashes and delivers only hash values | yes | yes, for the analyst | needs a custodian role, a trust boundary, and a procedural authorization; no custodian is identified |
| **R-d** | do not decide now; defer Gate 2 | n/a | no | no Gate 2 at all |

**Precedent, not authority.** Stage 2ZC computed full-file SHA-256 values that streamed bytes past
`2024-07-01T00:00:00Z`, disclosed it in its access log §3.4, and decoded no row. The Stage 2ZD audit
accepted that disclosure. That is a precedent for `R-a`; it is not a ruling, and it does not bind the
owner.

**Why this cannot be left implicit.** Under `R-b` Gate 2 cannot produce the artifact §8.2 demands; under
`R-a` it can. Either way the position must be stated **before** the hash is computed, or the one-look
protection is either strained or amended by silence.

**Recommendation in the packet.** None. Stage 2ZD records the four readings and leaves the choice to the
owner; it notes only that `R-a` is the reading most consistent with §8.2 and with the 2ZC precedent.

### 3.3 2ZD-2 — which candidate becomes the Gate 2 primary hypothesis

**What is being decided.** Which single frozen candidate a future Gate 2 registers.

**Why it is necessary.** D-11 permits one primary hypothesis per stage and forbids testing more than one.
A registration naming two primaries violates D-11; one naming none has no hypothesis. Entry, exit,
eligibility, secondary metrics, failure criteria, and the `p_exec` context all follow from this choice.

| option | candidate | recorded facts |
|---|---|---|
| **C-B** | Candidate B — volatility expansion + directional continuation + retest | frozen spec `v2.0.0`; 24 non-overlapping opportunities over 1,277 days; design effect 1.69 |
| **C-D** | Candidate D — intraday continuation with an HTF volatility budget | frozen spec `v2.0.0`; 34 non-overlapping opportunities; design effect 3.93 |
| **C-N** | no selection now; both stay unselected | Gate 2 cannot name a primary hypothesis |

**What the option does not do.** The packet states: selecting a candidate "does **not** authorize a
census, a backtest, or an outcome measurement. It only names the hypothesis a future Gate 2 would
register." The historical censuses already recorded both as feasibility failures on opportunity count;
those verdicts stand and are not reopened by a selection.

**Recommendation in the packet.** None. Stage 2ZD does not choose between B and D.

### 3.4 2ZD-3 — the `$2,500` notional cap when the stop is tight

**What is being decided.** When the frozen `$2,500` fixed-notional cap binds a stop distance below `4%`,
whether `1R` shrinks with the cap, or the cap is exceeded.

**Why it is necessary.** D-02 fixes a `$2,500` research-leg entry-notional cap and a `1.00R` per-trade
limit together. Below a `4%` stop the two bind each other: the cap holds only if `R` shrinks, so `1R`
falls below `$100`, `0.10R` falls below `$10`, and the trade count needed for `$250` rises. Tight stops
also raise `cost_R`, because the frozen cost formula divides by the stop distance. Gate 2 input #6 (risk
rules) cannot be written without the answer.

| option | exact meaning in the packet | consequence |
|---|---|---|
| **S-1** | `R` is defined by the capped notional, so `R` shrinks and effective risk per trade falls below `$100` | risk stays inside the cap; `0.10R` is worth less than `$10`; the trade count for `$250` rises |
| **S-2** | the cap is a hard skip: trades whose required notional exceeds `$2,500` are not taken | reduces the opportunity set; keeps `1R = $100` |
| **S-3** | defer the sizing rule to a later stage | Gate 2 input #6 stays `PARTIAL`; Gate 2 cannot be frozen |

**What it does not do.** It changes no D-02 value, selects no real-capital sizing, and does not decide
T-4. It fixes a research-leg rule only.

**Recommendation in the packet.** None. The blocker register records the prohibited shortcut — quietly
scaling the cap with the stop distance to preserve `$100` of risk — and does not choose between S-1 and
S-2.

### 3.5 2ZD-4 — dependence, block, embargo, and custody numbers

**What is being decided.** Five values the *standards* fix but the *numbers* do not:

| parameter | what it controls | recorded constraint |
|---|---|---|
| episode definition | what counts as one dependent episode for clustered errors | must not be fitted to `DE` |
| block length | the block bootstrap's resampling unit | must not be chosen to minimise `DE` |
| embargo length | the gap between development, validation, and OOS | part of the §8.2 split |
| who holds the validation split | custody of the reserved data | a person or a custodian procedure |
| when the split may be opened | the one-look timing | after the Gate 2 freeze, at Gate 5 only |

**Why it is necessary.** D-09 adopted option C (cluster-robust errors plus block bootstrap,
disagreement ⇒ inconclusive) and D-12 adopted strict one-look with logging and an embargo. Both are
standards without parameters; B-10 records the gap. Gate 2 inputs #10 and #14 need the values, and the
embargo length is part of the split §8.2 requires.

**What it does not do.** It authorizes no look at any block, opens nothing, and does not decide `σ`, `DE`,
or `p_exec` — those are 2ZD-5.

**Recommendation in the packet.** None, beyond the two prohibitions the blocker register already records:
no parameter chosen after seeing outcomes, and no block length selected because it minimises `DE`.

### 3.6 2ZD-5 — how `σ`, `DE`, and `p_exec` are obtained

**What is being decided.** The route by which the three sample-sufficiency inputs are produced, not their
values. The formula chain is already fixed:

```
N_ind ≈ (z_{1-α/2} + z_{1-β})² σ² / δ²      N_obs ≈ N_ind × DE      required_opportunities ≈ N_obs / p_exec
```

With `δ = 0.10R`, `σ = 1R`, α 5% two-sided, and 80% power, `N_ind ≈ 785`. That is arithmetic on stated
assumptions, not a requirement, and not a forecast.

**Why it is necessary.** §5.3 criterion 3 asks that the calculation be reproducible from its stated
assumptions. B-11 records that `σ`, `DE`, and `p_exec` are unset, and forbids choosing them after seeing an
outcome or a design effect. Without a route, Gate 2 input #11 stays `BLOCKED`.

| option | exact meaning in the packet | consequence |
|---|---|---|
| **E-1** | authorize a development-block-only census to estimate `σ` and `DE` | needs a new stage authorization, a dev-only boundary, and a no-outcome rule; `p_exec` still needs B-04 |
| **E-2** | adopt labelled pre-registered assumptions with sensitivity ranges, before any outcome | no data access; assumptions must be disclosed as assumptions, never as estimates |
| **E-3** | hybrid — census for `σ`/`DE`, assumption for `p_exec` until `C-6` is resolved | keeps the registration writable without an execution route; `p_exec` stays an assumption |
| **E-4** | defer the route decision | Gate 2 input #11 stays `BLOCKED` |

**What no option does.** No option here reads validation/OOS data. E-1 and E-3 are development-block only.
None selects a value for the owner. Choosing E-1 or E-3 **requires a separate census authorization**; the
route decision is not itself that authorization.

**Recommendation in the packet.** None. Stage 2ZD poses the question and notes that the answer is either a
census authorization or an owner-approved assumption.

---

## 4. The separate measured-cost question (Q-1)

This is **not** one of the six packet decisions. Stage 2ZD listed it as interpretation issue I-2 and
recorded `owner_decision_required = false`.

**What the text explicitly says.** §4.3: cost evidence is "either measured or explicitly labelled as an
assumption with a plan to replace it". §4.2 input 5 allows a "documented plan" to collect it. Two branches
are written into the protocol; there is no ambiguity about their existence.

**What was taken.** Stage 2ZC took the second branch: `26 bp` is labelled a Binance spot proxy in the frozen
specifications, a dated replacement plan (R-0…R-5) was added, and no measurement is claimed. Its verdict §6.2
records that a strict reading requiring measurement at Gate 1 would reverse the Gate 1 result.

**Why it does not block Gate 2.** §5.2 and §5.3 ask for a primary estimand, statistical methods, and a
reproducible sufficiency calculation. Neither asks for a cost measurement. D-06's p95 conservative-cost rule
can only apply once a cost *distribution* exists, and Gate 2 does not create one.

**What stays fixed.** `26 bp` is unchanged, remains a proxy, and may never be described as a Nobitex cost or
as execution evidence. Replacing it requires the R-4 plan under a new authorization; measuring spread, depth,
fees, or slippage is not authorized now.

**What the owner may record.** Either (i) a confirmation that the labelled assumption is the permitted
research-leg basis for Gate 2 and that no cost, execution, or real-capital claim may cite it; or (ii) an
instruction that measurement must precede Gate 2 — which is an O-3/O-4-type authorization, outside Path C,
and would delay Gate 2.

---

## 5. Which decisions do what

The distinction matters: resolving an interpretation changes what a future stage **may** do; authorizing a
stage permits work **now**.

| decision | kind | effect if recorded | work it authorizes by itself |
|---|---|---|---|
| **2ZD-0** = `C` | authorization | opens the Path C stage: record decisions and produce a Gate 2 specification | the Path C stage, within its stated scope |
| **2ZD-0** = `A` | authorization | opens a Gate 2 attempt | a Gate 2 stage that cannot pass on today's evidence |
| **2ZD-0** = `B` | authorization | opens a specification-only stage | a template and decision list, no verdict |
| **2ZD-0** = `D` | deferral | nothing changes | nothing |
| **2ZD-1** | interpretation | fixes whether a future Gate 2 may hash reserved blocks | **none** — it sets the rule, not the work |
| **2ZD-2** | selection | names the Gate 2 primary hypothesis | **none** — no census, no backtest, no outcome |
| **2ZD-3** | rule choice | fixes the research-leg sizing rule | **none** — document-level only |
| **2ZD-4** | parameter choice | fixes dependence, embargo, and custody values | **none**; `R-c`-style custody would need its own procedural authorization |
| **2ZD-5** | route choice | fixes how `σ`/`DE`/`p_exec` will be obtained | **none**; `E-1`/`E-3` need a separate census authorization |
| **Q-1** | confirmation | confirms the cost assumption is the permitted basis, or orders measurement first | **none**; measurement would need its own authorization |

**Reading of this table.** Only 2ZD-0 grants anything. The other five are preconditions that make a future
Gate 2 writable; none of them starts Gate 2, and none of them touches market data.

---

## 6. Copy-ready owner response template

Everything below is the owner's to complete. The agent has filled none of it. A blank field is an
undecided item, not a default.

```
STAGE 2ZE — OWNER RESPONSE

Instrument:        docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md
Instrument SHA-256: 042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42
Date (UTC):        ____________________
Owner statement (verbatim):
"______________________________________________________________________________"

2ZD-0  path selected:                 [ ] A   [ ] B   [ ] C   [ ] D

   -- complete the following only if 2ZD-0 = C; each is independent --
2ZD-1  block-hash reading:            [ ] R-a  [ ] R-b  [ ] R-c  [ ] R-d
2ZD-2  primary candidate:             [ ] C-B  [ ] C-D  [ ] C-N
2ZD-3  notional-cap rule:             [ ] S-1  [ ] S-2  [ ] S-3
2ZD-4  episode definition:            ____________________
       block length:                  ____________________
       embargo length:                ____________________
       who holds the validation split:____________________
       when it may be opened:         ____________________
2ZD-5  sample-input route:            [ ] E-1  [ ] E-2  [ ] E-3  [ ] E-4

Q-1    measured cost (optional):
       [ ] confirm the labelled 26 bp assumption is the permitted Gate 2 basis
       [ ] measurement must precede Gate 2 (this is an O-3/O-4-type authorization)
       [ ] no statement

Scope of this decision:               _________________________________________________
Conditions or qualifications:         _________________________________________________
Decisions intentionally left open:    _________________________________________________
Signature or equivalent:              ____________________
Recorded by:                          ____________________
```

**How to read it back.** Only 2ZD-0 selects a path. Only 2ZD-0 = `C` makes 2ZD-1…2ZD-5 meaningful. `Q-1` is
optional and changes nothing on its own. An unfilled line is recorded as *not decided*, and cannot be filled
later by the agent, by inference, or by a later general instruction to proceed.
