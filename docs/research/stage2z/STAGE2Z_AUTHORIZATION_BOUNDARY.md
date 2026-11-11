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
