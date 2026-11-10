# Stage 2O — Owner Response Record

**Stage:** 2O (owner-decision resolution only)
**Status:** **PARTIAL — D-01 resolved; D-02 scope resolved; four D-02 numeric limits open.**
**Date opened:** 2026-11-10 (UTC)
**Companion packet:** `STAGE2O_D01_D02_DECISION_PACKET.md`

**Rule:** a decision is recorded here only after the owner has explicitly selected or defined a value.
An unanswered item remains open. Nothing is defaulted.

---

## 1. Response summary

| ID | decision | status | value | units | date |
|---|---|---|---|---|---|
| D-01a | numeric minimum net R per executed trade | **RESOLVED** | **0.10R** | R per executed trade | 2026-11-10 |
| D-01b | numeric annual contribution target | **RESOLVED** | **`$250`/year** | USD/year on `$10,000` research leg | 2026-11-10 |
| D-02e | scope of the D-02 risk limits | **RESOLVED** | **Research leg only** | `$10,000` research leg | 2026-11-10 |
| D-02a | maximum drawdown | **OPEN** | — | % of equity peak | — |
| D-02b | per-trade loss limit | **OPEN** | — | R and % of equity | — |
| D-02c | tail-risk limit | **OPEN** | — | CVaR95 in R | — |
| D-02d | liquidity / position-size limit | **OPEN** | — | % of visible depth | — |

**D-01 overall:** **RESOLVED** — definition A; `δ_R = 0.10R`; annual target `$250`/year.
**D-02 overall:** **OPEN** — option C selected; scope resolved as research leg only; all four numeric limits unresolved.

---

## 2. D-01a — Numeric `δ_R`

### 2.1 Owner answer

- **Status:** resolved.
- **Value:** **0.10R** net per executed trade.
- **Units:** net R per executed trade, after all-in costs.
- **Dollar scale:** `$10` per trade at 1R = `$100` on the `$10,000` research leg.
- **Conditions:** the numeric sample requirement remains pending `σ`, `DE`, and `p_exec`.

### 2.2 Implications

1. The per-trade economic bar is the smallest listed value. It requires substantially more evidence
   than `0.15R`–`0.30R`.
2. At 1% risk, a trade at the MME earns `$10` on a `$100` risk unit. The annual target will therefore
   demand high frequency to be meaningful.
3. The illustrative requirement is `≈ 785` independent observations; dependence inflation and
   execution losses will raise the opportunity requirement further.
4. D-01 remains **open** overall until the annual contribution target is also set.
5. Gate 0 remains blocked, and D-10 still cannot produce a final numeric requirement without `σ`,
   `DE`, and `p_exec`.

### 2.3 Confirmation

- The owner explicitly selected 0.10R.
- The owner explicitly confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 3. D-01b — Numeric annual contribution target

### 3.1 Owner answer

- **Status:** resolved.
- **Value:** **`$250` per year**.
- **Percent:** **2.5%** of the `$10,000` research leg.
- **Units:** net annual contribution, USD/year, under the D-04 research convention.
- **Implied frequency:** **≈ 25 executed trades/year** at `δ_R = 0.10R`, before compounding and
  before `p_exec < 1`.
- **Conditions:** frequency feasibility remains a Gate 3 question.

### 3.2 Implications

1. D-01 is now complete: definition A, `δ_R = 0.10R`, and annual target `$250`/year.
2. The target is modest, but at `0.10R` it still implies about 25 executed trades per year. That is
   above Candidate A's historical opportunity frequency of about 20/year and well above B, C, and D.
3. Because `p_exec < 1`, the required **opportunity** count is higher than 25/year. Gate 3 may
   therefore fail on frequency even though the annual target is low.
4. The annual metric is co-primary and hierarchical: the per-trade test must pass first, then the
   annual target is tested conditionally.
