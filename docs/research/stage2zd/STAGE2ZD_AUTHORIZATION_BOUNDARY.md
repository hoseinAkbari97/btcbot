# Stage 2ZD — Authorization Boundary

**Stage:** 2ZD (decision preparation only)
**Date:** 2026-11-14 (UTC)
**Purpose:** state exactly what this stage did, what it did not do, and the boundary any future
authorization must respect.
**Status of this document:** a boundary statement. **It authorizes nothing.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital
> return, and not a sizing recommendation.**

---

## 1. What Stage 2ZD was authorized to do

The owner's Stage 2ZD instruction (2026-11-14) authorized exactly:

1. an independent audit of the Stage 2ZC Gate 1 result against the actual repository files;
2. reconstruction of the exact Gate 2 requirements from the adopted text;
3. a Gate 2 readiness assessment;
4. a comparison of four possible next paths and one recommendation;
5. a blank-field owner decision packet;
6. documentation, hash manifests, a commit, and a push of Stage 2ZD material only.

It authorized **nothing** beyond documentation, audit of already-recorded evidence, and decision
preparation.

---

## 2. What Stage 2ZD did

| activity | performed | scope |
|---|---|---|
| read committed repository documents | **yes** | governing sources, Stage 2ZC artifacts, predecessor manifests |
| recompute SHA-256 of committed files | **yes** | Stage 2ZC artifacts, predecessor manifests, governing documents |
| verify predecessor manifest self-hashes and referenced hashes | **yes** | Stage 2Y, 2Z, 2ZA, 2ZB, 2ZC, 2P, 2M, 2E-v2 |
| inspect `DEV_BLOCK_VALIDATION.json` | **yes** | read the committed JSON, no dataset row |
| inspect the dataset manifest | **yes** | `backend/data/datasets/manifest.json`, metadata only |
| inspect dataset file sizes | **yes** | `ls -l` metadata only |
| rerun the Stage 2ZC validation script | **no** | not necessary; existing evidence sufficient |
| re-stream any dataset file through SHA-256 | **no** | deliberately avoided to prevent further non-development byte contact |
| decode any validation or OOS row | **no** | **0** |
| run a census, backtest, simulation, or parameter fit | **no** | **0** |
| compute a signal, indicator, return, expectancy, or P&L | **no** | **0** |
| measure cost, spread, depth, fills, slippage, latency, or liquidity | **no** | **0** |
| contact a venue or call an API | **no** | **0** |
| place, modify, or cancel an order | **no** | **0** |
| change `26 bp`, any D-01…D-15 value, any A-1…A-4 value, or any verdict | **no** | **0** |
| modify any Stage 2ZC artifact or frozen predecessor | **no** | verified unchanged at commit time |

---

## 3. What Stage 2ZD did *not* authorize, and what remains unauthorized

| item | status after Stage 2ZD |
|---|---|
| Gate 0 | **NOT PASSED** — unchanged |
| Gate 1 | **PASSED — research leg only**, as recorded by Stage 2ZC — unchanged |
| Gate 2 | **NOT AUTHORIZED** |
| Gate 3 census | **NOT AUTHORIZED** |
| Gate 4 audit | **NOT AUTHORIZED** (and no reviewer identified) |
| Gate 5 validation/OOS performance | **NOT AUTHORIZED** |
| Gate 6 decision | **NOT AUTHORIZED** |
| validation/OOS access of any kind | **NOT AUTHORIZED** |
| measured-cost collection (O-3) | **NOT AUTHORIZED** |
| execution measurement (O-4 / `C-6` route) | **NOT AUTHORIZED** |
| real-capital sizing | **NOT AUTHORIZED**; T-4 remains deferred |
| paper or live trading | **NOT AUTHORIZED** |
| changing D-01…D-15 or A-1…A-4 | **NOT AUTHORIZED** |
| revisiting the T-4 deferral | **NOT AUTHORIZED** |

---

## 4. Prerequisites for each future activity

The table states, for each activity, what must be true before it could be authorized. It does not
authorize any of them.

