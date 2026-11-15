# Stage 2ZN — Custodian Appointment Record

**Decision ID:** appointment of the custodian under adopted protocol §8.2.1
**Status:** **APPOINTED — effective 2026-11-15 (UTC).** The owner appointed themselves as custodian, conditional on
adoption of the amendment. The amendment was adopted the same day (protocol version `2.0.0`), so the condition is
met and the appointment is in force.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word, name, value, or date is added, removed,
or reordered.
**Instrument:** `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md`
**Instrument SHA-256:** `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` (13254 bytes)
**Depends on:** the adopted amendment — protocol `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` version
`2.0.0`, SHA-256 `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a`, adopted 2026-11-15 (UTC)
**Custodian:** **Hossein Akbari** (the owner)
**Effective date:** 2026-11-15 (UTC)
**Date recorded:** 2026-11-15 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and not a
> sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner appointed themselves as custodian under the exact terms and restrictions of the custodian appointment
instrument, conditional on adoption of the amendment. The amendment was adopted on 2026-11-15 (UTC), so the
appointment is now in force: **Hossein Akbari is both the owner and the custodian**, and the role overlap is
disclosed. The appointment creates the single party permitted reserved contact, strictly for declared SHA-256 digest
runs under protocol §8.2.1 (`A-2`–`A-4`). It authorizes no research, no analyst contact with reserved bytes, and no
Gate 2 activity. The independent Gate 4 auditor is an outstanding operational dependency (§4); none is appointed
here.

---

## 1. Owner affirmation (verbatim)

Recorded exactly as supplied:

```
I appoint myself, Hossein Akbari, as custodian under the exact terms and restrictions of the custodian appointment instrument, conditional on adoption of the amendment.
```

| field | value |
|---|---|
| words | 24 |
| characters | 168 |
| provenance | the owner's written affirmation in the Stage 2ZN session |
| recorded UTC date | **2026-11-15** |
| agent-added words | none |

---

## 2. The appointment

| field | value |
|---|---|
| appointed as custodian | **Hossein Akbari** |
| the custodian is | **the owner** |
| the custodian is not the analyst | confirmed |
| instrument relied on | `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md`, SHA-256 `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` |
| dependency | adoption of the Stage 2ZI amendment — **met** on 2026-11-15 (UTC), protocol `2.0.0` |
| effective date | 2026-11-15 (UTC) |
| role overlap (§11.1) | **disclosed** — the owner is also the custodian; the Gate 4 audit must be performed by someone other than the custodian |

**Conditional language preserved.** The owner's affirmation is *"conditional on adoption of the amendment."* Because
the amendment is adopted, the condition is satisfied and the appointment takes effect on the same UTC date. Had the
amendment not been adopted, the appointment would be void.

---

## 3. Restrictions preserved

The appointment is bound by every restriction of the instrument, unchanged:

- **Digest-only access.** Only a declared SHA-256 digest of a declared reserved interval may be computed. Bytes are
  streamed in file order, without transformation; the output is the digest and the byte count, and nothing else.
- **No parsing, decoding, inspection, or analysis.** No structure, values, distributions, counts by value, returns,
  or opinions about reserved content; no "it looked fine" reassurance.
- **Append-only logging before delivery.** Every run is logged and the entry is committed **before** any digest is
  delivered; no entry is edited, reordered, deleted, or reconstructed; a correction is a new entry naming the entry
  it corrects.
- **Separation of custody and research analysis.** The custodian must not perform the analysis; the analyst must not
  perform custody; the analyst may never be the custodian; no information from a digest run may influence the
  research design.
- **Revocation and incident handling.** Revocable by the owner at any time, effective on the UTC date in the revoking
  statement; any reserved contact outside the procedure is an incident — stop, record from evidence, disclose to the
  owner and the Gate 4 auditor, assess admissibility as the owner's question, and never repair the record by editing
  it.
- **No opening of reserved material before the authorized protocol stage.** The one look at validation is at Gate 5
  only, after the Gate 2 freeze and the Gate 4 audit, and out-of-sample is used only if validation passes the
  pre-registered criteria.

**No reserved contact is authorized or performed now.** Under `C-N` there is no registered hypothesis, so no digest
run is yet warranted; and no reserved byte was read, streamed, hashed, parsed, or decoded in this stage. In
particular, the Stage 2ZC full-file digests (`Y-2`) were **not** recomputed.

---

## 4. Outstanding operational dependency — independent Gate 4 auditor

The instrument requires that, where the owner is also the custodian, the role overlap be disclosed (§11.1) and the
Gate 4 audit be performed by **someone other than the custodian**. No independent auditor exists on this programme
yet. This is recorded as an **outstanding operational dependency**:

- the Gate 4 audit must be performed by a party who is **not** the custodian and has **no prior involvement** in the
  design or implementation (protocol principle 6);
- **no auditor is appointed, named, or invented here**; appointing one is a separate owner act;
- the dependency blocks nothing before Gate 4, and it does not reopen the reserved blocks.

---

## 5. Integrity of this record

1. This record appoints the custodian and nothing else. It authorizes no data access, no research, and no Gate 2
   activity.
2. The instrument (`4db9d1…5aa22`) is byte-identical to its committed version; the adopted amendment
   (`973da9…d92c`) is likewise unchanged.
3. No owner word, name, value, or date was invented. The name and the self-appointment are the owner's own.
4. It makes no claim that a digest run occurred, that reserved material was opened, or that Gate 2 advanced.
5. No reserved byte was read, streamed, decoded, or hashed in producing this record.
