# Stage 2ZI — Custodian Appointment Instrument

**Status:** **UNSIGNED. NO CUSTODIAN IS APPOINTED.** The role does not exist under the current protocol, and this
document appoints no one.
**Creates, if signed:** a single custodian under proposed protocol §8.2.1 (`A-2`…`A-4`), which is itself
unadopted.
**Dependency, stated once and meant:** the appointment is void unless the amendment in
`docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` is adopted first or at the same time. An appointment
under a clause that does not exist appoints nobody.

## 1. Recommendation, and why it is only a recommendation

**[REC]** The owner is the recommended custodian. There is no second official with credentials on this programme,
an institutional custodian would have to be invented, and inventing one is a governance decision the agent may not
make. Naming the owner also puts the strongest available boundary in place: the party who may see the reserved
data is the party who owns the decision, and the analyst is excluded by construction.

**The recommendation is not an appointment.** Under the amendment, appointment happens only by a written owner
act. Until then this instrument is a form with empty fields, and the answer to "who is the custodian?" remains
**nobody**.

## 2. What the custodian may access, exactly

| may access | may not access |
|---|---|
| the reserved dataset files, as byte streams, for the sole purpose of a declared digest run | any reserved byte for any other purpose, including curiosity, spot-checking, debugging, or "seeing what it looks like" |
| one record per file per boundary, by its timestamp field alone, to locate the interval's first byte | any other field of any record, and any second inspection per boundary |
| the development block, under the ordinary permissions any analyst has | nothing more than any analyst may access, absent a separate authorization |

**"Access" is not limited to display.** Opening, streaming, reading into memory, copying, exporting, hashing,
parsing, querying, or measuring the reserved interval are all access. The only permitted instance of it is the
digest run in §3.

**Not a licence to research.** The custodian is not thereby authorized to analyse reserved material, form an
opinion about it, or act on what a digest run implies. Custody is a duty to hold and to identify, not a research
permission.

## 3. Digest-only processing rules

A digest run is the only permitted reserved contact. It proceeds as follows, in this order, with no step skipped:

1. **Declare first.** The interval's endpoints are declared in writing before the run — by calendar decision, not
   by observation. Declaring a date reads no data.
2. **Freeze the script.** The script is committed and its SHA-256 recorded before it is run. A modified script is a
   new script, requiring a new recorded hash and a new declaration.
3. **Stream, do not load.** The script streams the interval in file order through SHA-256 and writes nothing but
   the digest and the byte count. It does not build a frame, parse a line, decode a payload, or keep a buffer.
4. **State the boundary rule.** Locating the first record at or after the declared start by its timestamp field
   alone is permitted once per file per boundary, and the run must state that the boundary is determined this way.
5. **Log before delivering.** The log entry is committed **before** the digest leaves the custodian (§5). This is
   the step that makes the rest auditable, and it is the one step that cannot be reconstructed later.
6. **Deliver the six items only.** Digest, function, byte count, endpoints, date — and nothing else, to the Gate 2
   manifest.

**What the digest is for.** Identity, not knowledge. It fixes which bytes the split refers to so that a later
mismatch is detectable. It certifies nothing about content, return, or admissibility, and it must never be
presented as if it did.

**One honest consequence.** Under this design the digest is checkable by the custodian and **not** by the analyst,
whose only check is the internal consistency of the log and manifest. That trust limit is structural, not
procedural, and the Gate 4 audit must record it rather than assume it away.

## 4. Prohibited acts, itemised

The custodian must not:

- **parse** — read structure, split fields, interpret types, or build rows, tables, or frames from reserved bytes;
- **decode** — decompress, decrypt, deserialise, or otherwise turn bytes into values;
- **inspect** — view, print, display, diff, or sample reserved content, and must not inspect a boundary record
  beyond the single timestamp-field location permitted in §3 step 4;
- **analyse** — compute any indicator, statistic, count by value, distribution, return, or comparison over reserved
  bytes, and must not form or record an opinion about what they contain;
- **disclose** — deliver, quote, describe, hint at, or characterise reserved content to the analyst or to anyone
  else, including by way of "it looked fine", "the file is intact", or any similar reassurance, which is itself an
  observation about the data;
- **retain** — keep a copy, cache, snapshot, working file, backup, or derivative of reserved bytes outside the
  custodian's own directory, or place one in the repository.

**The prohibition binds the description, not only the data.** A custodian who says "validation looks profitable"
or "there are about the expected number of rows" has delivered a result. Delivery is limited to §3 step 6.

## 5. Required logging

The log is the custodian's evidence of compliance and the only thing the analyst can audit.

| field | content |
|---|---|
| run timestamp | UTC date and time, to the minute |
| file | repository-relative path, or the declared external location if outside the repository |
| interval | declared start and end timestamps, with the boundary rule stated |
| algorithm | the digest function, exactly as executed |
| bytes | byte count streamed |
| digest | SHA-256 hex, lowercase |
| operator | the custodian's identity |
| script | the SHA-256 of the script that ran |

**Rules.** Each entry is committed **before** delivery. The log is append-only: no entry is edited, reordered,
deleted, or rewritten, and a correction is a new entry naming the entry it corrects. The log is committed with
the Gate 2 manifest and falls inside the Gate 4 audit scope.

**What the analyst may do with it:** check that entries, declared dates, and manifest hashes agree, and check the
script hash. What the analyst may **not** do is recompute any digest to confirm it — that is the contact this
whole instrument exists to prevent.

## 6. Separation between custody and research analysis

