# Stage 2ZG — Delegated Decision Recommendations

**Stage:** 2ZG (delegated recommendation and formalization preparation)
**Date:** 2026-11-14 (UTC)
**Status:** **a recommendation package. Nothing in it is a decision, an authorization, or a signature.**
**Delegation:** the owner asked a delegated recommender for the best substantive choices; this report
carries those choices, tests each against the governing text, and records what it could not settle.

## 1. Starting state, verified

| item | expected | observed |
|---|---|---|
| branch | `main` | `main` |
| HEAD | `4fdddc7b92d3eadc136451e969afb70e180e3ea8` | matched, equal to `origin/main` |
| worktree | clean | clean |
| 2ZF validation report | present | present, `f74054bc…63d3ff` |
| 2ZD packet | `042f0497…7fe8e42` | matched, 14,986 bytes |
| `docs/research/stage2zg/` | absent | absent |

## 2. Sources read for this report

Every recommendation below cites one of these; their hashes are in `FREEZE_MANIFEST.json` under
`governing_sources`.

- `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §5.2, §5.3, §8.2, §8.3, §8.4 — the registration inputs, the pass
  criteria, the three-block split, the embargo requirement, and the one-primary rule.
- `stage2m/OWNER_DECISION_REGISTER.md` D-02, D-08, D-09, D-10, D-11, D-12 — the adopted standards.
- `stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3.4 — the pre-specified dependence policy.
- `stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` §7.4, §9.2, §10.4 — the adopted
  controls that constrain this stage.
- `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md` §5, §6 — the decision text being recommended on.
- `stage2e_v2/CANDIDATE_D_SPEC.md` §2.2, §6, §8, §9 — candidate D's session, regime, cost, and non-overlap
  construction.
- `stage2j/CANDIDATE_B_CENSUS_REPORT.md` and `CANDIDATE_D_CENSUS_REPORT.md` §5, §6, §10 — the recorded
  counts, design effects, and verdicts.
- `stage2zc/` range-and-hash record, access log, and cost-assumption record — the only recorded data contact.
