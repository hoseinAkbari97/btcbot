# Frontend and Backend URL Catalog

Last reviewed: **October 3, 2026** (updated for the Phase 1–5 research-hardening pass: expanded trade
ledger, gross/net R, R-distribution metrics, run modes)

This file inventories the URL routes and external service URLs defined in the current source tree.
Examples are illustrative; database contents, generated IDs, timestamps, and output file names vary at
runtime.

## Base URLs

| Purpose | Base URL | Notes |
|---|---|---|
| Docker frontend | `http://localhost:3000` | `docker-compose.yml` publishes container port `80` as host port `3000`. |
| Vite development frontend | `http://localhost:5173` | Configured by `frontend/vite.config.ts`. |
| Backend API | `http://localhost:8000` | FastAPI/Uvicorn address published by Docker Compose. |
| Backend inside Docker | `http://backend:8000` | Internal service address used by the frontend proxy configuration. It is not normally reachable from the host browser. |

The frontend uses relative API URLs. When a frontend reverse proxy is active, API requests can use the
frontend origin, for example `http://localhost:3000/api/v1/candles`. Every backend example below uses
the direct backend address, `http://localhost:8000`, which avoids proxy ambiguity.

## Frontend Route

### `GET /`

Public examples:

- Docker: `http://localhost:3000/`
- Vite development: `http://localhost:5173/`

This is the only React Router page currently defined. It renders the BTC market dashboard, system
status cards, timeframe controls, historical candles, and the live candle stream.

Example request:

```http
GET / HTTP/1.1
Host: localhost:3000
Accept: text/html
```

Example response:

```http
HTTP/1.1 200 OK
Content-Type: text/html

<!doctype html>
<html lang="en">
  <head>
    <title>BTC Quant Research Terminal</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- Development uses /src/main.tsx; production uses generated assets. -->
  </body>
</html>
```

Notes:

- React Router has no other declared page paths.
- A static server may return `index.html` for unknown paths as an SPA fallback, but those paths are not
  application routes and currently render no matching React page.
- Production asset URLs are generated during the Vite build and are intentionally not listed because
  their hashed names are not stable.

## Backend Application Routes

### `GET /health`

Direct URL: `http://localhost:8000/health`

Frontend-proxy form: `http://localhost:3000/health`

This lightweight liveness check confirms that the FastAPI process can answer HTTP requests. Docker
uses it for the backend container health check. It does not test PostgreSQL or Redis.

Example request:

```bash
curl http://localhost:8000/health
```

Example response — `200 OK`:

```json
{
  "status": "ok"
}
```

### `GET /api/v1/system/status`

Direct URL: `http://localhost:8000/api/v1/system/status`

Frontend-proxy form: `http://localhost:3000/api/v1/system/status`

This endpoint checks the API, PostgreSQL, and Redis. Dependency failures are reported in a successful
HTTP response with the overall status set to `degraded`, allowing the UI to show the failing component.
The frontend requests this URL immediately and then every 15 seconds.

Example request:

```bash
curl http://localhost:8000/api/v1/system/status
```

Example healthy response — `200 OK`:

```json
{
  "status": "healthy",
  "api": {
    "status": "up",
    "detail": null
  },
  "database": {
    "status": "up",
    "detail": null
  },
  "redis": {
    "status": "up",
    "detail": null
  }
}
```

Example degraded response — still `200 OK`:

```json
{
  "status": "degraded",
  "api": {
    "status": "up",
    "detail": null
  },
  "database": {
    "status": "down",
    "detail": "OperationalError"
  },
  "redis": {
    "status": "up",
    "detail": null
  }
}
```

### `GET /api/v1/candles`

Direct URL: `http://localhost:8000/api/v1/candles`

Frontend-proxy form: `http://localhost:3000/api/v1/candles`

This endpoint reads normalized candles from PostgreSQL and returns them in chronological order. If no
date range is supplied, the repository returns the newest candles up to `limit`. The dashboard calls
this endpoint with `limit=2000` whenever the selected timeframe changes.

Query parameters:

| Parameter | Required | Default | Rules and behavior |
|---|---:|---|---|
| `symbol` | No | `BTCUSDT` | 6–20 letters, digits, or `/`; slash form such as `BTC/USDT` is normalized to `BTCUSDT`. |
| `timeframe` | No | `5m` | One of `5m`, `15m`, `1h`, `4h`, or `1d`. |
| `start` | No | None | Timezone-aware ISO 8601 datetime; inclusive lower bound. |
| `end` | No | None | Timezone-aware ISO 8601 datetime; exclusive upper bound. |
| `limit` | No | `1000` | Integer from 1 through 5000. |

Example request:

```bash
curl --get http://localhost:8000/api/v1/candles \
  --data-urlencode 'symbol=BTC/USDT' \
  --data-urlencode 'timeframe=5m' \
  --data-urlencode 'start=2026-09-22T00:00:00Z' \
  --data-urlencode 'end=2026-09-23T00:00:00Z' \
  --data-urlencode 'limit=100'
```

