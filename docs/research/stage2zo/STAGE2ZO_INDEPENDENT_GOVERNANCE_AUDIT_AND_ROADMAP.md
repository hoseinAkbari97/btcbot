# Stage 2ZO — Independent Governance Audit and Next-Stage Roadmap

**Stage:** 2ZO (independent audit and planning only)
**Date:** 2026-11-15 (UTC)
**Status:** read-only audit. It adopts nothing, appoints nobody, registers nothing, opens no gate, and changes no
file outside this one.
**Scope:** verify the actual repository; audit governance integrity independently; diagnose the real blockage;
compare paths A–D; recommend one; give the minimal ordered roadmap.
**Boundary:** no reserved-data contact; no census, backtest, simulation, or fit; no strategy design or candidate
selection; no threshold, cost, or owner-decision change; no venue or execution work; no Gate 2 activity.

**Evidence labels:** **[F]** verified fact (recomputed or quoted from a named committed source) · **[D]** derived
conclusion (follows from facts by stated reasoning) · **[O]** observation, ambiguity, or disclosed discrepancy ·
**[OPEN]** unresolved and not answerable within this stage.

---

## 0. Outcome in one paragraph

The Stage 2ZN records are **substantively sound**: the repository is clean at the reported HEAD, every hash
recomputes, the amendment was applied as exactly the authorized text change, the adoption was recorded verbatim
against the hash the amendment requires, and the custodian appointment satisfies its instrument with the
owner/custodian overlap disclosed. Three **discrepancies** are reported rather than reconciled: (i) the appointment
record says the missing independent auditor "blocks nothing before Gate 4", but protocol §5.2 input **#15** requires
the independent auditor **in the Gate 2 registration**, so the auditor is a Gate 2 input, not merely a later
dependency; (ii) the amended protocol's header still reads "proposed protocol requiring owner approval" while
carrying an adopted `Version: 2.0.0`; and (iii) the adoption's incorporation-by-reference leans on a "prepared
statement" of Stage 2ZL/2ZM that is **not present in the repository**. None of these changes a gate, a decision, or
an authorization, and none voids the adoption. The real blockage is unchanged and two-fold: Gate 2 registration
input **#1** (a hypothesis) is withheld by `C-N`, and input **#5** (an exit/holding policy) is a rule that does not
exist. The recommended path is **B** — a genuinely new hypothesis through a separately authorized research-design
stage, preceded by the cheap administrative closures of path **D** — with **A** (stop and preserve) the honest
alternative if the owner will not authorize a new hypothesis. **C** (revisit the existing family) is **not
permitted on the current record**. Nothing here authorizes any research.

---

## 1. Repository verification (actual bytes, this session)

**[F] Repository state**, read directly and matching the Stage 2ZN report exactly:

| item | value |
|---|---|
| branch | `main` |
| HEAD | `31d5f197dea56b568c4b4287026ed79b443d61af` |
| `origin/main` | `31d5f197dea56b568c4b4287026ed79b443d61af` |
| worktree | clean (`## main...origin/main`, no changes) |
| HEAD ancestry | the five Stage 2ZN commits sit on `3959d419…`; no later commit exists |

**[F] Recomputed SHA-256 and byte counts** of the artifacts Stage 2ZN depends on — all match the reported values:

| artifact | SHA-256 | bytes |
|---|---|---:|
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` (v2.0.0) | `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` | 44625 |
| `stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 |
| `stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 |
| `stage2zn/STAGE2ZN_PROTOCOL_ADOPTION_RECORD.md` | `5882d37b439ddc917b17f9008589e7afdcd0e6f7dba00d7283d8af4506d88267` | 7860 |
| `stage2zn/STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md` | `1a22a18527583febd8d3f89b1446f5006d711b3a797889ac27978539ea365218` | 6656 |
| `stage2zn/STAGE2ZN_ADOPTION_VALIDATION_REPORT.md` | `719fe6303db1cbe1a39b681c6a45f4d4e1bb55c569ad36447a82616c62de556e` | 5987 |
| `stage2zn/FREEZE_MANIFEST.json` | `c411dc6a91e877b59892e73565ac99a5192af447d64d4619b88c3e97e22ae5a9` | 12126 |

**[F] The Stage 2ZN manifest validates independently.** Its stored `self_hash` is
`77c5e47d3882d9f6a7f895094bd855d4770f9007fc7390eb10c1018ca64c6937`; recomputing SHA-256 over the canonical JSON
(`sort_keys=True`, `separators=(',',':')`, `ensure_ascii=False`, `self_hash` removed) returns the **same** value. All
four `deliverables[]` entries re-hash to their recorded digests and byte counts. The two predecessor manifests
(`stage2zi`, `stage2zk`) also self-hash to their stored values.

**[F] The protocol change is exactly the authorized one.** `git diff 3959d419…HEAD` touches only
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`, as **71 insertions, 1 deletion**. The removed line is the superseded
§8.2 sentence ("The exact dates and hashes are frozen at Gate 2." — now **0** occurrences); the new sentence occurs
**once**; the `### 8.2.1` heading occurs **once**; a `Version: 2.0.0` header line was added. No other protocol line
changed.

