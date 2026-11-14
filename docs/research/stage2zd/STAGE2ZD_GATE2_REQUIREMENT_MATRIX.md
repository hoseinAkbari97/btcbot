# Stage 2ZD — Gate 2 Requirement Matrix

**Stage:** 2ZD (decision preparation only)
**Date:** 2026-11-14 (UTC)
**Purpose:** reconstruct the exact Gate 2 requirements from the adopted governing text, name the
evidence each requires, and record the current status of each.
**Controlling sources:** `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §5.1–§5.5 and §8.2;
`stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` (§7.2, §10.4);
`stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §5–§6;
`stage2m/OWNER_DECISION_REGISTER.md` D-08…D-14; `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`
§10–§15; `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` §1–§3.
**Status of this document:** it defines requirements and records status. **It treats no row as
satisfied by assumption, authorizes no Gate 2 work, and confers no permission of any kind.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 0. How to read this matrix

Gate 2's requirements are not all in one place. They come from four adopted clusters:

1. **Protocol §5.2 — sixteen required registration inputs.** Each must be present and complete in the
   registration document.
2. **Protocol §5.3 — six pass criteria.** Each must hold for the registration to be valid.
3. **Protocol §5.4 — five artifacts.** Each must exist and be frozen.
4. **Protocol §8.2 plus D-08…D-14 — data separation, statistics, and one-look controls.** These
   constrain *how* the registration's inputs are written.

The status vocabulary is fixed:

| status | meaning |
|---|---|
| `SATISFIED` | the required artifact/value exists, is current, and is verifiably consistent |
| `PARTIAL` | some required element exists, but at least one specific sub-element is missing |
| `BLOCKED` | a required input cannot be produced under current authorizations or owner decisions |
| `UNKNOWN` | the status cannot be determined from the repository, or the value is genuinely unknown |
| `NOT APPLICABLE` | the requirement does not apply to the research-leg Gate 2 as scoped |

Each row also records:

- **needs validation/OOS access?** — would producing the evidence require reading a validation or
  OOS row?
- **needs new owner authorization?** — beyond the (hypothetical) Gate 2 authorization itself.
- **venue / cost / execution / audit dependency** — which downstream dependency it carries.

A Gate 2 authorization is **not** present. Every row is scored as if a Gate 2 stage were
contemplated; scoring does not create the stage.

---

## 1. Protocol §5.2 — the sixteen required inputs

### 1.1 Input-by-input matrix

