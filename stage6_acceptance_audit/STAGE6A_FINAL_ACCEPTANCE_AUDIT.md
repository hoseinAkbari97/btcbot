# Stage 6A — Final Acceptance Audit (Read-Only)

**Audit date:** 2026-11-01
**Repository:** `/home/hakbari/projects/btcbot`
**HEAD:** `2283135dfdcb49e4331f484da2370f4f4f505175` — `research: finalize Stage 6 v1 Setup 1 accounting (v2)`
**Accepted implementation:** `stage6_rebuild_v2/`
**Unapproved draft:** `stage6_rebuild/` (not modified, not used)

**Verdict: PASS WITH LIMITATIONS**

The Stage 6 v1 accounting is internally consistent and independently reproducible. No
accounting defect, negative-cash/equity violation, count error, or cost-identity failure was
found. The verdict is not a clean PASS because several material interpretation and
documentation gaps remain: the report does not disclose that trading effectively ends on
2021-06-19, that the final ~$5 is a minimum-order residual, or that CAGR and time-in-market
are computed over the full evaluation window rather than the 169-day active period. It also
does not quantify that 38.4% of funded trades are same-bar round trips and 94.4% of entries
are spot-cash-cap bound.

**Evidence key.** `R` = `stage6_rebuild_v2/STAGE6_ACCOUNTING_REBUILD_V2.md`; `P` =
`stage6_rebuild_v2/portfolio.py`; `A` = `stage6_rebuild_v2/accounting.py`; `FS` =
`stage6_rebuild_v2/frozen_signal.py`; `C` = `stage6_rebuild_v2/canonical.py`; `S` =
`stage6_rebuild_v2/stage6_v2_summary.json`; `I` =
`stage6_acceptance_audit/independent_portfolio_audit.json`. Line numbers refer to the
audited files at HEAD.

---

## 1. Executive verdict

### 1.1 Acceptance-criteria scorecard

| criterion | status | basis |
|---|---|---|
| No unexplained accounting discrepancies | **PASS** | Every primary row and every recorded cash field reconstructs independently; totals match `S.portfolios.primary` to <1e-6 (`I.totals`, 46/46 checks). |
| No negative cash/equity violations | **PASS** | No negative cash or equity in 2,711 ledger rows or 1,277 daily rows; overdraft is a hard abort at `P:401-402`. |
| Correct portfolio trade counts and censoring treatment | **PASS** | 2,711 = 2,566 resolved + 145 C1 time exits; 1,769 censored all C1-valid, 0 invalid; time-stop CSV matches field-for-field. |
| Correct cost-scenario implementation | **PASS WITH LIMITATION** | All ten scenario identities hold; multiplier contract verified at `P:60-61`; fixed/re-filtered universes behave as documented. Per-scenario ledgers are not retained. |
| Reproducible final portfolio reconciliation | **PASS** | Independent final cash 4.982039008899883 vs reported 4.982039008876792 (difference 2.3e-11), and every generated-artifact hash read by the audit matches `determinism_check.json`. |
| No material misrepresentation of execution/statistical assumptions | **PASS WITH LIMITATIONS** | Proxy, 5m OHLC, tie, and bootstrap limits are disclosed; terminal exhaustion, CAGR window, floor residual, same-bar share, and cash-cap share are not. |

### 1.2 Critical findings

**None.** No finding invalidates the published accounting or requires a rerun of the
pipeline. There are no unexplained discrepancies, no duplicated trades, no invalid censored
rows in the portfolio, no negative balances, and no scenario identity failure.

### 1.3 Material findings

| ID | finding | effect on acceptance |
|---|---|---|
| MF-01 | Terminal capital exhaustion and the effective end of trading on 2021-06-19 are not disclosed. | Interpretation, not accounting. |
| MF-02 | Final equity is a minimum-order floor residual; scenario final equities are not performance rankings. | Interpretation. |
| MF-03 | CAGR and time-in-market denominators are undocumented; CAGR annualises ~1,276 days while trading lasted 169.4 days. | Material interpretation. |
| MF-04 | 1,041/2,711 funded trades (38.4%) are same-bar round trips; 5m OHLC cannot establish their intrabar path. | Material execution-model limitation. |
| MF-05 | 2,559/2,711 entries (94.4%) are spot-cash-cap bound; the nominal 1% risk is usually not achieved. | Material interpretation. |
| MF-06 | Scenario trade ledgers are absent; the fixed universe holds eligibility, not the executed trade set. | Material verification limitation. |
| MF-07 | The signal sign flips between stop-first (-0.2227R) and tie-win (+0.2685R); 24.6% of resolved trades are ambiguous. | Material robustness limitation. |
| MF-08 | The total net P&L cluster interval extends below total capital (-$11,852 on $10,000) and is not a live-portfolio risk interval. | Statistical interpretation. |
| MF-09 | Costs ($9,174) are ~11.2x the gross loss ($821); the funded subset's gross R (-0.066) differs from the full signal (-0.223). | Material interpretation. |
| MF-10 | Same-bar event ordering is deterministic but not documented. | Documentation only; empirically immaterial. |

