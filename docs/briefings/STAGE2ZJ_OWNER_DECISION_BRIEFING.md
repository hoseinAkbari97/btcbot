# Stage 2ZJ — Final Owner Decision Briefing

**Status:** read-only briefing. **Adopts nothing, signs nothing, appoints nobody, and changes no file outside this
one.** It sits outside the frozen Stage 2ZI instruments and outside the research-stage directories.

**Purpose:** let the owner make the outstanding Stage 2ZI decisions from one page, with the exact instruments,
hashes, and required statements in front of them.

**What was inspected (actual bytes, this session):**

| artifact | SHA-256 (recomputed) | bytes | matches manifest |
|---|---|---:|---|
| `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 | yes |
| `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md` | `c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232` | 10082 | yes |
| `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 | yes |
| `docs/research/stage2zi/STAGE2ZI_INDEPENDENT_VALIDATION_REPORT.md` | `fe7a3fde126b3ff942654943204b543b79136ba9c5c24aa0f9e84d81af18d3e8` | 20154 | yes |
| `docs/research/stage2zi/STAGE2ZI_AUTHORIZATION_BOUNDARY.md` | `4cb3cd86987edc22f591656fd30bc916a7d4b23efd4a67c3b9f7935a1a259f39` | 6871 | yes |
| `docs/research/stage2zi/FREEZE_MANIFEST.json` (self-hash) | `6a9694d66ae7af5b0a9195bd83fda02408fc06332e69f806749b85e5b769c84c` | — | yes |

All five deliverable hashes and byte counts match `FREEZE_MANIFEST.json`; the manifest self-hash recomputes to the
stored value. The governing sources match the manifest as well: `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`
`be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058`, `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`
`042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`, and `stage2zg/STAGE2ZG_RECOMMENDATION_REPORT.md`
`09d35c3000e9ef9589bd153c26204da244973ffb774db99eb06a01ddf9cbf99c`. Nothing in the Stage 2ZI set has changed since it
was frozen.

## 1. The amendment — version, hash, and what adoption requires

**Instrument:** `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md`
**SHA-256:** `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` (18069 bytes)
**Status:** adoption-ready draft. **Not adopted. Not effective.**

- **Version created:** `2.0.0`, class **major** (protocol §10.2, "a major version changes a rule").
- **Finding `V-1`:** the protocol carries **no version string** anywhere in its 896 lines. `2.0.0` is therefore
  *assigned* as "the first versioned form of this protocol", **not** an increment from a prior `1.x`. An adopting
  statement that presents it as an increment would describe a history that does not exist.
- **What it changes, and only this:** the final sentence of §8.2 ("The exact dates and hashes are frozen at Gate 2")
  is replaced, and a new §8.2.1 (`A-1`–`A-5`) is inserted. `A-5` states non-derogation: nothing else moves.
- **Trigger:** proposed selection `2ZD-1 = R-b` — any byte contact with a reserved block is a read. Under `R-b`,
  §8.2's hash requirement has no compliant procedure until this amendment supplies one (the custodian).

**The adopting statement must, at minimum (amendment §8):** (1) identify the instrument by path and by the SHA-256
above; (2) state **adopt**, or adopt with the revisions listed; (3) carry a UTC date, which becomes the effective
date (§3); (4) record the version as `2.0.0` and acknowledge `V-1`; (5) acknowledge `Y-1` and `Y-2` as recorded
pre-amendment deviations, **without grandfathering them unless the statement says so explicitly and in its own
words**; (6) be recorded verbatim, without agent paraphrase, in a record created for that purpose; (7) be accompanied
by a manifest for the amended protocol text carrying SHA-256 hashes, byte counts, and a canonical self-hash.

**Two consequences stated plainly.** A statement that does not name the hash adopts nothing (addendum §14.1). And
because §10.3 forbids editing a frozen artifact before adoption (finding `V-2`), the amended protocol **text** is not
changed by this instrument: adoption has to authorize that text change as a separate step.

## 2. The owner decision instrument — hash and the seven proposed selections

**Instrument:** `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md`
**SHA-256:** `c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232` (10082 bytes)
**Status:** unsigned draft. Every owner field is blank; a filled proposal is **not** a decision.

| # | decision | proposed value | practical consequence |
|---:|---|---|---|
| 1 | `2ZD-0` — path | **C** — resolve interpretation and decisions first | keeps work on governance, not data; authorizes no research |
| 2 | `2ZD-1` — reserved-data reading | **R-b** — any byte contact is a read | analyst may not hash/stream reserved bytes; operative only after the amendment is adopted |
| 3 | `2ZD-2` — primary candidate | **C-N** — neither B nor D selected | Gate 2 cannot be registered; both candidates stay failed and frozen |
| 4 | `2ZD-3` — sizing rule | **S-1** — `R` shrinks when the `$2,500` cap binds | keeps every per-trade loss ≤ `1R` inside the cap; supports no frequency claim |
| 5 | `2ZD-4` — dependence and custody | the seven values in the table below | fixes the dependence/embargo parameters; custody field is a recommendation, not an appointment |
| 6 | `2ZD-5` — `σ`, `DE`, `p_exec` route | **E-2** — labelled pre-registered assumptions | no data access; the values stay assumptions with sensitivity ranges |
| 7 | `Q-1` — cost basis | retain `26 bp` as an unmeasured, labelled Binance proxy | keeps a planning label, not a measurement; **not a packet field** (finding `X-4`) |

