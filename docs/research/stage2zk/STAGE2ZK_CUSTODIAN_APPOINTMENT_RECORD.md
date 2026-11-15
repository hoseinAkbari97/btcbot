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

