# Stage 2P — Gate 0 Readiness Assessment

**Stage:** 2P
**Status:** Documentary assessment only
**Supersedes:** nothing
**Depends on:** `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §3, `stage2m/OWNER_DECISION_REGISTER.md`, `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`
**Authorizes:** nothing

---

## 0. Purpose and scope

**Purpose:** determine, against the frozen Gate 0 criteria, whether the project is ready to
conclude Gate 0, and to state precisely what is missing.

**Scope of this stage:** reading frozen documents, restating recorded owner decisions, and
classifying Gate 0 requirements. It is not a gate session, does not record new owner decisions,
and does not pass, fail, or reopen any gate.

**Label discipline** (as in every Stage 2 document):

- **Verified fact** — checked against a frozen artifact in this repository.
- **Interpretation** — the agent's reading of those artifacts.
- **Proposal** — a recommendation, not a decision, not binding.
- **Owner decision** — recorded in `stage2n` or `stage2o`; not the agent's to change.

**Not done in this stage (by instruction):** no market-data processing, no validation or
out-of-sample access, no census, no backtest, no Monte Carlo or bootstrap, no new performance
metric, no venue cost or liquidity study, no code or strategy-specification change, no new
candidate, no independent audit, no resolution of D-04, D-05, D-06, D-13, or D-15, no Gate 0 pass,
no Gate 1–5 authorization, no trading of any kind.

---

## 1. Repository state at the start of this stage

| item | value |
|---|---|
| branch | `main` |
| HEAD | `b0630e5` `docs(stage2o): reconcile D-02e note with later limits` |
| working tree | clean |
| tracking | `## main...origin/main`, no ahead/behind |
| remote | `origin git@github.com:hoseinAkbari97/btcbot.git` |

**Verified fact:** the working tree was clean and the branch was level with its upstream when this
stage began. No discrepancy was found between the repository state and the state reported at
handoff, so the Stage 2P pre-work stop condition was not triggered.

**Verified fact:** the frozen manifests were re-hashed in this stage without modification:

| manifest | `self_hash` recomputed | status |
|---|---|---|
| `stage2m/FREEZE_MANIFEST.json` | matches `6469d6a4…f54b0a9` | 6 deliverables and 21 source artifacts intact |
| `stage2k/FREEZE_MANIFEST.json` | matches | 4 deliverables and 23 source artifacts intact |
| `stage2l/FREEZE_MANIFEST.json` | matches | 4 deliverables intact |

**Interpretation:** the decision record, the resolution record, the response record, and the
governing protocol are all consistent with their frozen hashes, so the inputs this assessment
relies on are the inputs the owner approved.

---

## 2. Documents inspected

Read in full for this stage:

1. `stage2m/OWNER_DECISION_REGISTER.md`
2. `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` (§0–§12)
3. `stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` (§7–§9 in detail)
4. `stage2m/STATISTICAL_SUFFICIENCY_FRAMEWORK.md` (§5)
5. `stage2m/STAGE2M_FINAL_PROPOSAL.md`
6. `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`
7. `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`
8. `stage2o/STAGE2O_D01_D02_DECISION_PACKET.md`
9. `stage2m/FREEZE_MANIFEST.json`, `stage2e_v2/FREEZE_MANIFEST.json`

No file in `stage2m`, `stage2n`, or `stage2o` was modified by this stage.

---

## 3. The recorded economic objective, restated without change

### 3.1 D-01 — minimum meaningful effect

**Owner decision (Stage 2O, option A):**

| element | recorded value |
|---|---|
| definition chosen | **Definition A** (net-of-cost, per-executed-trade edge in R) |
| MME value | **`0.10R` net per executed trade** |
| annual contribution target | **`$250` per year** |
| research equity | **`$10,000`** |

**Verified fact:** with fixed-fractional `1%` risk, `1R = $100` on the research leg and the MME is
`$10` per executed trade. The annual target and the per-trade target are recorded as separate
values linked only by frequency; neither is derived from the other.

### 3.2 D-02 — risk limits

**Owner decision (Stage 2O, extension of Stage 2N option C):**

