"""Synthetic tests for the frozen Candidate D rules."""

from __future__ import annotations

import math

import pytest
from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS
from stage2j_census.candidate_d import run_candidate_d
from stage2j_census.tests.helpers import fake_regime, make_series

DAY_MS = 86_400_000
HOUR_MS = TIMEFRAME_MS["1h"]
SESSION_START = DEV_START_MS + 151 * DAY_MS  # 2021-06-01T00:00:00Z
SESSION_SLOT_15M = (SESSION_START - DEV_START_MS) // TIMEFRAME_MS["15m"]
Q_SLOT_1H = (SESSION_START + HOUR_MS - DEV_START_MS) // HOUR_MS


def one_hour_bars(through_slot: int, true_range: float = 1000.0) -> list[dict]:
    midpoint = 30_000.0 + true_range / 2.0
    return [
        {
            "open_time_ms": DEV_START_MS + slot * HOUR_MS,
            "open": midpoint,
            "high": 30_000.0 + true_range,
            "low": 30_000.0,
            "close": midpoint,
        }
        for slot in range(through_slot + 1)
    ]


def session_bars(start_slot: int, *, entry_open: float = 30_610.0) -> list[dict]:
    bars = []
    for offset in range(7):
        bars.append(
            {
                "open_time_ms": DEV_START_MS
                + (start_slot + offset) * TIMEFRAME_MS["15m"],
                "open": 30_000.0 if offset == 0 else 30_100.0,
                "high": 30_150.0,
                "low": 30_050.0,
                "close": 30_100.0,
                # Seven bars at HLC3=30,100 with total volume 28, plus one bar
                # at HLC3=30,600 with volume 7, reproduce the frozen VWAP
                # 30,200.0 exactly: (30,100*28 + 30,600*7) / 35.
                "volume": 4.0,
                "trade_count": 4,
            }
        )
    bars.append(
        {
            "open_time_ms": DEV_START_MS + (start_slot + 7) * TIMEFRAME_MS["15m"],
            "open": 30_600.0,
            "high": 30_600.0,
            "low": 30_600.0,
            "close": 30_600.0,
            "volume": 7.0,
            "trade_count": 7,
        }
    )
    bars.append(
        {
            "open_time_ms": DEV_START_MS + (start_slot + 8) * TIMEFRAME_MS["15m"],
            "open": entry_open,
            "high": entry_open + 40.0,
            "low": entry_open - 60.0,
            "close": entry_open - 10.0,
            "volume": 1.0,
            "trade_count": 1,
        }
    )
    return bars


def regime(pct: float = 63.0, n_slots: int = 1000) -> object:
    return fake_regime(
        permission=[1] * n_slots,
        pct=[pct] * n_slots,
        run_id=[0] * n_slots,
        n_slots=n_slots,
    )


def series_pair(
    *,
    entry_open: float = 30_610.0,
    through_slot: int = Q_SLOT_1H + 1,
    true_range: float = 1000.0,
    include_entry: bool = True,
) -> tuple:
    bars_15m = session_bars(SESSION_SLOT_15M, entry_open=entry_open)
    if not include_entry:
        bars_15m = bars_15m[:-1]
    return (
        make_series("15m", bars_15m),
        make_series("1h", one_hour_bars(through_slot, true_range)),
    )


def test_frozen_worked_example_arithmetic_and_pipeline() -> None:
    series_15m, series_1h = series_pair()
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"] == {
        "S0": 3831,
        "S1": 9,
        "S2": 1,
        "S3": 1,
        "S4": 1,
        "S5": 1,
        "S6": 1,
        "S7": 1,
        "S8": 1,
        "S9": 1,
    }
    assert all(result["reconciliation"].values())
    assert result["primary_labels"]["measurement_window_incomplete"] == 3830

    signal = result["pre_gate"][0]
    assert signal["key"] == "D:2021-06-01T00:00:00+00:00|ASIA"
    assert signal["p0"] == 30_000.0
    assert signal["p1"] == 30_600.0
    assert signal["r2"] == pytest.approx(0.02)
    assert signal["threshold"] == pytest.approx(0.5 * 1000.0 / 30_000.0)
    assert signal["vwap"] == pytest.approx(30_200.0)
    assert signal["p1"] > signal["vwap"]
    assert signal["regime_pct"] == 63.0
    assert signal["entry_open"] == 30_610.0
    assert signal["stop"] == 29_610.0
    assert signal["D"] == 1000.0
    assert signal["stop_fraction"] == pytest.approx(1000.0 / 30_610.0)
    assert signal["cost_R"] == pytest.approx(0.0026 * 30_610.0 / 1000.0)
    assert signal["cluster_id"] == 0


def test_sessions_partition_the_utc_day_without_overlap() -> None:
    series = make_series(
        "15m",
        [
            {
                "open_time_ms": DEV_START_MS,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
            }
        ],
    )
    result = run_candidate_d(
        series,
        make_series("1h", one_hour_bars(5)),
        regime(),
        dev_end_ms=DEV_START_MS + DAY_MS,
    )

    assert result["counts"]["S0"] == 3
    assert result["per_session"]["ASIA"]["S0"] == 1
    assert result["per_session"]["EUROPE"]["S0"] == 1
    assert result["per_session"]["US"]["S0"] == 1
    assert result["primary_labels"]["measurement_window_incomplete"] == 3


def test_measurement_window_must_contain_all_eight_bars() -> None:
    series_15m, series_1h = series_pair()
    series_15m.usable[SESSION_SLOT_15M + 4] = False
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S2"] == 0
    assert result["primary_labels"]["measurement_window_incomplete"] == 3831


