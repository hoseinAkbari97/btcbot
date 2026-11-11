# Stage 2ZB — O-2 Owner Authorization Record

**Decision ID:** O-2
**Status:** **PENDING — NOT ACCEPTED. No O-2A activity was executed. Nothing is authorized by this record.**
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim word. No signature, date, or scope was supplied by
the agent on the owner's behalf.
**Instrument being authorized:** `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md`,
the hash-bound Stage 2ZA O-2 packet
**Option at issue:** `O-2A` — Gate 1 research-leg validity, documentary external evidence only
(activities A + D + B), as defined in the packet's §4.1 and specified in its §6.1
**Date recorded:** 2026-11-11 (UTC)

---

## 0. Outcome in one paragraph

The owner replied `confirm` immediately after an O-2A authorization declaration. The reply was verified
against the packet's own authorization requirements, and it does **not** meet them: it carries no date,
names neither the packet nor the option, and states no scope in the owner's own words or by reference to
the packet's §6.1. The packet is explicit about the consequence — a statement that does not name an
option authorizes nothing — so O-2A is **not** accepted as authorized. No Gate 1 data work, no venue
documentation collection, no readiness determination, and no disclosure work was performed. This record
is a **pending** authorization record: it preserves the owner's word, documents the gap, and asks for the
single missing formal statement. It records no decision and authorizes nothing.

---

## 1. What the owner was asked to decide

The O-2 packet puts one question to the owner (its §0): whether to authorize a named Gate 1
research-leg stage, and with which scope. It offers four options, each with its own consequences:

| option | scope | Gate 1 closable? |
|---|---|---|
| `O-2A` | activities A + D + B — readiness determination, Gate 1 data validity on the development block, published venue documents | **yes** |
| `O-2B` | activities A + D — data only | no — venue inputs stay UNKNOWN |
| `O-2C` | activities A + D + B + C — adds quote sampling | yes, but sampling is out of sequence |
| `O-2D` | defer; authorize nothing | no |

The packet recommends `O-2A` as the smallest scope that can close Gate 1's data-and-cost question
(packet §6). The recommendation is the agent's analysis, not an owner decision.

`O-2A` would permit, and only permit (packet §4.1):

1. recording the research-leg readiness determination (activity A);
2. the Gate 1 data work on the **development block only** — provenance, hash verification,
   data-quality report, alignment report, block separation (activity D);
3. collection of **published** venue facts with a dated source per fact, without contact, account
   change, or API use (activity B);
4. a Gate 1 record with the item-by-item venue disclosure under `P-5`, and a verdict of **passed** or
   **not passed**.

It would not permit new data acquisition, validation or out-of-sample rows, any signal or opportunity
count, any outcome, any backtest, any quote sampling, any venue contact, any order, any sizing, or any
trade.

---

## 2. The owner's response, verbatim

Recorded exactly as supplied. No word, punctuation mark, capitalisation, date, scope, or attribution was
added, removed, or reordered:

```
confirm
```

| field | value |
|---|---|
| words | 1 |
| characters | 7 |
| punctuation added | none |
| provenance | the owner's reply to the O-2A declaration reproduced in §3, in the Stage 2ZB session |
| date carried by the message | **none** — the message has no timestamp; the session date is 2026-11-11 (UTC) |
| agent-added words | none |

The reply does not name the packet, does not name `O-2A`, states no scope, and carries no date. It is a
single word of assent. §5 assesses it against the packet's authorization form and explains why that form
is not met.

---

## 3. The O-2A declaration to which the reply refers

The reply immediately follows this declaration, presented as the O-2A choice set. Reproduced exactly:

```
Decision: O-2A — AUTHORIZE.
Artifact: `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md`
SHA-256: `ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634`
```

| field | value |
|---|---|
| presented by | the agent, as the O-2A declaration in the Stage 2ZB instruction |
| nature | a restatement of **Choice `O-2A`** in the packet's §4.1; it adds no option and changes none |
| hash in the declaration | matches the packet's §1 binding and the Stage 2ZA freeze manifest — re-verified in §4 |
| scope stated in the declaration | **none** — it names a decision, an artifact, and a hash, and refers to no scope clause |
| owner's response to it | `confirm` (§2) |

The declaration names the option and the artifact. It does not state what `O-2A` permits, and it makes no
reference to the packet's §6.1, which is where the authorized scope is specified. That omission matters
in §5.

---

## 4. The packet, verified at recording time

| field | value |
|---|---|
| path | `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` |
| bytes | **21,990** |
| SHA256 | **`ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634`** |
| declared hash | the declaration in §3 — matches |
| bound in the Stage 2ZA manifest | `deliverables[1].sha256`, and `o2_status.packet` — both match |
| modified since the Stage 2Z package closed (`0bc3b27`) | no — the file's last commit is `07f7fab`, before that HEAD |
| newer or modified packet substituted | no |

| check | result |
|---|---|
| recomputed SHA256 of the packet at `HEAD` | `ab8c84d0…8634` — matches the declaration and the manifest |
| recomputed byte count | `21,990` — matches the manifest |
| adopted addendum still hash-bound | yes — 31,691 bytes, `b88db1e8…36dc`; O-1 record in force |
| any other Stage 2ZA file changed since `0bc3b27` | none |

The packet is therefore the exact artifact the owner was asked about. Verification of the instrument does
not supply the missing authorization: the defect in §5 is in the owner's statement, not in the packet.

---
