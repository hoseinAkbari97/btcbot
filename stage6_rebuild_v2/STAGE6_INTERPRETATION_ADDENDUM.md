# Stage 6 v1 — Interpretation Addendum

**Status:** Development-stage interpretation record. Documentation only.
**Applies to:** Stage 6 v1 Setup 1 accounting rebuild, accepted implementation `stage6_rebuild_v2/`.
**Freeze commit (documentation):** `5f735c0cab97076bee3f8d79687b9453bde9f91a`
**Accounting acceptance:** Stage 6A audit, `PASS WITH LIMITATIONS`.
**Execution proxy:** Binance BTCUSDT spot, long-only, no leverage. Not a Nobitex execution claim.

This addendum does not change any rule, artifact, or result. It records how the accepted
numbers must and must not be read. It does not authorize validation, out-of-sample analysis,
parameter tuning, or any live-trading conclusion.

**Evidence key.**
`[REP]` = `stage6_rebuild_v2/STAGE6_ACCOUNTING_REBUILD_V2.md`;
`[SUM]` = `stage6_rebuild_v2/stage6_v2_summary.json`;
`[PROTO]` = `stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md`;
`[PORT]` = `stage6_rebuild_v2/portfolio.py`;
`[ACC]` = `stage6_rebuild_v2/accounting.py`;
`[AUD]` = `stage6_acceptance_audit/STAGE6A_FINAL_ACCEPTANCE_AUDIT.md`;
`[AUJ]` = `stage6_acceptance_audit/acceptance_audit.json`.

---

## A. Signal-level result

The frozen barrier-only signal contains **101,789 resolved canonical trades**. The primary
same-bar tie convention is **stop-first**. Its gross expectancy is **-0.2227R**.

| quantity | value | source |
|---|---:|---|
| Resolved canonical trades | 101,789 | `[SUM].signal.n_resolved` |
| Stop-first gross expectancy | **-0.2227R** | `[SUM].signal.primary_stop_first.summary.mean` |
| Episode-cluster 95% CI | **-0.2290R to -0.2164R** | `[SUM].signal.primary_stop_first.bootstrap` |
| 14-day block 95% CI | **-0.2313R to -0.2142R** | `[SUM].signal.primary_stop_first.block_bootstrap` |
| Censored observations excluded | **1,769** | `[SUM].signal.n_censored_excluded` |
| Ambiguous same-bar ties | **24,998 / 101,789 (24.6%)** | `[SUM].signal.ambiguous_resolved` |
| Tie-win sensitivity | **+0.2685R** | `[SUM].signal.tie_win_sensitivity` |
| 50/50 tie-split sensitivity | **+0.0229R** | `[SUM].signal.tie_split_sensitivity` |

**Tie-win and 50/50 are sensitivities only.** They do not replace the predeclared stop-first
primary result. The primary result is negative under the convention recorded before the run
(`[PROTO]`, Decision 2A and Decision 3).

**The intrabar ordering is not established.** Five-minute OHLC cannot establish whether the
stop or the target was touched first inside a bar, nor the path between the open, high, low,
and close. The 24,998 ambiguous resolutions are therefore an irreducible measurement limit of
this dataset, not a modelling choice that can be resolved by re-reading the same candles. The
sign of the measured edge changes under the alternative tie convention, so the signal
conclusion should be stated as **negative under stop-first**, not as a convention-independent
negative edge.

---

## B. Portfolio capital exhaustion

| quantity | value | source |
|---|---:|---|
| Initial equity | **$10,000** | `[SUM].portfolios.primary.initial_capital` |
| Final residual equity | **$4.98** | `[SUM].portfolios.primary.final_equity` |
| Funded trades | **2,711** | `[SUM].portfolios.primary.n_taken` |
| Barrier-resolved funded trades | **2,566** | `[SUM].portfolios.primary.resolved_taken` |
| C1 time exits | **145** | `[SUM].portfolios.primary.time_exit_taken` |
| Last funded entry | **trade 10621 at `2021-06-19T12:55:00Z`** | `[AUJ].capital_timeline.last_funded_entry` |
| Permanent exhaustion | **`2021-06-19T13:04:59.999Z`** | `[AUJ].capital_timeline` |
| Later baseline-feasible candidates that could not be funded | **11,210 through 2024-06-30** | `[AUJ].capital_timeline.eligible_candidates_after_last_exit` |

