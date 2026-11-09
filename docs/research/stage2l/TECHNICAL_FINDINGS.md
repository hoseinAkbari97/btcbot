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

### L-004 — B pre-touch deep break is labelled `retest_too_deep`, not `structure_broken`

**Severity:** OBSERVATION  
**Location:** `stage2j_census/candidate_b.py:150-166`; frozen `CANDIDATE_B_SPEC.md:378-380`
and `658-659`; pre-registered interpretation B-2.  
**Requirement:** The frozen B table says any bar `x` in `e+1 .. r-1` with
`close[x] < L_e - 0.50*A_e` is `structure_broken`. A different row says penetration
`> 0.50` at the touch bar is `retest_too_deep`. A pre-touch bar that closes below the lower
bound necessarily has a low below the bound, so both rows can describe the same bar.  
**Explanation:** The implementation evaluates the touch and penetration first. A pre-touch
bar with penetration above 0.50 ends the episode as `retest_too_deep`; the pre-touch
`structure_broken` label is never emitted. Post-touch breaks are still labelled
`structure_broken`. This is exactly the resolution pre-registered as B-2.  
**Impact:** Label semantics differ from a literal reading of the pre-touch row, but both
labels are S6 rejections and no signal survives either way. Recorded B labels contain
`retest_too_deep=72` and `structure_broken=8`. The distinction affects diagnostics, not the
stage count or verdict.  
**Proof status:** Proved. Synthetic checks show a pre-touch deep break ending as
`retest_too_deep` and a post-touch break ending as `structure_broken`.  
**Historical-conclusion impact:** None.  
**Evidence:** `candidate_b_census.json` labels; synthetic checks “B pre-touch deep break
carries retest_too_deep (B-2)” and “B post-touch break carries structure_broken”.  
**Recommended resolution:** Future specifications should state the precedence between the
pre-touch structure row and the penetration row. Do not relabel the historical census.

### L-005 — D `budget_ok` is unnecessarily gated on SMA/slope availability

**Severity:** OBSERVATION  
**Location:** `stage2j_census/series.py:479-491`; frozen `CANDIDATE_D_SPEC.md:319-391`.  
**Requirement:** Candidate D's `S4` requires `budget_ok == True`, where the budget depends on
the ATR percentile band `[25, 80]`. D does not require SMA50 or the 24h slope for its budget
predicate.  
**Explanation:** `compute_regime_4h` computes both `permission` (which needs SMA50 and slope)
and `budget_ok` inside the same `if pct_known and sma_known and slope_known` block. Thus a
known percentile is not enough to set `budget_ok`; the other two indicators must also be
known. This couples D's budget availability to indicators D does not use.  
**Impact:** No observed effect. The first known percentile is at 4h index 552; SMA50 and the
24h slope are known much earlier, so the coupling cannot delay any D signal in the recorded
data. It is a latent maintenance and interpretation risk.  
**Proof status:** Proved by code trace and synthetic warm-up test: `pct`, `budget_ok`, and
`permission` all first become known at index 552, and `pct[551]` is NaN.  
**Historical-conclusion impact:** None.  
**Evidence:** `series.py:479-491`; synthetic checks in “4h regime warm-up boundary”.  
**Recommended resolution:** In future code, split the availability conditions: set
`budget_ok` on `pct_known` alone, and set `permission` on `pct_known and sma_known and
slope_known`. Stage 2L does not change the implementation.

### L-006 — D report attributes an extra non-exempt 4h bucket to the M3 exemption

**Severity:** MINOR  
**Location:** `docs/research/stage2j/CANDIDATE_D_CENSUS_REPORT.md:255-258`;
`docs/research/stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md:92-98`;
shared `SHARED_CENSUS_PROTOCOL.md:206-242`.  
**Requirement:** The M3 supplied-bar exemption applies to the twelve registered
gap-adjacent 4h buckets. A non-exempt gap-affected bucket must be excluded from the
4h-from-1h comparison denominator and reported separately.  
**Explanation:** The report correctly identifies the extra bucket
`2023-03-24T08:00:00Z` as non-exempt and explains that zero-volume 5m placeholders at
`11:30`–`11:55` make the `11:00` 1h bucket partial. It then says the supplied 4h bar
“remains usable under the M3 exemption.” The alignment audit uses the same phrase. Strictly,
the bucket is **not** an M3-exempt bucket; it remains in the primary series because the
supplied 4h bar is itself present and usable under the general 4h usability rule. The M3
exemption governs only the twelve registered buckets.  
**Impact:** Documentation only. The count is disclosed, the sensitivity excludes only the
twelve registered buckets, and no verdict depends on the wording. A reader could incorrectly
infer that the extra bucket is covered by M3.  
**Proof status:** Proved by direct text comparison and by the alignment JSON
(`complete_buckets=7649`, `exempt_buckets=12`, one non-exempt gap-affected bucket).  
**Historical-conclusion impact:** None.  
**Evidence:** Report sentence at lines 255-258; alignment audit §4.1;
`alignment_audit.json` bucket counts.  
**Recommended resolution:** Future notes should say the extra bucket is “usable under the
general supplied-4h rule” and is “not part of the twelve M3-exempt buckets.” Do not rewrite
the historical report.

### L-007 — `rho=1` sensitivity uses the arithmetic mean cluster size, not the exact Kish weight

