# Stage 2ZG — Delegated Decision Recommendations

**Stage:** 2ZG (delegated recommendation and formalization preparation)
**Date:** 2026-11-14 (UTC)
**Status:** **a recommendation package. Nothing in it is a decision, an authorization, or a signature.**
**Delegation:** the owner asked a delegated recommender for the best substantive choices; this report
carries those choices, tests each against the governing text, and records what it could not settle.

## 1. Starting state, verified

| item | expected | observed |
|---|---|---|
| branch | `main` | `main` |
| HEAD | `4fdddc7b92d3eadc136451e969afb70e180e3ea8` | matched, equal to `origin/main` |
| worktree | clean | clean |
| 2ZF validation report | present | present, `f74054bc…63d3ff` |
| 2ZD packet | `042f0497…7fe8e42` | matched, 14,986 bytes |
| `docs/research/stage2zg/` | absent | absent |

## 2. Sources read for this report

Every recommendation below cites one of these; their hashes are in `FREEZE_MANIFEST.json` under
`governing_sources`.

- `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §5.2, §5.3, §8.2, §8.3, §8.4 — the registration inputs, the pass
  criteria, the three-block split, the embargo requirement, and the one-primary rule.
- `stage2m/OWNER_DECISION_REGISTER.md` D-02, D-08, D-09, D-10, D-11, D-12 — the adopted standards.
- `stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3.4 — the pre-specified dependence policy.
- `stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` §7.4, §9.2, §10.4 — the adopted
  controls that constrain this stage.
- `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md` §5, §6 — the decision text being recommended on.
- `stage2e_v2/CANDIDATE_D_SPEC.md` §2.2, §6, §8, §9 — candidate D's session, regime, cost, and non-overlap
  construction.
- `stage2j/CANDIDATE_B_CENSUS_REPORT.md` and `CANDIDATE_D_CENSUS_REPORT.md` §5, §6, §10 — the recorded
  counts, design effects, and verdicts.
- `stage2zc/` range-and-hash record, access log, and cost-assumption record — the only recorded data contact.

## 3. How the report separates three kinds of statement

- **[F] source fact** — quoted or counted from a committed document, with its section.
- **[R] reasoning** — an inference from those facts, stated so it can be argued with.
- **[REC] recommendation** — a choice proposed for the owner, which binds nobody until ratified.

A recommendation is never presented as a finding. Where a fact undercuts a recommendation, the report says
so in the same section rather than in a footnote.

## 4. Decision 2ZD-0 — recommended: `C`

**[F]** The packet offers four paths (§5). Path C resolves "the protocol interpretation and owner decisions
first" and authorizes "the §8.2/D-12 ruling plus the four non-data Gate 2 decisions, and a Gate 2
specification reflecting them".

**[F]** Four of its six blockers need no data: B-1 (candidate), B-2 (cap against tight stops), B-3 (the
hashing question), B-5 (the dependence numbers). B-4 needs a route rather than data if `E-2` is adopted (§9).
**[R]** Path C is the only option that can close B-1, B-2, B-3, and B-5 without a guess, and it closes them
before any outcome exists, so nothing it settles can be informed by one.

**[REC] `2ZD-0 = C`.** It authorizes governance resolution and a Gate 2 *specification*, not Gate 2.

**Rejected:** `A` — Gate 2 cannot pass today (2 of 16 inputs satisfied), so A forces guesses or an implicit
amendment. `B` — builds the template while leaving the interpretation gap open. `D` — closes nothing;
legitimate only if the owner intends to pause.

## 5. Decision 2ZD-1 — recommended: `R-a`

**[F]** Protocol §8.2 requires that "the exact dates and hashes are frozen at Gate 2". D-12 (register) and
addendum §10.4 forbid reading "any validation or OOS row" before its gate. Neither text defines "read", and
neither mentions hashing.

**[F]** The two requirements cannot both hold for a hash over reserved bytes unless hashing is not a read:
option `R-b` makes §8.2 permanently unsatisfiable without an amendment (packet §6.1, consequence column).
**[R]** Hashing is whole-block and non-interpretive: SHA-256 consumes bytes and yields a digest from which no
row can be reconstructed. D-12 uses "read" in the sense of inspecting content — the sense in which §8.2 asks
for a hash it would forbid obtaining by inspection.

**[REC] `2ZD-1 = R-a`**, with three conditions: hash-only, streamed without decoding; logged with date, path,
block, bytes, and digest; and recorded in the Gate 2 manifest itself. No row, count, summary, or statistic may
be derived from the stream, and no digest may be compared across blocks until the relevant gate opens.

### 5.1 Finding X-2 — the cited precedent is not what the packet says it is

