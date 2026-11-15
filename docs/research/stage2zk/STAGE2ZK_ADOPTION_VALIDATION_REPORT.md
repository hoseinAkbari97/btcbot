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
