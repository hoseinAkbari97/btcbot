# Stage 2ZI — Independent Validation Report

**Scope:** verification of the Stage 2ZH deliverables, the two proposed instruments, and the seven proposed
selections against the governing documents, before anything was drafted on top of them.
**Status:** validation only. It ratifies nothing, adopts nothing, and changes no source.

## 1. Labels used here

| label | meaning | how to check it |
|---|---|---|
| **[F]** verified fact | recomputed or quoted from a named source in this repository | the source and line or section are given |
| **[D]** source-derived conclusion | follows from facts by stated reasoning, and could be wrong if the reasoning is | the reasoning is shown |
| **[REC]** recommendation | the agent's judgement, binding on no one | it is labelled, never presented as a finding |
| **[OPEN]** unresolved | not answerable with the available evidence, or forbidden to answer here | the reason is stated |
| **[OWNER]** owner affirmation required | cannot be performed, inferred, or pre-filled by the agent | the field is blank |

A **[D]** is not weaker than an **[F]**; it is differently checkable. The distinction exists so that a reader can
attack the reasoning without relitigating the arithmetic.

## 2. Repository state at the start of this stage

**[F]** HEAD `de4a3f0adf48f6e628650fece3b5fee243b79991`, equal to `origin/main`, worktree clean at the first
inspection of this stage.

**[F]** The predecessor manifests were verified under their own canonical procedures — SHA-256 over
`json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)` with `self_hash` removed:

| manifest | self-hash check | deliverables |
|---|---|---|
| `docs/research/stage2zh/FREEZE_MANIFEST.json` | **verifies** | 5/5 hashes and byte counts match |
| `docs/research/stage2zg/FREEZE_MANIFEST.json` | **verifies** | 3/3 hashes and byte counts match |
| `docs/research/stage2zd/FREEZE_MANIFEST.json` | **verifies** | re-verified in the Stage 2ZG and 2ZH records |

**[F]** Governing-source hashes, recomputed and unchanged from the values their own stages recorded:

| file | SHA-256 |
|---|---|
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | `be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058` |
| `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md` | `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42` |
| `stage2zg/STAGE2ZG_RECOMMENDATION_REPORT.md` | `09d35c3000e9ef9589bd153c26204da244973ffb774db99eb06a01ddf9cbf99c` |

**[F]** The five Stage 2ZH deliverables were hashed and compared to their manifest: all five matched, byte for
byte and in size. **No Stage 2ZH claim failed its own hash check.**

## 3. The amendment, checked against the protocol and its versioning rules

| check | result |
|---|---|
| §8.2 exists and contains the sentence being replaced | **[F]** "The exact dates and hashes are frozen at Gate 2" is the final sentence of §8.2 |
| §10.2 permits amendment by version | **[F]** "a major version changes a rule"; every version needs a manifest with hashes, byte counts, and a self-hash |
| §10.2 supplies a version to increment | **[F] no.** The protocol carries **no version string** in its header, its 896 lines, or its manifest. Recorded as finding `V-1` |
| the amendment changes one rule and nothing else | **[D]** one sentence replaced, one subsection added; `A-5` states non-derogation explicitly |
| the amendment removes the analyst's hash duty or the hash requirement | **[D] neither.** The duty moves to the custodian; the requirement survives via `A-3` |
| the amendment legalises the hash-only workaround | **[F] no.** `A-1′` is recorded as *not proposed*, and the analyst's contact stays prohibited |
| §10.3 (no retroactive editing) is respected | **[F]** §3 makes the amendment prospective; `Y-1` and `Y-2` are recorded, not grandfathered |
| the addendum needs an edit | **[F] no.** Addendum §10.4 restates D-12 and is silent on hashes, so it agrees with `R-b` |

**Finding `V-1`, restated for the record.** §10.2 requires semantic versions and a manifest per version, but the
protocol has never carried a version. The amendment therefore assigns `2.0.0` as "the first versioned form", and
the adopting statement must say so. An adopting statement that presents `2.0.0` as an increment from an earlier
protocol version would be describing a history that does not exist.

**Finding `V-2`.** The amended protocol would have to be committed as an edit to the protocol file itself, which
this stage did not do and could not do: §10.3 forbids changing a frozen artifact, and the amendment is unadopted.
The adopting statement therefore has to authorize the text change as a separate step. A reader who expects this
document to have already altered §8.2 will find that it has not.
