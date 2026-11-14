# Stage 2ZD — Owner Decision Packet

**Stage:** 2ZD (decision preparation only)
**Date:** 2026-11-14 (UTC)
**To:** the project owner
**From:** the research agent
**Status:** **decision preparation. This packet authorizes nothing. It is not a decision. It cannot be
signed by the agent.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 0. How to use this packet

1. Read §1–§4. They state what was found and what is being asked.
2. Pick **one** of the four paths in §5 and record it in the signature block in §9.
3. If you pick Path C, also fill in the sub-decisions in §6. If you leave a sub-decision blank, that
   sub-decision is **not decided** — it is not defaulted, inferred, or treated as consent.
4. **Silence is not authorization.** An empty field, a missing reply, a "continue", a merge of this
   commit, or a general instruction to proceed does **not** select a path, authorize a stage, or
   resolve an interpretation. Only an explicit recorded statement does.
5. This packet does not change any prior decision, verdict, threshold, or status.

---

## 1. What was found

| finding | result |
|---|---|
| Stage 2ZC Gate 1 verdict audited | **confirmed** on its recorded evidence: six §4.3 criteria supported, no substantive contradiction |
| Gate 1 verdict | **PASSED — research leg only** — unchanged, not reopened |
| Gate 2 requirements reconstructed | 16 inputs (§5.2), 6 pass criteria (§5.3), 5 artifacts (§5.4), plus §8.2 and D-08…D-14 |
| Gate 2 inputs `SATISFIED` | **2 of 16** |
| Gate 2 inputs `PARTIAL` | **10 of 16** |
| Gate 2 inputs `BLOCKED` | **4 of 16** |
| Gate 2 pass criteria `SATISFIED` | **1 of 6** (and only because no outcome exists yet) |
| Gate 2 artifacts complete | **0 of 5** |
| Gate 2 readiness | **NOT READY** |
| Validation or OOS rows read by this stage | **0** |
| Census / backtest / simulation run | **0** |
| Gate 0 | **NOT PASSED** — unchanged |
| Real capital | **not authorized** — unchanged |

### 1.1 The six blockers

| id | blocker | class | who resolves |
|---|---|---|---|
| B-1 | no single primary candidate selected (D-11) | owner decision | owner |
| B-2 | `$2,500` cap versus tight stops (B-09) | owner decision | owner |
| B-3 | is hashing a validation/OOS block a prohibited "read"? (§8.2 vs D-12) | owner interpretation | owner |
| B-4 | `σ`, `DE`, `p_exec` unset (B-11) | evidence / owner assumption | owner authorizes the route |
| B-5 | episode/block/embargo numbers and one-look logistics (B-10) | owner decision | owner |
| B-6 | no Gate 2 registration or manifest exists | document production | the future stage |

B-1, B-2, B-3, and B-5 need no data. B-4 needs either a census authorization or an owner-approved
labelled assumption. B-6 needs the other five.

### 1.2 The interpretation finding, stated plainly

Protocol §8.2 says the exact validation and OOS **dates and hashes** are frozen at Gate 2. D-12 and
adopted addendum §10.4 say **no validation or OOS row may be read** before its gate. Computing a block
hash requires streaming that block's bytes. The text does not say whether hashing is a "read". This is
a genuine gap, it belongs to the owner, and it is the strongest reason not to authorize Gate 2 yet.

---

## 2. What this packet is not

This packet is **not**:

- an authorization of Gate 2, a census, a backtest, a measurement, or any data access;
- a ruling on the §8.2/D-12 question;
- a selection of a candidate, a parameter, a threshold, or a cost;
- a change to Gate 0, the Stage 2ZC verdict, `26 bp`, D-01…D-15, or A-1…A-4;
- a reopening of T-4 or a real-capital decision;
- a statement that the owner intends to pause, continue, or accelerate.

---

## 3. Recommended path (agent analysis, not an owner decision)

**Path C — resolve the protocol interpretation and the Gate 2 owner decisions first.**

Why, in one paragraph: Gate 2 cannot be executed today, and four of its five real blockers are
decisions only the owner can make. The one that is also a textual gap — B-3 — must be closed expressly
before any block is hashed, or the one-look protection is either strained or silently amended.
Resolving the decisions first costs no data access, preserves every threshold, is fully reversible
before any outcome, and is the direct precedent of the Stage 2Y→2ZA path that produced the adopted
addendum. It is slower than Path A and more useful than Path B, and it does not trade rigor for speed.

Full scoring: `STAGE2ZD_PATH_COMPARISON_AND_RECOMMENDATION.md` §3 (C 37/40, D 33/40, B 32/40,
A 11/40).

---

## 4. Ready / not ready, in one table

| question | answer |
|---|---|
| Is Gate 2 executable today? | **No** |
| Is a Gate 2 specification preparable? | **Yes** |
| Are the owner decisions ready to be posed? | **Yes** — §5 and §6 |
| Is the sample-sufficiency calculation computable? | **No** (B-4) |
| Is the validation/OOS split nameable? | **No** (B-3) |
| Is the registration freezable? | **No** (B-1, B-2, B-3, B-4, B-5) |
| Has any outcome been observed? | **No** |
| Is Gate 0 passed? | **No** |
| Is real capital authorized? | **No** |

