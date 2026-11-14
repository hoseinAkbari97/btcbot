# Stage 2ZD — Path Comparison and Recommendation

**Stage:** 2ZD (decision preparation only)
**Date:** 2026-11-14 (UTC)
**Question:** of four possible next moves, which one should the owner authorize?
**Companions:** `STAGE2ZD_GATE2_REQUIREMENT_MATRIX.md`, `STAGE2ZD_GATE2_READINESS_ASSESSMENT.md`.
**Status:** recommendation to the owner. **Not an owner decision. Not an authorization.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 0. Summary

**Recommendation: Path C — resolve the protocol interpretation and the Gate 2 owner decisions first.**
It is the only path that closes the §8.2/D-12 hash gap *before* any parameter is chosen or any block is
touched, and it is the direct successor to the Stage 2Y→2ZA precedent that produced the adopted
addendum. **Path B is the correct follow-on** once C is resolved: a Gate 2 specification stage that
writes the registration template and the input table without executing Gate 2. **Path A fails** because
five of six Gate 2 pass criteria cannot be satisfied today and authorizing it would force guesses or an
implicit amendment. **Path D is legitimate but non-productive**; it is viable only if the owner intends
to pause the programme, and this stage does not assume that.

---

## 1. The four paths, stated precisely

Each path is a distinct next authorization. None of them is a Gate 2 pass, and none changes Gate 0.

### Path A — authorize Gate 2 execution now

**Mechanism.** One owner authorization naming Gate 2 and instructing the agent to produce the frozen
hypothesis registration, the analysis plan, the sample-sufficiency calculation, the data-access plan,
and the hash manifest, then to record a Gate 2 pass/fail.

**What actually happens.** Gate 2 cannot be completed. The candidate is not selected (B-1), the sizing
interpretation is open (B-2), the block-hash reading is unresolved (B-3), `σ`/`DE`/`p_exec` are unset
(B-4), and the dependence/embargo numbers are unset (B-5). The agent would have to either (i) guess the
numbers and freeze a registration that violates D-11/B-09/B-10/B-11, or (ii) ask the owner every
question mid-stage, which is Path C with extra steps and a false start recorded as a Gate 2 attempt.

### Path B — prepare a Gate 2 specification only

**Mechanism.** One owner authorization to produce the Gate 2 *template*: the sixteen-input table, the
artifact skeletons, the decision list, and the candidate-agnostic registration structure. **No Gate 2
verdict, no frozen registration, no census, no sample-sufficiency numbers, no validation/OOS access.**

**What actually happens.** The agent produces a reusable specification document. It cannot fill the
split, the numbers, or the primary hypothesis, because those are owner decisions or evidence. The
specification would be complete in structure and incomplete in every blocking cell — which is honest,
but it leaves the interpretation gap open and can be mistaken for progress toward a Gate 2 pass.

### Path C — resolve the protocol interpretation first

