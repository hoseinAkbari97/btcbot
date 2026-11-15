# Stage 2ZK — Adoption Validation Report

**Scope:** independent verification of the Stage 2ZK records, the three owner acts, and every hash they depend on,
against the governing documents, before anything is relied on.
**Status:** validation only. It ratifies nothing, adopts nothing, appoints nobody, and changes no source.

---

## 1. Labels used here

| label | meaning | how to check it |
|---|---|---|
| **[F]** verified fact | recomputed or quoted from a named source in this repository | the source and line or section are given |
| **[D]** source-derived conclusion | follows from facts by stated reasoning, and could be wrong if the reasoning is | the reasoning is shown |
| **[REC]** recommendation | the agent's judgement, binding on no one | it is labelled, never presented as a finding |
| **[OPEN]** unresolved | not answerable with the available evidence, or forbidden to answer here | the reason is stated |
| **[OWNER]** owner affirmation required | cannot be performed, inferred, or pre-filled by the agent | the field is blank |

---

## 2. Repository state at the start of this stage

**[F]** Branch `main`, worktree clean, synchronized with `origin/main` at HEAD
`f48b714056ff712196f7cbc4cee5f7d4fb2f152c`, verified before any Stage 2ZK file was created.

**[F]** Working-session date: **2026-11-15 (UTC)**. The repository's convention, recorded in
`stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`, `stage2za/STAGE2ZA_O1_OWNER_ADOPTION_RECORD.md`,
`stage2zb/STAGE2ZB_O2_OWNER_AUTHORIZATION_RECORD.md`, and `stage2zc/STAGE2ZC_O2_OWNER_AUTHORIZATION_RECORD.md`,
permits the agent to assign the working-session date as the **recording** date. It does **not** permit the agent to
assign an owner's adoption effective date, which amendment §3 reserves to the owner.

---

## 3. Hashes and sizes, recomputed from actual bytes

**[F]** The six Stage 2ZI artifacts, at the bytes on disk:

| artifact | SHA-256 | bytes |
|---|---|---:|
| `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 |
| `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md` | `c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232` | 10082 |
| `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 |
| `docs/research/stage2zi/STAGE2ZI_INDEPENDENT_VALIDATION_REPORT.md` | `fe7a3fde126b3ff942654943204b543b79136ba9c5c24aa0f9e84d81af18d3e8` | 20154 |
| `docs/research/stage2zi/STAGE2ZI_AUTHORIZATION_BOUNDARY.md` | `4cb3cd86987edc22f591656fd30bc916a7d4b23efd4a67c3b9f7935a1a259f39` | 6871 |
| `docs/research/stage2zi/FREEZE_MANIFEST.json` | `d1473fb5a635de76c561912b5f18dbfaf0f5ead7723a0034e6659b16f51900e7` | 15731 |

**[F]** Every one of the five deliverable hashes and byte counts matches the Stage 2ZI manifest's `deliverables[]`, and
the manifest's own `self_hash` recomputes to its stored value `6a9694d6…69c84c` under the canonical procedure.

**[F]** The governing sources, recomputed:

| file | SHA-256 | bytes |
|---|---|---:|
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | `be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058` | 39850 |
| `stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` | `b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc` | 31691 |
| `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md` | `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42` | 14986 |
| `stage2m/OWNER_DECISION_REGISTER.md` | `f67fa8de5e197a7391f84dd722a71803d57436e43e001b0151ce372c0a637f74` | 26674 |
| `stage2zg/STAGE2ZG_RECOMMENDATION_REPORT.md` | `09d35c3000e9ef9589bd153c26204da244973ffb774db99eb06a01ddf9cbf99c` | 21357 |
| `docs/briefings/STAGE2ZJ_OWNER_DECISION_BRIEFING.md` | `1b6c885245d9605a639e43e300afc7b62d50aea16be1042b737293b8e75f74b1` | 22958 |

**[F]** The protocol and addendum hashes match the values their own stages recorded; the packet and 2ZG hashes match
the Stage 2ZI manifest's `governing_sources`.

---

## 4. Predecessor manifests, verified

**[F]** Each predecessor manifest's self-hash was recomputed under the same canonical procedure — SHA-256 over
`json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=False)` with the self-hash field removed:

| manifest | stored self-hash | recomputed | result |
|---|---|---|---|
| `stage2zi/FREEZE_MANIFEST.json` | `6a9694d6…69c84c` | matches | **verifies** |
| `stage2zh/FREEZE_MANIFEST.json` | `f3910ac7…09bd3e` | matches | **verifies** |
| `stage2zg/FREEZE_MANIFEST.json` | `3d7830aa…5cf738a` | matches | **verifies** |
| `stage2zd/FREEZE_MANIFEST.json` | `b902597e…dd9d58c` | matches | **verifies** |
| `stage2zc/FREEZE_MANIFEST.json` | `1e161459…13925a2` | matches | **verifies** |
| `stage2z/FREEZE_MANIFEST.json` | `cc29845e…367d45b` | matches | **verifies** |

No predecessor artifact was modified by this stage.

---

## 5. The three acts, validated

### 5.1 Owner decisions — validated as recorded

