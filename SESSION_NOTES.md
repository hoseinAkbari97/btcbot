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

**Milestone 7 — Setup Statistical Research (Phase 11):** **SETUP-STATISTICS INFRASTRUCTURE
IMPLEMENTED AHEAD OF DEPENDENCIES.** Every setup is now measured
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

**Scope of the claim:** this measures *setups that the setup engine emits*. That engine does not
exist yet (Phase 10, no code). So this is a measurement of the machinery, not of setups — the
correct wording is **setup-statistics infrastructure implemented ahead of dependencies**, and
**actual setup statistical research is NOT STARTED**. What follows describes the machinery's
behaviour on the only inputs available today, which are the liquidity and compression families.

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

**Remaining in Milestone 6:** **Phase 7 (liquidity model) is now COMPLETE** — all 10 level types are
derived and all 9 sweep measurements are recorded; see the Phase 7 entry below. Phase 9 (zones,
retests) is now COMPLETE — see the Phase 9 entry below. Phase 10 (setup engine) has no code.

### Phase 7 — Liquidity Model: IMPLEMENTED and VALIDATED

**IMPLEMENTED.** All **10** level types are derived (the two swing types were the only ones before
this work) and all **9** sweep-record measurements are computed. The specification named the ten
types and the nine fields without defining either, so what follows is the *definition chosen* for
each — deterministic, parameterised, causal, and deliberately not fitted to BTC. These are
definitions, not strategy parameters: `SESSION_HOURS = 6`, `DEFAULT_RANGE_WINDOW = 20`,
`EQUAL_MIN_SWINGS = 2` and the equal-cluster tolerance are fixed by the meaning of the words, and no
test here asserts that changing one improves anything.

**Ambiguous concepts, decided explicitly** (each has a synthetic test in `test_derived_levels.py`):

- **Sessions** are six-hour blocks aligned to midnight UTC — `session_00/06/12/18` — so a day tiles
  exactly into four with no gap and no overlap, and every boundary is at a fixed bar index.
  Asserted by `test_a_day_has_exactly_four_sessions_and_no_gap_or_overlap`.
- **A session/previous-day level is the extreme of the *same* slot on a previous occurrence**, never
  of the period in progress. A period's extreme is not complete until its last bar closes, so the
  level published at a boundary holds the *previous* occurrence. This is the headline distinction
  from the rolling family and is asserted by
  `test_a_session_level_never_carries_its_own_sessions_extreme`.
- **Range high/low** is the extreme of a trailing 20-bar window **excluding** the bar being consumed;
  the level is published on the following bar. `creation_index` is the window's last bar and
  `creation_time` that bar's close. A level containing the bar it is compared against would have its
  own price depend on that bar.
- **Equal highs/lows** require `EQUAL_MIN_SWINGS = 2` swing confirmations inside one cluster. One
  swing is not an equal anything. The level is dated to the *second* confirmation's time while
  `first_seen` keeps the *first* swing's — the disagreement between them is exactly what
  `level_age_bars` reports.
- **Tolerance for equality** is a *relative* band (`price/(1±tol)`, default 0.001) applied by the
  bucket builder in `analysis.py`. `equal_level_for()` does **not** re-check it: membership is
  decided where the swings are clustered, and a second check there comparing a swing's price to the
  bucket's own anchor could never reject anything. The contract is documented and tested as
  *membership is decided by the bucket*, rather than a second filtering rule being invented.
- **Merging:** levels are identified by `(creation_index, level_type, price)` — identity, not price.
  Two levels at the same price with different creation indices are different facts and both can be
  swept; a bar and a price report exactly **one** sweep, under the most specific level at that price
  (`LEVEL_SPECIFICITY`: equal 2 > range/session/previous-day 1 > swing 0), then the most recently
  created. Asserted by `test_a_co_located_sweep_is_reported_once_not_once_per_level`.
- **Lifecycle:** a level stays active after being swept. It is *disarmed* while price remains beyond
  it and re-arms when price trades back inside. Crossing → back inside → crossing again is **two**
  events; a two-bar-long excursion is **one**. Both halves asserted, because asserting only one
  passes on a detector that marks a level swept forever.
- **Availability**, per family: a *rolling range* level completes at the close of its window's last
  bar; a *calendar* level (session, previous day) completes at the boundary that ends its period,
  which is the **open** of the bar that publishes it. Both are never later than the close of the bar
  whose index they carry. Documented per type in the module docstring and asserted by
  `assert_no_self_sweep` plus `test_a_level_is_dated_to_the_instant_its_information_completed`.

**The nine sweep measurements, defined.** Each is `None` when its definition does not apply to the
bar, rather than a fabricated number; a zero would be a claim about a bar that never moved.
`penetration = (high − level)/level` for a high swept from underneath, `(level − low)/level` for a
low; `penetration_percent = penetration × 100`. `time_above` / `time_below` count bars whose **close**
sat on each side of the level — closes, not wicks, because the question is whether price was
*accepted* out there, and a wick through a level that closed back is the definition of a sweep.
`recovery_ratio = |close(confirmation) − level| / |extreme(pierce) − level|`: how much of the move
past the level was given back, settled at the confirmation close. `wick_ratio = (pierced side past
the level) / (high − low)`. `volume` is the pierce bar's volume. `volatility` is the shared trailing
`_realized_volatility(before, last, 20)`. `structure_context` names whether a break of the same side
occurred within 100 bars, or `None` if the lookback has no data.

**Event timing is unchanged and correct:** `event_index` is the pierce bar, `confirmation_index` is
the *next* bar, always — asserted by `test_a_sweep_is_confirmed_exactly_one_bar_after_the_pierce`.
On the final bar present the confirmation falls back to that bar rather than naming one that does not
exist. No incorrect event definition was preserved.

**VALIDATED.** 18 tests in `test_liquidity_causality.py` plus 19 in `test_derived_levels.py`. §7's
required properties are each asserted in a form that fails for a *distinct* reason: **prefix
invariance** at four truncation points; **future mutation** (the tail rewritten to an extreme, with
the pre-tail events required byte-identical); **confirmation timing**; **duplicates** (no repeated
level identity, one sweep per bar-and-price, one level type per event); and **lifecycle** (the
swept/re-armed pair above). Plus **segment equivalence** at segment sizes 1, 7, 50, 288 and **checkpoint
round-trip**, both in `test_derived_levels.py`.

**MEASURED on real 5m data** (BTCUSDT, 2021-01-01 → 2021-04-01, 30-day segments, 4 segments):
25,887 bars, **269,470 events** (268,358 sweeps + 1,112 compressions), 16,767 levels, 3,295 swings,
1,930 episodes, **1,077,880 outcomes**, **0 warnings, 0 errors**.

Sweeps by level type — every one of the ten fires on real data:

| level type | sweeps | | level type | sweeps |
|---|---|---|---|---|
| `range_low` | 123,589 | | `swing_low` | 4,396 |
| `range_high` | 121,912 | | `swing_high` | 3,679 |
| `session_high` | 5,850 | | `previous_day_low` | 1,019 |
| `session_low` | 5,169 | | `previous_day_high` | 1,004 |
| | | | `equal_highs` | 972 |
| | | | `equal_lows` | 768 |

By side: 134,941 low, 133,417 high — no side is starved. The two `range_*` families dominate, which
is expected and not a finding: a 20-bar extreme moves far more often than a daily boundary does, so it
is published far more often. It is a statement about *how often a level is republished*, not about
which levels are worth trading. `time_above` / `time_below` are `null` on 38 events — those are the
final-bar sweeps, where the confirmation bar the count is defined over does not exist. Every other
measurement is populated on every event.

**Segmented == continuous: VERIFIED on this exact range.** A whole-series run over the same 25,887
bars produced **269,470 events, 16,767 levels** and an event-identity multiset **equal** to the
segmented spill's (36,960 distinct identities, zero difference), and an outcome accumulator with
**identical totals** (1,077,880, 604 truncated) and **0 of 44 cells differing** — barriers,
excursions, targets, and every horizon's `n` and `mean` matched.

**Resource usage: within budget.** Segmented run **291.7 s, 0.34 GB peak RSS** (0.34 GB self-reported,
0.36 GB observed externally) against a 4 GB target / 6 GB ceiling; **186 MB spill + 6.2 MB checkpoint**
on disk against a 256 GB ceiling. Full suite: **483 tests, 0 failures, 804 s user / 13:24 wall,
539 MB peak RSS**. The continuous comparison run, which by construction holds the whole window in
memory, peaked at 2.36 GB — still inside the ceiling, and it is only affordable because this is a
three-month window; the full history uses the segmented path.

**NOT RESEARCHED.** No liquidity definition has been evaluated for profitability, and none will be as
part of this work. The correct question — *can we define and measure liquidity objectively without
future leakage?* — is answered yes and demonstrated above. The question *which liquidity definition
makes money* is a later question requiring the setup engine, which does not exist.

**Remaining Phase 7 limitations.** (1) The parameters are defensible but not the only defensible ones;
a different session length or window would be equally valid and would produce different counts, so the
numbers above are properties of *these* definitions. (2) `equal_highs`/`equal_lows` membership depends
on the bucket builder's clustering, which has no test of its own against a hand-built cluster — only
against the function that consumes it. (3) Levels are never explicitly *expired*; activity is bounded
only by the swept/re-armed state, so a very old level can still be swept years later, and
`level_age_bars` is the only record of that. (4) `structure_context` is a single label within a
100-bar lookback, not a graded measure.

**Next dependency: Phase 10 — Setup Engine.** Phase 9 exists and is tested; Phase 10 (combining
Phase 7 (liquidity model), Phase 8 (compression), and Phase 9 (zones + retests) into candidate
setups: liquidity sweep + rejection, liquidity sweep + structure shift,
compression + breakout + retest, displacement + retest, higher-timeframe zone + lower-timeframe
structure confirmation) has no code.

**Remaining work:** actual strategy research and validation — choosing candidate strategies,
measuring them against the null baselines, and applying Benjamini–Hochberg across whatever that
produces. Everything in the "Current Limitations" section above is still true unless explicitly
marked resolved; this section is a summary, not a replacement for it.

### Phase 9 — Supply / Demand Zones and Retests: IMPLEMENTED and VALIDATED

**IMPLEMENTED.** A full implementation exists in `backend/app/services/research/zones.py` (1109 lines)
with 34 passing tests in `backend/tests/test_research_zones.py`. The implementation predates this
documentation update and was built as the causal dependency for Phase 10 (setup engine).

**Zone definition.** A zone is a rectangular price band derived from three causal ingredients:
(1) a base — the bars immediately *before* the displacement bar; (2) a displacement — the departure
candle with `magnitude_in_volatility` from `detect_displacement`; (3) structural significance — a
confirmed swing (lookback-confirmed) in the direction of the move near the base. The zone's
`high`/`low` are the exact extremes of the base bars — no rounding, no buffer.

**Three timestamps, deliberately not two.** `ResearchEvent` carries `event_index` and
`confirmation_index`. A zone adds `start_index` (first base bar). A zone is not published before
its `confirmation_index`, which is the later of the displacement's confirmation and the structural
swing's confirmation. The first legal retest is the first bar at or after `confirmation_index`.

**Lifecycle.** `fresh` → `mitigated` (touched) → `invalidated` (close deeper than
`max_touch_depth` fraction into the band) or `expired` (older than `max_age_bars`). A retest
increments `retest_count` and moves the zone to `mitigated`; it never returns to `fresh`. Both
terminal states are truly terminal: one invalidation per zone, not one per crossing.

**Touch vs invalidation.** Depth is measured from the bar's *range* (how far in came); invalidation
from the bar's *close* (how far it stayed). A long wick into a zone that closed back out is the
rejection the concept is named for, not a death.

**Clearing.** Price must be *clear* of the zone (close beyond the departure-side boundary) before a
retest is legal. Without this, a zone emits retests on bars that are part of its own construction —
on real data this was worth 38k phantom retests over 937 zones.

**Retest separation.** `min_retest_separation_bars` (default 3) suppresses repeated retests on
oscillating price. A bar touching a zone too soon after the previous one is recorded as a touch but
does not emit a retest event.

**Overlapping zones.** Two zones from different displacements may overlap and are left unmerged. A
bar entering two overlapping zones produces two retest events with different `zone_id` values.

**Carried state.** `ZoneCarried` survives segment boundaries, keyed by structural identity
`(creation_index, zone_type, low, high)` rather than `id()`. It carries open zones, pending zones
(confirmation bar not yet printed), `last_retest_index` for dedup, and `cleared` set. Checkpoint
round-trip is lossless.

**Causality.** No future leakage: the zone's boundaries are fixed at creation; `confirmation_index`
is never earlier than all three ingredients are knowable; outcomes are measured from
`confirmation_index`, not `event_index`. Prefix-invariance asserted by
`test_prefix_invariance` in `test_research_zones.py`.

**Validated:** 34 tests covering:
- Fixture hand-built with known zone boundaries, creation/confirmation times
- Retests before and after confirmation (first touch vs valid retest)
- No future leakage, including prefix-invariance at four truncation points
- Zone invalidation and expiration
- Overlapping zones with independent touch counts
- Duplicate suppression (oscillating price)
- Lifecycle carries across segment boundaries
- Checkpoint round-trip (payload serialization)
- `detect_all` includes both `zone` and `zone_retest` kinds
- Events round-trip through `to_payload`/`from_payload`

