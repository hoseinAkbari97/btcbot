# Stage 2P — Open Blocker Register

**Stage:** 2P
**Status:** Documentary register only
**Depends on:** `GATE0_READINESS_ASSESSMENT.md`, `stage2m/OWNER_DECISION_REGISTER.md`, `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`
**Authorizes:** nothing

---

## 0. How to read this register

Every entry is an item that is **not** satisfied today and that someone must act on. Nothing here is
resolved, scheduled, or estimated. No entry has a target date, because no stage after Stage 2P has
been authorized.

**Fields:**

- **Type** — `owner decision`, `owner input`, `external evidence`, `documentary artifact`, or
  `consistency acknowledgment`.
- **Status** — `open`, `open, deliberately deferred`, or `blocked by another entry`.
- **Blocks** — the gate or deliverable that cannot proceed while the entry is open.
- **Responsible party** — who must supply it. Only two answers are possible: **owner**, or an
  **external source the owner must authorize**.
- **Prohibited shortcut** — the specific wrong move that would appear to close the entry without
  closing it. These are recorded because each one is tempting.

**Global rules that apply to every entry:**

1. The research agent may not close any entry by assumption, interpolation, or analogy to another
   venue, another capital base, or another strategy.
2. No entry may be closed using validation or out-of-sample data.
3. No entry may be closed by changing a frozen artifact. A changed input requires a new stage and a
   new freeze, not an edit to `stage2m`, `stage2n`, or `stage2o`.

---

## 1. Register summary

| ID | Blocker | Type | Status | Blocks |
|---|---|---|---|---|
| `B-01` | D-04 real-capital translation | owner input | open | Gate 0 pass; any real-capital claim |
| `B-02` | D-05 Nobitex access and account capability | owner input + external | open | Gate 1; any Nobitex-executed stage |
| `B-03` | D-06 venue-specific cost distribution | external evidence | open | Gate 1; any primary verdict |
| `B-04` | Venue liquidity and execution evidence | external evidence | open | Gate 1, Gate 3 |
| `B-05` | D-13 independent reviewer | owner input | open | Gate 4 |
| `B-06` | D-15 deferred decision | owner decision | open, deliberately deferred | any new candidate |
| `B-07` | Gate 0 artifact consolidation | documentary artifact | open | Gate 0 pass |
| `B-08` | Frequency-feasibility acknowledgment | consistency acknowledgment | open | Gate 0 pass; Gate 3 |
| `B-09` | `$2,500` cap versus tight stops | consistency acknowledgment | open | Gate 2 sizing; Gate 3 |
| `B-10` | D-09 / D-12 numeric parameters | owner decision | open | Gate 2 |
| `B-11` | D-10 sample inputs (`σ`, `DE`, `p_exec`) | evidence + owner | open | Gate 2, Gate 3 |
| `B-12` | Operational risk excluded from limits | disclosure | recorded, not actionable | nothing today |

**Verified fact:** no entry above was created by Stage 2P. Each one is already recorded in
`stage2o` §9, `stage2n`, or the `stage2m` decision register. This register only collects them,
orders them by gate, and states what would be required to close them.

---

## 2. Entry detail

### B-01 — D-04 real-capital translation

**Owner record:** D-04 option C. The `$10,000` research leg is defined; the translation to real
deployable capital is **explicitly open**.

**What is missing:** either a real-capital figure, or an explicit statement that no real capital is
committed and the objective is research-leg only for the foreseeable future. Both are acceptable
answers; silence is not.

**Why it cannot be inferred:** the owner's capital is not in the repository, not derivable from the
research leg, and not a research question. `1R` in dollars, the meaning of the `15%` drawdown, and
the `$2,500` notional cap all change with the capital base.

**Status:** open.
**Blocks:** Gate 0 pass; every real-capital claim in any future document.
**Responsible party:** owner.
**Prohibited shortcut:** assuming real capital equals `$10,000` because that is the only figure on
record; scaling the research leg by a "reasonable multiplier"; deferring it silently while writing
downstream documents as though it were answered.

