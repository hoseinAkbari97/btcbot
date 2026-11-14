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
