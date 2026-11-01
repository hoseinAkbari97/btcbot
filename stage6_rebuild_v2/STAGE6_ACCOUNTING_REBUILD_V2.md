# Stage 6 v1 — approved Setup 1 accounting rebuild (v2)

Development data only (`2021-01-01T00:00:00Z` inclusive to `2024-07-01T00:00:00Z` exclusive). Historical execution proxy: **Binance BTCUSDT spot**, long-only, no leverage. This is not a Nobitex execution claim or integration.

The approved implementation lives in `stage6_rebuild_v2/`. The previous `stage6_rebuild/` draft and its outputs are untouched and unapproved.

## Protocol recorded before implementation

- **A. Frozen signal:** barrier-resolved trades only, stop-first same-bar ties, censored observations reported separately and never converted into resolved outcomes.
- **B. Executable portfolio:** frozen barrier exits for resolved trades; a C1-valid 12-candle no-barrier trade may exit at the twelfth candle's close under the explicitly named `time_stop_c1_valid_12th_close` policy.
- Data gaps, split boundaries and insufficient future data receive **no invented exit** and are excluded from the executable portfolio.
- Time-stop results are reported separately and are never combined with the frozen barrier-only signal expectancy.
- Cost scenarios: 0.5x, 1x, 1.5x, 2x and 3x, each for a re-filtered and a fixed primary trade universe.
- Portfolio path bootstrap is deferred to Stage 6b. The 14-day block bootstrap here resamples trade statistics only and does not re-simulate capital allocation.

## Exit-price semantics

| outcome | primary exit reference | treatment |
|---|---|---|
| Stop hit | Frozen ledger `exit_price`, normally the stop level; a gap-through uses the ledger's bar-open price (worse). | Adverse concession and tick-down; not clamped or rewritten. |
| Target hit | Frozen ledger `exit_price`, normally the +1R target; a gap-through uses the bar-open price (better). | Adverse concession and tick-down; not clamped or rewritten. |
| Same-bar tie | Stop-first, booked at the stop reference. | `ambiguous=true` retained; tie-win/split are labelled sensitivities only. |
| Gap through stop | Frozen bar-open price below the stop. | Used as recorded; more conservative than a stop-level fill. |
| Gap through target | Frozen bar-open price above the target. | Used as recorded; more favourable than a target-level fill. |
| Time stop | Close of the twelfth candle, only when C1-valid. | Adverse concession and tick-down; invalid windows receive no exit. |

Five-minute OHLC cannot establish realistic intrabar ordering or fills. That limitation is disclosed, not modelled. No alternative fill assumption is used in the primary result; any future alternative must be a separately named sensitivity.

## Data integrity and provenance

- Ledger rows read: **2,395,528**
- Canonical trades: **103,558**
- Resolved trades: **101,789**
- Censored trades: **1,769**
- Episodes: **22,982**
- Unique event indices: **103,558**
- Duplicate observations collapsed: **2,291,970**
- Censored with a valid C1 time exit: **1,769**
- Censored without an executable exit: **0**
- Sample span: `2021-01-01T02:50:00+00:00` to `2024-06-30T23:04:59.999000+00:00`

| provenance check | expected | actual | result |
|---|---:|---:|---|
| rows | 2,395,528 | 2,395,528 | pass |
| unique_entry_candles | 103,558 | 103,558 | pass |
| resolved_trades | 101,789 | 101,789 | pass |
| episodes | 22,982 | 22,982 | pass |
| unique_event_indices | 103,558 | 103,558 | pass |

All identity and accounting conflicts are hard aborts. The run records input SHA-256 hashes, configuration, code version and bootstrap seeds in `input_hashes.json`, `config.json`, `code_version.json` and the summary.

## A. Frozen barrier-only signal evaluation

Resolved canonical trades used: **101,789**. Censored observations excluded and reported separately: **1,769**. No time-stop return enters this section.

| tie convention | n | win rate | gross expectancy R | 95% CI | gross PF | total gross R |
|---|---:|---:|---:|---:|---:|---:|
| stop-first (primary) | 101,789 | 38.87% | -0.2227 | -0.2290 to -0.2164 | 0.636 | -22,665.0 |
| tie = win (sensitivity) | 101,789 | 63.43% | +0.2685 | +0.2624 to +0.2746 | 1.734 | +27,331.0 |
| 50/50 tie split (sensitivity) | 101,789 | 40.06% | +0.0229 | +0.0173 to +0.0286 | 1.063 | +2,333.0 |

Primary stop-first gross expectancy is **-0.2227R** (episode-cluster 95% CI -0.2290 to -0.2164). The 14-day block bootstrap CI is -0.2313 to -0.2142.

Diagnostic excluding every ambiguous same-bar resolution: n=76,791, win rate 51.52%, gross expectancy +0.0304R. This isolates the non-tie directional edge and is not a substitute for the primary result.

### Gross R by year (stop-first, resolved only)

