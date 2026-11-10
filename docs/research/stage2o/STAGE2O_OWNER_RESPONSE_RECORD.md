# Stage 2O — Owner Response Record

**Stage:** 2O (owner-decision resolution only)
**Status:** **PARTIAL — D-01 resolved; D-02 scope, maximum drawdown, per-trade, and tail limits resolved; one D-02 numeric limit open.**
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
| D-02a | maximum drawdown | **RESOLVED** | **15%** | % of prior equity peak, research leg | 2026-11-10 |
| D-02b | per-trade loss limit | **RESOLVED** | **1.00R** | R; % of equity at entry | 2026-11-10 |
| D-02c | tail-risk limit | **RESOLVED** | **0.50R** | CVaR95 in R, research leg | 2026-11-10 |
| D-02d | liquidity / position-size limit | **RESOLVED** | **`$2,500` fixed notional** | USD notional, research leg | 2026-11-10 |

**D-01 overall:** **RESOLVED** — definition A; `δ_R = 0.10R`; annual target `$250`/year.
**D-02 overall:** **RESOLVED** — option C; research-leg scope; maximum drawdown 15%; per-trade limit 1.00R; tail limit 0.50R CVaR95; position-size limit `$2,500` fixed notional. Real-capital translation and venue liquidity evidence remain open.

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

- **Status:** resolved — explicit owner approval.
- **Value:** **15% maximum drawdown**.
- **Units:** percentage of the prior equity peak.
- **Measurement basis:** net-of-cost, mark-to-market research-leg equity, measured peak-to-trough as a
  percentage of the prior equity peak.
- **Research-equity reference:** `$10,000`.
- **Dollar illustration:** **`$1,500`** at a `$10,000` equity peak.
- **Scope:** `$10,000` research leg only.
- **Real-capital translation:** remains open.

### 5.2 Implications

1. The drawdown constraint is now a fixed, pre-outcome risk limit at 15% of the running research-leg
   equity peak.
2. At a `$10,000` peak the limit corresponds to a `$1,500` decline; at a higher peak the currency
   amount scales with the peak, because the limit is a percentage.
3. The limit is evaluated on mark-to-market, net-of-cost equity, so open-position declines and
   execution costs count, not only closed-trade results.
4. It applies to the research leg only. It does not become a live/real-capital limit, and the D-04
   real-capital check remains open and separate.
5. The per-trade, tail, and liquidity limits remain unresolved; the drawdown limit does not imply
   their values.
6. Gate 0 remains blocked by the unresolved D-02 items and by other carried-open conditions.

### 5.3 Confirmation

- The owner explicitly approved 15% maximum drawdown.
- The approval specified the `$10,000` research-equity reference, the `$1,500` dollar illustration,
  the net-of-cost mark-to-market measurement basis, the research-leg scope, and the open real-capital
  translation.
- The measurement definition was not changed by the research agent, and no additional assumption was
  introduced.
- No value in this entry was defaulted by the research agent.

---

## 6. D-02b — Per-trade loss limit

### 6.1 Owner answer

- **Status:** resolved — explicit owner approval.
- **Value:** **1.00R**.
- **Percent basis:** **1.00% of equity at entry**.
- **Dollar illustration:** `$100` per trade at 1R = `$100` on the `$10,000` research reference.
- **Measurement:** realized **net** loss on a single executed trade, after entry and exit costs,
  including adverse gap and slippage beyond the planned stop.
- **Declared basis:** equity at entry, not current equity.
- **Scope:** `$10,000` research leg only; real-capital translation remains open.
- **Conditions:** gap and slippage compliance remains evidence-dependent.

### 6.2 Implications

1. This is a constraint on the realized outcome, distinct from the frozen 1% fixed-fractional *sizing*
   rule.
2. Because there is **no overshoot allowance**, a gap-through-stop or material slippage that produces
   a realized loss above 1R is a **policy breach**, unless position sizing includes an explicit
   slippage/gap buffer that keeps the realized loss at or below 1R.
3. The owner has therefore accepted the tighter of the two interpretations: 1% is both the sizing
   target and the realized per-trade ceiling.
4. A binding 1R ceiling may reject rules whose stops fill poorly, and may require smaller positions,
   which lowers contribution at `δ_R = 0.10R`.
5. Interaction with D-02a: at a 15% drawdown limit, roughly fifteen full 1R losses reach the budget,
   before gaps shorten the count.
6. Gap, slippage, and stop-fill distributions remain **unmeasured**; Nobitex execution evidence (D-05)
   is open, so compliance cannot yet be verified.
7. D-02d remains open; D-02c was subsequently resolved at 0.50R CVaR95, and neither value is changed
   by this entry.

### 6.3 Confirmation

- The owner explicitly selected 1.00R and confirmed this record before it was written.
- The approval specified the realized net-loss measurement, the equity-at-entry basis, the absence of
  an overshoot allowance, the research-leg scope, and the open real-capital translation.
- No value or basis in this entry was defaulted by the research agent.

---

## 7. D-02c — Tail-risk limit

### 7.1 Owner answer