| constraint | recorded value | unit |
|---|---|---|
| drawdown cap | **`15%`** of prior equity peak | % of equity |
| per-trade realized net loss cap | **`1.00R`** | R, and `1%` of equity at entry |
| tail limit (`CVaR95`) | **`0.50R`** | R |
| max entry notional | **`$2,500`** | USD |
| capital scope | **research leg only** (`$10,000`) | — |

**Owner decision (Stage 2N option C):** the adopted risk policy consists of a maximum drawdown, a
per-trade loss limit, a tail measure, and a liquidity/position-size constraint. Time under water,
ruin probability, concentration, and operational risk were **not** adopted as required limits.

### 3.3 The distinction this stage must preserve

**Verified fact:** D-01 and D-02 are *preferences selected by the owner*. They are not measurements,
not estimates, and not evidence about any candidate.

**Verified fact:** no value in §3.1 or §3.2 has been tested against data. Whether `0.10R` net is
attainable, whether `15%` drawdown is consistent with `1.00R` per-trade risk at the achievable
frequency, whether `CVaR95 = 0.50R` is binding, and whether `$2,500` is executable on the intended
venue are all **unverified**.

**Interpretation:** these numbers define what a future experiment must be able to detect and what
losses it may not exceed. Treating any of them as empirically established would be a category error,
and every downstream document must keep the label "owner-selected limit" attached to them.

---

## 4. The Gate 0 criteria, as frozen

**Verified fact** (`RESEARCH_GOVERNANCE_PROTOCOL.md` §3.2–§3.4), Gate 0 requires these inputs:

1. an owner-approved minimum meaningful effect, in the primary metric;
2. owner-approved risk limits;
3. owner-approved capital and position-sizing context;
4. owner-approved primary and secondary estimands;
5. owner-approved execution venue and cost-evidence standard;
6. owner-approved error-control objective and dependence-treatment standard.

Gate 0 passes only when all blocking decisions are resolved, no unresolved decision has been
silently defaulted, the objective is in a testable form, and the risk limits are expressed in units
compatible with the primary metric. Gate 0 requires four artifacts: a signed owner decision record,
an economic objective memo, a risk policy statement, and a capital and execution context statement.

---

## 5. Gate 0 readiness checklist

Status codes: **S** satisfied · **P** partially satisfied · **O** open, owner input required ·
**X** open, external evidence required · **B** blocked by another decision · **N** not applicable.

