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
