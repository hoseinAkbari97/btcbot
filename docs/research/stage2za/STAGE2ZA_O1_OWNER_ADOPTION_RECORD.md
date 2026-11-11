# Stage 2ZA — O-1 Owner Adoption Record

**Decision ID:** O-1
**Status:** **ADOPTED BY THE OWNER on 2026-11-11.** Recorded under the addendum's own §14.1
mechanism, with the single formality limitation disclosed in §3.3.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word is added, removed, or
reordered, and no signature is invented.
**Adopted instrument:** `docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md`,
version `1.0.0-draft`
**Date recorded:** 2026-11-11 (UTC)

---

## 1. Owner statement (verbatim)

Recorded exactly as supplied. No word, punctuation mark, capitalisation, or date was added, removed,
or reordered:

```
I confirm
```

| field | value |
|---|---|
| words | 2 |
| characters | 9 (including the single space between the two words) |
| punctuation added | none |
| provenance | the owner's reply to the O-1 declaration reproduced in §2, in the Stage 2ZA session |
| date | **2026-11-11** (UTC) — the working-session date recorded throughout Stage 2U–2Z |
| agent-added words | none |

The reply does not itself contain the word "adopt". It confirms the declaration that immediately
precedes it, which states the decision as **O-1 — ADOPT** and names the path and the SHA256. §3
assesses that arrangement against the addendum's own adoption mechanism and discloses its one
limitation; §4 verifies that the hash-bound file is unchanged.

---

## 2. The O-1 declaration to which the reply refers

The reply follows this declaration, presented immediately before it. Reproduced exactly:

```
Decision: O-1 — ADOPT.
Artifact: `docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md`
SHA-256: `b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc`
```

| field | value |
|---|---|
| presented by | the agent, as the O-1 choice set in the Stage 2ZA instruction |
| nature | a restatement of **Choice A** in `stage2z/STAGE2Z_O1_OWNER_DECISION_PACKET.md` §3.1; it adds no option and changes none |
| hash in the declaration | matches the packet's §1 and §7, and the Stage 2Z freeze manifest's `addendum_binding` record |
| owner's response to it | `I confirm` (§1) |

The declaration names no conditions, no revisions, and no exceptions. The reply adds none.

---

## 3. Formality assessment against the addendum's adoption mechanism

The addendum's §14.1 — restated in `stage2z/STAGE2Z_O1_OWNER_DECISION_PACKET.md` §7 — requires a
written owner statement that:

1. identifies the document by path and by the SHA256;
2. states **adopt** (or adopt with listed revisions);
3. carries a date; and
4. is recorded verbatim, without agent paraphrase.

### 3.1 Condition by condition

| # | condition | how it is satisfied | residual |
|---|---|---|---|
| 1 | names the path and SHA256 | the reply confirms, without qualification or condition, the declaration in §2, which names both; the hash is independently re-verified against the file now on disk in §4; the declaration is the unique and immediate subject of the reply | the owner's own two words do not independently restate the hash — see §3.3 |
| 2 | states adopt | the confirmed declaration states **O-1 — ADOPT**; no other option (reject, revise) is named in the declaration or the reply, so `I confirm` has one possible object | the token "adopt" appears in the confirmed declaration, not in the owner's two words |
| 3 | carries a date | **2026-11-11** (UTC), the working-session date recorded throughout Stage 2U–2Z; the owner's message carries no separate timestamp | none material |
| 4 | is recorded verbatim | §1 reproduces the reply exactly; §2 reproduces the confirmed declaration exactly; no paraphrase is used as evidence | none |

### 3.2 Why the exchange is treated as an adoption, not as a different act

1. **The hash condition exists for a stated reason.** §14.1 says a statement that does not name the
   hash "adopts nothing, because the text could otherwise change after the decision." The reason is
   post-decision text substitution. That reason is fully served here: the hash named in the confirmed
   declaration is the hash of the file at `HEAD` (§4), the file was finalized in commit `2ab9cf1`, and
   no commit since has touched it.
2. **The reply is not a generic assent.** It answers a declaration that names one instrument, one
   version, one hash, and one decision. Removing the declaration would change what the reply means;
   the two are a single exchange.
3. **The agent does not cure anything by interpretation.** It records the owner's words exactly,
   reports the literal gap, and verifies the hash independently. The adoption rests on the owner's
   words plus a verified artifact, not on an agent's reading of intent.

### 3.3 The single disclosed limitation

The owner's written statement is two words and does not itself name the path or the SHA256. Read
literally and in isolation, `I confirm` would not satisfy condition 1. This record does not conceal
that. It treats the reply as confirming the specific declaration in §2 — which is what the reply is,
and what the Stage 2ZA instruction records it as — and it verifies the hash independently.

**Optional cure, available to the owner only.** If the owner wants the record to be self-contained
under the strictest reading, one dated line restating the path, the SHA256, and the word "adopt" is
sufficient. The agent will record it verbatim and append it to this record. Until and unless that
happens, this record stands as the adoption record, and the adopted text is the hash-bound file
verified in §4.

### 3.4 What was not done

No signature, affirmation, or decision was created or inferred. No field in
`stage2z/STAGE2Z_O1_OWNER_DECISION_PACKET.md` §7 was filled in: that packet remains the historical
decision form for the draft as issued, with every field blank. This record is a new instrument; it
does not edit the packet.

---
