from datetime import UTC, datetime

import httpx
import pytest

from app.schemas.market_data import Timeframe
from app.services.market_data.kraken import KrakenMarketDataProvider


@pytest.mark.asyncio
async def test_kraken_historical_candle_normalization() -> None:
    raw = [
        [
            1704067200,
            "42000.00",
            "42100.00",
            "41900.00",
            "42050.00",
            "42025.00",
            "12.5",
            400,
        ]
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/0/public/OHLC"
        assert request.url.params["pair"] == "BTC/USDT"
        assert request.url.params["interval"] == "5"
        assert request.url.params["assetVersion"] == "1"
        return httpx.Response(200, json={"error": [], "result": {"BTC/USDT": raw, "last": 0}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = KrakenMarketDataProvider(rest_base_url="https://example.test", client=client)
        result = await provider.get_historical_candles(
            "BTCUSDT",
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
    assert candle.quote_volume is None
    assert candle.trade_count == 400
    assert candle.is_closed is True


@pytest.mark.asyncio
async def test_kraken_filters_candles_after_requested_end() -> None:
    raw = [
        [1704067200, "1", "2", "1", "2", "1.5", "10", 5],
        [1704067500, "2", "3", "2", "3", "2.5", "11", 6],
    ]

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": [], "result": {"BTC/USDT": raw, "last": 0}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = KrakenMarketDataProvider(rest_base_url="https://example.test", client=client)
        result = await provider.get_historical_candles(
            "BTCUSDT",
            Timeframe.M5,
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 1, 0, 5, tzinfo=UTC),
        )

    assert [candle.open_time for candle in result.candles] == [datetime(2024, 1, 1, tzinfo=UTC)]


@pytest.mark.asyncio
async def test_kraken_rejects_naive_date_range() -> None:
    provider = KrakenMarketDataProvider(rest_base_url="https://example.test")
    with pytest.raises(ValueError, match="timezone-aware"):
        await provider.get_historical_candles(
            "BTCUSDT", Timeframe.M5, datetime(2024, 1, 1), datetime(2024, 1, 2)
        )