Example response — `200 OK`:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "count": 1,
  "candles": [
    {
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "open_time": "2026-09-22T00:00:00Z",
      "close_time": "2026-09-22T00:04:59.999000Z",
      "open": "112500.10",
      "high": "112620.00",
      "low": "112480.50",
      "close": "112590.25",
      "volume": "18.742",
      "quote_volume": "2109425.37",
      "trade_count": 3842,
      "taker_buy_base_volume": "9.816",
      "taker_buy_quote_volume": "1104938.21",
      "is_closed": true
    }
  ]
}
```

An empty result is valid and returns `count: 0` with `candles: []`.

Example invalid range response — `422 Unprocessable Entity`:

```json
{
  "detail": "start must be before end"
}
```

Other `422` cases include a datetime without a timezone, an unsupported timeframe, an invalid symbol,
or a `limit` outside 1–5000. Framework-level validation errors use FastAPI's standard `detail` array.

### `POST /api/v1/market-data/ingest`

Direct URL: `http://localhost:8000/api/v1/market-data/ingest`

Frontend-proxy form: `http://localhost:3000/api/v1/market-data/ingest`

This synchronous administrative endpoint fetches historical candles from the configured provider,
which defaults to Kraken, validates them, stores
raw and Parquet files, writes normalized data and a quality report to PostgreSQL, and returns one result
per requested timeframe.

Important behavior:

- `start` and `end` are required and must include timezones.
- `start` must be earlier than `end`.
- The requested range cannot exceed 31 days; larger backfills must use the CLI.
- `symbol` defaults to `BTCUSDT`.
- `timeframes` defaults to all supported values: `5m`, `15m`, `1h`, `4h`, and `1d`.
- The endpoint has no authentication in the current phase and must not be exposed publicly.

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/market-data/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "BTCUSDT",
    "timeframes": ["5m", "1h"],
    "start": "2026-09-22T00:00:00Z",
    "end": "2026-09-23T00:00:00Z"
  }'
```

Example response — `200 OK`:

```json
[
  {
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "fetched": 288,
    "stored": 288,
    "duplicates": 0,
    "missing": 0,
    "invalid": 0,
    "anomalies": 0,
    "passed": true,
    "quality_report_id": "a85cfcf6-4e2e-4c35-9831-e394cb4a8683",
    "raw_file": "/app/data/raw/binance_spot/BTCUSDT/5m/20260922T000000Z.json",
    "parquet_files": [
      "/app/data/parquet/binance_spot/BTCUSDT/5m/year=2026/month=09/data.parquet"
    ]
  },
  {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "fetched": 24,
    "stored": 24,
    "duplicates": 0,
    "missing": 0,
    "invalid": 0,
    "anomalies": 0,
    "passed": true,
    "quality_report_id": "95fa148c-2043-420d-af2f-af0d9ed796a6",
    "raw_file": "/app/data/raw/binance_spot/BTCUSDT/1h/20260922T000000Z.json",
    "parquet_files": [
      "/app/data/parquet/binance_spot/BTCUSDT/1h/year=2026/month=09/data.parquet"
    ]
  }
]
```

Example range-too-large response — `422 Unprocessable Entity`:

```json
{
  "detail": "API ingestion is limited to 31 days; use the CLI for larger backfills"
}
```

### `WS /api/v1/ws/candles/{symbol}/{timeframe}`

Direct example: `ws://localhost:8000/api/v1/ws/candles/BTCUSDT/5m`

Frontend-proxy example: `ws://localhost:3000/api/v1/ws/candles/BTCUSDT/5m`

Use `wss://` instead of `ws://` when the page is served over HTTPS. The frontend chooses the protocol
automatically from `window.location.protocol`.

Path parameters:

| Parameter | Example | Rules and behavior |
|---|---|---|
| `symbol` | `BTCUSDT` | Forwarded to the provider and normalized by removing `/` and uppercasing. |
| `timeframe` | `5m` | One of `5m`, `15m`, `1h`, `4h`, or `1d`. |

Example request with `websocat`:

```bash
websocat ws://localhost:8000/api/v1/ws/candles/BTCUSDT/5m
```

Example handshake:

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
```

Example server message:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "open_time": "2026-09-23T12:00:00Z",
  "close_time": "2026-09-23T12:04:59.999000Z",
  "open": "113020.40",
  "high": "113105.00",
  "low": "112980.10",
  "close": "113080.75",
  "volume": "7.415",
  "quote_volume": "838401.82",
  "trade_count": 1734,
  "taker_buy_base_volume": "4.021",
  "taker_buy_quote_volume": "454690.16",
  "is_closed": false
}
```

Messages represent both in-progress and finalized candles. Consumers should inspect `is_closed`. If the
upstream provider stream fails, the server logs the failure and closes the socket with code `1011` and
reason `upstream market-data stream failed`. Delivery is not durable, and the client should reconnect.

## FastAPI-Generated Routes

These routes are created automatically by the default FastAPI configuration in `backend/app/main.py`.
They are available only on the backend origin because the provided frontend Nginx configuration proxies
`/api/` and `/health`, not these root-level documentation paths.

### `GET /openapi.json`

URL: `http://localhost:8000/openapi.json`

Returns the machine-readable OpenAPI schema used by Swagger UI and ReDoc.

Example request:

```bash
curl http://localhost:8000/openapi.json
```

