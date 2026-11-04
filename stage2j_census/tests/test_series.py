"""Synthetic tests for compact series construction and the shared Wilder ATR."""

from __future__ import annotations

import json
import math

from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS, LoadStats, iter_candles
from stage2j_census.series import (
    build_series,
    is_on_grid,
    slot_count,
    slot_index,
    slot_open_ms,
)
from stage2j_census.tests.helpers import make_series

HOUR = TIMEFRAME_MS["1h"]


def bar(index: int, open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {
        "open_time_ms": DEV_START_MS + index * HOUR,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


def flat_bars(count: int) -> list[dict[str, float]]:
    return [bar(index, 98.4, 99.4, 97.4, 98.4) for index in range(count)]


def test_slot_arithmetic_uses_the_frozen_epoch() -> None:
    assert slot_open_ms(0, "1h") == DEV_START_MS
    assert slot_index(DEV_START_MS, "1h") == 0
    assert slot_index(DEV_START_MS + 4 * HOUR, "1h") == 4
    assert is_on_grid(DEV_START_MS + 4 * HOUR, "1h")
    assert not is_on_grid(DEV_START_MS + HOUR + 1, "1h")
    assert slot_count("4h") == 7662


def test_wilder_atr_seed_and_recursion_match_the_shared_worked_check() -> None:
    bars = flat_bars(13)
    bars.append(bar(13, 100.0, 100.4, 99.9, 100.2))
    bars.append(bar(14, 100.0, 104.0, 99.5, 103.5))
    series = make_series("1h", bars)

    assert math.isnan(series.atr[12])
    assert series.tr[13] == 2.0
    assert series.atr[13] == 2.0
    assert series.atr[14] == (2.0 * 13.0 + 4.5) / 14.0
    assert series.atr[14] == 2.1785714285714284


def test_atr_is_segment_scoped_and_resets_after_a_missing_bar() -> None:
    bars = flat_bars(7) + flat_bars(7)[1:]
    for offset, item in enumerate(bars[7:], start=8):
        item["open_time_ms"] = DEV_START_MS + offset * HOUR
    series = make_series("1h", bars)

    assert series.segment_id[6] == 0
    assert series.local_index[6] == 6
    assert series.segment_id[8] == 1
    assert series.local_index[8] == 0
    assert series.local_index[13] == 5
    assert math.isnan(series.atr[13])
    assert series.stats.extra["segments"] == 2


def _write_15m_fixture(path) -> None:
    records = []
    for index, (open_price, close_price) in enumerate(
        [(100.0, 101.0), (101.0, 102.0), (102.0, 103.0)]
    ):
        records.append(
            {
                "symbol": "BTCUSDT",
                "timeframe": "15m",
                "open_time": f"2021-01-01 {index * 15 // 60:02d}:{index * 15 % 60:02d}:00+00:00",
                "close_time": (
                    f"2021-01-01 {index * 15 // 60:02d}:"
                    f"{index * 15 % 60 + 14:02d}:59.999+00:00"
                ),
                "open": str(open_price),
                "high": str(close_price + 1.0),
                "low": str(open_price - 1.0),
                "close": str(close_price),
                "volume": "1.0",
                "trade_count": "10",
                "is_closed": "True",
            }
        )
    path.write_text(json.dumps(records), encoding="utf-8")


def test_build_series_applies_partial_bucket_membership(tmp_path) -> None:
    path = tmp_path / "15m.json"
    _write_15m_fixture(path)
    member_count = [0] * slot_count("15m")
    member_count[0] = 3
    member_count[1] = 2
    member_count[2] = 3

    series = build_series(
        "15m", str(path), member_count=member_count, expected_members=3
    )

    assert series.usable[0] is True
    assert series.partial[1] is True
    assert series.usable[1] is False
    assert series.usable[2] is True
    assert series.stats.extra["partial_bars"] == 1


def test_duplicate_open_time_keeps_the_first_record_in_file_order(tmp_path) -> None:
    path = tmp_path / "dupes.json"
    _write_15m_fixture(path)
    records = json.loads(path.read_text(encoding="utf-8"))
    duplicate = dict(records[0])
    duplicate["close"] = "999.0"
    path.write_text(json.dumps([records[0], duplicate, records[1], records[2]]), encoding="utf-8")

    stats = LoadStats()
    candles = list(iter_candles(path, "15m", stats=stats))

    assert [candle.open_time_ms for candle in candles] == [
        DEV_START_MS,
        DEV_START_MS + TIMEFRAME_MS["15m"],
        DEV_START_MS + 2 * TIMEFRAME_MS["15m"],
    ]
    assert candles[0].close == 101
    assert stats.duplicate_timestamps == 1