**NOT RESEARCHED.** No zone has been evaluated for profitability. The question *do zones have
predictive value?* is a Phase 11 question. This module measures what a zone is and when it is
touched — nothing more.

**Remaining Phase 9 limitations.** (1) Zone boundaries are fixed at creation and never revised — a
zone that should have been wider or narrower was created too narrowly or too widely with no
opportunity to adjust. (2) `max_touch_depth` is a fixed fraction, not calibrated against the
instrument's typical wick ratios. (3) A zone's `confirmation_index` can lag the displacement bar by
a variable amount (swing confirmation delay), which means a retest window can be shorter for zones
near segment boundaries. (4) Zones that remain open at end-of-data are not explicitly marked; they
simply stop being updated.

**CORRECTED BY THE 2026-10-13 AUDIT.** The Phase 9 entry above was written from
the code and its tests rather than from a segmented run, and the implementation it
describes did not survive either check. Five defects were found and fixed; the
entry's claims about segmentation equivalence and bounding state were false.

### Audit of 2026-10-13: five defects in the zone/sweep path, all fixed

Every one of these lived in the code path that only executes when `offset > 0`,
which is every segment after the first in a segmented run. **Every existing unit
test ran at `offset == 0`**, where the window *is* the series, so a window-local
index and an absolute index are the same number and each defect was invisible to
them. That is the general lesson and it is now enforced: the zone tests below all
construct windows at a non-zero offset.

1. **`_build_zone` indexed the window with absolute indices.** `start` and `index`
   were converted to absolute and then used to read `candles[start]` /
   `candles[index]` anyway. At `offset == 0` harmless; above it, either an
   `IndexError` or a plausible candle from the wrong bar. Fixed by converting in
   one place at the boundary and reading `candles` with window-local indices
   throughout.

2. **The creation gate silently dropped most zones after the first segment.**
   `if not (offset <= index < len(candles))` compared a *window-local* `index`
   against the *absolute* `offset`. At `offset == 0` it accepts everything. At
   `offset == 9` it rejects every bar below local index 9 — which, in a window of
   tail-plus-segment, is most of the segment's own new bars. Verified against the
   pre-fix source on a repeating fixture: the whole series reports zones at bars 8
   and 17, the broken segmented run reports only bar 8. The consequence was not a
   crash but a run that quietly under-reports, which reads exactly like a detector
   that found less. Suppressing the prefix is a question of identity, not index
   arithmetic, and is now handled by the two structural-key checks.

3. **The lifecycle walk replayed prefix bars, corrupting carried zone state.**
   `touch_count`, `first_touch_index` and `last_touch_index` are increments, so
   re-applying bars a previous segment had already applied silently inflated them.
   Measured on a hand-built fixture: `touch_count` 4 where the whole series says 3
   — and the retest count coincidentally matched, because
   `min_retest_separation_bars` happened to suppress the replayed retest. A match
   on the number a reader would check, produced by luck rather than correctness.
   Fixed with a per-zone `applied_through` watermark, advanced before any branch
   can `continue` so a bar is applied at most once on every path.

4. **Terminal zones were never pruned, so the checkpoint grew without limit.**
   A terminal zone can never emit or change again, but every one was retained
   forever. Measured on real data before the fix: after 6,000 bars the carried
   state held 255 zones of which **3 were open**, 212 KB. Extrapolated to a
   multi-year run that is a checkpoint written at every segment boundary and
   growing with the length of the run — the exact resource profile this project is
   not allowed to have, and a direct contradiction of the module's own docstring.
   Fixed by `ZoneCarried.prune`, with a `max_age_bars` horizon rather than an
   immediate delete so a run resuming shortly after a zone ends can still report
   *how* it ended. After the fix: 27 retained zones, 23.5 KB.

5. **Deferred sweeps were re-dated but not re-measured.** Unrelated to zones, and
   found while validating the zone fix: a sweep on a non-final window's last bar is
   parked in `SweepCarried.pending` and re-emitted by the next window — the first
   place its confirmation bar exists. Three measurements depend on that bar, and
   they were computed in the window that could not see it, with the confirmation
   clamped back onto the pierce bar by `min(index + 1, len(candles) - 1)` — the
   *window's* length standing in for the series' length. The replay then patched
   only the index, time and price, so `time_above`, `time_below` and
   `recovery_ratio` described a bar the reader never saw them describe.
   **38 of 268,358 sweep events** differed from a continuous run in exactly this
   way — one per segment boundary — while every aggregate still matched, because
   38 rows out of 268,358 move no mean enough to notice. Fixed by taking the
   confirmation bar as an explicit argument, and by re-measuring the deferred
   event rather than replaying it blind. Reconstructing the excursion denominator
   from `penetration` is algebraically equal and numerically not, so
   `pierce_excursion` is now carried explicitly; that round-trip was moving the
   28th decimal place on 9 events, which is fatal to an equality check.

**Verification.** Each fix has a regression test that was confirmed to **fail
against the pre-fix source and pass after it** — re-introducing each defect in a
temporary copy of the file and running the suite, rather than trusting that a new
test is load-bearing. The `test_terminal_zones_are_pruned...` test was itself
tautological when first written (it passed with pruning disabled) and was rewritten
to drive the real detector; noted because a test that cannot fail is worse than no
test.

**Full suite: 527 tests, 0 failures** (was 483 before the zone work, 526 at the
first audit pass, and one transient failure at 526 that did not reproduce in two
subsequent full runs — recorded rather than rounded away). Peak RSS 513 MB against
the 6 GB ceiling.

### Validation after the fixes (BTCUSDT 5m, 2021-01-01 → 2021-04-01)

25,887 bars, 30-day segments, 4 segments, 0 warnings, 0 errors.

| | value |
|---|---|
| events | 273,901 |
| — sweeps | 268,358 |
| — compressions | 1,112 |
| — zones / zone retests | 1,192 / 3,239 |
| episodes | 1,946 |
| levels published | 16,767 |
| outcomes | 1,095,604 (624 truncated) |
| runtime | 240 s |
| peak RSS | 0.35 GB self-reported / **377 MB observed** (`/usr/bin/time -v`) |
| spill | 197 MB `events.jsonl` + 6.3 MB checkpoint |
| zones in checkpoint | **27 retained / 23.5 KB** (bounded, see defect 4) |

**Continuous == segmented: exact.** A whole-series run over the same 25,887 bars
produces a **byte-identical event list** — 273,901 rows, every field, *including
output ordering*, across all 13 detector families — and an outcome accumulator with
identical totals and 52/52 cells equal. This is a stronger result than the
previously recorded one, which compared the segmented spill against itself.

Getting there took three rounds, and the sequence is the useful part:

| comparison | rows differing |
|---|---|
| first attempt | 38 (`time_above`, `time_below`, `recovery_ratio` wrong) |
| after re-measuring the deferred sweep | 9 (`recovery_ratio`, 28th decimal) |
| after carrying `pierce_excursion` | **0**, and ordering equal too |

The middle row is the one worth remembering: the first fix was *correct in
substance* and still failed, because `level * (1 + penetration)` is algebraically
equal to `|extreme - level|` but not numerically equal. A value recomputed across a
segment boundary is a value that can drift, and "equal to within rounding" is not
equal — it is the state in which a real difference hides.

### Reconciling 269,470 vs 36,960 (previously flagged as a discrepancy)

These are **different units**, and neither was wrong:

- **269,470** — event *rows* in the spill (sweeps + compressions). A bar can sweep
  many co-located levels at once: up to **300** sweeps on one
  `(detector, bar)`, because one wick can pierce many range levels.
- **36,960** — distinct `(kind, detector, event_index, confirmation_index)`
  tuples: 35,848 sweep identities + 1,112 compression identities, zero overlap.
- **16,767** — level identities published over the run (`creation_index`,
  level type, price).
- **1,946** — episodes, the clustering unit the bootstrap resamples.

The useful statement is the ratio, not the totals: **268,358 sweep rows across
only 35,848 distinct `(detector, bar)` identities — 7.49 rows per identity**, and
18,833 distinct bars carry at least one sweep. Any statistic computed per *event*
is therefore computed over heavily repeated observations, which is exactly why the
bootstrap's default resampling unit is the **episode** and not the event.

### Event dependence: measured, not asserted