| function | who may hold it |
|---|---|
| holding the reserved files and running digests | the custodian |
| designing, implementing, and running the analysis | the analyst |
| approving objectives, risk, and stage authorizations | the owner |

**The custodian must not perform the analysis, and the analyst must not perform custody.** Where the owner is also
the custodian, the overlap is disclosed — protocol §11.1 permits a role overlap only if it is disclosed and the
audit is performed by someone else. The analyst may not be the custodian under any arrangement, because the whole
purpose is that the analyst's contact count stays at zero.

**No information may flow from the digest run to the analysis design.** A digest is a string. If the custodian
notices something during a run, the correct action is to stop and record a deviation (§8), not to mention it.

## 7. Revocation

- **By the owner, at any time, for any reason or none.** Revocation is effective on the UTC date in the revoking
  statement and does not require the custodian's agreement.
- **Effect.** Access ends immediately. Any in-progress run stops. The log is preserved in full, including any
  entries that appear incomplete, and no entry is tidied.
- **On revocation, the appointment is vacant.** No successor exists until a new instrument is signed; a vacancy is
  not a delegation to the analyst, and it does not reopen the reserved blocks.
- **Automatic by operation.** The appointment ends if the amendment is not adopted, if the amendment is repealed,
  if the custodian becomes the analyst, or at Gate 6, whichever comes first.
- **Recorded.** Every revocation and reappointment is a dated record naming this instrument by path and hash.

## 8. Incident handling

An **incident** is any reserved contact outside §3, any delivery beyond §3 step 6, any missing or late log entry,
any script run without a recorded hash, any copy of reserved bytes outside the custodian's directory, or any
disclosure of reserved content, however small and however well intentioned.

1. **Stop.** The run, the delivery, and the conversation about it stop immediately.
2. **Record.** A dated incident record states what happened, when, by whom, what was contacted, and what left the
   custodian. It is written from the evidence, not from recollection, and it is committed rather than filed
   privately.
3. **Disclose.** The incident is disclosed to the owner, and to the Gate 4 auditor at the audit. It is **not**
   disclosed to the analyst as content — the analyst learns that an incident occurred and its governance
   consequence, not what was seen.
4. **Assess.** Whether the incident affects admissibility of any result is the owner's question, informed by the
   Gate 4 audit. This instrument does not decide it, and an incident is not by itself a verdict on the data.
5. **Do not repair the record.** The log is not rewritten to look complete, no entry is back-filled, and no
   incident is resolved by later editing. §10.3 forbids exactly that.

**Precedent already in this programme.** The four Stage 2ZC boundary inspections and its full-file digests are
recorded as pre-amendment deviations (`Y-1`, `Y-2`). They are the model for how a deviation is written down: named,
dated, quantified, and neither concealed nor exaggerated.

## 9. When reserved material may be opened, if ever

**The custody procedure ends before any content is read.** Reset of the ordering:

| moment | what happens | who acts |
|---|---|---|
| Gate 2 registration | dates declared, digests computed and logged, split frozen | owner as custodian |
| Gate 3 | development block only; reserved blocks untouched | analyst, within dev permissions |
| Gate 4 | the implementation is independently audited; the log and procedure are audited here | auditor |
| Gate 5 | **the one look**: the validation interval is exported once to a read-only working copy, the export is logged, the frozen analysis runs once | owner exports; analyst runs the frozen plan |
| Gate 6 | the final research decision; OOS is used only if validation passed the pre-registered criteria | owner |

**Conditions on the one look, all of them:** the Gate 2 freeze has occurred; the Gate 4 audit has no open CRITICAL
or MAJOR finding (§8.8); the analysis plan is unchanged since the freeze; the export is logged before it happens;
and the copy's digest is recorded. A second export requires a new pre-registered stage under D-12 — not a new
request, a new registration.

**If validation fails, OOS is never opened.** That is the governing rule, not a preference: §8.2 allows the OOS
block to be used "only if validation passes the pre-registered criteria".

**Under `C-N` none of this can begin**, because there is no registered hypothesis for a look to test. The table
describes a route that a later decision would have to open, not a schedule.

## 10. Appointment record — blank

This table is the appointment. Empty, it appoints nobody.

| field | value |
|---|---|
| I appoint as custodian (name or role) | `________________` |
| The custodian is the owner, or is a third party | `________________` |
| The protocol amendment this appointment depends on, by path and SHA-256 | `________________` |
| I confirm the custodian is not the analyst | `________________` |
| I disclose any role overlap (§11.1) | `________________` |
| Access granted, in my words | `________________` |
| Conditions or qualifications | `________________` |
| Owner statement (verbatim) | `________________` |
| Effective date (UTC) | `________________` |
| Recorded by | `________________` |

**The agent has filled no field.** No name, date, identity, signature, or affirmation appears in this document.
Where the recommended appointee is the owner, the recommendation is a statement about who *could* hold the role,
not a statement that anyone does.

## 11. Integrity

- No custodian exists under the current protocol; the role is created only by the unadopted amendment.
- This instrument appoints no one, and a reader must not take the presence of a named recommended appointee in
  this file, or in `STAGE2ZH_METHODOLOGY_VALIDATION.md` §7, as an appointment.
- It is separate from the owner decision instrument: selecting `2ZD-4`'s custodian field is a recommendation about
  who should hold the role, and signing here is the act that confers it.
- It authorises no access to any dataset, no research, and no Gate 2 activity.

No reserved byte was read, streamed, decoded, or hashed in producing this instrument.
