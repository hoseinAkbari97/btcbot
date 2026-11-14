# Stage 2ZD — Gate 2 Readiness Assessment

**Stage:** 2ZD (decision preparation only)
**Date:** 2026-11-14 (UTC)
**Question:** is the project ready to execute Gate 2 — hypothesis registration — under the adopted
governing text?
**Companion:** `STAGE2ZD_GATE2_REQUIREMENT_MATRIX.md` (the row-level evidence and statuses).
**Status of this document:** assessment only. **It authorizes no Gate 2 work and passes no gate.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 0. Verdict in one paragraph

**Gate 2 is NOT READY to execute.** Of the sixteen required inputs in protocol §5.2, four are
`BLOCKED`, ten are `PARTIAL`, and only two are `SATISFIED`. Of the six pass criteria in §5.3, three are
`BLOCKED`, two are `PARTIAL`, and the only `SATISFIED` criterion — "no outcome data has been observed"
— holds **because no outcome work of any kind has begun**, and it is exactly the criterion most at
risk from the unresolved data-separation question. None of the five §5.4 artifacts exists. Six
distinct items stand between the project and an executable Gate 2, and three of them are owner
decisions that the agent cannot make. The project *is* ready to prepare a Gate 2 **specification** and
to resolve the interpretation question; it is *not* ready to freeze a registration, compute a
sample-sufficiency requirement, or name a validation/OOS split.

---

## 1. Readiness is not one question

A single yes/no hides where the project actually is. This assessment separates four readiness levels.

| level | question | verdict | basis |
|---|---|---|---|
| **L-0** | can Gate 2 be *authorized and executed* today? | **NO** | four blocked inputs, no artifacts, unresolved interpretation |
| **L-1** | can a Gate 2 *specification* (template, input table, decision list) be prepared? | **YES** | documentation only; no data access; no owner decision consumed |
| **L-2** | can the *owner decisions* that Gate 2 needs be posed as a decision packet? | **YES** | this stage does so |
| **L-3** | can the development-block *census* that supplies `σ` and `DE` be authorized? | **NOT YET** | requires a separate census authorization; Gate 3 territory; would need its own boundary |

Only L-1 and L-2 are ready. L-0 and L-3 are not. The owner decision is which of these to authorize
next.

---

## 2. The six blockers, in dependency order

### 2.1 B-1 — candidate / primary-hypothesis selection (owner)

**Requirement:** protocol §5.2 #1 and D-11 (one primary hypothesis per stage; multiple hypotheses not
permitted within a stage).
**State:** `CANDIDATE_B_SPEC.md` and `CANDIDATE_D_SPEC.md` both exist and are frozen at version
`2.0.0`. No candidate has been selected as the Gate 2 primary. D-15 is deferred, and the deferral
explicitly does not authorize activating the candidate it concerns.
**Why it blocks:** a registration that names two primaries violates D-11. A registration that names
none has no hypothesis.
**Who resolves it:** the owner. This stage cannot select.
**Cost to resolve:** one owner decision. No data access.
**Interaction:** the selection determines entry/exit rules, eligibility, secondary metrics, failure
criteria, and the `p_exec` context, so it must precede the rest of the registration.

### 2.2 B-2 — `$2,500` cap versus tight stops (owner)

**Requirement:** protocol §5.2 #6 (sizing rule) and #12 (capital geometry), plus B-09.
**State:** D-02 fixes a `$2,500` fixed notional and `1.00R` per-trade risk. The cap binds whenever the
stop distance is below `4%`; below that line `1R` shrinks in dollars, `0.10R` is worth less than
`$10`, and the trade count needed for `$250` rises (50 trades at a 2% stop, 100 at 1%). The register
records the missing item as an explicit choice: does `R` shrink with the cap, or is the cap exceeded
(which the owner has forbidden)?
**Why it blocks:** the sizing rule is an input, and the feasibility criteria depend on it.
**Who resolves it:** the owner.
**Cost to resolve:** one owner decision. No data access.
**Interaction:** flows directly into `required_opportunities` and the Gate 3 capital/liquidity check.

### 2.3 B-3 — validation/OOS hash interpretation (owner / governance)

**Requirement:** protocol §8.2 ("exact dates and hashes are frozen at Gate 2"), §5.2 #14 (data-access
plan), D-12 (strict one-look; no validation/OOS row read before its gate), addendum §10.4.
**State:** the controlling text does not settle whether computing a block SHA-256 is a prohibited
"read". Four readings are possible (audit §10.4; matrix §4.2): hash-only contact permitted; any byte
contact prohibited; custodian procedure; defer.
**Why it blocks:** Gate 2 must either produce block hashes (R-a/R-c) or amend §8.2 (R-b), and R-d
means no Gate 2. Every branch needs a governance decision.
**Who resolves it:** the owner, on the agent's analysis.
**Cost to resolve:** one owner decision. **No data access at the moment of decision.**
**Interaction:** decides whether §5.3 criterion 5 survives Gate 2, and whether a custodian role must
be created.

### 2.4 B-4 — `σ`, `DE`, `p_exec` (evidence / owner)

