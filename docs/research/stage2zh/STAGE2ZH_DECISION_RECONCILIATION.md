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
