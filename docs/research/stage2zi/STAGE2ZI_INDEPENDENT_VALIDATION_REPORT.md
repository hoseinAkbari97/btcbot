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

## 6. `S-1`, checked against D-02

**[F]** D-02 is resolved as option C with research-leg scope: maximum drawdown `15%`, per-trade limit `1.00R`,
tail limit `0.50R CVaR95`, position-size limit `$2,500` fixed notional, resolved 2026-11-10
(`STAGE2O_OWNER_RESPONSE_RECORD.md` line 26). The exact rule is `notional_usd ≤ $2,500` at entry (line 259).

**[D]** `S-1` — `R` is defined by the capped notional — satisfies the constraint by construction: if
`notional = $2,500` then `R = $2,500 × stop%`, and a per-trade loss of `1R` at that notional is inside the cap
whatever the stop distance. The competing option `S-2` keeps `1R = $100` and skips the trade instead; `S-1` takes
the trade at smaller size. Neither breaches D-02; they differ in which opportunity set survives.

**Checked for an implicit frequency or profitability claim, and none was found.** The formula
`R = min($100, $2,500 × stop%)` contains no count, no return, and no probability. Two consequences are stated
because a reader will otherwise infer the opposite of the truth: when the cap binds, `R` **falls**, so `0.10R` is
worth less and the number of trades needed for a fixed target **rises**. `S-1` therefore cannot be cited as
evidence that the objective is reachable; at its most favourable it leaves the objective where it was.

**[OWNER]** The `$250` target itself is `T-5` and is unanswered (`stage2t/STAGE2T_OWNER_RESPONSE_RECORD.md` §T-5,
fields blank). Nothing in this stage touches it, and `S-1` does not imply anything about it.

## 7. `E-2` and `26 bp`, checked for upgrade into evidence

| item | what it is | what it is not | check |
|---|---|---|---|
| `E-2` planning `σ`, `DE`, `p_exec` | labelled pre-registered assumptions with sensitivity ranges, declared at registration | an estimate, a census result, or a measured design effect | **[F]** packet §6.5 defines it that way; the proposal adds no measurement |
| `26 bp` cost basis | a labelled Binance spot proxy retained for planning | a Nobitex cost, a measured spread, or a fee schedule | **[F]** 2ZC cost record labels it; no `cost_R` is computed anywhere in this stage |

**Guarded boundary.** `E-2` and `E-1`/`E-3` differ in exactly one way: `E-1` and `E-3` authorize a
development-block census. `E-2` authorizes none. Since `B-11` forbids choosing `σ`, `DE`, or `p_exec` after
seeing an outcome, and since no census is authorized here, the values can only be declared assumptions. The
registration must carry the label, and the phrase "planning `DE` of `3.933333`" from the candidate-D census is a
development-block diagnostic, not a licence to reuse that number as a planning input.

**No measurement occurred in this stage**, so there is nothing that could have been upgraded. The check is that no
document says otherwise: `E-2` is called an assumption in every mention, and `26 bp` carries the word "proxy"
wherever it appears.

## 8. Status claims, checked one by one

Every status asserted by this stage's documents was matched to a source. None was inferred from silence, and none
was moved.

| status | asserted as | source | verdict |
|---|---|---|---|
| Gate 0 | **NOT PASSED** | `stage2x/STAGE2X_GOVERNANCE_STATUS_RECORD.md` line 42 | **[F]** unchanged; `R-08` `P` and `R-15` `B` still cap it |
| Gate 1 | **PASSED — research leg only** | `stage2zc/STAGE2ZC_GATE1_VERDICT.md` | **[F]** unchanged |
| Gate 2 | **NOT AUTHORIZED**, and now **unregistrable** under `C-N` | protocol §5.2 #1, §5.3 | **[D]** the first is standing; the second follows from the empty hypothesis slot |
| `T-4` | **deferred** | `stage2z/STAGE2Z_AUTHORIZATION_BOUNDARY.md` line 83 | **[F]** unchanged |
| `T-5` | **open** | `stage2t/STAGE2T_OWNER_RESPONSE_RECORD.md` §T-5 | **[F]** fields blank in the source |
| `R-08` | **`P`** | `stage2x` line 20 — real capital recorded, sizing convention deferred to `T-4` | **[F]** unchanged |
| `R-15` | **`B`** | `stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` line 29 | **[F]** unchanged |
| `C-4`, `C-6` | **unresolved** | `stage2zc/STAGE2ZC_FINAL_COMPLETION_REPORT.md` lines 195–196 | **[F]** unchanged |
| protocol | **unamended** | this stage did not edit it; hash matches the value 2ZD recorded | **[F]** unchanged |
| candidates B and D | **`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`** | census reports, frozen at `v2.0.0` | **[F]** unchanged; `C-N` does not revisit them |

**No document in this stage claims Gate 0 passed, Gate 2 authorized, or `T-4` resolved.** The closest risk is the
phrase "adoption-ready", which describes the *form* of an instrument and not the state of a gate; every use of it
here is paired with "unadopted" or "unsigned".

## 9. NOT VERIFIED, and why each one stops

These were attempted or considered and could not be completed inside this stage's boundary. They are recorded as
failures of verification, not as passes by omission.

