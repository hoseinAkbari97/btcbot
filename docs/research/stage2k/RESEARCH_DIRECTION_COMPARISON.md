# Stage 2K — Research Direction Comparison

**Status:** historical review and research design only.
**Date:** 2026-11-08.
**Scope:** compares the directions available after the four feasibility failures. It proposes no candidate,
runs no census, processes no market data, and computes no P&L, expectancy or optimisation.

This document does **not** make the decision. The decision is in
`STAGE2K_FINAL_RECOMMENDATION.md`. This document records the options, the criteria, the ordinal
scores, and the considerations that drive the ranking, so that the decision can be checked against
them.

---

## 0. What this document is and is not

It is a comparison of **research directions**, not of strategies. A direction is what the project
does next; a strategy is what it would test. The distinction matters here because the record's central
finding is that the project cannot yet tell whether it has a market problem or a framework problem
(`FAILURE_MODE_ANALYSIS.md` §9). Directions differ mainly in which of those two they address.

It is **not**:

- a new candidate specification, or a revision of any frozen one;
- a census, a feasibility count, or a re-count;
- an outcome study, a backtest, or an estimate of edge;
- an authorization to read validation or out-of-sample data;
- a Stage 2L plan.

Every quantitative statement below is quoted from a frozen artifact or is arithmetic on a quoted
value. Where Stage 2K computes something new (for example a detectable-effect figure), it is labelled
as Stage 2K arithmetic.

---

## 1. How the directions were generated

### 1.1 Constraints any direction must respect

| constraint | consequence for the comparison |
|---|---|
| Review-only authority | A direction cannot be executed inside Stage 2K; it can only be described, costed and scored |
| Frozen artifacts are immutable | No direction may propose editing a Stage 2A–2J artifact; the most it can do is supersede one by a new, separately authorized freeze |
| No validation or OOS use | Any direction needing data beyond 2021-01-01 → 2024-07-01 leaves the current authorization boundary |
| No Stage 2L | No direction may assume an outcome study is already permitted |
| Evidence labels | A direction's rationale must distinguish what the record establishes from what it assumes |

### 1.2 The generation rule

A direction qualifies only if it:

1. addresses at least one failure mode from the taxonomy in `FAILURE_MODE_ANALYSIS.md` §2;
2. is executable without altering a frozen artifact;
3. has a defined output that a later stage could audit.

Seven possibilities were generated first, then consolidated into five directions. The consolidation is
recorded in §6 so it can be challenged; it is not a claim that the five are exhaustive.

| id | possibility | becomes |
|---|---|---|
| P1 | Proceed to an outcome study on an existing candidate despite the floor | **D1** (with P2) |
| P2 | Lower the floor to fit the observed counts | **D1** |
| P3 | Relax the cost gate because the 26 bp proxy may be too high | **D2** |
| P4 | Re-run a censused candidate under a modified definition | **D3** (Candidate A only) |
| P5 | Verify venue cost and derive the sufficiency rule before deciding | **D2**, and the precondition for **D3** |
| P6 | Change the strategy family or the instrument | **D4** |
| P7 | Stop the direction and preserve the record | **D5** |

P1 and P2 consolidate because both are the same act — proceeding without a sufficiency rule — differing
only in whether the gate is formally amended. P3 does not stand alone because changing one input
without measuring it or replacing the decision rule is not a direction; it is an assumption change
inside D2. P4 survives only in the narrow form D3 because the record gives a specific reason to
revisit A and no comparable reason for B, C or D.

### 1.3 Evidence available to each direction

| direction | primary evidence base |
|---|---|
| D1 | The four census reports and the Stage 2J verdicts, which establish the counts |
| D2 | `STAGE2D_STRATEGY_REDESIGN.md` §1.3–§1.5 (the 150 floor is underived, 349 is an independence estimate, 0.15R is an assumption); every candidate spec §0.1 (26 bp is a proxy) |
| D3 | Stage 2C (A: 151 feasible, 71 canonical, 120h overlap removes 53%); Stage 2J A-related concentration diagnostics |
| D4 | The four failures, which say nothing about other families; Stage 2K synthesis §10 |
| D5 | The Stage 2J final decision and the four failed gates |

