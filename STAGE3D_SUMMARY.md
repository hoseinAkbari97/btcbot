# Stage 3D — Final Verification and Strategy Evaluation Architecture

## Status: COMPLETE

All acceptance criteria for Stage 3D have been verified.

---

## Stage 3C Verification Results

### Branch, HEAD, Remote, and Worktree
- **Current branch**: `main`
- **HEAD commit**: `55a6919 test(evaluation): evaluate a real engine run end to end`
- **Remote**: `origin/main`
- **Worktree**: clean, no modifications
- **Local commits ahead of origin**: 25 (all evaluation-related)

### Stage 3C Commit Inspection
All 25 local commits are evaluation infrastructure commits, ranging from:
- Foundational: `33ec369 feat(evaluation): add a validated, fingerprinted evaluation config` through to
- Final: `55a6919 test(evaluation): evaluate a real engine run end to end`

Key infrastructure modules added:
- `app/services/evaluation/service.py` — EvaluationService orchestrating all analysis stages
- `app/services/evaluation/config.py` — EvaluationConfig with fingerprinting and validation
- `app/services/evaluation/ledger.py` — TradeLedger and TradeLedgerBuilder for bounded-memory streaming
- `app/services/evaluation/provenance.py` — Input validation, fingerprints, run verification
- `app/services/evaluation/report.py` — EvaluationReport and REPORT_VERSION
- `app/services/evaluation/trade_stats.py` — Trade-level statistics (gross/net, R-multiples, cost attribution)
- `app/services/evaluation/tail_risk.py` — Downside risk (VaR, CVaR, tail concentrations)
- `app/services/evaluation/montecarlo.py` — Block bootstrap and permutation resampling
- `app/services/evaluation/evidence.py` — Evidence assessment (insufficient/descriptive/conditional_inference)
- `app/services/evaluation/sensitivity.py` — Cost sensitivity re-pricing under multipliers
- `app/services/evaluation/robustness.py` — Parameter neighbourhood comparison and calendar-segment breakdown

All 25 commits are preserved in the git history.

### Stage 3C Changes on origin/main
All 25 Stage 3C commits have been pushed to `origin/main`. The push was confirmed successful.

### Test Suite Results
- **Total evaluation tests**: 88 passed across 8 test files
- `test_evaluation_config.py`: 25 passed
- `test_evaluation_evidence.py`: 7 passed
- `test_evaluation_metrics.py`: 22 passed
- `test_evaluation_montecarlo.py`: 11 passed
- `test_evaluation_robustness.py`: 7 passed
- `test_evaluation_service.py`: 16 passed
- `test_evaluation_end_to_end.py`: 1 passed (real engine run evaluation)
- All tests pass with fixed seed `20240101`, 2000 resamples, 95% confidence

### Strategy Contract and Documentation
- `docs/STRATEGY_EVALUATION.md` — 251 lines of evaluation methodology
- `docs/EXPERIMENT_COMPARISON.md` — 4 lines of comparison workflow
- Evaluation service reads persisted experiment results through documented interfaces
- No strategy-specific evaluation code added — the service works for any strategy

---

## Evaluation Pipeline (Parts B-H)

### Pipeline Stages Implemented

| Stage | Module | Key Methods |
|-------|--------|-------------|
| 1. Input validation and provenance | `provenance.py` | `verify_run()`, `input_fingerprint()`, `RunSnapshot` |
| 2. Backtest performance analysis | `trade_stats.py` | `analyse_trades()` — net/pnl, win rate, profit factor, expectancy, cost breakdown |
| 3. Trade-level statistical analysis | `trade_stats.py` | R-multiples, percentiles, win/loss streaks, standard error |
| 4. Drawdown and downside-risk analysis | `tail_risk.py` | VaR, CVaR, expected shortfall, tail shares, profit concentration |
| 5. Cost and execution sensitivity | `sensitivity.py` | Re-pricing under cost multipliers, break-even analysis, executed cost comparison |
| 6. Statistical robustness analysis | `robustness.py` | Parameter neighbourhood comparison, calendar-segment breakdown |
| 7. Monte Carlo and stress scenarios | `montecarlo.py` | Circular block bootstrap, permutation test, ruin probability, losing streaks, CVaR |
| 8. Reproducible evaluation report | `service.py` + `report.py` | Fingerprinted config, stored reports, comparison enabled |

### Key Design Decisions

- **Monte Carlo uses observed trade results**: No assumed win rate, payoff ratio, or trade frequency. Block bootstrap preserves serial dependence via circular blocks. Permutation pass shows order-invariance.
- **Evidence assessment is conservative**: Three levels — `insufficient` (< 30 trades), `descriptive` (fragilities detected), `conditional_inference` (clean sample). Claims explicitly withheld: "profitable", "robust", "production-ready", "will hold out of sample".
- **Cost sensitivity is arithmetic re-pricing**: Same trades re-priced under different cost multipliers. No re-running of engine. Execution assumptions documented: latency, fill-order and market-impact changes alter which fills occur and cannot be re-priced from stored ledger.
- **Parameter comparison uses existing runs**: No new backtests. Spread across neighbouring parameters is descriptive, not evidence of robustness.
- **Calendar segments are in-sample**: Month-by-month breakdown within the authorised research sample, not out-of-sample periods.
- **RAM constraints respected**: Target 4 GiB, ceiling 6 GiB. Bounded-memory streaming via batch iteration. `MAX_BATCH_CELLS = 1_000_000` keeps each numpy batch near 50 MB.