| item | why it cannot be verified here | status |
|---|---|---|
| that the custodian's digest matches the reserved bytes | would require recomputing a digest over reserved bytes — the contact `R-b` forbids and this stage prohibits | **NOT VERIFIED** |
| that a record exists at each declared boundary date | requires opening a reserved interval | **NOT VERIFIED** |
| whether the four 2ZC boundary timestamps fell strictly inside a reserved interval | the 2ZC log records them as boundary records; the position is not determinable without contact, and the strict reading does not distinguish the cases | **NOT VERIFIED**, and recorded as unresolved in the amendment §7.3 |
| that the 2ZD-4 values are statistically adequate | adequacy depends on an exit policy that does not exist (`Z-3`), and any empirical check would need reserved data | **NOT VERIFIED**, **[OPEN]** |
| that `26 bp` is executable on Nobitex | requires execution measurement, which `C-6` leaves unresolved and this stage prohibits | **NOT VERIFIED**, unchanged from 2ZC |
| that the amendment yields a compliant procedure in practice | no digest run exists, the appointment is unsigned, and the protocol text is unamended | **NOT VERIFIED**, by construction |
| that `10,000` resamples is sufficient for the block bootstrap | a sufficiency claim would need the outcome distribution | **[OPEN]**, and deliberately not attempted |

**The pattern.** Every unverified item is unverified for the same reason: it needs reserved bytes, an outcome, or a
measurement. None is unverified because of time, and none is being deferred to a later stage of *this* kind. A
future stage that could verify them would need an authorization this one does not have.

## 10. Discrepancies found

| id | discrepancy | severity | treatment |
|---|---|---|---|
| `V-1` | the protocol requires versioned manifests but carries no version string | **material** | the amendment assigns `2.0.0` as a first version and says so; the adopting statement must acknowledge it |
| `V-2` | the amendment cannot itself edit §8.2, because §10.3 forbids changing a frozen artifact before adoption | low | recorded; the adopting statement must authorize the text change as a separate step |
| `X-4` | 2ZG cites "packet §7, issue `I-2`" for `Q-1`; the packet has no such issue, no §7 issue list, and no `Q-1` | **material to citation, nil to substance** | the owner decision instrument flags it in the row itself and again in a note |
| `X-5` | `2ZD-4` has five fields in the packet and seven in the proposal | low, disclosed | the addition is named, and it does not narrow the owner's five |
| `X-6` | the `90`-day embargo is derived and its agreement with `540 × 4 h` is exact but contingent | low | the registration should record the derivation, not the number |
| `Y-2` | the 2ZC full-file digests are reserved contact under `R-b`, a consequence 2ZH recorded only for the four boundary inspections | **material** | recorded as a pre-amendment deviation alongside `Y-1`, with the computational/governance distinction stated |

**No discrepancy was resolved by rewriting a governing document.** Each is either disclosed in the instrument that
depends on it or left for an owner act. That is the rule the brief set, and it is the rule that was followed.

**One correction of the record.** The chat summary that closed Stage 2ZH reported a truncated SHA-256 for the
reconciliation file that does not match its bytes; the file and manifest both carry
`9d9e1f5e089a38e44c5009c38eab3bc9160926ff92744d30bfe497ffc0b5314a`. The manifest was verified before use in this
stage, so no artifact was built on the wrong value, and this note exists because a hash that appears in
conversation and differs from the file is exactly the kind of thing a later reader should not have rediscover.

## 11. Unresolved questions, listed as questions

| # | question | who can answer it |
|---:|---|---|
| 1 | is any hypothesis to be registered at all, and if so which | owner — `C-N` says not now |
| 2 | what is the exit and holding policy | owner, via a registered rule; without it the episode and embargo arguments stay conditional |
| 3 | do `Y-1` and `Y-2` affect the admissibility of any 2ZC-derived result | owner, informed by the Gate 4 audit; this stage cannot investigate it without forbidden contact |
| 4 | is `Q-1` a decision the packet was meant to ask | owner, and a later documentation stage for the citation |
| 5 | what version number does the protocol carry today | nobody — it carries none; `2.0.0` is assigned, not inherited |
| 6 | how is a custodian's digest verified by anyone but the custodian | no answer exists under `R-b`; the trust limit is structural |
| 7 | does `T-5` keep the `$250` target | owner; fields blank |

## 12. What only the owner can do, after all of this

1. **Adopt the amendment** — dated, hash-named, acknowledging `V-1`, `Y-1`, and `Y-2`, in its own words.
2. **Ratify the seven selections** — in the decision instrument, or in a separate dated record that names it.
3. **Appoint the custodian** — signing the appointment instrument; the recommendation is not the act.
4. **Decide the hypothesis question** — or accept that Gate 2 stays unregistrable, which `C-N` already does.
5. **Answer `T-5` and the exit policy** if any later stage is to register anything.

None of the five can be performed, inferred, or pre-filled by the agent, and none is performed here.

## 13. This stage's own record

| item | count |
|---|---:|
| dataset files streamed | 0 |
| reserved bytes hashed | 0 |
| validation or OOS rows decoded | 0 |
| censuses, backtests, simulations, parameter fits | 0 |
| cost, spread, fee, depth, liquidity, slippage, fill, latency measurements | 0 |
| venue contacts, API keys, accounts, orders | 0 |
| predecessor documents modified | 0 |
| owner fields completed | 0 |
| gates changed | 0 |

Reads performed: committed repository documents only. Hashes computed: over this stage's own deliverables and over
committed predecessor documents — never over a dataset file.
