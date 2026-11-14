# Stage 2ZH — Methodology Validation

**Scope:** the seven values proposed for decision 2ZD-4, tested one by one against the frozen methodology.
**Status:** validation only. A value marked *supported* is supported as a proposal; none is adopted.

## 1. Four support tiers

| tier | meaning |
|---|---|
| **mandated** | a governing document requires this value, or the only value consistent with it |
| **derived** | computed from a frozen constant, with the arithmetic shown |
| **precedent** | fixed in a prior frozen artifact; defensible, but nothing requires it |
| **unsupported** | no source; must be left unresolved |

A value being *precedent* is not a weakness — the instruction forbids inventing values, and preferring a
recorded convention over a fresh guess is what that instruction asks for. But the tier must be stated, because
"supported" would otherwise blur a requirement and a habit.

## 2. What is under test

| # | field | proposed value |
|---|---|---|
| 1 | episode definition | maximal contiguous 4 h `budget_ok` run |
| 2 | block length | 14 calendar days |
| 3 | resample count | 10,000 |
| 4 | seed | `20240101` |
| 5 | embargo | 90 calendar days at each boundary |
| 6 | custodian | the human owner, under logged custody |
| 7 | opening | after the Gate 2 freeze and Gate 4 audit, at Gate 5 only, once |

## 3. Field 1 — episode definition: **mandated**

**[F]** Candidate D assigns each signal "to the maximal `budget_ok == True` 4 h run containing the session signal
instant", with 212 runs in the development interval (`CANDIDATE_D_CENSUS_REPORT.md` §6). The 4 h volatility
budget is a frozen eligibility rule of the specification (`CANDIDATE_D_SPEC.md` §6).

**[R]** The cluster unit is not a free choice under D-09 option C: the registered dependence model must be the
model whose design effect the pre-registration cites, and the recorded diagnostics were computed on this unit.
Using a different episode at Gate 2 would silently change the quantity `DE` refers to.