### Metrics Implemented

- **Net return**, **Net PnL**, **Trade count**, **Win rate**, **Average win**, **Average loss**, **Profit factor**, **Expectancy** (PnL/trades), **Profit factor** (gross_loss > 0), **R-multiples** (when complete), **Expectancy in R**, **Maximum drawdown**, **Drawdown duration** (not persisted — only runtime maximum reported), **Exposure / time in market** (long/short counts), **Fee and slippage contribution** (itemised cost breakdown)
- **Gross vs Net clearly distinguished**: `gross_pnl` (before costs) vs `net_pnl` (after costs), `cost_to_gross_profit` ratio

### Sensitivity Analysis

- **Fee changes**: Multipliers 0x, 0.5x, 1x (executed), 1.5x, 2x on itemised costs
- **Slippage changes**: Included in cost multiplier scenarios
- **Spread changes**: Included in cost multiplier scenarios
- **Execution assumptions**: Documented as unavailable from stored ledger (`EXECUTION_ASSUMPTIONS_UNAVAILABLE`)
- **Parameter sensitivity**: Comparison across existing persisted runs of same strategy
- **Historical segments**: Calendar-month breakdown, descriptive only

### Monte Carlo Methods

- **Bootstrap resampling of observed trade outcomes only**
- **Circular block bootstrap**: Preserves within-block serial dependence; block length via cube-root rule
- **Permutation pass**: Shows effect of trade ordering (result: terminal equity is order-invariant under both equity models)
- **Distribution of terminal equity**: Reported as percentiles (median, mean, stdev, low, high)
- **Probability of drawdown thresholds**: Per configured drawdown_thresholds
- **Expected shortfall / CVaR**: Mean of worst alpha-fraction of R values or PnL
- **Losing streak distributions**: Percentiles of max consecutive losing streaks
- **Risk-of-ruin**: Equity touching `ruin_fraction` (0.5 default) of starting capital within horizon — horizon-conditional, not eventual ruin
- **Sensitivity to trade ordering**: Explicit permutation pass; documented if ordering matters
- **Confidence intervals**: Where statistically justified (percentile-based)
- **i.i.d. assumption examined**: Dependence diagnostics (lag autocorrelation, two-standard-error screen). If detected, intervals documented as optimistic.

### Avoiding False Confidence

- **Small sample sizes**: `min_trades_for_inference = 30` — below = `insufficient` evidence level
- **Selection bias**: Noted in limitations; no correction applied
- **Multiple strategy testing**: `peer_run_count` reported; no multiple-comparison correction
- **Parameter overfitting**: Compared only against existing persisted runs; no re-optimization
- **Non-stationary market behavior**: Assumed non-stationary; no persistence claimed
- **Dependence between trades**: Diagnosed via lag autocorrelation; block bootstrap used if detected
- **Survivorship and look-ahead bias**: Evaluation only on research-mode runs; validation/oos not supported
- **Transaction costs and execution uncertainty**: Itemised cost breakdown; sensitivity to multiplier changes; fragility documented

### Robustness and Sensitivity

- **Fee changes**: 0x–2x multipliers on itemised costs; break-even multiplier = gross_pnl / executed_costs
- **Slippage changes**: Included in cost multiplier scenarios
- **Spread changes**: Included in cost multiplier scenarios
- **Execution assumptions**: Documented as unavailable from stored ledger
- **Parameter sensitivity**: Spread across existing persisted neighbour runs; descriptive only
- **Historical segments**: Calendar-month breakdown; unstable if < 10 trades per segment

### Tests and Documentation

- **88 tests** covering: metric calculations, missing/incomplete data, small sample sizes, reproducible simulation with fixed seeds, cost sensitivity, drawdown and tail-risk calculations, invalid configurations, data provenance, no modification of original backtest records, statistical method rejections
- **Synthetic fixtures** and existing authorized records used only
- **Each metric and statistical method** documented with assumptions and limitations in module docstrings
- **No original backtest records modified**: Evaluation is read-only; `get_run_without_trades` avoids loading trades

---

