from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.schemas.market_data import CandleData
from app.services.research.events import ResearchEvent
from app.services.research.split_filter import (
    assign_split_to_time,
    filter_events_for_split,
    last_evaluated_index,
    window_fits_in_split,
)


def _candle(
    t: datetime, o: str = "100", h: str = "101", low: str = "99", c: str = "100"
) -> CandleData:
    return CandleData(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time=t,
        close_time=t,
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(low),
        close=Decimal(c),
        volume=Decimal("1"),
    )


def test_assign_split_boundaries_are_half_open() -> None:
    assert assign_split_to_time(datetime(2021, 1, 1, tzinfo=UTC)) == "development"
    assert assign_split_to_time(datetime(2024, 6, 30, 23, 55, tzinfo=UTC)) == "development"
    # The documented development end is 2024-07-01T00:00Z, exclusive.
    assert assign_split_to_time(datetime(2024, 7, 1, tzinfo=UTC)) == "validation"
    assert assign_split_to_time(datetime(2025, 7, 1, tzinfo=UTC)) == "oos"
    assert assign_split_to_time(datetime(2026, 9, 1, tzinfo=UTC)) is None
    assert assign_split_to_time(datetime(2020, 12, 31, tzinfo=UTC)) is None


def test_window_fits_in_split() -> None:
    # Entry at confirmation_index + 1, horizon is 12 evaluated candles including
    # entry, so last_evaluated = confirmation_index + 12.
    assert last_evaluated_index(100) == 112
    assert window_fits_in_split(100, 112) is True  # fits exactly
    assert window_fits_in_split(100, 111) is False  # crosses boundary


def _make_event(conf_index: int, conf_time: datetime) -> ResearchEvent:
    return ResearchEvent(
        kind="liquidity_sweep",
        detector="liquidity_sweep",
        event_index=conf_index - 1,
        event_time=conf_time,
        confirmation_index=conf_index,
        confirmation_time=conf_time,
        price=Decimal("100"),
        features={"recovery_ratio": Decimal("0.6"), "wick_ratio": Decimal("0.6")},
        context={"level_price": "100", "level_type": "equal_highs", "side": "short"},
    )


def test_filter_excludes_warmup() -> None:
    candles = [
        _candle(datetime(2021, 1, 1, tzinfo=UTC) + timedelta(minutes=5*i))
        for i in range(200)
    ]
    events = [_make_event(10, candles[10].close_time)]
    kept, stats = filter_events_for_split(
        events, candles, "development", split_start_idx=20, split_end_idx=150
    )
    assert len(kept) == 0
    assert stats["warmup_excluded"] == 1


def test_filter_excludes_boundary_crossing() -> None:
    base = datetime(2021, 6, 1, tzinfo=UTC)
    candles = [_candle(base + timedelta(minutes=5*i)) for i in range(200)]
    # Window needs to fit: last_evaluated = conf_index + 12 <= split_end_idx
    events = [_make_event(150, candles[150].close_time)]  # needs up to 162, but split ends at 160
    kept, stats = filter_events_for_split(
        events, candles, "development", split_start_idx=0, split_end_idx=160
    )
    assert len(kept) == 0
    assert stats["boundary_crossing_excluded"] == 1


def test_filter_excludes_episode_crossing_boundary() -> None:
    base = datetime(2021, 6, 1, tzinfo=UTC)
    candles = [_candle(base + timedelta(minutes=5*i)) for i in range(200)]
    events = [
        _make_event(148, candles[148].close_time),
        _make_event(150, candles[150].close_time),
    ]
    kept, stats = filter_events_for_split(
        events, candles, "development", split_start_idx=0, split_end_idx=160
    )
    # First fits exactly (ends at 160), second crosses boundary (needs to 162)
    assert len(kept) == 1
    assert stats["boundary_crossing_excluded"] == 1


def test_filter_keeps_valid_events() -> None:
    base = datetime(2021, 6, 1, tzinfo=UTC)
    candles = [_candle(base + timedelta(minutes=5*i)) for i in range(200)]
    events = [_make_event(50, candles[50].close_time)]
    kept, stats = filter_events_for_split(
        events, candles, "development", split_start_idx=0, split_end_idx=200
    )
    assert len(kept) == 1
    assert stats["kept"] == 1