def test_budget_outside_the_band_rejects_at_s4() -> None:
    series_15m, series_1h = series_pair()
    result = run_candidate_d(series_15m, series_1h, regime(pct=90.0))

    assert result["counts"]["S3"] == 1
    assert result["counts"]["S4"] == 0
    assert result["primary_labels"]["budget_out_of_band"] == 1


def test_unknown_budget_is_warmup_budget() -> None:
    series_15m, series_1h = series_pair()
    result = run_candidate_d(series_15m, series_1h, regime(pct=float("nan")))

    assert result["counts"]["S4"] == 0
    assert result["primary_labels"]["warmup_budget"] == 1


def test_expected_q_bar_absent_is_stop_atr_unavailable() -> None:
    series_15m, _ = series_pair()
    series_1h = make_series(
        "1h",
        [
            {
                "open_time_ms": DEV_START_MS + (Q_SLOT_1H - 1) * HOUR_MS,
                "open": 30_500.0,
                "high": 31_000.0,
                "low": 30_000.0,
                "close": 30_500.0,
            },
            {
                "open_time_ms": DEV_START_MS + (Q_SLOT_1H + 1) * HOUR_MS,
                "open": 30_500.0,
                "high": 31_000.0,
                "low": 30_000.0,
                "close": 30_500.0,
            },
        ],
    )
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S3"] == 0
    assert result["primary_labels"]["stop_atr_unavailable"] == 1


def test_q_before_the_local_atr_warmup_is_warmup_atr() -> None:
    series_15m, _ = series_pair()
    series_1h = make_series(
        "1h",
        [
            {
                "open_time_ms": DEV_START_MS + Q_SLOT_1H * HOUR_MS,
                "open": 30_500.0,
                "high": 31_000.0,
                "low": 30_000.0,
                "close": 30_500.0,
            },
            {
                "open_time_ms": DEV_START_MS + (Q_SLOT_1H + 1) * HOUR_MS,
                "open": 30_500.0,
                "high": 31_000.0,
                "low": 30_000.0,
                "close": 30_500.0,
            },
        ],
    )
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S3"] == 0
    assert result["primary_labels"]["warmup_atr"] == 1


def test_below_vwap_rejects_after_the_threshold_passes() -> None:
    series_15m, series_1h = series_pair()
    for offset in range(7):
        series_15m.high[SESSION_SLOT_15M + offset] = 31_100.0
        series_15m.low[SESSION_SLOT_15M + offset] = 30_900.0 if offset else 29_900.0
        series_15m.close[SESSION_SLOT_15M + offset] = 31_000.0
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S3"] == 1
    assert result["counts"]["S5"] == 0
    assert result["primary_labels"]["below_vwap"] == 1


def test_entry_diagnostics_are_recorded_as_secondary_labels() -> None:
    series_15m, series_1h = series_pair()
    entry_slot = SESSION_SLOT_15M + 8
    series_15m.volume[entry_slot] = 0.0
    series_15m.trade_count[entry_slot] = 0
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S7"] == 1
    assert result["diagnostics"]["zero_volume_entry"] == 1
    assert result["secondary_labels"]["zero_volume_entry"] == 1
    assert result["primary_labels"].get("no_entry_bar", 0) == 0


def test_missing_entry_bar_rejects_without_skipping_forward() -> None:
    series_15m, series_1h = series_pair(include_entry=False)
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["no_entry_bar"] == 1


def test_entry_at_exclusive_interval_end_is_entry_outside_interval() -> None:
    series_15m, series_1h = series_pair()
    result = run_candidate_d(
        series_15m,
        series_1h,
        regime(),
        dev_end_ms=SESSION_START + 2 * HOUR_MS,
    )

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["entry_outside_interval"] == 1


def test_nonpositive_entry_open_is_invalid_entry_price() -> None:
    series_15m, series_1h = series_pair(entry_open=0.0)
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["invalid_entry_price"] == 1


def test_stop_below_zero_is_invalid_stop() -> None:
    series_15m, series_1h = series_pair(entry_open=500.0)
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["invalid_stop"] == 1


def test_cost_gate_population_is_pregate_s6_not_s7() -> None:
    series_15m, series_1h = series_pair(true_range=200.0)
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S6"] == 1
    assert result["counts"]["S7"] == 0
    assert result["counts"]["S8"] == 0
    assert result["counts"]["S9"] == 0
    assert result["primary_labels"]["cost_gate"] == 1
    assert result["pre_gate"][0]["cost_R"] > 0.20


def test_24h_non_overlap_uses_the_cost_feasible_population() -> None:
    bars = session_bars(SESSION_SLOT_15M) + session_bars(SESSION_SLOT_15M + 32)
    series_15m = make_series("15m", bars)
    series_1h = make_series("1h", one_hour_bars(Q_SLOT_1H + 9))
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S7"] == 2
    assert result["counts"]["S8"] == 2
    assert result["counts"]["S9"] == 1
    assert result["non_overlap"]["24h"]["rejected_count"] == 1
    assert result["per_session"]["ASIA"]["S9"] == 1
    assert result["per_session"]["EUROPE"]["S9"] == 0


def test_session_full_data_is_a_post_count_diagnostic() -> None:
    series_15m, series_1h = series_pair()
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["session_full_data"]["sessions_false"] == 3831
    assert result["session_full_data"]["feasible_signals_from_incomplete_sessions"] == 1
    assert result["counts"]["S7"] == 1


def test_invalid_15m_membership_makes_the_session_not_evaluable() -> None:
    series_15m, series_1h = series_pair()
    series_15m.partial[SESSION_SLOT_15M] = True
    series_15m.usable[SESSION_SLOT_15M] = False
    result = run_candidate_d(series_15m, series_1h, regime())

    assert result["counts"]["S2"] == 0
    assert math.isnan(series_15m.atr[SESSION_SLOT_15M + 7])
