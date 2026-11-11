# Stage 2Y — Governance Dependency Map

**Stage:** 2Y (governance audit and decision preparation only)
**Question:** does the existing framework permit collection of the research-leg evidence needed for
T-4 reconsideration while T-4 remains deferred and Gate 0 remains **NOT PASSED**?
**Status:** audit complete. **No gate is passed, no authorization is created, no evidence is
collected.**
**Authorizes:** nothing.

**Evidence labels used throughout:** **Verified fact** (stated in the cited repository document),
**Interpretation** (reasoned conclusion from cited text), **Conflict** (two authoritative statements
that cannot both be satisfied as written), **Open question** (cannot be resolved from the repository).

**Source hierarchy applied.** Where documents disagree, this map treats
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` as the governing text, `stage2m/OWNER_DECISION_REGISTER.md`
as the decision authority, and `stage2p/GATE0_READINESS_ASSESSMENT.md` plus
`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` as the frozen Gate 0 basis. Stages 2Q–2X are read
as records of owner decisions and of how the Gate 0 rows evolved. A later stage is not treated as
silently overriding the protocol; where it does depart, that is recorded in §5.

---

## 1. The components, defined from their own sources

### 1.1 T-4 and its six evidence items

**Verified fact** (`stage2t/STAGE2T_DECISION_PACKET.md` §3; `stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §3):
T-4 is the real-capital per-trade sizing convention. The owner selected **T-4c / W-F, defer**, on
2026-11-11. No dollar risk, no risk percentage, and no sizing formula is approved.

