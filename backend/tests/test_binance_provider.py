from datetime import UTC, datetime

import httpx
import pytest

from app.schemas.market_data import Timeframe
from app.services.market_data.binance import BinanceMarketDataProvider


@pytest.mark.asyncio
async def test_binance_historical_candle_normalization() -> None:
    raw = [
        [
            1704067200000,
            "42000.00",
            "42100.00",
            "41900.00",
            "42050.00",
            "12.5",
            1704067499999,
            "525000.0",
            400,
            "6.0",
            "252000.0",
            "0",
        ]
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/klines"
        assert request.url.params["symbol"] == "BTCUSDT"
        assert request.url.params["interval"] == "5m"
        return httpx.Response(200, json=raw)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = BinanceMarketDataProvider(rest_base_url="https://example.test", client=client)
        result = await provider.get_historical_candles(
            "BTC/USDT",
            Timeframe.M5,
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 1, 0, 5, tzinfo=UTC),
        )

    assert result.raw_pages == [raw]
    assert len(result.candles) == 1
    candle = result.candles[0]
    assert candle.symbol == "BTCUSDT"
    assert str(candle.open) == "42000.00"
    assert candle.open_time == datetime(2024, 1, 1, tzinfo=UTC)
    assert candle.is_closed is True


@pytest.mark.asyncio
async def test_binance_rejects_naive_date_range() -> None:
    provider = BinanceMarketDataProvider(rest_base_url="https://example.test")
    with pytest.raises(ValueError, match="timezone-aware"):
        await provider.get_historical_candles(
            "BTCUSDT", Timeframe.M5, datetime(2024, 1, 1), datetime(2024, 1, 2)
        )
