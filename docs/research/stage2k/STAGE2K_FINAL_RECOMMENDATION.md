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

---

## 2. What would have to be true to reverse the decision

Each item below would require **new, separately authorized work**. None can be established by
re-reading this record, and none is claimed to be likely.

| # | condition | what it would change | status |
|---|---|---|---|
| R1 | A verified all-in venue cost of about 10 bp **and** a computed D canonical non-overlap count at that cost that meets the derived requirement | D becomes a live candidate instead of an untested one | **Unmeasured and uncomputed** |
| R2 | A pre-registered A-family variant, frozen before counting, reaches the derived requirement with a design effect of 2.00 or less | D3 becomes admissible | **Not attempted** |
| R3 | The owner declares a minimum effect of 0.48R or larger as the effect actually of interest | D1b becomes an informative in-sample test, though still not a test of the 0.15R premise | **Undecided** |
| R4 | An arms-length audit finds a **material counting error** — not a disagreement about thresholds — large enough to move a canonical count above the derived requirement | The affected verdict would need re-examination | **No such error is known:** the v2 counters were remediated after Stage 2F, and Stage 2H found no reopened critical |
| R5 | A repaired framework's derived rule is met by an already-frozen population without re-counting | The stage could proceed on existing objects | **Implausible:** all four canonical counts are below even the 0.23R requirement of 150 |

**Verified fact:** no item in this table is satisfied by evidence currently in the repository. The
recommendation is therefore not conditional on a judgement call; it is conditional on work that has
not been done and is not authorized.

**Interpretation:** R1 is the only reversal that could plausibly arrive through measurement rather
than through a new hypothesis. That is why the conditional path in §3 puts cost verification first.

---

## 3. If the project continues: the conditional path

This section describes what a defensible continuation would look like. It is **not** a plan, an
authorization, or a prediction that it would succeed.

### 3.1 Required order

| step | output | who decides |
|---|---|---|
| 1. Declare the minimum economic effect δ in R | A written number with a rationale | **Owner only** |
| 2. Measure the venue cost | Fee schedule, measured spread, realised slippage, depth, minimum notional, outage record | New authorized work |
| 3. Derive the sufficiency rule | `N_required` from δ, α, power, σ and a declared dependence allowance | New authorized work, pre-declared |
| 4. Re-freeze the framework | A new framework version; no candidate yet | New freeze |
| 5. Audit it | An arms-length review, not a self-audit | Governance |
| 6. Decide on a candidate | Only now, and only against the derived rule | Owner |

Steps 1–5 are D2. Step 6 is where D3 would be considered.

### 3.2 Why only A could survive step 6

| candidate | absolute ceiling before costs and overlap | can a derived requirement of roughly 126–349 be met? |
|---|---:|---|
| A primary | 195 valid triggers | Possibly not at 71 canonical; the control arm at 150 is the only object near any plausible requirement |
| A control | 445 confirmed triggers; 342 feasible; 150 matched-window canonical | The only arm recorded at the old floor |
| B | 32 pre-gate | **No** — the ceiling is 32 under any cost assumption |
| C | 17 triggers | **No** — the ceiling is 17 under any cost assumption |
| D | 295 pre-gate | **Unknown** — depends on cost and on the uncomputed canonical count |

**Verified fact:** B and C cannot be rescued by any rule that requires more than 32 or 17. This is
arithmetic on their funnel end-points, not a judgement.

### 3.3 What an A-family variant would have to contain to avoid being gate-fitting

1. A new name and a new specification; no edits to the frozen Stage 2C artifact.
2. Named differences from A, each with a rationale that does not refer to the observed counts.
3. The same development interval, the same data, the same cost and overlap conventions unless a
   change is pre-declared and justified by step 2.
4. The frozen A result (71) and the control result (150) reported beside the new count.
5. A pre-declared success and failure condition, written before the census runs.
6. No validation or out-of-sample rows.

**Interpretation:** without items 2 and 5, the variant is indistinguishable from lowering the bar
until something passes, which is the failure mode the project's own change control was built to
prevent.

### 3.4 A legitimate negative outcome of D2

If the derived rule requires more independent opportunities than any plausible variant of A can
produce, then the correct conclusion is that **this design cannot be tested on this interval** — not
that the rule should be relaxed again. That outcome would make D2 the final step of the programme
rather than a prelude to D3.

---

## 4. Rejected alternatives

| alternative | reason for rejection |
|---|---|
| **Proceed to Stage 2L on D or A (D1)** | Dominated by stopping on every criterion; detectable effect 0.480R / 0.332R against a 0.15R premise; a null would be uninformative |
| **Lower the floor to 71 or 34** | Changes the decision rule after seeing counts, with no derivation; makes the next stage unfalsifiable |
| **Relax the cost gate to 10 bp on the proxy's authority** | Substitutes an unmeasured assumption for a measurement; even at 10 bp, B is 32 and C is 17 |
| **Re-census B with a relaxed definition** | Ceiling of 32 before costs; a relaxed definition would be a different hypothesis with no evidential support |
| **Re-census D with a wider stop** | Would convert a stop-geometry failure into an accounting change; the frozen spec expressly forbids tuning the stop to pass the gate |
| **Change family now (D4)** | No evidence in the record about other families; would inherit the same framework defects |
| **Extend the development interval** | Consumes validation/OOS data; requires separate governance authorization; not a Stage 2K action |
| **Run Stage 2L on A's control because it reaches 150** | The control was defined as a selectivity diagnostic and explicitly not promoted; 150 is underived and sufficient only for 0.229R |