**Requirement:** protocol §5.2 #11–#12; B-11.
**State:** the formula chain is fixed
(`N_ind ≈ (z_{1-α/2} + z_{1-β})² σ² / δ²`; `N_obs ≈ N_ind × DE`; `required_opportunities ≈ N_obs /
p_exec`). With `δ = 0.10R`, α = 5% two-sided, power 80%, and `σ = 1R`, `N_ind ≈ 785`. But `σ`, `DE`,
and `p_exec` are all unset. B-11 names the routes: `σ`/`DE` from an authorized census **or** a
documented pre-registered assumption; `p_exec` from B-04.
**Why it blocks:** the sample-sufficiency calculation is not reproducible without them, so §5.3
criterion 3 fails.
**Who resolves it:** evidence for `σ`/`DE` (census or owner-approved assumption); `p_exec` needs a
measurement route that does not exist (`C-6` unresolved).
**Cost to resolve:** **a census authorization and development-block processing**, or an owner-approved
assumption set. This is the most expensive blocker and the one most exposed to contamination risk.
**Interaction:** `p_exec < 1` pushes required opportunities above the naive 25 executed trades/year;
a low `σ` or a small `DE` makes the requirement small and must be resisted as a shortcut (B-11
prohibited shortcuts).

### 2.5 B-5 — dependence and embargo numbers (owner)

**Requirement:** protocol §5.2 #10 and #14; D-09 (cluster-robust + block bootstrap); D-12 (embargo
required); B-10.
**State:** the *standards* are resolved; the *numbers* are not: episode definition, block length,
embargo length, and the one-look logistics (who holds the validation split, when it may be opened).
**Why it blocks:** the statistical-methods input and the data-access plan both need the numbers, and
the embargo length is part of the §8.2 split.
**Who resolves it:** the owner.
**Cost to resolve:** one owner decision, but the numbers should be chosen on methodological grounds,
not fitted to a design effect (B-10 prohibits selecting a block length that minimises `DE`).
**Interaction:** feeds `DE` in B-4 and the split in B-3.

### 2.6 B-6 — consolidated Gate 2 registration and hash manifest (document production)

**Requirement:** protocol §5.4 all five artifacts; §10.2 manifest discipline.
**State:** nothing exists. Stage 2ZC established the manifest *pattern* (canonical self-hash over
sorted-key compact JSON, SHA-256 per file, byte counts); Stage 2ZD verifies that pattern still holds
across 2Y/2Z/2ZA/2ZB/2ZC. But no Gate 2 registration, plan, or manifest is written.
**Why it blocks:** it is the deliverable.
**Who resolves it:** the Gate 2 stage itself, once B-1…B-5 are resolved.
**Cost to resolve:** document production, not data access.
**Interaction:** none upward; it consumes the other five.

---

## 3. What is *not* a Gate 2 blocker

To prevent scope creep in any authorization, and because each of these has been argued before:

| item | why it does not block a research-leg Gate 2 |
|---|---|
| **Gate 0 not passed** | the adopted addendum's research-leg track proceeds with Gate 0 `NOT PASSED`; Gate 2 is not a Gate 0 pass and does not require one |
| **T-4 deferred** | T-4 blocks real-capital readiness only; the research-leg registration can be written without a real-capital sizing convention |
| **`26 bp` not measured** | Gate 2 requires a labelled assumption, not a measurement; D-06's p95 rule applies only when a cost distribution exists |
| **`C-4` venue completeness** | `P-5` disclosure is the adopted control; unresolved items are disclosed, not required to be resolved, for a research-leg Gate 2 |
| **`C-6` execution-measurement route** | no execution evidence is required at Gate 2; the absence blocks later execution claims, not the registration |
| **`R-05` / `R-10` `P`** | these are Gate 1 venue/liquidity and measured-cost items; they remain `P` and do not enter the Gate 2 input list |
| **`R-22` reviewer not identified** | Gate 4 is later; #15 needs a *plan* naming the standard and the scope, and D-13 supplies the standard; the person is a Gate 4 precondition |
| **No independent auditor yet** | same as above |

The one borderline item is **`p_exec`**: it is used in the Gate 2 sample-sufficiency calculation, and
its only honest source is an execution measurement that `C-6` does not authorize. That is why B-4 is a
blocker and not merely a dependency — Gate 2 can use a *pre-registered assumption* for `p_exec`, but
the assumption must be labelled and sensitivity-tested, and the owner must accept it.

---

## 4. The interpretation findings that Gate 2 inherits

Stage 2ZC disclosed three strict readings that would reverse Gate 1. Stage 2ZD confirms them and adds
the Gate 2 consequence.

### 4.1 Gate 1's strict readings are real but do not undo its result

| strict reading | effect if adopted | Gate 2 relevance |
|---|---|---|
| the validation/OOS sub-ranges are required at Gate 1 | Gate 1 would be `NOT PASSED` | **high** — the same tension recurs at Gate 2 in sharper form (B-3) |
| measured cost is required at Gate 1 | Gate 1 would be `NOT PASSED` | **low** — Gate 2 does not require measured cost |
| venue completeness is an implicit pass criterion | Gate 1 would be `NOT PASSED` | **low for research leg; high for execution** |

