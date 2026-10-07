# Session Notes - Development Session

**Session Started**: 2026-09-22
**Primary Goal**: Implement Phase 0 + Phase 1 of BTC/USDT Quantitative Trading Platform
**Target**: Complete professional trading terminal with market data infrastructure

## Current Status

✅ **Phase 0 + 1 Implementation Complete**
- Repository foundation with proper structure
- Docker Compose with PostgreSQL, Redis, FastAPI, React
- Alembic database migrations
- MarketDataProvider abstraction with Binance adapter
- Historical data ingestion (5m, 15m, 1H, 4H, 1D)
- Data validation and quality reporting
- Professional trading terminal frontend
- Real-time WebSocket streaming
- Comprehensive testing
- Documentation

✅ **Phase 2 Implementation Complete**
- Professional market chart with zoom/pan, crosshair, OHLC tooltip, volume
- Timeframe switching (5m, 15m, 1H, 4H, 1D)
- Backend market-structure analysis service (`backend/app/services/market_structure/`)
  - Swing high/low detection (configurable lookback window)
  - HH/HL/LH/LL classification
  - Break-of-Structure (BOS) detection
  - Structure shift detection
  - Objective liquidity level derivation from swing extrema
  - Market regime classification (TREND_UP / TREND_DOWN / RANGE / UNKNOWN)
- Backend API endpoint: `GET /api/v1/structure/analyze`
- Frontend chart overlay components:
  - `SwingHighLowMarkers` — arrow markers on swing highs/lows
  - `StructureShifts` — shape-coded markers for HH/HL/LH/LL/BOS/shift
  - `LiquidityZones` — dashed horizontal price lines for liquidity levels
  - `SetupMarkers` — placeholder for future Phase 3+ setup engine
- Overlay toggle controls in chart toolbar (Swings / Structure / Liquidity)
- Regime badge displayed in OHLC strip
- TypeScript types for all structure data
- All 17 backend tests passing
- Frontend builds cleanly

✅ **Phase 3 + Phase 4 Implementation Complete**
- Four baseline strategies as scientific controls (`backend/app/services/backtest/baselines.py`)
  - `buy_and_hold` — unbracketed, held to the end of the data
  - `random` — seeded null hypothesis under identical risk and execution assumptions
  - `sma_trend` — long-only moving-average trend with ATR brackets
  - `donchian_breakout` — long-only breakout of the prior N-bar high, N-bar low exit
- Event-driven backtest engine (`backend/app/services/backtest/engine.py`)
  - Signal at bar T, fill at the open of bar T + `latency_bars` — never at the signal bar's close
  - Intrabar stop/target evaluation, resolved stop-first when a bar touches both
  - Fixed-fractional position sizing capped by available cash (spot, no leverage)
  - End-of-data liquidation, so no position is left silently marked to market
  - No-future-leakage enforced structurally: the engine truncates history to `candles[:index + 1]`
    before handing it to the strategy, so leakage is not merely avoided but unrepresentable
- Cost model (`backend/app/services/backtest/costs.py`) — per-side fee, half-spread, slippage applied
  against the fill direction, and a `scaled()` multiplier for sensitivity testing
- Performance metrics (`backend/app/services/backtest/metrics.py`) — return, CAGR, volatility, Sharpe,
  Sortino, drawdown, Calmar, profit factor, win rate, expectancy, R-multiples, fees, turnover, exposure,
  and calendar-keyed monthly/yearly returns
- Reproducibility contract (`backend/app/services/backtest/runner.py`) — git commit, library version,
  effective parameters, dataset range, and full cost assumptions persisted with every run; runs are
  append-only
- Persistence (`backend/app/repositories/backtest.py`, `backend/app/models/backtest.py`) with cascade
  delete from run to trades
- API: `GET /api/v1/backtests/strategies`, `POST /api/v1/backtests/run`, `GET /api/v1/backtests/runs`,
  `GET /api/v1/backtests/runs/{run_id}`
- CLI: `python -m app.cli backtest --strategies ... --cost-scale ...`
- 109 backend tests passing

### Bugs found by the Phase 3+4 test suite

The new tests surfaced five defects in previously-verified code, all silent-wrong-answer or crash
class. The earlier manual smoke test had exercised only `buy_and_hold`, which is exactly the strategy
least affected by several of them.

1. **`latency_bars` was not applied to fill timing.** It gated only whether a signal was requested, so
   `latency_bars=2` still filled one bar after the signal. Fixed by adding `fill_index` to the pending
   order and gating the fill on `index >= pending.fill_index`.
2. **Exit signals were impossible.** The signal step skipped the strategy entirely while a position was
   open, so `CLOSE` could never be emitted and `sma_trend` / `donchian_breakout` would hold forever.
   The strategy is now consulted while in a position, with a flat-position rule that stops a second
   entry stacking on an open one.
3. **Full-cash entries were rejected for want of cash.** Sizing consumed the entire balance and left
   nothing for the entry fee, so the cash cap rejected the fill on a 1-ULP comparison. Sizing now
   reserves the fee.
4. **`build_strategy()` collided with the `name` parameter.** `default_parameters()` includes each
   strategy's own `name` field, so splatting it back raised `TypeError` for every baseline. `name` is
   now positional-only.
5. **`Decimal` parameters could not be persisted.** Every `POST /run` failed on a non-JSON-serialisable
   strategy parameter. Values are now coerced to an exact string, with unknown types stored by `repr`
   so a reproducibility record never silently loses information.

Two further corrections were made on the strength of reviewing actual metric output:

- **CAGR overflowed on short windows.** `(final/initial) ** (1/years)` raised `OverflowError` on any
  research run of a few hours, crashing it. Annualisation is now skipped below 30 days, and the
  power is guarded.
- **Sharpe and Sortino were nonsense on short samples.** Annualising a 33-hour window by
  `sqrt(105,120)` produced a Sharpe of 484. On a sub-annual window these are now reported
  unannualised, and Calmar follows CAGR in reporting zero.

## System Architecture

### Backend Stack
- FastAPI with structured JSON logging
- PostgreSQL with Alembic migrations (SQLite in-memory for tests)
- Redis for realtime coordination
- Python 3.12 with async support
- Provider pattern for exchange adapters

### Frontend Stack
- React 18 with TypeScript
- Vite for development/build
- Lightweight-Charts for professional trading charts
- WebSocket integration for real-time data
- Responsive trading terminal UI

### Data Flow
```
Binance REST/WebSocket → BinanceMarketDataProvider → Validation → PostgreSQL + Parquet → API/WebSocket → React Terminal
```

## Key Features Delivered