---

## 2. Scoring method

### 2.1 Criteria

Six criteria, each scored on a five-point **ordinal** scale. The scores are judgements about this
record, not measurements, and they are not commensurable across criteria.

| code | criterion | question it answers |
|---|---|---|
| **E** | Evidential support | Does the frozen record support this direction's premise? |
| **I** | Information gain | How much would the project learn per unit of work? |
| **C** | Effort and cost | How much work, data collection and elapsed time does it need? (high score = low effort) |
| **R** | Pre-registration safety | How low is the risk of post-hoc inference, HARKing or gate-moving? (high = safer) |
| **G** | Data and governance safety | How low is the risk of touching OOS data, frozen artifacts or unratified conventions? (high = safer) |
| **V** | Reversibility | How easily can the decision be undone if it proves wrong? |

### 2.2 Scale

| score | meaning |
|---:|---|
| 0 | contradicted by the record, or unacceptable on this criterion |
| 1 | weak / high cost / high risk |
| 2 | mixed / moderate |
| 3 | supported / low cost / low risk |
| 4 | directly supported / minimal cost / minimal risk |

### 2.3 Why there is no composite score

A single weighted total would require weights that encode a preference the owner has not declared —
how much information gain is worth how much governance risk. Averaging would launder that preference
into a number and make the ranking look empirical. Instead the comparison reports the six scores and
one **decisive consideration** per direction, and §5 states what would change the ranking.

**Verified fact:** nothing in this scoring is derived from a statistical model, a backtest or a
simulation. It is a structured judgement over the frozen record.

---

## 3. The five directions

### D1 — Proceed to an outcome study on an existing candidate by amending the gate

**What it is.** Take the candidate with the largest canonical population and run the outcome study
that Stage 2L would have run, treating the 150 floor as advisory rather than binding. The variants:

| variant | canonical N | smallest detectable effect | concentration |
|---|---:|---:|---|
| D1a — Candidate A | 71 | 0.332R | Kish `n_eff` 12.69 over 151; largest episode 13.9% |
| D1b — Candidate D | 34 | 0.480R | design effect 3.93; all signals 2021–2022 |
| D1c — Candidate B | 24 | 0.572R | design effect 1.69 on S8, 4.93 on the quarter view |

Candidate C is not a variant: 12 events imply 0.809R and the trigger population is capped at 17.

**Output.** An in-sample outcome estimate with a confidence interval on 24–71 events.

**What it requires.** An explicit owner override of a floor that was frozen before counting; a new
Stage 2L protocol; and a decision about what would count as a result. It does not require OOS data,
but it does spend the programme's remaining in-sample statistical budget.

**What it can establish.** Whether these particular frozen signal sets, on this interval, produced
returns distinguishable from zero at the effect sizes above.

**What it cannot establish.** An edge of the size the project says it cares about. **Verified
arithmetic:** with 34 events the smallest detectable effect is 0.480R, and with 71 events it is
0.332R; a failure to reject at those sizes is consistent with a true effect of 0.15R. A null result
would therefore be uninformative about the hypothesis, and a positive result would need out-of-sample
confirmation that no current plan provides.

**Main risk.** The move is exactly what the protocol forbids: changing the admissibility gate after
seeing the counts. Stage 2I considered threshold changes only as formal change proposals and Stage 2J
declined to apply them (`stage2i/CHANGE_PROPOSALS.md`; `stage2j/STAGE2J_FINAL_DECISION.md` §5).
Doing it informally would leave the programme without a rule it can trust in the next stage.

**Secondary risk.** D's canonical signals all fall before 2022-10, so a D1b estimate would describe a
market state that has not recurred in the sample; A's effective sample is roughly a sixth of its
nominal count.

**Scores.** E 0 · I 1 · C 2 · R 0 · G 2 · V 2

**Decisive consideration.** The study cannot answer the question it would be commissioned to answer,
because its own detectable effect is three times the target effect.

---

### D2 — Repair the research framework before any further candidate work

**What it is.** Three linked repairs, none of which touches a frozen artifact:

1. **Verify the execution cost.** Obtain the venue's fee schedule (maker and taker), measure the BTC
   spread distribution at the times these signals fire, measure realised slippage rather than assuming
   it, check depth and minimum notional at the sizes implied by 1% risk, and record outage behaviour.
2. **Replace the underived floor with a derived sufficiency rule.** The owner declares a minimum
   economic effect δ. The rule maps δ, the significance level, the power target, the return variance
   and a declared dependence allowance to a required count. The rule is frozen **before** any new
   count is taken, and it replaces 150 rather than being fitted to it.
3. **Re-freeze and audit the framework.** Publish the repaired framework as a new version and subject
   it to an arms-length audit, since Stage 2H was a self-audit
   (`STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md` §1).

**Output.** A framework in which "admissible" has a stated meaning; a documented, venue-specific cost
basis; a pre-declared count requirement. It produces **no** opportunity count and validates no
candidate.

**What it requires.** An owner decision on δ; external venue data collection; a new framework freeze;
preferably a third-party audit.

**What it can establish.** Whether the current threshold is defensible, what count would actually be
needed, and whether 26 bp over- or under-states the real cost.

**What it cannot establish.** That any candidate has an edge, or that any failed candidate would have
passed under a different rule. **Verified fact:** even a zero-cost world cannot lift B above 32 or C
above 17, so the framework repair cannot rescue those two.

**Main risk.** It produces no trading insight on its own. If the owner declares a large δ, the derived
rule may show that no design of this kind can be tested on this interval — which is informative but
may read as a refusal to proceed.

**Secondary risk.** Cost verification may reveal a **higher** all-in cost than 26 bp, which would
close A and D rather than open them.

**Evidence status.** E 3/4. Two defects are verified rather than supposed: the 150 floor has no
statistical derivation (`STAGE2D_STRATEGY_REDESIGN.md` §1.3;
`STAGE2D_STRATEGY_RECOMMENDATION.md` §9(1)), and 26 bp is a Binance proxy, not a measured Nobitex
cost (every candidate spec §0.1; `STAGE2D_STRATEGY_REDESIGN.md` §10.2, §10.4). A third is verified
arithmetic: the 150 floor is sufficient only for an effect near 0.23R, not the stated 0.15R
(`FAILURE_MODE_ANALYSIS.md` §7.3).

**Scores.** E 3 · I 2 · C 2 · R 4 · G 4 · V 4

**Decisive consideration.** It is the only direction that removes both known framework defects
without altering a frozen artifact, consuming OOS data, or prejudging any candidate.

---

### D3 — Revisit the trend-pullback family through a pre-registered variant of Candidate A

**What it is.** Open one new, pre-registered specification in A's family — not an edit to A — and
census it under the framework repaired by D2. The record points at A for four reasons:

1. **Highest canonical count:** 71, against 34 (D), 24 (B) and 12 (C).
2. **Smallest detectable effect:** 0.332R at 71, against 0.480R, 0.572R and 0.809R.
3. **No cost-geometry collapse:** feasible share 0.774, and 186 of 195 valid triggers pass even at
   10 bp.
4. **The largest identified removable loss:** the 120h overlap rule discards 80 of 151 feasible
   signals (53%).

Crucially, A's design already contains an unconditioned control arm that removes only the 4h regime
condition, and **its matched-window non-overlapping count is exactly 150**
(`STAGE2C_FEASIBILITY_CENSUS.md` §7, table). That is the only object anywhere in the record that
reaches the frozen floor. It is also explicitly **not promoted**: the report calls its higher
frequency "evidence about the regime filter's selectivity, not evidence that the unconditioned
strategy is profitable" (§7, closing paragraph).

**Output.** A new frozen specification, a new pre-declared count, and an explicit statement of
whether the regime condition or the overlap rule is what kept A at 71.

**What it requires.** A D2 framework first (otherwise the new count has no meaning); a written new
specification that differs from A in named, pre-declared ways; a new freeze; a new census; and — if
the count is to be believed — an arms-length audit. It does not require OOS data.

**What it can establish.** Whether a less-conditioned member of A's family is dense enough to be
testable at all, and how much of A's scarcity was the regime filter versus the overlap rule.