**$4.98 is a minimum-order floor residual, not a meaningful return estimate.** The last funded
entry bought a $5.000394 notional on $5.006893 cash, because the $5 minimum notional plus fee
was the smallest admissible order. It exited for $4.982039, leaving cash below the next entry
floor. The exact cents therefore reflect the last tiny order and the exchange minimum, not a
continuous compounding path. The economically meaningful fact is that approximately 99.95% of
capital was destroyed within roughly six months; the residual is an artifact of the order
minimum.

**The portfolio did not halt explicitly.** There is no halt flag, no forced end-of-window exit,
and no rule that stops the event loop when equity becomes small. The portfolio **continued
evaluating candidates through 2024-06-30**; every later eligible candidate was rejected by the
minimum-order/cash-cap logic in sizing (`[PORT]` lifecycle; `[ACC]` minimum-order check;
`[AUJ].capital_timeline.explicit_halt_flag_present = false`). The de facto stop is therefore
**economic infeasibility**, not a documented halt. This distinction matters: the portfolio's
"end time" is the last candidate scanned, not the last moment it could trade.

---

## C. Exposure and risk interpretation

| quantity | value | source |
|---|---:|---|
| Entries where the spot cash cap bound | **2,559 / 2,711 (94.4%)** | `[AUJ].chronology_and_reconciliation.execution_profile` |
| Median actual / requested risk | **0.398** | same |
| Entries using less than half the nominal 1% risk | **1,864** | same |

Sizing takes the minimum of the 1%-of-equity risk size and the cash-funded size, then floors to
the lot step (`[ACC]`; `[PORT]`). When the cash cap binds, the position is smaller than the
nominal 1% risk budget, often much smaller.

**The nominal 1% risk figure does not describe actual portfolio exposure.** The median entry
used only **39.8%** of the requested risk, and 1,864 entries used less than half. Because the
cash cap binds on 94.4% of entries, the strategy is effectively an **all-in spot** strategy
whose realised risk per trade is governed by available cash, not by a stable 1% budget. Any
statement that the portfolio "risked 1% per trade" is incorrect for this implementation.

---

## D. Same-bar portfolio ambiguity

| quantity | value | source |
|---|---:|---|
| Same-bar round trips (`entry_index == exit_index`) | **1,041 / 2,711 (38.4%)** | `[AUJ].chronology_and_reconciliation.execution_profile` |
| Combined net P&L of those trades | **-$5,658.28** | same |
| Share of total net loss | **56.6%** | same |
| Mix | 485 stops, 465 targets, 91 stop-first ties | same |

**Five-minute OHLC cannot establish the intrabar path.** A trade that enters and exits inside
the same five-minute bar is decided by an ordering the available data does not observe. The
model applies the frozen exit reference and the adverse fill concession, but it cannot verify
that the stop or target would have been reached first, or that a target touch would have
filled. Because same-bar trades account for more than half of the net loss, the portfolio
magnitude inherits this limitation directly.

---

## E. Cost sensitivity

All **ten** cost-scenario summaries satisfy their accounting identities:

- `final_equity = initial_capital + net_pnl`;
- `total_cost = gross_pnl - net_pnl`;
- `total_cost = fees + spread_slippage`;
- `n_taken + skipped = n_canonical_trades`.

The multiplier scales both the fee rate and the adverse spread/slippage rate (`[PORT]`
`_rates`). The two universes are not interchangeable:

- **Fixed-universe scenarios retain baseline eligibility, not the same executed trade set.**
  Membership fixes the 14,978 baseline-feasible candidates. Costs still change fills, cash,
  sizing, and therefore which candidates are actually funded and when capital dies.
- **Re-filtered scenarios reapply feasibility at each cost.** The feasible set changes with
  the cost level, so the candidate population is not held constant.

**No per-scenario trade ledgers are retained.** Only the primary ledger is written. The ten
scenario identities can be checked at summary level, but per-scenario chronology, selection,
and cash paths cannot be reconstructed from the accepted artifacts.

**Aggregate fees need not scale linearly with the cost multiplier.** Higher costs can
accelerate capital exhaustion, which reduces the number of funded trades and therefore the
cumulative fees actually paid. The 3x scenarios do not pay three times the 1x fees; they pay
fees on a much smaller surviving trade count. For this reason, and because the final balances
are floor residuals, **do not rank scenarios by final equity**. The scenario table is an
accounting-identity check, not a performance league table.