| # | Requirement | Current status | Missing evidence/input | Responsible party | Dependency |
|---|---|---|---|---|---|
| R-01 | MME definition and value | **S** — Definition A, `0.10R` net (Stage 2O) | none | owner (done) | — |
| R-02 | Maximum drawdown limit | **S** — `15%` of prior equity peak, research leg | confirmation that % units satisfy §3.3 unit compatibility | owner (done) | D-02 |
| R-03 | Per-trade loss limit | **S** — `1.00R`, `1%` of equity at entry | none | owner (done) | D-02 |
| R-04 | Tail limit | **S** — `CVaR95 = 0.50R` | measurement definition of the tail sample | owner (done) | D-02 |
| R-05 | Liquidity / position-size constraint | **P** — `$2,500` max entry notional recorded; executable on the intended venue **unverified** | venue depth, minimum notional, lot step (`B-04`) | owner + external evidence | D-05 |
| R-06 | Operational risk limits | **N** — not adopted (Stage 2N option C) | none; disclosed as a remaining exposure | owner | D-02 |
| R-07 | Capital and sizing context, research leg | **S** — `$10,000`, `1%` fixed-fractional, one position, no leverage | none | owner (done) | D-04 |
| R-08 | Capital and sizing context, **real capital** | **O** — explicitly left open; no real-capital figure exists anywhere in the repository | the owner's real deployable capital, or an explicit statement that none is committed | owner | D-04, D-01 |
| R-09 | Primary and secondary estimands | **S** — D-03 option A primary, option D co-primary; D-07 option A | none | owner (done) | — |
| R-10 | Execution venue and cost-evidence standard | **P** — venue split and standard approved (staged A+B; Binance research, Nobitex execution; p95 conservative rule); **no venue evidence exists** | access confirmation (`B-02`), cost distribution (`B-03`), liquidity evidence (`B-04`) | owner + external source | D-05, D-06 |
| R-11 | Error-control objective | **S** — `α = 5%` two-sided, power `80%`, hierarchical allocation (D-08 A+B) | none | owner (done) | — |
| R-12 | Dependence-treatment standard | **S** — D-09 option C, inconclusive on disagreement | numeric dependence parameters | owner (done), parameters at Gate 2 | D-09 |
| R-13 | Every blocking decision resolved | **P** — D-01, D-02, D-03, D-07 resolved; D-04 only partially (research leg) | D-04 real-capital translation | owner | D-04 |
| R-14 | No unresolved decision silently defaulted | **S** — every unresolved item is named in `stage2o` §9 and in `OPEN_BLOCKER_REGISTER.md` | none | owner (done) | — |
| R-15 | Objective in testable form | **S** for the research leg; **B** for any real-capital claim | real-capital context | owner | D-04 |
| R-16 | Risk limits in units compatible with the primary metric | **S** — per-trade and tail limits in R; drawdown in % of peak; liquidity in USD notional, each in its natural unit as recorded | none | owner (done) | — |
| R-17 | Signed owner decision record | **P** — `stage2n` and `stage2o` records are explicit and frozen, but neither is a signed Gate 0 instrument | a Gate 0 decision record consolidating D-01…D-07 | owner | — |
| R-18 | Economic objective memo | **O** — does not exist as a Gate 0 artifact; the content is spread across `stage2m` §2–§3 and `stage2o` | memo consolidating MME, annual target, estimands | owner or authorized author | R-01, R-09 |
| R-19 | Risk policy statement | **O** — content exists in `stage2o`; not consolidated as a policy statement | consolidated statement with units, measurement rules, scope | owner or authorized author | R-02…R-05 |
| R-20 | Capital and execution context statement | **O** — research leg recorded; execution context unresolved | the statement itself, which must include the venue decision and its evidence gap | owner | R-07, R-08, R-10 |
| R-21 | Frequency-feasibility consistency acknowledged | **O** — the `0.10R`/`$250` pair implies ~25 executed trades per year; no historical family reached that even in opportunities (§7) | owner acknowledgment that Gate 3 may fail on frequency, or a changed annual target | owner | D-01, D-03 |
| R-22 | Independent-audit standard and reviewer | **P** — standard resolved (D-13 B+E); **no reviewer identified**; audit not performed and not authorized | reviewer identity, qualification evidence, independence declaration | owner | D-13 |
| R-23 | Deferred decisions (D-15) | **N** — deferred; status preserved and not revisited | none in this stage | owner | D-15 |

**Count over the 23 rows:** 10 satisfied, 5 partially satisfied, 5 open to the owner, 1 satisfied
for the research leg and blocked for any real-capital claim, 2 not applicable. No row is satisfied
on the strength of the D-01/D-02 resolutions alone. The five open rows are `R-08` and `R-18` to
`R-21`.

---

## 6. Verdict

**Gate 0 has not passed and is not ready to pass.**

**Verified fact:** three of the six Gate 0 inputs (§4, items 1, 4, 6) are fully satisfied. Two
(items 2 and 3) are satisfied for the `$10,000` research leg only. One (item 5) is satisfied as a
*standard* but has no evidence behind it. Two of the four required Gate 0 artifacts (§4) do not
exist, and a third exists only in fragmented form.

**Interpretation:** the gap is not analytical. It is (a) one owner input that was deliberately
postponed (D-04 real capital), (b) three consolidation artifacts that no stage has been authorized
to write, and (c) one consistency acknowledgment that the owner has not yet been asked for
(the `$250`-per-year versus `~25` trades per year tension, §7).

**Explicitly not concluded:** that the objective is achievable; that the risk limits are coherent
with the objective; that any venue can execute the strategy; that any candidate is viable; that
Gate 1 may begin.

---

## 7. Critical consistency review

This section restates arithmetic that already appears in frozen documents. It introduces no data,
no estimate, and no new metric. Every number below is either a recorded owner value or an
arithmetic consequence of recorded values.

