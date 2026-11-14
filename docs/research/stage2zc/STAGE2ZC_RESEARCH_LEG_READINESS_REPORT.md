# Stage 2ZC — Research-Leg Readiness Determination

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Determination:** **Gate 0 research-leg inputs complete.**
**Gate 0 status:** **NOT PASSED.** This determination is not a Gate 0 pass and may never be recorded as
one.
**Date:** 2026-11-14
**Authority:** addendum §4.2 and §4.3; Stage 2X governance status record §1; Stage 2V reassessment §2.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

Every requirement that the adopted addendum marks "applies — `S`" for the research-leg base is satisfied
in the current checklist, and `R-15` is satisfied for the research leg under its own text. The record may
therefore state **"Gate 0 research-leg inputs complete."** That is a research-leg readiness determination,
not Gate 0 passage. Gate 0 remains **NOT PASSED** because `R-08` is `P` and `R-15` is `B` for real
capital, and T-4 remains deferred. The determination satisfies no requirement that is not already `S` for
the research leg, does not apply to `R-05`, `R-10`, or `R-22`, authorizes no stage, and says nothing about
real capital.

---

## 1. The rule being applied

Addendum §4.3 states:

> When every requirement marked "applies — `S`" for the research-leg base in §4.2 is satisfied, and
> `R-15` is satisfied for that base per its own text, the record may state: **"Gate 0 research-leg inputs
> complete"** — a **research-leg readiness determination**, not Gate 0 passage.

The same section fixes five limits: the determination is not a Gate 0 pass; it satisfies no requirement
not already `S` for the research leg; it authorizes no stage; it does not apply to `R-05`, `R-10`, or
`R-22`; and it says nothing about real capital. All five are restated in §4 below.

---

## 2. Current checklist

`stage2x/STAGE2X_GOVERNANCE_STATUS_RECORD.md` §1 records 23 rows as **16 S / 4 P / 0 O / 1 B / 2 N/A**:

| group | rows |
|---|---|
| **S (16)** | R-01, R-02, R-03, R-04, R-07, R-09, R-11, R-12, R-13, R-14, R-16, R-17, R-18, R-19, R-20, R-21 |
| **P (4)** | R-05, R-08, R-10, R-22 |
| **B (1)** | R-15 |
| **N/A (2)** | R-06, R-23 |

`R-15` is `B` **globally** and `S` for the research leg under its own text. The research-leg set is
therefore the 16 `S` rows plus `R-15` — 17 rows.

---

## 3. Row-by-row determination

The status codes below are the current checklist's, not the Stage 2P baseline. The evidence column points
to the record that established each row; this stage re-derives none of them and changes none of them.

| row | requirement | research-leg status | evidence |
|---|---|---|---|
| R-01 | MME definition and value | **S** | Definition A, `0.10R` net (Stage 2O; `stage2p` §5) |
| R-02 | Maximum drawdown limit | **S** | `15%` of prior equity peak, research leg (`stage2p` §5) |
| R-03 | Per-trade loss limit | **S** | `1.00R`, `1%` of equity at entry (`stage2p` §5) |
| R-04 | Tail limit | **S** | `CVaR95 = 0.50R` (`stage2p` §5) |
| R-07 | Capital and sizing context, research leg | **S** | `$10,000`, `1%` fixed-fractional, one position, no leverage (`stage2p` §5) |
| R-09 | Primary and secondary estimands | **S** | D-03 option A primary, option D co-primary; D-07 option A (`stage2p` §5) |
| R-11 | Error-control objective | **S** | `α = 5%` two-sided, power `80%`, hierarchical allocation (D-08 A+B) |
| R-12 | Dependence-treatment standard | **S** | D-09 option C; numeric parameters at Gate 2 |
| R-13 | Every blocking decision resolved | **S** | D-01–D-15 unchanged; T-4 is not a register decision (addendum §5.4) |
| R-14 | No unresolved decision silently defaulted | **S** | every unresolved item is named in `stage2o` §9 and `OPEN_BLOCKER_REGISTER.md` |
| R-15 | Objective in testable form | **S for the research leg** | its own text; `B` for any real-capital claim |
| R-16 | Risk limits in units compatible with the primary metric | **S** | per-trade and tail in `R`; drawdown in % of peak; liquidity in USD notional |
| R-17 | Signed owner decision record | **S** | A-1 signed 2026-11-11; `stage2v` §3; `R-17 P → S` |
| R-18 | Economic objective memo | **S** | A-2 ratified 2026-11-11 by T-1 |
| R-19 | Risk policy statement | **S** | A-3 ratified 2026-11-11 by T-2 |
| R-20 | Capital and execution context statement | **S** | A-4 ratified 2026-11-11 by T-3 |
| R-21 | Frequency-feasibility consistency acknowledged | **S** | owner acknowledgment recorded; `stage2v` §2 |

