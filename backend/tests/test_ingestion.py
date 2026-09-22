from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import make_candle
from sqlalchemy import func, select

from app.models.market_data import Candle, DataQualityReport
from app.schemas.market_data import CandleData, Timeframe
from app.services.market_data.base import HistoricalResult, MarketDataProvider
from app.services.market_data.ingestion import HistoricalIngestionService
from app.services.market_data.storage import ParquetCandleStore, RawDataStore


class FakeProvider(MarketDataProvider):
    name = "fixture_provider"
    rest_base_url = "https://fixture.invalid"

    async def get_historical_candles(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> HistoricalResult:
        candles = [make_candle(0), make_candle(5)]
        return HistoricalResult(candles, [[["raw"]]], [{"fixture": True}])

    async def stream_candles(self, symbol: str, timeframe: Timeframe) -> AsyncIterator[CandleData]:
        if False:
            yield make_candle()

    async def get_trades(
        self, symbol: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[dict[str, Any]]:
        return []

    async def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        return {}


@pytest.mark.asyncio
async def test_ingestion_persists_raw_parquet_database_and_quality_report(
    db_session, tmp_path
) -> None:
    service = HistoricalIngestionService(
        db_session,
        FakeProvider(),
        RawDataStore(tmp_path / "raw"),
        ParquetCandleStore(tmp_path / "parquet"),
    )
    result = await service.ingest(
        "BTCUSDT",
        Timeframe.M5,
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
    )

    assert result.fetched == 2
    assert result.stored == 2
    assert result.passed is True
    assert result.raw_file.exists()
    assert all(path.exists() for path in result.parquet_files)
    assert await db_session.scalar(select(func.count()).select_from(Candle)) == 2
    report = await db_session.scalar(select(DataQualityReport))
    assert report is not None
    assert report.row_count == 2
    assert report.passed is True
