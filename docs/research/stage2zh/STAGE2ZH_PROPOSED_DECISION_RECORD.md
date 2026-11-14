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