---

## 5. Decision 2ZD-0 — select exactly one path

Record **one** choice. Choosing none leaves the programme where it is, and is **not** a vote for any
default.

| option | label | what it authorizes | what it does not |
|---|---|---|---|
| **A** | Authorize Gate 2 execution now | a Gate 2 stage that attempts to freeze the registration and record a verdict | does not waive the four blocked inputs; would require guesses or an implicit amendment |
| **B** | Prepare a Gate 2 specification only | a template, the 16-input table, artifact skeletons, decision list | no voting, no sample-sufficiency numbers, no split, no Gate 2 verdict, no data access |
| **C** | Resolve the protocol interpretation and owner decisions first | the §8.2/D-12 ruling plus the four non-data Gate 2 decisions, and a Gate 2 specification reflecting them | no census, no data access, no Gate 2 execution, no parameter chosen without an authorized route |
| **D** | Defer | nothing; the programme pauses at the end of Stage 2ZC/2ZD | does not close any blocker; does not authorize anything |

**Owner selection (2ZD-0):** `________________`

| field | value |
|---|---|
| selected path | `________________` |
| date of decision (UTC) | `________________` |
| owner statement (verbatim) | `________________` |
| agent words added | `________________` |
| signature or equivalent | `________________` |

---

## 6. Decision 2ZD-1 … 2ZD-5 — the Path C sub-decisions

Fill these **only if** Path C is selected. Each is independent. Leaving one blank means that
sub-decision is **not decided**.

### 6.1 Decision 2ZD-1 — the §8.2 / D-12 block-hash interpretation (B-3)

**Question fixed:** is computing a SHA-256 over a reserved validation or OOS block a "read" that D-12
forbids, or a permitted hash-only contact?

| option | reading | consequence |
|---|---|---|
| **R-a** | hash-only contact is **not** a "read"; streaming bytes through SHA-256 without decoding is permitted | Gate 2 may compute and record exact block hashes; the contact must be logged; the Stage 2ZC full-file-hash precedent applies |
| **R-b** | any byte contact is a "read" | Gate 2 cannot compute block hashes; §8.2 must be amended or Gate 2 cannot freeze the split |
| **R-c** | a custodian computes the hashes and delivers only the hash values | preserves the analyst's no-look position; requires a custodian role, a trust boundary, and a procedural authorization |
| **R-d** | do not decide now; defer Gate 2 until a reading is adopted | no Gate 2 |

**Owner selection (2ZD-1):** `________________`
**Conditions or qualifications:** `________________`

### 6.2 Decision 2ZD-2 — primary candidate selection (B-1)

**Question fixed:** which single candidate is the Gate 2 primary hypothesis? D-11 permits one primary
per stage and forbids testing more than one.

| option | candidate | note |
|---|---|---|
| **C-B** | Candidate B — volatility expansion + directional continuation + retest | frozen spec `v2.0.0`; 24 historical opportunities over 1,277 days |
| **C-D** | Candidate D — intraday continuation with an HTF volatility budget | frozen spec `v2.0.0`; 34 historical opportunities; design effect 3.93 |
| **C-N** | no selection now; keep both as unselected | Gate 2 cannot name a primary hypothesis |

**Owner selection (2ZD-2):** `________________`
**Conditions or qualifications:** `________________`

> Selecting a candidate here does **not** authorize a census, a backtest, or an outcome measurement.
> It only names the hypothesis a future Gate 2 would register.

### 6.3 Decision 2ZD-3 — `$2,500` cap versus tight stops (B-2 / B-09)

**Question fixed:** when the `$2,500` fixed-notional cap binds a stop distance below `4%`, does `1R`
shrink with the cap, or is the cap exceeded? D-02 forbids exceeding the cap.

| option | rule | consequence |
|---|---|---|
| **S-1** | `R` is defined by the capped notional, so `R` shrinks and the effective risk per trade falls below `$100` | risk stays inside the cap; `0.10R` is worth less than `$10`; the trade count for `$250` rises |
| **S-2** | the cap is treated as a hard skip: trades whose required notional exceeds `$2,500` are not taken | reduces the opportunity set; keeps `1R = $100` |
| **S-3** | defer the sizing rule to a later stage | Gate 2 input #6 stays `PARTIAL`; Gate 2 cannot be frozen |

**Owner selection (2ZD-3):** `________________`
**Conditions or qualifications:** `________________`

### 6.4 Decision 2ZD-4 — dependence and embargo numbers (B-5 / B-10)

**Question fixed:** the numeric parameters D-09/D-12 leave open — episode definition, block length,
embargo length, and who holds the validation split.

| parameter | owner value | notes |
|---|---|---|
| episode definition | `________________` | e.g. cooling-off bars or regime break; must not be fitted to `DE` |
| block length | `________________` | for the block bootstrap; must not be chosen to minimise `DE` |
| embargo length | `________________` | separates blocks; part of the §8.2 split |
| who holds the validation split | `________________` | a person or a custodian procedure |
| when the split may be opened | `________________` | must be after the Gate 2 freeze and at Gate 5 only |

