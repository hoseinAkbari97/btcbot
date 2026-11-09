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
