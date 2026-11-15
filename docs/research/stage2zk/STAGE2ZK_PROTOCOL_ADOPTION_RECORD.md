# Stage 2ZK — Protocol Adoption Record

**Decision ID:** adoption of the Stage 2ZI final protocol amendment
**Status:** **PENDING — NOT ADOPTED. The protocol text is unmodified and no versioned protocol artifact is created.**
The owner accepted the recommendation to adopt, but the amendment's own §8 requires specific acknowledgements the
message does not contain. The exact missing owner statement is prepared in §5.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word, value, date, condition, or signature is
added, removed, or reordered.
**Instrument to be adopted:** `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md`
**Instrument SHA-256:** `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` (18069 bytes)
**Amends:** `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §8.2, and nothing else
**Protocol SHA-256:** `be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058` (39850 bytes)
**Date recorded:** 2026-11-15 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and not a
> sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner accepted the recommendation to adopt the Stage 2ZI amendment. That acceptance is real but does not by itself
complete the adoption: the amendment's §8 sets seven minimum requirements, and the owner's message meets some and not
others. It names no hash, carries no UTC date, and — decisively — does not acknowledge finding `V-1` (the protocol was
previously unversioned, so `2.0.0` is an assigned first version) or findings `Y-1` and `Y-2` (the Stage 2ZC boundary
inspections and full-file digests are pre-amendment deviations). Those acknowledgements cannot be inferred from
context, and the amendment states that a statement which does not name the hash **adopts nothing**. Adoption is
therefore **pending**, the protocol text is **not edited**, and no versioned protocol artifact is produced. §5 sets out
the single missing owner statement.

---

## 1. Owner statement (verbatim)

The owner's affirmative words, recorded exactly as supplied:

```
I agree with your recommendation about decisions and those are my choices.
```

The same owner instruction also accepted the recommendation to adopt the Stage 2ZI protocol amendment. That acceptance
is recorded as reported, in the owner's own terms as conveyed. It contains no instrument path, no hash, no version
number, no acknowledgement of `V-1`, `Y-1`, or `Y-2`, and no date. No adoption wording is invented here.

---

## 2. The amendment's own adoption requirements

The amendment §8 states, in its own words, that an adopting statement must, at minimum:

1. identify this instrument by path and by the SHA-256 recorded in `docs/research/stage2zi/FREEZE_MANIFEST.json`;
2. state **adopt**, or adopt with the revisions listed;
3. carry a UTC date, which becomes the effective date under §3;
4. record the version as `2.0.0`, acknowledging finding `V-1` (the protocol was previously unversioned);
5. acknowledge `Y-1` and `Y-2` as recorded pre-amendment deviations, without grandfathering them unless the statement
   says so explicitly and in its own words;
6. be recorded verbatim, without agent paraphrase, in a record created for that purpose;
7. be accompanied by a manifest for the amended protocol text carrying SHA-256 hashes, byte counts, and a canonical
   self-hash, as §10.2 requires.

The amendment adds its own null consequence: *"A statement that does not name the hash adopts nothing, because the text
could otherwise change afterwards (addendum §14.1 sets this standard). The agent may not create, infer, pre-fill, or
paraphrase that statement."* Amendment §3 adds: *"The amendment takes effect on the UTC date written into the adopting
statement, and not before it. The agent assigns no date."*

---

## 3. Condition-by-condition assessment

| # | requirement | met by the owner's message? | why |
|---:|---|---|---|
| 1 | identifies the instrument by path and SHA-256 | **no** | the message names no document and no hash; the amendment states a statement that does not name the hash adopts nothing |
| 2 | states **adopt** | **in substance, but not against the instrument** | the owner accepted the recommendation to adopt, but names no instrument to adopt |
| 3 | carries a UTC date | **no** | the message carries no date; the amendment forbids the agent from assigning the effective date |
| 4 | records version `2.0.0` and acknowledges `V-1` | **no** | the message says nothing about versioning or the previously unversioned protocol |
| 5 | acknowledges `Y-1` and `Y-2` as pre-amendment deviations | **no** | the message does not mention either deviation, and the amendment requires the acknowledgement in the owner's own words |
| 6 | recorded verbatim | **yes** | the affirmation is reproduced exactly in §1 |
| 7 | accompanied by a manifest for the amended protocol text | **not yet applicable** | it is produced only on a completed adoption; none is produced here |

**The decisive gaps are 1, 3, 4, and 5.** Requirements 4 and 5 are substantive governance acknowledgements, not
formalities: the owner may or may not accept the `V-1` characterisation, and may or may not accept that `Y-1` and
`Y-2` are deviations. Those are the owner's to state, and the agent cannot infer them.

