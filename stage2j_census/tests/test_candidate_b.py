"""Synthetic tests for the frozen Candidate B rules."""

from __future__ import annotations

import pytest
from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS
from stage2j_census.candidate_b import run_candidate_b
from stage2j_census.series import slot_open_ms
from stage2j_census.tests.helpers import fake_regime, make_series

HOUR = TIMEFRAME_MS["1h"]


def bar(index: int, open_: float, high: float, low: float, close: float) -> dict:
    return {
        "open_time_ms": DEV_START_MS + index * HOUR,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


def flat_bars(count: int, high: float = 99.4, low: float = 97.4) -> list[dict]:
    return [bar(index, 98.4, high, low, 98.4) for index in range(count)]


def worked_bars() -> list[dict]:
    """Frozen B section 10.1 worked example, with ATR[e-1] fixed at 2.0."""
    bars = flat_bars(13)
    bars.append(bar(13, 100.0, 100.4, 99.9, 100.2))
    bars.append(bar(14, 100.0, 104.0, 99.5, 103.5))
    bars.append(bar(15, 103.5, 103.8, 102.9, 103.0))
    bars.append(bar(16, 103.0, 104.2, 103.0, 103.9))
    bars.append(bar(17, 104.0, 104.5, 103.5, 104.2))
    return bars


def regime(n_slots: int = 18, permission: int = 1) -> object:
    return fake_regime(
        permission=[permission] * n_slots,
        pct=[50.0] * n_slots,
        run_id=[0] * n_slots,
        n_slots=n_slots,
    )


def test_frozen_worked_example_counters_and_arithmetic() -> None:
    series = make_series("1h", worked_bars())
    result = run_candidate_b(series, regime())

    assert result["counts"] == {
        "S1": 18,
        "S2": 4,
        "S3": 1,
        "S4": 1,
        "S5": 1,
        "S6": 1,
        "S7": 1,
        "S8": 1,
        "S9": 1,
        "S10": 1,
    }
    assert all(result["reconciliation"].values())

    signal = result["pre_gate"][0]
    assert signal["key"] == "B:2021-01-01T14:00:00+00:00"
    assert signal["entry_time_iso"] == "2021-01-01T17:00:00+00:00"
    assert signal["signal_time_ms"] == slot_open_ms(16, "1h") + HOUR - 1
    assert signal["entry_open"] == 104.0
    assert signal["stop"] == 99.5
    assert signal["D"] == 4.5
    assert signal["stop_fraction"] == pytest.approx(4.5 / 104.0)
    assert signal["cost_R"] == pytest.approx(0.0026 * 104.0 / 4.5)
    assert signal["regime_pct"] == 50.0
    assert signal["cluster_id"] == 0


def test_expansion_at_local_index_13_is_warmup_even_with_a_huge_range() -> None:
    bars = flat_bars(13)
    bars.append(bar(13, 98.4, 108.0, 98.0, 107.5))
    result = run_candidate_b(make_series("1h", bars), regime(14))

    assert result["counts"]["S2"] == 0
    assert result["counts"]["S3"] == 0


@pytest.mark.parametrize(
    ("open_", "close", "accepted"),
    [
        (100.80, 103.0, True),  # body/range exactly 0.55, close location 0.75
        (100.85, 103.0, False),  # body/range 0.5375
        (100.50, 102.9, False),  # close location 0.725
    ],
)
def test_expansion_directional_boundaries_are_inclusive(
    open_: float, close: float, accepted: bool
) -> None:
    bars = flat_bars(13)
    bars.append(bar(13, 100.0, 100.4, 99.9, 100.2))
    bars.append(bar(14, open_, 104.0, 100.0, close))
    result = run_candidate_b(make_series("1h", bars), regime(15))
    assert (result["counts"]["S3"] == 1) is accepted


def test_touch_penetration_above_half_atr_is_too_deep() -> None:
    bars = worked_bars()
    bars[15] = bar(15, 103.5, 103.8, 102.19, 103.0)
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["retest_too_deep"] == 1


def test_close_below_the_invalidation_bound_breaks_structure() -> None:
    bars = worked_bars()
    bars[16] = bar(16, 103.0, 103.0, 101.5, 102.0)
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["structure_broken"] == 1


def test_no_confirmation_within_three_bars_after_the_touch_times_out() -> None:
    bars = worked_bars()[:17]
    bars[16] = bar(16, 103.0, 103.4, 103.0, 103.4)
    bars.append(bar(17, 103.4, 103.4, 103.2, 103.2))
    bars.append(bar(18, 103.2, 103.4, 103.1, 103.2))
    result = run_candidate_b(make_series("1h", bars), regime(19))

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["resumption_timeout"] == 1


def test_no_retest_touch_within_six_bars_times_out() -> None:
    bars = worked_bars()[:15]
    for index in range(15, 21):
        bars.append(bar(index, 104.0, 104.5, 104.1, 104.2))
    result = run_candidate_b(make_series("1h", bars), regime(21))

    assert result["counts"]["S6"] == 0
    assert result["primary_labels"]["retest_timeout"] == 1


def test_missing_entry_bar_rejects_without_skipping_forward() -> None:
    bars = worked_bars()[:-1]
    result = run_candidate_b(make_series("1h", bars), regime(17))

    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["no_entry_bar"] == 1


def test_off_grid_entry_bar_is_no_entry_bar() -> None:
    bars = worked_bars()
    bars[-1]["exact"] = False
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["no_entry_bar"] == 1


def test_present_entry_bar_with_unusable_close_time_properties_is_accepted() -> None:
    bars = worked_bars()
    bars[-1]["volume"] = 0.0
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S7"] == 1
    assert result["counts"]["S8"] == 1
    assert result["diagnostics"]["zero_volume_entry"] == 1
    assert result["primary_labels"].get("no_entry_bar", 0) == 0


def test_entry_at_exclusive_interval_end_is_entry_outside_interval() -> None:
    result = run_candidate_b(
        make_series("1h", worked_bars()),
        regime(),
        dev_end_ms=slot_open_ms(17, "1h"),
    )

    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["entry_outside_interval"] == 1


def test_nonpositive_entry_open_is_invalid_entry_price() -> None:
    bars = worked_bars()
    bars[-1].update({"open": 0.0, "low": 0.0})
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["invalid_entry_price"] == 1


def test_entry_at_or_below_the_setup_low_is_invalid_stop() -> None:
    bars = worked_bars()
    bars[-1].update({"open": 99.0, "low": 98.5, "high": 99.5, "close": 99.2})
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["invalid_stop"] == 1


def test_a_stop_tighter_than_the_gate_fails_cost_without_widening() -> None:
    bars = [bar(index, 98.4, 98.5, 98.3, 98.4) for index in range(13)]
    bars.append(bar(13, 98.4, 98.9, 98.3, 98.4))
    bars.append(bar(14, 103.2, 103.7, 103.1, 103.6))
    bars.append(bar(15, 103.6, 103.8, 103.5, 103.7))
    bars.append(bar(16, 103.7, 103.9, 103.4, 103.8))
    bars.append(bar(17, 103.8, 104.0, 103.6, 103.9))
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S7"] == 1
    assert result["counts"]["S8"] == 0
    assert result["primary_labels"]["cost_gate"] == 1
    assert result["pre_gate"][0]["stop"] == 103.1
    assert result["pre_gate"][0]["cost_R"] > 0.20


def test_regime_failure_at_expansion_still_absorbs_later_expansions() -> None:
    bars = worked_bars()
    bars[15] = bar(15, 103.5, 108.0, 103.0, 107.5)
    bars[16] = bar(16, 107.5, 107.8, 103.8, 103.9)
    bars.append(bar(17, 103.9, 104.2, 103.5, 103.8))
    bars.append(bar(18, 103.8, 104.0, 103.4, 103.6))
    state = fake_regime(
        permission=[1, 1, 0, 1, 1],
        pct=[50.0] * 5,
        run_id=[0, 0, -1, 1, 1],
        n_slots=19,
    )
    result = run_candidate_b(make_series("1h", bars), state)

    assert result["counts"]["S3"] == 2
    assert result["counts"]["S4"] == 1
    assert result["counts"]["S5"] == 0
    assert result["counts"]["S6"] == 0
    assert result["diagnostics"]["expansions_absorbed"] == 1
    assert result["primary_labels"]["regime_not_permitted"] == 1
    assert result["reconciliation"]["S3_equals_S4_plus_expansions_absorbed"] is True


def test_confirmation_bar_that_is_also_an_expansion_is_absorbed() -> None:
    bars = worked_bars()
    bars[16] = bar(16, 103.0, 108.0, 102.9, 107.5)
    result = run_candidate_b(make_series("1h", bars), regime())

    assert result["counts"]["S3"] == 2
    assert result["counts"]["S4"] == 1
    assert result["diagnostics"]["expansions_absorbed"] == 1
    assert result["counts"]["S7"] == 1
    assert result["reconciliation"]["S3_equals_S4_plus_expansions_absorbed"] is True


def test_permission_unknown_at_confirmation_is_regime_lost() -> None:
    series = make_series("1h", worked_bars())
    state = fake_regime(
        permission=[1, 1, 1, -1],
        pct=[50.0, 50.0, 50.0, float("nan")],
        run_id=[0, 0, 0, -1],
        n_slots=18,
    )
    result = run_candidate_b(series, state)

    assert result["counts"]["S6"] == 1
    assert result["counts"]["S7"] == 0
    assert result["primary_labels"]["regime_lost"] == 1