This was the open question from the previous session ("range-high and range-low
events make up a very large fraction of all sweep events — determine whether
rolling-window levels are being repeatedly republished"). Measured:

- `range_high` + `range_low` are **91.5%** of all sweeps (245,501 of 268,358).
- They are the *only* families with heavy within-bar multiplicity: 12.54 and 11.79
  rows per `(detector, bar)` identity, versus 1.04–1.63 for every other family.
- Median gap between distinct `range_low` bars is **2 bars**; p10 is 1.
- Sweeps of levels older than the entire 25,887-bar window: **0.0%** for every
  family. Median level age at sweep is ~2,292 bars (median `range_low` 2,267).

So the concern is real and now quantified: a rolling 20-bar extreme is republished
far more often than a daily boundary is, and the resulting events are strongly
dependent — but the dependence is **temporal clustering within a bar-and-price
identity**, not republication of one level object. Levels are append-only and
never re-published at a moved price, so a "level" in the identity sense is distinct
each time. The correct unit for inference remains the episode, which is what the
bootstrap already resamples. **No correction to the detector is implied** — this is
a property of what a rolling-window extreme *is*.

### Level expiration: absent by design, and now measured rather than assumed

The previous session recorded as a limitation that levels are never explicitly
expired. It is still absent, and the audit **deliberately did not add it**, because
doing so would silently change every measurement already in this document and the
specification is silent on the point. What the audit did instead was quantify the
consequence, so the choice is informed rather than merely noted:

| detector | n | median age at sweep | p90 | p99 | max |
|---|---|---|---|---|---|
| `range_low` | 123,589 | 2,267 | 6,669 | 10,121 | 11,145 |
| `range_high` | 121,912 | 2,310 | 6,713 | 10,241 | 11,189 |
| `session_high` | 5,850 | 2,380 | 7,020 | 10,323 | 10,918 |
| `swing_low` | 4,396 | 1,814 | 6,085 | 10,170 | 10,835 |
| `equal_lows` | 768 | 1,201 | 5,658 | 7,874 | 7,990 |
| all sweeps | 268,358 | 2,292 | 6,682 | 10,184 | 11,189 |

**No sweep in this run is of a level older than the run itself**, and the maximum
age observed is 11,189 bars (~39 days on 5m) against a 25,887-bar window. So on
this evidence the missing expiry policy changed nothing measurable — but that is a
statement about *this window*, not a property of the code. Over a multi-year run
the age distribution would extend, and whether a 6-month-old swing high is still a
"liquidity level" is a research question, not an implementation detail.

**Recommendation, not implemented:** add a configurable `level_max_age_bars` and
report outcomes both with and without the cap, so the effect is visible rather than
assumed. Making it a silent default would mean every historical number in this
document no longer describes the code.

### Still open after this audit

1. **`structure_context` is one label in a 100-bar lookback**, not a graded
   measure — unchanged, and it discards information (how many breaks, how recent).
2. **Equal-high/low membership has no test against a hand-built cluster.** The
   bucket builder's tolerance boundary is exercised only through the function that
   consumes it. Named as limitation (2) in the Phase 7 entry and still true.
3. **The 38-event boundary bug was invisible to the aggregate comparison.** The
   aggregate cells matched while 38 event rows were wrong, because the aggregates
   are means over ~10⁶ outcomes. This is a property of the equivalence tests
   themselves, not a one-off: aggregate equality cannot detect sparse per-event
   corruption. The event-level byte-comparison added above is what caught it, and
   it should be the primary equivalence check going forward.
4. **Full-history 1h pass still not measured** — unchanged.
5. **No zone or retest has been evaluated for predictive value**, and none is
   claimed. Zones/retests are measurement infrastructure, like the rest.

### Generated research output: retention

`backend/data/research/` currently holds **1.15 GB** across four run directories
(`liquidity-q1-2021` 184 MB, `run-2021`/`run-2021b`/`run-2021c` 322 MB each).
All four are covered by `.gitignore` (lines 43 and 56) and none appears in
`git status`, so a `git add -A` cannot sweep them into a commit — verified, not
assumed.

`run-2021b` and `run-2021c` are byte-for-byte re-runs of `run-2021` kept from
earlier debugging and are **safe to delete**; they are regenerable from the
dataset. Nothing in this session wrote into `backend/data/` — the audit's
validation runs went to `/tmp`. Recommend deleting `run-2021b` and `run-2021c`
unless they are being kept as a deliberate reproducibility cross-check; if they
are, that intent should be recorded here rather than left implicit.

Apply migrations:

### Milestone 2 (2026-10-14): equal-level clustering, expiration, measurement contract

Baseline re-verified before any change: **527 tests, 0 failures**; segmented run
over BTCUSDT 5m 2021-01-01 → 2021-04-01 reproduced at 273,901 events / 1,946
episodes / 16,767 levels.

#### Two defects in the equal-level bucket builder

The clustering rule had no test of its own — coverage reached it only through
`equal_level_for`, the function that *consumes* clusters. Writing the missing
tests found two real defects, both in `extract_liquidity_levels`.

**1. The tolerance boundary was decided by IEEE-double representation error.**
The membership test compared `float` prices: `abs(price - anchor) > tolerance`.
The error's **sign depends on the magnitude**, so the verdict on a pivot sitting
exactly at the tolerance was an artefact of the price level:

| anchor | `abs(anchor+0.001 - anchor)` in float | verdict |
|---|---|---|
| 100 | 0.0010000000000047748 | rejected |
| 1,000 | 0.0009999999999763531 | admitted |
| 30,000 | 0.0010000000002037268 | rejected |

The stated rule is inclusive (`>` rejects, `==` admits), so at a BTC quote the
boundary was on the wrong side of the test purely by representation. Fixed by
comparing `Decimal` prices. **Real-data neutral** on this window — 38,524 levels
before and after, identical by type — because no real cluster member happens to
sit exactly on the boundary. It is a correctness fix that current prices do not
exercise, not a no-op.

**2. The price index excluded a bucket sitting exactly on its upper edge.**
`bisect_left(by_price, (high, -1))` stops *before* an entry whose price equals
`high`, while the membership test admits that case. The comment claimed the two
"cannot disagree about a boundary case"; they did, from opposite sides. Fixed
with an inclusive sentinel. **Currently unobservable and honestly labelled as
such**: under the absolute rule in force, admitting such a bucket requires
`|p - b| == tol`, a coincidence 60,000 real bars never produced. It becomes live
under the *relative* reading discussed below, which is why it was fixed anyway.

Both reverts were run against a temporary copy of the file: reverting defect 1
fails 2 tests; reverting defect 2 fails **none**, and
`test_the_index_never_hides_a_bucket_the_test_would_admit` says so explicitly
rather than implying coverage it does not have.

#### ESCALATED — absolute vs relative tolerance. Needs a human decision.

Three places describe the tolerance as **relative**; the rule applied is
**absolute**:

* `LEVEL_CLUSTER_TOLERANCE = Decimal("0.001")  # 0.1%`
* "The tolerance is relative to the *bucket's* price … derives `p/(1+tol) <= b <= p/(1-tol)`"
* `equal_level_for`: "confirmed within `tolerance` of it"

Measured on 60,000 real BTCUSDT 5m bars:

| rule | buckets | multi-member clusters ("equal levels") | max member spread |
|---|---|---|---|
| **A. absolute `|p-b| <= 0.001` (current)** | 7,395 | **271** | **0.00** |
| B. relative `|p-b| <= tol*b` (documented) | 986 | **844** | 117.96 |
| C. symmetric `|p-b| <= tol*p` | 986 | 843 | 117.96 |

Under the implemented rule **every** multi-member cluster has a member price
spread of exactly zero — an "equal high" is two swing highs at the identical
price to the cent. The relative reading yields 3.1× as many equal levels and
merges levels up to ~118 price units apart.

**This is not decided here.** It changes the dataset materially, it is a
specification question rather than an implementation one, and both readings are
defensible. `test_the_tolerance_is_absolute_while_the_documentation_says_relative`
pins the behaviour that exists so it cannot drift unnoticed in either direction.
Choosing by event count would be choosing by whichever definition produces more
events, which is exactly the reasoning this project forbids.

#### Level expiration: quantified, deliberately NOT changed

The specification is silent on level expiry, so no cap was introduced. The
mechanical effect was measured instead (BTCUSDT 5m, 25,887 bars, 90 days).

Levels published: **16,767** (13,553 time-anchored + 3,214 swing/equal).
Distinct level identities swept at least once: **12,514** → **4,253 (25.4%)
never swept** within the window.

| type | never swept / published |
|---|---|
| `range_high` | 463 / 6,284 (7.4%) |
| `range_low` | 774 / 6,373 (12.1%) |
| `session_high` | 77 / 359 (21.4%) |
| `session_low` | 117 / 359 (32.6%) |
| `previous_day_high` | 38 / 89 (42.7%) |
| `previous_day_low` | 43 / 89 (48.3%) |

Mechanical effect of a max-age cap (no outcome consulted):

| policy | sweep rows kept | excluded | levels touched | episodes |
|---|---|---|---|---|
| no expiry (current) | 268,358 | 0 | 12,514 | 1,946 |
| max age ≤ p90 (6,682 bars ≈ 23d) | 241,526 | 26,832 (10.0%) | 12,480 | — |
| max age ≤ p50 (2,292 bars ≈ 8d) | 134,205 | 134,153 (50.0%) | 12,170 | 1,944 |

Three findings that matter more than the caps themselves:

1. **No sweep in this window is of a level older than 11,189 bars (38.9 days)
   against a 90-day window.** The median age at sweep is ~8 days for every
   family. So the missing expiry policy has changed nothing *measurable here* —
   but that is a property of the window, not of the code. Over a multi-year run
   the distribution would extend, and whether a 6-month-old swing high is still
   a "liquidity level" is a research question.
2. **A p90 cap removes 10% of event rows while touching 0.27% of levels** — the
   excluded rows are concentrated in a few very old, very frequently re-swept
   levels (~21 sweep rows per level, from the re-arm lifecycle).
3. **A cap does not reduce the number of independent clusters.** Applying p90
   leaves 1,944 episodes against 1,946. The bootstrap resamples *episodes*, so a
   cap thins each cluster rather than reducing how many there are — a change to
   the estimand's variance, not to the sample's independence.

**Recommendation: leave the current behaviour in force.** Adding a cap now would
silently invalidate every measurement recorded in this document. If one is
wanted it should be a configurable `level_max_age_bars`, recorded in the run
fingerprint (as the zone parameters are), and reported **both with and without**
the cap so the effect is visible rather than assumed.

#### Event measurement contract: no tolerances, and what that costs

`tests/test_event_measurement_contract.py` formalises the two notions of equality
and, more usefully, pins what the aggregate one **cannot** see.
`time_above`, `time_below` and `recovery_ratio` are recorded on the event for
downstream research and are **never read by the outcome labeller** — so
rewriting them to `999` leaves every aggregate byte-identical. That blindness is
structural, not accidental: no aggregate comparison could ever have detected the
38-event bug, at any magnitude. The canary is asserted deliberately so the next
person to trust an aggregate comparison knows its boundary.

**No field is compared with a tolerance.** The 9-row, 2e-25 `recovery_ratio`
difference had a removable cause (reconstructing the excursion denominator as
`level * (1 + penetration)` instead of carrying it) and was fixed at the source.
A tolerance would have been the wrong repair: "equal to within 1e-20" is not
equality, and choosing one means choosing how much corruption to accept.
`test_measurements_are_compared_exactly_and_no_tolerance_is_silently_in_use`
perturbs one value in the 25th significant place and requires the comparison to
report it.

#### Event dependence: figures verified, not re-asserted

Recomputed from the run's own spill (the earlier numbers are confirmed):

| unit | count |
|---|---|
| event rows | 273,901 |
| sweep event rows | 268,358 |
| distinct `(detector, bar)` sweep identities | 35,848 (**7.49 rows per identity**) |
| distinct bars carrying ≥1 sweep | 18,833 |
| distinct `level_price` among sweeps | 11,507 |
| distinct level identities published | 16,767 |
| distinct level identities swept ≥1 | 12,514 |
| episodes (the bootstrap's resampling unit) | 1,946 |
| outcomes | 1,095,604 |

**`range_high` + `range_low` = 245,501 of 268,358 sweep rows (91.5%)**, and they
are the only families with heavy within-bar multiplicity (12.54 and 11.79 rows
per identity, versus 1.04–1.63 for every other family). A rolling 20-bar extreme
is republished far more often than a daily boundary is — that is what a rolling
window extreme *is*, not a defect, and levels are append-only so no level object
is ever repriced. The consequence for inference is that **event rows are not
independent observations**, which is exactly why the bootstrap's default unit is
the episode.

One structural limit found: the episode recomputation in the census reproduces
the runner's 1,946 exactly, but the checkpoint retains only *live* structure
buckets, not the cumulative swing-level list, so the never-swept figure is
reported against the cumulative time-anchored set (13,553) where that set is
available and against the run's own total (16,767) elsewhere.

#### Still open

1. **Absolute vs relative tolerance** — escalated above; blocks nothing until a
   decision is made, and the current behaviour is pinned either way.
2. **`structure_context`** is still one label in a 100-bar lookback rather than a
   graded measure (unchanged).
3. **Full-history 1h pass** still unmeasured (unchanged).
4. **No zone, retest, sweep or cluster has been evaluated for predictive value**,
   and none is claimed.
5. **A resumed run loses event-log rows** — `run-2021b` is missing 169 sweeps at
   its resume boundary while its checkpoint is byte-identical to an uninterrupted
   run. Statistics are unaffected; the event log is not. Mechanism unidentified;
   see GAP_REPORT G4.
6. **The tolerance decision gates the first experiment** (Setups 1 and 2 consume
   `equal_highs`/`equal_lows` sweeps, whose population changes with the rule).

#### Resource profile of this milestone

| | value |
|---|---|
| dataset | BTCUSDT 5m, 2021-01-01 → 2021-04-01, 25,887 bars |
| segmented run | 267 s, **375 MB observed peak RSS** (`/usr/bin/time -v`) |
| spill / checkpoint | 197 MB `events.jsonl` + 6.3 MB checkpoint |
| clustering census | 60,000 bars held in memory for the bucket study |
| full test suite | **553 passed, 0 failures**, 16:54 wall, **910 MB peak RSS** (was 527 / 12:29 / 513 MB) |

Note on suite cost: the two new test files add ~4.5 minutes and roughly 260 MB
above the 476 MB interpreter-and-import baseline. Three deliberate reductions
were made after measuring, and are worth recording because each was a real
regression in cost:

* memoising the whole-series event pass (was recomputed per test, ~4 min);
* mutating events in place in the canary rather than `copy.deepcopy`-ing ~78k
  objects (~1 GB of peak RSS);
* comparing the segmented log in **lockstep** rather than as a second
  materialised list, which also made a separate ordering test redundant --
  a row at a different position fails the lockstep comparison immediately.

All validation output went to `/tmp`; nothing was written into `backend/data/`,
whose 1.15 GB of pre-existing run directories remain gitignored and untouched.
The claim below that `run-2021b`/`run-2021c` were byte-identical re-runs has since
been **corrected** — see the artifact section of Milestone 3, which records that
`run-2021b` is missing 169 sweep events from its event log.

Milestone 3 added no research runs beyond the count verification above
(292 s, **383 MB observed peak RSS**, same 25,887-bar window) and a 60,000-bar
market-structure census for the clustering study. Full suite after Milestone 3:
**553 passed, 0 failures**, 18:24, **962 MB peak RSS**.

### Milestone 3 (2026-10-14): tolerance semantics, setup audit, research protocol

#### 1. What the specification actually requires

The specification's **only** mention of equal highs/lows is line 885–886 of
`btc_quant_trading_project.md`, inside the Phase 7 list of level types:

```
Possible liquidity levels:
- previous swing high
- previous swing low
- equal highs
- equal lows
...
```

There is **no tolerance anywhere in the specification** — no number, no
fraction, no absolute/relative statement. The only related instruction is
Section 3's: *"These concepts must be converted from subjective trading language
into precise mathematical definitions"* — which is a demand for precision, not a
specification of one. Every quantitative property of equal-level clustering in
this repository is therefore an **engineering decision**, and the codebase
documents that fact (`derived_levels.equal_level_for`: "The specification names
the nine fields a sweep record carries; it does not define them").

**This is a specification gap, not a specification conflict.** The comments that
say "0.1%" were never backed by a requirement.

#### 2. Trace: what the code does, traced end to end

| stage | behaviour |
|---|---|
| configuration | `LEVEL_CLUSTER_TOLERANCE = Decimal("0.001")`, commented `# 0.1%` |
| candidate matching | linear scan of buckets, **first match in creation order wins** |
| membership test | `abs(swing.price − bucket["price"]) > tol` → skip. **Absolute**, `Decimal` |
| reference price | `bucket["price"]` = `quantize(first_swing.price, 0.01)` — frozen at creation, never re-averaged |
| bucket indexing | `by_price` sorted list, `bisect_left` on a **relative** range `p/(1±tol)` |
| cluster publication | `equal_level_for` requires ≥2 confirmations; dated to the **second** |

So the index is relative and the test is absolute. They only agree as filters
where the relative band happens to be wider.

#### 3. Third defect found this milestone — the index was NOT a superset

The previous milestone asserted "at every price the absolute band sits inside the
relative one". **That was false.** The crossover is at a price of exactly $1:

* price ≥ $1: relative band (0.1%) is **wider** than the absolute band → index
  over-includes → safe;
* price < $1: relative band is **narrower** → the index can exclude a bucket the
  membership test would accept.

Verified by sweep: anchors $0.01–$2,000, five candidate offsets each, **35
(anchor, candidate) pairs were admissible and invisible to the index — every one
below $1**. Example: anchor `0.01`, candidate `0.011`, `|Δ| = 0.001` admissible,
but the index range was `[0.010989…, 0.011011…]` which excludes `0.01`.

At a BTC quote the two bands differ by five orders of magnitude, which is exactly
why it survived a suite that only ever used BTC-scale prices. **Fixed** by making
the bounds the *union* of both bands. Re-swept after the fix: **0 missed**. Real
data is unchanged — 38,524 levels on 60k bars, identical by type, because for BTC
the union equals the relative band it already used.

`test_the_index_never_hides_a_bucket_the_test_would_admit` now drives the
boundary case at $0.01, $0.22, $100 and $30,000, and **fails** against the
pre-fix relative-only bounds.

#### 4. Transitivity and order-dependence — measured, not assumed

Both are now answered explicitly, because the previous milestone had not asked.

**Not transitive.** Membership is against the frozen anchor, never pairwise.
With `A=100.0000, B=100.0009, C=100.0018`: `A~B` ✓, `B~C` ✓, `A~C` ✗. Production
returns **two** clusters — `[A,B]` and `[C]` — because the anchor quantises to
`100.00` and `C` is 0.0018 from it. This is the correct and intended behaviour for
an append-only level: re-averaging or merging would move a price an event has
already been published against.

**Not order-independent.** The anchor *is* the first member, so contents depend on
confirmation order. Over the 6 permutations of those three prices there are **4
distinct clusterings**. This is a direct consequence of the append-only rule and
is accepted, not a defect: a level's price must not move after publication.
It does mean a cluster's *contents* cannot be reproduced from its price alone —
`first_seen` and the recorded swing confirmations are part of its identity.

#### 5. Decision required from you — absolute vs relative

**The specification does not determine this, so this milestone does not choose.**

Descriptive comparison, 60,000 real BTCUSDT 5m bars. **Descriptive only — no
outcome, return or expectancy was computed for any row.**

| candidate rule | definition | buckets | clusters (≥2 members) | max member spread |
|---|---|---|---|---|
| **A. absolute (current)** | `\|p−b\| ≤ 0.001` | 7,395 | **271** | **0.00** |
| B. relative to anchor (comment) | `\|p−b\| ≤ 0.001·b` | 986 | **844** | 117.96 |
| C. relative to candidate | `\|p−b\| ≤ 0.001·p` | 986 | 843 | 117.96 |
| D. exchange tick | `p == b` | 7,395 | 271 | 0.00 |

Consequences of each:

* **A (current).** On BTC, `0.001` is ~1/30,000 of the quote, so after 2dp
  quantisation it degenerates to **"the same price to the cent"** — which is
  almost certainly *not* what "equal highs" means to a trader. Every one of the
  271 clusters has spread exactly 0.00. It is self-consistent, cheap, and
  arguably wrong as a concept.
* **B (relative).** Matches the existing comments and the trading concept. Costs
  3.1× more clusters and merges levels up to ~118 price units apart at BTC's
  scale, which may be too coarse. Would change every `equal_highs` /
  `equal_lows` level and every sweep attributed to one.
* **D (tick).** The strictest reading of "equal"; on BTC it coincides with A.

**Recommendation: B (relative to the anchor), and version the change.** Reasons:
it is the only candidate that matches the written intent of the constant and the
trading concept; A and D make "equal" mean "identical", which is a degenerate
cluster; and the anchor reference is the only one consistent with the
append-only rule. **But B is a change of dataset**, so it must not be mixed with
existing measurements — see the versioning note below.

I am not choosing on cluster count. B produces more clusters; that is a
*consequence*, and the argument above is about meaning, not yield.

#### 6. Versioning if the rule changes

Any change regenerates `equal_highs`/`equal_lows` levels and every sweep drawn
from them. Therefore:

* the rule must become a **named, fingerprinted configuration** (as the zone
  parameters already are) so a run records which rule produced it;
* outputs under A and under B must never be concatenated or compared without
  saying which produced each;
* the full-history run must be regenerated; the Q1-2021 figures in this document
  are all rule A and are labelled as such.

**No research outputs were regenerated in this milestone**, per the instruction to
settle the rule first.

#### 7. Generated artifacts — byte-level identity, and a correction

A previous entry recorded `run-2021b` and `run-2021c` as "byte-identical re-runs
of `run-2021`". **That was wrong.** It was inferred from `du` sizes, not
checksums, and the checksums contradict it. Measured now:

| file | run-2021 | run-2021b | run-2021c |
|---|---|---|---|
| `events.jsonl` | `ac6669aa…` | **`957cf5a2…`** | `ac6669aa…` |
| `checkpoint.json` | `276cf244…` | `4861ed33…` | `4861ed33…` |
| `report.json` | `b25a767a…` | `d57c309a…` | `9a68a7f4…` |

What the runs actually are:

* **`run-2021`** — 104,923 bars, 731,839 events, 2,927,356 outcomes, but
  **73,257 episodes**. Written by the pre-episode-fix code (its `report.json`
  predates the current schema: no `start`/`end`/`complete`).
* **`run-2021c`** — same bars/events/levels/outcomes, **7,720 episodes**, a clean
  uninterrupted run.
* **`run-2021b`** — same bars/events/levels/outcomes/episodes as `run-2021c`,
  `resumed_from_bar = 86779`. **Its final checkpoint is byte-identical to
  `run-2021c`'s.**

So `run-2021b` and `run-2021c` agree on every substantive quantity and on the
final accumulated state; they differ only in timing fields and in the **event
log**. Comparing the two logs: `run-2021b` is missing exactly **169
`liquidity_sweep` events**, in the contiguous `event_index` range
**86,730–86,777**, ending immediately before the resume point.

**Finding, stated precisely:** resuming a run reproduces the *statistics* but
not the *event log*. The checkpoint is byte-identical, so no outcome is lost or
double-counted — but 169 event rows are absent from the spilled log. A resumed
run's event log therefore cannot be treated as equivalent to an uninterrupted
one's, and any analysis that reads `events.jsonl` from a resumed run may be
missing boundary events. The mechanism is not yet identified and is **not
investigated in this milestone**; it is recorded as an open defect below.

No artifacts were deleted. Exact paths, if deletion is approved:

```
backend/data/research/run-2021b/checkpoint.json    11,694,265 bytes  4861ed33…  (identical to run-2021c)
backend/data/research/run-2021b/events.jsonl      325,472,962 bytes  957cf5a2…  (MISSING 169 events)
backend/data/research/run-2021b/report.json            1,672 bytes  d57c309a…
backend/data/research/run-2021c/checkpoint.json    11,694,265 bytes  4861ed33…  (identical to run-2021b)
backend/data/research/run-2021c/events.jsonl      325,548,989 bytes  ac6669aa…  (identical to run-2021)
backend/data/research/run-2021c/report.json            4,486 bytes  9a68a7f4…
```

If they are deleted, the loss is ~640 MB and nothing is unrecoverable — both are
regenerable by re-running `scripts/run_segmented_research.py` over 2021, and
`run-2021c` in particular is the *correct* complete run for that window, so
**keeping `run-2021c` is advisable**. `run-2021` should be kept or regenerated:
its 73,257-episode figure is a pre-fix artefact and is **not** comparable with
the 7,720-episode figure recorded elsewhere in this document.

#### 8. Research-unit counts — regenerated and defined

Re-measured from a fresh segmented run rather than carried forward, so "still
current" is evidence rather than assumption. BTCUSDT 5m, 2021-01-01 → 2021-04-01,
25,887 bars, horizons `[1, 3, 6, 12]`. **All six reported figures reproduce
exactly.**

| # | unit | count | definition |
|---|---|---|---|
| 1 | event rows | **273,901** | one row per detected event, one line of `events.jsonl`: 268,358 sweeps + 1,192 zones + 3,239 retests + 1,112 compressions |
| 2 | `(detector, bar)` identities | **35,848** | distinct detector/bar pairs among sweeps. **7.49 rows per identity**; 18,833 distinct bars carry ≥1 sweep |
| 3 | level identities published | **16,767** | `(creation_index, level_type, price)`; 13,553 of them time-anchored and retained cumulatively |
| 4 | level identities swept ≥1 | **12,514** | reconstructed exactly, since `level_age_bars == event_index − creation_index` |
| 5 | episodes | **1,946** | a new episode opens when a confirmation bar falls outside the previous event's forward window (max horizon 12). **140.8 event rows per episode** |
| 6 | outcomes | **1,095,604** | `(event, side, stop model, horizon)` labels — exactly 4.00 per event row (2 sides × 2 stop models) |

**A trade is not an event row.** One wick pierces many co-located range levels, so
one piece of market action yields many rows; and a level re-arms and fires again
on later bars. The chain, and where each stage is measured:

```
market episode        1,946   the independent unit; the bootstrap resamples these
    |
    +-- event rows   273,901  measurements, NOT independent          (measured)
            |
            +-- candidate setups    a subset, thinned by the setup rule   (unknown)
                    |
                    +-- executable trades   thinned by costs, missed
                                         entries, censoring              (unknown)
                            |
                            +-- outcome observations   the R-multiple grid (measured)
```

**Three thinnings, and two of them are not yet measurable** because the setup
engine does not exist. The episode-level bootstrap absorbs thinning 1
automatically. Thinnings 2 and 3 need no special statistical handling but **must
be counted and reported**, because the most likely way to manufacture a false edge
in this pipeline is counting one wick that pierces ten levels as ten
independent trades. The protocol requires both counts to be published alongside
every result.

### Audit of the five proposed candidate setups

Compared against specification Section 17 (setups), Section 18 (statistics) and
Section 11 (execution). **Nothing below is implemented.** Requirements are drawn
from the specification; everything else is a proposal or an open question.

Legend: **[SPEC]** required by the specification · **[DOC]** previously
documented decision in this repository · **[PROP]** new proposal here ·
**[OPEN]** unresolved, needs a decision.

#### Setup 1 — Liquidity sweep + rejection

| Aspect | Assessment |
|---|---|
| Purpose | Sweep of a liquidity level followed by a rejection of that level |
| Inputs | `liquidity_sweep` events: `level_price`, `penetration`, `wick_ratio`, `recovery_ratio`, `time_above`/`below` |
| Exact rule | **[PROP]** sweep confirmed at bar *c* **and** `recovery_ratio ≥ θ` **and** `wick_ratio ≥ φ`. θ, φ unspecified |
| Decision-time info | All inputs are knowable at *c*'s close **[DOC]** — the sweep is a two-bar definition and `confirmation_index = event_index + 1` |
| Entry | **[SPEC §11]** execution at *c+1*, never at *c*'s close |
| Stop / invalidation | **[PROP]** stop beyond the swept level; **θ/φ are themselves the invalidation rule** and are the whole experiment |
| Target / horizon | **[SPEC §18]** +0.5R/+1R/+1.5R/+2R; horizon from `FORWARD_HORIZONS` |
| Cancels the setup | **FROZEN** a bar containing both target and stop → **stop-loss** (user convention), flagged `ambiguous_bar` |
| Ambiguous OHLC | **FROZEN** ties sit inside the loss count; the `ambiguous` column reports how many losses the convention decided |
| Costs | **[SPEC §23]** normal / 1.5× / 2× / 3× sensitivity; a setup surviving only at 1× is rejected |
| Risks | Multiple levels co-located on one bar are merged to one event **[DOC]** — good, but means *which* level fired is chosen by `LEVEL_SPECIFICITY`, a research choice that conditions the sample |
| Unresolved | **[OPEN]** θ, φ; whether the stop is the level or an ATR multiple; whether `recovery_ratio` is measured on the pierce bar or the confirmation |
| Baseline | **[SPEC §10]** random entry; plus a **prior-window high/low** detector |
| Evidence before "useful" | Net expectancy in R exceeding the matched random baseline **after** 2× costs, with a bootstrap interval over **episodes** excluding zero, surviving Benjamini–Hochberg across the whole grid |

#### Setup 2 — Liquidity sweep + structure shift

| Aspect | Assessment |
|---|---|
| Purpose | Sweep coinciding with a break of structure in the swept direction |
| Inputs | `liquidity_sweep` + `StructureEvent` (BOS) |
| Exact rule | **[PROP]** BOS on the same side within *w* bars of the sweep confirmation. **[SPEC §17]** names only "liquidity sweep + structure shift" |
| Decision-time info | **[OPEN]** — a BOS at a *confirmed* swing is knowable at that swing's confirmation; "within *w* bars" must be anchored at the sweep's confirmation, not the BOS's |
| Entry | **[SPEC §11]** *c+1* |
| Stop / invalidation | **[PROP]** beyond the structure point that defined the BOS |
| Target / horizon | **[SPEC §18]** grid; **[SPEC §18]**'s own worked example is "15m liquidity sweep + structure shift, +1.5R before −1R" — the specification's own question |
| Cancels | **[DOC]** ambiguous-bar rule |
| Ambiguous OHLC | **[DOC]** same |
| Costs | **[SPEC §23]** |
| Risks | **Selection**: conditioning on a BOS makes the sample strongly regime-dependent (trending markets produce more BOS). Must be reported by regime **[SPEC §25]** |
| Unresolved | **[OPEN]** *w*; whether the BOS must break the swept level itself; whether "structure shift" is BOS or BOS + displacement |
| Baseline | random entry matched on regime and timing; prior-window detector |
| Evidence before "useful" | As Setup 1, plus no concentration in a single regime — if the edge exists only in trends that is a finding to report, not to trade around |

#### Setup 3 — Compression + breakout + retest

| Aspect | Assessment |
|---|---|
| Purpose | Coil, its release, and a return to the zone the release left |
| Inputs | `compression` events (`compression_ratio`, `range_5/10/20`, `volume_ratio`), `zone` / `zone_retest` |
| Exact rule | **[PROP]** compression confirmed **and** close beyond the release extreme **and** a `zone_retest` whose `creation_index` is that release bar |
| Decision-time info | **[DOC]** compression is confirmed at its own bar (`confirmation_index == event_index`); the retest is confirmed at its own bar |
| Entry | **[SPEC §11]** *c+1* |
| Stop / invalidation | **[PROP]** beyond the release bar's low |
| Target / horizon | **[SPEC §18]** grid |
| Cancels | **[DOC]** ambiguous-bar rule; **[PROP]** a retest before the zone was cleared is not a retest **[DOC]** |
| Ambiguous OHLC | **[DOC]** same |
| Costs | **[SPEC §23]** |
| Risks | **Overlap with Setup 4** — both are "zone retest" setups and share events; counting them as two independent candidates double-counts. Must be treated as a family in the multiple-testing correction **[SPEC §53]** |
| Unresolved | **[OPEN]** whether "breakout" means the release extreme or the zone's far edge; whether the compression must be the *same* release |
| Baseline | compression release alone (without the retest), which isolates the retest's contribution |
| Evidence before "useful" | Must beat **both** "compression alone" and "retest alone", not just the random baseline — otherwise the combination is doing nothing that either part does not already do |

#### Setup 4 — Displacement + retest

| Aspect | Assessment |
|---|---|
| Purpose | A large directional candle, then a return to the base it left |
| Inputs | `displacement` (`magnitude_in_volatility`, `body_ratio`, z-scores), `zone` / `zone_retest` |
| Exact rule | **[PROP]** `magnitude_in_volatility ≥ m` **and** a `zone_retest` whose zone's `creation_index` is that displacement bar |
| Decision-time info | **[DOC]** displacement confirms at *i+1*; zone confirms at the later of displacement and structural-swing confirmation, so the retest is strictly after both |
| Entry | **[SPEC §11]** *c+1* |
| Stop / invalidation | **[DOC]** a close deeper than `max_touch_depth` (0.5 of zone height) invalidates the zone — so invalidation is **already implemented**, with 0.5 an **undocumented default** |
| Target / horizon | **[SPEC §18]** grid |
| Cancels | **[DOC]** `invalidated` / `expired` zones stop emitting **[DOC]**; **[OPEN]** whether an *invalidated* zone's retests before invalidation count |
| Ambiguous OHLC | **[DOC]** same |
| Costs | **[SPEC §23]** |
| Risks | `max_touch_depth = 0.5` and `max_age_bars = 500` are **defaults chosen for meaning, not calibrated** — if the result is sensitive to them, that is a robustness failure **[SPEC §24]** |
| Unresolved | **[OPEN]** *m*; whether the first or any retest qualifies; `max_touch_depth` calibration |
| Baseline | displacement alone; zone retest alone |
| Evidence before "useful" | Must survive perturbation of `max_touch_depth` and `max_age_bars` **[SPEC §24]** — a broad plateau, not a single optimum **[SPEC §24]** |

#### Setup 5 — Higher-timeframe zone + lower-timeframe structure confirmation

| Aspect | Assessment |
|---|---|
| Purpose | Context filter from a higher timeframe applied to a 5m signal |
| Inputs | zones and BOS on 1H/4H; BOS on 5m |
| Exact rule | **[PROP]** a 1H/4H zone published strictly before the 5m decision bar **and** a 5m BOS into it |
| Decision-time info | **[OPEN] — the blocking gap.** Nothing in this repository carries a zone across timeframes. `detect_zones` is single-series; there is no cross-timeframe state, and the 1H series must be resampled from 5m with an explicit, stated rule about bars that straddle a boundary |
| Entry | **[SPEC §11]** *c+1* on the 5m series |
| Stop / invalidation | **[PROP]** beyond the 5m structure point |
| Target / horizon | **[SPEC §18]** grid on 5m |
| Cancels | **[DOC]** ambiguous-bar rule |
| Ambiguous OHLC | **[DOC]** same, plus the resampling ambiguity above |
| Costs | **[SPEC §23]** |
| Risks | **[SPEC §60]** explicitly warns the HTF→LTF hierarchy is an **assumption to be tested, not to be built in**: "Do not hard-code the assumption that 4H trend + 15m setup + 5m entry is automatically superior" |
| Unresolved | **[OPEN]** everything above; this is the least-defined of the five and needs the most design before code |
| Baseline | the 5m BOS **without** the HTF filter — the only way to tell whether the filter adds anything |
| Evidence before "useful" | Must beat its own no-filter control. If it does not, the correct conclusion is that HTF context does not help, and that is a result, not a failure |

#### Cross-cutting dependency on the tolerance decision

**Setups 1 and 2 consume `sweep` events, which include `sweep:equal_highs` and
`sweep:equal_lows`.** Under rule A those are 1,740 of 268,358 sweep rows (0.65%);
under rule B they would grow materially (equal-levels are 844 vs 271). So:

* Setup 1/2 results computed under A and under B are **not comparable**;
* any result table must state the rule, and a change of rule invalidates
  previously computed Setup 1/2 numbers;
* this is the concrete reason the tolerance decision gates the first experiment
  rather than being able to run alongside it.

### Proposed first controlled experiment (PROTOCOL — NOT IMPLEMENTED)

> **Status update (protocol-freeze milestone):** the *outcome contract* this
> experiment depends on is now FROZEN and implemented — tie → loss, gap fills
> at the open, T+1 open entry, shared resolver. See **§4b** for the frozen
> clauses and the approvals still required. Everything below remains the
> experiment protocol; where it still describes ties as excluded from the
> win/loss rate, §4b supersedes it.

#### Data separation

Chronological, never random **[SPEC §21]**. On the available history
(2021-01-01 → 2026-09-01, 5m):

| period | range | role |
|---|---|---|
| development | 2021-01-01 → 2024-06-30 | definitions fixed here; thresholds chosen here |
| validation | 2024-07-01 → 2025-06-30 | confirmatory; may be used once per candidate |
| out-of-sample | 2025-07-01 → 2026-09-01 | **touched once**, at the end, and reported whatever it says |

Every run records the experiment id, the git commit, the dataset digest, the
full parameter set **including the tolerance rule**, and the period — the
repository already has `config_fingerprint` and `dataset_sha256` for this
**[DOC]**. Repeated experiments append; nothing is overwritten **[SPEC §52]**.

#### Preventing leakage

* A setup is *knowable* at the max of its ingredients' `confirmation_index`;
  entry is at the open of the **following** bar **[SPEC §11]**.
* Thresholds θ/φ/m/*w* are fixed on the development period **before** validation
  or OOS is read. This is the single most important discipline in the protocol.
* No parameter is selected on OOS, ever.
* Cluster/level *membership* may grow with later swings **[DOC]** — a setup
  depending on `equal_highs` must use the membership knowable at the decision
  bar, not the final membership.

#### Execution assumptions

* Entry at the open of the bar after confirmation; a signal on a bar whose close
  is the last bar of the dataset is **censored**, not assumed filled.
* Stop/target precedence when one bar spans both: **unorderable from OHLC**.
  **FROZEN — user convention: the tie counts as a stop-loss**, in the primary
  backtest *and* in the labeller's resolved denominator alike, with the count
  still reported as the `ambiguous`/`unclear` diagnostic so the size of the
  decision is always visible (one canonical resolver,
  `backend/app/services/outcome_contract.py`; tests in
  `backend/tests/test_outcome_contract.py`).
* Gaps through the stop are modelled at the **open**, not the stop price —
  otherwise every gap loss is understated.
* Costs **[SPEC §23]**: fees + spread + slippage, each reported at 1×/1.5×/2×/3×.
  Slippage is proportional and applied to the entry; a stop gap adds slippage too.
* Missed entries (price already beyond the entry assumption) are recorded and
  excluded from the sample, with the count reported.
* **Position sizing is kept separate**: expectancy in R is computed on a
  fixed-risk notional (risk = 1R per trade by construction). Monetary and
  drawdown figures come only from a portfolio simulation that is reported
  separately, so that a sizing choice cannot flatter the signal.

#### Statistical evaluation

* **Unit of analysis is the episode**, never the event row. Measured on the
  validation window: 273,901 event rows but 35,848 `(detector, bar)` identities
  and **1,946 episodes** — 140.8 rows per episode. Treating events as
  independent would understate every interval by roughly an order of magnitude.
* Intervals by **cluster bootstrap over episodes** (whole episodes resampled,
  each contributing all its events) — already the repository default
  `episode_exact` **[DOC]**.
* Reported per candidate: n (episodes), n (events), win rate, payoff ratio,
  expectancy in R **net of 2× costs**, mean/median R, MFE, MAE, time-to-target,
  time-to-stop, ambiguous count, censored count, max drawdown (portfolio
  simulation only) **[SPEC §18]**.
* By regime **[SPEC §25]** and by level/setup type **where sample size supports
  it**; a cell with too few episodes is reported as "insufficient", not as a
  number.
* Overlapping horizons: events within one episode share price action and their
  forward windows overlap. The episode-level bootstrap absorbs this; **additionally
  the same setup firing on two levels swept by one bar must be deduplicated to
  one trade**, or one wick becomes several trades.

#### Rejection criteria — fixed **before** looking at OOS

A candidate is rejected if any of these holds. Stated now, on the development
period, so they cannot be tuned afterwards:

1. **No excess over baseline.** Net expectancy in R at 2× costs does not exceed
   the matched random-entry baseline with a bootstrap interval (over episodes)
   excluding zero.
2. **Cost-fragile.** The excess disappears at 2× or 3× cost **[SPEC §16]**.
3. **Parameter-fragile.** The result holds only at a narrow θ/φ/*w*/m region
   rather than a broad plateau **[SPEC §24]**.
4. **Period-fragile.** It fails on the validation period after being chosen on
   development.
5. **Regime-concentrated.** It survives only in one regime **[SPEC §25]**.
6. **Multiple-testing artefact.** It does not survive Benjamini–Hochberg across
   the whole grid (5 setups × 2 sides × 2 stop models × 4 targets × horizons).
7. **Composition artefact.** It does not beat the **simpler variant of itself**
   (e.g. "compression alone" for Setup 3, "BOS without HTF filter" for Setup 5).

**On sample size and significance thresholds:** no arbitrary minimum is
invented here. The honest statement is that the binding constraint is the
**episode count**, not the event count — 1,946 episodes on this window is the
resolution of any interval, and a bootstrap over 40 episodes cannot narrow one.
Before running, the episode count per candidate is computed first and reported;
if it is too small for a useful interval, that is reported as the finding rather
than papered over with a significance threshold chosen afterwards.

#### Baselines

**[SPEC §10]** buy-and-hold; **[DOC]** all-bars and random-events controls;
plus two the specification does not name and which matter most here:

* a **prior-window high/low detector** — the null that says whether the whole
  liquidity apparatus beats "the highest high of the last 20 bars";
* the **simpler variant of each setup** (Setup 3 vs compression alone, Setup 5
  vs unfiltered BOS).

### Proposed next milestone — objective candidate setup definitions (PROPOSAL ONLY, NOT IMPLEMENTED)

Everything below is a **proposal**, labelled as such, derived from the main
specification (Sections 17, 18, 19, 21, 22). Nothing here has been coded and
no setup has been evaluated. It is written down so the next milestone has a
target to be measured against rather than being defined by whatever the first
implementation happens to detect.

#### Scope boundary

In scope: precise, testable definitions of the five candidate setups named in
Section 17, the information each needs at decision time, and the statistical
protocol for evaluating them.

Explicitly out of scope until justified: the setup engine's execution semantics,
ML filtering (Section 20), parameter optimisation, and any live or paper
trading. Section 56's ordering still governs: DATA → MEASUREMENT → HYPOTHESIS.

#### Stage A — define before detecting

For each candidate, the specification's vocabulary has to become arithmetic
*before* any code runs, or the code defines the concept retroactively. Proposed
definitions, each to be written as a hand-checkable spec first:

| # | Setup (Section 17) | Proposed mathematical rule | Ambiguity to resolve |
|---|---|---|---|
| 1 | Liquidity sweep + rejection | `sweep` per the existing two-bar definition **and** `recovery_ratio >= θ` and `wick_ratio >= φ` on the pierce bar, evaluated at `confirmation_index` | θ, φ are *proposed* thresholds; the spec gives none. Must be fixed before seeing outcomes, not tuned after |
| 2 | Liquidity sweep + structure shift | `sweep` **and** a BOS on the same side within `w` bars of the confirmation, where BOS requires close beyond a *confirmed* swing | `w`; and whether the shift must be on the swept level itself |
| 3 | Compression + breakout + retest | compression event (`volatility_5/volatility_20 <= c`) **and** a close beyond the release extreme **and** a retest of the zone left by the release | the breakout reference (extreme vs. zone edge) |
| 4 | Displacement + retest | `magnitude_in_volatility >= m` **and** a zone retest whose `creation_index` is that displacement bar | whether the retest must be the *first* one |
| 5 | HTF zone + LTF structure | a 1H/4H zone published before the 5m decision bar **and** a 5m BOS in the zone's direction | how a zone on a different timeframe is carried into a 5m decision — **not yet specified anywhere** |

Every threshold above is a **definition to be pre-registered**, not a parameter
to be searched. Section 53's danger signs are explicit that too many parameters
and exact-threshold dependence are failure modes.

#### Stage B — decision-time information

For each setup, the availability time is the maximum of its ingredients'
`confirmation_index`. Two rules from this milestone's work carry directly:

* a *cluster* grows as later swings confirm, so an equal-highs setup's
  availability is the **second** swing's confirmation, never the first;
* a *sweep* is confirmed on the bar **after** the pierce — entry cannot be at
  the pierce bar's close, which would be 3–5 bars better than reality
  (Section 11's "signal at T, execution at T+1").

#### Stage C — entry, invalidation, target, horizon

Proposed, matching Section 18's grid (+0.5R / +1R / +1.5R / +2R):

* entry at the **open of the bar after confirmation** (Section 11's rule);
* stop from the setup's structural point (zone far edge, swept level, swing low),
  with an ATR multiple as the alternative already implemented;
* target defined in R, resolved on a **single pass** per bar through the
  shared contract: a bar containing both target and stop counts as a **loss**
  (frozen convention) flagged `ambiguous_bar`, never as a win;
* holding horizon from the existing `FORWARD_HORIZONS`; outcomes beyond the data
  end recorded as `truncated`, never imputed.

No-trade cases to be specified explicitly: a bar whose range spans both
boundaries, a level swept by more than one co-located price on the same bar
(the merge rule already reports one event under the most specific level), and
any event whose forward window is truncated.

#### Stage D — evaluation protocol

* chronological development / out-of-sample, never random splits (Section 21);
* costs: Section 16's model with the 1×/1.5×/2×/3× sensitivity, and rejection of
  any candidate that only survives 1×;
* **dependence**: bootstrap over **episodes**, not events. This milestone
  measured 7.49 sweep rows per `(detector, bar)` identity and 140.8 rows per
  episode — treating events as independent would understate every interval by
  roughly an order of magnitude;
* multiple testing: Benjamini–Hochberg across the whole grid (detector × side ×
  stop model × target × horizon), reported, not optional;
* baselines before any candidate: buy-and-hold, all-bars, random events, **and
  a plain prior-window high/low detector**. The last one matters most here — if
  the sophisticated liquidity detector does not beat a trailing 20-bar extreme,
  that is the finding, and it should be measured rather than assumed.

#### Acceptance criteria for the next milestone

1. Each setup written as a spec with hand-computed fixtures before code.
2. A minimum sample size stated *per episode count*, not per event count, with
   the interval width reported at that count.
3. Every candidate compared to the trailing-window baseline and to the null
   controls, with the comparison's dependence handled.
4. Benjamini–Hochberg applied and the surviving set reported as such.
5. A candidate is **rejected** on any of: no significant excess over baseline,
   significance that does not survive cost sensitivity, or dependence on a
   narrow parameter region.

Passing this milestone's acceptance criteria establishes only that the
*measurement* is sound. It establishes no predictive value and no profitability.

### Next milestone — depends on the tolerance decision

Nothing can be measured for Setups 1 and 2 until the tolerance rule is settled,
because their `equal_highs`/`equal_lows` population changes with it. The order
is therefore:

1. **Human decision on absolute vs relative** (this milestone's blocker). On
   approval, the rule becomes a named, fingerprinted configuration so a run
   records which produced it, and the full history is regenerated under a new
   version tag. Existing figures are rule A and must not be mixed with rule B.
2. **Setup 1 first, alone.** It is the cheapest (no cross-timeframe state), it
   has the specification's own worked question attached to Setup 2, and it
   establishes the measurement protocol end to end before the more entangled
   setups are attempted.
3. Setups 3/4 as a **family** (they share zone-retest events and must be
   corrected for multiplicity together), then Setup 5, which needs the
   cross-timeframe zone design resolved first.

**Acceptance criteria for that milestone**, unchanged from the protocol above:
each setup written as a spec with hand-computed fixtures before code; episode
counts published per candidate; baselines including the prior-window detector
and each setup's simpler variant; Benjamini–Hochberg across the whole grid; and
the seven rejection criteria fixed *before* the out-of-sample period is read.

**Out of scope until justified:** ML filtering, parameter optimisation, live or
paper trading, and any statement about profitability.

### Milestone 4 (2026-10-17): relative-to-anchor tolerance adopted; resume defect fixed

#### 1. The equal-level rule, as approved and implemented

**Relative to the frozen anchor.** A swing joins a bucket when

```
abs(swing.price - anchor) <= LEVEL_CLUSTER_TOLERANCE * anchor
```

* ``LEVEL_CLUSTER_TOLERANCE = Decimal("0.001")`` — the existing value, 0.1%.
* ``anchor`` is the **first** swing that created the bucket, quantised to
  ``Decimal("0.01")``, and is **never re-averaged** as the cluster grows.
* The band is **inclusive** at the boundary (``>`` skips, ``==`` joins).
* Comparison is exact ``Decimal`` throughout — membership *and* the search index
  bounds. No binary float participates in a decision.
* **Not transitive.** Every member is tested against the anchor, never pairwise.
  ``A~B`` and ``B~C`` do not imply ``A~C``.
* **Order-dependent.** The anchor is the first member, so a cluster's contents
  follow confirmation order. A direct consequence of the append-only rule and
  accepted: a published level must not move its price.
* The index is a **superset** filter and may never exclude an admissible bucket.
* Recorded in ``config_fingerprint`` as ``level_cluster_tolerance`` and
  ``level_cluster_rule="relative_to_frozen_anchor"``, so a checkpoint written
  under one rule is refused by a build using another.

**Recorded as an engineering decision, because the specification does not define
it.** The only mention of equal highs/lows is the level-type list in Section 14;
Section 3 demands precise mathematical definitions but supplies no tolerance. The
rule was adopted on the meaning of the term — the previous absolute rule made
"equal" mean "identical to the cent", since on a ~$30,000 quote `0.001` is
1/30,000 of the price and every one of its 271 clusters over 60,000 bars had a
member spread of exactly 0.00 — **not** on the fact that the relative rule yields
more clusters.

#### 2. Two further defects found while implementing it

**(a) The rule was implemented twice, and only once.** ``extract_liquidity_levels``
(batch) and ``StructureState._find_bucket`` (segmented) each carried their own
copy of the membership test. Both were absolute and both in ``float``. Fixing only
the batch path made the two disagree, and the first symptom was the
segment-boundary clustering test failing — a segmented run stopped matching a
continuous one. **Both now derive membership from the same rule in exact
arithmetic.** A duplicated rule in two modules is a standing divergence risk and is
recorded as such.

**(b) The float index bounds excluded exactly-at-boundary anchors.** The
pre-filter's lower bound is ``price / (1 + tol)``. In binary double
``30030.0 / 1.001`` is ``30000.000000000004`` — four femto-units above the true
boundary — so a bucket sitting exactly at the edge was excluded from the scan and
the exact membership test never got to admit it. The bounds are now computed in
``Decimal``. A pre-filter that is narrower than the test by a representation error
is not a pre-filter.

#### 3. Tests for the approved rule

22 tests in `tests/test_equal_level_clustering.py`, all with hand-written prices
and expectations derived from the arithmetic, never from the production
clusterer:

* boundary equality joins / one unit past splits;
* **the band scales with the anchor** — $0.10 at $100, $30.00 at $30,000, and the
  converse below $1 where the relative band is the *narrow* one;
* membership measured against the frozen **quantised** anchor, not the raw pivot;
* anchor never re-averaged;
* **non-transitivity** (A~B, B~C, not A~C) and **order-dependence** as explicit
  properties, each asserting the two orders differ;
* index cannot hide an admissible bucket at four price scales ($0.01, $0.22,
  $100, $30,000) — verified to **fail** against the pre-fix float bounds;
* formation, opposite-side non-merging, equal-level dating to the second
  confirmation, prefix append-only property, segment-boundary and checkpoint
  equality, empty/short/flat input.

Reverting either path to the absolute rule fails 8 of the 22.

#### 4. Effect of the change on the dataset — do not mix with earlier figures

BTCUSDT 5m, 2021-01-01 → 2021-04-01, 25,887 bars, 30-day segments, 247 s,
**371 MB peak RSS**, 0 warnings, 0 errors.

| | absolute (previous) | relative (current) |
|---|---|---|
| events | 273,901 | **267,992** |
| levels published | 16,767 | **14,899** |
| outcomes | 1,095,604 | **1,071,968** |
| episodes | 1,946 | **1,946** |
| `sweep:equal_highs` | 972 | **6,302** |
| `sweep:equal_lows` | 768 | **7,962** |
| `sweep:swing_high` | 3,679 | **351** |
| `sweep:swing_low` | 4,396 | **476** |

The swing-level collapse is **not** fewer swing levels: it is the documented merge
rule (`LEVEL_SPECIFICITY` prefers equal > range/session/day > swing) doing its job.
The same price swept by one bar is now reported once, under the *equal* label,
because far more prices qualify as equal. **Every figure recorded under the
absolute rule earlier in this document is superseded** and must not be compared
with these.

#### 5. Resume event-log defect — root cause, fix, and what was *not* reproduced

**Root cause.** The event spill flushes every 1,000 events, which can happen
part-way through a segment. The checkpoint is written only at a segment boundary.
A process killed between the two leaves the file holding events from a segment the
checkpoint does **not** yet claim. On resume the runner skips forward to the
checkpoint's bar and **re-processes** that segment, and appending writes those
events a second time.

**Reproduced before the fix:** BTCUSDT 5m, 2021-01-01 → 2021-03-01, killed 6,000
events into a run — the resumed log held **156,757 rows against a continuous
run's 155,601: 1,156 duplicated events** spanning the whole re-processed segment.
Every aggregate still matched, because duplicates fold into the same accumulators.
Only the event log showed them.

**Fix — truncate-to-offset, not append.** The checkpoint records the spill's byte
length (`events_bytes`); a resumed run cuts the file back to it before appending.
A byte offset rather than a line count because it also repairs a **partially
written final line**, which a line count cannot distinguish from a complete one.

Two further defects in the same code, both found by the new tests:

* `events_written` **under-counted** on a resumed run: a fresh `EventSpill` counts
  from zero, so the checkpoint described only the resumed portion — 150,757 against
  a file holding 155,601. Now seeded from the checkpoint.
* The **final** checkpoint recorded `events_bytes = 0`, because it is written after
  the spill is closed. Left unfixed, any resume would truncate the run's entire
  event log. The offset is now captured before closing.

**After the fix:** the same mid-segment kill reproduces 155,601 rows against
155,601, identity multiset **equal**, zero duplicates, and `events_written` matches
the file.

**What was NOT reproduced — stated plainly.** The originally reported symptom was
a **loss** of 169 sweep events in `run-2021b`; the mechanism reproduced here is a
**duplication**. Both are the same class (the spill and the checkpoint disagreeing
about how far the run got), and the protocol now enforces agreement in both
directions. But the specific loss in `run-2021b` could **not** be reproduced in a
controlled experiment, so **I do not claim that specific instance is fixed**. It
cannot be re-tested: the interruption that produced it is not recorded. The
evidence for the class is the 1,156-duplicate reproduction, before and after.

**Regression tests** (`tests/test_resume_event_log.py`, 9 tests): mid-segment kill
vs continuous, compared as canonical records; no duplicates; **three resume
cycles**; every-segment-boundary interruption; checkpoint count matches the file;
recorded offset matches the file size; a **partially written final line** is
repaired; a spill shorter than the offset is refused rather than padded; and
downstream aggregates agree with the log.

Two other test defects surfaced and were fixed:
* `test_liquidity_differential.py`'s quadratic **oracle** was a transcription of
  the *old absolute* rule. An oracle is a transcription of the rule, not an
  independent opinion about which rule is right, so it was updated by hand and
  annotated — silently letting the implementation win by rewriting the oracle's
  expectations would have destroyed its entire purpose.
* The same file's merge assertion checked the **spread of the members**, which
  assumes transitivity. Under the frozen-anchor rule members may straddle the
  anchor and span twice the band, so it now measures each member against the
  anchor.

**Honest note on test stability:** three of these failed in one full-file run and
passed individually and on a re-run. The cause was initially unknown and I guessed
at a shared-state interaction. It is now established: **the disk.** Each run wrote
~110 MB of event log, `/tmp` is a 5.8 GB tmpfs, and twenty runs exhausted it, so
`ensure_disk_space` raised `InsufficientDiskSpace` — an error about free space
surfacing as nine resume failures. The test window is now 14 days with 3-day
segments (~1/50 the output); the bookkeeping being tested is scale-independent.

#### 6. Other output paths audited

* `checkpoint.json` — atomic (temp file + `replace`). Safe.
* `events.jsonl` — now carries a durable offset and truncates on resume. Fixed.
* `report.json` — written **once at the end**, non-atomically. A crash mid-write
  would leave a truncated report beside a checkpoint marked `complete`. **Not
  fixed**: there is no evidence it has occurred, and the milestone's instruction
  is to expand only where evidence supports. Flagged for the next milestone; the
  fix is the same temp-file-plus-rename already used for the checkpoint.

#### 6b. `report.json` re-audited — resolved as regenerable, NOT fixed

Milestone 4 flagged the non-atomic `report.json` write (§6 above) as a possible
defect and deferred it. This milestone settled the question by test rather than by
argument, and the answer is that it **cannot** damage recoverable state.

Three findings:

* **Nothing reads it back.** A repository-wide search for `report.json` returns
  exactly three hits: its definition (`segmented_runner.py:487`) and two `print`
  statements in `scripts/run_event_research.py`. No resume path, no test and no
  downstream analysis parses it.
* **It is written last.** The report is produced after the `finally` block that
  flushes and closes the spill and after the final `_write_checkpoint`, so both
  durable artifacts already exist on disk when it is written.
* **It is regenerated by re-running.** Because `report.json` is not an input, a
  truncated one is simply overwritten by the next invocation — and since the
  checkpoint reads `complete`, that invocation re-reports the finished result
  rather than re-detecting events.

So the failure mode is "a reader sees an unparseable summary of a run whose
events are all present", not "a run is unrecoverable". That is the difference
between an inconvenient artifact and lost work, and it is why **no production
change was made** — the milestone's instruction was to fix only if needed for
correctness.

Pinned by two new tests in `tests/test_resume_event_log.py`, because "nothing
reads it back" is a property of the whole repository that a comment cannot
enforce and a future reader could invalidate by adding a reader:

* `test_a_torn_report_does_not_damage_the_state_it_describes` — tears the report
  mid-file, asserts the JSON no longer parses, asserts `events.jsonl` is
  **byte-identical**, then re-runs and asserts the report comes back complete with
  the event log still byte-identical (i.e. regenerating does not duplicate events).
* `test_the_report_is_written_after_the_state_it_would_vouch_for` — pins the
  ordering, and asserts checkpoint `events_written` agrees with both the spill and
  the report, so a report can never exist for state that is not yet durable.

**Standing recommendation, unchanged:** if `report.json` ever *gains* a reader,
promote it to the same temp-file-plus-rename the checkpoint already uses, and
delete both tests' premise in favour of an atomicity test.

#### 7. Artifact provenance (nothing deleted)

| run | interval | rows | episodes | kind | status |
|---|---|---|---|---|---|
| `run-2021` | 2021-01-01→2022-01-01, 104,923 bars | 731,839 | **73,257** | continuous, **pre-episode-fix code** | **historical artefact — obsolete.** Its episode figure is not comparable with anything current |
| `run-2021c` | same | 731,839 | 7,720 | continuous, complete | the correct complete run for that window, but **also pre-relative-tolerance** |
| `run-2021b` | same | 731,670 | 7,720 | **resumed** from bar 86,779 | checkpoint byte-identical to `run-2021c`; **log missing 169 sweeps** (GAP_REPORT G4) |

**Identical checkpoints do not establish identical event logs.** `run-2021b` and
`run-2021c` have byte-identical `checkpoint.json` and **different**
`events.jsonl`: the checkpoint holds the accumulated *statistics*, which both runs
computed identically, while the spill holds the *event stream*, which the resumed
one corrupted. A checkpoint is evidence about totals, not about the log.

All three predate the relative-tolerance change and are therefore **superseded**
for any equal-level analysis. None is deleted; a deletion proposal is in the
previous milestone and stands, with the added note that all three should be
regenerated under the new rule before any is used again.

## Milestone 5 — frontend swing markers, bounded audit, first-experiment spec

### 1. Frontend: swings did not render (real defect, fixed)

Reported as "the swings in the frontend don't work". The **backend was correct** —
`GET /api/v1/structure/analyze` returns a populated `swings` array, and the
`SwingPoint` TypeScript type matches the response. The fault was entirely in how
the chart layer applied markers, and it was two independent bugs that compounded.

**Bug 1 — `setMarkers` replaces, it does not append.** `SwingHighLowMarkers` and
`StructureShifts` were sibling components, each calling `series.setMarkers()` on the
**same** candlestick series. Per the library's own typings, `setMarkers` "allows to
set/replace **all** existing series markers". Each effect therefore wiped the
other's work, and the survivor was decided by **React mount order**, not by intent:
`StructureShifts` is declared second, so its effect ran last and **swings were
always erased**. Toggling "Swings" off appeared to do nothing, because unmounting
the component ran no cleanup — the last writer simply stayed.

The fix is `composeMarkers()` in `chart-features.ts`: both layers are merged into
one array and applied in a **single** `setMarkers` call, sorted by time as the
library requires, with swings ranked before events at an identical timestamp so the
structural primitive sits underneath the label derived from it. One owner,
`components/StructureOverlays.tsx`, replaces the three previous components.
`LiquidityZones` is untouched and correctly still owns price lines — a different
series API, not markers.

**Bug 2 — the series was published through a ref.** `MarketChart` read
`const candleSeries = candleSeriesRef.current` during render. Assigning a ref in an
effect does **not** re-render, so on the first pass this was `null`, and the
overlays only mounted if some unrelated state change happened to arrive first.
The series is now mirrored into state, so overlays mount deterministically on the
first paint. This also meant unchecking "Swings" re-rendered into a state where
neither overlay could re-assert itself.

Also removed: `SetupMarkers.tsx`, which called `setMarkers` too and would have
reintroduced the same clobbering the moment it was wired up.

**Verification.** `npm run lint` (tsc) and `npm run build` both pass clean. There
is **no frontend test runner in this repository** (no vitest/jest, no
`*.test.tsx`), so adding one was out of scope for this milestone; the merge
ordering was instead verified by executing the composed sort directly under node:
two swings plus two events produced a correctly time-sorted 4-marker array with
both layers intact. **A frontend test runner remains an open gap** — see §4.

### 2. Bounded audit of `479c23b`

Time-boxed as instructed; no historical dataset was re-run. Findings:

* **Tolerance rule is genuinely single-sourced.** `LEVEL_CLUSTER_TOLERANCE`
  (`analysis.py:68`) is imported by `segmented.py:70`, and both paths implement
  the *identical* authoritative test — `abs(price - anchor) > tolerance * anchor`,
  inclusive at the boundary, against a frozen `0.01`-quantised anchor
  (`analysis.py:531`, `segmented.py:736`). Not merely a shared constant: the same
  semantics, in `Decimal`, on both sides. The duplicate-implementation defect the
  commit describes is genuinely closed.
* **Resume tests cover the full matrix.** All five required scenarios are present
  and pass: interruption+resumption, no duplicates, missing/partial events,
  repeated resume cycles, plus every-boundary interruption, offset agreement,
  refusal against a short spill, and aggregate agreement.
* **`report.json`** — see §6b above. Resolved as regenerable; not fixed.

**Tests run (actual durations, not estimates):**

| suite | result | duration |
|---|---|---|
| `test_resume_event_log.py` | 11 passed | 3:24 |
| `test_equal_level_clustering.py` | 20 passed | (in the 3:00 joint run below) |
| both jointly, pre-test-addition | 31 passed | 3:00 |

No significant unresolved defect was found in the audited scope.

### 3. First experiment — Setup 1 (liquidity sweep + rejection)

Five candidate setups are specified (§17, `btc_quant_trading_project.md:1009-1031`).
**Setup 1 is recommended**, and the recommendation rests on dependency count, not
on preliminary results — there are none, and no setup has ever been evaluated:

| setup | blocker |
|---|---|
| **1. sweep + rejection** | **none beyond tuning.** Uses the existing `liquidity_sweep` events, which already carry `recovery_ratio` and `wick_ratio` as first-class fields |
| 2. sweep + structure shift | needs the window *w* defined; only the interaction with existing `BOS` events is missing |
| 3. compression + breakout + retest | needs a breakout-reference choice; shares a grid with setup 4 |
| 4. displacement + retest | needs threshold *m*; shares the zone-retest grid with setup 3 |
| 5. HTF zone + LTF confirmation | **blocked outright.** "Nothing in this repository carries a zone across timeframes" (`SESSION_NOTES.md:1928`); needs a 1h resample rule for straddling bars |

Setup 1 is the only candidate whose **detection inputs already exist and are
already tested**, requiring no new state and no cross-timeframe machinery. Its
parameters are θ (min `recovery_ratio`) and φ (min `wick_ratio`) — both
**UNSPECIFIED** in every document, and deliberately left unspecified here. The
pre-registered rejection criteria (`SESSION_NOTES.md:2020-2037`) require that the
result hold across a *broad plateau*, so θ/φ must be **fixed before looking**, not
tuned after. Full specification in §4.

### 4. Setup 1 specification — and what is still unspecified

Stated as a specification to be reviewed, **not** implemented and **not** run.

**Entry.** On `liquidity_sweep` events with `recovery_ratio ≥ θ` and
`wick_ratio ≥ φ`. Entry at the **open of the bar after `confirmation_index`**
(`ENTRY_OFFSET = 1`, spec's `signal at T / execution at T+1`). The sweep's
`event_index` is the pierce bar and `confirmation_index` is the next bar; the
confirming bar's close is the first price that could be acted on.

**Direction.** Short a sweep of a high-side level, long a sweep of a low-side
level. **UNSPECIFIED:** whether both sides are in scope at once, or whether the
first run is long-only. *Recommendation: long-side lows only* — a symmetric
two-sided run doubles the multiple-testing burden before a single result exists.

**Stop.** **UNSPECIFIED in the spec; PROPOSED primary stop — requires approval
before the run.** Candidates: beyond the swept level, or an ATR multiple.
*Recommendation: beyond the swept level, i.e. the `swing_extreme` (SWING_STOP)
stop model already implemented in `outcomes.py`.* Rationale: it is the level
the sweep itself defines, so the stop distance is a property of the event
rather than of a volatility parameter; ATR_STOP remains in the grid as the
alternative stop model for the secondary analysis and the multiple-testing
family. Note the interaction with the existing `max_touch_depth = 0.5` zone
default, which is itself an uncalibrated default (`SESSION_NOTES.md:1916`).

**Target.** The existing `TARGET_R_GRID = (0.5, 1, 1.5, 2)`. **Fixed, not chosen**
— the notes' rationale is that "a target grid chosen after seeing the results is a
grid that will always contain a winner", and that reasoning applies with more
force to the first experiment than to any later one.

**Primary target (PROPOSED — requires approval before the run): +1R.**
Stated now, before any outcome data exists, because choosing it afterwards is
exactly the failure the grid's rationale guards against. Rationale: (a) it is
symmetric with the −1R structural stop, so the win and the loss cost the same
size and the win rate alone decides the sign of expectancy — no payoff
assumption is smuggled in; (b) it is the first cell of the already-fixed grid,
so designating it changes no measurement, only which cell carries the primary
claim; (c) a multiple beyond 1R asserts that sweeps tend to travel more than
their own stop distance, which is precisely what the experiment must *test*,
not assume. The remaining cells (+0.5R/+1.5R/+2R) are **secondary/exploratory**,
reported with the multiple-testing correction, and cannot be promoted to
primary after the run. If the user prefers a different primary cell, that
choice must be recorded here before any development-period outcome is read.

**Invalidation.** Distinct from the stop and not yet written down: the event is
discarded if the level is already invalid, if the sweep resolves as
`unresolved` within the horizon, or if the entry open has already gapped beyond
the assumed entry price.

**Fees / slippage.** *Values exist in code and in no document.* From
`backtest/costs.py:27-29`: `fee_rate 0.001` (0.1% per side), `spread_rate 0.0002`,
`slippage_rate 0.0001`, `latency_bars 1` — round-trip ≈ 0.26% of notional. These
are **Binance** costs; Nobitex figures are absent, so every result here is an
upper bound. Sensitivity at 1×/1.5×/2×/3× is mandatory per spec §16.

**Ambiguous bars — RESOLVED and FROZEN this milestone.** The conflict that
lived at this spot (backtester: tie → stop loss; labeller: tie → excluded as
`ambiguous`) is reconciled by the user's explicit convention, now the single
canonical rule in `backend/app/services/outcome_contract.py`, called by both
the labeller (`research/outcomes.py::_scan_barriers`) and the engine
(`backtest/engine.py::_intrabar_exit`):

* a tie counts as a **stop-loss** in the primary backtest *and* in the
  labeller's resolved denominator — the labeller may no longer drop ties from
  its win/loss rates while the engine calls them losses;
* `ambiguous_bar` / the `ambiguous` column survives as a **diagnostic on top
  of the loss count**, never as a separate population;
* the same function decides **gap fills**: a level the bar *opened* through
  fills at that open (a stop gapped down fills worse than its trigger; a
  target gapped up fills better), and a gap also *orders* the bar, so such a
  bar is not ambiguous.

Two further reconciliations shipped with it: the labeller's entry is now the
**open of the bar after confirmation** (it used to be that bar's close, one
full bar later than the engine's fill), and its stop distance is signed — a
structural stop the entry bar gapped through is **no completed trade** in
either component (the engine refuses it as "not protective"; the labeller
returns no stop distance), where the old `abs()` turned it into a guaranteed
instant loss. The labeller's R multiples remain **gross** of costs (event
study); executable net results come from the engine applying spread, slippage
and fees once, on top of the same raw fill references.

**θ and φ — exact definitions (from code, this milestone).** The two thresholds
gate the *rejection* reading of a sweep. Both are anchored to the **pierce bar**
(`event_index`) — the bar whose wick took the level — and both are settled at
the **confirmation bar's close** (`confirmation_index = event_index + 1`), which
is exactly the instant the signal is actionable. Neither reads any bar later
than the confirmation, so neither leaks a future price.

*Source, `backend/app/services/research/events.py`, `measure_sweep` (the
`SweepMeasures` block; the seven measured fields are attached as event features
in `_sweep_event`, so they are first-class and available at confirmation):*

| symbol | field | formula | units / range | notes |
|---|---|---|---|---|
| **θ** | `recovery_ratio` | `|confirmation_close − level_price| / |pierce_extreme − level_price|`, where `pierce_extreme = pierce_bar.high` for a high-side sweep and `pierce_bar.low` for a low-side sweep | dimensionless, **[0, ∞)** in principle; **≈ [0, 1]** in practice, > 1 only when the confirmation close overshoots *past* the level to the far side beyond the price the level was swept from | `None` when the excursion denominator is 0 (a zero-range pierce bar) — never a default 0 |
| **φ** | `wick_ratio` | `wick / bar_range`, where `wick = pierce_bar.high − level_price` (high side) or `level_price − pierce_bar.low` (low side) and `bar_range = pierce_bar.high − pierce_bar.low` | dimensionless, **[0, 1]** | `None` on a zero-range bar (0/0), never a fabricated 0 |

Numerator/denominator placement matters and is the source of the earlier "measured
on the pierce bar or the confirmation" ambiguity (`SESSION_NOTES.md:1860`): θ's
**numerator is a confirmation-bar quantity** (the close) while its **denominator
is a pierce-bar quantity** (the excursion); φ is **entirely a pierce-bar
property**. So a sweep can have a large φ (long wick) and a small θ (price closed
far from the level, i.e. did not recover) — the two are not redundant with each
other. The filed ambiguity is therefore resolved: **θ = recovery at the
confirmation close; φ = wick fraction of the pierce bar.**

**Redundancy check (required by the milestone).** `close_back`
(`events.py:818/865`, carried as `context["close_back_through_level"]`) is a
**boolean**, `pierce_bar.close < level_price` (high side) / `> level_price`
(low side), and by design it is a **feature, not a filter** — a sweep that did
not close back is still a sweep. So `close_back` is a *strict, weaker* relative
of θ: it only asks "did the close finish on the far side of the level", whereas
θ asks "how far back toward/through the level did it recover, relative to the
excursion". With `θ ≥ 0`, `recovery_ratio ≥ θ` already implies the price
recovered at least θ of the excursion — and `close_back` is implied by any
θ that requires a close beyond the level (i.e. θ > the excursion's own
overshoot fraction). **Implication for the proposal: θ must not be set so high
that it collapses to `close_back`; at the mid-scale value below it does not, so
the two are not redundant at the proposed operating point.** No other existing
filter duplicates either threshold: `min_penetration` bounds how *far past* the
level the wick went (a price-fraction of the level, applied before the event is
emitted), which is orthogonal to how much of that excursion was recovered (θ) or
how much of the bar was wick (φ).

**PROPOSED FIXED PAIR — θ = 0.50, φ = 0.50 (APPROVAL REQUIRED).** Rationale is
by **signal definition and feature scale, not performance** (no Setup 1 outcome
has been computed, and none will be read before this is confirmed):

* θ = 0.50 — "the market gave back at least half of the ground the wick took past
  the level". It is the exact midpoint of the feature's natural [0, 1] scale, so
  it separates *recovered* from *not recovered* without asserting a precise
  trading band; it is symmetric in spirit with the primary target/stop being 1R
  each. It is deliberately **not** 0 (which admits a graze, i.e. would make θ a
  no-op) and deliberately **not** ≥ 1 (which would collapse θ into `close_back`,
  the redundancy the milestone asks to avoid). At 0.50, θ is non-trivial and
  non-redundant.
* φ = 0.50 — "at least half of the pierce bar's range was the wick that took the
  level". This is the defining shape of *rejection* (a bar dominated by the
  excursion past the level and its return), and again the midpoint of the
  feature's [0, 1] range: it excludes bodies that merely happened to cross a
  level. φ = 0.50 is the value at which the bar is *more wick than body+opposite
  wick*, which is the ordinary-language meaning of a rejection bar.

Both are **mid-scale, definitional midpoints** — the only defensible fixed pair
that can be stated *before* any return is observed without encoding a
profitability prior. They are the values the milestone asks to freeze; the
**grid/plateau** requirement (`SESSION_NOTES.md:2020-2037`) is satisfied by
reporting the neighbourhood around them *after* the frozen pair is recorded, not
by selecting the pair from that neighbourhood. **If the user prefers different
values, they must be written here before the development period is labelled**;
the alternative defensible reading (θ ≥ 0.5 as above but φ = 0.6/0.7 for a
stricter rejection bar) is noted only so the choice is explicit, not so it can
be tuned.

**Chronological split** (spec §14 — never random). Proposed, mapping onto the
actual data range 2021-01-01 → 2026-08-31, consistent with the existing proposal at
`SESSION_NOTES.md:1954-1968`:

| period | range | role |
|---|---|---|
| development | 2021-01-01 → 2024-06-30 | θ/φ fixed here |
| validation | 2024-07-01 → 2025-06-30 | confirmatory, used once |
| out-of-sample | 2025-07-01 → 2026-08-31 | touched once, at the end |

**Split coverage and boundary handling (checked against the data this
milestone).** The registered 5m dataset covers 2021-01-01T00:00Z →
2026-08-31T23:55Z with seven internal 5-minute gaps (213 bars total, all in
2021 except one in 2023-03); every proposed boundary is inside the data with
room on both sides. Frozen rules:

* **Warm-up is allowed, scoring is not.** Indicator/level state may be built
  from bars before a split's start (a swing needs its lookback), but an event
  whose `confirmation_index` falls before the split start is **not scored** in
  that split.
* **Boundary-crossing observations are excluded, not truncated.** An event is
  assigned to a split only if its **entire evaluation window** fits inside that
  split: `confirmation_index = event_index + 1`, entry at `+2`, and the barrier
  horizon runs to `entry_index + 12`, so the last scorable confirmation bar of a
  split is `split_end − 14` bars. The excluded tail events are **counted and
  reported**, so a reader can see how many were dropped and that the count is
  small relative to the split. Truncating instead (scoring a partial horizon)
  would silently convert an unresolved outcome into a shorter, non-comparable
  one — the same error the sparse `forward_return` dict exists to prevent.
* **Episodes do not straddle a boundary either.** Because events within 12 bars
  cluster into one episode, a cluster is assigned wholly to one split; an
  episode near a boundary is excluded from both rather than split across them.
* **No trades, labels, or horizons leak across splits.** Entry, stop, and the
  barrier scan are functions only of bars at or after confirmation and at or
  before `entry_index + 12`; a scan that would run past the split end is
  excluded by the rule above rather than reading the next split's bars.
* **Machinery status.** This is a **documented protocol, not yet code** (open
  risk 3: no walk-forward/split splitter exists). The feasibility run must
  filter the continuous segment by these rules before scoring; the filter is a
  small, testable layer on top of the existing segmented runner.

**Horizon expiry — exact semantics.** The position is live from the entry
candle's open. Barriers are evaluated on the entry candle (`bars_to_* == 0` if a
barrier prints there) and on each of the next `barrier_horizon = 12` candles,
i.e. candles `entry_index … entry_index + 12` inclusive; the scan stops at
`min(entry_index + 12, last_data_bar)`. If neither barrier printed by the close
of candle `entry_index + 12`, the outcome is **unresolved** — expiry is *not* a
time exit and does not price a trade; the row is censored rather than booked as
a win or a loss. `forward_return` diagnostics use `FORWARD_HORIZONS (1/3/6/12)`
measured from the entry open to each horizon's close, and a horizon past the end
of the data is left absent, never zero. For an executable backtest the engine's
`default_max_hold_bars` must be set to 12 so its time exit matches this horizon
(the engine default is 200 and applies only to bracketed positions).

**Smallest sufficient feasibility run.** The episode rule makes **episodes**, not
events, the independent unit (events within `|a-b| ≤ 12` bars are one experiment).
So the binding constraint on sample size is episode count, not bar count. The
minimum defensible interval is **one quarter of 5m data (2021 Q1)** — large enough
for a non-trivial episode count at the horizon this framework actually uses,
small enough to run in minutes. Required minimum tests before any result is read:
the existing `test_lookahead_audit.py` prefix-invariance suite (Setup 1 must pass
it), the clustering suite (the tolerance rule underpins the levels it consumes),
and a resume test (the run must survive interruption).

### 4b. Outcome protocol — FROZEN status, approvals still required

Written at the protocol-freeze milestone. Code and tests exist for the
contract; the items marked **APPROVAL** are decisions the user must confirm
before any historical experiment reads an outcome.

**Frozen and implemented** (one canonical resolver,
`app/services/outcome_contract.py`; focused tests in
`backend/tests/test_outcome_contract.py`, plus rewrites in
`test_research_target_grid.py`):

| clause | rule |
|---|---|
| stop only | loss, at the stop level |
| target only | win, at the target level |
| both in one bar | **loss** (user convention), flagged `ambiguous_bar` — in the backtester *and* the labeller's resolved denominator |
| neither by the horizon | unresolved/censored, outside the denominator — never silently a loss |
| gap through a stop | fills at the bar's **open**, worse than the trigger |
| gap through a target | fills at the bar's **open**, better than the level; touch alone never fills |
| entry baseline | signal at T's close → fill at **T+1 open** in both components |
| entry bar | **evaluated** for exits once the fill has happened (both components). The fill is the bar's open, so every price after that open is post-entry; a barrier printed in the entry candle resolves the trade on it, `bars_to_* == 0`. The entry price is never read as a barrier hit because brackets are validated strictly beyond it |
| invalid before entry | inverted/gapped-through stop ⇒ no completed trade, in either component |
| costs | applied once, on top of the shared raw fill reference, by the engine; labeller R is explicitly gross |
| spot scope | `is_spot_executable("short") is False`; short event studies are reported separately and never as spot performance; the engine rejects `OPEN_SHORT` by default |

**APPROVALS STILL REQUIRED before the first experiment:**

1. **Primary target: +1R** (proposed above, with rationale) — the grid's other
   three cells stay secondary/exploratory.
2. **Primary stop: SWING_STOP** (structural, beyond the swept level) —
   ATR_STOP stays as the secondary stop model.
3. **θ (min `recovery_ratio`) and φ (min `wick_ratio`)** — the rejection rule
   itself. **Definitions extracted from code and PROPOSED values recorded this
   milestone**: θ = **0.50**, φ = **0.50** (full rationale in §4, "θ and φ —
   exact definitions" and "PROPOSED FIXED PAIR"; the former ambiguity is
   resolved: θ is measured at the confirmation close against the pierce-bar
   excursion, φ is the pierce bar's wick fraction). The pair must be confirmed
   here **before the development period is labelled**, not tuned against it.
4. **Direction: long-only first** (sweeps of low-side levels) — recommended to
   halve the multiple-testing burden before any result exists.
5. **Chronological splits:** development 2021-01-01 → 2024-06-30, validation
   2024-07-01 → 2025-06-30, out-of-sample 2025-07-01 → last data bar
   2026-08-31 (one boundary, written both as "→ 2026-09-01 exclusive" and
   "→ 2026-08-31 inclusive" in earlier tables — same split).
6. **Horizon:** the 12-bar barrier horizon with `FORWARD_HORIZONS` (1/3/6/12)
   diagnostics, as already implemented.

**Cost assumptions (frozen by reference, [SPEC §23]):** fee 0.1% per side,
spread 0.02%, slippage 0.01%, latency 1 bar (Binance figures — every result is
an upper bound); sensitivity at 1×/1.5×/2×/3× is mandatory, and a candidate
surviving only at 1× is rejected. **Denominator (frozen):** ties are inside
`losses`; unresolved rows are outside `n`; the `ambiguous` column is a
diagnostic subset of losses. **Episodes, correction, metrics, rejection
criteria:** unchanged from the protocol above (`SESSION_NOTES.md` protocol
section: episode-level bootstrap, Benjamini–Hochberg across the whole grid,
rejection criteria 1–7 fixed before OOS, no invented minimum sample size —
episode counts reported with the estimates).

**Known simplifications carried into the first experiment, documented not
fixed:** (a) ~~the entry candle is not evaluated for stop/target touches in
either component~~ — **FIXED this milestone**: both components now evaluate the
entry candle immediately after the fill (see the contract row above; tests
`test_the_entry_candle_is_evaluated_after_the_fill`,
`test_an_entry_candle_deep_into_the_target_resolves_as_a_win`,
`test_a_tie_in_the_entry_candle_is_a_flagged_loss`,
`test_the_entry_price_itself_is_never_a_barrier_hit`); (b) the engine's MFE/MAE
diagnostics include the entry candle while the labeller's start one bar later —
diagnostic-only fields, no effect on outcomes; (c) checkpoints written before
this milestone (`run-2021*`, deliberately retained) carry the old
excludes-ties semantics and must not be resumed under the frozen protocol;
(d) the 5m dataset is still absent from `manifest.json` (open risk 4) — a
feasibility-run blocker to close first.

### 5. Open risks carried forward

1. **No frontend test runner.** The swing-marker fix is verified by typecheck,
   build and a manual node check — not by an automated regression test. Adding
   vitest is a small, worthwhile follow-up.
2. **`run-2021`, `run-2021b`, `run-2021c` (1.1 GB) remain on disk.** They are
   pre-relative-tolerance and superseded for equal-level analysis. The prior
   milestone proposed deleting `run-2021b`/`run-2021c` (~640 MB, regenerable);
   **not deleted here**, because this milestone's instruction was to delete no
   artifacts. Decision still open.
3. **No walk-forward machinery exists.** The split above is a table, not code.
4. **The 5m dataset was absent from `manifest.json`** — **CLOSED this
   milestone**: the 5m row is now registered (`bars 595659`, `expected_bars
   595872`, `gap_count 7`, `gap_bars_total 213`, sha256
   `20f8f50d…027681`), computed from the file itself and consistent with the
   same seven gap events the other timeframes record. Full coverage of
   2021-01-01 → 2026-08-31 (last bar `2026-08-31T23:55:00Z`), which confirms the
   proposed split boundaries are inside the data.
5. **Existing research results are all null.** "No event survives multiple-testing
   correction" (`SESSION_NOTES.md:397-401`). Setup 1 should be expected to fail;
   a null here is a valid, publishable result and must be reported as one.

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