---

## F. Annualization

| quantity | value | source |
|---|---:|---|
| Full-window CAGR | **-88.66%** | `[SUM].portfolios.primary.cagr` |
| Full-window length used by CAGR | **~1,276 days** | `[PORT]` `_summarize` |
| Active trading duration | **~169.4 days** | first entry to last exit; `[AUJ]` |
| Active-period annualization | **~-99.999992%** | `[AUJ].evidence.interpretation` |
| Time in market | **1.677%** of the full **1,277-day** window | `[SUM].portfolios.primary.time_in_market` |
| Daily rows with an open position | **18 / 1,277** | `[AUJ].evidence.interpretation` |

The reported **-88.66%** is arithmetically correct for the full-window denominator, but that
window extends long after the portfolio stopped trading. The active-period figure is
**approximately -99.999992%**. The `time_in_market` denominator is also the full window; it is
not the fraction of the active period during which a position was open.

**Neither CAGR figure should be presented as a normal live-trading performance estimate.**
They describe a path that destroyed essentially all capital and then ceased to be fundable.
The full-window number understates the speed of the loss; the active-period number is an
extreme annualization of a short, terminal path. Both are diagnostic, not forecast.

---

## G. Statistical limitations

- The reported **total net P&L cluster interval of -$11,852.20 to -$8,161.71** is **not a
  live-portfolio risk interval** (`[SUM].portfolio_bootstrap.net_pnl_total`; `[AUD]` MF-08).
- The interval **extends below the initial capital** of $10,000. A feasible cash-constrained
  portfolio cannot lose more than its capital, so the lower bound cannot describe an actual
  capital path. It is a path-independent resampling of realised trade P&L, not a re-simulation
  of capital allocation.
- The **funded subset's gross R is -0.0665**, versus **-0.2227** for the full resolved signal
  (`[AUJ].statistical_interpretation.funded_subset_selection`). The feasibility filter selects
  a materially less negative subpopulation than the full signal. Portfolio results are
  therefore **not** a direct application of the signal expectancy to a representative sample;
  costs then convert the funded gross edge into the large net loss.

These are interpretation limits, not accounting errors. The accounting identities are
verified; the inferential claims must be limited accordingly.

---

## H. Execution limitations

- **Venue proxy:** the execution model is a **Binance BTCUSDT spot** proxy, long-only, no
  leverage. It **does not establish Nobitex execution performance** (`[REP]`; `[PROTO]`).
  Nobitex fees, tick/lot/min-notional rules, liquidity, latency, outages, and order-book impact
  are not modelled or validated.
- **Target touch versus actual limit fill:** the model books a target touch at the target
  reference less adverse concession and tick-down. It does not model queue position, partial
  fills, or touch-and-reverse. This is optimistic relative to a real resting limit order.
- **Gap and stop behaviour:** gap-through exits use the frozen ledger bar-open reference, with
  adverse concession and tick-down. The ledger price is not clamped or rewritten. The
  five-minute bar cannot establish the intrabar fill path around the gap.
- **Slippage, spread, and fees:** 0.1% fee per side and 3 bps adverse per side (2 bps spread +
  1 bps slippage) are frozen assumptions, not venue measurements. They are scaled by the cost
  scenarios but are not calibrated to Nobitex or to realised account tiers.
- **Same-candle ambiguity:** the primary result uses stop-first for same-bar stop/target ties;
  24.6% of resolved trades are ambiguous. Alternative conventions are sensitivities only.
- **Within-bar event ordering:** entries are processed before exits within a bar. Entries use
  the bar open and exits occur later in the bar, so this is the implemented chronology. It
  should be stated explicitly in any downstream description because it determines the cash
  available to same-bar entries. It is documented here and in the Stage 6A audit (MF-10).

---

## Interpretation boundary

This addendum does **not** authorize:

- validation or out-of-sample inspection;
- parameter tuning or a claim that any parameter change is a validated improvement;
- a Nobitex execution or profitability claim;
- ranking the ten cost scenarios by final equity;
- presenting -88.66% CAGR, -99.999992% active CAGR, or $4.98 as a normal performance estimate.

**Validation and out-of-sample performance have not been inspected or authorized.**