**Severity:** OBSERVATION  
**Location:** `stage2j_census/stats.py:294-329`; shared
`SHARED_CENSUS_PROTOCOL.md:340-360`.  
**Requirement:** The shared protocol defines
`n_eff(rho) = N / (1 + (m̄ - 1) * rho)` with `m̄` the mean cluster size, and asks for the
exact Kish value alongside it for `rho = 1`. The exact Kish value uses cluster sizes
weighted by themselves, not the unweighted arithmetic mean.  
**Explanation:** The implementation sets `mean_size = population / k_nonempty` and uses that
arithmetic mean in the `rho` sensitivity. The exact Kish `n_eff` is computed separately from
`Σ n_k^2`. For unequal cluster sizes, the `rho=1` sensitivity therefore does not equal the
exact Kish value. The report's `note` field explains this distinction and both values are
reported.  
**Impact:** Presentation only. The concentration verdict uses `design_effect = N /
n_eff_kish`, not the `rho` sensitivity, so the screen is unaffected. The sensitivity is not
an estimate of dependence and is not used to claim effective sample size.  
**Proof status:** Proved. Synthetic sizes 5 and 1 give exact Kish `36/26 = 1.384615`, design
effect `6/(36/26) = 4.333333`, and `rho=1` sensitivity `6/(1+(3-1)*1) = 2.0`; the last two
values differ.  
**Historical-conclusion impact:** None.  
**Evidence:** `stats.py:294-329`; synthetic checks “rho=1 uses mean non-empty size, not
exact Kish” and “rho=1 value differs from exact Kish for unequal clusters”.  
**Recommended resolution:** Either define `m̄` explicitly as the arithmetic mean of
non-empty cluster sizes, or use the size-weighted mean so that `rho=1` reproduces exact
Kish. Keep the exact Kish value separately reported in either case.

### L-008 — Recorded B `retest_timeout=0` is not independently reproduced

**Severity:** OBSERVATION  
**Location:** `docs/research/stage2j/machine_readable/candidate_b_census.json` (`labels`);
`stage2j_census/candidate_b.py:150-166`.  
**Requirement:** If no touch occurs in the six-bar window `e+1 .. e+6`, the episode must end
with `retest_timeout`.  
**Explanation:** The recorded B label table contains `retest_timeout=0`, while
`retest_too_deep=72`, `structure_broken=8`, `resumption_timeout=3`, and
`regime_not_permitted=322`. A zero timeout count is plausible if every attempt that reaches
the touch phase touches within six bars, but confirming the historical incidence would
require rerunning the detector on the development data, which Stage 2L is prohibited from
doing. The synthetic harness now proves that the timeout branch emits `retest_timeout` when
no touch occurs; it does not prove that the historical count is zero.  
**Impact:** No identified effect. The count is a recorded output and the branch is present
and correct under controlled input.  
**Proof status:** Mechanism verified; historical incidence not independently reproduced.  
**Historical-conclusion impact:** None.  
**Evidence:** Recorded B labels; synthetic checks “B no touch in window yields no S6” and
“B no touch in window carries retest_timeout”.  
**Recommended resolution:** A future authorised reproduction can confirm the historical zero.
No Stage 2L action is required.

### L-009 — Determinism claim has no retained second-run artifacts

**Severity:** MINOR  
**Location:** `docs/research/stage2j/FREEZE_MANIFEST.json`
(`census_execution.determinism_verified`, `determinism_method`);
`stage2j_census/run_census.py:408-420`.  
**Requirement:** The audit is asked to assess reproducibility and provenance. A determinism
claim should be checkable from retained evidence or be labelled as unverified.  
**Explanation:** Stage 2J records that two runs with identical code and HEAD produced
byte-identical analytical JSON, with `resources.json` differing by design because it records
wall time and RSS. No second-run artifacts or digests are retained. The audit cannot rerun
the census under its prohibitions, so the claim cannot be independently checked. The code is
deterministic by construction in the ordinary sense (sorted keys, fixed serialisation), but
that is not the same as retained two-run evidence.  
**Impact:** Reproducibility evidence gap. It does not indicate that the recorded outputs are
wrong, and no verdict depends on the determinism claim.  
**Proof status:** Not independently verified.  
**Historical-conclusion impact:** None.  
**Evidence:** Stage 2J manifest `census_execution` block; `census_run.json`
`deterministic_serialization` with `excluded_from_identity: ["resources.json"]`.  
**Recommended resolution:** Future census runs should retain both run manifests or a
determinism receipt with per-file digests, or state that determinism was observed once and
is not independently evidenced.

### L-010 — Code hash omits `freeze_verify.py` and test files

**Severity:** MINOR  
**Location:** `stage2j_census/run_census.py:31,44-54`;
`docs/research/stage2j/machine_readable/census_run.json` (`code.files`).  
**Requirement:** The recorded code identity should cover code that can affect the census or
its preflight verification.  
**Explanation:** `run_census.py` imports `run_preflight` and `git_state` from
`stage2j_census/freeze_verify.py`, but `freeze_verify.py` is not in `CODE_FILES`. The code
hash covers the nine analytical and loader files, not the preflight/hash-verification logic
and not any test file. A change to preflight behaviour would therefore not change the
recorded `code_sha256`, even though it could change whether a run is admitted.  
**Impact:** Incomplete code identity. The analytical code that produces counts is covered;
the verification wrapper is not. No observed effect: all Stage 2J preflight and integrity
checks passed.  
**Proof status:** Proved by direct comparison of the imported module and the `CODE_FILES`
tuple.  
**Historical-conclusion impact:** None observed.  
**Evidence:** `run_census.py:31` import; `CODE_FILES` at lines 44-54; `census_run.json`
`code.files` list.  
**Recommended resolution:** Add `stage2j_census/freeze_verify.py` (and any audit-critical
test or harness commit) to the hashed code set in a future census, while keeping the
historical identity record unchanged.