**[F] The applied §8.2.1 text is byte-identical to the amendment's authorized text.** Unquoting the amendment's
blockquoted `A-1`–`A-5` bodies and removing the two documents' heading lines, the clause bodies match with **no
textual difference**; the only added material is the `### 8.2.1` heading itself.

**[F] The 2ZN validation report is an agent self-validation.** It is read here as evidence of what was checked, not
as independent proof; this stage re-verified the hashes itself rather than relying on it.

**[F] No manifest is created for this stage.** Protocol §10.2 attaches the manifest requirement to **versions of
frozen artifacts**; §10.1's frozen list is unchanged by a read-only audit, and this stage freezes nothing. A stage
manifest is therefore not required by the governing protocol, and none is produced — one report is the whole
deliverable set.

---

## 2. Independent governance audit

Each check is scored **[PASS]**, **[PASS with observation]**, or **[DISCREPANCY]**.

### 2.1 Was the adoption recorded correctly? — **[PASS]**

**[F]** The owner's adopting affirmation is recorded verbatim (21 words, including the inline-code hash), names the
instrument by path and full SHA-256, states **adopt**, records version `2.0.0`, and incorporates the statement's
acknowledgements. This satisfies amendment §8 elements 1–6. **[F]** Element 7 (a manifest for the amended protocol
text with SHA-256, byte counts, and a canonical self-hash) is satisfied by `FREEZE_MANIFEST.json`, which validates
(§1). **[F]** The effective date `2026-11-15 (UTC)` is the date written into the statement, as amendment §3
requires. **[D]** The adoption is complete on its own terms.

### 2.2 Was the amendment applied exactly as authorized? — **[PASS]**

**[F]** Only §8.2's final sentence changed, §8.2.1 (`A-1`–`A-5`) was inserted immediately after §8.2, and a version
line was added; the diff is confined to those lines (§1). **[F]** The clause bodies are byte-identical to the
amendment's text. **[D]** No unrelated edit and no silent ambiguity resolution was made.

### 2.3 Does the custodian appointment satisfy its instrument? — **[PASS with observation]**

**[F]** The affirmation names **Hossein Akbari**, appoints the owner, states the custodian is **not** the analyst,
binds the role to "the exact terms and restrictions of the custodian appointment instrument", and is "conditional on
adoption of the amendment". **[F]** The amendment was adopted the same UTC date, satisfying the instrument's
"adopted first or at the same time" dependency. **[D]** The appointment is in force and correctly recorded.