**Mechanism.** One owner-facing decision stage (this stage's packet is its instrument) that resolves:
(1) the §8.2-versus-D-12 block-hash reading; and (2) the Gate 2 owner decisions that do not require
data — candidate selection, the `$2,500`-cap interpretation, and the dependence/embargo numbers. **No
data access. No Gate 2 execution.** Its output is a set of recorded owner decisions that make a
Gate 2 specification writable.

**What actually happens.** The owner answers a bounded, pre-analysed set of questions. The
interpretation gap closes expressly rather than by implication. A subsequent Gate 2 specification
(Path B) becomes writable, and the only remaining blocker is the evidence for `σ`/`DE`/`p_exec`, which
needs its own census authorization decision.

### Path D — defer

**Mechanism.** No new authorization. The programme pauses at the end of Stage 2ZC/2ZD.

**What actually happens.** Nothing changes. Gate 0 stays `NOT PASSED`, Gate 2 stays unauthorized, T-4
stays deferred. This is compliant and reversible but produces no decision. It is the correct choice
**only** if the owner's intent is to stop, and Stage 2ZD does not read the owner's commissioning of this
stage as evidence of that intent — nor as evidence against it.

---

## 2. Scoring rubric

Scores are 1–5, where **5 is best** on every dimension. For *contamination risk*, 5 means **lowest**
risk. The rubric is stated so the owner can disagree with a score without disputing the structure.

| dimension | what a 5 means |
|---|---|
| **Protocol compliance** | every action maps to a named section; no implicit amendment |
| **Statistical integrity** | D-08/D-09/D-10/D-11/D-12 preserved exactly; no parameter chosen post-outcome |
| **Contamination risk** (5 = lowest) | no contact with confirmatory blocks; no opportunity to fit |
| **Decision usefulness** | produces an artifact that materially advances a real decision |
| **Resources** (5 = least) | smallest data, time, and review cost |
| **Governance complexity** (5 = simplest) | fewest new stages, roles, and trust boundaries |
| **Reversibility** (5 = most reversible) | can be undone by a later owner decision without permanent loss |
| **Consistency with owner decisions** | agrees with D-01…D-15, O-1, O-2A, and the Stage 2X W-F record |

---

## 3. Scored comparison

| dimension | A — authorize Gate 2 | B — spec only | C — resolve interpretation | D — defer |
|---|---:|---:|---:|---:|
| Protocol compliance | **1** | 4 | **5** | 5 |
| Statistical integrity | **1** | 4 | **5** | 5 |
| Contamination risk (5 = low) | **1** | 5 | **5** | 5 |
| Decision usefulness | 2 | 3 | **5** | 1 |
| Resources (5 = least) | 2 | 4 | **4** | 5 |
| Governance complexity (5 = simple) | 2 | **4** | 3 | 5 |
| Reversibility | **1** | 5 | 5 | 5 |
| Consistency with owner decisions | **1** | 3 | **5** | 2 |
| **total (max 40)** | **11** | **32** | **37** | **33** |

### 3.1 Why Path A scores low

- **Protocol compliance 1.** §5.2 has four `BLOCKED` inputs; §5.3 has three `BLOCKED` criteria; §8.2
  cannot be met without choosing a reading that has not been adopted. Authorizing A would either
  produce an invalid registration or force an implicit amendment — the exact failure Stage 2Y
  identified and the addendum was written to prevent.
- **Statistical integrity 1.** `σ`, `DE`, `p_exec`, and the dependence/embargo numbers would have to be
  chosen under deadline, which is precisely the post-outcome fitting that D-09/D-10/D-12 forbid.
- **Contamination risk 1.** With the block-hash reading unresolved, the stage would either hash the
  confirmatory blocks under a disputed interpretation or skip hashing and violate §8.2.
- **Reversibility 1.** A frozen registration that is later found invalid is not a draft; the
  pre-registration record would carry an invalid artifact forever.
- **Consistency 1.** It cannot be reconciled with D-11, D-12, B-09, B-10, or B-11.

### 3.2 Why Path B scores well but not best

- It is safe: documentation only, no data access, fully reversible.
- But it does not resolve the interpretation gap, and its central cells stay empty. It also carries a
  presentation risk: a "Gate 2 specification" can be mistaken for a Gate 2 that is nearly done, when
  the blocking work is all still ahead.
- **Consistency 3**, because it neither advances nor contradicts the owner's decisions; it sidesteps
  them.

### 3.3 Why Path C scores highest

- It is the only path that closes the §8.2/D-12 gap **expressly** and before any data contact.
- It converts four owner-decision blockers into recorded decisions in one bounded stage.
- It preserves every threshold and every one-look protection.
- It is reversible: an interpretation decision can be superseded by a later owner decision **before**
  any outcome, which is exactly the change-control window §10.3 allows.
- It follows the precedent: Stage 2Y recommended Path C, the owner adopted the addendum as O-1, and
  Stage 2ZA recorded it. Repeating the pattern is consistent, not circular, because the subject is a
  different gap.
- **Its one weakness is governance complexity (3)**: it asks the owner to decide a hard textual
  question. That is unavoidable — the question exists whether or not it is posed, and leaving it
  unposed is what Path A would do implicitly.

### 3.4 Why Path D is not recommended

Path D's total (33) is inflated by compliance-by-inaction: doing nothing is trivially compliant,
trivially contamination-free, and trivially reversible. It scores 1 on the only dimension that matters
for a live programme — **decision usefulness** — and 2 on consistency, because the Stage 2X W-F
deferral was specifically about T-4 and real-capital sizing, not about the research-leg track that
O-2A advanced on 2026-11-14. Path D is the honest record **if** the owner intends to pause, and this
document does not decide that for the owner. It is not recommended as a default.

---

## 4. Sensitivity of the ranking

The ranking should not depend on one contested score. Two perturbations:

| perturbation | effect on ranking |
|---|---|
| treat the §8.2/D-12 gap as **not** blocking (adopt reading R-a by assumption) | C's protocol-compliance advantage shrinks; B rises. A still fails on B-1, B-2, B-4, B-5. **C ≥ B > D > A** still holds unless *all* owner decisions are also assumed |
| treat Path D as excluded by owner intent | C > B > A |
| weight resources heavily | D > B > C > A — but this rewards doing nothing, which is the pathology Stage 2Y rejected |
| weight decision usefulness heavily | C > B > A > D |

**The ranking is stable for A at the bottom and C at the top** across every weighting except one that
rewards inactivity. That is the robustness test this comparison is meant to pass.

---

## 5. What Path C would and would not authorize

If the owner selects Path C, the authorization must state the following, and nothing more.

### 5.1 Would authorize

1. Record the owner's decision on the §8.2/D-12 block-hash reading (R-a, R-b, R-c, or R-d).
2. Record the owner's selection of a single primary candidate for a future Gate 2 (B-1).
3. Record the owner's `$2,500`-cap interpretation (B-2).
4. Record the owner's episode/block/embargo numbers and one-look logistics (B-5).
5. Produce a **Gate 2 specification** (the Path B artifact) reflecting those decisions.
6. Pose — but **not** decide — the `σ`/`DE`/`p_exec` question as a separate census-or-assumption
   decision.

### 5.2 Would not authorize

- executing Gate 2, freezing a registration, or recording a Gate 2 verdict;
- any census, backtest, simulation, or parameter fit;
- reading, hashing, decoding, or summarizing any validation or OOS row;
- measuring cost, spread, depth, fills, slippage, latency, or liquidity;
- contacting a venue, calling an API, or placing an order;
- selecting `σ`, `DE`, or `p_exec` by any route other than an authorized census or an owner-approved
  labelled assumption;
- changing `26 bp`, any D-01…D-15 value, any A-1…A-4 value, or any prior verdict;
- passing Gate 0, revisiting T-4, or authorizing real capital.

---

## 6. Recommendation

**Path C.** Concretely:

1. **Adopt Path C** as the next stage: a bounded owner-decision stage that resolves the §8.2/D-12
   interpretation and records the three non-data Gate 2 decisions (candidate, cap interpretation,
   dependence/embargo numbers).
2. **Authorize the Gate 2 specification (Path B work) as a permitted output of C**, not as a separate
   stage — so the decisions are immediately expressed in a concrete artifact rather than left as
   abstract answers.
3. **Pose the `σ`/`DE`/`p_exec` question separately**, because its honest answer is a census
   authorization or an owner-approved assumption, and neither should be bundled into the
   interpretation decision.
4. **Do not authorize Path A.** It cannot satisfy §5.2 or §5.3 today, and authorizing it would trade
   rigor for the appearance of progress.
5. **Do not default to Path D.** It is available and legitimate, but it must be chosen, not assumed.

The recommendation does not choose speed over rigor. It chooses **order** over speed: resolve the
definitions before the parameters, the parameters before the registration, and the registration before
any outcome. That is the sequence the protocol was written to enforce.

---

## 7. Integrity statement

1. No validation or OOS row was read to produce this comparison.
2. No census, backtest, simulation, or parameter fit was run.
3. No candidate was selected, no parameter was chosen, and no threshold was changed.
4. Every score is justified in the text and is the agent's analysis, not an owner decision.
5. This document authorizes nothing. Gate 2 remains **NOT AUTHORIZED**.
6. Gate 0 remains **NOT PASSED**; T-4 deferred; `R-08` `P`; `R-15` `B`; C-4 and C-6 unresolved.