### Core Infrastructure
1. **Docker Compose** - Four-service deployment (frontend, backend, postgres, redis)
2. **Database Schema** - markets, instruments, data_sources, candles, quality_reports
3. **Configuration Management** - Pydantic settings with .env support
4. **Logging** - Structured JSON logging with correlation IDs
5. **Testing** - Unit, integration, and end-to-end tests with coverage

### Backtesting (Phases 3+4)
1. **Four Baselines** - Scientific controls, not candidate strategies
2. **Event-Driven Engine** - Signal-then-fill with configurable latency
3. **Realistic Costs** - Fee, spread, and slippage charged on both sides
4. **Risk Management** - Fixed-fractional sizing, protective stop and target
5. **Full Metric Suite** - Return, drawdown, Sharpe, Sortino, Calmar, profit factor, expectancy
6. **Reproducible Runs** - Commit, library version, parameters, and costs stored per run
7. **Sensitivity Analysis** - `cost_scale` re-runs a strategy under worse assumptions

### Market Data
1. **Provider Abstraction**
2. **Historical Ingestion** - 5m, 15m, 1h, 4h, 1d timeframes
3. **Data Validation** - Hard rules and anomaly detection
4. **Dual Storage** - PostgreSQL for queries, Parquet for research
5. **Quality Reports** - Persistent validation evidence

### Trading Terminal
1. **Professional Chart** - Candlestick charts with volume
2. **Real-time Streaming** - WebSocket data updates
3. **System Status** - API, DB, Redis health monitoring
4. **Timeframe Controls** - 5m through 1d switching
5. **Trading Safety** - Phase 1 boundary (no execution)

## Technical Implementation

