# Stage 2L — Technical Findings

**Audit baseline:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Finding set:** 10 findings — 0 CRITICAL, 0 MAJOR, 6 MINOR, 4 OBSERVATION  
**Primary audit verdict:** **SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED**

## 1. Severity definitions

| Severity | Meaning |
|---|---|
| **CRITICAL** | The recorded Stage 2J conclusion is wrong, the census is not traceable, or a frozen prohibition was violated. Immediate stop and correction required. |
| **MAJOR** | A frozen requirement is materially unimplemented, or a defect could plausibly change a verdict, without an overriding pre-registered interpretation. |
| **MINOR** | A requirement, label, population, or documentation detail diverges from the frozen text, but the divergence is bounded, disclosed, or has no observed effect on the recorded verdict. |
| **OBSERVATION** | A latent coupling, presentation ambiguity, or evidence gap worth recording. No demonstrated effect on Stage 2J. |

## 2. Finding summary

| ID | Severity | Short title | Stage 2J verdict impact |
|---|---|---|---|
| L-001 | MINOR | D capital-geometry verdict condition narrowed to the cost-feasible population | None — insufficient opportunities has precedence |
| L-002 | MINOR | Concentration FAIL criterion added by the Stage 2J plan | None — criterion met for D but lower precedence |
| L-003 | MINOR | Entry checks presence, not same-usable-segment continuity | None observed — no entry diagnostics fired |
| L-004 | OBSERVATION | B pre-touch deep break is labelled `retest_too_deep`, not `structure_broken` | None — label semantics only |
| L-005 | OBSERVATION | D `budget_ok` is unnecessarily gated on SMA/slope availability | None — warm-up ordering prevents effect |
| L-006 | MINOR | D report attributes an extra non-exempt 4h bucket to the M3 exemption | None — documentation wording only |
| L-007 | OBSERVATION | `rho=1` sensitivity uses arithmetic mean cluster size, not exact Kish weight | None — exact Kish is reported separately |
| L-008 | OBSERVATION | Recorded B `retest_timeout=0` not independently reproduced | None — mechanism verified, incidence not |
| L-009 | MINOR | Determinism claim has no retained second-run artifacts | None — evidence gap only |
| L-010 | MINOR | Code hash omits `freeze_verify.py` and test files | None observed — analytical code is covered |

## 3. Detailed findings

### L-001 — D capital-geometry verdict condition is narrowed by pre-registration

**Severity:** MINOR  
**Location:** `stage2j_census/analysis.py:631-644` and `921-938`;
`docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md:450-461`;
frozen `CANDIDATE_B_SPEC.md:790` and `CANDIDATE_D_SPEC.md:700`;
`docs/research/stage2j/machine_readable/candidate_d_census.json` (`capital_geometry`).  
**Requirement:** The frozen specifications state that the capital-geometry FAIL condition is
met when **any signal** has `notional_pct > 1.00`. Pre-registered interpretation C-1 states
that the **verdict condition** is evaluated on the cost-feasible population (B S8, D S7),
while the pre-gate population is reported as a diagnostic.  
**Explanation:** The two statements are not textually identical. For D, the pre-gate S6
population contains 295 signals, and 208 of them (70.51%) have `notional_pct > 1.00`; the
maximum is 4.0725. After the 0.20 cost gate, the S7 verdict population contains 45 signals,
none above 1.00, with a maximum of 0.7609. The frozen "any signal" wording would therefore
be satisfied on the pre-gate population, while the pre-registered verdict condition is not
satisfied on the cost-feasible population. B has no violation in either population.  
**Impact:** The capital FAIL term is effectively vacuous on the verdict population for D.
A reader who compares only the frozen sentence with the verdict could conclude that no
capital-geometry problem exists, even though the pre-gate geometry is impracticable for
70.51% of D signals. The pre-gate diagnostic is disclosed, so the information is present,
but the decision rule has been narrowed.  
**Proof status:** Proved. C-1 is explicitly written in the pre-registered plan; the counts
are exact machine-readable values; the code evaluates `capital_violation` on the verdict
population.  
**Historical-conclusion impact:** None. Both Stage 2J verdicts are
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`, which has precedence over the capital
condition. D also meets the concentration criterion independently. The verdict names cannot
change.  
**Evidence:** `candidate_d_census.json` `capital_geometry.pre_gate_diagnostic`
(`count_notional_pct_above_1_00=208`, `population_count=295`,
`share_notional_pct_above_1_00=0.7050847457627119`, `max=4.072533136959225`) and
`capital_geometry.verdict_population` (`population_count=45`,
`count_notional_pct_above_1_00=0`, `max=0.760891209644192`).  
**Recommended resolution:** Future freezes should name the capital-geometry evaluation
population in the frozen verdict table itself, rather than resolving it in a pre-registered
interpretation. A future report should keep the pre-gate violation count next to the verdict
term. Stage 2L does not alter the Stage 2J rule or report.

### L-002 — Concentration FAIL criterion is a Stage 2J extension

**Severity:** MINOR  
**Location:** `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md:517-528`;
`stage2j_census/analysis.py:996-1012`; frozen `CANDIDATE_B_SPEC.md:781-790` and
`CANDIDATE_D_SPEC.md:682-700`.  
**Requirement:** The frozen specifications define FAIL as `N < 150`, `M_all > 0.20`, or a
capital-geometry violation. They require concentration diagnostics but do not define an
`EXCESSIVE CONCENTRATION` FAIL term. The Stage 2J pre-registered plan adds a
`FEASIBILITY FAIL — EXCESSIVE CONCENTRATION` term when the largest non-empty cluster share
is `> 0.50` or the Kish design effect is `>= 2.00`.  
**Explanation:** The added criterion is pre-registered before counting, so it is not a
post-hoc rule. It is nevertheless a substantive extension of the frozen decision rule:
D's design effect is 3.9333, so D meets the added criterion. Under the frozen documents
alone, D would not have a concentration FAIL term.  
**Impact:** The extension does not change either recorded verdict because insufficient
opportunities precedes it. It would matter only if a future census passed the floor and the
cost condition while failing the concentration criterion; then the verdict vocabulary and
the frozen rule would diverge.  
**Proof status:** Proved by direct text comparison and by the machine-readable verdict
(`concentration.criterion_met=true` for D, with
`precedence="INCONCLUSIVE, then INSUFFICIENT OPPORTUNITIES, then EXCESSIVE CONCENTRATION,
then FEASIBILITY PASS"`).  
**Historical-conclusion impact:** None. The lower-precedence term is not the primary reason
for either FAIL.  
**Evidence:** D design effect `3.933333333333333`, largest share `0.17777777777777778`;
B design effect `1.6896551724137934`, largest share `0.10344827586206896`; frozen FAIL
tables contain no concentration term.  
**Recommended resolution:** Record the concentration term as a formal protocol amendment
for future stages, or remove it from the verdict vocabulary and keep it as a descriptive
diagnostic. Do not retroactively edit Stage 2J.

