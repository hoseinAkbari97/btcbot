# Stage 3H provenance audit

Baseline: `1cbe18c` (Stage 3G close), clean `main`, `HEAD == origin/main`.
This audit was made from the code at that revision. It records what can and
cannot be established from persisted evidence.

## Existing integrity protections

- `ExperimentSubmission` is frozen and its JSON definition is fingerprinted
  (`app/schemas/experiment.py:34-73`, `app/services/experiment/service.py:122-133`).
- Idempotency includes the config fingerprint, dataset fingerprint, strategy
  version and git commit; replay is deliberately distinct
  (`app/services/experiment/service.py:135-168`).
- Lifecycle transitions are explicit and terminal states cannot be changed
  (`app/services/experiment/service.py:55-91`).
- Backtest runs, trades and exact engine equity points are persisted
  (`app/repositories/backtest.py:50-168`).
- Evaluation is read-only, verifies run input, streams the ledger, runs
  accounting reconciliation and fingerprints the ledger and equity series
  (`app/services/evaluation/service.py:50-146`,
  `app/services/evaluation/reconciliation.py`).
- Report digests are stored with report snapshots
  (`app/models/evaluation.py:27-51`, `app/services/evaluation/report.py:97-102`).
- Backtest comparison refuses runs with unrecorded or differing assumptions
  (`app/services/backtest/comparison.py`).

## Existing reproducibility guarantees

- A fresh experiment records the requested strategy name, parameters, symbol,
  timeframe, period, capital, accounting currency, costs, risk limits, mode and
  evaluation settings in an immutable configuration document.
- The exact candle values consumed by the engine are fingerprinted by
  `dataset_fingerprint()` (`app/services/backtest/runner.py:54-67`).
- Engine and accounting versions are present on the run row (`git_commit`,
  `accounting_model_version`), and evaluation method version is stored on the
  report row.
- Historical runs keep nulls for fields that were not recorded. Stage 3G
  migration explicitly did not backfill them.

## Actual gaps identified

1. **No canonical run manifest.** The inputs needed to identify one run are
   spread across the experiment, run and report rows; there is no single
   immutable, fingerprinted description of a run.
2. **Strategy implementation identity is not persisted.** The registry stores a
   factory, name, description and optional capabilities
   (`app/services/backtest/registry.py:75-84`). The runner does not pass the
   resolved strategy version to the engine (`app/services/backtest/runner.py:167-179`),
   so the run stores the default `"1"` (`app/services/backtest/engine.py:420`).
   No module, qualified name or source identity is recorded.
3. **Market source is dropped on the research read path.** Candles are unique
   per instrument/source/timeframe/open_time
   (`app/models/market_data.py:60-82`), but `list_candles()` has no source filter
   or deterministic tie-break and `load_candles()` discards `source_id`
   (`app/repositories/market_data.py:139-157`,
   `app/services/backtest/runner.py:86-114`). The dataset fingerprint covers
   only `open_time` and OHLCV, not close time, closed status or the remaining
   CandleData fields that the engine receives.
4. **Stored report integrity is never rechecked.** Retrieval endpoints return
   `report.report` directly (`app/api/routes/experiment.py:252-258`,
   `app/api/routes/experiment.py:422-430`). No code compares the stored digest
   with a reconstructed report or compares source fingerprints with the current
   run.
5. **Reports do not reference a manifest.** Even if a manifest existed, a stored
   report could not be tied to it.
6. **The dashboard cannot distinguish verified, partial and unavailable
   provenance.** It shows configuration and dataset fingerprints but no report
   verification, manifest state, reconciliation status or verification
   classification (`frontend/src/pages/ExperimentDetail.tsx:195-220,347-403`).

## Assumptions that cannot be verified from old persisted data

- Whether an old run's factory source matched the currently registered factory.
- Which data source supplied an old run's candles when more than one source had
  rows for the same symbol/timeframe/window.
- Whether a report digest and source fingerprints were correct at the time an
  old report was stored unless the stored document itself can be reconstructed.
- Whether a legacy run had an engine equity curve; Stage 3G only proves that no
  such series is persisted for it now.

## Narrow implementation decision

Stage 3H will add one immutable manifest per new backtest run, a canonical
dataset fingerprint over the exact ordered rows consumed by the engine, a
read-time report verification helper, and a read-only verification service/API.
It will not rerun a backtest, rewrite historical reports, backfill manifests, or
change statistical methods and thresholds. Historical rows will be explicitly
reported as partial or unavailable.
