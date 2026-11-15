# Stage 2ZP — Independent Auditor Qualification and Governance Remediation

**Stage:** 2ZP (administrative and governance preparation only)
**Date:** 2026-11-15 (UTC)
**Status:** preparation only. It contacts no auditor, appoints no one, authorizes no research, opens no gate, and
changes no file outside this one.
**Strategic direction:** proceed toward **Path B** from Stage 2ZO — a genuinely new hypothesis through a separately
authorized design stage. Both existing candidates remain **permanently closed** under their `FEASIBILITY FAIL`
verdicts; they are not reopened, modified, or substituted.
**Boundary:** no reserved, validation, or OOS access; no census, backtest, simulation, or statistical analysis; no
strategy design; no candidate reopening; no threshold, cost, owner-decision, or verdict change; no venue or
execution work; no Gate 2 or later gate.

**Evidence labels:** **[F]** verified fact (recomputed or quoted from a named committed source) · **[D]** derived
conclusion · **[O]** observation or disclosed discrepancy · **[OPEN]** unresolved and not answerable here.

---

## 0. Outcome in one paragraph

This stage turns the Stage 2ZO finding that the independent auditor is a **Gate 2 registration input** (§5.2 #15)
into prepared, unadopted instruments: a **qualification specification** and a **draft appointment instrument** for an
independent auditor who is not the owner-custodian. It assesses the three Stage 2ZO discrepancies and recommends the
**smallest defensible remediation** for each without editing any historical record or the adopted protocol. It
proposes a **boundary for a future H1 design stage** that defines a genuinely new mechanism, forbids reuse of failed
candidate evidence, and keeps the economic objective and frozen thresholds binding. It updates the blocker matrix and
restates what remains unauthorized. **Nothing is appointed, adopted, or authorized.** The auditor fields are blank; no
person, qualification, consent, or appointment is invented. No manifest is produced, because this stage freezes
nothing (protocol §10.2 attaches manifests to versions of frozen artifacts).

---

## 1. Repository verification (actual bytes, this session)

**[F] Repository state**, read directly:

| item | value |
|---|---|
| branch | `main` |
| HEAD | `355f40f4301447dc1beb89faa5b21c94002453e4` |
| `origin/main` | `355f40f4301447dc1beb89faa5b21c94002453e4` |
| worktree | clean (`## main...origin/main`, no changes) |
| HEAD ancestry | the six Stage 2ZO commits sit on `31d5f197…`; no later commit exists |

**[F] Recomputed SHA-256 and byte counts** — all match:

| artifact | SHA-256 | bytes |
|---|---|---:|
| `stage2zo/STAGE2ZO_INDEPENDENT_GOVERNANCE_AUDIT_AND_ROADMAP.md` | `7f650087604dcffda2c45796db5c9aa65637e2ee92a110ec20d5c6bc94c1f5ea` | 28622 |
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` (v2.0.0) | `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` | 44625 |
| `stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 |
| `stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 |
| `stage2zn/STAGE2ZN_PROTOCOL_ADOPTION_RECORD.md` | `5882d37b439ddc917b17f9008589e7afdcd0e6f7dba00d7283d8af4506d88267` | 7860 |
| `stage2zn/STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md` | `1a22a18527583febd8d3f89b1446f5006d711b3a797889ac27978539ea365218` | 6656 |
| `stage2zn/STAGE2ZN_ADOPTION_VALIDATION_REPORT.md` | `719fe6303db1cbe1a39b681c6a45f4d4e1bb55c569ad36447a82616c62de556e` | 5987 |
| `stage2zn/FREEZE_MANIFEST.json` | `c411dc6a91e877b59892e73565ac99a5192af447d64d4619b88c3e97e22ae5a9` | 12126 |

**[F] The Stage 2ZN manifest validates independently.** Stored `self_hash`
`77c5e47d3882d9f6a7f895094bd855d4770f9007fc7390eb10c1018ca64c6937` recomputes exactly; all four `deliverables[]`
re-hash to their recorded digests and byte counts.

**[F] The Stage 2ZO report was read in full** (the hash above matches). Its findings — three discrepancies and the
Path B recommendation — are the input to this stage.

**[F] The governing text read for this stage:** protocol §5.2 (sixteen registration inputs), §5.3 (pass criteria),
§7.2–§7.7 (Gate 4 inputs, independence requirements, audit scope, finding severity, practical alternatives), §8.2.1
(`A-1`–`A-5`), §10 (freeze policy), and §11.1–§11.8 (separation of duties, auditor access, conflict-of-interest
disclosure, finding classification, re-audit, and the Stage 2L precedent).

**[F] No manifest is produced for this stage.** Protocol §10.2 attaches the manifest requirement to versions of frozen
artifacts; this stage freezes nothing and changes nothing frozen. One report is the whole deliverable set.

---

## 2. Independent auditor qualification specification

**[F]** Protocol §5.2 input #15 requires the registration document to contain "the independent auditor and the scope
of Gate 4". **[F]** Protocol §7.3 fixes six independence requirements; §7.4 fixes the audit scope; §11.3 fixes the
conflict-of-interest disclosure; §7.7 fixes the minimum defensible standard when no external professional auditor is
available. **[D]** The specification below restates those requirements as qualification criteria. It is a
specification, **not** an appointment, and it names no person.

### 2.1 Independence from the owner-custodian — **mandatory**

- **[F]** The auditor must **not** be the owner-custodian. `A-2` makes the custodian the only party permitted
  reserved contact, and §11.1 requires the audit to be performed by **someone other than** the custodian where a role
  overlap exists. **[D]** Hossein Akbari is the owner-custodian and **cannot** serve as this auditor.
- **[F]** The auditor must also not be the analyst/implementer (§11.1: "An implementer cannot audit their own work").
- **[D]** Independence is a property of the **relationship**, not of the tool or the conversation (§11.7): a different
  model, a new conversation, or a separate agent does not by itself create independence.

### 2.2 No prior involvement in the work under review — **mandatory**

**[F]** §7.3 requires: (1) no prior implementation involvement (did not design, write, review, or report on the
implementation); (2) no decision involvement (did not choose the candidate, threshold, population, or verdict rule).
**[D]** For the Stage 2ZP path, the auditor must have had no part in any prior candidate design, census, or verdict —
including candidates B and D.

### 2.3 Relevant quantitative research and statistical expertise — **required, per §7.7**

**[F]** §7.7's alternatives differ in what they can establish: an external professional auditor provides arms-length
review and domain expertise; a separate reviewer may lack domain expertise; a second agent may share training biases.
**[D]** The auditor must be able to assess: cluster-robust and block-bootstrap dependence handling (D-09), the
sample-sufficiency chain (`N_ind`, `N_obs`, `required_opportunities`), the design-effect and `p_exec` assumptions
under `E-2`, cost arithmetic (`cost_R`, the `26 bp` proxy, the `$2,500` cap geometry), and the verdict logic.

### 2.4 Ability to inspect frozen artifacts and governance evidence — **required**

**[F]** §7.2 and §7.4 require access to the frozen specification and config, source code and version hashes, the test
suite and synthetic fixtures, the data manifest and alignment report, recorded outputs and logs, a
specification-to-code trace, and the governance records. **[F]** §11.2 lists the auditor's inputs and permits
synthetic tests and inspection of code and aggregate outputs. **[D]** The auditor must be able to work from the
**frozen artifacts**, not from an implementer's undocumented assumptions (§7.3 requirement 4).

### 2.5 Confidentiality and data-access obligations — **mandatory**

**[F]** §11.2: "The auditor may not access validation or OOS data unless the audit scope explicitly requires it and
the owner authorizes it." **[D]** The auditor's default posture is **no reserved-data access**; any exception is a
written, owner-authorized, scope-limited act under protocol §8.2.1. **[D]** The auditor must keep confidential any
non-public artifact reviewed and must not disclose reserved content beyond what the authorized scope permits.

### 2.6 Conflict-of-interest disclosure — **mandatory**

**[F]** §11.3 requires disclosure of: any prior involvement in design, implementation, or reporting; any financial or
employment interest in the outcome; any relationship with the implementer or owner that could affect judgment; and
the scope and limits of the auditor's expertise. **[F]** §7.3 requirement 6 requires a signed statement of
independence listing the evidence reviewed. **[D]** The disclosure is made before the audit and updated if it
changes.

### 2.7 Required audit deliverables and evidence standards — **mandatory**

**[F]** §7.4 fixes the audit scope (traceability, synthetic testing, temporal correctness, data alignment, cost and
capital arithmetic, non-overlap, diagnostics, verdict logic, reproducibility, provenance). **[F]** §7.5 and §11.5
fix the finding scale (`CRITICAL`/`MAJOR`/`MINOR`/`OBSERVATION`), each finding carrying an ID, location, the
requirement it violates, explanation, impact, proof status, historical-conclusion impact, evidence, and a recommended
resolution. **[F]** §11.5: CRITICAL and MAJOR findings **block the next gate**; MINOR findings require owner sign-off
and a remediation plan; OBSERVATION items are recorded for a future version. **[F]** §11.6: the audit report, hashes,
and owner decisions are versioned and never deleted, and the audit record is part of the stage's freeze manifest.
**[F]** §11.7 requires the report to state who performed the audit, their prior involvement, what they reviewed, what
they could and could not verify, and what independence limitations remain.

### 2.8 Explicit prohibition on unauthorized reserved-data access — **mandatory**

**[F]** Under §8.2.1, the analyst's reserved contact is zero and the custodian is the only party permitted reserved
contact, for declared digest runs only. **[D]** The auditor is **not** a second custodian: the auditor may inspect
frozen artifacts, code, logs, and aggregate outputs, but may **not** stream, hash, parse, or decode reserved bytes
unless a separate owner authorization explicitly widens the audit scope under §11.2. **[D]** Any reserved contact by
the auditor outside such an authorization is an **incident** under the custodian instrument §8, handled by stop,
record-from-evidence, disclosure, and no repair of the record.

### 2.9 Qualification summary

| # | criterion | class | source |
|---|---|---|---|
| 1 | not the owner-custodian; not the analyst/implementer | mandatory | §11.1, `A-2` |
| 2 | no prior implementation or decision involvement | mandatory | §7.3 |
| 3 | quantitative research / statistical expertise | required | §7.7 |
| 4 | access to frozen artifacts and governance evidence | required | §7.2, §7.4, §11.2 |
| 5 | confidentiality; default no reserved-data access | mandatory | §11.2, §8.2.1 |
| 6 | signed conflict-of-interest / independence disclosure | mandatory | §7.3, §11.3 |
| 7 | deliverables in the §7.5/§11.5 finding format; §11.6 retention | mandatory | §7.5, §11.5, §11.6 |
| 8 | no unauthorized reserved-data access | mandatory | §8.2.1, §11.2 |

**[F] No person, qualification, consent, or appointment is supplied here.** The specification is a standard, not a
nomination.

---

## 3. Draft appointment instrument — **DRAFT — NOT APPOINTED**

> **DRAFT — NOT APPOINTED.** This is an unexecuted template. Its existence appoints no one, grants no access, and
> creates no obligation. Every field is blank. It is modeled on the custodian appointment instrument
> (`stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md`) but is not that instrument and does not amend it.

### 3.1 Parties

- **Owner-custodian:** Hossein Akbari (recorded, `stage2zn/STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md`).
- **Independent auditor (candidate):** `______________________` — name, professional affiliation, and contact left
  **blank**.
- **Role:** independent Gate 4 auditor under protocol §7 and §11.

### 3.2 Recitals

- **[F]** Protocol §5.2 input #15 requires the independent auditor and the Gate 4 scope to be named in the Gate 2
  registration document.
- **[F]** Protocol §7.3 and §11.1 require the auditor to be independent of the owner-custodian and the implementer.
- **[D]** The owner-custodian cannot serve as auditor; the candidate named above must satisfy §2 in full.

### 3.3 Independence declaration (auditor-signed, blank)

The auditor declares, by signature below, that they satisfy every mandatory criterion in §2:

- **[F]** no prior implementation involvement and no decision involvement in the work under review (§7.3);
- **[F]** no financial, employment, or personal interest in the outcome (§7.3, §11.3);
- **[F]** a signed statement of independence listing the evidence reviewed (§7.3 requirement 6);
- **[D]** not the owner-custodian, not the implementer, and not an agent re-labeled to appear independent (§11.1, §11.7).

**Signature:** `______________________`  **Date:** `______________`

### 3.4 Scope and responsibilities

- **[F]** Perform the Gate 4 audit against the §7.4 scope: specification-to-code trace, synthetic testing, temporal
  correctness, data alignment, cost and capital arithmetic, non-overlap, diagnostics, verdict logic, reproducibility,
  and provenance.
- **[F]** Report findings in the §7.5/§11.5 format, each with ID, location, requirement violated, explanation, impact,
  proof status, historical-conclusion impact, evidence, and recommended resolution.
- **[F]** Classify findings; CRITICAL/MAJOR block the next gate; MINOR requires owner sign-off and a remediation plan;
  OBSERVATION is recorded for a future version.
- **[F]** State in the report who performed the audit, their prior involvement, what was reviewed, what could and could
  not be verified, and what independence limitations remain (§11.7).

### 3.5 Access boundaries

- **[F]** Permitted by default: frozen specification and config, source code and version hashes, test suite and
  synthetic fixtures, data manifest and alignment report, recorded outputs and logs, the trace, and governance records
  (§7.2, §11.2).
- **[F]** Prohibited by default: validation and OOS data, and any reserved bytes. Reserved access requires an explicit
  audit-scope statement **and** owner authorization (§11.2, §8.2.1).
- **[D]** The auditor is not a custodian and gains no reserved contact by this instrument.

### 3.6 Confidentiality

- **[D]** The auditor keeps confidential all non-public artifacts reviewed and does not disclose reserved content
  beyond the authorized scope.
- **[D]** On completion, the auditor returns or destroys copies as the owner directs, retaining only the audit record
  and its hashes, which are versioned and never deleted (§11.6).

### 3.7 Conflict-of-interest declaration (auditor-signed, blank)

- **[F]** Disclosure of prior involvement in design, implementation, or reporting; any financial or employment interest
  in the outcome; any relationship with the implementer or owner that could affect judgment; and the scope and limits
  of expertise (§11.3).
- **[D]** The declaration is made before the audit and updated if any fact changes.

**Signature:** `______________________`  **Date:** `______________`

### 3.8 Audit deliverables

- **[F]** A written Gate 4 audit report with the §7.4 scope, the §7.5/§11.5 findings, and the §11.7 disclosure.
- **[F]** Versioned hashes of the artifacts reviewed and the report itself; the report enters the stage freeze manifest
  (§11.6).
- **[D]** A clear statement of what the audit could not verify.

### 3.9 Revocation and replacement

- **[D]** The owner may revoke this appointment in writing at any time; revocation is recorded, not deleted.
- **[D]** If the auditor becomes non-independent, or breaches §3.5 or §3.6, the appointment is revoked and the affected
  work is re-audited by a new party under §11.6.
- **[D]** A replacement must satisfy §2 afresh; a revoked auditor's prior report remains in the record with its status
  noted.

### 3.10 Acceptance fields (blank)

- **Owner-custodian acceptance:** `______________________`  **Date:** `______________`
- **Auditor acceptance:** `______________________`  **Date:** `______________`

**[F]** With all fields blank, this instrument is **DRAFT — NOT APPOINTED**. No appointment exists until the owner
signs it and the named auditor accepts.

---

## 4. Governance discrepancy assessment

**[D]** This section assesses the three discrepancies reported by Stage 2ZO. It **quotes** the exact source text,
states the impact, recommends the **smallest defensible remediation**, and states whether owner authorization is
required. **[F]** No historical record and no protocol text is edited by this stage.

### 4.1 `D1` — auditor appointment timing (Gate 2 input #15 vs. "blocks nothing before Gate 4")

**Exact source text.**

- **[F]** Protocol §5.2 input #15 (line 225): "**Audit plan:** the independent auditor and the scope of Gate 4."
- **[F]** Custodian appointment record §4 (line 108):
  "the dependency blocks nothing before Gate 4, and it does not reopen the reserved blocks."

**Impact.** **[D]** The two statements are in tension. §5.2 #15 is a **Gate 2 registration input**: under §5.2 the
registration document must name the auditor, so an unappointed auditor is a **blocker at Gate 2**, not only at
Gate 4. **[F]** The custodian record's own §4 (line 107) also says "no auditor is appointed, named, or invented here;
appointing one is a separate owner act." **[D]** Practical effect: Gate 2 is currently unregistrable not only because
of `C-N` (hypothesis withheld) and the unresolved exit/holding policy, but also because input #15 cannot be filled.

**Smallest defensible remediation.** **[D]** Do **not** edit either record. Add a one-line **clarification** in a
future owner-approved governance note (or in the next stage's record) stating that the custodian record's "blocks
nothing before Gate 4" is scoped to *reserved-data and research blocks* and does not override §5.2 #15's requirement
that the auditor be named at Gate 2 registration. **[D]** The clarifying note is prospective; the original wording
stays for audit.

**Owner authorization required?** **[D]** Yes — any governance note that interprets the custodian record is an owner
act; the research agent may only propose it.

### 4.2 `D2` — protocol header ("proposed protocol requiring owner approval" with adopted `Version: 2.0.0`)

**Exact source text.**

- **[F]** Protocol header (lines 4–7): "**Status:** proposed protocol requiring owner approval. It authorizes no
  experiment, candidate, or data access." followed by "**Version:** 2.0.0 — first versioned form, assigned on
  adoption 2026-11-15 (UTC) under finding `V-1`".
- **[F]** The same header's `Version:` line cites `stage2zn/STAGE2ZN_PROTOCOL_ADOPTION_RECORD.md`, which records the
  adoption.

**Impact.** **[D]** The header carries **two statuses at once**: a `Status:` line that says *proposed*, and a
`Version:` line that says *assigned on adoption*. A reader cannot tell from the header alone whether the protocol is
adopted or merely proposed. **[D]** The `Version: 2.0.0` line is unambiguous that adoption occurred; the `Status:`
line is stale relative to it.

**Smallest defensible remediation.** **[D]** Change **only the `Status:` line** to a status consistent with adoption
— e.g. "**Status:** adopted 2026-11-15 (UTC) as version 2.0.0; it authorizes no experiment, candidate, or data
access until the applicable gate is registered and approved." This is a one-line edit to a header, not a change to
any normative rule, threshold, or decision. **[D]** It must not be done by the research agent unilaterally; it is an
owner-approved edit, and the pre-edit text stays recoverable in git history.

**Owner authorization required?** **[D]** Yes — editing the adopted protocol's header is a protocol change; it
requires explicit owner authorization and should be recorded as a versioned header correction, not a silent edit.

### 4.3 `D3` — adoption record's incorporation-by-reference to an uncommitted prepared statement

**Exact source text.**

- **[F]** Adoption record §1: the owner's affirmation reads "…including all acknowledgements and qualifications in the
  statement."
- **[F]** Adoption record, *By reference*: "The affirmation incorporates, by the phrase *'including all
  acknowledgements and qualifications in the statement'*, the prepared Statement 1 of Stage 2ZM/2ZL, whose
  acknowledgements (`V-1`, `V-2`, the manifest requirement, `Y-1`, `Y-2`) are set out in §3."
- **[F]** No `docs/research/stage2zl/` or `docs/research/stage2zm/` directory exists in the repository, and no commit
  message references Stage 2ZL or Stage 2ZM.

**Impact.** **[D]** The adoption record asserts that the affirmation incorporates a "prepared Statement 1 of Stage
2ZM/2ZL", but that statement is **not in the repository**. **[F]** The adoption record itself partially mitigates this:
it says the acknowledgements "are set out in §3", so the *substance* of the incorporated items is reproduced inside
the record. **[D]** The remaining gap is **provenance**: a future auditor cannot independently verify that §3's
reproduction matches the original prepared statement, because the original is absent.

**Smallest defensible remediation.** **[D]** Do **not** fabricate or retro-add a Stage 2ZL/2ZM document. Two
defensible options, in order of least change: (a) add a one-line **provenance note** to the adoption record (owner
act) stating that the referenced Stage 2ZL/2ZM statement was a session-local preparation with no committed artifact,
and that §3 of the record is the authoritative transcription; or (b) leave the record as-is and record the gap as an
**`OBSERVATION`** for the future auditor to weigh under §11.4 (historical evidence unavailable ⇒ cannot be fully
reproduced). **[D]** Option (a) is the smallest change that restores auditability; option (b) is the smallest change
that changes nothing.

**Owner authorization required?** **[D]** Yes for (a) — it edits a committed record; **(b) requires no change** and is
already satisfied by this assessment being committed.

---

## 5. Proposed H1 design-stage boundary

**[D]** This section proposes the **scope boundary** for a future design stage ("H1"). It defines what the stage may
and may not do, and what must be complete before Gate 2 registration. **[F] It proposes no actual trading
hypothesis** — no mechanism, no signal, no rule. **[F]** Gate 2 remains **NOT AUTHORIZED**; this is preparation only.

### 5.1 What counts as a genuinely new mechanism

- **[D]** A new mechanism must differ in its **economic source of return**, not merely in parameter values, symbol,
  timeframe, or naming. **[F]** §7.3 requirement 2 forbids the auditor from having chosen the candidate; the same
  logic requires the candidate to be genuinely distinct from the closed ones.
- **[D]** A candidate that reduces to candidate B's or D's logic under any parameter setting is **the same candidate**
  and stays closed.
- **[F]** Both closed candidates failed at v2.0.0 on `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`
  (`B`=24 opps, `D`=34, vs. required 150; frozen Stage 2J rule `N<150` or `M_all>0.20`).

### 5.2 Preventing reuse of failed-candidate evidence as new evidence

- **[D]** The new hypothesis may not cite B's or D's censuses, backtests, or opportunity counts as evidence of
  feasibility. **[F]** Those artifacts remain valid only as *historical records of a closed candidate*.
- **[D]** Any census for the new hypothesis must be a fresh, separately authorized run under the §8.2.1 reserved
  discipline, with its own manifest, and may not pool data windows with the closed candidates.
- **[F]** The frozen feasibility thresholds (`N_ind`, `N_obs`, `required_opportunities`, the `N<150` /
  `M_all>0.20` rule) remain **binding**; H1 may not relax or reinterpret them.

---

