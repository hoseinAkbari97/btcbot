# Stage 2ZH — Proposed Decision Record

**Status:** **PROPOSAL. NOT A DECISION. NOT RATIFIED. NO SIGNATURE, NO DATE, NO OWNER WORD.**
**Instrument:** `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`
**Instrument SHA-256:** `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`
**Supersedes in proposal only:** the Stage 2ZG record. Nothing in 2ZG was adopted, so nothing is revoked.

## 1. Standing of this record

Each line below is a delegated recommendation. The agent has written no date, signature, or owner statement, and
has completed no field of the packet's §9 block. Adoption requires a separate dated instrument naming the packet
and its hash; this record cannot become a decision by citation.

## 2. 2ZD-0 — path

| field | proposed value | status |
|---|---|---|
| selected path | `C` | recommendation, unratified |
| owner date, statement, signature | `—` | **not written by the agent** |

Effect if adopted: the amendment route, three sub-decisions, and a Gate 2 specification are authorised. Gate 2
is not.

## 3. 2ZD-1 — block-hash interpretation

| field | proposed value | status |
|---|---|---|
| selection | `R-b` — any byte contact with a reserved block is a read | recommendation, unratified |
| instrument required | adoption of `STAGE2ZH_PROTOCOL_AMENDMENT_DRAFT.md` as protocol §8.2.1 | **[OWNER]**, separately |
| condition | no reserved byte is hashed until that adoption is recorded | binding on this stage |

Disclosure carried into any ratification: until the amendment is adopted, §8.2's requirement that hashes be
frozen at Gate 2 has no compliant procedure, so Gate 2 cannot freeze its split. That is the intended consequence
of `R-b`, not an oversight.

## 4. 2ZD-2 — primary candidate

| field | proposed value | status |
|---|---|---|
| selection | `C-N` — no candidate registered now | recommendation, unratified |
| consequence | Gate 2 cannot name a primary hypothesis; B-1 stays open | stated, not hidden |

Both candidates remain frozen at `v2.0.0` with their `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` verdicts.
No threshold, population, or verdict is altered, and no third candidate is created.

## 5. 2ZD-3 — notional cap against tight stops

| field | proposed value | status |
|---|---|---|
| selection | `S-1` — `R` is set by the capped notional and shrinks | recommendation, unratified |
| condition | per-trade loss remains ≤ `1.00R`; the `$2,500` cap is never exceeded | arithmetic, verified |

Disclosed consequence: at a 2% stop, `R` falls to `$50`, `0.10R` to `$5`, and the `$250` target needs 50 trades
a year instead of 25. The evidence requirements are unchanged, the `150` floor is unchanged, and `T-5` remains
open.

## 6. 2ZD-4 — dependence, custody, and opening values

| parameter | proposed value | status |
|---|---|---|
| episode definition | maximal contiguous 4 h `budget_ok` run containing the signal instant | recommendation, unratified |
| block length | 14 calendar days | recommendation, unratified |
| resampling count | 10,000 | recommendation, unratified |
| seed | `20240101` | recommendation, unratified |
| embargo length | 90 calendar days at each boundary | recommendation, unratified |
| validation-split custodian | the human owner, under the logged custody procedure | recommendation, unratified; appointment is a separate owner act |
| when the split may be opened | after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only, once, logged | recommendation, unratified |

Support tier for each value is recorded in `STAGE2ZH_METHODOLOGY_VALIDATION.md` §10: one mandated, one derived,
three precedent, one a new role. Two disclosures belong with the selection — that 10,000 and the seed come from
a single prior recommendation rather than a protocol requirement, and that the custodian's digests cannot be
verified by the analyst under `R-b`.

## 7. 2ZD-5 — `σ`, `DE`, `p_exec` route

| field | proposed value | status |
|---|---|---|
| selection | `E-2` — labelled pre-registered assumptions with sensitivity ranges | recommendation, unratified |
| condition | declaration at Gate 2 registration; planning `DE` not taken from `3.933333` | recommendation, unratified |
