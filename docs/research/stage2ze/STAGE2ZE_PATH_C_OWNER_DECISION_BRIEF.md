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