**What it cannot establish.** That the variant has an edge. It also cannot make the frozen A result
admissible retroactively: 71 stays 71, and the control's 150 was never a candidate.

**Main risk.** Promoting a diagnostic control after seeing that it reaches the floor is the clearest
possible case of post-hoc gate-fitting. The control was defined as a selectivity check, not as a
strategy; Stage 2C anticipated exactly this move and refused it. A variant is defensible only if it
is written and frozen as a *new hypothesis* with its own rationale, and if the frozen A and control
results are reported beside it.

**Secondary risk.** Even at 150, the smallest detectable effect is 0.229R, not the stated 0.15R. A
variant that lands at the floor would still be underpowered for the project's own target.

**Scores.** E 2 · I 3 · C 2 · R 2 · G 3 · V 3

**Decisive consideration.** It has the highest information gain per unit of work of any candidate
direction, and it also carries the highest inference risk, because the one object at the floor is a
diagnostic that was designed not to be promoted.

---

### D4 — Change the strategy family or the instrument

**What it is.** Abandon the trend-continuation / breakout / intraday-momentum family and pre-register
a different hypothesis class, or move to a different instrument or venue. Candidate families that
were screened and not advanced in Stage 2D §8 would be the natural starting list; new ones would need
their own rationale.

**Output.** A new research object with no inheritance from the four censuses.

**What it requires.** A family-level economic rationale, a data-availability check, a new freeze and a
new census. Some families need data outside the current boundary (funding rates, other pairs, order
book, on-chain), which raises a separate authorization question even when it is not OOS data.

**What it can establish.** Whether a different premise is dense enough to test.

**What it cannot establish.** Anything about the four failed candidates, and nothing that transfers
from their verdicts.

**Main risk.** Restart cost with no evidential support from this record. The record is silent on other
families; the four failures are weak evidence about the family and no evidence about the market. If
the framework defects are not repaired first, the new family inherits the underived floor, the
unverified cost proxy and the 0.15R mismatch, and is likely to fail for the same framework reasons.

**Scores.** E 1 · I 2 · C 0 · R 2 · G 2 · V 2

**Decisive consideration.** The highest ceiling and the weakest current support; it is the natural
successor to D2, not an alternative to it.

---

### D5 — Stop the current strategy family under the current framework

**What it is.** Close the four-candidate programme as a **negative feasibility result**. Record that
under the frozen framework no candidate was admissible; preserve every artifact; authorize no further
census and no Stage 2L. Framework repair, if wanted, becomes a separate later decision rather than a
continuation of this programme.

**Output.** A closure decision and a preserved, auditable negative result. No new count, no new
specification.

**What it requires.** An owner decision and a closure record — this stage supplies the latter.

**What it can establish.** Only what is already established: that these four frozen designs produced
too few opportunities under the frozen rules, and that the causes differ by candidate.

**What it cannot establish.** That the market lacks the opportunities, that the family has no edge, or
that a repaired framework would fail. D5 is a decision about research allocation, not a market claim.

**Main risk.** Forgoing the unmeasured possibility that A's family, or D under a verified lower cost,
is admissible. Sunk-cost pressure to continue will be real, and a stop can be read as a verdict on the
market rather than on the framework — which is why the closure record must state its scope precisely.

**Scores.** E 4 · I 2 · C 4 · R 4 · G 4 · V 3

**Decisive consideration.** It is the only direction whose premise the record fully establishes, and
the only one that requires no assumption the record cannot support.

---

## 4. Comparison

### 4.1 Scores

| direction | E | I | C | R | G | V | what would have to be true for it to work |
|---|---:|---:|---:|---:|---:|---:|---|
| D1 — proceed by amending the gate | 0 | 1 | 2 | 0 | 2 | 2 | The frozen sets carry an effect of at least 0.48R (D) or 0.33R (A) that is not selection artefact |
| D2 — repair the framework | 3 | 2 | 2 | 4 | 4 | 4 | The owner can declare a minimum effect, and venue cost is measurable |
| D3 — pre-registered A-family variant | 2 | 3 | 2 | 2 | 3 | 3 | A pre-declared variant is denser than 71 and the gain survives a dependence allowance |
| D4 — change family or instrument | 1 | 2 | 0 | 2 | 2 | 2 | Another family is denser, and the framework defects are fixed first |
| D5 — stop the current family | 4 | 2 | 4 | 4 | 4 | 3 | Nothing further can be learned without new authorization — true by construction of the mandate |

