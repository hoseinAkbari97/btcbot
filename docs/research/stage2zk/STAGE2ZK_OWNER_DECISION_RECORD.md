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

---

## 3. Decision `2ZD-4` — the seven values, with their qualifications preserved

The owner accepted all seven proposed values. The qualifications are part of the value and are preserved exactly; a
registration that cites a value without its qualification would overstate the evidential base.

| # | field | value as accepted | qualification that is part of the value |
|---:|---|---|---|
| 1 | episode definition | maximal contiguous 4 h `budget_ok` run containing the signal instant | mandated by the frozen eligibility rule; dependence adequacy **conditional** on an exit policy that does not exist |
| 2 | block length | 14 calendar days | **convention**, from Stage 6; not derived from the data or the MME |
| 3 | resample count | 10,000 | a **comparability choice**, explicitly not a protocol mandate |
| 4 | seed | `20240101` | a **reproducibility choice**; arbitrary by construction |
| 5 | embargo | 90 calendar days at each boundary | **derived** from `540 × 4 h`; gives 91 development blocks and consumes 180 of 792 reserved days; contingent on the lookback staying in 4 h bars (finding `X-6`) |
| 6 | custodian | the human owner, under the logged custody procedure | a **recommendation only**; appointment requires the separate instrument and explicit affirmation — see `STAGE2ZK_CUSTODIAN_APPOINTMENT_RECORD.md` |
| 7 | opening condition | after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only, once, logged | consistent with protocol §2.2 and §8.8; the audit condition is the protocol's own sequence made explicit |

**This table is not a claim of statistical adequacy.** Six values are usable as accepted; none is invented, and none
was fitted to a design effect or an outcome. Two rest on a single prior recommendation, and one creates a role the
governing text does not yet contain.

---

## 4. What `C-N` means, recorded

`C-N` selects **neither** candidate. Candidate B and candidate D remain frozen at `v2.0.0` with their
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` verdicts untouched. Neither is promoted, revived, or replaced, and no
third candidate is created to fill the gap. Candidate substitution is not permitted.

| consequence | stated plainly |
|---|---|
| **no primary hypothesis is selected** | `2ZD-2 = C-N` supplies none; this is a decision, not an omission |
| Gate 2 cannot be **registered** | protocol §5.2 input #1 is a hypothesis, and §5.3 requires the registration to be complete |
| Gate 2 is unauthorized **and** unregistrable | the first is a standing prohibition; the second is a fact created by this selection |
| no strategy-design work is authorized | not by `2ZD-0 = C`, not by `C-N`, and not by anything in this record |

`C-N` is not a vote against either candidate's evidence and does not reopen either verdict. It does not breach D-11:
a rule capping primaries at one is satisfied by zero.

---

## 5. Formality assessment against the decision instrument's standard

The owner decision instrument §7 states the standard a valid statement meets: it identifies the document by path and
hash, states the decision in the owner's own words, carries a date, and is recorded verbatim without agent paraphrase.
The instrument's §2 adds that a single signature naming only one of the three instruments adopts only that one.

### 5.1 Condition by condition

| # | condition | how it is met | residual |
|---:|---|---|---|
| 1 | names the path and SHA-256 | the message confirms, without qualification, the seven selections proposed immediately before it, which name the instrument and its hash; the hash is independently re-verified in §5.3 | the owner's own words do not restate the hash — see §5.2 |
| 2 | states the decision in the owner's own words | *"those are my choices"*, read against the seven enumerated selections it answers; the message names no other option set | the seven option letters appear in the proposed list, not in the owner's words |
| 3 | carries a date | **2026-11-15** (UTC), the working-session date recorded for this stage; the owner's message carries no separate timestamp | none material |
| 4 | recorded verbatim | §1 reproduces the message exactly; no paraphrase is used as evidence | none |

### 5.2 The single disclosed limitation, and the cure

The owner's message does not itself name the path or the SHA-256. Read literally and in isolation, it would not
satisfy condition 1. This record does not conceal that. It treats the message as deciding the specific seven
selections it answers — which is what it is — and verifies the instrument's hash independently.

**Optional cure, available to the owner only.** If the owner wants the record to be self-contained under the strictest
reading, one dated line restating the instrument path and its SHA-256, alongside the word *ratify* (or *adopt*), is
sufficient. The agent will record it verbatim and append it to this record. Until and unless that happens, this record
stands as the decision record, and the decided content is the seven selections in §2–§3.

### 5.3 The instrument, verified at recording time

| field | value |
|---|---|
| path | `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md` |
| bytes | **10082** |
| SHA-256 | **`c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232`** |
| recorded in the Stage 2ZI manifest | `deliverables[1].sha256` and `deliverables[1].bytes` — both match |
| recomputed at recording time | matches the manifest |
| source packet hash | `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42` (14986 bytes) — matches the instrument's own §2 citation |

A later edit to either file would change its hash and void the corresponding binding in this record.

### 5.4 What was not done

No signature, identity, affirmation, or decision was created or inferred. No field in the Stage 2ZI owner decision
instrument was filled in: that instrument remains the historical decision form for what was proposed, with every
owner field blank. This record is a new, separately dated instrument; it edits nothing.



