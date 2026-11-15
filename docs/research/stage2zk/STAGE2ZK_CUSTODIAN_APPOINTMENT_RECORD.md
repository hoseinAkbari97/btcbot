# Stage 2ZK — Custodian Appointment Record

**Decision ID:** appointment of the custodian under proposed protocol §8.2.1
**Status:** **PENDING — NO CUSTODIAN IS APPOINTED.** The owner's message accepts the `2ZD-4` custody *recommendation*
but is not the separate, named appointment the instrument requires. The appointment is also void while the amendment
is unadopted. The exact missing owner statement is prepared in §4.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word, name, value, date, or signature is added,
removed, or reordered.
**Instrument to be signed:** `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md`
**Instrument SHA-256:** `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` (13254 bytes)
**Depends on:** `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md`,
SHA-256 `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` — currently **not adopted**
**Date recorded:** 2026-11-15 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and not a
> sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner's message accepts the seven selections, one of which (`2ZD-4`, field 6) recommends the human owner as
custodian under the logged custody procedure. That is a **recommendation**, and the appointment instrument states in
its own words that it is not the appointment: appointment happens only by a separate written owner act. The owner's
message does not name a custodian, does not state that the custodian is the owner or a third party, does not confirm
the custodian is not the analyst, does not disclose a role overlap, does not state the access granted, and carries no
date. Independently, the appointment is **void unless the amendment is adopted first or at the same time**, and the
amendment is pending. The custodian is therefore **not appointed**, and §4 sets out the single missing owner statement.

---

## 1. Owner statement (verbatim)

The owner's affirmative words, recorded exactly as supplied:

```
I agree with your recommendation about decisions and those are my choices.
```

The `2ZD-4` custody recommendation is one of the seven selections that message answers. The message does not name a
custodian and does not use appointment wording.

---

## 2. What the appointment instrument requires

The instrument states, in its own words:

- §1: *"The recommendation is not an appointment. Under the amendment, appointment happens only by a written owner
  act. Until then this instrument is a form with empty fields, and the answer to 'who is the custodian?' remains
  **nobody**."*
- Header: *"the appointment is void unless the amendment in
  `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` is adopted first or at the same time. An appointment
  under a clause that does not exist appoints nobody."*
- §11: *"It is separate from the owner decision instrument: selecting `2ZD-4`'s custodian field is a recommendation
  about who should hold the role, and signing here is the act that confers it."*

The instrument's §10 appointment table is the act. Its fields are:

| field | content required |
|---|---|
| I appoint as custodian (name or role) | a name or role |
| The custodian is the owner, or is a third party | which |
| The protocol amendment this appointment depends on, by path and SHA-256 | the amendment binding |
| I confirm the custodian is not the analyst | confirmation |
| I disclose any role overlap (§11.1) | disclosure |
| Access granted, in my words | the scope |
| Conditions or qualifications | any |
| Owner statement (verbatim) | the owner's words |
| Effective date (UTC) | a date |
| Recorded by | who records it |

---

## 3. Assessment against the instrument

| requirement | met by the owner's message? | why |
|---|---|---|
| a separate written owner act of appointment | **no** | the message accepts a recommendation; the instrument states the recommendation is not the appointment |
| names the custodian (name or role) | **no** | no name or role is given |
| states owner or third party | **no** | not stated |
| confirms the custodian is not the analyst | **no** | not stated |
| discloses any role overlap (§11.1) | **no** | not stated |
| states the access granted, in the owner's words | **no** | not stated; the message states no scope |
| carries a UTC effective date | **no** | the message carries no date |
| the amendment is adopted first or at the same time | **no** | the amendment is pending (§ `STAGE2ZK_PROTOCOL_ADOPTION_RECORD.md`) |

**Two independent reasons the appointment does not exist.** First, the owner's message is an acceptance of a
recommendation, not the separate named appointment the instrument requires. Second, even a perfect appointment
statement would be void today, because the §8.2.1 clause it depends on is unadopted. The second reason alone is
sufficient, and the first is not curable by the second.

