# Operations and Troubleshooting

This document covers deployment, maintenance, and common issues for the BTC Quant Research Platform.

## Quick Start

### Docker Deployment

```bash
# Start all services (first time)
docker compose up --build

# Apply database migrations
make migrate

# Backfill initial data (7 days of historical candles)
make ingest
```

### Development Setup

```bash
# Install dependencies
cd backend && pip install -e .[dev]
cd frontend && npm ci

# Start backend
cd backend && python -m app.main

# Start frontend (in separate terminal)
cd frontend && npm run dev
```

## Service Management

### Using Makefile

```bash
# View all services
make help

# Start services
docker compose up

# Stop services  
docker compose down

# Follow logs
make logs

# Apply migrations
make migrate

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Direct Docker Commands

```bash
# Run backend alone
docker compose exec backend bash

# Run frontend alone  
docker compose exec frontend bash

# Access PostgreSQL shell
docker compose exec postgres psql -U btcbot -d btcbot

# Access Redis CLI
docker compose exec redis redis-cli
```

## Data Management

### Historical Data Ingestion

The system automatically ingests 7 days of historical data during the first run. To ingest more data:

```bash
# Ingest 7 days for all timeframes
make ingest

# Custom range (CLI)
docker compose exec backend python -m app.cli ingest \
  --symbol BTCUSDT \
  --timeframes 5m,15m,1h,4h,1d \
  --start 2026-09-01T00:00:00Z \
  --end 2026-09-08T00:00:00Z
```

### Data Quality Reports

View data quality reports:

```sql
-- List all reports
SELECT id, symbol, timeframe, created_at, passed FROM data_quality_reports ORDER BY created_at DESC;

-- View specific report details
SELECT * FROM data_quality_reports WHERE id = 'report_id';
```

## API Endpoints

### Health and System Status

```bash
# API health check
curl http://localhost:8000/health

# System status (API, DB, Redis)
curl http://localhost:8000/api/v1/system/status
```

### Candle Data

```bash
# Get latest candles
curl "http://localhost:8000/api/v1/candles?symbol=BTCUSDT&timeframe=5m&limit=100"

# Get candles in time range
curl "http://localhost:8000/api/v1/candles?symbol=BTCUSDT&timeframe=15m&start=2026-09-01T00:00:00Z&end=2026-09-02T00:00:00Z&limit=1000"
```

### Ingestion (Development Only)

```bash
# Trigger ingestion via API (31-day max)
curl -X POST http://localhost:8000/api/v1/market-data/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframes": ["5m", "15m", "1h"],
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-09-02T00:00:00Z"
  }'
```

## Monitoring

### System Resources

The dashboard shows system health:

- **API Status**: FastAPI service health
- **Database Status**: PostgreSQL connectivity
- **Redis Status**: Redis coordination service
- **Trading**: Always disabled in Phase 1 (safety boundary)

### Real-time Monitoring

The system provides real-time candle updates via WebSocket:

```bash
# WebSocket endpoint
ws://localhost:8000/api/v1/ws/candles/BTCUSDT/5m
```

## Troubleshooting

### Common Issues

#### API Not Starting

```bash
# Check if ports are available
netstat -tlnp | grep 8000
netstat -tlnp | grep 3000

# Check Docker logs
make logs
```

#### Database Migration Errors

```bash
# View migration status
docker compose exec backend alembic history

# Retry failed migrations
docker compose exec backend alembic upgrade head
```

#### Data Validation Failures

```bash
# Check the logs for validation issues
make logs | grep -i "validation\|error"

# Check recent data quality reports
SELECT * FROM data_quality_reports WHERE passed = false ORDER BY created_at DESC LIMIT 5;
```

#### WebSocket Connection Issues

```bash
# Check if backend is running
make logs | grep "websocket"

# Test WebSocket connection
curl -i http://localhost:8000/api/v1/system/status
```

### Docker Issues

#### Permission Denied

```bash
# Fix data directory permissions
docker compose down
rm -rf data
mkdir -p data/raw data/parquet
chmod -R 777 data

# Restart services
docker compose up --build
```

#### Port Conflicts

```bash
# Check for conflicting processes
lsof -i :8000
lsof -i :3000

# Kill conflicting processes (if safe)
pkill -f uvicorn
pkill -f vite
```

## Production Considerations

### Security

Phase 1 uses public market-data APIs only. However, for production deployment:

- Add API authentication for administrative endpoints
- Implement rate limiting
- Set up HTTPS with proper certificates
- Configure firewall rules
- Regular backup procedures

### Performance

- Use SSDs for faster data access
- Consider increasing PostgreSQL connection pool size
- Monitor Redis memory usage
- Set up log rotation to prevent disk filling

### Backups

```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U btcbot btcbot > backup_$(date +%Y%m%d).sql

# Redis backup (if persistence is enabled)
docker compose exec redis redis-cli BGSAVE
```

## Development Workflow

### Making Changes

1. **Code Changes**: Edit source files directly
2. **Testing**: Run `make test` before committing
3. **Linting**: Run `make lint` to check code quality
4. **Formatting**: Run `make format` to apply consistent formatting
5. **Documentation**: Update relevant docs
6. **Commit**: Use meaningful commit messages

### Testing

Run the full test suite:

```bash
make test
```

Individual test modules:

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Provider tests
cd backend && python -m pytest tests/test_binance_provider.py -v

# Validation tests
cd backend && python -m pytest tests/test_validation.py -v
```

### Migration Guide

When upgrading the project, run:

```bash
# Always backup first
docker compose down

# Run migrations
docker compose up --build -d
make migrate

# Re-ingest data if needed
make ingest
```

## Session Handoff

For information about the current development session:

- System: BTC Quant Research Platform - Phase 0 + 1
- Started: 2026-09-22
- Environment: Development/Testing

The platform is ready for Phase 2 (professional market chart) after successful validation of Phase 0 + 1.

## Changelog

### 2026-09-22
- Initial Phase 0 + 1 implementation completed
- Docker Compose setup with PostgreSQL and Redis
- FastAPI backend with health and status endpoints
- PostgreSQL database schema with Alembic migrations
- Binance market data provider
- Professional trading terminal frontend
- Data validation and quality reporting
- Comprehensive test coverage
- Documentation and troubleshooting guide

### 2026-09-23 (Planned)
- Phase 2: Professional market chart implementation
- Setup detection logic
- Market structure detection
- Liquidity model
- Initial baseline strategies
- Walk-forward validation setup