### L-003 — Entry checks presence, not same-usable-segment continuity

**Severity:** MINOR  
**Location:** `stage2j_census/candidate_b.py:191-205`;
`stage2j_census/candidate_d.py:164-176`; frozen `CANDIDATE_B_SPEC.md:432-436`;
frozen `CANDIDATE_D_SPEC.md:415-418`;
pre-registered interpretations B-3 and D-1.  
**Requirement:** The frozen B specification says a confirmation bar that is the last bar of
its 1h segment is rejected as `no_entry_bar` **even if a bar exists after the gap**, because
a new segment is a different price history. The shared segment definition says a segment is
broken by a missing **or unusable** bar. The entry checks in both candidates test `present`,
`exact`, interval bounds, and `open > 0`, but not `segment_id[index+1] ==
segment_id[index]`.  
**Explanation:** A present-but-unusable bar at the expected entry slot (for example a
zero-volume, unclosed, partial, or invalid-OHLC record) breaks the segment under the shared
definition, yet the implementation accepts it as an entry and records the close-time
property only as a diagnostic. Pre-registered B-3 and D-1 explicitly choose this
presence-only reading under M2, arguing that close-time properties are not knowable at the
open. The frozen text contains both ideas, and the pre-registration resolves the tension in
favour of presence.  
**Impact:** The implementation can accept an entry that a literal same-segment reading would
reject. The recorded Stage 2J entry diagnostics are empty for both candidates
(`secondary_labels` is empty; B has no `unclosed_entry_bar`, `zero_volume_entry`,
`partial_entry_bar`, or `invalid_entry_ohlc`), so no observed Stage 2J signal was affected.
The audit cannot rule out an effect on a different dataset without rerunning the detector.  
**Proof status:** Code path proved; synthetic checks confirm that a present-but-unusable
entry is accepted and diagnosed, and that a missing entry is rejected. Historical incidence
is evidenced by empty entry diagnostics but not by a full rerun.  
**Historical-conclusion impact:** None observed.  
**Evidence:** Synthetic checks “B present-but-unusable entry still reaches S7/S8”,
“D present-but-unusable entry still reaches S6/S7”, and the empty `secondary_labels` /
`diagnostics` objects in both census JSON files.  
**Recommended resolution:** Future specifications should state which rule wins for a
present-but-unusable bar at `c+1`. If segment continuity is intended, add an explicit
segment check; if presence-only is intended, remove the contrary sentence. Stage 2L does not
repair the implementation.