### 1.4 Why not PASS, why not FAIL

- **Not PASS:** the report omits disclosures that are required to read the headline numbers
  correctly, above all the fact that the strategy stops trading on 2021-06-19. The reported
  CAGR of -88.66% is arithmetically correct for its window but describes a portfolio that no
  longer trades for the final three years.
- **Not FAIL:** the accounting, capital constraints, trade counts, censoring treatment,
  cost-scenario identities, and independent reconciliation all pass. The defects are
  interpretive and documentary, not fabricated or broken results. The implementation does
  what the protocol says it does.

---

## 2. Capital exhaustion analysis

### 2.1 What the portfolio does near zero

The portfolio is re-sized on every entry from **current bar-open equity and current cash**
(`P:356-372`, `A:85-122`). Sizing is the minimum of the 1%-of-equity risk size and the cash
size, floored to the lot step:

```
size_at_risk = equity * 0.01 / (entry_fill - stop_exec)
size_at_cash = cash / (entry_fill * (1 + fee_rate))
size = floor_lot(min(size_at_risk, size_at_cash))
```

(`A:105-108`). The entry is rejected if `size < LOT` or `notional < $5`
(`A:122`, `P:371-372`). If several positions are desired on one bar, a cash scale is applied
and rechecked against lot/notional (`P:387-398`). An entry that would overdraw cash is a hard
abort (`P:401-402`). There is **no explicit halt state**; the loop continues to the end of the
development window and skips every unfundable candidate through the minimum-order path.

### 2.2 The exact capital events

These are four distinct events and must not be conflated:

| event | exact time | trade | evidence |
|---|---|---|---|
| First **capital-constrained candidate** (funded at reduced size) | `2021-01-01T02:50:00+00:00` | 0 | Risk-sized notional $35,973.08 vs $10,000 cash; actual notional $9,989.85; `spot_cap_binds=true` (`I.capital_timeline.first_entry`). |
| First **minimum-notional/lot rejection** (transient) | `2021-01-01T07:20:00+00:00` | 6 | Cash $0.056573 was reserved in open trade 5; size floors to 0, failing both lot and $5 notional (`I.capital_timeline.first_min_order_rejection`). |
| First candidate unfunded **after the last funded entry, while the last position is still open** | `2021-06-19T13:00:00+00:00` | 10622 | Cash at bar open $0.001499; position 10621 still open; size floors to 0. |
| **Permanent exhaustion after the last liquidation** | `2021-06-19T13:04:59.999000+00:00` | — | Trade 10621 exits, cash becomes $4.982039. |
| First eligible candidate **after permanent exhaustion** | `2021-06-19T14:05:00+00:00` | 10624 | 11,210 baseline-feasible candidates follow through 2024-06-30; none can be funded. |
| **Explicit halt** | — | — | None. |
| **Final equity** | `2024-06-30T20:35:00+00:00` (last evaluation bar) | — | $4.982039008876792; no open positions. |

The last funded entry is trade 10621 at `2021-06-19T12:55:00+00:00`. It buys a $5.000394
notional on $5.006893 cash, paying the $5.005394 entry cost, and exits at
`2021-06-19T13:04:59.999` for $4.982039. That is the final balance
(`I.capital_timeline.last_funded_entry`; `I.totals.final_equity`).

### 2.3 The eight required checks

| check | result | evidence |
|---|---|---|
| Is sizing recalculated using current equity? | **Yes** | `equity_open` is recomputed at each bar from cash plus marked open positions (`P:356-360`), then passed to `size_position` (`P:362`). |
| Are cash constraints enforced before every entry? | **Yes** | Cash cap in `A:107-108`; per-entry overdraft abort in `P:401-402`; independent cash chain matches every entry and exit field. |
| Can positions open with insufficient equity/cash? | **No** | `size_position` returns zero size when equity/cash ≤ 0 (`A:95-96`); minimum-order check rejects below-lot/below-$5 (`A:122`). |
| Are minimum notional and lot size enforced consistently? | **Yes** | `meets_min_order` at sizing (`A:122`) and recheck after cash scaling (`P:396-398`); no funded row violates lot or notional. |
| Does the portfolio stop opening trades when constraints cannot be met? | **Yes, de facto** | No halt flag; after 2021-06-19 every eligible candidate fails `meets_min_order`. 11,210 later candidates are skipped this way. |
| Any trade causing negative cash or negative equity? | **No** | 2,711 rows and 1,277 daily rows all non-negative; cash chain has zero errors (`I.checks.all_entries_cash_funded`). |
| Are open positions handled correctly at the end? | **Yes** | No forced end exit; a hard abort fires if any position remains (`P:521-524`); zero remain. |
| Is $4.98 valid or an artifact? | **Valid under the implemented rules** | It is residual cash after the last permitted liquidation, not a rounding or accounting defect. |

### 2.4 Decomposition of the 14,978 baseline-feasible candidates

