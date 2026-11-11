# Stage 2Z — Authorization Boundary

**Stage:** 2Z (governance drafting and decision preparation only)
**Purpose:** state exactly what is prohibited now, what would change if the owner adopts O-1, what
would still be prohibited after adoption, and what a separate O-2 authorization must contain.
**Status:** boundary description only. **This document authorizes nothing.** Every activity named
below requires a separate written owner authorization under
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §2.1.
**Date:** 2026-11-11

---

## 0. The three states

| state | description |
|---|---|
| **State 0 — now** | O-1 pending, addendum not adopted. The protocol applies unchanged, including §3.5. |
| **State 1 — O-1 rejected** | identical to State 0. The rejection changes no permission. |
| **State 2 — O-1 adopted** | the addendum's `P-1`–`P-5` take effect. A research-leg readiness determination becomes *possible*; **no research is yet authorized**. |

The distinction between "possible" and "authorized" is the subject of this document.

---

## 1. State 0 — what is prohibited now

Everything below is prohibited today, and prohibited in this stage regardless of any future decision:

- market-data access, download, or processing of any kind;
- a feasibility census or any signal or opportunity count;
- strategy or candidate design, naming, selection, or revision;
- parameter selection, fitting, or optimisation;
- backtesting, simulation, or performance evaluation;
- expectancy, return, profitability, or P&L calculation or claim;
- validation or out-of-sample data access, in whole or in part;
- venue research, contact, or capability checking;
- cost, spread, depth, liquidity, fill, slippage, or latency measurement;
- real-capital sizing, a sizing convention, or sizing implementation in code;
- paper trading, live trading, leverage, or bot execution;
- changes to D-01–D-15, A-1–A-4, or any frozen artifact;
- Gate 0 passage, or progression to any gate;
- treating Binance proxy data as verified Nobitex execution evidence;
- treating a research-leg result as a real-capital return or as a reason to size real capital.

**Reason:** Gate 0 is recorded **NOT PASSED**; protocol §3.5 bars hypothesis registration and
strategy data access; no stage is authorized.

---

## 2. State 1 — if O-1 is rejected

No permission changes. The list in §1 remains in force without modification. Gate 0 remains
**NOT PASSED**, `R-08` remains `P`, `R-15` remains `B`, T-4 remains deferred, and the circularity
`C-3` remains.

The only difference is documentary: the record will state that the owner considered and rejected the
scoping addendum, so no later stage can describe the resulting stop as an oversight.

---

## 3. State 2 — if O-1 is adopted

### 3.1 What becomes possible

1. A **research-leg readiness determination** may be recorded once the research-leg rows in addendum
   §4.2 are satisfied. It is not a gate pass and not an authorization.
2. Protocol §3.5's prohibition is scoped to the base whose Gate 0 inputs are incomplete.
3. The readings in addendum §5 (`R-08` real-capital only; `R-15` per its own text; T-4 not a register
   blocking decision) become part of the governance text.

### 3.2 What does not change

| item | after adoption |
|---|---|
| Gate 0 status | **NOT PASSED** |
| `R-08` | `P`, unchanged code and requirement |
| `R-15` | `B`, unchanged code |
| `R-17`–`R-21` | `S`, unchanged |
| `R-05`, `R-10` | `P`, Gate 1 items |
| `R-22` | `P`, Gate 4 item |
| `B-02`–`B-05` | open, unchanged |
| checklist | 16 S / 4 P / 0 O / 1 B / 2 N/A |
| T-4 | deferred |
| D-01–D-15, A-1–A-4 | unchanged |
| Gate 1–6 sequence and criteria | unchanged |
| D-12 one-look and embargo | unchanged |

### 3.3 The critical distinction

> Adoption makes a research-leg authorization **permissible**. It does not make any activity
> **authorized**.

Without O-2, State 2 permits no market-data access, no census, no backtest, and no strategy design.
The determination in 3.1 is a prerequisite that O-2 must cite, not a substitute for it.

### 3.4 What adoption still prohibits

The full list in §1, with no exception except that a properly authorized O-2 stage may perform the
narrow Gate 1 analyses named in §4. Even then, the prohibitions on signals, outcomes, venue
measurement, sizing, and trading remain.

---

## 4. What a separate O-2 authorization must contain

O-2 is the only instrument that can turn State 2 into a permitted research stage. Under protocol
§2.1 it must name:

| element | required content |
|---|---|
| stage | Gate 1, research leg, explicitly named (e.g. "Stage 3 — Gate 1 data and cost validity") |
| objective | establish that the research dataset and the cost assumption are fit for the frozen experiment |
| artifacts | data-provenance manifest; data-quality report (gaps, duplicates, off-grid, zero-volume, invalid OHLC, partial buckets, segment boundaries); alignment report; development/validation/OOS date ranges and hashes; execution-cost evidence file; venue specification; access log |
| data | Binance historical, **development block only**; no validation or OOS row |
| analyses | dataset-hash verification; gap accounting; alignment reconciliation; block separation — **no signal count, no outcome, no return** |
| cost rule | the Binance proxy is a labelled research-leg assumption with a dated plan to replace it (protocol §4.3); never described as a Nobitex cost (2P §8) |
| venue rule | documentary specification only; every unresolved item marked **UNKNOWN** with the evidence that would resolve it; the Gate 1 record must disclose completeness item by item (`P-5`, `C-4`) |
| audit | the Gate 4 reviewer is not yet appointed (`I-4`); no confirmatory result is acceptable without the Gate 4 audit |
| prohibitions | no hypothesis registration; no census; no backtest; no expectancy; no venue contact beyond document collection; no sizing; no trading |
| stop condition | stop on any hash mismatch, any validation/OOS read, any unlabelled assumption, or any scope breach |

