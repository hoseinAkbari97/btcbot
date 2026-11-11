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

## 4. The adopted artifact, verified at recording time

| field | value |
|---|---|
| path | `docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` |
| version | `1.0.0-draft` |
| bytes | **31,691** |
| SHA256 | **`b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc`** |
| finalized by commit | `2ab9cf1` ("docs(stage2z): add the preserved owner values, enumerated changes and adoption terms") |
| unchanged since finalization | yes — `git log 2ab9cf1..HEAD -- <path>` returns no commit, and the blob at `2ab9cf1` hashes to the same value |
| bound in the O-1 packet | §1 and §7 — both values match |
| bound in the Stage 2Z manifest | `addendum_binding.sha256` and `addendum_binding.bytes` — both match |

**Verification performed at recording time**

| check | result |
|---|---|
| recomputed SHA256 of the file at `HEAD` | `b88db1e8…36dc` — matches the declaration, the packet, and the manifest |
| recomputed byte count | `31,691` — matches |
| file content at `2ab9cf1` | identical hash and byte count — no post-decision edit, no substitution |
| any other stage2z file changed since `9ce1b93` | none |
| newer or modified artifact substituted | no |

A later edit to that file would change the hash and void this adoption record.

---

## 5. Effects of adoption

Under the addendum's §14.2, and only these:

1. **`P-1` through `P-5` become part of the governance text.** The protocol §3.5 prohibition is
   scoped to the capital base whose Gate 0 inputs are incomplete; Gate 0 status may be accompanied by
   a per-base assessment; `R-08` is read as real-capital-only; `R-15` is applied per its own `S`/`B`
   text; a future Gate 1 authorization must disclose venue-specification completeness item by item.
2. **A research-leg readiness determination may be recorded** under addendum §4.3 once its conditions
   hold. **It is not recorded by this document.** Stage 2ZA makes no status change; the determination
   is the first step of any O-2 authorization, as set out in
   `STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` §2 and §4.
3. **The failure rule is scoped** as described in addendum §6.2. A complete research-leg context is no
   longer blocked by an incomplete real-capital context — but still requires a separate, named stage
   authorization before any research.

None of the three effects authorizes any activity. Effect 3 removes a bar; it does not create a
permission.

---

## 6. What adoption does **not** do

This list is exhaustive for the adopted text as drafted. Adoption does **not**:

1. pass Gate 0, on the research leg or on real capital — the verdict remains **NOT PASSED**;
2. authorize Gate 1, or any other gate, or advance the gate sequence;
3. authorize market-data access, download, or processing;
4. authorize a feasibility census or any signal or opportunity count;
5. authorize venue research, contact, or capability checking;
6. authorize cost, spread, depth, liquidity, fill, slippage, or latency measurement;
7. authorize a backtest, simulation, expectancy, return, or P&L calculation;
8. authorize strategy or candidate design, naming, selection, or parameter fitting;
9. authorize validation or out-of-sample data access;
10. approve a real-capital sizing convention, risk amount, or risk percentage, or decide T-4;
11. move `R-08` or `R-15` beyond the precise readings in addendum §5;
12. close a blocker, mark a requirement satisfied, or change a status code;
13. resolve `C-4` or `C-6` (or `C-7`/`C-8`, which are preserved as recorded);
14. create, imply, or pre-fill O-2;
15. authorize paper trading, live trading, leverage, or bot execution;
16. change D-01–D-15, A-1–A-4, or any frozen artifact;
17. authorize Stage 3 or any research stage.

**Adoption makes a research-leg authorization permissible. It does not make any activity authorized.**

---

## 7. Governance status after this record

| item | status | changed by this record? |
|---|---|---|
| **O-1** | **ADOPTED 2026-11-11** (this record) | yes — from pending to adopted |
| **O-2** | **NOT AUTHORIZED — pending a separate owner decision** | no |
| Gate 0 | **NOT PASSED** (both bases) | no |
| research-leg readiness determination | **not recorded** | no |
| `R-08` | `P` — real-capital sizing convention deferred | no |
| `R-15` | `B` — real-capital objective not in testable form | no |
| T-4 | deferred | no |
| checklist | 16 S / 4 P / 0 O / 1 B / 2 N/A | no |
| D-01–D-15 | unchanged | no |
| A-1–A-4 | unchanged | no |
| Gate 1–6 sequence and criteria | unchanged | no |

The Stage 2Z packet and boundary documents state that O-1 is pending. That was true when they were
written. They are not edited; this record is the later instrument that supersedes that status
prospectively.

---

## 8. Integrity of this record

1. This record creates no decision. It records the owner's `I confirm` against the declaration in §2,
   under the addendum's own §14.1 mechanism, with the limitation in §3.3 disclosed.
2. It edits no adopted or historical document. The addendum, the O-1 packet, the conflict matrix, the
   Stage 2Z boundary, and the Stage 2Z manifest are byte-identical to their frozen versions.
3. It adds no owner value, threshold, condition, or exception.
4. It makes no claim that Gate 0 passed, that any gate advanced, or that any research is authorized.
5. If a future edit changes the addendum's bytes, this record's hash binding is void and a new O-1
   decision is required.

---