---

## 4. The missing owner statement, prepared (pending affirmation)

This is **not** written in the owner's voice as if already affirmed. It is the separate appointment statement the
instrument requires, labelled pending. It becomes effective only if the owner issues it **and** the amendment is
adopted first or at the same time.

```
Custodian appointment.
I appoint as custodian (name or role): ______________________
The custodian is [ the owner / a third party ].
The protocol amendment this appointment depends on: docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md
   (SHA-256 973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c), adopted [ before / at the same time as ] this appointment.
I confirm the custodian is not the analyst.
I disclose any role overlap (section 11.1): ______________________
Access granted, in my words: ______________________
Conditions or qualifications: ______________________
Effective date (UTC): ______________________
Recorded by: ______________________
```

**Other valid answers.** Appointing a third party instead of the owner is valid under the instrument and will be
recorded as written. A decision **not** to appoint a custodian is also valid; it leaves the role vacant, and it does
not delegate custody to the analyst or reopen the reserved blocks.

**On receipt**, and only if the amendment is adopted first or at the same time, the agent will record the statement
verbatim and bind it to the amendment hash. Until then, the answer to *"who is the custodian?"* remains **nobody**.

---

## 5. Restrictions preserved

If the appointment is later made, the instrument's restrictions bind it unchanged. They are restated here so they are
not lost:

- **Digest-only access.** The custodian may contact reserved bytes only to compute a declared digest — streaming the
  interval in file order through SHA-256, writing nothing but the digest and the byte count. Endpoints are declared in
  writing before the run; the script is committed and hashed before it runs.
- **No parsing, decoding, inspection, or analysis.** No structure, values, distributions, returns, or opinions about
  the reserved bytes. No "it looked fine" reassurance.
- **Append-only logging before delivery.** Every run is logged and the entry is committed **before** any digest is
  delivered. The log is append-only and is inside the Gate 4 audit scope.
- **Separation of custody and research.** The custodian must not perform the analysis; the analyst must not perform
  custody. The analyst may never be the custodian.
- **Revocation and incident handling.** Revocable by the owner at any time; any contact outside the procedure is an
  incident to be stopped, recorded from evidence, disclosed to the owner and the Gate 4 auditor, and never repaired
  by editing the record.
- **No opening of reserved material before the authorized protocol stage.** The one look at validation is at Gate 5
  only, after the Gate 2 freeze and the Gate 4 audit; OOS is used only if validation passes the pre-registered
  criteria.

Under `C-N` none of that can begin, because there is no registered hypothesis for a look to test.

---

## 6. Governance status after this record

| item | status | changed by this record? |
|---|---|---|
| custodian | **NOT APPOINTED — pending the statement in §4** | no |
| `2ZD-4` custody field | recorded as the owner's accepted **recommendation** | no |
| Stage 2ZI protocol amendment | **PENDING — NOT ADOPTED** | no |
| reserved blocks | closed; analyst contact count stays at zero | no |
| Gate 2 | **NOT AUTHORIZED** and unregistrable under `C-N` | no |
| Gate 0 / Gate 1 | **NOT PASSED** / **PASSED — research leg only** | no |

---

## 7. Integrity of this record

1. This record appoints nobody and authorizes no access to any dataset, no research, and no Gate 2 activity.
2. It edits no adopted, frozen, or historical document. The Stage 2ZI instruments and manifests are byte-identical
   to their committed versions.
3. It writes no owner name, role, date, or acknowledgement on the owner's behalf. The statement in §4 is labelled
   pending and is written in the third person, not in the owner's voice as if affirmed.
4. It makes no claim that a custodian exists, that the amendment was adopted, or that reserved material may be opened.
5. If the owner issues the §4 statement, it is recorded verbatim in a new record and bound to the amendment hash.
   This record is then superseded prospectively; it is not edited.