### Backend Components
- **app/main.py** - FastAPI application factory
- **app/core/config.py** - Configuration management
- **app/services/market_data/** - Provider abstraction
- **app/repositories/market_data.py** - Data access layer
- **app/api/routes/** - REST and WebSocket APIs
- **app/cli.py** - Command-line ingestion and backtest tools
- **app/services/backtest/** - Engine, baselines, costs, metrics, runner (Phases 3+4)
- **app/repositories/backtest.py** - Backtest run and trade persistence
- **app/api/routes/backtest.py** - Backtest research endpoints

### Frontend Components
- **src/App.tsx** - Main application router
- **src/pages/Dashboard.tsx** - Main dashboard with status and chart
- **src/charts/MarketChart.tsx** - Professional trading chart
- **src/components/StatusCard.tsx** - System status display
- **src/hooks/useSystemStatus.ts** - System status polling
- **src/services/api.ts** - API client abstraction

## Development Workflow

### Commands
```bash
# Docker deployment
docker compose up --build

# Apply migrations
make migrate

# Backfill data
make ingest

# Run tests
make test

# Backtest baselines over stored candles
cd backend && python -m app.cli backtest --strategies sma_trend,donchian_breakout
cd backend && python -m app.cli backtest --strategies buy_and_hold --cost-scale 2

# Backtest over HTTP
curl -X POST http://localhost:8000/api/v1/backtests/run \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","timeframe":"5m","strategy":"sma_trend"}' 

# Event -> outcome research (CLI only; no HTTP route). Writes a JSON and a Markdown
# report to data/research/. Use --sample N to bound the run: the full 1h history is
# feasible but slow, and detection alone takes minutes.
python backend/scripts/run_event_research.py \
  --dataset backend/data/datasets/BTCUSDT-1h-20210101-20260901.json \
  --sample 20000

# View logs
make logs

# Development servers
# Backend (one terminal)
cd backend && python -m app.main

# Frontend (separate terminal)  
cd frontend && npm run dev
```

### Testing
- Unit tests for validation, providers, storage
- Integration tests for end-to-end data flow
- API tests for endpoint behavior
- Coverage tracking with pytest-cov

## Data Quality

### Validation Rules
- **Hard Rules**: OHLCV integrity, positive prices, proper timestamps
- **Dataset Checks**: Duplicate detection, missing intervals, overlaps
- **Anomaly Detection**: Statistical outliers (robust z-score > threshold)

### Quality Reports
Each ingestion creates a persistent record with:
- Symbol, timeframe, source, time range
- Fetched, stored, duplicates, missing, invalid, anomaly counts
- Pass/fail status and structured issue list
- Raw capture path and Parquet file paths

## Safety Boundaries

### Constraints (still in force)
- No exchange credentials stored
- No live trading (all trading is paper-only)
- No leverage — sizing is capped by available cash
- No ML model training
- No autonomous or scheduled order placement
- No news or sentiment agent
- Public market data only

### Data Integrity
- Raw provider responses never overwritten
- All timestamps in UTC
- No future data leakage — enforced structurally in the backtest engine, not by convention
- Timeframe alignment enforced
- Backtest runs are append-only; a stored experiment is never edited in place

## Performance Characteristics

### Database
- PostgreSQL with indexed queries
- Parquet with Zstandard compression
- Partitioned by symbol/timeframe/year/month

### Realtime
- WebSocket bridge for live chart updates
- 15-second system status polling
- Connection persistence and reconnection

### Data Volume
- 5-minute data: ~10,800 candles/day
- 15-minute data: ~3,600 candles/day
- 1-hour data: ~24 candles/day
- Daily data: ~1 candle/day

✅ **Phase 5 Implementation Complete — Risk Engine**
- Risk engine (`backend/app/services/backtest/risk.py`) as a layer *independent of strategy logic*,
  per spec §12: a strategy says what it wants, the engine decides what it is allowed to do and how
  big. A strategy can lower its own risk but can never raise it past the ceiling or override a halt.
- `RiskLimits` — frozen dataclass, one field per spec control, `__post_init__` validating every
  field so a misconfigured limit is a `ValueError` at construction rather than a silent wrong run:

  | Field | Default | Meaning |
  |---|---|---|
  | `max_risk_per_trade` | `0.01` | Ceiling on any single trade's risk, whatever the strategy asks |
  | `max_portfolio_exposure` | `1.0` | Notional / equity ceiling; 1.0 means spot, no leverage |
  | `max_daily_loss` | `0.05` | Fraction of day-open equity; halts entries for the rest of the day |
  | `max_weekly_loss` | `0.10` | Same, anchored to the ISO week |
  | `max_drawdown` | `0.20` | From the running peak; halts all entries |
  | `max_simultaneous_positions` | `1` | Accepted and validated; see limitations |
  | `cooldown_bars_after_loss` | `0` | Bars blocked after a losing trade |
  | `emergency_stop_loss` | `0.50` | Absolute kill switch on total loss; latches for the run |
  | `max_stale_bars` | `5` | Force-exits a position whose bar data stops advancing |

  Per spec §12 these values are examples, not a recommended universal setting, and every run records
  the limits it used.
- `RiskDecision` — every gate returns one, with a stable reason slug (`emergency_stop`,
  `daily_loss_limit`, `drawdown_limit`, `cooldown`, `stale_data`) so a stored run's violation list
  can be counted and compared across experiments.
- Integration into the engine:
  - Entries are gated before sizing; a refusal is recorded in `rejected_signals` *and* in
    `risk_violations` rather than silently skipped
  - Risk-forced exits outrank a position's own stop and target, so a halt or stale-data exit does
    not have to wait for a stop to trigger
  - The exposure cap bounds a new position by the headroom left under `max_portfolio_exposure`
  - `BacktestRun` gained `risk_violations: list[str]`
- Opt-in by construction: `BacktestEngine(risk=None)` means *no risk layer* and honours the strategy's
  request exactly, so every pre-Phase-5 run stays reproducible and the 109 existing tests stayed
  green unchanged. All 9 of the 9 limits are opt-in; omitting them from an API or CLI request leaves
  the run unsupervised.
  - **Superseded by the hardening pass.** `risk=None` is now only permitted in `RunMode.RESEARCH`.
    `simulation`, `paper` and `live` raise rather than proceed unsupervised, so the risk engine
    cannot be bypassed by omission outside research experiments. `BacktestRequest.mode` also makes
    those modes reachable over HTTP, and the route returns a 422 naming the mode when an ordered
    mode arrives without `risk_limits`, so the enforcement is exercisable end to end.
- Recorded with the run rather than in a new table: the limits are execution assumptions, already
  captured in the `parameters` JSON alongside `allow_short` and the cost model, so a stored run
  reproduces without a migration.
- API: optional `risk_limits` object on `POST /api/v1/backtests/run`; `risk_violations` returned on
  every run response
- CLI: `--max-risk-per-trade`, `--max-portfolio-exposure`, `--max-daily-loss`, `--max-weekly-loss`,
  `--max-drawdown`, `--cooldown-bars`, `--emergency-stop-loss`, `--max-stale-bars`
- 143 backend tests passing (up from 109)

### Phase 1–5 Research Hardening (session of 2026-10-03)

The bulk of the hardening was already implemented in this working tree by an earlier pass. This
session verified the fixes against the code rather than assuming them, and found and fixed two
defects the original gap report had not anticipated.

✅ **Verified as already implemented** (each confirmed by reading the code, not taken on trust):

| Requirement | Where it lives |
|---|---|
| Confirmation timestamps on swings, events, levels | `market_structure/analysis.py`, `schemas/market_structure.py` |
| Causal rewrite — every derived quantity respects `as_of_index` | `market_structure/analysis.py` |
| Reusable lookahead audit (prefix-invariance + no-future-timestamps) | `research/lookahead.py` |
| Event detection separated from strategy decision | `research/events.py` — events carry `event_index` / `confirmation_index` / `is_known_at()` |
| Event → outcome labelling (forward returns, MFE/MAE, R barriers) | `research/outcomes.py` |
| Target grid +0.5R/+1R/+1.5R/+2R resolved in one pass, three-valued outcomes | `research/outcomes.py` (`TARGET_R_GRID`, `TargetOutcome`, `_scan_barriers`) |
| Phase 11 per-setup stats (win/loss rate over resolved only, avg + median R, time to target/stop) | `research/aggregate.py` (`OutcomeAccumulator.target_stats`) |
| Null hypotheses and baselines | `research/baselines.py` |
| Bootstrap + Benjamini–Hochberg FDR | `research/statistics.py` |
| Research report generator | `research/report.py`, `backend/scripts/run_event_research.py` |
| Complete trade ledger (signal/order/fill times, costs itemised, MAE/MFE, regime) | `backtest/engine.py` (`Trade`) |
| **Gross and net R both computed** | `engine.py` — `gross_r`, `net_r`, `r_multiple` as a backward-compatible alias of `gross_r` |
| Risk vs allocation vs exposure kept distinct | `SizingModel` (`stop_risk` / `notional_exposure`), `risk_fraction` / `capital_fraction` / `exposure_fraction` |
| Risk engine cannot be bypassed outside research | `RunMode` + `enforce_run_mode()` in `engine.py` |
| Full R-distribution statistics | `backtest/distributions.py`, `metrics.r_distribution` |
| Multi-year dataset with content-hash versioning | `backend/data/datasets/` + `manifest.json` (sha256 per file) |
| Monte Carlo handoff projection | `Trade.as_monte_carlo_row()` — single definition of the downstream contract |

🆕 **New this session**

- `docs/MONTE_CARLO_HANDOFF.md` — the handoff contract that existed in code but was written down
  nowhere. Documents every field, the invariants a consumer may rely on, and how to handle the
  `null` R on stopless trades without fabricating a risk definition.
- `docs/GAP_REPORT.md` addendum — the two findings below, recorded rather than silently fixed.
- Regression test `test_a_sweep_is_a_crossing_not_a_persistent_condition`.

### Bugs found by the Phase 1–5 research-hardening pass

Both are in the event-research layer, which is new since the last test sweep, and both were silent
wrong answers rather than crashes.

1. **Liquidity sweeps counted a persistent condition as an event.** `detect_liquidity_sweeps` fired
   on *every* bar price was trading beyond a level, with no memory of whether that crossing had
   already been reported. A sweep is a **crossing** — a transition through a level and back — not a
   state. On 6,000 1h bars this produced **1,033,617** "events" from 743 levels, roughly 170
   samples per bar of what is really one crossing. Two consequences: every sweep statistic was built
   on samples that are not independent (which Benjamini–Hochberg cannot repair, because it corrects
   for multiplicity and not for correlation), and the full 1h history could not be analysed at all —
   it died with `MemoryError`. Fixed by tracking whether a level is already beyond the current bar
   and firing only on the first such bar; the flag clears when price returns inside, so a genuine
   second crossing counts again. Same 6,000 bars now yield **9,019** events, and the full history
   completes.
2. **Bootstrap was O(resamples × n) in scalar Python.** `bootstrap_mean`, `paired_difference` and
   `difference_p_value` each ran 2,000 Python loops of `n` `randrange` calls, across ~176
   detector/side/stop/horizon combinations. A pass that should take seconds ran for over 28 minutes,
   and an unbatched vectorised fix would have needed a 1.6 GB index matrix. Vectorised with numpy
   *and* batched (`BOOTSTRAP_BATCH_CELLS`, ~8 MB peak) so memory stays bounded regardless of sample
   size.

   **Reproducibility note:** the resampling method and the fixed seed are unchanged, so intervals
   remain reproducible run-to-run, but the specific resample indices differ from the scalar
   implementation and any interval reported before this change will shift slightly on re-run. The
   tests assert distributional properties — an interval widens with dispersion, a constant sample
   gives a degenerate interval, a sample compared against itself gives exactly zero — rather than
   exact values, so nothing depended on the old draw.

### Event research result (5,000 × 1h bars, 2021-01-01 → 2021-07-28)

11 detector families, 176 tests: liquidity sweeps (n=3,251 high / 3,914 low), BOS (n=639), regime
transitions (n=903), displacement (n=253), volatility expansion (n=201), and the HH/HL/LH/LL and
structure-shift families.

**No event survives multiple-testing correction.** The minimum adjusted p-value is ~1.0, against 8.8
false positives expected at a nominal 5% level. Liquidity sweeps show no edge over the all-bars
baseline at any horizon. **No profitability is claimed for any phenomenon** — this is a null result,
and a useful one: it establishes that the measurement apparatus runs end-to-end and that these
particular events carry no measurable information on this sample.

This is a **5,000-bar slice, not the full 49,642-bar history.** See limitations below.

- **252 tests collected** across the suite at the time of that pass, all passing except
  `test_storage.py`, which aborted inside pyarrow under the memory caps available then and was
  therefore **unverified** rather than known-failing. *It has since been verified as passing; see
  the 2026-10-05 session below.*

### Design decisions worth recording

- **Clamp, don't forbid.** A strategy that asks for more than the ceiling gets a *smaller position*,
  not a rejection. Forbidding outright would make a risk limit indistinguishable from a broken
  strategy, and the resulting run would report zero trades for a reason that has nothing to do with
  the strategy's merit. The clamp is also the honest reading of §12: risk management narrows what a
  strategy does, it does not decide whether it trades at all.
- **An unsized position must not escape the ceiling.** `buy_and_hold` asks for `risk_fraction=1` and
  carries no stop, and fixed-fractional sizing has nothing to spend the fraction against without one.
  Left alone, the ceiling would bind nothing for exactly the most aggressive strategy in the suite.
  Under a risk engine the fraction is therefore read as a direct share of the account committed, so
  `max_risk_per_trade` bounds a stopless position too. The regression test
  `test_buy_and_hold_cannot_escape_the_ceiling` pins the ratio at exactly 0.01.
- **Backtest analogue for stale data; documented gap for exchange disconnect.** There is no live feed
  here for data to go stale on, but a held position whose bars stop advancing is the same failure
  mode in simulation, so `max_stale_bars` is a real control. "Exchange disconnect protection" has no
  analogue at all — there is no connection to drop, since §1.5 forbids one during research — so it
  is documented as out of scope rather than faked with an inert flag.
- **Risk can veto an entry but never a close.** A gate that refused to let a position be exited
  would be actively dangerous. `test_a_close_signal_is_not_gated_by_risk` pins this.

### Bugs found by the Phase 5 test suite

1. **A zero `emergency_stop_loss` halted every run on its first bar.** The sibling drawdown and
   period-loss checks treat a zero limit as "this control is disabled", but the emergency stop
   compared `equity <= initial * (1 - 0)` — true at exactly the starting equity — so the
   "permissive" configuration used to prove the two code paths agree latched a stop immediately and
   returned 21 spurious violations. Now guarded like its siblings.
2. **A stale-data force-exit left no trace in the record.** Every other bound records a violation;
   a stale exit bounded a limit silently, so a run's `risk_violations` could not show which control
   had acted. It now records the reason, matching the reasoning already applied to entry refusals.

### Phase 1–5 Final Hardening: segmented runner, episodes, streaming handoff (session of 2026-10-05)

The remaining structural problem was that the research pipeline was single-shot: `detect_all()` and
`run_research()` each took one full `list[CandleData]`. That is fine at 1h/49k bars and impossible at
5m/198k. The correctness problem underneath mattered more than the speed one — liquidity levels and
the swept-level set are **global**, so chunks cannot be independent and a year boundary genuinely
determines what the next year detects.

The acceptance criterion chosen: **processing the whole history in segments must produce the same
events and statistics as processing it continuously, with bounded memory and no strategy reset at a
boundary.** The boundary is a memory boundary only.

**Delivered**

- `research/streaming.py` — JSON array → `CandleData` iterator via `raw_decode` over a bounded
  buffer, plus segment planning and chunking. Peak memory is a function of buffer size, not of file
  size. The existing dataset file stays the single canonical copy; nothing was duplicated or
  reformatted to Parquet.
- `research/segmented_runner.py` + `scripts/run_segmented_research.py` — incremental structure state
  (level buckets, swings, swept set, regime, 70 bars of trailing close), a pending-outcome buffer for
  events whose forward window crosses the boundary, and atomic checkpoints.
- `research/aggregate.py` — `assign_episodes`, `Episode`, `ClusteredBootstrapper` (both the exact and
  the episode-mean resampling paths), `adaptive_resamples`, and the Phase 11 target grid
  (`OutcomeAccumulator.target_stats`, `TARGET_R_SAMPLE_CAP`).
- `statistics.py` — `clustered_bootstrap_mean(..., method="exact"|"approx")`, and
  `BootstrapResult.{bootstrap_method, n_episodes, statistic_definition, random_seed}`.
- `backtest/monte_carlo_export.py` — batched CSV/JSONL writers, `net_r` canonical with `net_R` as a
  documented compatibility alias.
- `schemas/backtest.py` + `api/routes/backtest.py` — `mode` on the request, refused with a 422
  naming the mode when an ordered mode arrives without risk limits.
- `core/resources.py` — `ResourceLimits`, `/proc` memory reader (no `psutil` dependency), and a
  pre-flight `ensure_disk_space`.

**The episode rule.** Two events are the same experiment iff their forward outcome windows overlap:
`|a - b| <= H`, where `H` is the analysis's own max horizon (12 bars). A single left-to-right sweep
over events in bar order — no clustering library, no tuned constant. **The boundary is `H`, not
`H - 1`:** events `H` bars apart still overlap, because an event confirmed on bar 100 reads
101..113 and one confirmed on 112 reads 113..125. This is pinned by
`test_an_episode_boundary_is_exactly_the_horizon_plus_one_away`.

**Why clustering matters.** A sweep, the structure shift it confirms, and a retest of the same level
are three readings of one move. Resampling them individually reports an interval narrower than the
truth by roughly √(events per episode) — and the point estimate is unchanged, so the error shows up
only in the width. In 2021 that is 731,839 events resting on **7,720 episodes**. `n_episodes` is now
reported alongside `n` on every result, because "measured on 700,000 events" and "measured on 700,000
events drawn from 7,720 episodes" are different claims.

**Three resampling schemes, not one.** The distinction matters because they weight observations
differently, and a reader cannot recover which one produced an interval from the numbers alone:

| `bootstrap_method` | What is drawn | Estimand | Exact? |
|---|---|---|---|
| `event` | individual observations | event-weighted mean | exact for the estimand, **wrong about the uncertainty** when observations cluster |
| `episode_exact` | whole episodes, each drawn episode contributing all of its events | event-weighted mean | yes |
| `episode_mean_approx` | one mean per episode | **episode-equal-weight** mean | no |

The approximation reduces each episode to its mean before resampling, so every episode counts once
regardless of size. That is O(n_episodes) per replicate instead of O(n_events), which is what makes
it usable at 700k events inside this project's budget — but it is a different statistic. An episode of
100 observations and one of 2 get equal weight, so on a sample like "100 events at 1.0, 2 at 0.0" the
approximation's interval is centred near 0.5 while the event-weighted mean is 100/102 ≈ 0.98. The
point estimate is unaffected either way (resampling never moves a mean); it is the interval's subject
that differs.

`method="exact"` is the default. It reduces the events once to per-episode sums and counts, then
builds every replicate as `(d multiplicities @ sums) / (d multiplicities @ counts)` over a bounded
batch — so the resampled sample matches the observed cluster-size distribution and the estimand
stays the event-weighted mean. Measured at 100,000 events over 5,000 episodes with 10,000
resamples: **peak RSS 96 MB**, no `(resamples, events)` array anywhere. The approximation is kept and
reported, but only ever under `episode_mean_approx`, with a `statistic_definition` that begins
`APPROXIMATION:` and names the episode-equal-weight mean. Pinned by
`tests/test_bootstrap_weighting.py`, including a hand-enumerable two-episode case where every
replicate must land on `100k / (100k + 2(n - k))` — a size-dropping implementation could not produce
those values.

Every `BootstrapResult` records `bootstrap_method`, `n_events` (as `n`), `n_episodes`,
`statistic_definition`, `resamples` (as the iteration count) and `random_seed`, so an interval
carries its own provenance rather than relying on the reader to know which code path ran.

### 2021 5m validation run (measured)

One year, 5m, run to completion and then stopped. Treated as resource + correctness validation, not
as a strategy conclusion.

| Measure | Value |
|---|---|
| Bars | 104,923 |
| Events | 731,839 |
| Episodes (independent clusters) | 7,720 |
| Swings / liquidity levels | 13,382 / 12,596 |
| Outcomes labelled | 2,927,356 |
| Segments / checkpoints | 14 / 14 |
| Wall clock | 665.2 s |
| Peak process RSS | 0.32 GB |
| Lowest system-available memory | 6.30 GB |
| Stopped on memory | false |
| Warnings / errors | 0 / 0 |
| Swap activity | none |

Fully self-consistent on re-check: spill count == checkpoint count == 731,839, event log sorted, and
the runner's episode partition identical to a batch `assign_episodes` sweep over the same file
(7,720 clusters, same start indices).

**Verdict on running more years:** safe. Peak process memory is 0.32 GB against a 4 GB project
ceiling, the lowest system availability never dropped below 6.30 GB, and memory did not grow with
bars processed — the segmented path holds a bounded carry state regardless of how many segments come
after. **2022–2026 was not launched**, per the agreed stop condition. Disk cost is ~322 MB of run
output per year of 5m, against a 256 GB budget.

### Bugs found by the segmented runner

Both surfaced only at 5m scale, and both were silent wrong answers.

3. **Episodes were never checkpointed.** Resuming Q1 2021 gave 9,621 clusters against 14,618 for the
   uninterrupted run, with every other figure matching. `_episode_indices` was rebuilt from the
   *resumed* segment alone, so each restart re-drew the partition boundary. The failure reads as
   "a quieter market", not as a bug, which is what made it worth a regression test. Fixed by folding
   episodes incrementally — the carry state is ~7,720 ints rather than 732k — and checkpointing the
   partition itself. `report.episodes` was also counting distinct bars rather than clusters.
4. **A checkpoint claimed more events than the spill could back.** `_write_checkpoint` recorded a
   running tally while `EventSpill` was still buffering in 1,000-event batches, so a hard kill between
   a segment's detection and the next flush left a checkpoint asserting 731,839 events next to a
   spill holding 731,670. A checkpoint is a promise the run is resumable from; a promise the spill
   cannot back is worse than no checkpoint, because it is believed. Now the spill is flushed *first*
   and `events_written` is read from the spill's own count.
   Regression test: `test_a_hard_kill_leaves_no_claim_the_spill_cannot_back`, which patches
   `EventSpill.close` to raise `KeyboardInterrupt`.

### Bug previously recorded as unverified, now verified

`tests/test_storage.py` is reported above as aborting inside pyarrow. It now **passes** — the earlier
failure was memory pressure from concurrent work, not a defect in the storage layer, and no
memory-allocated workaround was needed.

### Test suite

**371 passing**, up from 252. New this session:

| File | Covers |
|---|---|
| `test_segment_equivalence.py` (9) | Continuous == segmented across unequal splits; the episode partition matches a batch sweep; episodes survive an interrupted run; a hard kill leaves no unbacked checkpoint claim |
| `test_episodes.py` (19) | The `H + 1` boundary; `bincount` cluster reduction; peak bootstrap memory bounded by episodes not events; the three precision tiers (1k / 10k / 50k); clustered intervals widen where the naive one does not |
| `test_monte_carlo_export.py` (18) | `net_r` canonical, `net_R` an identical alias; writers stream; header built from the field list; trades with no defined R counted rather than silently dropped; no OHLCV carried |
| `test_streaming.py` (21) | Reader equals a full parse at three buffer sizes including one smaller than a single record; brackets inside strings; truncation and malformed input refused rather than silently short |
| `test_resource_limits.py` (18) | Guard states and their order; system availability checked before process RSS; batch halving with a floor; disk refusal before any work, including against the project budget rather than the filesystem's |

### Design decisions worth recording (this session)

- **Flush, then checkpoint.** Durability ordering is not a detail. A checkpoint written before the
  spill is durable is a claim about a state that does not exist yet.
- **Canonical name plus compatibility alias, not a rename.** `net_r` is canonical because that is
  what the Monte Carlo project is specified against; `net_R` ships alongside it because a consumer
  written against the current schema would otherwise return an empty column, and that failure is
  invisible until a downstream report comes back wrong. The mapping is explicit rather than
  case-insensitive, so renaming either side surfaces as a `None` column instead of a silent
  mismatch.
- **A missing memory reading is `ok`, not `critical`.** Refusing to start because `/proc` could not
  be read would stop the run for a condition that was never observed.
- **The system check has no warning band, deliberately.** `critical_ram_gb` sits above
  `warning_ram_gb` because they threshold two different quantities — the machine and this process.
  So any system reading below the warning line is also below the critical one, and the guard stops
  rather than warning. Warning there would mean telling a job to shrink its batches when the machine
  has under 3 GB left for everything, and shrinking takes several chunks to take effect.
- **The episode-mean approximation is retained, but is no longer the default.** *Previously:* exact
  cluster resampling did not exist, and reducing each cluster to its mean was the only path — cheap,
  and the reason it was usable at 700k events inside this budget, but it silently changed the
  estimand from the event-weighted mean to the episode-equal-weight mean. *Fix:* `method="exact"`
  now defaults to resampling whole episodes with each drawn episode contributing all of its events,
  so only the uncertainty accounts for clustering and the estimand is unchanged. The approximation
  remains available as `method="approx"`, reported under `bootstrap_method="episode_mean_approx"`
  with a `statistic_definition` that begins `APPROXIMATION:` and names the episode-equal-weight
  mean. *Current status:* both paths are batched identically (peak RSS 96 MB at 100k events /
  10k resamples), every result records its own provenance, and
  `tests/test_bootstrap_weighting.py` pins the distinction. What remains true is narrower: the
  approximation is still **an approximation** and must never be reported as the exact statistic.
  The per-mode weighting table is above.

## Current Limitations (Phases 3–5)

These are honest boundaries of what exists today, not a roadmap.

- **No profitability has been demonstrated.** The baselines are controls, not evidence of an edge, and
  the risk engine is a constraint on a result, not a source of one. Per §1.2, risk management cannot
  turn a strategy with negative expectancy into a profitable one. No backtest result from this
  repository should be read as a claim that any strategy works.
- **The risk engine is backtest-only.** It places no orders and contacts no exchange; it is not an
  execution guard and cannot be one while §1.5 forbids a live connection. A control that only exists
  inside a simulation has not been tested against a real feed, real latency, or a real exchange
  rejecting an order.
- **API mode selection was previously unavailable; it is implemented now.** *Previous issue:*
  `BacktestRequest` had no `mode` field and `POST /api/v1/backtests/run` never passed one, so every
  API-created run was recorded as `research` and the ordered-mode enforcement could not be exercised
  over HTTP at all. *Fix:* `BacktestRequest.mode` exists and defaults to `research`; the route passes
  it through and returns `mode` on the response; an ordered mode arriving without `risk_limits` is
  refused with a 422 that names the mode. `enforce_run_mode()` additionally makes `risk=None` an
  error under `simulation` / `paper` / `live` at the engine level. *Current status:* the plumbing is
  complete and the distinction is reachable end to end — **the gap is closed.** What remains
  unproven is not the plumbing but the *content* of those modes: `simulation` is a backtest that
  happens to carry a risk engine, not a feed-driven simulation, so **treat any API-created run as a
  research control, not a tradeable result.**
- **The full-history event analysis has not been run end to end.** 5m segmented processing *is*
  validated — one year ran to completion under the resource caps and is reported above. The open item
  is narrower: the complete 49,642-bar **1h** pass was not run to completion under the memory limits
  that session was held to. The sweep fix and the batched bootstrap both exist specifically to make
  it feasible; that 1h run should be repeated before any conclusion is drawn from those events.
  This is a missing *measurement*, not a missing capability.
- **Event samples are only as independent as the detectors make them.** The crossing fix removed the
  grossest violation, but a level that price retests repeatedly still yields correlated observations,
  and neither Benjamini–Hochberg nor the paired bootstrap corrects for serial dependence within a
  detector. Treat the confidence intervals as optimistic on that account.
- **The regime classifier is unvalidated.** `market_regime` is a label used to slice results, not a
  demonstrated predictive feature.
- **Research market and execution market are not the same venue.** All history and all cost
  assumptions are Binance BTC/USDT. Nobitex spreads, depth, fees and execution behaviour differ, so
  every figure here is an upper bound until Nobitex-specific costs are plugged into the same cost
  interfaces. No live or paper execution exists.
- **Risk defaults remain unvalidated examples.** `1%` per trade, `5%` daily, `10%` weekly, `20%`
  drawdown are configuration illustrations carried over from the spec, not empirically derived
  values. They are deliberately not optimised yet.
- ~~**`backend/tests/test_storage.py` is currently unverified.**~~ — **RESOLVED; it passes.**
  Previously it aborted inside pyarrow under every memory cap that session was permitted to use.
  The abort was memory pressure from concurrent work, not a defect in the storage layer, and no
  memory-allocated workaround was needed. It now passes (2/2) as part of the 401-test suite. See
  "Bug previously recorded as unverified, now verified" below. This limitation is **closed**; nothing
  about storage is outstanding.
- **The sweep and bootstrap fixes changed measured output.** Any event-research result produced before
  this session used a detector with non-independent samples; such results should be discarded and
  regenerated, not compared against new ones.
- **`max_simultaneous_positions` is structurally always 1.** It is accepted and validated for
  forward compatibility, but it cannot bind: the engine holds at most one position and never adds to
  one. Raising it above 1 requires the pyramiding work that remains a limitation below.
- **Every individual limit is still opt-in.** Run mode makes the risk engine *mandatory* outside
  research, but a `simulation`-mode run that configures no limits still has an engine with defaults
  rather than with none — so there is a floor, not a per-control default-deny.
- **Exchange disconnect protection is not implemented.** There is no exchange connection to protect,
  and an inert flag that looks like a control is worse than a documented gap.
- **The weekly loss limit reports under the daily slug.** Both are enforced, but a weekly breach is
  reported as `daily_loss_limit` because the day is the tighter, faster control and a single slug
  keeps the violation list unambiguous. A weekly breach is therefore not distinguishable from a
  daily one in a stored run.
- **Long-only by default.** `allow_short` exists and is recorded, but no short-side statistics have
  been studied. Short results have not been validated as a research finding.
- **Bar-level data only.** Intrabar stop and target resolution is conservative (stop-first on a
  tie), but with OHLC bars the true fill within a bar is unknowable. Tick or trade-level replay
  would be needed to make that claim precisely.
- **Single position, no pyramiding.** The engine holds at most one position and never adds to it.
- **No slippage model beyond a flat rate.** Real impact scales with size and book depth; the current
  model charges a constant rate per side.
- **No walk-forward or out-of-sample validation.** Every figure reported so far is in-sample by
  construction, which is the single largest reason to distrust any of them.
- **CAGR, Calmar, Sharpe, and Sortino are suppressed on sub-30-day windows** rather than reported
  annualised. Long-horizon conclusions require multi-month datasets.

## Next Steps (Phase 6+)

### Immediate Priorities
1. ~~**Ingest a multi-month dataset**~~ — **done.** 2021-01-01 → 2026-08-31 across 5m/15m/1h/4h, with
   a content-hashed manifest (`backend/data/datasets/manifest.json`). Note the 15m and 1h files carry
   7 small gaps (70 and 14 bars respectively); 4h is complete. Gaps are reported, never silently
   filled.
2. **Re-run the full-history event analysis** — the sweep fix and batched bootstrap make it feasible;
   it should be run on all 49,642 1h bars before any conclusion about these events is drawn from the
   5,000-bar slice.
3. **Walk-Forward Validation** - Chronological train/validate/test splits (Phase 14). The single
   largest gap in what this repository currently proves. The event, ledger and experiment-metadata
   interfaces now exist so results can migrate into it without redesign.
4. **Price-Action Strategy Candidates** - Judged against the baselines under identical assumptions,
   and *behind* the risk engine, which must never be bypassed by a strategy or a model. Gated on the
   event research showing something worth trading; the null result so far argues against rushing this.
5. **Risk-parameter sensitivity study** - Re-run each baseline across a grid of limits to show what
   each control actually costs or saves, rather than asserting defaults are reasonable. This is what
   will eventually justify the current unvalidated defaults.
6. **ML Trade Filter** - Logistic regression / XGBoost to filter setups (Phase 13), only after 3–4.
   Whatever it produces routes through `check_entry` unchanged; §12 requires the risk engine to be
   unbypassable by ML, and that constraint is why the filter is Phase 13 rather than Phase 6. Not yet
   started, by design.

### Architecture Considerations
- Extension points for new providers
- Background data collection
- Quality report API/UI
- ~~Dataset manifests for research~~ — done (see priority 1)
- Nobitex-specific cost parameters behind the existing `CostConfig` interface, so the research/execution
  venue split is explicit rather than assumed away. Not yet implemented.
- ~~A `mode` field on `BacktestRequest`~~ — done; `simulation` / `paper` / `live` are reachable over
  HTTP and the route 422s an ordered mode sent without `risk_limits`
- Trades and order books (future)

## Code Quality

### Standards
- Type hints throughout
- Async/await for I/O operations
- Structured logging with correlation IDs
- Comprehensive unit test coverage
- Pre-commit hooks (ruff, black, isort, mypy)

### Project Structure
```
btc-quant-trader/
├── backend/                    # Python backend
│   ├── app/                   # Application code
│   │   ├── core/              # Core infrastructure
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # Data access
│   │   ├── api/              # HTTP/WebSocket APIs
│   │   └── schemas/           # Pydantic models
│   └── tests/                # Test suite
├── frontend/                   # React frontend
│   ├── src/                  # Application code
│   │   ├── components/       # UI components
│   │   ├── charts/           # Chart components
│   │   ├── hooks/            # Custom hooks
│   │   ├── pages/            # Pages
│   │   ├── services/         # API services
│   │   └── types/            # TypeScript definitions
│   └── public/               # Static assets
├── docker/                     # Docker configurations
├── data/                       # Data storage
├── docs/                       # Documentation
├── scripts/                    # Build scripts
└── tests/                      # Cross-platform tests
```

## Validation Commands

Run the full test suite:
```bash
make test
```

Run specific test modules:
```bash
# Backend unit tests
cd backend && python -m pytest tests/ -v

# Provider tests
cd backend && python -m pytest tests/test_binance_provider.py -v

# Validation tests
cd backend && python -m pytest tests/test_validation.py -v

# API tests
cd backend && python -m pytest tests/test_api.py -v

# Backtest tests
cd backend && python -m pytest tests/test_backtest_engine.py -v
cd backend && python -m pytest tests/test_backtest_baselines.py -v
cd backend && python -m pytest tests/test_backtest_costs.py -v
cd backend && python -m pytest tests/test_backtest_metrics.py -v
cd backend && python -m pytest tests/test_backtest_api.py -v

# Risk engine tests
cd backend && python -m pytest tests/test_backtest_risk.py -v
```

Run linting and formatting:
```bash
make lint
make format
```

## Current Phase Status

Each line below is confirmed by the implementation and by the current test run, not asserted.

**Implementation status:** COMPLETE for this phase — infrastructure, research pipeline, statistical
machinery, and risk enforcement. **444 tests passing, 0 failing** across 32 test files.

**Research foundation:** READY FOR STRATEGY RESEARCH. The detectors, episode rule, outcome labelling,
null baselines, and interval machinery are in place and measured. No strategy research has been
performed yet, and no profitability is claimed.

**Current bootstrap default:** `episode_exact` — whole episodes resampled with replacement, each
drawn episode contributing all of its events. The estimand is the event-weighted mean.

**Approximate bootstrap:** `episode_mean_approx`, available as `method="approx"`, documented
separately and never reported as the exact statistic. Its interval describes the
episode-equal-weight mean, which is a different quantity whenever episodes are unevenly sized.

**API mode:** IMPLEMENTED. `BacktestRequest.mode` (default `research`) is accepted and echoed;
`simulation` / `paper` / `live` are reachable over HTTP and are refused with a 422 when they arrive
without `risk_limits`.

**Storage tests:** PASSING (2/2). The earlier pyarrow abort was memory pressure from concurrent work,
not a storage defect; no workaround was needed and the limitation is closed.

**5m segmented processing:** VALIDATED — one year ran to completion under the resource caps. The
open measurement gap is the full-history **1h** pass.

**Resource safety:** VALIDATED. Both bootstrap resampling paths are batched; measured peak RSS is
96 MB at 100,000 events / 5,000 episodes / 10,000 resamples, against a 6 GB hard limit and a
comfortably-under-4 GB target. No `(n_resamples, n_events)` array is built by either path.

**Milestone 7 — Setup Statistical Research (Phase 11):** IMPLEMENTED. Every setup is now measured
against a fixed target grid of **+0.5R / +1R / +1.5R / +2R**, all four resolved in a single pass
over the same bars, and reported per family (detector × kind × side × stop model) as: sample size,
win rate, loss rate, ambiguous count, unresolved count, average R, median R, mean bars-to-target and
mean bars-to-stop. The grid is in both the batch report (`analyze_family` / `FamilyReport.targets`,
rendered as a Markdown table with its denominators and footnotes) and the segmented checkpoint.

Three properties this measurement deliberately does not smooth over:
- **Win and loss rates are over *resolved* outcomes only.** A bar containing both the target and the
  stop is unorderable from OHLC; it is counted as `ambiguous`, not as a loss. A target the price never
  reached inside the horizon is `unresolved`, not a loss — that is a different claim.
- **The four targets are four different populations.** `n` rises and falls across the grid, so the
  win rates are not comparable without it, and are never averaged together.
- **Median R is the one number a resumed run cannot restore.** The R sample is a capped per-cell list
  (20,000 values, reservoir-by-threshold), not a moment, so it is not serialised. A resumed run
  reports `median_r: null` with `median_truncated: true` rather than the median of its own tail.
  Win/loss counts, `average_r` and both time moments resume exactly — verified against an
  uninterrupted run.

**Measured on real 5m data** (2021-01-01 → 2021-04-01, 25,887 bars, 67,017 events, 268,068 outcomes,
1,808 episodes, 7-day segments): no family at any target shows a positive average R that survives its
own denominator. The strongest cell is `sweep:swing_low / liquidity_sweep / short / atr_1.5` at +1R —
51.4% win rate, **+0.028R average**, which is indistinguishable from the null and two orders of
magnitude below any tradeable edge. This is a measurement of what these detectors do, **not** a
finding that they work.

**Resource safety of the grid:** the target buckets are bounded by (families × targets). A full
3-month segmented run measured **96 MB peak RSS** and **32 MB of spill**, against a 6 GB / 256 GB
budget.

**Milestone 6 — Price Action, Part 1 (Phase 8: Compression):** IMPLEMENTED and VALIDATED. A gap audit
against the main specification was done before any code, reading the repository rather than these
notes. It found Milestone 6's remaining bullets: **compression was entirely absent**, displacement
was under-measured, and Phases 9 (zones/retests) and 10 (setup engine) had no code at all. This
entry covers only the first genuinely incomplete dependency — compression and the displacement
measurements it needs — and stops there.

`detect_compression` emits a coil-and-release event with an objective definition, not a chart
judgement:
- `compression_ratio` = trailing `volatility_5 / volatility_20`, both on the *same*
  `_realized_volatility` that `detect_displacement` uses. Sharing the definition is the point: a
  compression and the displacement that ends it are only comparable if they measure "quiet" the
  same way, and two private definitions would make them incomparable by construction. Pinned by
  `test_compression_and_displacement_agree_on_what_volatility_is`.
- Volume must also dry up (`volume_ratio <= 0.8`). A contraction on rising volume is distribution,
  not coiling.
- Features recorded: `compression_ratio, range_5, range_10, range_20, volatility_5, volatility_20,
  range_zscore, volume_zscore, volume_ratio, release_range, release_expansion, atr_normalized_move`.
- `confirmation_index == event_index`. The release bar's range is final at its close and every window
  is trailing, so there is no bar to wait for — inventing a lag would misdescribe when the
  information exists.

`detect_displacement` gained the four measurements Phase 8 names and it lacked:
`range_zscore, return_zscore, volume_zscore, atr_normalized_move`. The existing
`magnitude_in_volatility` stays — it is the gate, a ratio to a volatility estimate; the z-scores are
distances from the market's own recent *distribution*, which is a different question. All reference
windows **exclude the bar being scored**: a population containing the bar shrinks toward the mean by
an amount that grows with the window, so a 50-bar window would systematically report weaker
displacement than a 20-bar one on identical price action, and the report would be comparing them.
Pinned by `test_the_zscore_window_excludes_the_bar_being_scored`.

Three properties deliberately not smoothed over:
- **No z-score over a zero-spread population.** Twenty identical bars have a standard deviation of
  exactly zero; returning 0 would file a dead-flat stretch as "average" and a large number would file
  it as "extreme". `_zscore` returns `None`.
- **A release is compression's *end*, not a displacement of its own.** The detector stops at the
  release and does not carry `magnitude_in_volatility` or `body_ratio`; claiming the move as well
  would count one bar in two families with nothing to distinguish them.
- **A state is not an event.** A contraction that never ends emits nothing, and a coil that runs
  longer than the trailing window reports a `start_index` truncated to the prefix — which affects
  `duration_bars` only, never which bar the event lands on.

**Two latent bugs found by the audit and fixed**, both in code this work builds on:
- `events.py` marked a level `swept` *before* testing penetration against `min_penetration`, so a
  level rejected for insufficient penetration was suppressed for the whole excursion and could never
  be swept by a deeper bar either — silently, since the resulting non-event is indistinguishable from
  a level that was never near.
- `_sweep_event` was called with a hardcoded `"swing_high"` / `"swing_low"` instead of
  `level.level_type`. Latent only because every derived level so far happens to be a swing; it would
  have become wrong the moment an equal-highs or session level was derived.

**Validated:** 26 new tests in `test_research_compression.py` plus additions to
`test_research_events.py`, `test_sweep_windowing.py` and `test_segment_equivalence.py`. Causality is
asserted by the prefix-invariance audit both through the package's `DETECTORS` table and on a
fixture where a mutated 50-bar future is required to leave every earlier event byte-identical. The
segment-equivalence baseline was **extended to include compression** — it was sweeps-only, so it
would have kept passing on a runner that had lost every compression event while the sweep cells
agreed.

**Measured on real 5m data** (2021-01-01 → 2021-04-01, 25,887 bars, 7-day segments, 13 segments):
68,129 events (67,017 sweeps + **1,112 compressions**), 1,847 episodes, 272,516 outcomes,
**55.6 s wall, 92.8 MB peak RSS, 32 MB spill**, 0 warnings, 0 errors. Segmented and whole-series runs
were compared over the same data and produced **identical totals and byte-identical cells**. Every
`median_r` across all 48 target cells is a value the population can actually take.

**What this is not:** no claim that compression is predictive. The strongest compression cell
(`long / atr_1.5`) is −0.012R at +0.5R and −0.32R at +2R over 713–1,084 resolved events. Those are
measurements of what a compression release does after the fact, on one instrument over three months,
with no multiple-testing correction applied to the choice of stopping at that cell.

**Resource safety:** the compression detector holds no state across segments and no per-event
structures beyond the segment's own list; it re-derives from `self._tail + bars`, so a run's memory
is unchanged by its presence (92.8 MB before and after, against a 6 GB limit).

**Remaining in Milestone 6:** Phase 7 is still partial (2 of 10 level types derived; 2 of 9 sweep
fields recorded — `penetration_percent`, `time_above/below`, `recovery_ratio`, `wick_ratio`, `volume`,
`volatility`, `structure_context` are absent, and `equal_highs/lows`, `range_high/low`,
`session_high/low`, `previous_day_high/low` are declared in the enums but never derived). Phase 9
(zones, retests) and Phase 10 (setup engine) have no code. Those are the next dependencies, in that
order, and the setup engine depends on zones and retests existing first.

**Remaining work:** actual strategy research and validation — choosing candidate strategies,
measuring them against the null baselines, and applying Benjamini–Hochberg across whatever that
produces. Everything in the "Current Limitations" section above is still true unless explicitly
marked resolved; this section is a summary, not a replacement for it.

Apply migrations:
```bash
make migrate
```

## Project Philosophy

### Research-First Approach
- Build infrastructure before strategies
- Test hypotheses with historical data
- Maintain reproducibility
- Document everything
- No profitability claims

### Safety First
- Clear boundaries between research and execution
- No hardcoded trading assumptions
- Configurable risk controls
- Comprehensive logging and monitoring

### Quality Assurance
- Automated testing
- Data validation and quality reporting
- Persistent evidence of all decisions
- Review before progression to next phase