**The seven `2ZD-4` values, with their required qualifications:**

| # | field | proposed value | qualification that is part of the value |
|---:|---|---|---|
| 1 | episode definition | maximal contiguous 4 h `budget_ok` run containing the signal instant | mandated by the frozen eligibility rule; dependence adequacy **conditional** on an exit policy |
| 2 | block length | 14 calendar days | **convention**, from Stage 6; not derived from the data or the MME |
| 3 | resample count | 10,000 | a **comparability choice**, explicitly not a protocol mandate |
| 4 | seed | `20240101` | a **reproducibility choice**; arbitrary by construction |
| 5 | embargo | 90 calendar days at each boundary | **derived** from `540 × 4 h`; gives 91 development blocks, consumes 180 of 792 reserved days |
| 6 | custodian | the human owner, under the logged custody procedure | a **recommendation**; appointment needs the separate instrument |
| 7 | opening condition | after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only, once, logged | consistent with §2.2 and §8.8 |

**Two caveats the owner should hold.** Row 7 (`Q-1`) is a legitimate question the 2ZD packet never asked — it appears
nowhere in `stage2zd/` — so selecting it is a confirmation of the `26 bp` label, not a packet decision. And `2ZD-4`
is a **superset**: the packet asks for five fields; the proposal supplies seven, adding the resample count and seed
(finding `X-5`).

## 3. The custodian appointment — statement and restrictions

**Instrument:** `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md`
**SHA-256:** `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` (13254 bytes)
**Status:** unsigned. **No custodian is appointed.** The role does not exist under the current protocol.

**The appointment statement, if made, would say:** the owner appoints **exactly one** custodian under proposed
protocol §8.2.1 (`A-2`–`A-4`); the appointment is **void unless the amendment is adopted first or at the same time**;
the recommended appointee is the **owner** (a recommendation, not the act); and the custodian **is not the analyst**.

**What the custodian may access:** the reserved dataset files **as byte streams, for the sole purpose of a declared
digest run**; one record per file per boundary, **by its timestamp field alone**, to locate the interval's first byte;
and the development block under the ordinary permissions any analyst has. Nothing more.

**Restrictions that bind the role (appointment instrument §§3–6):**

- **Digest-only.** A digest run streams the interval in file order through SHA-256 and writes nothing but the digest
  and the byte count. The interval endpoints are **declared in writing before the run** (by calendar decision, not
  observation); the script is committed and hashed **before** it runs.
- **Prohibited acts:** parse, decode, inspect, analyse, disclose, retain — no reading of structure, no values, no
  "it looked fine" reassurance, no copy outside the custodian's directory, no opinion about what the bytes contain.
- **Log before delivery.** Every run is logged and the entry is committed **before** any digest is delivered. The log
  is append-only and falls inside the Gate 4 audit scope. Delivery is limited to six items: digest, function, byte
  count, endpoints, date — and nothing else.
- **Separation of duties.** The custodian must not perform the analysis; the analyst must not perform custody. The
  analyst may never be the custodian. A role overlap is permitted only if disclosed (§11.1) and audited by someone else.
- **Revocation.** By the owner at any time, effective on the UTC date in the revoking statement; ends automatically if
  the amendment is not adopted, if it is repealed, if the custodian becomes the analyst, or at Gate 6.
- **Incident handling.** Any contact outside the procedure is an incident: stop, record from evidence, disclose to the
  owner and the Gate 4 auditor (not to the analyst as content), assess admissibility as the owner's question, and
  **do not repair the record**.

**One structural trust limit, stated honestly:** under `R-b` the custodian's digest is checkable by the custodian and
**not** by the analyst, whose only check is the internal consistency of the log and manifest. The Gate 4 audit must
record this, not assume it away.

## 4. The two deviations — `Y-1` and `Y-2`, in plain words

Both are **pre-amendment deviations**: acts that were permitted under the reading then in force, but that the
stricter `R-b` reading classifies as reserved contact. Neither is grandfathered, neither is retroactively legitimised,
and neither is erased.

**`Y-1` — the four boundary inspections.** In Stage 2ZC, four boundary records were inspected — one per dataset file,
four files. What was inspected was the **`open_time` string only**; **zero payloads were decoded**, and the access was
disclosed and deliberate. Under `R-b`, reading even that timestamp field is reserved contact. So the analyst's
reserved-contact count for this programme is **not zero** on a strict accounting. The deviation is not that the acts
were hidden — they were disclosed at the time — but that they were performed under a reading the owner has since
declined to adopt. What it does **not** imply: that any validation or OOS *value, price, return, or outcome* was seen.
What stays **unresolved**: whether those four timestamps fell strictly inside a reserved interval or exactly on its
boundary — the position cannot be determined without the contact `R-b` forbids, and a reader should not assume the
favourable case.

