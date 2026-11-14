# Stage 2ZH — Decision Reconciliation

**Stage:** 2ZH (decision reconciliation and governance amendment preparation)
**Date:** 2026-11-14 (UTC)
**Status:** **reconciliation and drafts only. No recommendation here is ratified, and no amendment is adopted.**
**Relation to Stage 2ZG:** this stage evaluates a *changed* recommendation set against the same authoritative
sources, and records where it agrees with 2ZG, where it departs, and what the departure costs.

## 1. Starting state, verified

| item | expected | observed |
|---|---|---|
| branch | `main` | `main` |
| HEAD | `61b6438d44bfe6145391ad542f47c79495e8f4bb` | matched, equal to `origin/main` |
| worktree | clean | clean |
| 2ZG report | present | `09d35c30…bf99c`, 21,357 bytes |
| 2ZG decision record | present | `e3d3dd08…ee3258`, 6,366 bytes |
| 2ZG boundary | present | `b3c8fc95…0c06a8`, 5,159 bytes |
| 2ZG manifest | present | `ae55e362…926736`, self-hash `3d7830aa…cf738a`, verified |

The four Stage 2ZG hashes were recomputed from current bytes and match the values reported at the end of that
stage. The Stage 2ZD manifest's canonical self-hash and its six deliverable hashes were re-verified in Stage
2ZG and are not re-derived here; this stage reads no dataset file.

## 2. Labels used in this document

- **[F]** verified source fact, quoted or counted, with its section.
- **[CALC]** arithmetic shown in full, reproducible from the stated inputs.
- **[REC]** the delegated recommendation under evaluation.
- **[OPEN]** unresolved; needs evidence or a decision that does not exist yet.
- **[OWNER]** a formal owner act is required; the agent may draft, never perform.

## 3. What changed from Stage 2ZG, and what it costs

| decision | 2ZG | 2ZH proposed | change |
|---|---|---|---|
| 2ZD-0 | `C` | `C` | none |
| 2ZD-1 | `R-a` | `R-b` | a ruling becomes an amendment |
| 2ZD-2 | `C-D` | `C-N` | a candidate becomes no candidate |
| 2ZD-3 | `S-1` | `S-1` | none |
| 2ZD-4 | four values, custodian open | same values, owner as custodian | custody closes |
| 2ZD-5 | `E-2` | `E-2` | none |
| Q-1 | confirm `26 bp` | retain as labelled proxy | none |

Two of the three changes make the programme *stricter*, and both add work rather than remove it:

- `R-b` declines to settle a governance question by interpretation, and therefore requires a versioned
  amendment to the protocol before Gate 2 can freeze a split.
- `C-N` declines to register any hypothesis, and therefore leaves Gate 2 unable to pass even after everything
  else is settled.

Neither is a shortcut. Both are defensible; §5 and §6 say exactly what each costs.

## 4. Decision 2ZD-0 — `C`, unchanged

**[F]** Path C is "resolve the protocol interpretation and owner decisions first" and authorizes "the §8.2/D-12
ruling plus the four non-data Gate 2 decisions, and a Gate 2 specification reflecting them" (packet §5).

**[REC]** `2ZD-0 = C`, as in 2ZG. **Consistency check:** under `R-b` the "ruling" is delivered as a proposed
amendment rather than an interpretation, and under `C-N` the Gate 2 specification carries an empty hypothesis
slot. Path C's text accommodates both — it authorizes a resolution, not a particular mechanism — but the two
together mean Path C no longer produces a *registrable* Gate 2 package. It produces an amendment plus three
decisions plus a specification with a hole.

That is not a defect in `C`. It is the honest state after choosing `R-b` and `C-N`: two blockers (B-3, B-1)
move from "owner decision pending" to "owner decision made, consequence pending", and the consequence for B-1
is that Gate 2 stays blocked until a later candidate decision.

## 5. Decision 2ZD-1 — `R-b`, with one counter-argument recorded

**[F]** Protocol §8.2: "the exact dates and hashes are frozen at Gate 2". D-12 (register) and addendum §10.4:
no validation or OOS "row" may be read before its gate. The word "read" is nowhere defined.
**[F]** Protocol §10.4 says: "A pre-registered interpretation may resolve an ambiguity before counting, but it
must be recorded in the plan and disclosed in the report." This is the counter-argument, and it is real: the
protocol itself provides an interpretation route, so `R-b`'s premise — that interpretation alone is
insufficient — is not stated anywhere in the text.

**[R]** The distinction that saves `R-b` from being merely optional: §10.4 sits under "labels and populations"
and concerns how a *label or population* is read, not whether a *data-access rule* may be relaxed by
interpretation. An interpretation of §8.2 would bind only the analyst who recorded it and would leave the next
reader free to interpret the other way; an amendment binds everyone, including a future custodian.

