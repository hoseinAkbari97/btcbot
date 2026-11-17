# Phase 1 API

Interactive OpenAPI documentation is served at `/docs`.

## Health and system

### `GET /health`

Process liveness endpoint used by Docker.

```json
{"status":"ok"}
```

### `GET /api/v1/system/status`

Reports API, PostgreSQL, and Redis connectivity. A dependency failure returns a `degraded` payload
instead of hiding which component failed.

## Candles

### `GET /api/v1/candles`

Query parameters:

| Name | Default | Rules |
|---|---:|---|
| `symbol` | `BTCUSDT` | Slash or compact form accepted |
| `timeframe` | `5m` | `5m`, `15m`, `1h`, `4h`, `1d` |
| `start` | none | timezone-aware ISO 8601, inclusive |
| `end` | none | timezone-aware ISO 8601, exclusive |
| `limit` | `1000` | 1–5000 |

The response is always chronological. Without a range it returns the newest `limit` candles.

### `POST /api/v1/market-data/ingest`

Runs a bounded synchronous historical ingestion for one or more timeframes. The maximum range is 31
days to keep HTTP request behavior predictable. CLI ingestion is preferred for larger backfills.

The response includes fetched/stored counts, quality counts and outcome, raw file, Parquet files,
and the database quality-report ID.

This administrative development endpoint is intentionally unauthenticated in Phase 1 and must not
be exposed publicly. Add authentication/job queuing before any public deployment.

## Realtime candles

### `WS /api/v1/ws/candles/{symbol}/{timeframe}`

Bridges normalized public exchange kline updates. Messages use the same candle field names as the
REST API and include `is_closed`, allowing clients to distinguish current from finalized candles.

The client should reconnect after close. The bridge does not promise durable delivery or persist
updates in this phase.

## Backtests

### `GET /api/v1/backtests/strategies`

Lists the registered strategy names available for research runs.

### `POST /api/v1/backtests/run`

Runs one registered strategy over stored candles, persists the run and returns its metrics,
cost assumptions and provenance.

### `GET /api/v1/backtests/runs` · `GET /api/v1/backtests/runs/{run_id}`

Lists or fetches stored run summaries.

### `POST /api/v1/backtests/compare`

Compares 2–10 existing runs identified by `run_ids`. It is read-only: no backtest is rerun
and no run record is changed. Requires every symbol/timeframe/period, dataset fingerprint,
capital, cost, fill-delay, direction and risk assumption to match; strategies and their
parameters may differ. Incompatible or conditionally comparable runs return `422` with the
exact differing fields in `detail.reasons`.

See [EXPERIMENT_COMPARISON.md](EXPERIMENT_COMPARISON.md) for the full compatibility rules,
metric units, interpretation guidance and limitations.