| disposition | count | evidence |
|---|---:|---|
| Taken (funded) | 2,711 | `S.portfolios.primary.n_taken` |
| Skipped by minimum order before the terminal exit | 1,057 | `12,267 − 11,210` |
| Skipped by minimum order after the terminal exit | 11,210 | `I.capital_timeline.eligible_candidates_after_last_exit` |
| **Total baseline-feasible** | **14,978** | Independently rederived from `canonical_trades.jsonl.gz` (`I.counts.baseline_feasible`) |

The other 88,580 candidates are not baseline-feasible because round-trip cost exceeds 1R
(`S.portfolios.primary.skipped.cost_exceeds_1R`). The 11,210 post-exit skips are not a
separate rejection rule; they are all minimum-order rejections caused by cash below the
$5.005 entry floor. The portfolio is not "paused"; it is economically unable to trade.

### 2.5 Is the final $4.98 meaningful?

The **number is valid**; the **interpretation is not**. The exact cents are a floor residual:
the last trade had to clear a $5 notional, consumed almost all remaining cash, and left
$4.982039 after its loss. If that last trade had won, the residual would have been slightly
above $5 and a few more tiny trades might have occurred. The structurally meaningful fact is
that **the portfolio destroyed ~99.95% of capital within 169 days and then stopped trading**,
not that it earned a -88.66% annual return for 3.5 years.

---

## 3. Portfolio chronology and accounting reconciliation

### 3.1 Ordering and timestamp semantics

- Canonical entries are **next-bar-open**: `entry_index = confirmation_index + 1` for all
  103,558 canonical trades (`backend/app/services/research/outcomes.py:141`
  `ENTRY_OFFSET = 1`; `setup1.py:304`; independently verified in `I.checks.no_lookahead_entry_after_confirmation`).
- The portfolio is processed bar by bar from the first candidate entry to the last candidate
  exit (`P:355`). Within a bar, **entries are sized and booked before exits** (`P:355-470`),
  which is the correct chronology because entries use the bar open and exits occur later in
  the bar.
- Result rows are appended when the exit is processed, so
  `primary_portfolio_trades.csv` is ordered by `exit_index`; the 2,711 rows are correctly
  sorted and all have `entry_index <= exit_index` (`I.checks.rows_sorted_by_exit_index`,
  `I.checks.entry_not_after_exit`).
- No bar has more than one entry. Eight bars contain an entry at the open plus a different
  position exiting later in that bar; production correctly does **not** credit same-bar exit
  proceeds at the open (five entries would be larger under that look-ahead convention)
  (`I.evidence.execution_profile`). This ordering is deterministic but is not stated in the
  protocol or report (MF-10).

### 3.2 Cash reservation and concurrent positions

Cash is reserved at entry (`cash -= notional + entry_fee`, `P:404`) and released at exit
(`cash += proceeds − exit_fee`, `P:446-448`). The independent Decimal replay reproduces every
recorded `cash_before_entry`, `cash_after_entry`, `cash_before_exit`, and `cash_after_exit`
field with zero errors (`I.checks.cash_chain_reconstructs_every_recorded_cash_field`). The
maximum concurrent position count in the primary run is **2**; the first two-position moment
is the pair 25/26 on 2021-01-01, with notionals $9,778.61 and $103.90 and residual cash
$0.1546. Some cost scenarios reach 3 concurrent positions (`S.portfolios.*.max_concurrent`).

### 3.3 Row reconciliation: 2,711 = 2,566 + 145

| check | result | evidence |
|---|---|---|
| Unique trade IDs | 2,711 | `I.checks.trade_ids_unique` |
| Barrier-resolved rows | 2,566 | `I.counts.resolved_trades` |
| C1-valid time exits | 145 | `I.counts.time_exit_trades` |
| Duplicate trades | 0 | ID uniqueness |
| Invalid censored rows in portfolio | 0 | All time exits are C1-valid; `I.checks.time_rows_exit_index_is_entry_plus_11` |
| `time_stop_trades.csv` vs primary time rows | exact field-level match, 145/145 | `I.checks.time_stop_csv_field_level_match` |
| Exit-reason partition | stop 1,271; stop-first tie 111; target 1,184; time stop 145 | `I.checks.exit_reason_partition` |

The 1,769 censored canonical trades are **all** C1-valid and **none** is invalid
(`I.counts.canonical_censored_valid=1769`, `canonical_censored_invalid=0`). All 1,769 are
excluded from the frozen signal; 145 of them are funded and receive the separately named
time-stop exit. No censored row is silently converted into a barrier outcome.

### 3.4 Fees, spread, slippage, tick, gross and net reconcile

For every row the independent script recomputes:

```
entry_fill   = ceil_tick(entry_raw * 1.0003)
exit_fill    = floor_tick(exit_raw * 0.9997)
notional     = size * entry_fill
entry_fee    = notional * 0.001
exit_fee     = (exit_fill * size) * 0.001
gross_pnl    = (exit_raw − entry_raw) * size
net_pnl      = exit_fill*size − exit_fee − (notional + entry_fee)
total_cost   = gross_pnl − net_pnl = fees + spread_slippage
```