| activity | needs a new owner authorization | reads market data | outcome access | needs owner decisions | needs external evidence |
|---|---|---|---|---|---|
| Stage 2ZD commit/push (this stage) | no — within this instruction | no | no | no | no |
| Path C interpretation stage | **yes** | no | no | **yes** | no |
| Path B Gate 2 specification | **yes** (or as an output of C) | no | no | **yes** — C's decisions | no |
| Gate 2 execution | **yes** | dev only | **no** | yes — all six blockers | possibly `σ`/`DE` |
| development-block census (`σ`, `DE`) | **yes** | **yes**, dev only | no | yes | no |
| `p_exec` measurement | **yes** (and `C-6` must be resolved) | yes | no | yes | yes |
| Gate 3 census | **yes** | **yes**, dev only | no | no | cost model from Gate 1 |
| Gate 4 audit | **yes** | no | **no**, unless scoped | **yes** — reviewer | no |
| Gate 5 performance | **yes** | validation + one OOS look | **yes** | yes | no |
| Gate 6 decision | **yes** | no | no | yes | no |
| documentary venue evidence (already collected) | no — a collection act, not a gate | no | no | no | already dated |
| spread/depth sampling | **yes** | yes | no | yes | quotes |
| execution measurement | **yes** — a new decision | yes | no | yes | executions |
| real capital | **yes** — and Gate 0 must pass | yes | yes | yes | yes |

---

## 5. The boundary any next authorization must respect

Any next authorization — whichever path the owner selects — must satisfy all of the following. This
section is the operative boundary.

### 5.1 It must be explicit

1. It must **name the stage** and the gate it concerns.
2. It must **state its scope** in terms that can be checked after the fact.
3. It must **state its stop condition** — what the stage does when it cannot complete.
4. It must **not** rely on silence, ambiguity, or the mere commissioning of a prior stage as
   authorization. Reading this document, or receiving a Stage 2ZD commit, is not a decision.

### 5.2 It must preserve the record

5. It must **not** change Gate 0's status, the Stage 2ZC verdict, any frozen predecessor, any D-01…D-15
   value, any A-1…A-4 value, or `26 bp`.
6. It must **not** retroactively reinterpret a completed stage.
7. It must **record** any interpretation decision in the pre-registration and disclose it in the
   report (protocol §10.4).

### 5.3 It must preserve the one-look protection

8. It must **not** read, decode, or summarize any validation or OOS row before the gate that owns it.
9. If it computes a block hash, it must **state which reading** of §8.2/D-12 it applies and **log**
   the contact.
10. It must **not** "check the pipeline" against the confirmatory blocks.

### 5.4 It must preserve statistical integrity

11. It must **not** choose `σ`, `DE`, `p_exec`, an episode definition, a block length, or an embargo
    length after seeing an outcome or a design effect.
12. It must **not** select a block length that minimises `DE`.
13. It must **not** test more than one primary hypothesis within a stage (D-11).
14. It must **not** substitute a measured cost for `26 bp` without the `O-3` authorization.

### 5.5 It must respect real-capital separation

15. It must **not** treat a research-leg result as execution feasibility, a real-capital return, or a
    sizing recommendation.
16. It must **not** revisit T-4 or size real capital.
17. It must **not** pass Gate 0.

---

## 6. Activity classes that are never authorized by implication

Some activities are so consequential that no inference from a prior stage may authorize them. Each
requires an explicit, separate owner decision:

- reading any validation or OOS row;
- measuring cost, spread, depth, fills, slippage, latency, or liquidity;
- contacting a venue or placing any order;
- running a census, backtest, simulation, or parameter fit;
- selecting a candidate or a parameter;
- changing a threshold or a verdict;
- sizing real capital;
- passing Gate 0.

Commissioning Stage 2ZD, reading this file, or merging the Stage 2ZD commit does **not** authorize any
of them.

---

## 7. Integrity statement

1. This boundary statement was written from the actual repository and the actual Stage 2ZD work.
2. It records what was done, not what was intended.
3. It records what remains unauthorized, not what would be convenient.
4. It authorizes nothing.
5. Gate 0 remains **NOT PASSED**; Gate 2 remains **NOT AUTHORIZED**; T-4 remains deferred.