**Owner selection (2ZD-4):** `________________`
**Conditions or qualifications:** `________________`

### 6.5 Decision 2ZD-5 — the `σ`, `DE`, `p_exec` route (B-4 / B-11)

**Question fixed:** how are the three sample-sufficiency inputs obtained? B-11 forbids choosing them
after seeing an outcome or a design effect.

| option | route | consequence |
|---|---|---|
| **E-1** | authorize a **development-block-only census** to estimate `σ` and `DE` | requires a new stage authorization, a dev-only boundary, and a no-outcome rule; `p_exec` still needs B-04 |
| **E-2** | adopt **labelled pre-registered assumptions** with sensitivity ranges, before any outcome | no data access; the assumptions must be disclosed as assumptions, never as estimates |
| **E-3** | hybrid — census for `σ`/`DE`, assumption for `p_exec` until `C-6` is resolved | keeps the registration writable without an execution route; `p_exec` stays an assumption |
| **E-4** | defer the route decision | Gate 2 input #11 stays `BLOCKED` |

**Owner selection (2ZD-5):** `________________`
**Conditions or qualifications:** `________________`

> No option here authorizes validation/OOS access. E-1 and E-3 are development-block only. E-2 and E-3
> label every assumption. None of them selects a value for the owner.

---

## 7. Exact artifacts and hashes

The packet's evidentiary basis is the Stage 2ZD set. Every hash is SHA-256 of the current bytes.

| artifact | bytes | SHA-256 |
|---|---:|---|
| `docs/research/stage2zd/STAGE2ZD_GATE1_EVIDENCE_AUDIT.md` | 33,074 | `7ace928e0ed77dc1d7920466a1b427662470ffe917c63e2781329c5321818174` |
| `docs/research/stage2zd/STAGE2ZD_GATE2_REQUIREMENT_MATRIX.md` | 19,385 | `209c33213ac240192a2796ffa9bc9b55b987717b9bd91b3ec21ad6639bd76241` |
| `docs/research/stage2zd/STAGE2ZD_GATE2_READINESS_ASSESSMENT.md` | 15,419 | `5e264fc4de1784601d6d060110a6dc26e897f197158468a31040f5e25fdab2ce` |
| `docs/research/stage2zd/STAGE2ZD_PATH_COMPARISON_AND_RECOMMENDATION.md` | 12,965 | `2c2d344b18290e58963fcf026733b0f6b04601888461fdf98acd40fea400a132` |
| `docs/research/stage2zd/STAGE2ZD_AUTHORIZATION_BOUNDARY.md` | 8,097 | `1f293a8c27594ec80833379f65a53acd71635907af1be4785637003704ae704e` |
| `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md` | this file | recorded in `FREEZE_MANIFEST.json` |

The Stage 2ZD freeze manifest records each artifact's byte count and hash and carries a canonical
self-hash. The Stage 2ZC verdict this packet audited is
`docs/research/stage2zc/STAGE2ZC_GATE1_VERDICT.md`, SHA-256
`86aa62382fd2ceafddb4802eb094b69e96ffa256515043ac957a72fa76ee2f31`, unchanged.

---

## 8. What stays unauthorized regardless of the selection

Whichever path is chosen, these remain unauthorized unless a **separate** decision says otherwise:

- reading, hashing (except under an adopted R-a/R-c reading), decoding, or summarizing any validation
  or OOS row;
- any census, backtest, simulation, or parameter fit (except E-1/E-3's development-only census, if
  separately authorized);
- measuring cost, spread, depth, fills, slippage, latency, or liquidity;
- contacting a venue or placing any order;
- changing `26 bp`, any D-01…D-15 value, any A-1…A-4 value, or any verdict;
- passing Gate 0;
- revisiting T-4 or sizing real capital;
- paper or live trading.

The full boundary is in `STAGE2ZD_AUTHORIZATION_BOUNDARY.md` §5.

---

## 9. Signature block

**This block is blank by design. Only the owner may complete it. The agent has added no word, value,
date, condition, or signature.**

| field | value |
|---|---|
| I have read this packet | `________________` |
| I select path (2ZD-0) | `________________` |
| If Path C, my sub-decisions (2ZD-1…2ZD-5) | `________________` |
| Conditions or qualifications | `________________` |
| Effective date (UTC) | `________________` |
| Owner statement (verbatim) | `________________` |
| Recorded by | `________________` |

**A blank field is not a decision. A missing reply is not a decision. Silence is not authorization.**

---

## 10. Integrity statement

1. Every hash in §7 was recomputed from the current file bytes.
2. No validation or OOS row was read to produce this packet.
3. No census, backtest, simulation, or parameter fit was run.
4. No candidate was selected, no parameter was chosen, and no threshold was changed.
5. Every owner field is blank. The agent completed none of them.
6. This packet authorizes nothing and passes no gate.
7. Gate 0 remains **NOT PASSED**; Gate 2 remains **NOT AUTHORIZED**; T-4 remains deferred; `R-08` `P`;
   `R-15` `B`; C-4 and C-6 unresolved.
