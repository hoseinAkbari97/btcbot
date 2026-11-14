# Stage 2ZH — Methodology Validation

**Scope:** the seven values proposed for decision 2ZD-4, tested one by one against the frozen methodology.
**Status:** validation only. A value marked *supported* is supported as a proposal; none is adopted.

## 1. Four support tiers

| tier | meaning |
|---|---|
| **mandated** | a governing document requires this value, or the only value consistent with it |
| **derived** | computed from a frozen constant, with the arithmetic shown |
| **precedent** | fixed in a prior frozen artifact; defensible, but nothing requires it |
| **unsupported** | no source; must be left unresolved |

A value being *precedent* is not a weakness — the instruction forbids inventing values, and preferring a
recorded convention over a fresh guess is what that instruction asks for. But the tier must be stated, because
"supported" would otherwise blur a requirement and a habit.

## 2. What is under test

| # | field | proposed value |
|---|---|---|
| 1 | episode definition | maximal contiguous 4 h `budget_ok` run |
| 2 | block length | 14 calendar days |
| 3 | resample count | 10,000 |
| 4 | seed | `20240101` |
| 5 | embargo | 90 calendar days at each boundary |
| 6 | custodian | the human owner, under logged custody |
| 7 | opening | after the Gate 2 freeze and Gate 4 audit, at Gate 5 only, once |

## 3. Field 1 — episode definition: **mandated**

**[F]** Candidate D assigns each signal "to the maximal `budget_ok == True` 4 h run containing the session signal
instant", with 212 runs in the development interval (`CANDIDATE_D_CENSUS_REPORT.md` §6). The 4 h volatility
budget is a frozen eligibility rule of the specification (`CANDIDATE_D_SPEC.md` §6).

**[R]** The cluster unit is not a free choice under D-09 option C: the registered dependence model must be the
model whose design effect the pre-registration cites, and the recorded diagnostics were computed on this unit.
Using a different episode at Gate 2 would silently change the quantity `DE` refers to.

**Leakage test.** An episode closes at the first 4 h bucket in which the budget fails, so no bucket belongs to
two episodes and no episode spans a failure. Within the canonical population, accepted signals are ≥24 h apart
(`CANDIDATE_D_CENSUS_REPORT.md` §5), which is six 4 h buckets — so two accepted trades cannot sit in adjacent
episodes without a failed bucket between them.

**Artificial-independence test.** The episode unit does not claim independence. The sufficiency framework says so
explicitly — "non-overlap is a construction rule; it is not an inferential adjustment"
(`STATISTICAL_SUFFICIENCY_FRAMEWORK.md` §3.4, item 5) — and D-09 requires the block bootstrap as a second
treatment precisely because one cluster definition cannot carry the inference alone.

**Condition attached.** The adequacy above rests on accepted trades being short-lived relative to the 24 h
spacing. That is not a frozen fact: candidate D's specification is a *signal* specification and contains no exit
rule — it says of the 24 h window that it "is a frequency-conservatism choice, not an exit rule"
(`CANDIDATE_D_SPEC.md` §9.2). Until the registration fixes an exit and holding policy, the episode definition is
mandated but its *dependence adequacy* is **[OPEN]**.

## 4. Field 2 — block length: **precedent**

**[F]** Stage 6 ran "episode-cluster intervals and a 14-calendar-day block bootstrap of trade" statistics
(`stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md` line 69). No protocol section, register decision, or 2J-plan clause
fixes a block length; the 2J plan ran no bootstrap at all.

**[CALC]** Development interval `[2021-01-01, 2024-07-01)` is 1,277 days; `1,277 / 14 = 91.2`, so 91 whole blocks.
A 14-day block contains 84 4 h buckets and 42 sessions.

**[R]** Adequacy argument: the block must exceed the range over which outcomes co-move. With intraday exits the
range is at most a few days; 14 days covers it with margin, and 91 blocks is ample for a percentile interval.
The number is therefore defensible on the mechanism, not merely inherited — but it is inherited as well, and the
inheritance is what makes it reproducible against the recorded work.

**Weak point stated:** nothing derives 14 from the data or the MME. A reviewer who asks "why not 10 or 20" is
answered by comparability and by the absence of any other frozen value — not by a statistical optimum. That is
acceptable for a pre-registration and must be disclosed as such in the registration.

## 5. Fields 3 and 4 — 10,000 resamples and seed `20240101`: **precedent, thin**

**[F]** These two values appear in one governing-adjacent document: "episode-cluster bootstrap **and** 14-day
block bootstrap, 10,000 resamples, seed `20240101`" (`STRATEGY_2_RECOMMENDATION.md` line 216).

**[F]** They appear in **no** other governing source: the protocol's §8.5 requires a reported dependence
sensitivity but names no resample count; the register's D-09 names none; the 2J pre-registered plan explicitly
computed no bootstrap (`PRE_REGISTERED_ANALYSIS_PLAN.md` §0, §10); the Stage 6 protocol requires that "random
seeds are recorded" (line 96) without fixing one.

**[R]** Status: supported as a recorded convention, **not mandated**. Adopting them is legitimate and improves
reproducibility, but the Gate 2 registration must cite them as chosen for comparability, not as a protocol
requirement. 10,000 resamples is unremarkable for a percentile interval; the seed is arbitrary by construction
and its only function is exact reproducibility.

## 6. Field 5 — embargo: **derived**

**[F]** The longest backward-looking window in the frozen rules is the volatility percentile, computed over 540
consecutive 4 h bars ending at the current bucket (`CANDIDATE_D_SPEC.md` §6).

**[CALC]** `540 × 4 h = 2,160 h = 90 days` exactly. Two boundaries at 90 days consume `180` of the `792` reserved
days (`[2024-07-01, 2026-09-01)`), leaving `612` lookable days for validation plus OOS.

**[R]** Adequacy against the episode structure: episodes are 4 h runs and the spacing between accepted signals is
≥24 h, both far shorter than 90 days, so no episode or trade can straddle a boundary. Adequacy against the
dependence assumption: the embargo is not sized from the dependence structure at all — it is sized from the
feature lookback, which is the stricter of the two here.

**Residual risk, stated:** if the registered exit policy allowed a holding period beyond 24 h, a trade could span
a boundary regardless of the embargo, because the embargo bounds *when a signal may occur*, not *how long a
position lives*. Under any intraday policy the risk is nil; under a multi-day policy the 90 days would need to be
re-derived. This is the same missing input as §3, and it is the single largest open item in 2ZD-4.

**Not claimed:** no dependence range was measured, and no cost was measured. The embargo's justification is a
declared completeness argument — the first validation decision sees validation bars only — not an empirical one.

## 7. Field 6 — custodian: the owner, under logged custody

**[F]** The protocol and the addendum contain no custodian role: the word does not occur in either. The role is
created by the amendment draft (`A-2`, `A-4`).

**[R]** Naming the human owner is the only appointment available today — there is no second official with
credentials, and inventing an institutional custodian would be an agent decision about governance structure. It
is also the strongest available trust boundary: the party who may see the data is the party who owns the
decision, and the analyst is excluded by construction.
