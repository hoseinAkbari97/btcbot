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

## 4. The seven selections, checked against the packet

Each proposed selection was matched to the packet text it claims to come from. The identifiers are the packet's
own, and the option letters are the packet's own.

| selection | packet location | the option is in the instrument | verdict |
|---|---|---|---|
| `2ZD-0 = C` | §5, path table | yes — path C, "resolve the protocol interpretation and owner decisions first" | **[F]** present |
| `2ZD-1 = R-b` | §6.1, reading table | yes — "any byte contact is a read" | **[F]** present |
| `2ZD-2 = C-N` | §6.2, candidate table | yes — "no selection now; keep both as unselected" | **[F]** present |
| `2ZD-3 = S-1` | §6.3, rule table | yes — `R` shrinks with the capped notional | **[F]** present |
| `2ZD-4` | §6.4, parameter table | the packet asks for five fields; the proposal supplies seven, adding resample count and seed | **[D]** a superset, not a substitution |
| `2ZD-5 = E-2` | §6.5, route table | yes — "labelled pre-registered assumptions" with sensitivity ranges | **[F]** present |
| `Q-1` | **not in the packet** | no — the packet has no `Q-1` and no §7 issue list | **[F]** missing; see `X-4` |

**Finding `X-4`.** Stage 2ZG introduced `Q-1` as "measured cost (packet §7, issue `I-2`)". The packet's §7 is a
table of artifact hashes, and a full text search of `stage2zd/` returns **no** occurrence of `Q-1`, `I-2`, or any
cost question. `Q-1` is therefore a legitimate question that the packet does not ask. Nothing about the proposed
answer depends on the citation — it is the `26 bp` label from the 2ZC cost record — but the reference chain is
broken and the owner decision instrument says so rather than repeating it.

**Finding `X-5`.** `2ZD-4` as the packet writes it has five fields (episode, block, embargo, custody, opening).
Stage 2ZH and 2ZI add two — the resample count and the seed — because the registration cannot be reproduced
without them. The addition is disclosed, and it does not narrow the owner's five. It does mean that a signature on
`2ZD-4` covers seven values, two of which the packet never asked for.

## 5. The 2ZD-4 values, checked against their sources

| value | source checked | what the source actually says | verdict |
|---|---|---|---|
| episode = maximal contiguous 4 h `budget_ok` run | `CANDIDATE_D_CENSUS_REPORT.md` §6; `CANDIDATE_D_SPEC.md` §6 | the maximal `budget_ok == True` 4 h run containing the signal instant; 212 runs | **[F]** matches |
| block = 14 calendar days | `stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md` line 69 | "14-calendar-day block bootstrap" | **[F]** matches; a convention, not a requirement |
| 10,000 resamples | `STRATEGY_2_RECOMMENDATION.md` line 216 | "10,000 resamples" | **[F]** matches; appears in no protocol, register, 2J plan, or Stage 6 requirement |
| seed `20240101` | same line | "seed `20240101`" | **[F]** matches; same single-source status |
| embargo = 90 days | `CANDIDATE_D_SPEC.md` §6 (540-bar lookback) | `540 × 4 h = 2,160 h = 90 days` | **[D]** arithmetic exact; derived, not mandated |
| custodian = the owner | protocol and addendum, full text | the word "custodian" **does not occur** in either | **[F]** new role; **[OWNER]** appointment |
| opening = after Gate 2 freeze and Gate 4 audit, at Gate 5 | protocol §2.2, §8.2, §8.8; packet §6.4 | §2.2 orders Gate 4 before Gate 5; §8.8 rejects on an open CRITICAL/MAJOR finding | **[D]** consistent; the audit condition is the protocol's sequence made explicit |

**Finding `X-6`.** The `90`-day figure is the only 2ZD-4 value that is neither inherited nor mandated but
**derived**, and its derivation is a coincidence that happens to be exact: `540` bars of `4 h` is `2,160` hours,
which is `90` days to the hour. If the lookback were `540` bars of a different timeframe, or the embargo expressed
in bars, the agreement would break. The registration should record the derivation rather than the number, so that a
future change to the lookback surfaces as a change to the embargo.

**What is not claimed.** None of these checks establishes that the values are statistically adequate. The episode
definition's adequacy depends on an exit policy that does not exist (finding `Z-3`), the block length is a
convention, and the resample count and seed are comparability and reproducibility choices. **Supported is not the
same as sufficient**, and this stage does not upgrade one into the other.