**[F]** Packet §6.1 justifies `R-a` by saying "the Stage 2ZC full-file-hash precedent applies". The record
says otherwise: the range-and-hash record §2 states the hashes "are **not** full-file hashes" — each is a
SHA-256 over development-interval objects only — and §1 states that no row in the reserved remainder "was …
hashed as part of a block identity".

**[F]** The only recorded reserved-block contact is a boundary probe: one `open_time` string per file, four in
total, payload decoded zero (`STAGE2ZC_ACCESS_LOG.md`, access table).

**[R]** There is therefore no prior reserved-block *hash* to point to. `R-a` must stand on the text of §8.2
and the ordinary meaning of "read". The boundary probe is not a precedent either: it is a metadata read the
access log disclosed, not a hash pass.
**This does not change the recommendation, and it does not weaken it:** an unsupported premise is removed
rather than inherited. The packet's §6.1 row is corrected here, in a new document, without editing the packet.

**Rejected:** `R-b` — §8.2 becomes unsatisfiable and Gate 2 cannot freeze the split it must freeze. `R-c` —
the strongest governance answer, but it needs a custodian role, a trust boundary, and an appointment that do
not exist today, so a one-line ruling becomes a multi-stage build. `R-d` — no Gate 2. If the owner prefers
`R-c`, the custody proposal in §8.4 survives that choice unchanged.

## 6. Decision 2ZD-2 — recommended: `C-D`, subject to conflict X-1

**[F]** D-11 adopted option A, one primary hypothesis per stage. The packet §6.2 names Candidate B (24
canonical opportunities) and Candidate D (34) as the live options, both frozen at `v2.0.0`.

**[F]** Both candidates already failed Stage 2J — `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`
(`CANDIDATE_B_CENSUS_REPORT.md` §10; `CANDIDATE_D_CENSUS_REPORT.md` §10). Selecting one names a future
hypothesis; it does not revive it.

### 6.1 Conflict X-1 — on the recorded criteria, B is the stronger candidate and D is weaker

**[F]** Read side by side, on each report's canonical population:

| quantity | Candidate B (canonical S10) | Candidate D (canonical S9) |
|---|---:|---:|
| canonical opportunities | 24 | **34** |
| design effect | **1.250** | 3.059 |
| effective units (`N / DE`) | **19.2** | 11.1 |
| `M_all` at 26 bp | **0.0865** | 0.3226 |
| cost-median condition (`M_all ≤ 0.20`) | **met** | **failed** |
| opportunity floor | failed | failed |

**[R]** D wins on raw count by ten signals and loses on every other row: a design effect 2.4× larger, 40%
fewer effective units, and a cost-median failure B does not have. D therefore fails **two** pre-declared
conditions and B fails **one**. On the recorded evidence, `C-D` is the weaker selection.

**[F]** The packet's §6.2 note for `C-D` records "34 historical opportunities; design effect 3.93" and omits
the cost-median failure. That omission is what makes the option look cost-neutral; it is a presentation gap
in the packet, not a contradiction of its text, and it is corrected in the table above rather than by editing
the packet.

**Position taken here:** `C-D` is carried as the delegated recommendation and is **not** silently changed to
`C-B`. A conflict is reported, not repaired. The owner must confirm `C-D` with X-1 in view, or choose `C-B`,
which would make the package internally consistent with the feasibility record. `C-N` remains available and
closes nothing.

**What no selection does:** it authorizes no census, changes no `FEASIBILITY FAIL` verdict, and establishes no
edge for either candidate.

## 7. Decision 2ZD-3 — recommended: `S-1`

**[F]** D-02 is resolved as option C: maximum drawdown 15%, per-trade limit `1.00R`, tail limit `0.50R CVaR95`,
and a `$2,500` fixed-notional position limit (`stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`, D-02, 2026-11-10).

**[F]** At the recorded `1R = $100`, a `4%` stop consumes the whole `$2,500` cap exactly, so any tighter stop
makes the cap — not the risk budget — the binding constraint (packet §6.3).
**[R]** `S-1` defines `R` from the capped notional, so the loss on any trade is `R` — now below `$100`. The
per-trade limit is met with room to spare and the `$2,500` cap is never exceeded. `S-2` also respects the cap
but deletes exactly the trades where it binds, which are the tight-stop trades the design depends on: it
shrinks an opportunity set that is already recorded as insufficient.

**[REC] `2ZD-3 = S-1`.** Consequence accepted: `δ = 0.10R` becomes a smaller absolute amount, so the MME is
cheaper to meet in currency, no easier to meet in `R`, and a larger `$250` trade count is required.