All identities hold with Decimal arithmetic (`I.checks.per_trade_accounting_reconciles`,
`I.checks.total_cost_equals_fees_plus_spread`). Totals:

| quantity | independent reconstruction | reported (`S.portfolios.primary`) |
|---|---:|---:|
| Gross P&L | -$821.376033000 | -$821.376033000 |
| Fees | $7,055.906353091 | $7,055.906353091 |
| Spread + slippage | $2,117.735574900 | $2,117.735574900 |
| Total cost | $9,173.641927991 | $9,173.641927991 |
| Net P&L | -$9,995.017960991 | -$9,995.017960991 |
| Final equity | $4.982039008900 | $4.982039008877 |

The 2.3e-11 final-equity difference comes from summing recorded floating-point net P&L in
Decimal rather than replaying the final float cash assignment; it is not an accounting
discrepancy. The direct cash-chain replay gives exactly the recorded final cash.

### 3.5 Daily equity and end of window

`daily_equity.csv` has 1,277 rows from 2021-01-01 to 2024-06-30. The final daily equity equals
the cash-chain final equity, no daily cash or equity is negative, and the curve is flat from
2021-06-19 to 2024-06-30 (`I.checks.equity_flat_after_last_exit`). There are no open positions
at the end (`I.checks.no_open_positions_at_end`), and no forced end-of-window exit was used
(`P:521-524`).

### 3.6 Execution profile that matters for chronology

| metric | value | evidence |
|---|---:|---|
| Same-bar round trips (`entry_index == exit_index`) | 1,041 / 2,711 (38.40%) | `I.evidence.execution_profile` |
| Same-bar share of resolved trades | 1,041 / 2,566 (40.57%) | same |
| Same-bar net P&L | -$5,658.28 (56.6% of total net loss) | same |
| Same-bar mix | 485 stops, 465 targets, 91 stop-first ties | same |
| Median holding time | 10.0 minutes (max 60.0) | same |
| Spot-cap-bound entries | 2,559 / 2,711 (94.39%) | same |
| Median actual / requested risk | 0.398 | same |
| Entries below half the nominal 1% risk | 1,864 / 2,711 (68.8%) | same |

The same-bar share is the single most important execution fact the report does not quantify.
It means 38% of the portfolio's outcomes are decided inside one 5-minute candle, where the
available OHLC cannot establish whether the stop or the target was touched first, or whether a
target touch would actually have filled.

---

## 4. Cost sensitivity audit

### 4.1 What the multiplier does

`_rates(cost_scale)` returns `FEE_RATE * cost_scale` and `ADVERSE_RATE * cost_scale`
(`P:60-61`). The multiplier therefore scales **both** the 0.1% fee and the 3 bps adverse
(spread + slippage) component. It is **not** a fee-only multiplier. Entry and exit fees are
charged on notional/proceeds; adverse is embedded in the fill prices. The per-row algebra
proves there is no double counting:

```
gross − net = (entry_fill − entry_raw)·size + (exit_raw − exit_fill)·size + fees
```

(`P:449-453`; verified on all 2,711 primary rows). Costs are applied once per side, not twice.

### 4.2 Fixed versus re-filtered universes

- **Re-filtered:** `allowed_ids=None`; `assess_trade` is rerun at the scenario cost and the
  feasibility envelope is reapplied (`P:273-286`; `rebuild_setup1_accounting.py:565-575`).
  The candidate ledger stays at 103,558; the feasible set varies from 1,140 to 36,485.
- **Fixed primary universe:** `allowed_ids=baseline feasible_ids`; the 14,978 baseline-feasible
  candidates are held constant and **not** re-filtered at the new cost (`P:270-272`,
  `P:283-286`; `rebuild_setup1_accounting.py:583-590`). Membership already encodes the
  baseline decision.
- The **1x re-filtered scenario is an alias** of the primary summary object
  (`rebuild_setup1_accounting.py:567-568`), so its exact equality is by construction, not an
  independent rerun. The fixed 1x scenario is a separate run and independently reproduces the
  primary totals, which is a meaningful check.

### 4.3 All ten scenarios