### 4.2 The partial order

No composite score is computed (§2.3), so the ranking is stated as dominance relations among the six
criteria.

**Verified by inspection of the table:**

- **D1 is dominated by D5.** D5 scores at least as high on every criterion and strictly higher on E
  (4 vs 0), C (4 vs 2), R (4 vs 0) and G (4 vs 2). There is no criterion on which D1 is preferable.
  This is the cleanest result in the comparison.
- **D2 and D5 are not ordered.** D5 is better supported and cheaper; D2 is more reversible and
  produces a reusable framework. The choice between them is a choice about whether the project wants
to keep the option to test a candidate later.
- **D3 trades against D2.** D3 has the highest information gain (3) but is materially weaker on
  evidential support (2 vs 3) and pre-registration safety (2 vs 4). It cannot be undertaken before D2
  without inheriting the defects it is meant to address.
- **D4 is the weakest on support and effort.** It is the only direction scoring 0 on effort, and its
  evidence score of 1 reflects that the record says nothing about other families.

**Ranking as three tiers:**

| tier | directions | meaning |
|---|---|---|
| directly supported, low risk | **D5** | Premise established; no new assumption |
| conditionally strong | **D2**, then **D3** | D2 creates the conditions under which D3 could mean something |
| not supported by this record | **D4** | Rationale must come from outside the record |
| dominated | **D1** | Strictly worse than stopping |

### 4.3 The single most decision-relevant missing number

**Verified fact:** D has 253 of 295 sessions passing the cost gate at 10 bp and 45 at 26 bp. The
**canonical non-overlap count at 10 bp was never computed**; only the gate-pass count was reported
(Stage 2J D report §4). Everything else about D is known.

**Interpretation:** if a verified venue cost were low enough, D's canonical count would be the one
number that could plausibly exceed 150 — or it might not, because the 24h overlap rule could still
collapse 253 sessions. Until it is computed, no direction can claim D is rescuable, and D1b's premise
remains untested rather than refuted.

---

## 5. What would change the ranking

These are the conditions under which the comparison in §4 would have to be rewritten. None is
satisfied by the current record.

| condition | effect on the ranking | status |
|---|---|---|
| Verified all-in cost ≤ 10 bp | D's feasible share rises from 0.153 to 0.858; D2 and D3 rise; D1b still cannot detect 0.15R | **Unmeasured** |
| Verified all-in cost ≥ 39 bp | D falls to 8 feasible, A to 122, B to 25, C to 9; every candidate closes; D5 strengthens | **Unmeasured** |
| Owner declares δ = 0.15R | No count in the record is sufficient (best case 150 → 0.229R); D1 collapses entirely; D2 must produce a dependence-aware requirement near 349 or larger | **Undecided** |
| Owner declares δ ≈ 0.23R | The 150 floor becomes approximately consistent with the target, but A's 71 and D's 34 still fail; D3's relevance rises | **Undecided** |
| Owner declares δ = 0.25R | The independent requirement falls to about 126, so A's control at 150 would clear a nominal count — but not a dependence-adjusted one | **Undecided** |
| An A-family variant yields ≥ 200 canonical with design effect ≤ 2 | D3 becomes genuinely admissible and would justify an outcome study | **Not tested** |
| A third-party audit is required before any new count | D2 must precede D3 and D4; D5 unaffected | **Governance question** |
| The owner will not declare a minimum effect | D2 and D3 cannot be completed; the choice reduces to D5 | **Owner decision** |

**Verified arithmetic for the δ rows:** `N = (2.801585 / δ)²` under the project's independence
assumptions. At δ = 0.25R this gives 125.6, so 126; at δ = 0.23R it gives 148.4, close to 150; at
δ = 0.15R it gives 348.8, the recorded 349 reference.