**Rejected:** `S-2` — removes opportunities from a programme that already fails the floor. `S-3` — leaves Gate
2 input #6 `PARTIAL` and Gate 2 unfreezable.

**Not authorized by this choice:** no sizing is applied to real capital, no position is computed, and the
Gate 0 `$250`/`$10` arithmetic is not revised.

## 8. Decision 2ZD-4 — proposed methodology values

The packet §6.4 asks for five values and forbids fitting any of them to `DE`. The method here is to take each
value from a construction already frozen in the candidate specification or the adopted statistics policy,
state why it suits the mechanism, and record what the alternative would cost.

A value is proposed only where the frozen text supports one. Where it does not, the field stays open and the
missing governance decision is named — §8.7.

### 8.1 Episode definition — proposed: the 4 h `budget_ok` regime run

**Proposed value:** one episode is the maximal contiguous run of 4 h buckets in which the volatility budget is
satisfied, containing the signal instant, closed at the first 4 h bucket where it fails.

**[F]** That run is already the frozen cluster unit: candidate D assigns each signal "to the maximal
`budget_ok == True` 4 h run containing the session signal instant", with 212 such runs in the development
interval (`CANDIDATE_D_CENSUS_REPORT.md` §6).
**[R]** Three reasons: it is causal — the run is knowable at the signal instant and looks no further ahead;
it is the mechanism's own unit, since the budget is what makes an intraday continuation eligible at all; and
it is the unit the recorded design-effect diagnostics were computed on, so the registered dependence model and
the pre-registered `DE` describe one object instead of two.

**Rejected:** the UTC session — the recorded session-id view gives a grouped design effect of 15.13 over only
three groups, so it is both unstable and coarse. Calendar month — not linked to the mechanism, and 12 groups.

### 8.2 Block length — proposed: 14 calendar days

**Proposed value:** the moving-block bootstrap resamples contiguous 14-day blocks, 10,000 resamples, seed
`20240101`.

**[F]** This is the predecessor convention, not a new choice: Stage 6 ran a 14-day block bootstrap
(`stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md` line 69) and the strategy recommendation fixed 14 days, 10,000
resamples, seed `20240101` (`STRATEGY_2_RECOMMENDATION.md` line 216).
**[R]** Adequacy: a block must exceed the dependence range. The holding horizon here is intraday and the
canonical non-overlap window is 24 h, so 14 days spans fourteen times the longest plausible range; the
1,277-day development interval yields 91 blocks, enough for a stable bootstrap. Independence from `DE`: the
number was fixed long before this decision and is not varied here, so it cannot have been tuned.

**Rejected:** 1 day — too short for multi-day clustering and leaves 1,277 near-adjacent blocks. 30 or 90 days
— fewer than 43 blocks and outside the frozen convention, ending comparability with the recorded work for no
stated gain.

### 8.3 Embargo length — proposed: 90 calendar days

**Proposed value:** a 90-day gap between development and validation, and between validation and OOS, with no
signal, trade, or feature window crossing either gap.

**[F]** 540 consecutive 4 h bars is 90 calendar days, and that is the longest backward-looking window in the
frozen rules: the volatility percentile is computed over 540 4 h bars ending at the current bucket
(`CANDIDATE_D_SPEC.md` §6).
**[R]** An embargo must be at least as long as anything that reaches backwards. A 90-day gap ensures the first
validation decision is computed from validation bars alone, so no feature window, episode, or holding period
straddles the boundary, and the "no shared information" claim becomes literally true rather than approximately
true. It is derived from a frozen lookback, not from an outcome or a design effect.

**Rejected:** 24 h — the canonical non-overlap window, enough for trades but not for features, since the first
validation signal's percentile would still be built from pre-boundary bars. 7 days — no frozen justification
exists; it is neither the holding horizon nor the lookback.

**Cost accepted:** the reserved remainder is 792 days (`[2024-07-01, 2026-09-01)`); two 90-day embargoes
consume 180 of them and leave 612 days of lookable data for validation plus OOS.

### 8.4 Validation-split custody — proposed: a written custodian procedure; the holder left open

**Proposed procedure:** a named custodian — possibly the owner — alone holds read access to the reserved
remainder; the analyst holds none; the custodian delivers hash values under `R-a` and never rows; each delivery
is logged with date, block, bytes, digest, and purpose; no delivery may precede §8.5's opening conditions.
**Why a procedure and not a name:** a name is not derivable from any frozen document. It is an owner
appointment — a person, a role, and a written delegation — and the agent will not supply one. The procedure is
what makes the appointment meaningful; it can be adopted now and filled with a name later. `R-c`, if chosen
instead of `R-a`, slots into the same procedure with the custodian running the hash pass.

### 8.5 Opening condition — proposed: after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only