### 7.1 The frequency implication of `0.10R` and `$250`

**Verified fact** (`stage2o` §3.1, `STAGE2O_D01_D02_DECISION_PACKET.md` §4.2): under fixed-fractional
`1%` risk with `1R = $100`, the required executed trades per year is
`annual_target / (δ_R × $100)`. At `δ_R = 0.10R` and `$250`, that is

```
$250 / ($10 per trade) = 25 executed trades per year
```

**Interpretation:** the value is modest in money and demanding in count. It assumes every executed
trade earns exactly the MME, ignores compounding and idle capital, and ignores
`p_exec < 1` — every one of which pushes the true requirement **up**.

### 7.2 Historical opportunity frequencies, verified against the source records

**Verified fact** (`STAGE2O_D01_D02_DECISION_PACKET.md` §5.2, over the frozen `1,277`-day
development interval):

| candidate | non-overlapping opportunities | approximate per year |
|---|---:|---:|
| A | 71 | ≈ 20 |
| B | 24 | ≈ 7 |
| C | 12 | ≈ 3 |
| D | 34 | ≈ 10 |

**Verified fact:** these are *census opportunities*, not executed trades, and they are not outcome
evidence. The historical feasibility gates had already failed on count for most families
(`stage2k`/`stage2l` record A at 71 against a `150` floor, C at 12 against `200`, and B and D as
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`).

### 7.3 Why this is a Gate 3 problem and not an edge problem

**Arithmetic, from the two verified facts above:** `25` executed trades per year requires at least
`25` opportunities per year, because `p_exec ≤ 1`. Every historical family is below that line on
*opportunities*: A at ≈ 20, D at ≈ 10, B at ≈ 7, C at ≈ 3. At any `p_exec < 1` the required
opportunity rate is `25 / p_exec`, which moves A from a 1.25× shortfall to roughly 1.6× at
`p_exec = 0.8`, and pushes B, C, and D further out.

**Interpretation:** the likely failure mode at the resolved objective is not "the edge is too
small" but "not enough trades to earn `$250` in a year". That is a feasibility failure at Gate 3,
which the governance protocol treats as a legitimate stop rather than a reason to lower the
requirement.

**Also verified:** the sample-sufficiency requirement at the resolved MME points the same way.
`N_ind ≈ (z_{1-α/2} + z_{1-β})² σ² / δ²` at `δ = 0.10R`, `σ = 1R`, `α = 5%` two-sided, power `80%`
is ≈ `785` independent observations — the figure already carried in `stage2o` §2.2. The entire
`1,277`-day interval produced `12`–`71` opportunities per family. **Arithmetic consequence:** the
resolved MME is roughly an order of magnitude beyond what that interval can supply even before
dependence inflation (`DE`) and `p_exec`, and well beyond its `3.5`-year calendar span.

**Label:** the `785` figure is a conventional power calculation on an assumed `σ = 1R`, not a
measurement, and the historical counts are census opportunities, not outcomes. The comparison is an
arithmetic consistency check. It is not evidence that the strategy fails, and it is not a
recomputation of any historical result.

**What this section may not do, and does not do:** change D-01, change the annual target, declare
`$250` unachievable, select a different candidate, or re-run any census on new data.

### 7.4 Consequence of the `$2,500` notional cap when the stop is tight

**Verified fact** (`stage2o`, D-02d note): with `1%` risk on `$10,000`, the position notional before
the cap is `$100 / stop_fraction`, so the `$2,500` cap binds whenever `stop_fraction < 4%`.

**Arithmetic, from recorded limits only** (notional capped at `$2,500`; realized risk
`= $2,500 × stop_fraction`):

| stop distance | uncapped notional | executed notional | realized risk `1R` | value of `0.10R` | executed trades needed for `$250` |
|---:|---:|---:|---:|---:|---:|
| `1%` | `$10,000` | `$2,500` | `$25` | `$2.50` | `100` |
| `2%` | `$5,000` | `$2,500` | `$50` | `$5.00` | `50` |
| `3%` | `$3,333` | `$2,500` | `$75` | `$7.50` | `34` |
| `4%` | `$2,500` | `$2,500` | `$100` | `$10.00` | `25` |
| `5%` | `$2,000` | `$2,000` | `$100` | `$10.00` | `25` |

**Interpretation:** below a `4%` stop the cap silently *reduces risk per trade* and therefore
*shrinks each trade's contribution in dollars*, roughly as `1 / stop_fraction`. The `1.00R` per-trade
cap still holds, because `R` is redefined smaller; what breaks is the link between "`0.10R`" and
"`$10`". The annual target then needs two to four times as many trades as §7.1 assumes. A tight-stop
design is therefore doubly penalised: fewer dollars per winner and a higher `cost_R`, since the
frozen cost formula divides the cost fraction by the stop distance.

**Explicitly not concluded:** which stop distance any candidate would use; whether the `$2,500` cap
is appropriate for a `$10,000` leg with Nobitex lot sizes; whether `100` trades per year is
attainable. Those are Gate 1–3 questions with evidence attached.

---

## 8. What must be resolved before Gate 0 can pass, and what may wait

### 8.1 Before Gate 0 can pass (owner inputs)

1. **D-04 real-capital translation** — the capital figure, or an explicit statement that no real
   capital is committed and the objective is research-leg only. This is the only *decision* that
   still gates Gate 0.
2. **Gate 0 artifacts R-17 to R-20** — one consolidated decision record plus the economic
   objective memo, the risk policy statement, and the capital and execution context statement.
   These are writing tasks, not research tasks, but they must be produced and frozen.
3. **R-21 frequency acknowledgment** — the owner has to see §7 and either accept the Gate 3 risk
   or change the annual target. Silence here would be exactly the "silent default" §3.3 forbids.

### 8.2 May be resolved in Gate 1 (no Gate 0 claim depends on it)

- **D-05** Nobitex access and account capability (`B-02`).
- **D-06** venue-specific cost distribution and the `p95` rule's applicability (`B-03`).
- **Venue liquidity and execution evidence** (`B-04`): depth, volume, minimum order size and lot
  increment, fees, spread, slippage, market impact, stop-execution and gap behaviour.
- The arithmetically checkable half of **R-05**: whether `$2,500` clears the venue's minimum
  notional and lot step.

### 8.3 Must be resolved in Gate 2 or later

- D-09 numeric parameters (episode definition, block length, embargo, regime definitions).
- D-10 inputs (`σ`, `DE`, `p_exec`), which convert `785` into an actual `required_opportunities`.
- D-11 exploratory-versus-confirmatory labelling, D-12 one-look discipline logistics.
- **D-13** reviewer identification and the audit itself (Gate 4). The *standard* is resolved; the
  *person* does not exist. `stage2l` already recorded `SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`.

### 8.4 Deliberately untouched

- **D-15** remains deferred. This stage does not revisit it, does not activate the candidate it
  concerns, and does not treat the deferral as a Gate 0 gap.

---

## 9. What this assessment does not establish

- It does **not** pass Gate 0, and would not pass it even if D-04 were answered tomorrow, because
  the artifacts in R-17 to R-20 do not exist yet.
- It does **not** reopen D-01 or D-02, and finds no reason in the frozen record to do so.
- It does **not** claim `$250` per year is achievable or unachievable.
- It does **not** rank the historical candidates; the frequency figures in §7.2 are quoted from the
  frozen packet, not re-derived.
- It does **not** collect venue evidence, audit anything, or authorize any gate.

---

## 10. Summary

The economic objective is now fully specified for the `$10,000` research leg and the governance
standard around it is coherent. Gate 0 nonetheless remains open for three concrete reasons: the
real-capital translation (D-04) is unanswered, the four Gate 0 artifacts have not been consolidated,
and the frequency implication of `0.10R` at `$250` — about `25` executed trades per year against a
historical best of about `20` opportunities per year — has not been acknowledged by the owner. The
venue, cost, liquidity, and audit prerequisites are real but belong to Gate 1 and Gate 4, and should
not be allowed to obscure the smaller, purely documentary gap holding Gate 0 open today.