Abbreviated example response — `200 OK`:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "BTC Quant Research Platform",
    "description": "Research-only BTC/USDT market-data infrastructure. No trading execution.",
    "version": "0.1.0"
  },
  "paths": {
    "/health": {},
    "/api/v1/system/status": {},
    "/api/v1/candles": {},
    "/api/v1/market-data/ingest": {}
  }
}
```

The OpenAPI document describes HTTP routes. WebSocket routes are not represented by OpenAPI.

### `GET /docs`

URL: `http://localhost:8000/docs`

Serves Swagger UI, an interactive browser interface backed by `/openapi.json`.

Example request:

```bash
curl -i http://localhost:8000/docs
```

Abbreviated example response — `200 OK`:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
  <head><title>BTC Quant Research Platform - Swagger UI</title></head>
  <body><div id="swagger-ui"></div></body>
</html>
```

### `GET /docs/oauth2-redirect`

URL: `http://localhost:8000/docs/oauth2-redirect`

Serves Swagger UI's OAuth2 callback helper. The current API defines no authentication scheme, so normal
project usage does not need this route, but FastAPI registers it by default.

Example request:

```bash
curl -i http://localhost:8000/docs/oauth2-redirect
```

Abbreviated example response — `200 OK`:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!doctype html>
<html>
  <head><title>Swagger UI: OAuth2 Redirect</title></head>
  <body><script>/* OAuth2 redirect handling */</script></body>
</html>
```

### `GET /redoc`

URL: `http://localhost:8000/redoc`

Serves ReDoc, a read-only rendered view of `/openapi.json`.

Example request:

```bash
curl -i http://localhost:8000/redoc
```

Abbreviated example response — `200 OK`:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
  <head><title>BTC Quant Research Platform - ReDoc</title></head>
  <body><redoc spec-url="/openapi.json"></redoc></body>
</html>
```

## Backend Outbound URLs

These are external URLs called by backend provider code. They are not endpoints hosted by this project.

### `GET https://api.kraken.com/0/public/OHLC`

This is the default historical candle source. The adapter sends `pair=BTC/USDT`, a timeframe in
minutes, a Unix `since` timestamp, and `assetVersion=1`, then filters the returned candles to the
requested end time. Kraken returns at most 720 recent candles, so deep high-frequency backfills require
another provider or repeated archival collection.

Example outbound request:

```http
GET /0/public/OHLC?pair=BTC%2FUSDT&interval=5&since=1790035200&assetVersion=1 HTTP/1.1
Host: api.kraken.com
```

Abbreviated example response:

```json
{
  "error": [],
  "result": {
    "BTC/USDT": [
      [1790035200, "86556.1", "86561.3", "86399.0", "86423.8", "86524.3", "0.60910315", 33]
    ],
    "last": 1790035500
  }
}
```

### `GET https://api.kraken.com/0/public/Depth`

Implemented by `KrakenMarketDataProvider.get_order_book()` as the default order-book foundation. No
project HTTP route or frontend component currently exposes it.

Example outbound request:

```http
GET /0/public/Depth?pair=BTC%2FUSDT&count=100&assetVersion=1 HTTP/1.1
Host: api.kraken.com
```

### `WSS wss://ws.kraken.com/v2`

This is the default live source. After connecting, the provider sends an `ohlc` subscription for
`BTC/USDT` and the requested interval.

Example subscription message:

```json
{
  "method": "subscribe",
  "params": {
    "channel": "ohlc",
    "symbol": ["BTC/USDT"],
    "interval": 5,
    "snapshot": true
  }
}
```

The Binance URLs below remain available when `MARKET_DATA_PROVIDER=binance`, but Binance returned HTTP
451 from the deployment region during verification on September 23, 2026.

### `GET https://api.binance.com/api/v3/klines`

Used by historical ingestion to fetch up to 1,000 Binance Spot candles per page. The base URL can be
overridden with `BINANCE_REST_BASE_URL`.

Example outbound request:

```http
GET /api/v3/klines?symbol=BTCUSDT&interval=5m&startTime=1790035200000&endTime=1790121599999&limit=1000 HTTP/1.1
Host: api.binance.com
```

Abbreviated example response:

```json
[
  [
    1790035200000,
    "112500.10",
    "112620.00",
    "112480.50",
    "112590.25",
    "18.742",
    1790035499999,
    "2109425.37",
    3842,
    "9.816",
    "1104938.21",
    "0"
  ]
]
```

The provider paginates until the requested end time and converts each array into the project's named
candle schema.

### `GET https://api.binance.com/api/v3/depth`

Implemented by `BinanceMarketDataProvider.get_order_book()`. No project HTTP route or frontend component
currently calls it, but it is an existing backend outbound URL. The base URL can be overridden with
`BINANCE_REST_BASE_URL`.

Example outbound request:

```http
GET /api/v3/depth?symbol=BTCUSDT&limit=100 HTTP/1.1
Host: api.binance.com
```

Abbreviated example response:

```json
{
  "lastUpdateId": 987654321,
  "bids": [["113079.90", "0.840"]],
  "asks": [["113080.00", "1.125"]]
}
```

### `WSS wss://stream.binance.com:9443/ws/{stream}`