---

### B-02 — D-05 Nobitex access and account capability

**Owner record:** staged option A+B. Binance BTCUSDT is the research data venue; Nobitex is the
intended execution venue. Access is **unknown**.

**What is missing:** confirmation of whether the owner can (a) open or already holds a Nobitex
account, (b) pass KYC at the required level, (c) obtain API credentials with the order permissions
the strategy needs, (d) deposit and withdraw in the required currency, and (e) place the order types
the specification assumes.

**Why it cannot be inferred:** no Nobitex account record, fee schedule, API document, or fill record
exists in the repository. The absence is documented in `stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md`
§8.2 and `stage2k` §7 U1.

**Status:** open.
**Blocks:** Gate 1; any Nobitex-executed experiment; `B-03` and `B-04` both depend on it.
**Responsible party:** owner, with an external source the owner must authorize.
**Prohibited shortcut:** substituting Binance as the execution venue without an owner decision;
assuming Nobitex access because the historical specifications named it; treating an API key's
existence as evidence of venue capability.

---

### B-03 — D-06 venue-specific cost distribution

**Owner record:** option A — a venue-specific cost study is required, the `p95` rule is the
mandatory sensitivity, and an optimistic-cost pass is prohibited.

**What is missing:** a measured all-in cost distribution for the execution venue at the strategy's
decision times and order sizes. The frozen `26 bp` figure is documented as a Binance spot *proxy*
for fees plus adverse execution, not a Nobitex measurement, and the framework forbids using it as
one.

**Why it matters more than it looks:** the proxy was decision-critical historically — Candidate D's
cost gate rejected `250` of `295` pre-gate sessions at `26 bp`. A cost distribution that moves in
either direction changes which sessions are even admissible, so it cannot be treated as a
calibration detail added after the verdict.

**Status:** open.
**Blocks:** Gate 1; any primary verdict; the `p95` sensitivity cannot be computed without a
distribution to take a percentile of.
**Responsible party:** external source the owner must authorize.
**Prohibited shortcut:** reusing `26 bp` as if measured; taking a current published fee schedule as
a historical cost distribution; using a mean where the resolved rule requires the `p95`; reporting a
pass that depends on an optimistic cost scenario.

---

### B-04 — Venue liquidity and execution evidence

**What is missing** — the eight-item evidence set, each item independent and each required:

| # | item | what the evidence must show | why an assumption fails |
|---|---|---|---|
| 1 | order-book depth | visible depth at the `$2,500`-scale order size at decision and exit times | top-of-book size is not available size |
| 2 | traded volume | volume distribution over the intended holding period | a thin book may still print volume, and vice versa |
| 3 | minimum order size and lot increment | the venue's minimum notional and step, checked against `$2,500` and against the capped notional at tight stops | an unexecutable size is not a small size |
| 4 | fee schedule | dated maker/taker schedule, account tier, effective dates, payment-token or tier effects | fee schedules change and tiers are account-specific |
| 5 | bid-ask spread | distribution at the strategy's actual decision times, by session and volatility regime | a daily average hides the moments the strategy trades |
| 6 | slippage | decision-to-fill difference at the intended size and order type | the signal price is not the fill price |
| 7 | market impact | price response to the order, as a size-depth curve | a `$2,500` order is not free of its own effect |
| 8 | stop execution and gap behaviour | fill behaviour of stop orders in fast moves, including gaps through the stop | a stop is not a guaranteed exit at the stop price |

**Status:** open.
**Blocks:** Gate 1; Gate 3's capital/liquidity check; the executability half of `R-05`.
**Responsible party:** external source the owner must authorize.
**Prohibited shortcut:** collecting this evidence in Stage 2P or in any stage that has not been
authorized to do so; inferring Nobitex depth from Binance depth; treating one day of snapshots as a
distribution; concluding "the order is small relative to daily volume" without a size-depth curve.

**Explicit note:** this register *lists* this evidence and does not collect it. Collecting it is a
separately authorized stage (`B-02` first, then a cost/liquidity study).