**[O]** The instrument's §10 appointment table has a field *"Access granted, in my words."* The owner did not restate
the access in their own words; they incorporated the instrument's own terms by reference ("under the exact terms and
restrictions"). The record renders the access as the instrument's digest-only procedure. **[D]** This is a minor
formality observation, not a defect: the instrument is expressly designed to be incorporated ("the exact terms and
restrictions"), and the appointment is not void.

### 2.4 Is the owner/custodian overlap properly disclosed? — **[PASS]**

**[F]** The overlap is disclosed in the appointment record (§0, §2) and stated in the 2ZN manifest. **[F]** Protocol
§11.1 permits an overlap **only if** it is disclosed **and** the audit is performed by someone else; the record
carries both halves (disclosure here; the auditor requirement in §2.5).

### 2.5 Is the independent Gate 4 auditor requirement explicit and enforceable? — **[DISCREPANCY]**

**[F]** The requirement is explicit and correctly framed: the auditor must **not** be the custodian and must have
**no prior involvement** in design or implementation (protocol §11.1, §7.3; instrument §6), and it is recorded as
outstanding dependency `AN-1`.

**[DISCREPANCY]** The appointment record §4 states the dependency "blocks nothing before Gate 4". That is
**inconsistent with protocol §5.2 input #15**, which requires the registration document to contain *"the independent
auditor and the scope of Gate 4."* **[D]** The independent auditor is therefore a **Gate 2 registration input**, not
only a downstream Gate 4 dependency: a registration that does not name the auditor cannot be complete under §5.3
criterion 1. The Stage 2ZD matrix already scored input #15 `PARTIAL` for exactly this reason ("no reviewer or
specialist is identified"). Reported, not reconciled.

**[O] Enforceability is by rule only.** No mechanism prevents a custodian from self-auditing beyond the prohibition
itself, and the owner is the only human on the programme, so an independent auditor must be sourced externally;
protocol §7.7 ("Practical alternatives when no external professional auditor is available") is the route if none is
found. This is a live dependency, not a closed one.

### 2.6 Do all predecessor deviations remain disclosed? — **[PASS]**

**[F]** `Y-1` (the four Stage 2ZC boundary `open_time` inspections) and `Y-2` (the Stage 2ZC full-file digests) are
recorded as **pre-amendment deviations**, neither grandfathered nor retroactively legalized, in the amendment §7,
the adoption record §3, the custodian record §3, and the Stage 2ZJ briefing §4. **[F]** The analyst's
reserved-contact count is disclosed as **not zero** on a strict `R-b` accounting, and the "inside or on the
boundary" question is left explicitly unresolved.

### 2.7 Was any decision, authorization, or status accidentally changed? — **[PASS]**

**[F]** The protocol diff is confined to §8.2/§8.2.1/header. **[F]** The seven recorded decisions (`2ZD-0`=C,
`2ZD-1`=R-b, `2ZD-2`=C-N, `2ZD-3`=S-1, `2ZD-4`=seven values, `2ZD-5`=E-2, `Q-1`=26 bp) are unchanged and are not
ratified or reopened by the adoption (adoption record §4). **[F]** Gate status is unchanged; no threshold, MME,
population, or verdict moved (`A-5` non-derogation). **[F]** No predecessor artifact was modified except the
authorized protocol change.

### 2.8 Does the amended protocol introduce contradictions or circular dependencies? — **[PASS with observations]**

**[O] A tension between §8.2.1 `A-2` and protocol §11.2.** `A-2` says the custodian is "the **only** party permitted
reserved contact", while §11.2 permits the **auditor** validation/OOS access "if the audit scope explicitly requires
it and the owner authorizes it". `A-5` preserves earlier restrictions but does not explicitly reconcile the two.
Read narrowly, `A-2`'s exclusivity governs the digest procedure and §11.2 remains an owner-authorized exception; the
text does not say so. Disclosed for the Gate 4 audit or a future clarification; it authorizes nothing and changes no
gate.

**[O] A stale header line.** The protocol header still reads *"Status: proposed protocol requiring owner approval"*
while also carrying *"Version: 2.0.0 — first versioned form, assigned on adoption"*. **[D]** The adoption was
authorized to change only §8.2/§8.2.1 and to assign the version, so the record correctly left the status line; but
the header is now internally inconsistent (adopted vs proposed). A future **minor** version could clarify it.

**[O] A non-committed incorporation-by-reference.** The adopting affirmation incorporates "all acknowledgements and
qualifications in the statement". That "statement" is the prepared Stage 2ZL/2ZM statement, and **no
`docs/research/stage2zl` or `stage2zm` directory exists** and no commit mentions them. The repository's only
rendering of those acknowledgements is the adoption record §3. **[D]** The affirmation independently names the hash
and version, so the adoption is **not void**; but the referenced statement is **not independently auditable from the
repository**, and the record's §3 enumerations are the operative text. Disclosed as an evidentiary gap.

**[O] A phrasing imprecision.** The custodian record lists "the custodian's digest run, which waits for Gate 2
registration" as open. Strictly, the digest run is part of **producing** the Gate 2 manifest (`A-3`), so it waits for
the Gate 2 stage **authorization** (a dated opening), not for a completed registration. No circular dependency
exists: dates (owner) → digests (custodian) → Gate 2 manifest is a sequence, not a cycle.

**[D] No contradiction or circular dependency was found that changes a gate, a decision, or an authorization.**

---

## 3. Blocker matrix and diagnosis

### 3.1 Why Gate 2 is unregistrable, in the correct order

**[F]** Gate 2 registration requires all sixteen §5.2 inputs to be present and complete (§5.3 criterion 1). Two
inputs are open, and they are **not interchangeable**:

| input | state | why it blocks |
|---|---|---|
| **#1 Hypothesis** | **open by decision** (`C-N`) | §5.2 input #1 is a hypothesis; `C-N` selects neither candidate and no third candidate may be invented, so no registration can **exist** |
| **#5 Exit rules** | **open, unresolved** (`Z-3`) | the candidate specs are signal specs and contain no exit/holding rule, so a registration cannot be **complete** |

**[D]** Input #1 is the primary obstruction — it prevents a registration from existing at all. Input #5 would matter
the moment a hypothesis were named. Calling the exit policy "the only blocker" while `C-N` stands would invert the
obstruction.

### 3.2 Is `C-N` the correct reading of the owner's decision? — **[PASS]**

**[F]** `2ZD-2 = C-N` is recorded as the owner's choice in Stage 2ZK, from the owner's verbatim words read against
the seven selections. **[F]** The Stage 2ZD packet defines `C-N` as "no selection now; keep both as unselected — Gate
2 cannot name a primary hypothesis". **[D]** The reading is correct and consistent: `C-N` withholds the hypothesis by
decision, does not reopen either verdict, and does not breach D-11 (a one-primary cap is satisfied by zero). No
discrepancy.

### 3.3 Should the two failed candidates stay permanently closed? — **[D] Yes, on the current record**

**[F]** Both candidates failed at Stage 2J under the **frozen** decision rule (`N < 150` or `M_all > 0.20`): B with
24 opportunities and D with 34 (against 150), recorded `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` and frozen at
`v2.0.0`. **[D]** A genuinely **different** research family may be considered under the protocol (§2.3 permits the
owner to "authorize a new hypothesis"), but a failed candidate may **not** be re-registered by relabeling: that
would reuse failed evidence and/or relax a frozen threshold, both prohibited (§10.3, §15). Reopening a verdict is an
owner act that the present record does not contain.

### 3.4 What is still required before a new hypothesis can be registered

**[F]** Beyond #1 and #5, the remaining §5.2 gaps are: #6 risk/sizing (now writable — `S-1` fixed the cap-versus-stop
interpretation), #7 numeric regime definitions, #9 secondary-metric table, #10 dependence numerics (now supplied by
`2ZD-4`), #11/#12 sample-sufficiency and feasibility criteria (`E-2` supplies the assumptions at registration), #13
failure list, #14 data-access plan (mechanism now exists via the custodian), #15 audit plan (**the auditor must be
named** — §2.5), and #16 version and hashes (produced last).

