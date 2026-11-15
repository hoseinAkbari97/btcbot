# Stage 2ZK — Owner Decision Record

**Decision ID:** the seven Stage 2ZI owner selections — `2ZD-0`, `2ZD-1`, `2ZD-2`, `2ZD-3`, `2ZD-4`, `2ZD-5`, `Q-1`
**Status:** **RECORDED — the seven selections are the owner's decisions.** The owner's message names no instrument
path or hash and carries no date; that single formality limitation is disclosed in §5, with a cure offered.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word, value, date, condition, or signature is
added, removed, or reordered.
**Instrument decided:** `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md`
**Instrument SHA-256:** `c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232` (10082 bytes)
**Source packet:** `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`
**Source packet SHA-256:** `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42` (14986 bytes)
**Date recorded:** 2026-11-15 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and not a
> sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner stated: *"I agree with your recommendation about decisions and those are my choices."* Read against the
seven selections proposed immediately before it, this is an affirmative decision on all seven, and this record fixes
them as the owner's choices. No selection here authorizes data access, research, or Gate 2. Under `2ZD-2 = C-N` no
primary hypothesis is selected, so Gate 2 remains **NOT AUTHORIZED** and **unregistrable**. The owner's message names
no instrument path or hash and carries no date; that single limitation is disclosed in §5 and does not change any
decision, because the hash condition exists to prevent post-decision text substitution and the hash is independently
re-verified in §5.3. The same owner instruction also accepted the recommendation to adopt the Stage 2ZI protocol
amendment; that separate act is assessed in `STAGE2ZK_PROTOCOL_ADOPTION_RECORD.md` and is **not** recorded as complete.

---

## 1. Owner statement (verbatim)

Recorded exactly as supplied. No word, punctuation mark, capitalisation, or date was added, removed, or reordered:

```
I agree with your recommendation about decisions and those are my choices.
```

| field | value |
|---|---|
| words | 12 |
| characters | 74 (including the internal spaces and the final period) |
| punctuation added | none |
| provenance | the owner's instruction in the Stage 2ZK session, immediately after the seven selections were proposed |
| date carried by the message | **none** — the message has no timestamp; the recording date is 2026-11-15 (UTC) |
| agent-added words | none |

The message states no scope of its own; its object is the seven selections presented immediately before it, which
are reproduced in §2 exactly as proposed. §5 assesses the exchange against the decision instrument's own standard.

**The separate adoption sentence.** The same owner instruction also accepted the recommendation to adopt the Stage 2ZI
protocol amendment. It is recorded here only as reported, in the owner's own terms as conveyed, and is assessed
separately in `STAGE2ZK_PROTOCOL_ADOPTION_RECORD.md`; no adoption wording is invented here.

---

## 2. The seven selected decisions

Recorded exactly as listed in the owner instruction. Each value is the one proposed in the Stage 2ZI owner decision
instrument §3; the owner added no qualification and removed none.

| # | decision | owner's choice | packet reference | practical consequence |
|---:|---|---|---|---|
| 1 | `2ZD-0` — path | **C** — resolve the protocol interpretation and owner decisions first | §5 | keeps work on governance, not data; authorizes no research |
| 2 | `2ZD-1` — reserved-data reading | **R-b** — any byte contact with a reserved block is a read | §6.1 | the analyst may not hash, stream, or inspect reserved bytes; operative only after the amendment is adopted |
| 3 | `2ZD-2` — primary candidate | **C-N** — neither candidate B nor candidate D selected | §6.2 | Gate 2 cannot be registered; both candidates stay failed and frozen |
| 4 | `2ZD-3` — sizing rule | **S-1** — `R` shrinks when the `$2,500` cap binds | §6.3 | keeps every per-trade loss at or below `1R` inside the cap; supports no frequency or profitability claim |
| 5 | `2ZD-4` — dependence and custody | accept all seven proposed values, preserving their qualifications (§3 below) | §6.4 | fixes the dependence and embargo parameters; the custody field remains a recommendation, not an appointment |
| 6 | `2ZD-5` — `σ`, `DE`, `p_exec` route | **E-2** — labelled pre-registered assumptions with sensitivity ranges | §6.5 | no data access; the values stay assumptions, never estimates |
| 7 | `Q-1` — cost basis | retain `26 bp` strictly as an unmeasured Binance proxy assumption | **not a packet field** — introduced by Stage 2ZG; see finding `X-4` | keeps a planning label, not a measurement; no `cost_R` is computed from it |

**Two qualifications on the list itself, preserved.**

- Row 7 (`Q-1`) is not a Stage 2ZD packet field. The packet contains no `Q-1`, no issue `I-2`, and no issue list in
  its §7 (finding `X-4`). The selection is therefore an owner statement about a question the packet did not ask, and
  it is recorded strictly as a confirmation of the `26 bp` label.
- Row 5 (`2ZD-4`) is a **superset**: the packet asks for five fields, and the accepted proposal supplies seven,
  adding the resample count and the seed (finding `X-5`). The addition is disclosed and does not narrow the packet's
  five fields.