| year | trades | resolved | censored | episodes | win rate | mean R | total R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 26,846 | 26,399 | 447 | 6,344 | 38.70% | -0.2260 | -5,965.0 |
| 2022 | 29,669 | 29,153 | 516 | 6,608 | 39.25% | -0.2150 | -6,267.0 |
| 2023 | 31,191 | 30,629 | 562 | 6,698 | 38.31% | -0.2339 | -7,163.0 |
| 2024 | 15,852 | 15,608 | 244 | 3,334 | 39.52% | -0.2095 | -3,270.0 |

## B. Executable spot portfolio (time stops separate)

Candidates: **103,558** canonical trades. Executable exits: **103,558**; no executable exit: **0**. Feasible under the predeclared cost envelope: **14,978**. Taken: **2,711**.

- Initial capital **$10,000.00**, final equity **$4.98**, total return **-99.95%**, CAGR **-88.66%**.
- Net P&L **-$9,995.02**; gross P&L **-$821.38**; fees **$7,055.91**; spread+slippage **$2,117.74**; total cost **$9,173.64**.
- Max drawdown **$10,003.94** (**99.95%**) from `2021-01-01T18:00:00+00:00` to `2021-06-19T13:00:00+00:00`; recovery `not reached`.
- Mean net R **-0.6918**, median **-1.1764**, win rate **39.14%**, profit factor **0.303**.
- Max concurrent positions **2**, max utilization **100.00%**, time in market **1.68%**.

### Time-stop contribution (separate from the frozen signal)

| quantity | value |
|---|---:|
| time-exited trades | 145 |
| net P&L from time exits | -$191.05 |
| gross P&L from time exits | $186.40 |
| fees from time exits | $290.32 |
| total net R from time exits | -36.8308 |
| mean net R per time exit | -0.2540 |
| share of portfolio trades | 5.35% |
| share of portfolio net P&L | +1.91% |
| share of portfolio gross P&L | -22.69% |

The time-stop contribution above belongs only to the executable portfolio. It is not added to, netted against, or used to restate the frozen barrier-only signal expectancy in section A.

### Exit mix and skips

| exit reason | trades |
|---|---:|
| stop | 1,271 |
| stop_tie_stop_first | 111 |
| target | 1,184 |
| time_stop_c1_valid_12th_close | 145 |

| skip reason | trades |
|---|---:|
| below_min_order_at_entry | 12,267 |
| cost_exceeds_1R | 88,580 |

### Yearly portfolio results

| year | trades | net P&L | gross P&L | win rate | mean R |
|---|---:|---:|---:|---:|---:|
| 2021 | 2,711 | -$9,995.02 | -$821.38 | 39.14% | -0.6918 |

## Cost scenarios

| scenario | universe | taken | final equity | total return | net P&L | mean R | PF | max DD | time exits |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| primary (1x re-filtered) | re-filtered | 2,711 | $4.98 | -99.95% | -$9,995.02 | -0.6918 | 0.303 | 99.95% | 145 |
| 0.5x re-filtered | re-filtered | 5,105 | $5.00 | -99.95% | -$9,995.00 | -0.5664 | 0.447 | 99.95% | 151 |
| 1x re-filtered | re-filtered | 2,711 | $4.98 | -99.95% | -$9,995.02 | -0.6918 | 0.303 | 99.95% | 145 |
| 1.5x re-filtered | re-filtered | 1,926 | $4.99 | -99.95% | -$9,995.01 | -0.7198 | 0.220 | 99.95% | 161 |
| 2x re-filtered | re-filtered | 1,451 | $5.00 | -99.95% | -$9,995.00 | -0.7610 | 0.169 | 99.95% | 205 |
| 3x re-filtered | re-filtered | 1,054 | $5.08 | -99.95% | -$9,994.92 | -0.7904 | 0.104 | 99.95% | 271 |
| 0.5x fixed primary universe | fixed | 5,060 | $4.98 | -99.95% | -$9,995.02 | -0.3911 | 0.514 | 99.95% | 296 |
| 1x fixed primary universe | fixed | 2,711 | $4.98 | -99.95% | -$9,995.02 | -0.6918 | 0.303 | 99.95% | 145 |
| 1.5x fixed primary universe | fixed | 1,885 | $5.00 | -99.95% | -$9,995.00 | -0.9562 | 0.174 | 99.95% | 104 |
| 2x fixed primary universe | fixed | 1,434 | $4.97 | -99.95% | -$9,995.03 | -1.1730 | 0.104 | 99.95% | 69 |
| 3x fixed primary universe | fixed | 988 | $4.97 | -99.95% | -$9,995.03 | -1.5956 | 0.041 | 99.95% | 50 |

The fixed-universe rows hold the baseline feasible trade set constant while changing execution costs; the re-filtered rows apply the predeclared feasibility envelope at each cost level.

## Dependence-aware trade intervals