### 4.1 What O-2 would not authorize

Gate 2 registration, Gate 3 census, a backtest, a strategy design, venue measurement, real-capital
sizing, or trading. Each needs its own authorization.

### 4.2 Ordering

O-2 depends on O-1 being adopted. If O-1 is rejected, O-2 cannot be validly issued in the form
contemplated here, because protocol §3.5 would still bar the stage. An owner who wants a research
stage without the addendum must record the exception explicitly (Stage 2Y Path B) — the agent cannot
choose that for them.

---

## 5. Claim boundary, restated for this stage

| claim | permitted in State 0 | permitted in State 2, before O-2 | permitted after an authorized Gate 1–6 sequence |
|---|---|---|---|
| "the addendum is drafted" | yes | yes | yes |
| "the addendum is adopted" | no | only if the owner's dated statement exists | same |
| "the research-leg inputs are complete" | no | yes, as a determination | yes |
| "Gate 0 has passed" | no | **no** | **no** |
| "a strategy is feasible" | no | no | at Gate 3, within its stated scope |
| "the strategy is profitable" | no | no | **no** — profitability is not an estimand |
| "Nobitex can execute this strategy" | no | no | only with venue evidence and measured execution |
| "the real-capital objective is achievable" | no | no | not until T-4 is decided |
| "the account should risk `$X` per trade" | no | no | only after T-4 |

### 5.1 Required reporting sentence

Every Gate 5 and Gate 6 report on the research-leg track must state:

> *"This result is research-leg evidence on historical Binance data under a labelled cost assumption.
> It is not evidence of Nobitex execution feasibility, not a real-capital return, and not a sizing
> recommendation."*

---

## 6. Prohibitions that survive adoption

Even in State 2, and even after O-2, the following remain prohibited unless a later, separate owner
authorization names them:

- any real-capital claim, real-capital return, drawdown, sizing, or funding calculation;
- treating Binance depth, the `26 bp` proxy, or a published fee schedule as verified Nobitex execution
  evidence;
- opening validation or OOS data before its gate;
- more than one validation look, or any reuse of the OOS block;
- counting signals or outcomes in a stage not authorized for them;
- implementing a sizing convention in code before T-4;
- paper or live trading, leverage, or bot execution before the Gate 6 decision and a separate
  deployment authorization;
- any change to a frozen artifact or to D-01–D-15 / A-1–A-4.

---

## 7. Stop conditions

Any authorized stage must stop and report without proceeding if:

1. a dataset, manifest, or frozen artifact does not match its recorded hash;
2. a validation or OOS row is read before its gate;
3. signal counting, outcomes, backtesting, expectancy, or P&L appear in a stage not authorized for
   them;
4. a cost, venue constraint, or dependence parameter is used without being labelled an assumption with
   a plan;
5. a Nobitex value is stated without a dated source;
6. a document begins computing a real-capital return, drawdown, sizing, or funding requirement;
7. Gate 1 finds the data or cost basis unfit — the experiment is then inconclusive or not authorized,
   never "assumed to pass";
8. Gate 3's upper bound is below `required_opportunities` — a legitimate stop, not a reason to lower
   the bar;
9. the Gate 4 reviewer has prior involvement — the result must then be labelled provisional or not
   accepted;
10. a protocol amendment is needed mid-stage — stop and escalate; never amend around a defect found
    during execution;
11. the owner withdraws the authorization.

---

## 8. Owner decisions remaining

| ID | decision | state |
|---|---|---|
| **O-1** | adopt / reject / revise the addendum | **PENDING — this stage** |
| **O-2** | named Gate 1 research-leg stage authorization | not authorized; depends on O-1 |
| **O-3** | authorize documentary venue evidence collection (I-2, I-3) | pending |
| **O-4** | authorize quote sampling for spread, and when | pending |
| **O-5** | create a measurement-only execution category (`C-6`), or keep the assumption | pending |
| **O-6** | appoint the independent reviewer (I-4) before Gate 4 | pending |
| **O-7** | T-4 itself, only after the six evidence items exist | pending |
| **O-8** | reaffirm or restate `$250` on `$100` (T-5) | pending |

None is decided, implied, or pre-filled by Stage 2Z.

---

## 9. Confirmations

1. No research occurred in this stage: no data was read, no census run, no backtest, no expectancy, no
   strategy designed, no venue contacted, no cost measured, no sizing selected, no trade placed.
2. No gate was passed or advanced. Gate 0 remains **NOT PASSED**.
3. No frozen artifact, decision, threshold, or owner-supplied value changed.
4. No owner decision was created, inferred, or pre-filled. O-1 remains pending; O-2 is not authorized.
5. This document is a boundary description, not an authorization.
