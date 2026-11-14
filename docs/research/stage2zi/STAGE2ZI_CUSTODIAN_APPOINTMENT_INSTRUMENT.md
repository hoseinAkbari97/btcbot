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
