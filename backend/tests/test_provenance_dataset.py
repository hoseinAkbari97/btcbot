from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.market_data import CandleData, Timeframe
from app.services.provenance.dataset import (
    DATASET_FINGERPRINT_VERSION,
    DatasetFingerprintBuilder,
    dataset_identity,
    dataset_rows_identity,
)


def candle(minute: int, close: str = "100", volume: str = "10") -> CandleData:
    start = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)
    return CandleData(
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        open_time=start,
        close_time=start + timedelta(minutes=5),
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal(close),
        volume=Decimal(volume),
        quote_volume=Decimal("1000"),
        trade_count=10,
        taker_buy_base_volume=Decimal("5"),
        taker_buy_quote_volume=Decimal("500"),
        is_closed=True,
    )


def identity(candles: list[CandleData], sources: list[str] | None = None):
    return dataset_identity(
        candles,
        sources or ["source-1"] * len(candles),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
    )


def test_fingerprint_is_stable_for_the_same_ordered_selection() -> None:
    first = identity([candle(0), candle(5)])
    second = identity([candle(0), candle(5)])

    assert first.fingerprint == second.fingerprint
    assert first.version == DATASET_FINGERPRINT_VERSION
    assert first.candle_count == 2
    assert first.source_ids == ("source-1",)


def test_decimal_representation_does_not_change_the_fingerprint() -> None:
    assert identity([candle(0, volume="10.0")]).fingerprint == identity(
        [candle(0, volume="10.00")]
    ).fingerprint


def test_changed_values_sources_and_order_change_the_fingerprint() -> None:
    baseline = identity([candle(0), candle(5)])

    assert identity([candle(0, close="101"), candle(5)]).fingerprint != baseline.fingerprint
    assert identity([candle(0), candle(5)], ["source-2", "source-2"]).fingerprint != (
        baseline.fingerprint
    )
    assert identity([candle(5), candle(0)]).fingerprint != baseline.fingerprint


def test_duplicate_open_times_are_counted() -> None:
    duplicate = identity([candle(0), candle(0)])

    assert duplicate.duplicate_open_times == 1


def test_streaming_builder_matches_in_memory_identity() -> None:
    rows = [(candle(0), "source-1"), (candle(5), "source-1")]
    builder = DatasetFingerprintBuilder(symbol="BTCUSDT", timeframe="5m")
    for row, source_id in rows:
        builder.add(row, source_id)

    assert builder.build().fingerprint == dataset_rows_identity(
        iter(rows), symbol="BTCUSDT", timeframe=Timeframe.M5
    ).fingerprint


def test_source_id_count_must_match_candle_count() -> None:
    with pytest.raises(ValueError, match="counts must match"):
        dataset_identity([candle(0)], [], symbol="BTCUSDT", timeframe=Timeframe.M5)