**Verified fact** (`stage2w/STAGE2W_OWNER_DECISION_PACKET.md` §4, "Evidence gate before any numeric
convention is approved"): T-4 is to be revisited only after all six items exist:

| # | item (verbatim from the 2W packet §4) | what class of evidence it is |
|---|---|---|
| E-1 | "a validated net-of-cost expectancy from an authorized experiment" | research outcome |
| E-2 | "measured fee, spread, and slippage distributions for the intended venue and order sizes" | venue measurement / documentary |
| E-3 | "verified minimum order/notional, lot step, tick size, and stop-order support" | documentary venue fact |
| E-4 | "an assessed tail-loss and gap/stop-failure distribution" | research outcome / model |
| E-5 | "the strategy's actual trade frequency" | research census |
| E-6 | "a restated annual objective reconciled with the above, or an explicit decision that the objective is aspirational and not a sizing input" | owner decision |

**Verified fact** (`stage2x/STAGE2X_T4_OWNER_DECISION_RECORD.md` §3 item 3): meeting the six items
"does not itself approve a convention; it only makes the decision appropriate to take up again."

### 1.2 The Gate 0 requirements

**Verified fact** (`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3.2): Gate 0 requires six
owner-approved inputs — minimum meaningful effect; risk limits; **capital and position-sizing
context**; primary and secondary estimands; execution venue and cost-evidence standard; error-control
objective and dependence-treatment standard.

**Verified fact** (§3.3): Gate 0 passes only when every **blocking** register decision is resolved,
no unresolved decision is silently defaulted, the objective is written in a form a future experiment
can test, and the risk limits are in the same units as the primary metric.

**Verified fact** (§3.4): four artifacts — signed owner decision record, economic objective memo,
risk policy statement, capital and execution context statement.

**Verified fact** (§3.5, verbatim): "If Gate 0 is incomplete, no hypothesis may be registered and no
data may be accessed for a strategy experiment. A research stage may still review documentation or
design methodology, but it may not count signals or outcomes."

**Verified fact** (`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §5): Gate 0 requires `I-1`,
`I-6`, and `A-1`–`A-4`.

**Verified fact** (`stage2v/STAGE2V_A1_OWNER_AFFIRMATION_RECORD.md`;
`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §2): the signed `A-1` was affirmed on
2026-11-11 and `R-17` moved `P → S`. Every `R-17`–`R-21` row is therefore `S` in the current record.

### 1.3 The two checklist rows that are said to hold Gate 0 open

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §5, row R-08, verbatim missing evidence):
"the owner's real deployable capital, or an explicit statement that none is committed."
Row R-08 is classified `O` there, with the note "no real-capital figure exists anywhere in the
repository".

**Verified fact** (same table, row R-15, verbatim): "**S** for the research leg; **B** for any
real-capital claim", missing evidence "real-capital context", dependency D-04.

**Verified fact** (`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §4): Gate 0 does not
pass because (1) `R-08` is `P` — the real-capital per-trade sizing convention is deferred (T-4);
(2) `R-15` is `B` — the real-capital objective is therefore not in testable form. The report adds,
verbatim: "Gate 0 would pass on the real-capital objective only after a separately authorized T-4
decision. It cannot pass on the research leg alone while the owner's stated objective is the
real-capital one."

---

## 2. Requirement-by-requirement dependency table

Columns: **prereq** = must exist before the dependent item; **downstream** = is an output of it;
**under T-4 deferral** = can the requirement be satisfied while T-4 stays deferred; **owner** =
needs an owner decision; **data/venue** = needs market data or external venue evidence.

| ID | requirement | source and section | type | under T-4 deferral | owner | data/venue |
|---|---|---|---|---|---|---|
| **T-4** | real-capital per-trade sizing convention | 2T §3; 2X §3 | downstream of E-1…E-6 | **is the deferred item** | yes | no (its evidence needs data) |
| **E-1** | validated net-of-cost expectancy | 2W §4 | downstream of Gates 0–5 | **no** | stage authorization | yes (historical data) |
| **E-2** | measured fee/spread/slippage at the intended venue and size | 2W §4; 2P §3.2 | mixed | **partly** — see §4.D | authorization to collect | yes (venue measurement) |
| **E-3** | verified min order/notional, lot step, tick, stop support | 2W §4; 2P §3.1 | independent | **yes** (documentary) | authorization to collect | venue documents/account screens |
| **E-4** | tail-loss and gap/stop-failure distribution | 2W §4; protocol §8.6 | downstream of Gates 3–5 | **no** | stage authorization | yes |
| **E-5** | actual trade frequency | 2W §4; protocol §6.2 | downstream of Gates 0–3 | **no** | stage authorization | yes (census, no outcomes) |
| **E-6** | restated annual objective | 2W §4 | owner-only | **yes** (but depends on E-1…E-5) | yes | no |
| **R-08** | real-capital capital and sizing context | 2P §5; 2R §6.2; 2T §3 | Gate 0 row | **no** (stays `P` by 2T) | yes | no |
| **R-15** | objective in testable form | 2P §5 | Gate 0 row | **yes for research leg; no for real capital** | yes | no |
| **R-13** | every blocking decision resolved | 2P §5; 2U report §4 | Gate 0 row | **yes** — D-04 resolved, its derivative is T-4 | yes (done) | no |
| **Gate 0** | economic objective | protocol §3 | prerequisite to Gates 1–5 | **only if scoped** | yes | no |
| **Gate 1** | data and venue validity | protocol §4 | prereq to Gate 2 | **yes, conditionally** — cost may be an assumption with a plan (§4.3) | D-05/D-06 authorizations | yes |
| **Gate 2** | hypothesis registration | protocol §5 | prereq to Gate 3 | **no** — §3.5 bars registration | stage authorization | development data only |
| **Gate 3** | feasibility census | protocol §6 | prereq to Gate 4 | **no** | stage authorization | yes (counts, no outcomes) |
| **Gate 4** | independent implementation audit | protocol §7 | prereq to Gate 5 | **no** | I-4 appointment | no |
| **Gate 5** | controlled performance evaluation | protocol §8 | prereq to Gate 6 | **no** | stage authorization | validation/OOS |
| **Gate 6** | final research decision | protocol §9 | terminal | **no** | separates paper trading | no |
| **Research-leg strategy validation** | Gates 0→5 on `$10,000` under D-01/D-02 | 2P §4–§5; protocol §3–§8 | composite | **procedurally no; substantively yes** | yes | yes |
| **Venue execution feasibility** | does Nobitex accept and fill the strategy's orders | `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 (R-05, R-10); `stage2p/OPEN_BLOCKER_REGISTER.md` `B-02`–`B-04` | Gate 1, Gate 3 | **documentary half yes; measured half no** | I-2, I-3 | yes |
| **Independent audit** | arms-length implementation verification | protocol §7.3; 2P §3.4 | Gate 4 | **yes in principle** (needs a named reviewer) | I-4 | no |

**Verified fact** (`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §5, "Interpretation"):
"nothing above Gate 0 can be started honestly, because Gate 1's evidence standard presumes an
objective and a capital base that Gate 0 has not finished stating."

---

## 3. The dependency graph as the documents actually define it

```
                         OWNER DECISIONS (D-01, D-02, D-03, D-07, T-5)
                                        │
                            ┌───────────┴────────────┐
                            │                        │
                   RESEARCH LEG ($10,000)     REAL CAPITAL ($100)
                   R-07 S, R-15 S             R-08 P, R-15 B
                            │                        │
                       GATE 0  ◄─────────────────────┘
                  (§3.2 inputs, §3.3 criteria, §3.4 artifacts)
                            │
              ┌─────────────┴──────────────┐
              │  §3.5: if incomplete,      │  §3.5: documentation and
              │  no hypothesis registered  │  methodology review only
              │  and no data accessed      │
              ▼                            ▼
          GATE 1  data + venue validity   (methodology, no counts)
              │   cost may be an assumption with a plan (§4.3)
              ▼
          GATE 2  frozen registration, N_ind/N_obs/required_opportunities,
              │   no outcome observed (§5.3)
              ▼
          GATE 3  feasibility census, no outcomes (§6.2–§6.4)
              │
              ▼
          GATE 4  independent audit (§7)
              │
              ▼
          GATE 5  performance, one validation look, one OOS look (§8.2)
              │
              ▼
          GATE 6  research decision (§9.2)
              │
              │  "Advance to paper trading" requires all gates pass
              │  AND a separate owner authorization (§9.2, §9.4)
              ▼
        MEASURED EXECUTION (paper / live) — a Gate 6 outcome, not an input
```

**T-4 evidence edges, overlaid:**

```
  E-5 frequency ────────────── Gate 3
  E-1 expectancy ───────────── Gate 5
  E-4 tails / gaps ─────────── Gate 3 + Gate 5 (§8.6)
  E-2 measured costs ───────── Gate 1 (assumption + plan)  +  measured execution (post-Gate 6)
  E-3 venue constraints ────── documentary evidence, independent of every gate
  E-6 objective ────────────── owner
                               │
                               ▼
                             T-4  ──►  R-08 S  ──►  R-15 (real) S  ──►  real-capital readiness
```

**Interpretation:** the graph has **one** edge that closes a loop and **one** edge that is missing.
The loop is `Gate 0 → §3.5 → no research → E-1/E-4/E-5 unobtainable → T-4 cannot be decided →
R-08 stays P → Gate 0 stays unpassed`. The missing edge is a defined route from "measured execution"
back into the evidence set: the protocol places measured execution *after* Gate 6, but E-2 asks for it
*before* T-4.

---

## 4. Circularity hypotheses A–F, tested independently

### A. Research-leg independence

**Question:** can a strategy be designed, pre-registered, tested and independently audited on the
`$10,000` framework, under D-01/D-02, without approving real-capital sizing?

**Evidence.** The framework already carries a complete, separate research-leg specification:
`R-07` S (`$10,000`, `1%` fixed-fractional, one position, no leverage; 2P §5);
`R-02`–`R-04` S (15% drawdown of prior peak, `1.00R` per-trade, `CVaR95 = 0.50R`);
`R-15` S for the research leg; `R-16` S (units compatible with the `R`-denominated primary metric);
`R-13` S (all blocking decisions resolved — 2V §2, 2U §4). `stage2p/GATE0_READINESS_ASSESSMENT.md` §10
states that "The economic objective is now fully specified for the `$10,000` research leg". None of
these references a real-capital sizing rule.

**Verdict — substantively confirmed, procedurally refuted.** A research-leg experiment needs no
real-capital sizing rule: the risk rule is `1%` of `$10,000`, fixed and frozen. But `§3.5` is
unconditional, and the current status of Gate 0 is recorded as "not passed", so the experiment
cannot be registered today. The dependency on T-4 is **not intrinsic to the research leg**; it is
created by treating the real-capital rows as Gate 0 blockers.

### B. Gate 0 interpretation

**Question:** does Gate 0 prohibit all research until every Gate 0 requirement is satisfied, or does
it distinguish research-leg readiness from real-capital readiness?

**Evidence for a distinction.** The register separates the two bases at the decision level: D-04 has
a research-leg branch and a real-capital branch; `R-07` and `R-08` are separate rows; `R-15` carries
an explicit `S`/`B` split; `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 requires the
capital and execution context artifact to contain "the open real-capital item" — i.e. the Gate 0
artifact is *defined* to record real capital as open, not to close it. In
`stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §4, the research-only option states that `R-08`
"is answered *as a scope statement*
rather than as a figure: the requirement is satisfied for the research stage and explicitly deferred
for any live stage."

**Evidence against a distinction.** Protocol §3.2 requires an "owner-approved capital and
position-sizing context" without qualification; §3.5 attaches a blanket prohibition to an incomplete
Gate 0; and `stage2v` §4 explicitly refuses to pass Gate 0 on the research leg "while the owner's
stated objective is the real-capital one."

**Verdict — the framework distinguishes readiness in its evidence structure but not in its failure
rule.** That asymmetry is the defect. Gate 0's *inputs* are scoped by base; Gate 0's *failure
handling* is not. Therefore a single global "not passed" status necessarily blocks the research leg
even when the research-leg inputs are complete.

### C. The T-4 evidence requirement

**Question:** do the six items require evidence that only real-capital trading can generate?

**Evidence.** Item by item (see §1.1): **E-3** is documentary (venue specification). **E-5** is a
Gate 3 census that "observes no outcomes" (protocol §6.2) and needs no capital. **E-6** is an owner
statement. **E-1** and **E-4** need a research experiment, but a research experiment on historical
data consumes no real capital. **E-2** is the only genuinely execution-dependent item: fee schedules
are documentary, spread can be sampled from quotes, but slippage, latency, fill rates and rejections
require orders (2P §3.2 requires "decision-to-fill measurements").

**Verdict — partly confirmed, and the confirmed part is narrow and already accommodated.** Four of
the six items are obtainable without any real-capital trading. The two that need an experiment are
obtainable without real capital. Only measured fill/slippage needs execution — and the protocol
already handles that case: Gate 1 §4.3 requires cost evidence "either measured or explicitly labelled
as an assumption with a plan to replace it". So the six-item gate does **not** require real-capital
trading; it requires an authorized research experiment plus documentary venue evidence plus one
explicitly deferred measurement.

### D. R-15

**Question:** is R-15 a blocker to research-leg validation, or specifically to a real-capital claim?

**Evidence.** `stage2p` §5 row R-15 says, verbatim, "**S** for the research leg; **B** for any
real-capital claim". `stage2p` §5 counts it in the "satisfied for the research leg and blocked for
any real-capital claim" category. `stage2v` §4 treats it as a Gate 0 blocker without qualifying the
scope.

**Verdict — refuted as a research-leg blocker.** By its own text R-15 blocks only a real-capital
claim. Treating it as a global blocker is an extension of the row beyond its definition. That
extension is what `stage2v` does, and it is the second half of the deadlock.

### E. Execution feasibility

**Question:** can Nobitex's constraints be established independently of live trading?

**Evidence.** `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §3.1 lists nine capabilities, each
requiring "a dated yes/no plus the supporting venue document or account screen": account existence,
identity tier, API credentials, deposit, withdrawal, order types, instrument specification (symbol,
minimum notional, lot step, price tick), rate limits and maintenance, regional restriction. **Verified
fact** there: "none of these nine exists in the repository in any form." §3.2 adds the cost
distribution, and its acceptance standard requires observed fees, spread measured at decision times,
a size-depth curve, decision-to-fill slippage, latency, partial fills and rejections.

**Verdict — mostly yes, with an exact split.**

| evidence | obtainable without any order | method | authorization needed |
|---|---|---|---|
| minimum notional, lot step, tick, order types, API limits, maintenance | **yes** | venue documentation | owner authorizes collection (2P `I-3`) |
| account existence, identity tier, deposit/withdrawal capability | **yes** | account screens | owner verification (2P `I-2`) |
| fee schedule, fee currency | **yes** | venue documentation | `I-3` |
| spread distribution | **yes, without trading** | quote sampling at decision times | market-data authorization |
| slippage, latency, fill rate, partial fills, rejections | **no** | requires order placement | paper/live execution — a Gate 6 outcome (§9.2) |

**Interpretation:** the venue-constraint question (T-4 E-3) is fully answerable by documentation. The
cost question (E-2) splits: half documentary/sampling, half execution-dependent. No part of it
requires *real capital* — but the execution-dependent half requires an authorization the protocol does
not currently define (see Conflict C-6 in §5).

### F. Statistical sufficiency

**Question:** can the project establish whether the required number of independent observations is
achievable *before* opening OOS data?

**Evidence.** Protocol §5.2 item 11 requires a "sample-sufficiency calculation: `N_ind`, `N_obs`,
`required_opportunities`, assumptions, and sensitivity" in the registration, and §5.3 requires it to
be reproducible before any outcome is seen. Protocol §6.2 requires a feasibility census that "counts
signals and opportunities but observes **no outcomes**". D-12 is resolved to **strict one-look with
logging and an embargo** (`stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §13), and protocol §8.2
requires chronological non-overlapping blocks with an embargo.

**Verdict — confirmed by design.** The framework is constructed so that the sufficiency question is
answered before the OOS look: Gate 2 freezes `required_opportunities`, Gate 3 compares the
dependence-adjusted feasible count against it, and only Gate 5 spends the one validation look.
**Interpretation:** the arithmetic already recorded is unpromising — `N_ind ≈ 785` at `δ = 0.10R`,
`σ = 1R`, `α = 5%`, power `80%`, against `12`–`71` opportunities per family over 1,277 days
(`stage2p/GATE0_READINESS_ASSESSMENT.md` §7.3) — but that is a legitimate Gate 3 stop, and it is
decision-relevant. It is not a reason to lower the bar and not a reason to skip the census.

---

## 5. Conflicts and discrepancies found

Each is recorded, **not resolved** by this stage.

### C-1 — MATERIAL — Gate 0's own blocker list is satisfied, yet Gate 0 is recorded as not passed

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §8.1): before Gate 0 could pass, only three
things were needed — D-04 real-capital translation; the `R-17`–`R-20` artifacts; and the `R-21`
frequency acknowledgment.

**Verified fact** (same document, §9): "It does **not** pass Gate 0, and would not pass it even if
D-04 were answered tomorrow, because the artifacts in R-17 to R-20 do not exist yet."

**Verified fact** (later records): D-04 is resolved with all four figures and the explicit statement
that no deposit/withdrawal/access restrictions are known
(`stage2u/STAGE2U_A1_SIGNED_OWNER_DECISION_RECORD_DRAFT.md` §3, D-04 row;
`stage2u/STAGE2U_STAGE_COMPLETION_REPORT.md` §4). `R-17`–`R-20` are
`S` and `R-21` is `S` (`stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` §2). `R-13` —
"every blocking decision resolved" — is `S` in the same list.

**Conflict.** Every blocker named by the frozen Gate 0 assessment is now closed, and the protocol's
§3.3 criteria read as satisfied for the research-leg objective; yet Gate 0 is recorded as not passed
on the strength of `R-08`/`R-15`, neither of which appears in the frozen blocker list and one of which
(`R-15`) says on its face that it blocks only real-capital claims.

**Interpretation:** the current "not passed" status is defensible only if the Gate 0 objective is the
real-capital one. That scoping choice is made in `stage2v` §4's final sentence, and it is an
interpretation, not a protocol criterion. It is the single most consequential unresolved point in the
framework.

### C-2 — MATERIAL — R-08's requirement was strengthened after the Gate 0 criteria were frozen

**Verified fact** (2P §5, R-08): missing evidence was "the owner's real deployable capital, or an
explicit statement that none is committed."

**Verified fact** (`stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §6.2): "the real-base sizing context is
still incomplete: the restrictions are unknown, and no real-basis per-trade sizing rule exists (and
none is invented)." R-08 stayed `P` with its description "refined".

**Verified fact** (`stage2t/STAGE2T_DECISION_PACKET.md` §3): "T-4c keeps `R-08` **P**."

**Interpretation:** R-08 now encodes both the capital context *and* the T-4 sizing rule, while its
frozen definition named only the capital context. Applying the 2P definition literally, the owner's
`$100` plus the four constraint statements would satisfy R-08; applying the 2R/2T definition, only a
T-4 decision would. This is a documented evolution, not a silent edit — but it means **"R-08 P" is not
the same requirement it was when Gate 0's criteria were frozen.**

### C-3 — MATERIAL / CIRCULAR — protocol §3.5 bars the evidence T-4 requires

**Verified fact** (§3.5): with Gate 0 incomplete, "no hypothesis may be registered and no data may be
accessed for a strategy experiment".

**Verified fact** (2W §4): T-4 requires E-1 (validated expectancy), E-4 (tail distribution) and E-5
(frequency), all of which are outputs of Gates 2–5.

**Conflict.** The only route to E-1/E-4/E-5 runs through the gates that Gate 0 gates. Gate 0's
completion is said to depend on R-08, whose completion depends on T-4, whose completion depends on
E-1/E-4/E-5. **No amount of additional evidence breaks this loop, because the loop controls access to
the evidence.** It can only be broken by a scope decision.

### C-4 — MINOR — Gate 1 requires a venue specification but its pass criteria do not test it

**Verified fact** (§4.2): the venue specification (instrument, minimum notional, lot size, order
types, API limits, maintenance windows) is a required **input**.

**Verified fact** (§4.3): the pass criteria test dataset hashes, gaps, alignment, block separation,
cost evidence (measured or assumption-plus-plan), and no OOS read. Venue-specification completeness is
not among them.

**Interpretation:** a research-leg Gate 1 could formally pass with the venue specification still
`UNKNOWN`. That is an ambiguity in the protocol, and it matters because it would let a data-validity
gate pass while the execution-feasibility question is untouched. It should be resolved by an explicit
recorded descoping statement at Gate 1, not by silence.

### C-5 — MINOR — Binance-proxy cost is allowed by §4.3 but forbidden as a "venue cost" by 2P §8

**Verified fact** (§4.3): cost evidence may be "explicitly labelled as an assumption with a plan to
replace it".

**Verified fact** (2P §8): "the frozen `26 bp` figure as a venue cost" is an unacceptable
substitution, because it is "documented as a Binance spot proxy, explicitly not a measurement".

**Interpretation:** these are reconcilable if the research leg labels the cost as a *research-leg
cost assumption* and never as a Nobitex cost. The label is not cosmetic: it determines whether a
Gate 5 verdict can be described as execution-feasible. It cannot.

### C-6 — MATERIAL — measured execution is both required (T-4 E-2) and forbidden before Gate 6

**Verified fact** (protocol §9.2): "Advance to paper trading" is a Gate 6 decision requiring all gates
passed plus "separate owner authorization".

**Verified fact** (§9.4): "no decision in this table authorizes a trade, a paper-trading account, a
live account, or a new candidate."

**Verified fact** (2P §3.2): slippage must be "decision-to-fill measurements at the intended order
type", fill rates must be "observed rates", and rejections must be observed.

**Conflict.** T-4's E-2 asks for evidence the gate sequence places after the last research gate. The
framework defines no "measurement-only execution" authorization. Therefore E-2 is either (a) satisfied
partially and labelled an assumption under §4.3, or (b) requires a new owner-defined authorization
category. Making that choice is an owner decision, not an agent default.

### C-7 — RECORDED, not a conflict — R-17 wording discrepancy

`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 requires `A-1` to carry **D-01, D-02, D-03,
D-07, D-08, D-09, D-12**; `stage2p/GATE0_READINESS_ASSESSMENT.md` §5 row R-17 says "consolidating
**D-01…D-07**". The signed A-1 resolves the *content* by carrying the §4 list in Part A and the
remainder in Part A-addendum, and records the discrepancy rather than reconciling it
(`stage2u/STAGE2U_A1_SIGNED_OWNER_DECISION_RECORD_DRAFT.md` §7). Preserved here unchanged.

### C-8 — RECORDED — R-08 `O → P` evolution

`stage2p` records R-08 as `O`; from 2Q onward it is `P` (2Q §4; 2R §6.2; 2X §4). The evolution is
documented in `stage2x/STAGE2X_GOVERNANCE_STATUS_RECORD.md` §5. It is not a conflict, but it is the
visible trace of C-2.

### C-9 — OBSERVATION — the register's blocking marks do not name T-4

**Verified fact** (`stage2m/OWNER_DECISION_REGISTER.md` §1): D-04 is **BLOCKING**; there is no
decision ID for the real-capital per-trade sizing convention. T-4 is a Stage 2T decision attached to
D-04, not a register decision.

**Interpretation:** Gate 0 §3.3 tests whether "every decision in the owner register that is marked
blocking is resolved". D-04 is resolved and `R-13` is `S`. T-4 is therefore **not** a Gate 0 blocking
decision by the register's own construction. This is further evidence that the deadlock is created by
the checklist rows, not by the register.

---

## 6. What is *not* a dependency (checked, so it is not assumed later)

| item | status | why it does not block Gate 0 |
|---|---|---|
| `R-05` | P | Gate 1 evidence item (2V §4 item 3) |
| `R-10` | P | Gate 1 evidence item (2V §4 item 3) |
| `R-22` | P | Gate 4 evidence item (2V §4 item 3) |
| `R-06`, `R-23` | N/A | not adopted; D-15 deferred (2P §5) |
| `D-15` | deferred | "BLOCKING for any new candidate", not for Gate 0 (register §1) |
| `B-02`–`B-04` | open | Gate 1 / Gate 3 (2P §5) |
| `B-05` | open | Gate 4 (register D-13) |
| `$30` tolerance | personal, cumulative | not a strategy drawdown limit; does not scale D-02 (2W §2) |
| `$250` objective | owner, unvalidated | a target, not a Gate 0 input (2P §3.3) |

---

## 7. Conclusion of the audit

**Finding 1.** The circularity is real. It is not a misunderstanding of one document; it is produced
by the interaction of three authoritative statements: §3.5's unconditional prohibition, §3.3's
pass criteria, and the 2V interpretation that Gate 0 must be judged on the real-capital objective.

**Finding 2.** The circularity is **scoping-induced, not evidence-induced**. Three independent lines of
evidence show the research leg does not need T-4: R-07/R-02–R-04/R-15(research)/R-16 are all `S`;
`R-13` is `S`; and the Gate 0 artifact definition *requires* the real-capital item to be recorded as
open.

**Finding 3.** T-4's six-item gate does not require real-capital trading. Four items need no
execution, two need a research experiment, and one needs a measurement the protocol currently places
after Gate 6.

**Finding 4.** The framework therefore already contains the *substance* of a research-leg/real-capital
separation (R-07 vs R-08, R-15's `S`/`B`, A-4's required open item) but not the *procedure* that would
let the research leg proceed under it. The gap is procedural and small; the consequence of leaving it
is total.

**Finding 5.** No further evidence can close the loop. Only an owner scope decision can. Paths are
compared in `STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md`; the boundary any such decision must
respect is in `STAGE2Y_AUTHORIZATION_BOUNDARY.md`.

**Explicitly not concluded here:** that Gate 0 has passed; that any gate may advance; that the
research leg will succeed; that `$250` on `$100` is achievable; that the `$30` tolerance is sufficient;
that Nobitex can execute the strategy; that any candidate is viable; that the annual objective is
economically sensible.
