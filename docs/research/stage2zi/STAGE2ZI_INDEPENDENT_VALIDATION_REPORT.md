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