---

### B-05 — D-13 independent reviewer

**Owner record:** option B+E — a reviewer separate from the research agent, with no prior
involvement in the work under audit.

**What is missing:** a named reviewer, evidence of the qualifications the protocol requires, an
independence declaration, and the audit itself. None exists. `stage2l` already recorded
`SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`, and every stage from `2J` to `2L` was produced by the
same single agent, so no candidate reviewer exists inside this repository's history.

**Prerequisites the reviewer will need:** the frozen manifests and their hashes, read access to the
pre-registration, the dependence and cost models, and the ability to re-run the stated procedure.
Without those, an audit degenerates into a document review.

**Status:** open.
**Blocks:** Gate 4. Not a Gate 0 blocker — the *standard* is resolved; the *person* is not.
**Responsible party:** owner. This stage does not appoint, solicit, or conduct any audit.
**Prohibited shortcut:** using the research agent as its own reviewer; treating a second agent
session with the same instructions and the same context as "independent"; marking an audit complete
because the documents were reread.

---

### B-06 — D-15 deferred decision

**Owner record:** D-15 is deferred. This stage preserves that status exactly.

**What is missing:** nothing that Stage 2P may supply. The deferral stands.

**Status:** open, deliberately deferred.
**Blocks:** any new candidate or experiment that would depend on it.
**Responsible party:** owner.
**Prohibited shortcut:** revisiting the deferral because the surrounding work is being tidied;
reading the deferral as an implicit rejection; activating the candidate it concerns.

---

### B-07 — Gate 0 artifact consolidation

**What is missing:** the four Gate 0 artifacts the governance protocol requires — a signed owner
decision record, an economic objective memo, a risk policy statement, and a capital and execution
context statement. Today the substance exists across `stage2m` §2–§3, `stage2n`, and `stage2o`, but
no consolidated, frozen Gate 0 instrument exists, and `stage2o`'s records are stage records rather
than a gate instrument.

**Why it is a real blocker and not paperwork:** the consolidation is the step at which the objective,
the risk limits, and the capital base are stated in one place with one set of units. That is where
inconsistencies such as `B-08` and `B-09` get caught. Skipping it means the first place those
inconsistencies surface is inside a Gate 3 result.

**Status:** open.
**Blocks:** Gate 0 pass.
**Responsible party:** owner, or an author the owner explicitly authorizes. Writing these is not
research and consumes no data.
**Prohibited shortcut:** declaring the existing stage records to be the artifacts without
consolidating them; writing the memo in a way that introduces a new decision; restating D-01 or D-02
with different numbers.

---

### B-08 — Frequency-feasibility acknowledgment

**The arithmetic, restated from `GATE0_READINESS_ASSESSMENT.md` §7:** `0.10R` at `$10` per trade
needs `25` executed trades per year to reach `$250`. The historical opportunity frequencies are
A ≈ 20, D ≈ 10, B ≈ 7, C ≈ 3 per year — opportunities, before `p_exec < 1` reduces them to executed
trades. The sample requirement at the resolved MME is ≈ `785` independent observations, against
`12`–`71` opportunities over the whole `1,277`-day interval.

**What is missing:** an owner acknowledgment that this risk exists, or a revised annual target. The
owner may legitimately keep `$250` and accept that Gate 3 will probably stop on frequency. What is
not acceptable is discovering it at Gate 3 with no record that it was foreseen.

**Status:** open.
**Blocks:** Gate 0 pass (`R-21`); the Gate 3 frequency check.
**Responsible party:** owner.
**Prohibited shortcut:** lowering the annual target to fit the history without an owner decision;
reinterpreting opportunities as executed trades; assuming a higher `p_exec` to close the gap;
treating a 3.5-year interval as if it could be extended without new data.

---

### B-09 — `$2,500` cap versus tight stops

**The arithmetic, restated from `GATE0_READINESS_ASSESSMENT.md` §7.4:** the cap binds whenever the
stop distance is below `4%`. Below that line, `1R` shrinks in dollars, so `0.10R` is worth less than
`$10` and the trade count needed for `$250` rises — `50` trades at a `2%` stop, `100` at `1%`. Tight
stops also raise `cost_R`, because the frozen cost formula divides by the stop distance.