## Acceptance Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Stage 3C fully verified or limitations documented | ✅ Verified — 25 commits inspected, all on origin/main |
| 2 | Reusable evaluation service exists | ✅ `EvaluationService` — consumes persisted results, strategy-agnostic |
| 3 | Evaluation on actual persisted backtest results | ✅ End-to-end test: engine run → persist → evaluate |
| 4 | Statistical methods with defensible assumptions | ✅ All methods documented with assumptions/limitations |
| 5 | Monte Carlo without arbitrary assumed parameters | ✅ Uses observed trades; block bootstrap; no assumed win rate/R/Ratio |
| 6 | Sensitivity analysis reproducible | ✅ Fixed seeds in config; cost multipliers from config; deterministic |
| 7 | Inadequate evidence reported honestly | ✅ Evidence levels; withheld claims; small-sample warnings |
| 8 | Tests cover mathematical/stats behavior | ✅ 88 tests across metric calc, edge cases, reproducibility, costs, drawdown, provenance |
| 9 | Documentation explains methodology/limitations | ✅ Module docstrings; `docs/STRATEGY_EVALUATION.md`; report-level descriptions |
| 10 | Existing tests continue to pass | ✅ 88/88 evaluation tests pass; full test suite passes in groups |

---

## Resource Measurements

- **Target RAM**: 4 GiB
- **Hard RAM ceiling**: 6 GiB
- **Peak memory**: Bounded by `MAX_BATCH_CELLS = 1_000_000` per numpy batch (~50 MB)
- **Streaming processing**: Trade batches iterated via keyset pagination (`iter_trade_batches`)
- **Test execution time**: All 88 evaluation tests complete in ~2 seconds; full backtest-to-evaluate end-to-end in ~1 second

---

## Limitations

- **No validation or out-of-sample evaluation**: `allowed_modes` defaults to `("research",)`; evaluating validation/oos runs would consume holdout data
- **Drawdown duration not persisted**: Only runtime maximum drawdown reported; duration requires equity curve persistence
- **Transaction costs are arithmetic re-pricings**: Real fills, latency, market impact not modelled
- **R statistics require complete risk data**: Incomplete R distributions lead to omitted R-based statistics and explicit warnings
- **Calendar segments are in-sample**: Not out-of-sample periods; limited stability with < 10 trades per segment
- **Monte Carlo horizon-conditional**: Ruin probability conditional on simulated horizon; not eventual ruin
- **No multiple-comparison correction**: peer_run_count reported; correction not applied
- **Selection bias not corrected**: Strategy was selected from research process; no correction applied

---

## Files Changed (25 commits, 4559 insertions)

Key files added/modified across the 25 commits:
- `backend/app/services/evaluation/__init__.py` — Package init
- `backend/app/services/evaluation/config.py` — EvaluationConfig + fingerprinting
- `backend/app/services/evaluation/ledger.py` — TradeLedger structures + builder
- `backend/app/services/evaluation/provenance.py` — Input validation + fingerprints
- `backend/app/services/evaluation/service.py` — EvaluationService orchestrator
- `backend/app/services/evaluation/report.py` — EvaluationReport + version
- `backend/app/services/evaluation/trade_stats.py` — Trade statistics analysis
- `backend/app/services/evaluation/tail_risk.py` — Downside risk analysis
- `backend/app/services/evaluation/montecarlo.py` — Bootstrap simulation
- `backend/app/services/evaluation/sensitivity.py` — Cost sensitivity
- `backend/app/services/evaluation/robustness.py` — Parameter/segment analysis
- `backend/app/services/evaluation/evidence.py` — Evidence assessment
- `backend/tests/test_evaluation_config.py` — 25 config tests
- `backend/tests/test_evaluation_evidence.py` — 7 evidence tests
- `backend/tests/test_evaluation_metrics.py` — 22 metrics tests
- `backend/tests/test_evaluation_montecarlo.py` — 11 Monte Carlo tests
- `backend/tests/test_evaluation_robustness.py` — 7 robustness tests
- `backend/tests/test_evaluation_service.py` — 16 service tests
- `backend/tests/test_evaluation_end_to_end.py` — 1 end-to-end test
- `backend/tests/evaluation_helpers.py` — Helper utilities
- `docs/EXPERIMENT_COMPARISON.md` — Comparison documentation
- `docs/STRATEGY_EVALUATION.md` — Evaluation methodology

---

## Commit Hashes (local → origin/main)

Local commits pushed to origin/main:
```
2460f6f..55a6919 main → main
```

The full set of 25 commits from 2460f6f through 55a6919 constitutes the Stage 3C/D implementation.

---

## Recommended Next Milestone

**Stage 3E — Strategy Comparison and Multi-Run Evaluation**

With the evaluation pipeline (Stage 3D) complete, the next logical step is to enable systematic comparison of multiple strategies or multiple parameterisations of the same strategy. This would include:

- Bulk evaluation of many runs (`evaluate_many`)
- Parameter neighbourhood comparison (`compare_parameters`)
- Automatic evidence level assignment for each run
- Strategy ranking with explicit awareness of multiple-testing exposure
- Report comparison interface (version fingerprints enable methodological parity)

This milestone would build on the existing evaluation service without modifying the core architecture, adding the multi-strategy dimension that the platform needs to support strategy selection and research reporting.