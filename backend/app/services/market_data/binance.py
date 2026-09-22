import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
import websockets

from app.core.config import get_settings
from app.schemas.market_data import CandleData, Timeframe
from app.services.market_data.base import HistoricalResult, MarketDataProvider


class BinanceMarketDataProvider(MarketDataProvider):
    """Public Binance Spot market-data adapter. It never handles orders or credentials."""

    name = "binance_spot"

    def __init__(
        self,
        rest_base_url: str | None = None,
        ws_base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self.rest_base_url = (rest_base_url or settings.binance_rest_base_url).rstrip("/")
        self.ws_base_url = (ws_base_url or settings.binance_ws_base_url).rstrip("/")
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

        symbol = symbol.replace("/", "").upper()
        cursor_ms = int(start.astimezone(UTC).timestamp() * 1000)
        end_ms = int(end.astimezone(UTC).timestamp() * 1000)
        interval_ms = timeframe.seconds * 1000
        raw_pages: list[list[list[Any]]] = []
        metadata: list[dict[str, Any]] = []
        candles: list[CandleData] = []
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=30.0)

        try:
            while cursor_ms < end_ms:
                params = {
                    "symbol": symbol,
                    "interval": timeframe.value,
                    "startTime": cursor_ms,
                    "endTime": end_ms - 1,
                    "limit": 1000,
                }
                response = await client.get(f"{self.rest_base_url}/api/v3/klines", params=params)
                response.raise_for_status()
                page = response.json()
                if not isinstance(page, list):
                    raise ValueError("unexpected Binance kline response")
                raw_pages.append(page)
                metadata.append({"endpoint": "/api/v3/klines", "params": params})
                if not page:
                    break

                page_candles = [self._normalize_rest_candle(symbol, timeframe, row) for row in page]
                candles.extend(candle for candle in page_candles if candle.open_time < end)
                next_cursor = int(page[-1][0]) + interval_ms
                if next_cursor <= cursor_ms:
                    raise RuntimeError("Binance pagination did not advance")
                cursor_ms = next_cursor
                if len(page) < 1000:
                    break
        finally:
            if owns_client:
                await client.aclose()

        return HistoricalResult(candles=candles, raw_pages=raw_pages, request_metadata=metadata)

    async def stream_candles(self, symbol: str, timeframe: Timeframe) -> AsyncIterator[CandleData]:
        normalized_symbol = symbol.replace("/", "").upper()
        stream = f"{normalized_symbol.lower()}@kline_{timeframe.value}"
        async with websockets.connect(f"{self.ws_base_url}/{stream}", ping_interval=20) as socket:
            async for message in socket:
                payload = json.loads(message)
                data = payload.get("data", payload)
                yield self._normalize_ws_candle(normalized_symbol, timeframe, data["k"])

    async def get_trades(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("trade ingestion is reserved for a later Phase 1 extension")

    async def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.get(
                f"{self.rest_base_url}/api/v3/depth",
                params={"symbol": symbol.replace("/", "").upper(), "limit": limit},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _utc_from_ms(value: int) -> datetime:
        return datetime.fromtimestamp(value / 1000, tz=UTC)

    @classmethod
    def _normalize_rest_candle(
        cls, symbol: str, timeframe: Timeframe, row: list[Any]
    ) -> CandleData:
        return CandleData(
            symbol=symbol,
            timeframe=timeframe,
            open_time=cls._utc_from_ms(int(row[0])),
            close_time=cls._utc_from_ms(int(row[6])),
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=Decimal(str(row[5])),
            quote_volume=Decimal(str(row[7])),
            trade_count=int(row[8]),
            taker_buy_base_volume=Decimal(str(row[9])),
            taker_buy_quote_volume=Decimal(str(row[10])),
            is_closed=datetime.now(UTC) > cls._utc_from_ms(int(row[6])),
        )

    @classmethod
    def _normalize_ws_candle(
        cls, symbol: str, timeframe: Timeframe, kline: dict[str, Any]
    ) -> CandleData:
        return CandleData(
            symbol=symbol,
            timeframe=timeframe,
            open_time=cls._utc_from_ms(int(kline["t"])),
            close_time=cls._utc_from_ms(int(kline["T"])),
            open=Decimal(kline["o"]),
            high=Decimal(kline["h"]),
            low=Decimal(kline["l"]),
            close=Decimal(kline["c"]),
            volume=Decimal(kline["v"]),
            quote_volume=Decimal(kline["q"]),
            trade_count=int(kline["n"]),
            taker_buy_base_volume=Decimal(kline["V"]),
            taker_buy_quote_volume=Decimal(kline["Q"]),
            is_closed=bool(kline["x"]),
        )