**[F]** The seven selections in `STAGE2ZK_OWNER_DECISION_RECORD.md` §2 are identical, value for value, to the seven
proposed selections in the Stage 2ZI owner decision instrument §3, and the `2ZD-4` values and qualifications in §3
match the instrument's §4 table. **[D]** The owner's message is a valid object for those selections: it confirms the
list presented immediately before it, and no other option set is named.

**[F]** The record discloses the one formality limitation — the message names neither the instrument path nor its
hash — and offers a cure, following the Stage 2ZA O-1 precedent. **[D]** The limitation does not change any decision,
because the hash condition exists to prevent post-decision text substitution, and the instrument hash was
independently re-verified (`c7f6eebf…a996232`).

### 5.2 Protocol adoption — validated as pending

**[F]** The amendment §8 requires seven elements, and the owner's message meets condition 6 (recorded verbatim) but
not conditions 1, 3, 4, or 5. **[F]** The amendment's own text states that a statement which does not name the hash
adopts nothing, and amendment §3 forbids the agent from assigning the effective date. **[D]** Requirements 4 and 5 —
acknowledging `V-1`, and acknowledging `Y-1` and `Y-2` — are owner judgements that cannot be inferred from the
message or from any context. Adoption is therefore correctly recorded as **pending**, and the protocol is correctly
left unmodified.

**[F]** The protocol file is byte-identical to its committed version (`be5a61bf…34c058`, 39850 bytes); §8.2 still
contains the sentence the amendment would replace, and no §8.2.1 exists. **[F]** No versioned protocol artifact and
no amended-protocol manifest were produced.

### 5.3 Custodian appointment — validated as pending

**[F]** The appointment instrument states that its §10 table is the act, and that selecting `2ZD-4`'s custody field is
a recommendation. The owner's message names no custodian and states none of the table's fields. **[D]** The
appointment is correctly recorded as **not made**. **[F]** Independently, the instrument is void while the amendment
is unadopted, so no valid appointment could exist today.

---

## 6. Which of the three acts are complete, and which are pending

| act | state | reason |
|---|---|---|
| **Owner decisions (`2ZD-0`…`Q-1`)** | **COMPLETE — recorded** | the owner affirmed all seven; the record discloses the one formality limitation and offers a cure |
| **Protocol amendment adoption** | **PENDING — not adopted** | amendment §8 conditions 1, 3, 4, 5 unmet; `V-1`, `Y-1`, `Y-2` acknowledgements cannot be inferred |
| **Custodian appointment** | **PENDING — not made** | the instrument requires a separate named appointment; also void while the amendment is unadopted |

**The complete act's boundary.** Recording the seven decisions changes no authorization boundary. It authorizes no
data access, no census, no backtest, no strategy design, and no Gate 2 opening. `R-b` remains a selection without
operative text until the amendment is adopted.

---

## 7. NOT VERIFIED, and why each stops

| item | why it cannot be verified here | status |
|---|---|---|
| that the owner accepts finding `V-1` | requires the owner's own acknowledgement in the adopting statement | **NOT VERIFIED** — pending |
| that the owner accepts `Y-1` and `Y-2` as pre-amendment deviations | requires the owner's own words; the agent may not infer it | **NOT VERIFIED** — pending |
| the effective date of any adoption | amendment §3 reserves it to the owner's statement | **NOT VERIFIED** — pending |
| that the custodian will be the owner | the appointment is a separate owner act not yet issued | **NOT VERIFIED** — pending |
| that the custodian's digest matches the reserved bytes | would require recomputing a digest over reserved bytes — the contact `R-b` forbids | **NOT VERIFIED** |
| whether the four Stage 2ZC boundary timestamps fell strictly inside a reserved interval | not determinable without forbidden contact; the strict reading does not distinguish the cases | **NOT VERIFIED**, recorded as unresolved |
| that the `2ZD-4` values are statistically adequate | adequacy depends on an exit policy that does not exist (`Z-3`) | **NOT VERIFIED**, **[OPEN]** |
| that `26 bp` is executable on Nobitex | requires execution measurement, which `C-6` leaves unresolved | **NOT VERIFIED** |

**The pattern.** Every unverified item needs either the owner's own statement or reserved bytes. None is unverified
because of time, and none is being deferred to a later stage of this kind.

---

## 8. This stage's own record

| item | count |
|---|---:|
| dataset files streamed | 0 |
| reserved bytes hashed | 0 |
| validation or OOS rows decoded | 0 |
| censuses, backtests, simulations, parameter fits | 0 |
| cost, spread, fee, depth, liquidity, slippage, fill, latency measurements | 0 |
| quote samples | 0 |
| venue contacts, API keys, accounts, orders | 0 |
| predecessor or frozen artifacts modified | 0 |
| protocol text changed | 0 |
| owner fields completed in a predecessor | 0 |
| owner signatures or dates invented | 0 |
| gates changed | 0 |

Reads performed: committed repository documents only. Hashes computed: over this stage's own deliverables and over
committed predecessor documents — never over a dataset file.

---

## 9. Integrity of this report

1. It ratifies nothing, adopts nothing, appoints nobody, and authorizes no activity.
2. It changes no source. Every artifact it cites is byte-identical to its committed version.
3. It records no owner acknowledgement that the owner did not make, and treats the two incomplete acts as pending.
4. It makes no claim that Gate 0 passed, that Gate 2 was authorized or registered, or that any research occurred.


