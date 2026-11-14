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
