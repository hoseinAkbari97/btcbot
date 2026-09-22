# Phase 1 Architecture

## Goals and boundaries

This architecture makes BTC/USDT market data reproducible, replaceable, auditable, and safe to use
in later research. It intentionally stops before feature engineering, backtesting, strategies, ML,
news, account connectivity, and execution.

## Component flow

```text
Binance public REST                  Binance public WebSocket
        |                                      |
        v                                      v
BinanceMarketDataProvider <---- MarketDataProvider interface
        |                                      |
        | raw pages + normalized DTOs           | candle updates
        v                                      v
Immutable RawDataStore                  Backend WebSocket bridge
        |                                      |
        v                                      v
CandleValidator                         React terminal
        |
        +------------------+
        |                  |
        v                  v
PostgreSQL warehouse   Partitioned Parquet
        |
        +--> DataQualityReport
        |
        v
REST candle API --> React terminal
```

## Design decisions

### Provider isolation

`MarketDataProvider` is the only contract ingestion and streaming depend on. Binance response
shapes and interval conventions are contained in `BinanceMarketDataProvider`. A CSV, Parquet, or
second exchange adapter can be added without changing validation, persistence, APIs, or the UI.

The adapter uses public Binance Spot market-data interfaces only:

- REST `GET /api/v3/klines` for historical klines
- WebSocket `<symbol>@kline_<interval>` for current candle updates
- REST `GET /api/v3/depth` as the order-book interface foundation

The contracts were checked against the official Binance developer documentation on 2026-09-22.
Provider behavior should be rechecked before any material integration change.

### Raw-before-derived storage

Every historical provider response is written to a unique JSON file before normalized persistence.
The document includes capture time and exact request parameters. Files use UUID names and are never
updated, so a normalization or validator change can be replayed against original evidence.

### UTC and temporal integrity

- API range inputs must be timezone-aware and are converted to UTC.
- Provider epoch timestamps are converted directly to timezone-aware UTC datetimes.
- Candle timestamps must align to timeframe boundaries.
- The ingestion service excludes an incomplete current candle from durable storage.
- REST results are served chronologically even though the query fetches the newest bounded set.
- No future candle, forward fill, interpolation, or derived feature exists in Phase 1.

### Dual normalized storage

PostgreSQL is the operational query store. The unique key
`(instrument_id, source_id, timeframe, open_time)` makes ingestion idempotent. The requested lookup
index `(symbol, timeframe, open_time)` supports chart and research range access.

Parquet is the offline research store, partitioned by symbol, timeframe, year, and month and written
with Zstandard compression. Each ingestion creates new immutable part files.

### Data quality as persisted evidence

Validation does not merely log failures. Every ingestion creates a `data_quality_reports` row with
counts, issues, source range, raw path, and Parquet paths. Invalid candles are retained in raw input
but excluded from normalized stores. Statistical return anomalies are warnings, not automatic data
deletions.

### Realtime scope

The backend provides a WebSocket bridge that normalizes public exchange kline updates before they
reach the browser. Phase 1 does not yet run a durable background stream collector. Historical
ingestion remains the source of durable candle records; live updates are presentation-only.

## Database schema

| Table | Phase 1 purpose |
|---|---|
| `markets` | Venue and spot-market identity |
| `instruments` | Normalized symbol/base/quote catalog |
| `data_sources` | Provider provenance and metadata |
| `candles` | Normalized OHLCV warehouse |
| `trades` | Reserved normalized trade schema |
| `order_book_snapshots` | Reserved snapshot schema |
| `data_quality_reports` | Persistent validation/audit result |

The trades and order-book tables are migrated now to establish the specified schema. Historical
trade collection and continuous order-book capture are explicitly deferred.

## Deployment topology

Docker Compose starts four services:

- `frontend`: static Vite build served by Nginx, with API/WebSocket reverse proxy
- `backend`: FastAPI/Uvicorn; runs Alembic before starting
- `postgres`: PostgreSQL 16 with a persistent volume
- `redis`: Redis 7 with append-only persistence

The browser only speaks to the frontend origin. Nginx routes API and WebSocket traffic internally,
avoiding provider details and credentials in browser code.

## Extension points

- Add providers under `backend/app/services/market_data/`.
- Add background collection without changing DTO, validator, or repository contracts.
- Add quality-report API/UI on the existing persisted schema.
- Add dataset manifests/checksums before formal experiment tracking.
- Add trades and order books using their existing catalog/provenance relationships.

