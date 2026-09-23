import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, ClassVar

import httpx
import websockets

from app.core.config import get_settings
from app.schemas.market_data import CandleData, Timeframe
from app.services.market_data.base import HistoricalResult, MarketDataProvider


class KrakenMarketDataProvider(MarketDataProvider):
    name = "kraken_spot"

    _intervals: ClassVar[dict[Timeframe, int]] = {
        Timeframe.M5: 5,
        Timeframe.M15: 15,
        Timeframe.H1: 60,
        Timeframe.H4: 240,
        Timeframe.D1: 1440,
    }
    _quote_assets: ClassVar[tuple[str, ...]] = (
        "USDT",
        "USD",
        "EUR",
        "GBP",
        "CAD",
        "JPY",
        "AUD",
        "CHF",
    )

    def __init__(
        self,
        rest_base_url: str | None = None,
        ws_base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self.rest_base_url = (rest_base_url or settings.kraken_rest_base_url).rstrip("/")
        self.ws_base_url = (ws_base_url or settings.kraken_ws_base_url).rstrip("/")
        self._client = client

    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> HistoricalResult:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware")
        if start >= end:
            raise ValueError("start must be before end")

        normalized_symbol = symbol.replace("/", "").upper()
        kraken_symbol = self._kraken_symbol(normalized_symbol)
        params = {
            "pair": kraken_symbol,
            "interval": self._intervals[timeframe],
            "since": int(start.astimezone(UTC).timestamp()),
            "assetVersion": 1,
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.get(f"{self.rest_base_url}/0/public/OHLC", params=params)
            response.raise_for_status()
            payload = response.json()
        finally:
            if owns_client:
                await client.aclose()

        errors = payload.get("error", [])
        if errors:
            raise ValueError(f"Kraken OHLC request failed: {', '.join(errors)}")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("unexpected Kraken OHLC response")
        rows = result.get(kraken_symbol)
        if not isinstance(rows, list):
            pair_keys = [key for key in result if key != "last"]
            if len(pair_keys) != 1 or not isinstance(result[pair_keys[0]], list):
                raise ValueError("unexpected Kraken OHLC pair response")
            rows = result[pair_keys[0]]

        candles = [
            self._normalize_rest_candle(normalized_symbol, timeframe, row)
            for row in rows
            if start <= self._utc_from_seconds(int(row[0])) < end
        ]
        return HistoricalResult(
            candles=candles,
            raw_pages=[rows],
            request_metadata=[{"endpoint": "/0/public/OHLC", "params": params}],
        )

    async def stream_candles(self, symbol: str, timeframe: Timeframe) -> AsyncIterator[CandleData]:
        normalized_symbol = symbol.replace("/", "").upper()
        kraken_symbol = self._kraken_symbol(normalized_symbol)
        request = {
            "method": "subscribe",
            "params": {
                "channel": "ohlc",
                "symbol": [kraken_symbol],
                "interval": self._intervals[timeframe],
                "snapshot": True,
            },
        }
        async with websockets.connect(self.ws_base_url, ping_interval=20) as socket:
            await socket.send(json.dumps(request))
            async for message in socket:
                payload = json.loads(message)
                if payload.get("channel") != "ohlc":
                    continue
                for candle in payload.get("data", []):
                    yield self._normalize_ws_candle(normalized_symbol, timeframe, candle)

    async def get_trades(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("trade ingestion is reserved for a later Phase 1 extension")

    async def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.get(
                f"{self.rest_base_url}/0/public/Depth",
                params={
                    "pair": self._kraken_symbol(symbol.replace("/", "").upper()),
                    "count": limit,
                    "assetVersion": 1,
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            errors = payload.get("error", [])
            if errors:
                raise ValueError(f"Kraken order-book request failed: {', '.join(errors)}")
            return payload
        finally:
            if owns_client:
                await client.aclose()

    @classmethod
    def _kraken_symbol(cls, symbol: str) -> str:
        for quote_asset in cls._quote_assets:
            if symbol.endswith(quote_asset) and len(symbol) > len(quote_asset):
                base_asset = symbol[: -len(quote_asset)]
                if base_asset == "XBT":
                    base_asset = "BTC"
                return f"{base_asset}/{quote_asset}"
        raise ValueError(f"unsupported Kraken symbol format: {symbol}")

    @staticmethod
    def _utc_from_seconds(value: int) -> datetime:
        return datetime.fromtimestamp(value, tz=UTC)

    @classmethod
    def _close_time(cls, open_time: datetime, timeframe: Timeframe) -> datetime:
        return open_time + timedelta(seconds=timeframe.seconds) - timedelta(milliseconds=1)

    @classmethod
    def _normalize_rest_candle(
        cls, symbol: str, timeframe: Timeframe, row: list[Any]
    ) -> CandleData:
        open_time = cls._utc_from_seconds(int(row[0]))
        close_time = cls._close_time(open_time, timeframe)
        return CandleData(
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=Decimal(str(row[6])),
            quote_volume=None,
            trade_count=int(row[7]),
            taker_buy_base_volume=None,
            taker_buy_quote_volume=None,
            is_closed=datetime.now(UTC) > close_time,
        )

    @classmethod
    def _normalize_ws_candle(
        cls, symbol: str, timeframe: Timeframe, candle: dict[str, Any]
    ) -> CandleData:
        open_time = datetime.fromisoformat(candle["interval_begin"].replace("Z", "+00:00"))
        close_time = cls._close_time(open_time, timeframe)
        return CandleData(
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=Decimal(str(candle["open"])),
            high=Decimal(str(candle["high"])),
            low=Decimal(str(candle["low"])),
            close=Decimal(str(candle["close"])),
            volume=Decimal(str(candle["volume"])),
            quote_volume=None,
            trade_count=int(candle["trades"]),
            taker_buy_base_volume=None,
            taker_buy_quote_volume=None,
            is_closed=datetime.now(UTC) > close_time,
        )