**`Y-2` — the full-file digests.** Stage 2ZC also computed SHA-256 over **every byte of every dataset file**, including
reserved bytes, and recorded those digests as each file's identity. Under `R-b`, streaming a file whose bytes include
a reserved interval is reserved contact **even though no byte was interpreted**. The consequence differs in kind from
`Y-1`: the four inspections produced a timestamp fact, while these digests produced **no content at all**. Their
*computational* value is untouched — they remain valid as file identity — while their *governance* status is a
pre-amendment deviation. After the amendment takes effect, **no analyst may recompute those digests**; verification of
an existing full-file digest becomes a custodian task.

**The common point.** Both deviations change the *status of an access*, not the *quality of a computation*. Whether
they affect the admissibility of any Stage 2ZC-derived result is a question this briefing **cannot answer**, because
the only arguments either way would need exactly the access `R-b` forbids. It is left to the owner and to Gate 4.

## 5. What retaining `C-N` means

`C-N` selects **neither** candidate. Candidate B and candidate D remain frozen at `v2.0.0` with their
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` verdicts untouched. Neither is promoted, revived, or replaced, and no
third candidate is created to fill the gap.

| consequence | stated plainly |
|---|---|
| Gate 2 cannot be **registered** | protocol §5.2 input #1 is a hypothesis; `C-N` supplies none, and §5.3 requires the registration to be complete |
| the hypothesis input is unresolved **by choice** | this is a decision, not an omission and not a missing reply |
| Gate 2 is unauthorized **and** unregistrable | the first is a standing prohibition; the second is a new fact created by this selection |
| no strategy-design work is authorized | not by `2ZD-0 = C`, not by `C-N`, and not by anything in this package |

**What `C-N` is not.** It is not a vote against either candidate's evidence, and it does not reopen either verdict. It
is a refusal to register a hypothesis now, which is a legitimate option in the packet (§6.2) and does not breach D-11,
because a rule capping primaries at one is satisfied by zero.

## 6. The questions still open — `T-5` and the exit/holding policy

**`T-5` — the real-capital expression of the annual objective.** The source record
(`stage2t/STAGE2T_OWNER_RESPONSE_RECORD.md` §T-5) is **blank** and awaiting an owner answer. The owner options are
recorded there as: `T-5a` keep `$250`; `T-5b` keep the 2.5% ratio (`$2.50`); `T-5c` research-reference only; `T-5d`
custom. No agent may answer it, and nothing in Stage 2ZI touches it. Selecting `S-1` implies nothing about it.

**The exit and holding policy.** No candidate specification contains an exit or holding rule (finding `Z-3`), so the
episode-definition and embargo arguments stay **conditional**. It is Gate 2 registration input **#5**.

**The order of the two obstructions matters, and they are not interchangeable:**

| input | state | why |
|---|---|---|
| #1 hypothesis | **open by decision** | `C-N` selects neither candidate; no third candidate may be invented |
| #5 exit rules | **open, unresolved** | the candidate specs are signal specs and contain no exit rule |

Input #1 is the one that prevents a registration from existing **at all**. Input #5 would matter as soon as a
hypothesis were named, because a registration without an exit rule cannot be complete under §5.3. Calling the exit
policy "the only thing blocking Gate 2" while `C-N` stands would invert the obstruction. **Neither is closable here:**
#1 needs a candidate decision and #5 needs a registered rule, and both are owner acts.

## 7. Adoptable now, versus open that must stay open

**Decisions the owner can make now (owner acts, document production):**

1. **Adopt the amendment** — dated, hash-named, acknowledging `V-1`, `Y-1`, and `Y-2`.
2. **Ratify the seven selections** — in the decision instrument, or in a separate dated record naming it.
3. **Appoint the custodian** — signing the appointment instrument; the recommendation is not the act.

**Decisions that must remain open:**

- **The hypothesis.** `C-N` withholds it by decision, and no third candidate may be invented. Gate 2 stays
  **unregistrable** until a candidate is named, and even then it stays **unauthorized** until a dated opening exists.
- **The exit and holding policy.** A rule that does not exist yet; required for any registration to be complete.
- **`T-5`.** The `$250`/2.5% real-capital objective expression; fields blank.
- **Whether `Y-1` and `Y-2` affect admissibility** of any Stage 2ZC-derived result — owner, informed by Gate 4.
- **The `Q-1` citation question** — the packet never asked it (`X-4`); a later documentation stage could repair the
  reference.
- **How a custodian's digest is verified by anyone but the custodian** — no answer exists under `R-b`; the trust limit
  is structural.

**Nothing here is authorized by being listed.** Adopting all three instruments still leaves Gate 2 **NOT AUTHORIZED**
and, under `C-N`, **unregistrable**; the blocker list changes shape rather than closing.
