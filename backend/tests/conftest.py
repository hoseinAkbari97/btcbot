from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.schemas.market_data import CandleData, Timeframe


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def make_candle(
    minute: int = 0,
    *,
    timeframe: Timeframe = Timeframe.M5,
    open_price: str = "50000",
    high: str = "50100",
    low: str = "49900",
    close: str = "50050",
    volume: str = "10",
) -> CandleData:
    open_time = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)
    return CandleData(
        symbol="BTCUSDT",
        timeframe=timeframe,
        open_time=open_time,
        close_time=open_time + timedelta(seconds=timeframe.seconds) - timedelta(milliseconds=1),
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        quote_volume=Decimal("500000"),
        trade_count=100,
        taker_buy_base_volume=Decimal("5"),
        taker_buy_quote_volume=Decimal("250000"),
        is_closed=True,
    )