The backend WebSocket bridge connects to a Binance stream named
`{lowercase-symbol}@kline_{timeframe}`. The base URL can be overridden with `BINANCE_WS_BASE_URL`.

Example connection URL:

```text
wss://stream.binance.com:9443/ws/btcusdt@kline_5m
```

Example handshake result:

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
```

Abbreviated example message:

```json
{
  "e": "kline",
  "s": "BTCUSDT",
  "k": {
    "t": 1790164800000,
    "T": 1790165099999,
    "s": "BTCUSDT",
    "i": "5m",
    "o": "113020.40",
    "c": "113080.75",
    "h": "113105.00",
    "l": "112980.10",
    "v": "7.415",
    "n": 1734,
    "x": false,
    "q": "838401.82",
    "V": "4.021",
    "Q": "454690.16"
  }
}
```

The provider normalizes the nested `k` object and sends the resulting candle to project WebSocket
clients.

## Frontend Outbound Asset URL

### `GET https://fonts.googleapis.com/css2?...`

The frontend stylesheet imports IBM Plex Mono and Inter from Google Fonts:

```text
https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap
```

Example browser request:

```http
GET /css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap HTTP/2
Host: fonts.googleapis.com
```

Abbreviated example response:

```css
@font-face {
  font-family: "Inter";
  font-style: normal;
  font-weight: 400;
  src: url(https://fonts.gstatic.com/...) format("woff2");
}
```

The returned CSS references font files hosted by `fonts.gstatic.com`. Exact file URLs vary by browser,
font subset, and Google Fonts response and therefore are not fixed in this repository.

## Common Error Responses

Unknown backend route — `404 Not Found`:

```json
{
  "detail": "Not Found"
}
```

Malformed or invalid HTTP input — usually `422 Unprocessable Entity`:

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "timeframe"],
      "msg": "Input should be '5m', '15m', '1h', '4h' or '1d'",
      "input": "10m"
    }
  ]
}
```

Unhandled dependency or provider failures normally produce `500 Internal Server Error`, except
`GET /api/v1/system/status`, which deliberately converts PostgreSQL and Redis failures into a `200`
response with `status: "degraded"`.

## Proxy and Deployment Notes

- `frontend/src/services/api.ts` calls `/api/v1/system/status`, `/api/v1/candles`, and the same-origin
  WebSocket URL `/api/v1/ws/candles/{symbol}/{timeframe}`.
- `frontend/vite.config.ts` defines development proxies for `/api` and `/health` to
  `http://backend:8000`.
- `docker/nginx.conf` defines equivalent HTTP and WebSocket proxies, but the current
  `docker/frontend.Dockerfile` runs `vite preview` and does not copy or start that Nginx configuration.
  Therefore, direct backend URLs on port `8000` are the reliable API URLs unless deployment is adjusted
  to activate the reverse proxy.
- CORS allows browser origins `http://localhost:3000` and `http://localhost:5173` by default.
- There are no trading, order execution, account, authentication, or quality-report retrieval HTTP routes
  in the current application. The `/api/v1/backtests/*` routes run strategies against stored candles and
  persist the result; they place no order and contact no exchange.

### `GET /api/v1/structure/analyze`

Direct URL: `http://localhost:8000/api/v1/structure/analyze`

Frontend-proxy form: `http://localhost:3000/api/v1/structure/analyze`

This endpoint returns a market-structure analysis for the most recent candles of the requested
symbol and timeframe. It detects swing highs/lows, classifies them as HH/HL/LH/LL, identifies
breaks of structure (BOS) and structure shifts, and derives objective liquidity levels.

Query parameters:

| Parameter | Required | Default | Rules and behavior |
|---|---:|---|---|
| `symbol` | No | `BTCUSDT` | 6–20 letters, digits, or `/`; slash form is normalized to uppercase with `/` removed. |
| `timeframe` | No | `5m` | One of `5m`, `15m`, `1h`, `4h`, or `1d`. |
| `limit` | No | `500` | Integer from 50 through 2000 candles used for analysis. |

Example request:

```bash
curl "http://localhost:8000/api/v1/structure/analyze?symbol=BTCUSDT&timeframe=15m&limit=500"
```

Example response — `200 OK`:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "swings": [
    {
      "index": 42,
      "timestamp": "2026-09-26T08:00:00Z",
      "price": "112450.50",
      "kind": "low"
    }
  ],
  "events": [
    {
      "timestamp": "2026-09-26T08:15:00Z",
      "price": "112680.00",
      "event_type": "HH",
      "source_swing_idx": 42,
      "confidence": 0.9
    }
  ],
  "liquidity_levels": [
    {
      "price": "112000",
      "level_type": "swing_low",
      "strength": 0.72,
      "first_seen": "2026-09-20T00:00:00Z",
      "last_seen": "2026-09-26T08:00:00Z",
      "touch_count": 5
    }
  ],
  "recent_range_high": "113200.00",
  "recent_range_low": "111800.00",
  "current_regime": "TREND_UP"
}
```

An empty result is valid and returns empty arrays with `current_regime: "UNKNOWN"`.

## Backtest Routes

These four routes are research tooling. They execute strategies over candles already stored in the
database and persist the outcome. **No route places, routes, or signs an order, and none contacts an
exchange.** Results describe a simulated model under stated assumptions and are not evidence of
profitability.

### `GET /api/v1/backtests/strategies`

Direct URL: `http://localhost:8000/api/v1/backtests/strategies`

