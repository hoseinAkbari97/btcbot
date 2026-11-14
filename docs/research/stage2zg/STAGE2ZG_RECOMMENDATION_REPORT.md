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

## 3. How the report separates three kinds of statement

- **[F] source fact** — quoted or counted from a committed document, with its section.
- **[R] reasoning** — an inference from those facts, stated so it can be argued with.
- **[REC] recommendation** — a choice proposed for the owner, which binds nobody until ratified.

A recommendation is never presented as a finding. Where a fact undercuts a recommendation, the report says
so in the same section rather than in a footnote.

## 4. Decision 2ZD-0 — recommended: `C`

**[F]** The packet offers four paths (§5). Path C resolves "the protocol interpretation and owner decisions
first" and authorizes "the §8.2/D-12 ruling plus the four non-data Gate 2 decisions, and a Gate 2
specification reflecting them".

**[F]** Four of its six blockers need no data: B-1 (candidate), B-2 (cap against tight stops), B-3 (the
hashing question), B-5 (the dependence numbers). B-4 needs a route rather than data if `E-2` is adopted (§9).
**[R]** Path C is the only option that can close B-1, B-2, B-3, and B-5 without a guess, and it closes them
before any outcome exists, so nothing it settles can be informed by one.

**[REC] `2ZD-0 = C`.** It authorizes governance resolution and a Gate 2 *specification*, not Gate 2.

**Rejected:** `A` — Gate 2 cannot pass today (2 of 16 inputs satisfied), so A forces guesses or an implicit
amendment. `B` — builds the template while leaving the interpretation gap open. `D` — closes nothing;
legitimate only if the owner intends to pause.

## 5. Decision 2ZD-1 — recommended: `R-a`

**[F]** Protocol §8.2 requires that "the exact dates and hashes are frozen at Gate 2". D-12 (register) and
addendum §10.4 forbid reading "any validation or OOS row" before its gate. Neither text defines "read", and
neither mentions hashing.

**[F]** The two requirements cannot both hold for a hash over reserved bytes unless hashing is not a read:
option `R-b` makes §8.2 permanently unsatisfiable without an amendment (packet §6.1, consequence column).
**[R]** Hashing is whole-block and non-interpretive: SHA-256 consumes bytes and yields a digest from which no
row can be reconstructed. D-12 uses "read" in the sense of inspecting content — the sense in which §8.2 asks
for a hash it would forbid obtaining by inspection.

**[REC] `2ZD-1 = R-a`**, with three conditions: hash-only, streamed without decoding; logged with date, path,
block, bytes, and digest; and recorded in the Gate 2 manifest itself. No row, count, summary, or statistic may
be derived from the stream, and no digest may be compared across blocks until the relevant gate opens.
