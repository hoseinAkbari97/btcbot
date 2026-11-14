# Stage 2ZH — Decision Reconciliation

**Stage:** 2ZH (decision reconciliation and governance amendment preparation)
**Date:** 2026-11-14 (UTC)
**Status:** **reconciliation and drafts only. No recommendation here is ratified, and no amendment is adopted.**
**Relation to Stage 2ZG:** this stage evaluates a *changed* recommendation set against the same authoritative
sources, and records where it agrees with 2ZG, where it departs, and what the departure costs.

## 1. Starting state, verified

| item | expected | observed |
|---|---|---|
| branch | `main` | `main` |
| HEAD | `61b6438d44bfe6145391ad542f47c79495e8f4bb` | matched, equal to `origin/main` |
| worktree | clean | clean |
| 2ZG report | present | `09d35c30…bf99c`, 21,357 bytes |
| 2ZG decision record | present | `e3d3dd08…ee3258`, 6,366 bytes |
| 2ZG boundary | present | `b3c8fc95…0c06a8`, 5,159 bytes |
| 2ZG manifest | present | `ae55e362…926736`, self-hash `3d7830aa…cf738a`, verified |

The four Stage 2ZG hashes were recomputed from current bytes and match the values reported at the end of that
stage. The Stage 2ZD manifest's canonical self-hash and its six deliverable hashes were re-verified in Stage
2ZG and are not re-derived here; this stage reads no dataset file.

## 2. Labels used in this document

- **[F]** verified source fact, quoted or counted, with its section.
- **[CALC]** arithmetic shown in full, reproducible from the stated inputs.
- **[REC]** the delegated recommendation under evaluation.
- **[OPEN]** unresolved; needs evidence or a decision that does not exist yet.
- **[OWNER]** a formal owner act is required; the agent may draft, never perform.

## 3. What changed from Stage 2ZG, and what it costs

| decision | 2ZG | 2ZH proposed | change |
|---|---|---|---|
| 2ZD-0 | `C` | `C` | none |
| 2ZD-1 | `R-a` | `R-b` | a ruling becomes an amendment |
| 2ZD-2 | `C-D` | `C-N` | a candidate becomes no candidate |
| 2ZD-3 | `S-1` | `S-1` | none |
| 2ZD-4 | four values, custodian open | same values, owner as custodian | custody closes |
| 2ZD-5 | `E-2` | `E-2` | none |
| Q-1 | confirm `26 bp` | retain as labelled proxy | none |

Two of the three changes make the programme *stricter*, and both add work rather than remove it:

- `R-b` declines to settle a governance question by interpretation, and therefore requires a versioned
  amendment to the protocol before Gate 2 can freeze a split.
- `C-N` declines to register any hypothesis, and therefore leaves Gate 2 unable to pass even after everything
  else is settled.

Neither is a shortcut. Both are defensible; §5 and §6 say exactly what each costs.

## 4. Decision 2ZD-0 — `C`, unchanged

**[F]** Path C is "resolve the protocol interpretation and owner decisions first" and authorizes "the §8.2/D-12
ruling plus the four non-data Gate 2 decisions, and a Gate 2 specification reflecting them" (packet §5).

**[REC]** `2ZD-0 = C`, as in 2ZG. **Consistency check:** under `R-b` the "ruling" is delivered as a proposed
amendment rather than an interpretation, and under `C-N` the Gate 2 specification carries an empty hypothesis
slot. Path C's text accommodates both — it authorizes a resolution, not a particular mechanism — but the two
together mean Path C no longer produces a *registrable* Gate 2 package. It produces an amendment plus three
decisions plus a specification with a hole.

That is not a defect in `C`. It is the honest state after choosing `R-b` and `C-N`: two blockers (B-3, B-1)
move from "owner decision pending" to "owner decision made, consequence pending", and the consequence for B-1
is that Gate 2 stays blocked until a later candidate decision.

## 5. Decision 2ZD-1 — `R-b`, with one counter-argument recorded

**[F]** Protocol §8.2: "the exact dates and hashes are frozen at Gate 2". D-12 (register) and addendum §10.4:
no validation or OOS "row" may be read before its gate. The word "read" is nowhere defined.