5. D-01 being resolved does **not** pass Gate 0. D-02, the D-04 real-capital check, D-05 Nobitex
   access, and D-13 remain unresolved.
6. No compounding forecast, performance estimate, or backtest is implied by this target.

### 3.3 Confirmation

- The owner explicitly selected `$250`/year.
- The owner explicitly confirmed the record above before it was written.
- No value in this entry was defaulted by the research agent.

---

## 4. D-02e — Scope of the D-02 risk limits

### 4.1 Owner answer

- **Status:** resolved.
- **Scope:** **Research leg only.**
- **Basis:** `$10,000` equity, 1% risk, fixed-fractional, one position, no leverage, spot long-only.
- **Real capital:** not covered; the D-04 real-capital check remains open and separate.
- **Conditions:** the real-capital translation remains open.

### 4.2 Implications

1. The drawdown, per-trade, tail, and liquidity limits will be expressed on the `$10,000` research leg.
2. They are **not** automatically the owner's live limits. A separate real-capital translation is
   required before any live-decision claim.
3. The real-capital amount remains undisclosed and the D-04 check remains open.
4. The limits can be evaluated against research-leg evidence without implying live authorization.
5. If real capital differs from `$10,000`, the position sizes, liquidity check, and currency
   drawdown will change accordingly.
6. This decision does not resolve any of the four numeric limits.

### 4.3 Confirmation

- The owner explicitly selected research leg only.
- The owner explicitly confirmed the record above before it was written.
- No scope was defaulted by the research agent.

---

## 5. D-02a — Maximum drawdown

### 5.1 Owner answer

- **Status:** open — no answer recorded.
- **Value:** not set.
- **Units:** % of equity peak, net-of-cost mark-to-market equity.
- **Conditions:** none recorded.

### 5.2 Confirmation

- No confirmation has been received.
- No value has been defaulted.

---

## 6. D-02b — Per-trade loss limit

### 6.1 Owner answer

- **Status:** open — no answer recorded.
- **Value:** not set.
- **Units:** R and % of equity at entry.
- **Conditions:** none recorded.

### 6.2 Confirmation

- No confirmation has been received.
- No value has been defaulted.

---

## 7. D-02c — Tail-risk limit

### 7.1 Owner answer

- **Status:** open — no answer recorded.
- **Value:** not set.
- **Units:** CVaR95 in R.
- **Conditions:** none recorded.

### 7.2 Confirmation

- No confirmation has been received.
- No value has been defaulted.

---

## 8. D-02d — Liquidity / position-size limit

### 8.1 Owner answer

- **Status:** open — no answer recorded.
- **Value:** not set.
- **Units:** % of visible top-of-book depth, or a stated alternative.
- **Conditions:** none recorded.

### 8.2 Confirmation

- No confirmation has been received.
- No value has been defaulted.

---

## 9. Explicitly unresolved items carried forward

- **D-01:** **resolved** — `δ_R = 0.10R` and annual target `$250`/year; Gate 3 frequency feasibility
  remains untested.
- **D-02:** scope resolved as research leg only; all four numeric limits remain open.
- **D-04:** real-capital check remains open.
- **D-05:** Nobitex access and cost evidence remain open.
- **D-06:** the p95 rule cannot be applied until a Nobitex cost distribution exists.
- **D-07:** the annual target remains pending D-01.
- **D-13:** no reviewer or specialist has been identified and no audit has been performed.
- **D-15:** remains deferred; not revisited here.

---

## 10. Integrity statement

- No Stage 2M or Stage 2N artifact was modified.
- No historical research artifact was modified.
- No market data, validation row, or out-of-sample row was accessed.
- No census, backtest, bootstrap, Monte Carlo, or optimization was run.
- No P&L, expectancy, drawdown, Sharpe, Sortino, CAGR, or equity curve was computed.
- No candidate, strategy, experiment, or implementation stage was authorized.
- No Gate 0–5 progression was authorized.
- No Stage 2P was started.
