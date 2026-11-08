# Stage 2K — Final Recommendation

**Status:** historical review and research design only. No candidate, no census, no backtest, no
market-data processing, no Stage 2L.
**Date:** 2026-11-08.
**Inputs:** `HISTORICAL_RESEARCH_SYNTHESIS.md`, `FAILURE_MODE_ANALYSIS.md`,
`RESEARCH_DIRECTION_COMPARISON.md`, and the Stage 2A–2J artifacts they cite.

---

## 0. The recommendation

**Stop the current strategy family under the current research framework.**

Do not proceed to an outcome study on A, B, C or D. Do not lower the 150 floor. Do not relax the
26 bp cost gate. Do not open validation or out-of-sample data. Do not edit a frozen artifact.

If the owner wants to keep the option of testing a candidate later, the only defensible next step is
to **repair the framework first** (D2 in `RESEARCH_DIRECTION_COMPARISON.md`): verify the real venue
cost, derive a sufficiency rule from an owner-declared minimum effect, and re-freeze and audit that
framework. Only after that would a **single pre-registered variant of A's family** (D3) be worth
considering, and only if its derived count requirement is plausible before the census is run.

Candidate A is the only historical object worth revisiting. Its unconditioned control arm — 150
matched-window non-overlapping events — is the only object in the entire record that reaches the
frozen floor, and the freeze explicitly declined to promote it.

**Neither the framework repair nor the A-family variant is authorized by Stage 2K.** They are
described here so that the owner can decide whether to authorize them separately.

### 0.1 What exactly is being stopped

| stopped | not stopped |
|---|---|
| Further candidate design inside the trend-continuation / breakout / intraday-momentum family under the current framework | Preserving and citing every Stage 2A–2J artifact |
| Any Stage 2L outcome study on A, B, C or D | An owner decision, on its own authority, to authorize D2 later |
| Any change to a frozen specification, threshold or manifest | Research outside this programme |
| Any read of validation or out-of-sample rows | Publishing the negative result |
| Any re-count intended to make a failed candidate pass | Auditing the record for errors |

The stop is a decision about **research allocation under this framework**, not about the market and
not about the strategy family in general. That distinction is the whole point of the analysis in
`FAILURE_MODE_ANALYSIS.md` §9.

---

## 1. Why the decision is to stop

### 1.1 The claim the record fully establishes

**Verified fact:** four frozen designs were censused once each on 2021-01-01 → 2024-07-01, and none
reached its applicable opportunity gate:

| candidate | canonical opportunities | gate | outcome | smallest detectable effect at that count |
|---|---:|---:|---|---:|
| A — MTF trend pullback | 71 | 150 | fail | 0.332R |
| B — expansion and retest | 24 | 150 | fail | 0.572R |
| C — compression breakout | 12 | 200 (Stage 2A gate) | fail | 0.809R |
| D — session momentum | 34 | 150 | fail | 0.480R |

That is the whole of the established claim. It is enough to stop this programme under this framework,
because the framework's own admissibility rule was not met and the rule was frozen before counting.

### 1.2 The stop does not rest on the 150 floor

This matters, because the floor is the weakest link in the record.

**Verified fact:** 150 was introduced at the Stage 2C freeze without a statistical derivation; Stage 2A
had used 200; the Stage 2D redesign says calling it "pre-registered" overstates the record
(`STAGE2D_STRATEGY_REDESIGN.md` §1.3). So "the floor said no" is not a sufficient argument.

Remove the floor and ask what a defensible rule would say. The project's stated effect of interest is
0.15R. Under its own independence assumptions that requires about 349 observations; at 150 the
smallest detectable effect is 0.229R. So:

- **B and C are capped below any floor.** B's entire pre-gate population is 32 and C's entire trigger
  population is 17. No threshold revision, no cost revision and no definition change short of a new
  hypothesis can lift them.
- **A's best recorded arm sits exactly at the old floor** (control, 150 matched-window), and 150 is
  sufficient only for 0.229R — not for 0.15R — before any dependence adjustment. The project's own
  concentration diagnostics put A's effective sample near 13.
- **D is the only candidate whose count might exceed 150 under a verified lower cost**, and the number
  that would settle it — the canonical non-overlap count at low cost — was never computed. Its
  primary population also fails the concentration screen (design effect 3.93) and has no cost-feasible
  signal after 2022-09.

**Interpretation:** the stop survives the removal of the 150 floor. What remains is not "150 was not
met"; it is "no candidate is admissible under any sufficiency rule tied to the effect the project says
it cares about, and the two candidates that are not structurally capped depend on unmeasured
quantities."

### 1.3 Why not amend the gate and proceed (D1)

**Verified by inspection:** in the ordinal comparison, D1 is dominated by D5 on every criterion and
strictly worse on four (evidence, effort, pre-registration safety, governance safety). It has no
advantage that stopping lacks.

The substantive reason is the detectable-effect arithmetic. Proceeding with 34 events answers only
whether the effect exceeds 0.480R. If the true effect is 0.15R — the project's own assumption — the
study will fail to reject and the project will have learned nothing it did not already know, while
having consumed its remaining in-sample budget and, in any likely sequel, out-of-sample data. A test
that cannot distinguish the hypothesis from the null it was designed against is not a test.

**Interpretation:** an effect of 0.48R per trade on a 1–3 day continuation setup would be very large.
That does not make it impossible; it makes it a different question from the one the project has been
asking, and the record contains no outcome evidence either way.

### 1.4 What continuing would cost

| cost | why it matters |
|---|---|
| The remaining in-sample statistical budget | Spent on a test whose detectable effect is 3× the target |
| Credibility of the gate | Lowering it after seeing counts removes the only pre-commitment the programme has |
| Multiplicity | Sequential candidates and variants without a pre-declared rule inflate the chance of a false positive |
| Out-of-sample reserve | Any positive in-sample result would need OOS confirmation, which the programme has not planned or authorized |
| Sunk-cost pressure | Each additional stage makes stopping harder without adding evidence |

### 1.5 Why stopping is not the same as declaring failure of the hypothesis

The record shows **feasibility failure**, not unprofitability. No outcome was ever observed on any
candidate; no return, expectancy, win rate or P&L was computed at any point in Stages 2A–2J
(Verified fact: every census report states this). "Too few opportunities to test" and "the strategy
loses money" are different findings, and this recommendation depends only on the first.

What is also not claimed: that BTC lacks these opportunities, that the family has no edge, that the
26 bp proxy is wrong, or that the v2 freeze is unsound. Each of those is **Unknown** on this record.
