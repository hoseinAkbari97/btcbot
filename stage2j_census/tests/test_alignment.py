"""Synthetic tests for the gap-aware alignment helpers."""

from __future__ import annotations

from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS, LoadStats
from stage2j_census.alignment import (
    _compare_upper_from_members,
    _expected_resume_open_ms,
    _missing_runs,
    _within_volume_tolerance,
)
from stage2j_census.series import FiveMinuteSupport, slot_count
from stage2j_census.tests.helpers import make_series

HOUR = TIMEFRAME_MS["1h"]


def one_hour_bars() -> list[dict]:
    return [
        {
            "open_time_ms": DEV_START_MS + index * HOUR,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
        }
        for index, (open_, high, low, close) in enumerate(
            [
                (100.0, 102.0, 99.0, 101.0),
                (101.0, 104.0, 100.0, 103.0),
                (103.0, 105.0, 102.0, 104.0),
                (104.0, 106.0, 103.0, 105.0),
            ]
        )
    ]


def four_hour_bars(volume: float = 4.0, high: float = 106.0) -> list[dict]:
    return [
        {
            "open_time_ms": DEV_START_MS,
            "open": 100.0,
            "high": high,
            "low": 99.0,
            "close": 105.0,
            "volume": volume,
        }
    ]


def test_complete_bucket_aggregation_matches_exactly() -> None:
    series_1h = make_series("1h", one_hour_bars())
    series_4h = make_series("4h", four_hour_bars())
    result = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
    )

    assert result["complete_buckets"] == 1
    assert result["gap_affected_buckets"] == 0
    assert result["ohlc_mismatch_buckets"] == 0
    assert result["volume_mismatches"] == 0
    assert result["passes_0_1_percent_price_tolerance"] is True


def test_missing_member_makes_the_bucket_gap_affected_not_a_mismatch() -> None:
    series_1h = make_series("1h", one_hour_bars()[:-1])
    series_4h = make_series("4h", four_hour_bars())
    result = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
    )

    assert result["complete_buckets"] == 0
    assert result["gap_affected_buckets"] == 1
    assert result["missing_members_total"] == 1
    assert result["ohlc_mismatch_buckets"] == 0


def test_exempt_supplied_bucket_is_reported_outside_the_denominator() -> None:
    series_1h = make_series("1h", one_hour_bars()[:-1])
    series_4h = make_series("4h", four_hour_bars())
    result = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
        exempt_slots=frozenset({0}),
    )

    assert result["complete_buckets"] == 0
    assert result["gap_affected_buckets"] == 0
    assert result["exempt_buckets"] == 1
    assert result["exempt_gap_affected_buckets"] == 1


def test_price_mismatch_is_counted_and_fails_the_tolerance() -> None:
    series_1h = make_series("1h", one_hour_bars())
    series_4h = make_series("4h", four_hour_bars(high=107.0))
    result = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
    )

    assert result["high_mismatches"] == 1
    assert result["ohlc_mismatch_buckets"] == 1
    assert result["ohlc_mismatch_share_of_complete"] == 1.0
    assert result["passes_0_1_percent_price_tolerance"] is False


def test_volume_uses_relative_tolerance_of_one_e_minus_nine() -> None:
    assert _within_volume_tolerance(4.0, 4.0 * (1.0 + 1e-10))
    assert not _within_volume_tolerance(4.0, 4.4)

    series_1h = make_series("1h", one_hour_bars())
    series_4h = make_series("4h", four_hour_bars(volume=4.4))
    result = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
    )
    assert result["volume_mismatches"] == 1


def test_fifteen_minute_bucket_requires_all_three_five_minute_members() -> None:
    bars = [
        {
            "open_time_ms": DEV_START_MS + index * TIMEFRAME_MS["15m"],
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 3.0,
        }
        for index in range(2)
    ]
    series_15m = make_series("15m", bars)
    size = series_15m.n_slots
    support = FiveMinuteSupport(
        member_15m=[3, 2] + [0] * (size - 2),
        member_1h=[0] * slot_count("1h"),
        aggregate_open_15m=[100.0, 100.0] + [float("nan")] * (size - 2),
        aggregate_high_15m=[101.0, 101.0] + [float("nan")] * (size - 2),
        aggregate_low_15m=[99.0, 99.0] + [float("nan")] * (size - 2),
        aggregate_close_15m=[100.5, 100.5] + [float("nan")] * (size - 2),
        aggregate_volume_15m=[3.0, 3.0] + [float("nan")] * (size - 2),
        aggregate_count_15m=[3, 2] + [0] * (size - 2),
        present_5m=[True] * 6,
        usable_5m=[True] * 6,
        stats=LoadStats(),
        counters={},
    )

    from stage2j_census.alignment import _compare_15m_from_5m

    result = _compare_15m_from_5m(support, series_15m)
    assert result["complete_buckets"] == 1
    assert result["gap_affected_buckets"] == 1
    assert result["missing_members_total"] == 1
    assert result["hlc_mismatch_buckets"] == 0


def test_missing_runs_report_the_last_present_bar_and_resume() -> None:
    present = [True, True, False, False, False, True]
    runs = _missing_runs(present, "1h")

    assert len(runs) == 1
    assert runs[0]["missing_bars"] == 3
    assert runs[0]["last_bar_before_utc"] == "2021-01-01T01:00:00+00:00"
    assert runs[0]["first_missing_open_utc"] == "2021-01-01T02:00:00+00:00"
    assert runs[0]["resumes_at_utc"] == "2021-01-01T05:00:00+00:00"


def test_resume_times_are_floored_per_timeframe() -> None:
    resume_ms = DEV_START_MS + 2 * HOUR + 30 * 60_000

    assert _expected_resume_open_ms(resume_ms, "5m") == resume_ms
    assert _expected_resume_open_ms(resume_ms, "15m") == resume_ms
    assert _expected_resume_open_ms(resume_ms, "1h") == DEV_START_MS + 2 * HOUR
    assert _expected_resume_open_ms(
        resume_ms, "4h"
    ) == DEV_START_MS
