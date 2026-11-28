from datetime import UTC, datetime, timedelta

from conftest import make_candle

from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe


async def test_list_candles_can_select_a_source_and_orders_ties_deterministically(
    db_session,
) -> None:
    repository = MarketDataRepository(db_session)
    source_a, instrument = await repository.ensure_catalog(
        "provenance-a", "https://a.invalid", "BTCUSDT"
    )
    source_b, _ = await repository.ensure_catalog(
        "provenance-b", "https://b.invalid", "BTCUSDT"
    )
    base = datetime(2024, 1, 1, tzinfo=UTC)
    a = make_candle(0, open_price="100", close="101")
    b = make_candle(0, open_price="200", close="201")
    await repository.upsert_candles([a], source_a.id, instrument.id)
    await repository.upsert_candles([b], source_b.id, instrument.id)
    await db_session.commit()

    only_a = await repository.list_candles(
        "BTCUSDT", Timeframe.M5, base, base + timedelta(minutes=5), 10,
        source_ids=[source_a.id],
    )
    both = await repository.list_candles(
        "BTCUSDT", Timeframe.M5, base, base + timedelta(minutes=5), 10
    )
    repeated = await repository.list_candles(
        "BTCUSDT", Timeframe.M5, base, base + timedelta(minutes=5), 10
    )

    assert len(only_a) == 1
    assert only_a[0].source_id == source_a.id
    assert len(both) == 2
    assert [row.id for row in both] == [row.id for row in repeated]
    assert [row.source_id for row in both] == sorted(row.source_id for row in both)
