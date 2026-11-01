# Stage 6 v1 — final protocol clarifications (approved rebuild v2)

Status: recorded before implementation. Supersedes the unapproved
`stage6_rebuild/` draft. The draft directory and its outputs are left untouched.

Execution proxy: **Binance BTCUSDT spot**, long-only, no leverage. This is a
historical execution proxy, not a Nobitex integration or execution claim.

Data scope: **development split only**, `2021-01-01T00:00:00Z` inclusive to
`2024-07-01T00:00:00Z` exclusive. No validation or out-of-sample performance is
read or reported.

## Decision 1 — preserve the existing draft

- Approved implementation lives in `stage6_rebuild_v2/`.
- `stage6_rebuild/` and its outputs are not modified or overwritten.
- All previous Stage 6 draft results are treated as unapproved.

## Decision 2 — two separate evaluations

### A. Frozen signal evaluation

- Only barrier-resolved trades contribute.
- Same-bar stop/target ties use the frozen **stop-first** convention.
- Censored observations are reported separately and are **not** converted into
  resolved outcomes.
- The primary statistic is gross R with the raw entry-to-stop distance as the
  denominator. No time-stop return enters this evaluation.

### B. Executable portfolio evaluation

- Barrier-resolved trades use the frozen outcome contract.
- A censored trade may be closed at the close of the twelfth candle only when it
  is a **C1-valid 12-candle no-barrier trade**: the entry is inside the
  development split, all twelve candles exist, and no data gap falls inside the
  window.
- Data gaps, split boundaries and insufficient future data never receive an
  invented exit. Such a trade is excluded from the executable portfolio and
  reported as `no_executable_exit`.
- Time-exited trades are reported separately: count, net P&L, total R, fees,
  and their share of portfolio activity.
- Time-stop results are never combined with the frozen barrier-only signal
  expectancy.

## Decision 3 — exit-price semantics

The frozen outcome contract in the scored ledger is the primary exit reference.
The implementation does not assume that a candle close is a realistic stop or
target fill.

| outcome | primary exit reference | treatment |
|---|---|---|
| Stop hit | Frozen ledger `exit_price` at the stop bar, normally the stop level; if price gaps through the stop, the ledger records the bar-open price, which is worse. | Sell fill applies the frozen adverse concession and tick-down. The ledger price is not clamped or rewritten. |
| Target hit | Frozen ledger `exit_price` at the target bar, normally the +1R target; if price gaps through the target, the ledger records the bar-open price, which is better. | Sell fill applies the frozen adverse concession and tick-down. The ledger price is not clamped or rewritten. |
| Same-bar stop/target tie | Stop-first: booked as a stop hit at the stop reference. | Retained with `ambiguous=true`; tie-win or split conventions are not substituted into the primary result. |
| Gap through stop | Frozen ledger bar-open price below the stop. | Used as recorded; this is more conservative than a stop-level fill. |
| Gap through target | Frozen ledger bar-open price above the target. | Used as recorded; this is more favourable than a target-level fill. |
| Time-stop exit | Close of the twelfth candle (`entry_index + 11`), only for C1-valid no-barrier trades. | Sell fill applies the frozen adverse concession and tick-down. Invalid windows receive no exit. |

Five-minute OHLC cannot establish the intrabar order of touches or a realistic
intrabar fill. That limitation is disclosed rather than modelled. No
alternative fill assumption is used in the primary v1 result; any future
alternative fill assumption must be a separately named sensitivity.

## Decision 4 — confirmed choices

- Output directory: `stage6_rebuild_v2/`.
- Portfolio path bootstrap: deferred to Stage 6b. v1 reports trade-level
  episode-cluster intervals and a 14-calendar-day block bootstrap of trade
  statistics only; it does not re-simulate the capital path.
- Block length: 14 days. 7-day and 28-day sensitivities are reserved for
  Stage 6b.
- Identity or accounting conflicts: hard abort.
- Cost scenarios: 0.5x, 1x, 1.5x, 2x and 3x, each with (a) a re-filtered trade
  universe and (b) the fixed primary trade universe.

## Decision 5 — v1 scope

Not implemented: a multi-strategy framework, validation/OOS analysis,
parameter optimization, Monte Carlo, portfolio path-bootstrap simulations, or
Nobitex execution claims/integration.

## Verification gates

The run is accepted only if all of the following pass; a critical failure aborts
the run before accepted outputs are written.

1. Canonical trade counts and provenance reconcile with the Stage 5 checkpoint.
2. A deterministic sample of 20 trades is independently recomputed from raw
   ledger rows.
3. Every accounting identity holds.
4. Cash and position constraints hold at every bar.
5. No unavailable exit is invented.
6. Repeated runs produce identical output.
7. Frozen signal results and time-stop portfolio results remain distinct.
8. Input hashes, configuration, code version and random seeds are recorded.