| statistic | estimate | interval |
|---|---:|---:|
| net R per taken trade (episode cluster) | -0.6918 | -0.7275 to -0.6566 |
| net P&L per taken trade (episode cluster) | -$3.69 | -$4.34 to -$3.03 |
| total net R (episode cluster) | -1,875.5 | -1,986.2 to -1,765.3 |
| total net P&L (episode cluster) | -$9,995.02 | -$11,852.20 to -$8,161.71 |
| net R per taken trade (14-day blocks, 12 blocks) | -0.6918 | -0.7258 to -0.6461 |
| net P&L per taken trade (14-day blocks) | -$3.69 | -$7.44 to -$0.60 |

These intervals resample realised trades by episode or by 14-calendar-day block. They do not re-simulate capital allocation. Portfolio path bootstrap is deferred to Stage 6b; 7-day and 28-day block sensitivities are also reserved for Stage 6b.

## Verification

Overall verification: **PASS**. Critical failures: **0**.

| check | result | critical |
|---|---|---|
| provenance_reconciled | pass | yes |
| canonical_counts_match_stage5 | pass | yes |
| trades_equal_resolved_plus_censored | pass | yes |
| censored_time_exit_partition | pass | yes |
| trade_ids_unique_and_sequential | pass | yes |
| canonical_trade_fields_consistent | pass | yes |
| portfolio_net_pnl_sum | pass | yes |
| portfolio_gross_pnl_sum | pass | yes |
| portfolio_fee_sum | pass | yes |
| portfolio_final_equity_identity | pass | yes |
| portfolio_total_cost_identity | pass | yes |
| portfolio_cost_components_identity | pass | yes |
| portfolio_utilization_le_one | pass | yes |
| per_trade_accounting_identities | pass | yes |
| position_constraints | pass | yes |
| daily_equity_identities | pass | yes |
| daily_final_equity_matches | pass | yes |
| invalid_censored_never_traded | pass | yes |
| no_forced_end_exit | pass | yes |
| time_exits_are_valid_c1_only | pass | yes |
| resolved_exits_use_frozen_reference | pass | yes |
| time_stop_contribution_reported | pass | yes |
| time_stop_contribution_not_in_signal | pass | yes |
| signal_uses_resolved_only | pass | yes |
| portfolio_14day_block_bootstrap_present | pass | yes |
| executable_portfolio_includes_separate_time_stops | pass | yes |
| all_scenario_equity_identities | pass | yes |
| input_hashes_recorded | pass | yes |
| configuration_and_seed_recorded | pass | yes |
| code_version_recorded | pass | yes |
| independent_20_trade_recompute | pass | yes |

Independent deterministic sample: **20** funded trades (3 same-bar ties, 4 other stops, 7 targets, 6 censored time exits). Result: **PASS**.

| trade_id | resolved | exit kind | exit index | exit reason | pass |
|---:|---|---|---:|---|---|
| 310 | yes | barrier | 2915 | stop_tie_stop_first | pass |
| 932 | yes | barrier | 6353 | target | pass |
| 1469 | yes | barrier | 8948 | target | pass |
| 2502 | yes | barrier | 15390 | stop_tie_stop_first | pass |
| 2574 | yes | barrier | 15769 | target | pass |
| 2684 | yes | barrier | 16316 | stop_tie_stop_first | pass |
| 3648 | yes | barrier | 20844 | target | pass |
| 4263 | yes | barrier | 23585 | stop | pass |
| 4343 | yes | barrier | 23842 | stop | pass |
| 4637 | yes | barrier | 25011 | target | pass |
| 5346 | no | time | 27532 | time_stop_c1_valid_12th_close | pass |
| 5854 | no | time | 29261 | time_stop_c1_valid_12th_close | pass |
| 6188 | yes | barrier | 30867 | target | pass |
| 6216 | no | time | 31020 | time_stop_c1_valid_12th_close | pass |
| 6356 | no | time | 31464 | time_stop_c1_valid_12th_close | pass |
| 7247 | no | time | 34805 | time_stop_c1_valid_12th_close | pass |
| 7447 | yes | barrier | 35389 | target | pass |
| 7630 | no | time | 36095 | time_stop_c1_valid_12th_close | pass |
| 8263 | yes | barrier | 38240 | stop | pass |
| 8540 | yes | barrier | 39579 | stop | pass |

Repeated-run determinism is checked by running this script twice and comparing artifact hashes; the result is recorded in `determinism_check.json`.

## Limitations

- 5m OHLC cannot resolve intrabar ordering or establish realistic intrabar fills; frozen barrier references are the primary contract.
- The spot cash cap can force actual risk far below the 1% budget; R is measured against risk actually taken.
- The 14-day block bootstrap resamples trade statistics, not capital paths. Portfolio path bootstrap is deferred to Stage 6b.
- This is development-sample accounting only; no validation or OOS performance is read. No parameter was optimized.
- Binance BTCUSDT spot is a historical execution proxy; there is no Nobitex execution claim or integration.

## Reproduction

```bash
python stage6_rebuild_v2/rebuild_setup1_accounting.py
```

Artifacts: `stage6_v2_summary.json`, `canonical_trades.jsonl.gz`, `daily_equity.csv`, `primary_portfolio_trades.csv`, `time_stop_trades.csv`, `verification_report.json`, `input_hashes.json`, `config.json`, `code_version.json`.