Lists the registered baseline strategy names. Requires no parameters and no stored data.

Example request:

```bash
curl "http://localhost:8000/api/v1/backtests/strategies"
```

Example response — `200 OK`:

```json
[
  "buy_and_hold",
  "donchian_breakout",
  "random",
  "sma_trend"
]
```

### `POST /api/v1/backtests/run`

Direct URL: `http://localhost:8000/api/v1/backtests/run`

Runs one baseline strategy over stored candles, computes performance metrics, and appends the run and
its trades to the database. Runs are append-only: nothing edits an existing experiment.

Request body fields (all optional except as noted):

| Field | Type | Default | Rules and behavior |
|---|---|---|---|
| `symbol` | string | `BTCUSDT` | Slash form is normalized to uppercase with `/` removed. |
| `timeframe` | string | `15m` | One of `5m`, `15m`, `1h`, `4h`, `1d`; anything else returns `422`. |
| `strategy` | string | `buy_and_hold` | Must be one of the names from `/strategies`; anything else returns `422`. |
| `start` | datetime or null | `null` | Inclusive lower bound. |
| `end` | datetime or null | `null` | Exclusive upper bound. |
| `initial_capital` | decimal string | `10000` | Must be positive. |
| `max_candles` | integer | `5000` | 100 through 100000. |
| `fee_rate` | decimal string | `0.001` | 0 through `0.01`, charged on both sides of a trade. |
| `spread_rate` | decimal string | `0.0002` | 0 through `0.01`, charged as half the spread. |
| `slippage_rate` | decimal string | `0.0001` | 0 through `0.01`, applied against the fill direction. |
| `latency_bars` | integer | `1` | 1 through 10 bars between a signal and its fill. |
| `cost_scale` | decimal string | `1` | `0.1` through `10`; multiplies every cost for sensitivity tests. |
| `allow_short` | boolean | `false` | Long-only by default. |
| `parameters` | object | `{}` | Per-strategy overrides merged over the defaults. |
| `risk_limits` | object or null | `null` | Risk engine configuration (Phase 5). Omit for an unsupervised run. See below. |
| `notes` | string or null | `null` | Free-text annotation stored with the run, max 2000 characters. |

`risk_limits` fields — all optional, each defaulting to the `RiskLimits` default. Fractions are
decimal strings between `0` and `1`; counters are integers. Any value outside its range returns
`422`.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `max_risk_per_trade` | decimal | `0.01` | Ceiling on any single trade's risk, whatever the strategy requests. |
| `max_portfolio_exposure` | decimal | `1.0` | Notional / equity ceiling. `1.0` means spot: no leverage. |
| `max_daily_loss` | decimal | `0.05` | Fraction of day-open equity that halts entries for the rest of the day. |
| `max_weekly_loss` | decimal | `0.10` | Same, anchored to the ISO week. |
| `max_drawdown` | decimal | `0.20` | Drawdown from the running peak that halts all entries. |
| `max_simultaneous_positions` | integer | `1` | Accepted and validated, but see the limitation below. |
| `cooldown_bars_after_loss` | integer | `0` | Bars blocked after a losing trade. `0` means no cooldown. |
| `emergency_stop_loss` | decimal | `0.50` | Absolute kill switch on total loss from starting equity. Latches for the run. |
| `max_stale_bars` | integer | `5` | Force-exits a position whose bar data stops advancing. |

Three semantics worth knowing before using these:

- **A fraction of `0` disables that control** rather than halting everything. This applies to
  `max_daily_loss`, `max_weekly_loss`, `max_drawdown`, and `emergency_stop_loss`.
- **A strategy's request is advisory.** The engine may clamp a position *smaller* than the strategy
  asked for, or refuse the entry outright. It can never enlarge one.
- **`max_simultaneous_positions` cannot bind.** The engine holds at most one position and never
  adds to one, so this field is recorded and validated for forward compatibility only. Raising it
  above `1` would require pyramiding, which does not exist.

These defaults are examples, not a recommended universal setting, and every run records the limits
it actually used.

Example request:

```bash
curl -X POST "http://localhost:8000/api/v1/backtests/run" \
  -H "Content-Type: application/json" \
  -d '{
        "symbol": "BTCUSDT",
        "timeframe": "5m",
        "strategy": "sma_trend",
        "initial_capital": "10000",
        "cost_scale": "2",
        "risk_limits": {
          "max_risk_per_trade": "0.005",
          "max_drawdown": "0.15"
        },
        "notes": "cost sensitivity check"
      }'
```

Example response — `200 OK` (metrics abbreviated, arrays shortened; `monthly_returns` and
`yearly_returns` omitted):

