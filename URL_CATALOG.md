# Frontend and Backend URL Catalog

Last reviewed: **September 23, 2026**

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
- There are no trading, order execution, account, authentication, quality-report retrieval, or trade
  retrieval HTTP routes in the current application.

## Source Locations

- Frontend page route: `frontend/src/App.tsx`
- Frontend API URL construction: `frontend/src/services/api.ts`
- Backend health routes: `backend/app/api/routes/health.py`
- Backend market-data routes: `backend/app/api/routes/market_data.py`
- Request and response schemas: `backend/app/schemas/market_data.py`
- Default Kraken outbound URLs: `backend/app/services/market_data/kraken.py`
- Optional Binance outbound URLs: `backend/app/services/market_data/binance.py`
- Runtime base URLs and ports: `docker-compose.yml`
- Reverse-proxy paths: `docker/nginx.conf`
- Vite development proxy: `frontend/vite.config.ts`