Stage 2ZD does not reopen Gate 1. It records that the first reading is the one that carries forward.

### 4.2 Gate 2's own interpretation finding

Freezing exact validation/OOS **dates and hashes** at Gate 2 (§8.2) while forbidding any validation/OOS
**row** read before its gate (D-12/§10.4) is only coherent if "read" means "decode or observe a row
value". Under that reading, hashing is permitted, and the Stage 2ZC full-file-hash precedent is the
template. Under the stricter reading, §8.2 cannot be satisfied without an amendment. **This is a
genuine textual gap and is the primary reason Gate 2 should not be authorized until it is closed.**

---

## 5. The contamination-risk assessment

Gate 2's whole purpose is to freeze the hypothesis and plan **before** any outcome is observed. The
readiness question therefore has a contamination dimension, not only a completeness dimension.

| contamination vector | current exposure | severity |
|---|---|---|
| the analyst has already seen development-block outcomes | **no** — Stage 2ZC ran data-quality checks only, computed no signal, indicator, return, or P&L | low |
| the analyst has seen validation/OOS outcomes | **no** — `0` rows decoded | low (today) |
| the analyst could see then choose parameters to fit | **yes, if a census is authorized before the plan is frozen** | **high** |
| the analyst could choose `σ`/`DE` after seeing the design effect | **yes, under B-11's prohibited shortcut** | **high** |
| the analyst could choose a block length that minimises `DE` | **yes, under B-10's prohibited shortcut** | **high** |
| the analyst could open the split "just to check the pipeline" | **yes, under B-10's prohibited shortcut** | **high** |
| hashing the validation/OOS blocks could be argued to violate one-look | **unresolved** | **high** |

**Conclusion.** The completeness blockers (B-1, B-2, B-6) are inconvenient but safe: they cost time.
The contamination blockers (B-3, B-4, B-5) are the dangerous ones: executed in the wrong order, they
would permanently destroy the confirmatory status of the experiment. **The order in which these are
resolved matters more than the speed with which any of them is resolved.**

---

## 6. Readiness of each §5.4 artifact

| artifact | could be produced now? | what is missing |
|---|---|---|
| frozen registration document | **no** | B-1…B-5 |
| frozen specification and config | **partially** | candidate selection; config exists for B and D but the selected one must be frozen |
| analysis plan | **no** | B-3, B-4, B-5 |
| hash manifest | **no** | the artifacts it hashes do not exist |
| data-access log | **yes, in skeleton** | it can state "zero outcome access to date"; it cannot state blocks until B-3 is closed |

---

## 7. Overall readiness verdict

| verdict element | result |
|---|---|
| **Gate 2 executable today?** | **NO** |
| **Gate 2 specification preparable?** | **YES** |
| **Owner decisions ready to be posed?** | **YES** (this stage poses them) |
| **Sample-sufficiency computable?** | **NO** (B-4) |
| **Data split nameable?** | **NO** (B-3) |
| **Registration freezable?** | **NO** (B-1, B-2, B-3, B-4, B-5) |
| **Contamination currently present?** | **NO**, but the resolution order is the risk |
| **Gate 0 passed?** | **NO** — unchanged |
| **Real capital authorized?** | **NO** — unchanged |

**Research-leg readiness determination:** Gate 0 research-leg *inputs* remain complete per Stage 2ZC.
That is a different statement from Gate 2 readiness. Gate 2 is **not ready**.

---

## 8. What would change this verdict

The verdict flips to "ready to authorize" only when **all** of the following are true:

1. the owner has selected a single primary candidate (B-1);
2. the owner has fixed the `$2,500`-cap sizing interpretation (B-2);
3. the owner has adopted a reading of the §8.2/D-12 hash question, or created a custodian role (B-3);
4. `σ`, `DE`, and `p_exec` are either computed from an authorized development-only census or fixed as
   labelled pre-registered assumptions with sensitivity ranges (B-4);
5. the episode/block/embargo numbers and one-look logistics are fixed (B-5);
6. the five artifacts are drafted and hashable (B-6).

Items 1, 2, 3, and 5 are owner decisions. Item 4 requires either a census authorization or an
assumption decision. Item 6 is mechanical once 1–5 exist. **No item requires validation/OOS access.**
That is the important structural fact: a complete Gate 2 registration is producible **without ever
touching the confirmatory blocks**, which is why the correct path preserves the one-look protection
rather than straining it.

---

## 9. Integrity statement

1. No validation or OOS row was read to produce this assessment.
2. No census, backtest, simulation, or parameter fit was run.
3. No candidate was selected, no parameter was chosen, and no threshold was changed.
4. Every status traces to a named source section.
5. This assessment authorizes nothing. Gate 2 remains **NOT AUTHORIZED**.
6. Gate 0 remains **NOT PASSED**; T-4 remains deferred; `R-08` `P`; `R-15` `B`; C-4 and C-6
   unresolved.