```json
{
  "run_id": "01a90c70-f58b-4e6f-b15a-e77cf12d1153",
  "strategy": "sma_trend",
  "symbol": "BTCUSDT",
  "timeframe": "5m",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-02T09:19:59.999000",
  "candle_count": 400,
  "metrics": {
    "initial_capital": 10000.0,
    "final_equity": 10105.24,
    "total_return": 0.010524,
    "cagr": 0.0,
    "annualized_volatility": 0.0311,
    "sharpe": 0.42,
    "sortino": 0.55,
    "max_drawdown": -0.0043,
    "calmar": 0.0,
    "profit_factor": 1.6,
    "win_rate": 0.7,
    "trade_count": 10,
    "average_win": 12.4,
    "average_loss": -6.1,
    "expectancy": 6.0,
    "average_r": 0.41,
    "total_fees": 45.13,
    "total_turnover": 45130.2,
    "average_bars_held": 22.6,
    "exposure": 0.76,
    "best_trade": 19.8,
    "worst_trade": -7.2,
    "r_distribution": {
      "sufficient_sample": true,
      "count": 10,
      "mean_r": 0.41,
      "median_r": 0.38,
      "stdev_r": 0.52,
      "skew_r": -0.11,
      "percentiles": {"p05": -0.98, "p25": -0.21, "p50": 0.38, "p75": 1.12, "p95": 1.91},
      "max_consecutive_wins": 4,
      "max_consecutive_losses": 3,
      "mean_mae_r": -0.44,
      "mean_mfe_r": 1.22,
      "mean_cost_per_trade": 4.51,
      "r_by_regime": {"TREND_UP": {"n": 6, "mean_r": 0.62}}
    },
    "insufficient_sample": false,
    "sample_span_seconds": 100800.0
  },
  "exit_reasons": {
    "end_of_data": 1,
    "stop_loss": 2,
    "take_profit": 7
  },
  "costs": {
    "fee_rate": "0.001",
    "spread_rate": "0.0002",
    "slippage_rate": "0.0001",
    "latency_bars": 1,
    "round_trip_cost_rate": "0.0026"
  },
  "parameters": {
    "name": "sma_trend",
    "fast_period": 20,
    "slow_period": 50,
    "risk_fraction": "0.01",
    "atr_stop_multiple": "1.5",
    "atr_target_multiple": "3.0",
    "allow_short": false,
    "risk_limits": {
      "max_risk_per_trade": "0.005",
      "max_portfolio_exposure": "1.0",
      "max_daily_loss": "0.05",
      "max_weekly_loss": "0.10",
      "max_drawdown": "0.15",
      "max_simultaneous_positions": 1,
      "cooldown_bars_after_loss": 0,
      "emergency_stop_loss": "0.50",
      "max_stale_bars": 5
    }
  },
  "git_commit": "1cd95d9c6da80bc1616b1baa5f94d5a721b17d73",
  "library_version": "0.1.0",
  "mode": "research",
  "trades": [
    {
      "id": 0,
      "side": "long",
      "signal_time": "2024-01-01T01:45:00",
      "order_time": "2024-01-01T01:45:00",
      "fill_time": "2024-01-01T01:50:00",
      "entry_time": "2024-01-01T01:50:00",
      "entry_price": "20626.186000",
      "exit_time": "2024-01-01T04:19:59.999000",
      "exit_price": "21426.090244",
      "size": "0.2222488920892729349744191525",
      "notional_value": "4583.66",
      "sizing_model": "stop_risk",
      "risk_fraction": 0.005,
      "risk_amount": "22.918",
      "capital_fraction": "0.458366",
      "exposure_fraction": null,
      "stop_price": "20176.240000000000",
      "target_price": "21432.520000000000",
      "gross_pnl": "177.7778320065074475603739115",
      "fees": "9.346071805061051770656923274",
      "spread_cost": "0.916700",
      "slippage_cost": "0.458366",
      "latency_cost": "0.0",
      "other_costs": "0.0",
      "net_pnl": "168.4317602014463957897169882",
      "r_multiple": 1.7777783200650745,
      "gross_r": 7.755554670083015,
      "net_r": 7.348216554371902,
      "mae": -0.4412,
      "mae_price": "20176.24",
      "mfe": 3.2190,
      "mfe_price": "21432.52",
      "bars_held": 29,
      "holding_seconds": 10800.0,
      "exit_reason": "take_profit",
      "strategy_name": "sma_trend",
      "strategy_version": "1",
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "market_regime": "TREND_UP",
      "strategy_context": {}
    }
  ],
  "equity_curve": [
    {
      "time": "2024-01-01T00:04:59.999000",
      "equity": "10000",
      "cash": "10000",
      "unrealized": "0",
      "position_side": null,
      "drawdown": "0"
    }
  ],
  "rejected_signals": [],
  "risk_violations": []
}
```

The `costs` block echoes the assumptions **after** `cost_scale` is applied, so the run can be
reproduced from the response alone. The `parameters` block records the effective strategy parameters
including `allow_short`, which is an execution assumption rather than a strategy parameter but is
stored alongside them for exactly that reason. For the same reason `risk_limits` is stored *inside*
`parameters` when one was supplied: the risk configuration is an execution assumption, and the
append-only record already holds the rest of them, so no additional table is needed. When
`risk_limits` is omitted, the key is absent and the run was genuinely unsupervised.

### Reading the trade record

The trade object is the authoritative ledger, and several of its fields exist specifically to stop
a reader from drawing a conclusion the data does not support.