**Verdict on consistency:** `R-b` is **consistent** with the protocol — nothing in it forbids amendment, and
§10.2 provides the versioning mechanism — and it is the stronger of the two routes. It is **not required** by
the text, and a future reader should not be told that interpretation was unavailable. Both were available; the
owner has preferred the one that changes the text.

**What `R-b` costs:** §8.2's hash requirement becomes unachievable by the analyst, so Gate 2 cannot freeze its
split until an amendment is adopted (§6 of the amendment draft). No reserved byte may be hashed in the
meantime — including by this stage.

## 6. Decision 2ZD-2 — `C-N`: valid under the packet

**[F]** Packet §6.2 offers three options: `C-B`, `C-D`, and `C-N` — "no selection now; keep both as
unselected", with the consequence "Gate 2 cannot name a primary hypothesis". `C-N` is therefore an option in
the instrument itself, not a write-in.

**[F]** D-11 adopted option A: "One primary hypothesis — test one pre-registered hypothesis; all else
exploratory". The rule caps the number of primaries at one.

**Determination: `C-N` is valid.** It does not violate D-11 — a rule that forbids *more than one* primary is
satisfied by zero — and it is not a refusal to decide, because it decides that no candidate is registered now.
What it does not do is leave Gate 2 unchanged: §5.2 #1 requires a hypothesis and §5.3 requires the registration
to be "complete and internally consistent", so with `C-N` Gate 2 cannot pass, and B-1 stays open.

**What `C-N` means in practice:**

- neither candidate is registered, promoted, or revived; both stay frozen at `v2.0.0` with their
  `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES` verdicts untouched;
- the Gate 2 specification retains an explicitly empty hypothesis slot, and may not be filled by the agent;
- no candidate is replaced by the other to satisfy the one-primary rule — which is precisely the cosmetic fix
  `C-N` refuses.

**[OPEN]** Sheet one of the Gate 2 requirement matrix (input #1) is now unsatisfiable by construction, so the
matrix must be rewritten to show it as *deferred by decision* rather than *awaiting a decision*. That rewrite
belongs to a later documentation stage, not to this one.

## 7. Decision 2ZD-3 — `S-1`: consistent with D-02, and it makes the target harder

**[F]** D-02 is resolved as option C: maximum drawdown 15%, per-trade limit `1.00R`, tail limit `0.50R CVaR95`,
`$2,500` fixed-notional position limit (`stage2o`, D-02, 2026-11-10).

**[CALC]** Under `S-1`, `R` is set by the capped notional, `R = min($100, $2,500 × stop%)`:
| stop | notional at `1R = $100` | cap binds? | effective `R` | `0.10R` | trades for `$250` |
|---:|---:|---|---:|---:|---:|
| 4.00% | $2,500 | exactly at the cap | $100 | $10.00 | 25 |
| 2.00% | $5,000 | yes | $50 | $5.00 | 50 |
| 1.30% | $7,692 | yes | $32.50 | $3.25 | 77 |

**[F]** The recorded arithmetic is `$250 / ($10 per trade) = 25` executed trades/year "under full `1R` risk"
(`stage2t` §3), and the historical opportunity frequency is "~20/10/7/3 opportunities per year" (same section).

**[R]** `S-1` satisfies D-02 on both counts — per-trade loss is `R`, which is at most `$100`, and the cap is
never exceeded — so the risk rule is sound. The economic consequence runs the other way: a tighter stop halves
`R`, halves `0.10R`, and doubles the trade count needed for the same `$250`, from 25 to 50 at a 2% stop.

**[R]** That does not argue against `S-1`; it argues against using `S-1` as a frequency argument. The
minimum-evidence requirements are unchanged, the `150` floor is unchanged, and 50 trades a year against a
recorded 20-at-best frequency is a stronger reason to doubt the objective than to lower the bar.

**[OWNER]** The `$250` target itself is decision `T-5` and remains open; this stage does not touch it.

## 8. Decision 2ZD-4 — reconciled, not re-derived

The five values and their evidential status are examined field by field in
`STAGE2ZH_METHODOLOGY_VALIDATION.md`. In reconciliation terms only one thing changed from 2ZG: the custodian is
now named as the human owner. That closes the field 2ZG left open, and it is consistent with `R-b`, because a
custodian who is not the analyst is exactly the party the amendment can authorise to compute a digest.

The four numeric values are unchanged, and §3 of the methodology document records what each is and is not
supported by — including the two that rest on a prior recommendation rather than on a protocol requirement.

## 9. Decisions 2ZD-5 and Q-1 — unchanged
