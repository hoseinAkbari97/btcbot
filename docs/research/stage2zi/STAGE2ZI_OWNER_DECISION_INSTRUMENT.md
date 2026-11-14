# Stage 2ZI — Owner Decision Instrument

**Status:** **UNSIGNED DRAFT. NOT A DECISION.** Every owner field below is blank. No selection is ratified by
this document, and none may be inferred from its existence.
**Instrument:** the seven proposed selections for `2ZD-0`, `2ZD-1`, `2ZD-2`, `2ZD-3`, `2ZD-4`, `2ZD-5`, and
`Q-1`, presented in the form an owner decision takes.
**Source instrument:** `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`, SHA-256
`042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`.
**Proposals from:** `docs/research/stage2zh/STAGE2ZH_PROPOSED_DECISION_RECORD.md`, examined by
`docs/research/stage2zi/STAGE2ZI_INDEPENDENT_VALIDATION_REPORT.md`.

## 1. What this instrument is

A form. It restates the packet's seven decisions with a proposed value beside each, so that the owner can record
an actual decision without drafting one. The proposed values are agent recommendations; the fields are the
owner's. **A filled proposal is not a decision; only a completed owner field is.**

## 2. What this instrument is not, and what it is separate from

| it is not | because |
|---|---|
| the protocol amendment | `STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` changes §8.2. This instrument changes no text and adopts nothing in that instrument |
| the custodian appointment | `STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` appoints a party. Selecting `2ZD-4`'s custodian field **recommends** an appointee; it does not appoint one |
| a Gate 2 opening | Gate 2 needs its own dated authorization, and under `C-N` it has no hypothesis to register |
| a research authorization | no selection here authorizes data access of any kind, and the reserved blocks stay closed |
| a claim that the owner has read anything | the packet's own "I have read this packet" field is blank and stays blank |

**Separation, stated from this side.** Adopting the amendment ratifies nothing here; signing here adopts no
amendment. A single signature that names only one of the three instruments adopts only that one. If the owner
intends a single act, the statement must say so and name all three by path and hash.

## 3. The seven decisions

Proposed values are recommendations. The `owner selection` column is the decision, and it is empty.

| # | decision | proposed value | packet reference | owner selection |
|---:|---|---|---|---|
| 1 | 2ZD-0 — path | **C** — resolve interpretation and decisions first | §5 | `________________` |
| 2 | 2ZD-1 — reserved-data reading | **R-b** — any byte contact is a read; requires the amendment | §6.1 | `________________` |
| 3 | 2ZD-2 — primary candidate | **C-N** — neither B nor D selected | §6.2 | `________________` |
| 4 | 2ZD-3 — sizing rule | **S-1** — `R` shrinks when the `$2,500` cap binds | §6.3 | `________________` |
| 5 | 2ZD-4 — dependence and custody | the seven values in §4 below | §6.4 | `________________` |
| 6 | 2ZD-5 — `σ`, `DE`, `p_exec` route | **E-2** — labelled pre-registered assumptions | §6.5 | `________________` |
| 7 | Q-1 — cost basis | retain `26 bp` as an unmeasured, labelled Binance proxy | **not a packet field** — introduced by 2ZG §10; see finding `X-4` | `________________` |

Row 7 needs a word of warning: `Q-1` appears nowhere in the 2ZD packet. It was raised by Stage 2ZG, which cited
it as "packet §7, issue `I-2`", and the packet's §7 is a table of artifact hashes with no issue list. The
selection is therefore an owner statement about a question the packet did not ask, and it is legitimate only as
a confirmation of the `26 bp` label, which is what it is written as.

## 4. Decision 2ZD-4 — the seven values, with their qualifications

Preserve these values exactly. The qualifications are part of the value: a registration that cites `10,000`
without the "comparability choice" label, or `14 days` without "convention", would overstate the evidential
base.

| # | field | proposed value | required qualification | owner value |
|---:|---|---|---|---|
| 1 | episode definition | maximal contiguous 4 h `budget_ok` run containing the signal instant | mandated by the frozen eligibility rule; dependence adequacy **conditional** on an exit policy | `________________` |
| 2 | block length | 14 calendar days | **convention**, from Stage 6; not derived from the data or the MME | `________________` |
| 3 | resample count | 10,000 | a **comparability choice**, explicitly not a protocol mandate | `________________` |
| 4 | seed | `20240101` | a **reproducibility choice**; arbitrary by construction | `________________` |
| 5 | embargo | 90 calendar days at each boundary | **derived** from `540 × 4 h`; gives 91 development blocks, and consumes 180 of 792 reserved days | `________________` |
| 6 | custodian | the human owner, under the logged custody procedure | a **recommendation**; appointment requires the separate instrument and explicit affirmation | `________________` |
| 7 | opening condition | after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only, once, logged | consistent with §2.2 and §8.8; the audit condition is the protocol's own sequence made explicit | `________________` |

**Do not read this table as a claim of statistical adequacy.** Six values are usable as proposed; none is
invented, and none was fitted to a design effect or an outcome. Two of the seven rest on a single prior
recommendation, and one creates a role that the governing text does not contain.

## 5. Consequences of `C-N`, if it is selected

**Neither candidate is selected.** Candidate B and candidate D remain frozen at `v2.0.0` with their
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` verdicts untouched. Neither is promoted, revived, or replaced,
and no third candidate is created to fill the gap.

| consequence | stated plainly |
|---|---|
| Gate 2 cannot be registered | protocol §5.2 input #1 is a hypothesis; `C-N` supplies none, and §5.3 requires the registration to be complete |
| the hypothesis input is unresolved **by choice** | this is a decision, not an omission and not a missing reply |
| Gate 2 is unauthorized **and** unregistrable | the first is a standing prohibition, the second is a new fact created by this selection |
| no strategy-design work is authorized | not by `2ZD-0 = C`, not by `C-N`, and not by anything in this package |

**On the exit and holding policy.** The missing exit rule is **not** the only remaining obstacle while `C-N`
stands. It matters only if a hypothesis is later selected, because it is a Gate 2 input #5 for a registration
that does not exist. Listing it as "the one thing blocking Gate 2" while no hypothesis is named would invert the
order of the obstruction. Both are open; the hypothesis slot is the one that is open first.

**What `C-N` is not.** It is not a vote against either candidate's evidence, and it does not reopen either
verdict. It is a refusal to register a hypothesis now, which is a legitimate option in the packet (§6.2) and does
not breach D-11, because a rule capping primaries at one is satisfied by zero.

**Owner statement (verbatim), if any:** `________________`
**Conditions or qualifications:** `________________`
**Effective date (UTC):** `________________`

A blank row is not a decision. Selecting some rows and not others ratifies only the selected rows, and leaves the
rest exactly as they are.