**Interpretation:** the floor and the target are consistent only if the target is about 0.23R. The
project has never said that is the effect it cares about.

---

## 6. Challenge of the seven source possibilities

Each possibility is stated in its strongest form before its disposition is recorded, so that the
consolidation in §1.2 can be checked rather than trusted.

### P1 — Proceed to an outcome study despite the floor

*Strongest form:* the 150 floor is underived, so treating it as binding has no statistical authority;
a 34- or 71-event study could still detect a large edge, and a large edge is what would matter
economically.

*Disposition:* kept as D1, and dominated. The argument succeeds only if the effect is large; the
record's own design margin assumes 0.15R, at which neither count is informative. A direction that
works only under an assumption the project has rejected is not a direction.

### P2 — Lower the floor to fit the observed counts

*Strongest form:* since 150 was never derived, replacing it with a number the data can meet is not
obviously worse than keeping it.

*Disposition:* merged into D1 and not separately scored. Lowering a threshold after seeing the counts,
without a rule that says what the new number must satisfy, is gate-fitting. The legitimate version of
this idea is D2: derive the number from a declared effect before counting again.

### P3 — Relax the cost gate

*Strongest form:* 26 bp is a Binance proxy; if the real Nobitex cost is 10 bp, D's feasible population
is 8.6 times larger and the cost gate is doing most of the damage.

*Disposition:* merged into D2, not kept as a direction. Relaxing an unmeasured input is an assumption
change, not evidence. D2 measures the input; only then can the gate be re-set, and only with a
pre-declared rule.

### P4 — Re-run a censused candidate under a modified definition

*Strongest form:* A is the closest object to the floor and its control arm already reaches 150; a
variant that removes one condition might be admissible.

*Disposition:* narrowed to A and kept as D3. It does not generalise: B's pre-gate ceiling is 32 and
C's is 17, so no definition change can rescue them without replacing the hypothesis, and D's problem
is stop geometry rather than definition. Re-running with a modified definition is a new hypothesis,
so the direction is only defensible as a new pre-registration.

### P5 — Repair the framework first

*Strongest form:* both known defects — the underived floor and the unverified cost — are framework
defects, not market findings, and every candidate direction inherits them.

*Disposition:* kept as D2 and made the precondition for D3 and D4. This is the only possibility that
addresses a verified defect without a new market claim.

### P6 — Change the strategy family or instrument

*Strongest form:* four within-family attempts have failed; the family may be the problem.

*Disposition:* kept as D4. Its support is weak because the record contains no census of another
family, and the four failures are equally consistent with a framework problem. It is the natural
successor to D2, not a substitute for it.

### P7 — Stop and preserve the record

*Strongest form:* every direction except D2 and D5 depends on an assumption the record cannot support;
stopping is the only choice that adds no unsupported premise.

*Disposition:* kept as D5, the primary direction of the final recommendation.

### 6.1 Possibilities not considered, and why

| excluded possibility | reason |
|---|---|
| Extend the development interval | Would consume validation/OOS data; prohibited in Stage 2K and a separate governance decision |
| Add leverage or a short leg | Changes the hypothesis and the mandate, not the sample; every prior verdict would cease to apply |
| Tune candidate parameters | Prohibited by every frozen specification and by Stage 2I change control |
| Combine candidates into a portfolio | Introduces multiplicity and dependence problems on top of populations that individually fail |
| Change the data vendor | Addresses none of F1–F5; the seven gaps were already handled and no gap explains the counts |

The five directions are therefore **not claimed to be exhaustive**. They are the set that survives
the constraints in §1.1 and the generation rule in §1.2.

---

## 7. What this comparison does not decide

It does not decide what the project should do. It establishes that:

1. D1 is dominated by D5 and cannot be recommended on this record;
2. D2 is the only direction that repairs verified framework defects without a new market claim;
3. D3 has the highest information gain and the highest inference risk, and depends on D2;
4. D4 has the highest ceiling and no support from this record;
5. D5 is the only direction whose premise the record fully establishes.

The choice between D5 and D2 — and whether D3 should follow either — is made in
`STAGE2K_FINAL_RECOMMENDATION.md`, with its reasoning and its authorization limits stated there.