### 3.5 Mandatory versus conservative

**[D]** Only the items below block a Gate 2 registration. The rest are conservative or belong to later gates.

| blocker | type | mandatory? | restricted data? | owner act? |
|---|---|---|---|---|
| #1 hypothesis (`C-N`) | decision | **mandatory** | no | yes |
| #5 exit/holding policy | rule | **mandatory** | no | yes |
| #15 independent auditor (`AN-1`) | person | **mandatory** | no | yes |
| #16 frozen spec + hash manifest | document | **mandatory** | no | no (produced by the stage) |
| #7 regime numerics, #9 metrics, #13 failure list | document | **mandatory** | no | no |
| #11/#12 sample sufficiency under `E-2` | assumption | **mandatory** | no (if `E-2`) | yes (declaration) |
| #14 dates + custodian digests | procedure | **mandatory** | **yes** (digest-only) | yes (dates) |
| `26 bp` not measured | cost proxy | **not blocking** — Gate 2 needs a cost basis, not a measured one | no | no |
| `C-4` / `C-6` venue, execution | venue | **not blocking** if no execution claim is made | venue | no |
| `T-4` / `T-5` real capital | capital | **not blocking** Gate 2 | no | yes (later) |
| `Y-1`/`Y-2` admissibility | question | **[OPEN]** — owner, informed by Gate 4 | no | yes |

---
