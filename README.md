# BTC Quant Research Platform

A research-first BTC/USDT market-data platform implementing Phase 0 and Phase 1 of
[`btc_quant_trading_project.md`](btc_quant_trading_project.md). It downloads public exchange
candles, preserves the raw response, validates and normalizes UTC data, stores it in PostgreSQL
and Parquet, exposes a REST/WebSocket API, and renders a professional candlestick dashboard.

This project does **not** contain strategy logic, ML predictions, leverage, exchange credentials,
or order execution. It makes no profitability claim.

## Quick start

### Docker (Recommended)

```bash
# Start all services
docker compose up --build

# Apply database migrations
make migrate

# Backfill initial 7 days of data
make ingest
```

### Running in development

```bash
# Start backend development server
cd backend && python -m app.main

# Start frontend development server (separate terminal)
cd frontend && npm run dev
```

Open the research terminal at `http://localhost:3000`

## Architecture

The system follows Phase 0 + Phase 1 of the project specification:

### Core Services
- **FastAPI backend** with structured JSON logging and health/status endpoints
- **PostgreSQL database** with Alembic migrations for all market-data tables
- **Redis** for realtime coordination and caching
- **Docker Compose** for development and production deployment

### Market Data Infrastructure
- Replaceable `MarketDataProvider` abstraction
- Kraken Spot REST and OHLC WebSocket adapter by default, with optional Binance support
- Paginated historical ingestion for `5m`, `15m`, `1h`, `4h`, and `1d` candles
- Immutable raw JSON captures and normalized Parquet files
- UTC normalization with deterministic validation

### Data Quality
- Hard rules for OHLCV integrity
- Duplicate, missing, and anomaly detection
- Statistical return anomaly warnings
- Persistent quality reports

### Frontend
- React/TypeScript trading terminal with professional charting
- Lightweight-Charts integration with candlestick and volume overlays
- Real-time WebSocket data streaming
- System status monitoring
- Timeframe switching and responsive design

## Key Features

### Backend
- Historical data ingestion from configurable public exchange endpoints
- RESTful API for querying candles across all timeframes
- WebSocket bridge for real-time candle updates
- Comprehensive data validation and quality reporting
- Automated database migrations

### Frontend
- Professional trading terminal UI with dark theme
- Multi-timeframe candlestick charts with volume
- System status cards (API, Database, Redis)
- Live trading feed status indicator
- Timeframe selector and symbol display

### Development
- Unit and integration tests with coverage
- Pre-commit hooks for code quality
- Makefile with common commands
- Comprehensive documentation

## Data Locations

```text
data/raw/<provider>/<symbol>/<timeframe>/YYYY/MM/DD/*.json
data/parquet/symbol=<symbol>/timeframe=<tf>/year=YYYY/month=MM/*.parquet
```

## Testing

```bash
# Run all tests
make test

# Run linting and formatting
make lint
make format

# Apply migrations
make migrate

# View service logs
make logs
```

## Safety Note

Only public market-data functionality is implemented. There is no account API, API-key handling, 
order manager, risk engine, strategy, paper execution, or live execution. Those remain locked 
until the corresponding milestones are explicitly reviewed and approved.

## Project Status

This implements **Phase 0 + Phase 1** of the quantitative trading platform:
- Foundation infrastructure and deployment
- Market data collection and validation
- Professional trading terminal UI
- System monitoring and observability

The system is ready for Phase 2 (professional market chart) and beyond.

## Next Steps

After Phase 0 + Phase 1 is validated:
1. Review system with `make test`
2. Start services with `docker compose up`
3. Verify dashboard functionality
4. Progress to Phase 2 (setup detection and ML integration)