- **`fill_time` is always strictly later than `signal_time`.** The engine refuses
  `latency_bars < 1` and fills at the open of a *later* bar. A record where these are equal or
  inverted means a lookahead defect upstream, not a fast fill — treat the run as suspect.
- **`r_multiple` is an alias of `gross_r`, kept for backward compatibility.** It is the pre-cost
  figure and overstates the edge. **`net_r` is the research number**: it is `net_pnl` after fees,
  spread and slippage, divided by the trade's initial monetary risk. Quote `net_r`.
- **Costs are itemised, never summed into the fill price.** `fees + spread_cost + slippage_cost +
  latency_cost + other_costs` reconciles exactly against `gross_pnl - net_pnl`, so a reader can
  reconstruct the result from the response.
- **`risk_fraction` is not a position size.** It is monetary risk as a fraction of equity at entry.
  `capital_fraction` is the share of the account committed, and `exposure_fraction` is populated
  only when `sizing_model` is `notional_exposure` — it is `null` for stop-sized trades on purpose, so
  the three quantities can never be read interchangeably.
- **`r_multiple`, `gross_r` and `net_r` are `null` when the trade had no stop.** No stop means no
  defined `1R`, so no R exists. This is not missing data: converting a stopless benchmark trade into
  R would fabricate a risk definition the strategy never used.
- **`mae` / `mfe` are in R units**, with `mae_price` / `mfe_price` the same excursions in price
  terms. Both are derived from intrabar OHLC extremes, so they are approximations from bar data, not
  tick-accurate.
- **`market_regime` is a label, not a probability.** The regime classifier behind it has not been
  validated as a research finding.

### `r_distribution` and `insufficient_sample`

`metrics.r_distribution` carries the trade-level net-R distribution — median, standard deviation,
skew, percentiles, win/loss streaks, mean MAE/MFE, cost per trade, and a breakdown by regime — because
a win rate and an average winner/loser pair are not enough to characterise a strategy's risk, and the
downstream Monte Carlo project consumes the distribution rather than the summary.

When the run has too few trades for that shape to mean anything, `sufficient_sample` is `false` and
the estimates are withheld rather than returned as thin numbers.

Separately, `insufficient_sample` on the metrics block flags a run whose **time span** is too short to
annualise. In that case `cagr`, `annualized_volatility`, `sharpe`, `sortino` and `calmar` are returned
per-period rather than annualised: they are mathematically computable but economically meaningless on
a short sample, and the flag exists so a consumer cannot mistake them for annual figures.
`sample_span_seconds` reports the span the judgement was made on.

### Run mode and the `mode` field

`mode` records which risk regime the run executed under. `research` is the only mode that permits
`risk=None`; `simulation`, `paper` and `live` all require a configured risk engine and raise rather
than proceeding unsupervised.

**Known limitation:** the HTTP route does not accept a `mode` field, so every run created over the API
is recorded as `research`. The engine-level guard is enforced, but the API surface cannot yet
exercise `simulation` / `paper` / `live`. Treat any API-created run as a research control rather than
a tradeable result until a `mode` field is added to `BacktestRequest`.

Three response fields deserve attention:

- `metrics.cagr` and `metrics.calmar` are `0.0` for any run shorter than 30 days. Annualising a
  window of hours is not meaningful, and the arithmetic overflows outright. `sharpe` and `sortino`
  are reported unannualised on the same short windows; do not read them as annual figures.
- `rejected_signals` lists signals the engine declined, with the reason — for example a close signal
  while already flat, an entry the available cash could not cover, or a protective stop that would
  not sit on the correct side of the fill price. A non-empty list is normal.
- `risk_violations` lists the risk controls that bound during the run, one entry per occurrence, with
  a stable reason slug: `emergency_stop`, `daily_loss_limit`, `drawdown_limit`, `cooldown`, or
  `stale_data`. The slugs are counted and compared across experiments. A weekly loss breach is
  reported under `daily_loss_limit` because the day is the tighter control. This list is always
  present and is `[]` when no limit bound, including for every run with no `risk_limits` at all.
  A limit that bounded a position is a fact about the run, not a fault — a non-empty list is
  evidence the risk engine did its job, and says nothing about whether the strategy was any good.

Error responses:

| Status | Condition |
|---:|---|
| `422` | Unknown `strategy` or unsupported `timeframe`. |
| `422` | Fewer than 2 candles stored for the symbol/timeframe and range. The `detail` says how many were found and that data must be ingested first. |
| `422` | A bracket the engine refuses to accept, such as a stop on the profitable side of the fill price. |
| `422` | A `risk_limits` value outside its permitted range, such as a fraction above `1` or a negative loss limit. |

### `GET /api/v1/backtests/runs`

Direct URL: `http://localhost:8000/api/v1/backtests/runs`

Lists stored runs, newest first.

Query parameters:

| Parameter | Required | Default | Rules and behavior |
|---|---:|---|---|
| `symbol` | No | all | 6–20 letters, digits, or `/`; slash form is normalized. |
| `timeframe` | No | all | One of `5m`, `15m`, `1h`, `4h`, `1d`. |
| `strategy` | No | all | Must be a known strategy name; an unknown name returns `422` rather than an empty list. |
| `limit` | No | `50` | 1 through 500. |