**What is missing:** owner acknowledgment, and later a Gate 2 sizing rule that states explicitly
whether `R` is defined by the capped notional (risk reduced) or the cap is to be exceeded (which the
owner has forbidden).

**Status:** open.
**Blocks:** Gate 2 sizing design; Gate 3 feasibility.
**Responsible party:** owner.
**Prohibited shortcut:** quietly scaling the notional cap with the stop distance to preserve `$100`
of risk; treating the shrinking `R` as harmless because the R-multiple limits still pass; ignoring
the cost interaction.

---

### B-10 — D-09 / D-12 numeric parameters

**What is missing:** the numeric dependence parameters (episode definition, block length, embargo
length) and the one-look logistics (who holds the validation split, when it may be opened). The
*standards* are resolved (D-09 option C; D-12 option A strict one-look); the numbers are not.

**Status:** open.
**Blocks:** Gate 2.
**Responsible party:** owner.
**Prohibited shortcut:** choosing parameters after seeing outcomes; selecting a block length that
minimises the design effect; opening the validation split "just to check the pipeline".

---

### B-11 — D-10 sample inputs

**What is missing:** `σ` (outcome variance in R), `DE` (design effect for the intended dependence
model), and `p_exec` (execution rate). With `δ = 0.10R` fixed, these three convert the ≈ `785`
independent-observation figure into an actual `required_opportunities`.

**Status:** open.
**Blocks:** Gate 2; Gate 3's feasibility comparison.
**Responsible party:** evidence for `σ` and `DE` from an authorized census or a documented,
pre-registered assumption; `p_exec` from `B-04`.
**Prohibited shortcut:** using Candidate D's `DE = 3.93` for a different design without stating it
as an assumption; estimating `p_exec` from the historical censuses' fill proxies; picking `σ` to
make the requirement small.

---

### B-12 — Operational risk excluded from limits

**Recorded fact:** D-02 option C adopted drawdown, per-trade loss, tail, and liquidity limits, and
did **not** adopt time under water, ruin probability, concentration, or operational risk.

**What this means:** venue outage, API failure, withdrawal restriction, and key-compromise risk are
real exposures of a Nobitex-executed strategy that the risk policy does not constrain. This is not a
defect to fix in Stage 2P and not a blocker; it is a disclosed exposure that the owner accepted by
choosing option C, and it should appear in the Gate 0 risk policy statement (`B-07`) as an explicit
exclusion rather than an omission.

**Status:** recorded, not actionable.
**Responsible party:** owner (disclosure only).

---

## 3. Dependency order

```
B-01 (real capital) ──► Gate 0 pass ◄── B-07 (artifacts) ◄── B-08, B-09 (acknowledgments)
                              │
B-02 (Nobitex access) ──► B-03 (cost distribution) ──► Gate 1 ──► B-11 (σ, DE, p_exec)
        │                                                     │
        └──────────► B-04 (liquidity/execution) ──► Gate 3 ───┘
                                                              │
B-10 (dependence/one-look numbers) ──► Gate 2 ────────────────┘
B-05 (reviewer) ──────────────────────────────────────► Gate 4
B-06 (D-15) ────────────────────────────────────► no new candidate
```

**Interpretation:** the critical path to Gate 0 runs through `B-01`, `B-07`, `B-08`, and `B-09` —
four items that need no data, no venue access, and no new research, only owner input and writing.
The expensive items (`B-02` to `B-04`) are all downstream of Gate 0 and cannot be started before the
owner authorizes them.

---

## 4. What this register does not do

- It does not close, schedule, or estimate any blocker.
- It does not rank blockers by importance to the owner's goals, only by gate order.
- It does not treat `B-06` as a gap; the deferral is the owner's decision.
- It does not authorize the collection of `B-03` or `B-04` evidence, or the appointment of `B-05`.
