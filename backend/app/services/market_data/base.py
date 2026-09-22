from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.schemas.market_data import CandleData, Timeframe


@dataclass(frozen=True)
class HistoricalResult:
    candles: list[CandleData]
    raw_pages: list[list[list[Any]]]
    request_metadata: list[dict[str, Any]]


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> HistoricalResult:
        """Return provider-native raw pages and normalized UTC candles."""

    @abstractmethod
    async def stream_candles(self, symbol: str, timeframe: Timeframe) -> AsyncIterator[CandleData]:
        """Yield candle updates. Consumers decide whether to retain incomplete candles."""
        if False:
            yield  # pragma: no cover

    @abstractmethod
    async def get_trades(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Fetch normalized trades when supported."""

    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        """Fetch an order-book snapshot when supported."""