- **Status:** resolved — explicit owner approval.
- **Value:** **0.50R**.
- **Unit:** R, where 1R is the trade's initial stop risk.
- **Dollar translation:** `$50` per tail-average trade at 1R = `$100` on the `$10,000` reference.
- **Equity translation:** 0.50% of the `$10,000` research leg.
- **Definition:** average net loss across the worst 5% of executed trades, after entry and exit costs,
  including gap, slippage, and stop-execution effects.
- **Observation unit:** individual executed trade outcomes.
- **Selection:** order net trade R outcomes worst-to-best and average the worst 5%.
- **Scope:** `$10,000` research leg only; real-capital translation remains open.
- **Conditions:** the tail estimate remains evidence-dependent.

### 7.2 Implications

1. This is a **binding** tail constraint: under D-02b's 1.00R no-overshoot ceiling, 0.50R is below the
   per-trade ceiling and therefore actually constrains the worst-5% average.
2. It is independent of D-02a and D-02b: it can fail even when no single trade exceeds 1.00R and the
   path drawdown stays under 15%.
3. It is stricter than the packet's illustrative 1.5R–3.0R values; those would have been non-binding
   given the recorded per-trade limit.
4. Interaction with D-02a: at a 0.50R CVaR95 (`$50`), roughly thirty worst-5% average losses reach the
   `$1,500` 15% drawdown budget, before clustering and other losses.
5. The estimate cannot yet be computed or verified: gap, slippage, and stop-fill distributions are
   unmeasured, and no historical analysis is authorized in Stage 2O.
6. This is an owner-selected risk tolerance, **not** a measured description of the strategy's tail
   behavior.
7. D-02d remains open and is unaffected by this value.

### 7.3 Cross-consistency note

D-02b is recorded as 1.00R with no overshoot allowance. If every compliant trade loss is at or below
1.00R, the average of the worst 5% cannot exceed 1.00R. The 0.50R limit is therefore inside the
feasible region and binding; a limit above 1.00R would have been non-binding under strict D-02b
compliance. This note records an arithmetic consequence of the two decisions; it does not re-open
D-02b or alter its measurement.

### 7.4 Confirmation

- The owner explicitly selected 0.50R and confirmed this record before it was written.
- The approval specified the CVaR95 definition, the worst-5% averaging, the executed-trade observation
  unit, the R unit, the research-leg scope, and the open real-capital translation.
- No value or definition in this entry was defaulted by the research agent.

---

## 8. D-02d — Liquidity / position-size limit

### 8.1 Owner answer

- **Status:** resolved — explicit owner approval.
- **Rule type:** fixed maximum notional.
- **Exact rule:** `notional_usd ≤ $2,500` at entry.
- **Unit:** USD notional (quantity × entry price).
- **Equity translation:** 25% of the `$10,000` research leg.
- **Scope:** `$10,000` research leg only; real-capital translation remains open.
- **Evidence status:** arithmetically enforceable now; **not** a verified liquidity constraint.
- **Conditions:** venue depth, volume, minimum notional, lot size, slippage, and impact remain
  unmeasured.

### 8.2 Implications

1. The rule is a **notional ceiling**, not a depth or volume participation rate. It does not establish
   that `$2,500` is executable on Nobitex.
2. Because D-04 sizes positions at 1% risk via `notional = $100 / stop_fraction`, the cap binds
   whenever `stop_fraction < 4%` (stop tighter than 4% of entry). In that region realized planned risk
   falls **below** `$100`, so R is smaller than 1% of equity.
3. That interaction can reduce the annual contribution at `δ_R = 0.10R`, weakening but not changing the
   D-01 `$250`/year target. It does **not** relax D-02b's 1.00R or D-02c's 0.50R limits.
4. Maximum exposure remains ≤ `$10,000` mechanically under spot long-only, one position, no leverage;
   the `$2,500` cap is tighter and binding.
5. The cap is measurable now from price and position size alone, so the rule can be applied in any
   future test without venue data.
6. It cannot be validated as a liquidity constraint: Nobitex depth, volume, minimum notional, lot
   size, slippage, and impact remain unmeasured.
7. This is a **research convention**, not evidence that the venue can absorb the order.

### 8.3 Confirmation

- The owner explicitly selected and confirmed the `$2,500` fixed notional cap.
- The approval specified the exact rule, the USD notional unit, the 25%-of-equity translation, the
  research-leg scope, and the unverified venue-liquidity status.
- No value, formula, or scope in this entry was defaulted by the research agent.

---

## 9. Explicitly unresolved items carried forward

- **D-01:** **resolved** — `δ_R = 0.10R` and annual target `$250`/year; Gate 3 frequency feasibility
  remains untested.
- **D-02:** **resolved** — research-leg scope; maximum drawdown 15%; per-trade limit 1.00R; tail limit
  0.50R CVaR95; position-size limit `$2,500` fixed notional. Real-capital translation and venue
  liquidity evidence remain open.
- **D-04:** real-capital check remains open.
- **D-05:** Nobitex access and cost evidence remain open.
- **D-06:** the p95 rule cannot be applied until a Nobitex cost distribution exists.
- **D-07:** annual target is set via D-01b at `$250`/year; co-primary status unchanged.
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