| scenario | universe | scale | candidates | feasible | taken | final equity | fees | spread | total cost | identities |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| primary | re-filtered | 1.0 | 103,558 | 14,978 | 2,711 | $4.982039 | $7,055.91 | $2,117.74 | $9,173.64 | pass |
| 0.5x | re-filtered | 0.5 | 103,558 | 36,485 | 5,105 | $4.999641 | $6,479.20 | $1,945.50 | $8,424.70 | pass |
| 1.0x | re-filtered | 1.0 | 103,558 | 14,978 | 2,711 | $4.982039 | $7,055.91 | $2,117.74 | $9,173.64 | pass |
| 1.5x | re-filtered | 1.5 | 103,558 | 6,719 | 1,926 | $4.987129 | $7,429.06 | $2,229.39 | $9,658.46 | pass |
| 2.0x | re-filtered | 2.0 | 103,558 | 3,326 | 1,451 | $5.001637 | $7,218.80 | $2,166.11 | $9,384.91 | pass |
| 3.0x | re-filtered | 3.0 | 103,558 | 1,140 | 1,054 | $5.082277 | $7,255.81 | $2,177.06 | $9,432.88 | pass |
| 0.5x | fixed | 0.5 | 14,978 | 14,978 | 5,060 | $4.984938 | $6,359.64 | $1,909.54 | $8,269.19 | pass |
| 1.0x | fixed | 1.0 | 14,978 | 14,978 | 2,711 | $4.982039 | $7,055.91 | $2,117.74 | $9,173.64 | pass |
| 1.5x | fixed | 1.5 | 14,978 | 14,978 | 1,885 | $4.999015 | $7,336.07 | $2,201.50 | $9,537.56 | pass |
| 2.0x | fixed | 2.0 | 14,978 | 14,978 | 1,434 | $4.974134 | $7,476.13 | $2,243.34 | $9,719.47 | pass |
| 3.0x | fixed | 3.0 | 14,978 | 14,978 | 988 | $4.966314 | $7,600.99 | $2,280.66 | $9,881.64 | pass |

A notable consequence of the min-order floor: aggregate fees do **not** scale up with the
cost multiplier. Because higher costs accelerate capital death, the 3x scenarios take far
fewer trades and end with aggregate fees near the same order as 1x ($7,256 and $7,601, not
$21,000). Total cost is bounded by the capital that exists to pay it, so the cost scenarios
are not a clean comparison of "the same activity at a different price."

Every row satisfies `final_equity = initial + net`, `total_cost = gross − net`,
`total_cost = fees + spread`, and `taken + skipped = 103,558`
(`I.checks.all_scenario_identities_hold`). The fixed-universe candidate count is exactly
14,978 in all five fixed scenarios (`I.checks.fixed_universe_constant_candidate_count`).

### 4.4 Does changing costs change selection, sizing, and capital availability?

**Yes, all three.**

- **Selection:** taken trades range from 988 (3x fixed) to 5,105 (0.5x re-filtered). In the
  re-filtered universe the feasible set itself changes from 36,485 to 1,140.
- **Sizing and capital:** even the fixed universe holds only candidate **eligibility**
  constant. Costs change entry/exit fills, fees, the equity path, and therefore the cash cap
  on each entry. The executed trade set is not held constant: fixed-universe taken counts
  still vary 5,060 → 2,711 → 1,885 → 1,434 → 988. The fixed scenarios are therefore **not** a
  pure "same trades with more fees" experiment.
- **Capital availability:** higher costs make the portfolio die at a different moment. The 3x
  re-filtered scenario still has 31 trades in 2024, because it lost capital more slowly in
  trade-count terms and retained a tiny residual longer; the primary run is dead by
  2021-06-19 (`S.portfolios.*.years`).

### 4.5 Are all ten scenarios trustworthy?

**Summary-level: yes, with a material limitation.**

- The arithmetic identities are verified for all ten, and the multiplier contract is
  verified in code.
- The scenarios are **not** independently per-trade verifiable: only the primary trade ledger
  is written. There is no scenario `trades.csv`, so no scenario cash chain, selection trace,
  or chronology can be reconstructed from artifacts. The audit can confirm the summary
  identities and the code path, not the scenario ledgers themselves.
- The final-equity differences ($4.966 to $5.082) are **floor residuals, not a ranking**.
  A higher-cost scenario ending at $5.08 does not mean higher costs performed better; it means
  the last tiny $5 trade occurred on a slightly different path. This should be stated
  explicitly in any downstream use.

---

## 5. Execution-model limitation matrix

Classification: **A** = explicitly implemented and verified; **B** = implemented but based on
an unverified modelling assumption; **C** = not modelled or not established by the available
evidence.