| # | §5.2 input | required evidence (exact text) | current evidence | status | val/OOS access? | new owner auth? | dependencies |
|---:|---|---|---|---|---|---|---|
| 1 | **Hypothesis** | a clear, falsifiable statement of the economic mechanism | `stage2e_v2/CANDIDATE_B_SPEC.md` §1–§3 and `CANDIDATE_D_SPEC.md` §1–§3 each state a falsifiable directional mechanism; no *single* candidate has been selected as the Gate 2 primary | **PARTIAL** | no | **yes** — candidate/primary selection is an owner decision; D-15 deferred | venue none; cost none; execution none; audit Gate 4 |
| 2 | **Rationale** | why the mechanism should exist, independent of the observed data | both specs give an economic rationale independent of the dataset; the rationale is untested | **SATISFIED** (text exists) | no | no | — |
| 3 | **Universe and data** | instrument, venue, timeframes, development interval, exclusions | instrument `BTCUSDT`, spot, Binance data, dev interval `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` recorded; **venue is unresolved** — data is Binance, intended execution is Nobitex; the validation/OOS internal split is unfrozen | **PARTIAL** | **yes, for §8.2 block hashes** (see §4) | **yes** — venue choice and split interpretation | venue `C-4`; cost `26 bp`; execution `C-6`; audit none |
| 4 | **Entry rules** | signal conditions, timing, look-ahead safeguards | both specs state boolean entry rules and next-open timing; the frozen spec for a selected candidate exists | **PARTIAL** (candidate not selected) | no | **yes** (selection) | venue none; cost none; execution none |
| 5 | **Exit rules** | target, stop, time exit, holding policy | both specs state target, stop, time exit, holding policy | **PARTIAL** (candidate not selected) | no | **yes** (selection) | cost `26 bp` (stop distance); execution none |
| 6 | **Risk rules** | position sizing, max concurrent positions, capital limits | D-02 fixes 15% DD, 1.00R per-trade, CVaR95 0.50R, `$2,500` fixed notional research leg; **B-09** (`$2,500` cap versus tight stops) is open and blocks the sizing rule | **PARTIAL** | no | **yes** — B-09 interpretation is the owner's | venue liquidity `R-05`; cost `cost_R`; execution none |
| 7 | **Eligibility conditions** | regime, liquidity, session, or other filters | D-14 requires all three regimes (volatility, trend, liquidity); **numeric regime definitions are not set** | **PARTIAL** | no | **yes** — numeric regime definitions | venue none; cost none; execution none |
| 8 | **Primary estimand and MME** | the metric and the owner-approved threshold | D-01 fixes `δ_R = 0.10R` net per executed trade and `$250`/year; the estimand is defined | **SATISFIED** | no | no | cost `26 bp` affects net R; execution `p_exec` affects trade count |
| 9 | **Secondary metrics** | frequency, utilization, drawdown, tail, stability, cost sensitivity | the metric list is conceptually fixed by protocol §8.5–§8.6 and D-02; no candidate-specific secondary metric table is frozen | **PARTIAL** | no | no (derivable, but must be written) | cost `26 bp`; execution `p_exec` |
| 10 | **Statistical methods** | estimator, dependence model, error control, multiple-testing policy | D-08 (α 5% two-sided, 80% power, hierarchical), D-09 (cluster-robust + block bootstrap, disagreement→inconclusive), D-11 (one primary hypothesis), D-12 (strict one-look); **numeric dependence parameters are open (B-10)** | **PARTIAL** | no | **yes** — B-10 numeric parameters | venue none; cost none; execution none; audit Gate 4 |
| 11 | **Sample-sufficiency calculation** | `N_ind`, `N_obs`, `required_opportunities`, assumptions, sensitivity | the formula chain exists in `STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §5 (`N_ind ≈ (z+ z)² σ²/δ²`; `N_obs ≈ N_ind × DE`; `required_opportunities ≈ N_obs / p_exec`); **`σ`, `DE`, `p_exec` are all open (B-11)**; the ≈ `785` figure is illustrative only | **BLOCKED** | **yes, if `σ`/`DE` come from a census** | **yes** — census authorization, or pre-registered assumption | venue none; cost none; execution `p_exec`; audit none |
| 12 | **Feasibility criteria** | what opportunity count and capital geometry would justify proceeding | protocol §6.4 gives the interval decision rule; the numeric thresholds depend on row 11 and on capital geometry (`B-09`) | **BLOCKED** (depends on 11) | inherits 11 | inherits 11 | venue liquidity; cost; execution |
| 13 | **Failure criteria** | what evidence would reject the hypothesis | protocol §8.8 gives the rejection conditions; D-12/D-14 add look-integrity and regime conditions; not yet written as a candidate-specific pre-registered list | **PARTIAL** | no | no (writable now) | cost; execution |
| 14 | **Data-access plan** | development, validation, OOS, and the one-look rule | the development boundary is exact (§8.2); the validation/OOS split is **unfrozen**; D-12 fixes one-look and logging; the §8.2-versus-D-12 hashing tension is unresolved | **BLOCKED** | **yes, for block hashes** | **yes** — interpretation decision (see §4) | venue none; cost none; execution none; audit Gate 4 |
| 15 | **Audit plan** | the independent auditor and the scope of Gate 4 | D-13 fixes the standard (separate reviewer + external specialist if feasible); **no reviewer or specialist is identified (R-22, B-05)**; Gate 4 is later | **PARTIAL** | no | **yes** — reviewer identity is the owner's | audit Gate 4 |
| 16 | **Version and hashes** | the frozen specification and code identity | Stage 2ZC established the manifest/hash discipline and Stage 2ZD verifies it; **no Gate 2 registration, config, code version, or hash manifest exists yet** | **BLOCKED** (nothing to hash yet) | no | no (produced by the stage) | all |

### 1.2 Input count summary

| status | count | inputs |
|---|---:|---|
| `SATISFIED` | **2** | #2 rationale, #8 primary estimand/MME |
| `PARTIAL` | **10** | #1, #3, #4, #5, #6, #7, #9, #10, #13, #15 |
| `BLOCKED` | **4** | #11, #12, #14, #16 (and #12 inherits #11) |
| `UNKNOWN` | **0** | — |
| `NOT APPLICABLE` | **0** | — |

No input is `SATISFIED` merely because the governing text supplies a rule; a row is `SATISFIED` only
when the *registration artifact* exists. On that strict reading only #2 and #8 have a complete
artifact today, and even #8's artifact is a frozen owner value rather than a registration section.

---

## 2. Protocol §5.3 — the six pass criteria

Pass criteria are properties of the completed registration. They cannot be evaluated until the
registration exists, so the current status is "not yet evaluable" for most. The table records what
each criterion would demand and whether any *precondition* is already broken.

| # | §5.3 pass criterion | what it demands | current precondition | status |
|---:|---|---|---|---|
| 1 | the registration is complete and internally consistent | all sixteen §5.2 inputs present, no contradictions | four inputs are `BLOCKED`, ten `PARTIAL` | **BLOCKED** |
| 2 | the MME and risk limits match the Gate 0 record | `δ_R = 0.10R`, DD 15%, 1.00R, CVaR95 0.50R, `$2,500`, research-leg only | D-01/D-02 values are fixed and consistent; **B-09 sizing interpretation is open** | **PARTIAL** |
| 3 | the sample-sufficiency calculation is reproducible from its stated assumptions | explicit `σ`, `DE`, `p_exec`; reproducible formula; sensitivity range | **B-11 open**; no census authorized | **BLOCKED** |
| 4 | the failure criteria are stated before the outcome | a pre-registered rejection list | §8.8 exists; candidate-specific list not written; no outcome has been observed | **PARTIAL** |
| 5 | no outcome data has been observed by the analyst | a data-access log showing zero outcome access | Stage 2ZC decoded **0** validation/OOS rows; the analyst has observed no outcome | **SATISFIED** (as of 2026-11-14) |
| 6 | the specification and analysis plan are hashed and frozen | a frozen registration, spec, plan, and manifest | no Gate 2 artifacts exist | **BLOCKED** |

### 2.1 Criterion 5 must be re-established, not assumed

Criterion 5 is satisfied today only because **no outcome has been observed at all**. The moment a
Gate 2 stage computes validation/OOS block hashes, the meaning of "no outcome data has been
observed" depends on the interpretation chosen in §4. A definition of "observed" that treats hashing
as observation would break this criterion unless the hashing is done by a custodian or on
ciphertext. This is the sharpest live risk in the matrix.

---

## 3. Protocol §5.4 — the five required artifacts

| # | §5.4 artifact | exists today? | status | notes |
|---:|---|---|---|---|
| 1 | the frozen registration document | no | **BLOCKED** | depends on §1 inputs |
| 2 | the frozen specification and config | partially — `CANDIDATE_B_CONFIG.json`, `CANDIDATE_D_CONFIG.json` exist but no candidate is selected and no Gate 2 config is frozen | **PARTIAL** | selection is an owner decision |
| 3 | the analysis plan | no Gate 2 plan; `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` is a historical precedent, not this plan | **BLOCKED** | depends on §1 rows 10–14 |
| 4 | the hash manifest | no Gate 2 manifest | **BLOCKED** | produced last |
| 5 | the data-access log showing no outcome access | no Gate 2 log; Stage 2ZC's log shows zero outcome access to date | **PARTIAL** | must be created and must show zero |

---

## 4. Protocol §8.2 and D-12 — the data-separation requirement and its tension

This section is the core readiness finding. It is stated in full here because it determines whether
Gate 2 can be authorized at all.

### 4.1 The exact requirement

| source | text | demand |
|---|---|---|
| protocol §8.2 | "The exact dates and hashes are frozen at Gate 2." | the registration must contain exact validation and OOS **dates** and **hashes** |
| protocol §5.2 #14 | "Data-access plan: development, validation, OOS, and the one-look rule." | the plan must name all three blocks and the one-look rule |
| D-12 §13.1–§13.2 | strict one-look; one look each; access logging required; embargo required; additional looks only as a new stage | no validation/OOS row may be read before its gate |
| addendum §10.4 | "No validation or OOS row may be read before its gate." | same prohibition, adopted |
| protocol §8.3 | embargo/purge separates the blocks; "exact dates and hashes are frozen at Gate 2" (restated) | the split includes an embargo whose numeric length is **B-10** |

### 4.2 The tension

Freezing an exact validation/OOS **block hash** requires streaming that block's bytes. D-12/adopted
§10.4 forbids reading a validation/OOS **row** before its gate. The text does not define whether
hashing is a "read". Four readings exist (Stage 2ZD audit §10.4):

| reading | block hashes at Gate 2 | consistent with §8.2? | consistent with D-12? | residual risk |
|---|---|---|---|---|
| R-a: hash-only contact is not a "read" | **yes** | yes | yes, if "read" = decode/observe | the disclosure must be exact; a hash could in principle leak length, not content |
| R-b: any byte contact is a "read" | **no** | no — §8.2 unmet | yes | Gate 2 cannot satisfy §8.2 without an amendment |
| R-c: custodian computes hashes | **yes, delivered by a third party** | yes | yes, for the analyst | needs a new procedural authorization and a trust boundary; no custodian identified |
| R-d: defer Gate 2 | n/a | n/a | n/a | Path C or D |

### 4.3 The status of this requirement

**`BLOCKED`.** Not because the data are missing, but because the controlling text does not settle
which section governs the timing of the block hash. This is a **governance/interpretation blocker**,
not a data blocker, and it cannot be resolved by the agent. It is the single strongest argument for
Path C over Path A.

---

## 5. D-08…D-14 — the decision-level constraints on Gate 2

| decision | resolved value | Gate 2 consequence | status |
|---|---|---|---|
| **D-08** significance/power | α 5% two-sided, 80% power, hierarchical (primary then secondary) | fixes `z` values in the `N_ind` formula | **SATISFIED** |
| **D-09** dependence | option C — cluster-robust plus block bootstrap; disagreement → inconclusive | fixes the *standard*; **numeric episode/block/embargo parameters open (B-10)** | **PARTIAL** |
| **D-10** power methodology | power methodology adopted; numeric sample pending | fixes the *method*; **`σ`, `DE`, `p_exec` open (B-11)** | **PARTIAL** |
| **D-11** multiple testing | one primary hypothesis per stage; exploratory labelled; OOS confirmation for promotion | forbids testing both B and D in one stage; forces a single-candidate selection | **PARTIAL** (selection pending) |
| **D-12** one-look | strict one-look; one each; logging; embargo; new stage for extra looks | fixes the *policy*; **logistics (who holds the split) open (B-10)** | **PARTIAL** |
| **D-13** audit | B+E — separate reviewer + external specialist if feasible | fixes the *standard*; **reviewer not identified (R-22)** | **PARTIAL** |
| **D-14** representativeness | regime coverage (volatility, trend, liquidity) + later-period confirmation via the single OOS look | fixes the *requirement*; **numeric regime definitions open** | **PARTIAL** |

### 5.1 What Gate 2 does NOT require

For the avoidance of doubt, and to prevent scope creep in any future authorization:

- Gate 2 does **not** require measured venue cost. The `26 bp` proxy is the frozen research-leg
  assumption; D-06's p95 rule cannot be applied until a cost distribution exists, and Gate 2 does not
  create one.
- Gate 2 does **not** require execution evidence, fills, slippage, latency, or order placement.
- Gate 2 does **not** require `C-4` (venue completeness) or `C-6` (execution-measurement route) to be
  resolved, **provided** no execution-feasibility or real-capital claim is made.
- Gate 2 does **not** require Gate 0 to pass. Gate 0 remains **NOT PASSED**; the research-leg track
  proceeds under the adopted addendum with that status intact.
- Gate 2 does **not** require T-4 to be revisited. T-4 remains deferred and blocks only real-capital
  readiness.

---

## 6. Cross-cutting dependency map

| dependency | affects inputs | current state | blocking? |
|---|---|---|---|
| candidate/primary selection | #1, #4, #5, #9, #13 | D-15 deferred; no selection authorized | **yes** |
| venue choice and `C-4` | #3, #6, #7, #12 | Nobitex intended; venue spec incomplete; disclosed under P-5 | only for execution claims |
| cost basis `26 bp` | #5, #8, #9, #11, #13 | frozen assumption; not measured; replacement plan unauthorized | no for Gate 2 |
| execution rate `p_exec` | #11, #12 | **B-11 open**; `B-04` (execution measurement) unresolved | **yes** |
| dependence parameters | #10, #11, #14 | **B-10 open** | **yes** |
| audit/reviewer | #15, criterion 6 | **R-22 `P`**; D-13 standard set, person not | no for authorization; yes for Gate 4 |
| `$2,500` cap interpretation | #6, #12 | **B-09 open** | **yes** for sizing rule |
| validation/OOS hash interpretation | #3, #14, criterion 5 | **unresolved** (§4) | **yes** |

---

## 7. Net Gate 2 status

**Gate 2 is not ready to be executed.** Of the sixteen required inputs, four are `BLOCKED`, ten are
`PARTIAL`, and two are `SATISFIED`. Of the six pass criteria, one is `SATISFIED` (criterion 5, and only
because no outcome exists yet), two are `PARTIAL`, and three are `BLOCKED`. Of the five artifacts, none
is complete.

Four of the blockers are **owner decisions**: candidate selection (D-11/D-15), the `$2,500` sizing
interpretation (B-09), the validation/OOS hash interpretation (§4), and the episode/block/embargo
numbers (B-10). Two are **evidence requirements**: `σ`/`DE` and `p_exec` (B-11/B-04). The rest are
**document production** once the decisions are made.

The matrix therefore supports a decision between:

- **Path B** — a Gate 2 *specification* stage that produces the registration template, the input
  table, and the decision list **without** executing Gate 2 or touching any block;
- **Path C** — resolve the §8.2/D-12 interpretation and the owner decisions first, then authorize a
  Gate 2 that can actually pass.

The scored comparison is in `STAGE2ZD_PATH_COMPARISON_AND_RECOMMENDATION.md`.

---

## 8. Integrity statement

1. Every status in this matrix is derived from a named source section, not from summary memory.
2. No row is marked `SATISFIED` to make Gate 2 look closer than it is.
3. No validation or OOS row was read to produce this matrix.
4. No candidate was selected, no parameter was chosen, and no threshold was changed.
5. This matrix authorizes nothing. Gate 2 remains **NOT AUTHORIZED**.
6. Gate 0 remains **NOT PASSED**; `R-08` `P`; `R-15` `B`; C-4 and C-6 unresolved.