All 17 rows are satisfied for the research leg.

---

## 4. What the determination does not do

1. **It is not a Gate 0 pass.** The line **"Gate 0: NOT PASSED"** remains the global verdict and is
   unchanged.
2. **It satisfies no requirement that is not already `S` for the research leg.** In particular, it does
   not satisfy `R-05`, `R-08`, `R-10`, `R-15` for real capital, or `R-22`.
3. **It does not apply to `R-05`, `R-10`, or `R-22`.** Those remain the Gate 1 and Gate 4 items they
   already are:
   - `R-05` — liquidity / position-size constraint: `P`; venue depth, minimum notional, and lot step are
     not verified. This stage's venue register marks them **UNKNOWN**.
   - `R-10` — execution venue and cost-evidence standard: `P`; no venue evidence and no measured cost
     distribution. This stage records a labelled proxy and a dated replacement plan, not evidence.
   - `R-22` — independent-audit standard and reviewer: `P`; no reviewer identified and no Gate 4 audit.
4. **It authorizes no stage.** Gate 2 requires its own owner authorization.
5. **It says nothing about real capital.** `R-08` is `P`, `R-15` is `B` for real capital, and T-4 remains
   deferred.

---

## 5. Real-capital status, restated

| item | status | consequence |
|---|---|---|
| `R-08` — real-capital capital and sizing context | **P** | `$100` real capital is recorded; the per-trade sizing convention is deferred (T-4) |
| `R-15` — objective in testable form, real capital | **B** | blocked for any real-capital claim |
| `T-4` | **deferred** | the six-item evidence set is not met; see addendum §8 |
| Gate 0 | **NOT PASSED** | no real-capital claim of any kind may be made |

The `$250` objective on `$100` capital remains an unvalidated owner objective. Nothing in this
determination makes it testable, achievable, or evidenced.

---

## 6. Governance status after this report

| gate / decision | status |
|---|---|
| Gate 0 | **NOT PASSED** |
| Gate 0 research-leg inputs | **complete** (this report) |
| Gate 1 | **authorized and in progress under O-2A** |
| Gate 2 | not authorized |
| T-4 | deferred |
| `R-08` | `P` |
| `R-15` (real capital) | `B` |
| `R-05`, `R-10` | `P`; Gate 1 items, disclosed in the venue register |
| `R-22` | `P`; Gate 4 item |

---

## 7. Integrity of this report

1. It records the determination the adopted text permits, and no more.
2. It changes no checklist row, status code, decision value, threshold, or frozen artifact.
3. It does not read a validation or OOS row, compute a signal or outcome, or measure a venue value.
4. It makes no real-capital claim and no execution-feasibility claim.
5. Its only source for the status codes is the current governance record; where the Stage 2P baseline
   differs, the later record controls and the difference is preserved in the record that made it.

---

**Research-leg readiness: Gate 0 research-leg inputs complete. Gate 0: NOT PASSED. Gate 1: authorized under O-2A only. Real-capital work: not authorized.**