| # | assumption | class | evidence / why |
|---:|---|---|---|
| 1 | Venue: Binance BTCUSDT spot, long-only, no leverage | **B** | Explicitly implemented and labelled as a proxy (`R:3`, `R:223`; `config.json`). It is not calibrated to Nobitex; the proxy assumption itself is unverified. |
| 2 | Entry fill: next bar open, 3 bps adverse, ceil tick | **B** | Mechanically verified on every row (`A:64-65`, `P:73-75`; `I.checks.per_trade_accounting_reconciles`). Realistic 5m-open fills are not established. |
| 3 | Stop execution and gap-through | **B** | Uses the frozen ledger exit reference (stop or gap-through bar open) plus adverse concession and tick-down (`R:16-27`; `P:288-295`, `P:323`). Mechanically verified; intrabar path is not. |
| 4 | Target touch versus actual limit fill | **B** | Target is booked at the target reference minus 3 bps and tick-down (`P:323`). A touch is assumed fillable; queue, partial fill, and touch-and-reverse are not modelled. This is optimistic. |
| 5 | Same-candle stop/target ambiguity | **B** | Predeclared stop-first (`R:24`; `FS:90`); `ambiguous` retained; tie-win/split are labelled sensitivities. 24,998/101,789 resolved trades (24.56%) are ambiguous. The true ordering is **C/not established**; the sign flips under tie-win. |
| 6 | Spread and slippage | **B** | 2 bps spread + 1 bps slippage per side (`A:24-26`), scaled by scenario. Frozen assumptions, not venue measurements. |
| 7 | Tick and lot rounding | **A** | TICK 0.01, LOT 0.00001 (`A:18-19`); ceil buys, floor sells, floor lot. Independently verified, including `size % LOT == 0`. |
| 8 | Minimum notional | **A** | $5 enforced at sizing (`A:122`) and after cash scaling (`P:396-398`). The Nobitex-specific minimum is **C/not established**. |
| 9 | Fees | **A** | 0.1% per side, scaled (`A:23`, `P:60-61`); entry fee on notional, exit fee on proceeds; per-row recomputation matches. Realised fee tier, rebates, and BNB discounts are not modelled (**B** for venue realism). |
| 10 | C1 time-stop execution | **A** | Named `time_stop_c1_valid_12th_close`; exit at the 12th candle close, only when C1-valid with all 12 candles present and no window gap; adverse concession and tick-down (`P:9-12`, `P:298-308`, `P:323`). 145 funded time exits; invalid censored rows receive no exit. |
| 11 | Open positions at end of window | **A** | Hard abort if any remain (`P:521-524`); zero remain; no forced end exit. |
| 12 | Data gaps and split boundaries | **A** | No synthetic candle; gap-crossing resolved windows rejected; censored rows with gaps/insufficient future bars receive no invented exit (`C:254-300`; `R:13`). |
| 13 | Intrabar fill realism from 5m OHLC | **C** | Not modelled. 38.4% of funded trades are same-bar round trips, 24.6% of resolved trades are same-bar ties. OHLC cannot resolve ordering or the fill path. |
| 14 | Nobitex-specific execution performance | **C** | Not established by any artifact. No Nobitex fees, tick/lot/min-notional, liquidity, latency, outages, or order-book impact are modelled or validated. |

**Explicit statement:** the Binance BTCUSDT spot proxy **does not establish actual Nobitex
execution performance**. The report says this at `R:3` and `R:223`; that statement is correct
and should be preserved. No Nobitex-specific behaviour should be inferred from these results.

---

## 6. Statistical interpretation audit

| requirement | status | evidence |
|---|---|---|
| Primary signal expectancy uses the frozen barrier-only definition | **PASS** | `FS:85-92` uses resolved trades only and stop-first; independent mean -0.222666471310813 matches reported -0.222666471310380 (`I.checks.independent_frozen_signal_mean_matches`). |
| Censored observations reported separately | **PASS** | 1,769 excluded, all C1-valid, 0 invalid (`S.signal`; `FS:85-88, 142-144`). |
| C1 time-stop results not silently merged into frozen signal expectancy | **PASS** | `S.signal.uses_time_stops=false`; time-stop contribution is a separate block with its own note (`S.portfolios.primary.time_exit_contribution`; `R:85-99`). |
| Episode-cluster confidence intervals interpreted correctly | **PASS** | Signal CI -0.2290 to -0.2164; portfolio net R CI -0.7275 to -0.6566; both labelled episode-cluster (`R:54-64`, `R:141-150`). |
| Block-bootstrap intervals not misrepresented as live portfolio risk intervals | **PASS WITH LIMITATION** | Report says they do not re-simulate capital allocation and defers path bootstrap to Stage 6b (`R:14`, `R:150`). **Limitation:** the total net P&L interval -$11,852 to -$8,162 extends below the $10,000 capital, which is infeasible in the actual portfolio; it must not be read as a live risk interval (MF-08). |
| Negative gross expectancy not confused with the more severe portfolio net loss | **PASS** | Signal gross -0.2227R, portfolio gross -$821.38, net -$9,995.02; the report distinguishes them (`R:54-64`, `R:75-83`). |
| CAGR interpreted with the capital-infeasibility disclosure | **FAIL (documentation)** | CAGR -88.66% (`R:79`) is annualised over ~1,276 days (`P:643-646`) while trading stops after 169.4 days. Active-period annualisation is approximately -99.999992%. The disclosure is absent (MF-03). |
| Tie-win and 50/50 remain sensitivities, not primary conclusions | **PASS** | Primary stop-first; tie-win/split labelled sensitivity (`R:54-64`; `FS:90-92`). **Caveat:** 24.6% ambiguous and a sign flip (-0.2227R vs +0.2685R), which the report does not emphasise (MF-07). |

### 6.1 Additional interpretation findings

**Cost dominance.** Gross P&L is -$821.38, while total costs are $9,173.64 (fees $7,055.91;
spread+slippage $2,117.74). Costs are ~11.2x the gross loss. The portfolio does not fail
because the directional edge is -0.22R applied to the funded set; it fails because costs are
large relative to the risk actually taken. The report shows the gross/net split but does not
explain this.

**Selection effect.** The funded subset's gross R (raw entry-to-stop denominator) is -0.0665
(n=2,711; -0.0772 on 2,566 resolved), versus -0.2227 for the full resolved signal. The
feasibility filter selects a materially different subpopulation, so the portfolio result is
**not** a direct application of the signal expectancy to a representative sample. The report
reports both numbers but does not discuss the selection.