Example request:

```bash
curl "http://localhost:8000/api/v1/backtests/runs?strategy=sma_trend&limit=10"
```

Example response — `200 OK`:

```json
[
  {
    "id": "01a90c70-f58b-4e6f-b15a-e77cf12d1153",
    "strategy_name": "sma_trend",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-01-02T09:19:59.999000",
    "candle_count": 400,
    "initial_capital": "10000",
    "final_equity": "10105.24",
    "total_return": 0.010524,
    "sharpe": 0.42,
    "max_drawdown": -0.0043,
    "profit_factor": 1.6,
    "trade_count": 10,
    "git_commit": "1cd95d9c6da80bc1616b1baa5f94d5a721b17d73",
    "created_at": "2026-09-30T06:23:13.605813Z"
  }
]
```

### `GET /api/v1/backtests/runs/{run_id}`

Direct URL: `http://localhost:8000/api/v1/backtests/runs/{run_id}`

Returns the same summary shape as one element of the listing, for a single run.

Example request:

```bash
curl "http://localhost:8000/api/v1/backtests/runs/01a90c70-f58b-4e6f-b15a-e77cf12d1153"
```

Example response — `200 OK`: the single run object shown above.

An unknown identifier returns `404` with a `backtest run {id} not found` detail. Note that the
per-trade detail is returned by `POST /run` and is persisted in `backtest_trades`; this endpoint
returns the summary only.

### Command line

The same runs are available without the API:

```bash
cd backend
python -m app.cli backtest --strategies sma_trend,donchian_breakout --cost-scale 2
python -m app.cli backtest --strategies buy_and_hold --start 2024-01-01T00:00:00Z

# Phase 5 risk limits — a fresh engine is built per strategy, so no state leaks between them
python -m app.cli backtest --strategies buy_and_hold,sma_trend \
  --max-risk-per-trade 0.005 --max-drawdown 0.15 --no-save
```

`--start` and `--end` require an explicit timezone offset; a naive timestamp is rejected rather than
silently assumed to be UTC.

Risk flags mirror the `risk_limits` request fields one for one, all optional:

| Flag | Maps to | Default |
|---|---|---|
| `--max-risk-per-trade` | `max_risk_per_trade` | `0.01` |
| `--max-portfolio-exposure` | `max_portfolio_exposure` | `1.0` |
| `--max-daily-loss` | `max_daily_loss` | `0.05` |
| `--max-weekly-loss` | `max_weekly_loss` | `0.10` |
| `--max-drawdown` | `max_drawdown` | `0.20` |
| `--cooldown-bars` | `cooldown_bars_after_loss` | `0` |
| `--emergency-stop-loss` | `emergency_stop_loss` | `0.50` |
| `--max-stale-bars` | `max_stale_bars` | `5` |

**Omitting every risk flag leaves the run unsupervised** — no risk engine is constructed at all, and
the strategy's requested risk is honoured exactly. This is what keeps pre-Phase-5 runs reproducible.
The printed output includes a `risk_violations` list for every run, empty when no limit bound.

## Source Locations

- Frontend page route: `frontend/src/App.tsx`
- Frontend API URL construction: `frontend/src/services/api.ts`
- Backend health routes: `backend/app/api/routes/health.py`
- Backend market-data routes: `backend/app/api/routes/market_data.py`
- Backend market-structure routes: `backend/app/api/routes/market_structure.py`
- Backend market-structure service: `backend/app/services/market_structure/analysis.py`
- Backend backtest routes: `backend/app/api/routes/backtest.py`
- Backtest schemas: `backend/app/schemas/backtest.py`
- Backtest engine (Phase 4): `backend/app/services/backtest/engine.py`
- Risk engine (Phase 5): `backend/app/services/backtest/risk.py`
- Baseline strategies (Phase 3): `backend/app/services/backtest/baselines.py`
- Cost model: `backend/app/services/backtest/costs.py`
- Performance metrics: `backend/app/services/backtest/metrics.py`
- Backtest runner: `backend/app/services/backtest/runner.py`
- Backtest persistence: `backend/app/repositories/backtest.py`, `backend/app/models/backtest.py`
- Command-line runner: `backend/app/cli.py`
- Market structure schemas: `backend/app/schemas/market_structure.py`
- Frontend chart overlay components:
  - `frontend/src/components/SwingHighLowMarkers.tsx`
  - `frontend/src/components/StructureShifts.tsx`
  - `frontend/src/components/LiquidityZones.tsx`
  - `frontend/src/components/SetupMarkers.tsx`
- Chart feature utilities: `frontend/src/services/chart-features.ts`
- Main chart component: `frontend/src/charts/MarketChart.tsx`
- Frontend market-structure types: `frontend/src/types/market.ts`
- Request and response schemas: `backend/app/schemas/market_data.py`
- Default Kraken outbound URLs: `backend/app/services/market_data/kraken.py`
- Optional Binance outbound URLs: `backend/app/services/market_data/binance.py`
- Runtime base URLs and ports: `docker-compose.yml`
- Reverse-proxy paths: `docker/nginx.conf`
- Vite development proxy: `frontend/vite.config.ts`