**Proposed value:** the split may be opened only when (i) the Gate 2 registration, analysis plan, and hash
manifest are frozen and committed, and (ii) the Gate 4 implementation audit is closed with no open `CRITICAL`
or `MAJOR` finding — and then once only, at Gate 5, under the logged one-look rule.

**[F]** The packet §6.4 already constrains this field to "after the Gate 2 freeze and at Gate 5 only". The
proposal adds the Gate 4 condition, which is when §5.3's "no outcome data has been observed" and §8.8's
audit-rejection condition both become checkable.

### 8.6 The six tests the proposal was put through

| test | result |
|---|---|
| leakage between episodes | none: an episode closes at the first failed 4 h budget, so two episodes cannot share a bucket |
| dependence between observations | handled by the episode cluster plus the 14-day block bootstrap, which is D-09 option C |
| temporal ordering | all five values are causal and forward-only; no rule reads a future bar (protocol §8.3) |
| embargo adequacy | 90 days ≥ the 540-bar lookback and ≫ the 24 h holding window, so nothing straddles a boundary |
| custody and access separation | the analyst holds no read access, and hash-only delivery is logged by the custodian |
| outcome influence | no value is derived from an outcome, a `DE`, or a validation or OOS result; §8.3's lookback is a design constant |

The last row is the one that needed the most care, and it is a claim about provenance rather than about
mathematics: the block length and the episode rule predate the 2J design effect and were not varied in
producing this report, and the embargo comes from a specification constant. None of the three can be traced to
an outcome. The two quantities that *are* outcome-adjacent — `σ` and `DE` — are deliberately not given values
here (§9).

### 8.7 What remains unresolved in 2ZD-4

- **Custodian identity** — needs an owner appointment: a person, a role, and a written delegation. The
  procedure is proposed; the name is not the agent's to give.
- **Adoption of the three proposed numbers** — `90`-day embargo, `14`-day block, and the episode rule are
  recommendations, not decisions. Each field may be set differently or left blank.
- **Whether the embargo also bars feature lookback** — this proposal says yes, the stricter reading. Adopting
  the looser one is a governance decision, not a methodological one, and it would weaken the §8.2 claim.

## 9. Decision 2ZD-5 — recommended: `E-2`

**[F]** B-11 forbids choosing `σ`, `DE`, or `p_exec` after seeing an outcome or a design effect. Candidate D's
recorded design effect is `3.933333` — a design effect — so it may be cited as evidence that D is highly
clustered, but it may not be adopted as the planning value (packet §6.5; `stage2p/OPEN_BLOCKER_REGISTER.md`,
B-11).
**[R]** `E-2` is the only route that yields a writable registration without a census: it turns three unknown
quantities into three declared assumptions, each with a sensitivity range, fixed before any outcome. That is
also what protocol §5.3 already demands — the sufficiency calculation must be "reproducible from its stated
assumptions".

**[REC] `2ZD-5 = E-2`**, with the assumption set declared at Gate 2 registration and labelled as an assumption
in every downstream table, sensitivity range included.
**Why no numbers are proposed here.** Any `DE` this report proposed would be chosen by an author who has read
`3.933333`, so it could not be certified independent of it. The defensible move is to fix the rule — declare,
label, bracket — now, and make the declaration a Gate 2 registration act with its own disclosure, rather than
smuggle a number into a recommendation and call it pre-registered.

**Rejected:** `E-1` and `E-3` — both need a census authorization this stage cannot give, and both still leave
`p_exec` to B-04. `E-4` — leaves Gate 2 input #11 `BLOCKED`.

## 10. Q-1 — recommended: confirm the labelled `26 bp` as the Gate 2 assumption

**[F]** `26 bp` round trip (`0.0026`) is the frozen Binance spot proxy for "fees plus adverse execution",
explicitly "not a Nobitex measurement" (`CANDIDATE_B_SPEC.md` §8; `CANDIDATE_D_SPEC.md` §8;
`STAGE2ZC_COST_ASSUMPTION_RECORD.md` §1). Protocol §4.3 accepts measured cost **or** a labelled assumption with
a replacement plan; Stage 2ZC took the second branch.
**[R]** Gate 2 needs a cost basis for input #8 and the failure criteria; it does not need a measured one.
Confirming the proxy keeps the valuation frozen and the claim boundary intact. It must not be described as
observed, measured, or Nobitex-specific, and it must not be relaxed — at `26 bp` candidate D already fails the
cost-median condition (§6.1).

**[REC] Q-1 = confirm the proxy as a labelled assumption**, replacement plan retained, no `cost_R` computed
here. **Not authorized:** any measurement, quote sampling, or venue contact.