**R denominators.** The signal R uses raw entry-to-stop distance; the portfolio R uses actual
fill-to-stop risk. The portfolio "mean net R" -0.6918 is therefore not directly comparable to
the signal "gross expectancy R" -0.2227. The report labels them differently, but a reader
could wrongly subtract them. The correct decomposition is: funded gross R ≈ -0.066, costs
consume ≈ 0.63R, leaving net R ≈ -0.692.

**Time in market.** `time_in_market=1.677%` (`P:698`) is the fraction of the full candidate
span (first entry bar to last candidate exit bar, ~1,276 days) with an open position. Only 18
of 1,277 daily rows have an open position. During the 169.4-day active period the portfolio
was in the market about 12.6% of bars and 95.4% invested when in market
(`S.portfolios.primary.avg_utilization_when_in_market`). The denominator should be stated.

---

## 7. Independent reconstruction results

The audit script `stage6_acceptance_audit/independent_portfolio_audit.py` does **not** import
any `stage6_rebuild_v2` module. It reads only the published artifacts and uses Decimal for
prices, cash, fees, and tick/lot work.

```
python stage6_acceptance_audit/independent_portfolio_audit.py \
    --repo-root . \
    --out stage6_acceptance_audit/independent_portfolio_audit.json
```

**Result: 46/46 checks pass** (`I.passed=true`, `I.failed_checks=[]`).

| reconstructed quantity | independent | reported | match |
|---|---:|---:|---|
| Final equity | $4.982039008900 | $4.982039008877 | yes (2.3e-11) |
| Gross P&L | -$821.376033000 | -$821.376033000 | yes |
| Fees | $7,055.906353091 | $7,055.906353091 | yes |
| Spread + slippage | $2,117.735574900 | $2,117.735574900 | yes |
| Total cost | $9,173.641927991 | $9,173.641927991 | yes |
| Net P&L | -$9,995.017960991 | -$9,995.017960991 | yes |
| Trades | 2,711 | 2,711 | yes |
| Resolved / time exits | 2,566 / 145 | 2,566 / 145 | yes |
| Baseline feasible | 14,978 | 14,978 | yes |
| Signal mean R | -0.222666471311 | -0.222666471310 | yes |

Additional independent checks include:

- per-row notional, entry/exit fee, gross/net/total-cost/fees/spread identities;
- independent re-sizing from recorded pre-entry equity and cash, including `spot_cap_binds`;
- full cash-chain replay with every recorded cash field;
- 1,277-row daily curve and final-equity match;
- exact C1 time-stop CSV field match;
- 103,558-row canonical scan: `entry_index = confirmation_index + 1` on every row;
- baseline feasibility rederived from the canonical ledger (14,978);
- all ten cost-scenario identities;
- independent frozen-signal mean.

**Limitations of the independent reconstruction:**

1. Scenario trade ledgers are not retained, so scenario cash chains and per-trade selection
   cannot be reconstructed; only summary identities and the code contract are checked.
2. The 2.5 GB observation ledger is not rebuilt; upstream canonical construction is taken as
   given, though its row counts and entry/confirmation relation are checked.
3. The audit does not rerun the bootstraps; it reads their reported intervals and checks
   their labels and feasibility bounds.

---

## 8. Unresolved limitations and risks

| risk | severity | detail |
|---|---|---|
| Intrabar path/fill ambiguity | **High for interpretation** | 38.4% same-bar round trips; 24.6% ambiguous ties; the signal sign flips between stop-first and tie-win. Not recoverable from 5m OHLC. |
| Nobitex transfer | **High for any live conclusion** | Binance spot is a proxy; no Nobitex execution, liquidity, fees, tick/lot/min-notional, latency, or outage evidence. |
| Cost/slippage constants | **Material** | 2 bps spread + 1 bps slippage and 0.1% fees are frozen assumptions, not venue measurements. |
| Path-dependent capital exhaustion | **Material** | Final equity and CAGR are dominated by the $5 floor and the early death of the portfolio; they are not a continuous return series. |
| Scenario ledgers absent | **Material** | Per-scenario chronology and selection cannot be audited from artifacts. |
| No portfolio path bootstrap | **Material** | Reported intervals resample trade statistics; path-dependent risk is deferred to Stage 6b. |
| Funded-subset selection | **Material** | The feasibility filter changes the gross edge from -0.223R (signal) to -0.066R (funded); portfolio results are not a representative application of the signal. |
| Tie-convention dependence | **Material** | The primary conclusion's sign depends on an unresolved intrabar fact; tie-win is not merely a numerical sensitivity. |

No risk in this table is an accounting defect. They are limits on what the accounting result
can be said to prove.

---

## 9. Recommendation: freeze Stage 6 v1 as the development baseline

**Yes — freeze the Stage 6 v1 accounting implementation and artifacts as the development
baseline, subject to the interpretation conditions below.** Stage 6 v1 is acceptable as the
development-stage baseline because its accounting is correct, its capital constraints are
enforced, its trade counts and censoring are right, and its totals are independently
reproducible. It is **not** acceptable as a performance estimate or as evidence of Nobitex
profitability.

Conditions for downstream use:

1. **Do not change the Stage 6 v1 rules during validation.** The implementation is frozen;
   the limitations travel with it.
2. **Add a short interpretation addendum** stating at minimum:
   - trading effectively ended `2021-06-19T13:04:59.999` after 169.4 days;
   - 11,210 later baseline-feasible candidates were unfunded;
   - the final ~$5 is the minimum-order residual, not a continuous return;
   - CAGR -88.66% annualises the full ~1,276-day window; active-period annualisation is
     approximately -99.999992%;
   - `time_in_market=1.677%` uses the full-window denominator; the active period is ~12.6%
     of bars and 95.4% invested when in market;
   - 1,041/2,711 funded trades (38.4%) are same-bar round trips;
   - 2,559/2,711 entries (94.4%) are spot-cash-cap bound;
   - scenario ledgers are not retained and scenario final equities are floor residuals.
3. **Do not describe -88.66% CAGR or $4.98 as a performance estimate.** Describe the result
   as capital destruction within roughly six months under the Binance spot proxy.
4. **Keep stop-first primary and tie-win/split as labelled sensitivities**, but state that
   the primary sign is not robust to intrabar ambiguity.
5. **Do not rank scenarios by final equity.** The $4.97–$5.08 spread is residual-path noise.
6. **Make no Nobitex execution claim.** The proxy is Binance spot.

**Do not proceed to validation/OOS.** This audit stops at development-stage acceptance.
Explicit authorization is required before any validation or out-of-sample work.

---

## Appendix A — Audit outputs and read-only confirmation

New files created (all under `stage6_acceptance_audit/`):

| file | purpose |
|---|---|
| `STAGE6A_FINAL_ACCEPTANCE_AUDIT.md` | this report |
| `acceptance_audit.json` | consolidated verdict, findings, criteria, scenario table, matrix |
| `independent_portfolio_audit.py` | independent Decimal reconstruction script |
| `independent_portfolio_audit.json` | 46-check evidence record |

Artifact integrity: `determinism_check.json` records a byte-identical repeated run over 10
generated artifacts. The audit read 7 of those generated artifacts and the SHA-256 of each
one matches its recorded hash (`I.artifact_hashes`; `determinism_check.json` `passed=true`).
The 8th audited file, `STAGE6_V2_PROTOCOL.md`, is a protocol document, not a generated
artifact. This confirms the audited result files are byte-identical to the accepted
deterministic run.

**Read-only confirmation:**

- `stage6_rebuild/` was not modified, read for results, or used. `git status` shows no
  changes there.
- `stage6_rebuild_v2/` was not modified. `git status` shows no tracked changes there, and all
  read artifacts match their determinism hashes.
- The only working-tree change is the new untracked `stage6_acceptance_audit/` directory.
- No accepted artifact, generated ledger, equity curve, summary, or report was overwritten.
- No pipeline, market-structure engine, bootstrap, canonical ledger, or portfolio was rerun.
- No validation or OOS artifact was inspected.

Commands used to verify:

```bash
git status --porcelain
git status --porcelain stage6_rebuild_v2 stage6_rebuild
python stage6_acceptance_audit/independent_portfolio_audit.py --repo-root . \
  --out stage6_acceptance_audit/independent_portfolio_audit.json
```

`git status --porcelain` at audit close:

```
?? stage6_acceptance_audit/
```

---

## Appendix B — Primary artifacts cited

| artifact | role |
|---|---|
| `stage6_rebuild_v2/portfolio.py` | event loop, sizing, cash reservation, exits, summary |
| `stage6_rebuild_v2/accounting.py` | tick/lot, fills, sizing, minimum order |
| `stage6_rebuild_v2/frozen_signal.py` | barrier-only signal and tie conventions |
| `stage6_rebuild_v2/canonical.py` | canonical identity, C1 validity, provenance |
| `stage6_rebuild_v2/rebuild_setup1_accounting.py` | primary run, feasibility, ten cost scenarios |
| `stage6_rebuild_v2/verification.py` | 31 built-in checks and 20-trade sample |
| `stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md` | approved protocol |
| `stage6_rebuild_v2/STAGE6_ACCOUNTING_REBUILD_V2.md` | report under audit |
| `stage6_rebuild_v2/stage6_v2_summary.json` | primary and scenario results |
| `stage6_rebuild_v2/primary_portfolio_trades.csv` | 2,711-row primary ledger |
| `stage6_rebuild_v2/time_stop_trades.csv` | 145-row time-exit subset |
| `stage6_rebuild_v2/daily_equity.csv` | 1,277-row daily curve |
| `stage6_rebuild_v2/canonical_trades.jsonl.gz` | 103,558 canonical trades |
| `stage6_rebuild_v2/verification_report.json` | 31/31 passed, 0 critical failures |
| `stage6_rebuild_v2/determinism_check.json` | byte-identical repeated run |
