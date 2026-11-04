"""Synthetic tests for the descriptive statistics and accounting helpers."""

from __future__ import annotations

import math

import pytest
from stage2j_census.stats import (
    calendar_counts,
    capital_geometry,
    cluster_analysis,
    cost_bucket,
    cost_bucket_table,
    cost_sensitivity,
    decile_counts,
    deduplicate_by_entry,
    detectable_effect,
    distribution,
    median,
    non_overlap,
    pct_decile,
    quantile,
    ratio,
    stop_distance_table,
)

HOUR_MS = 3_600_000


def test_median_uses_the_mean_of_the_two_middle_values() -> None:
    assert median([3.0, 1.0, 2.0]) == 2.0
    assert median([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert median([]) is None


def test_type_7_quantiles_and_missing_values() -> None:
    values = [0.0, 10.0, 20.0, 30.0]
    assert quantile(values, 0.25) == 7.5
    assert quantile(values, 0.90) == 27.0
    assert quantile([5.0], 0.75) == 5.0
    assert quantile([], 0.5) is None
    assert distribution([])["count"] == 0
    assert distribution(values)["mean"] == 15.0


@pytest.mark.parametrize(
    ("value", "label"),
    [
        (0.10, "<= 0.10"),
        (0.1000001, "(0.10, 0.20]"),
        (0.20, "(0.10, 0.20]"),
        (0.30, "(0.20, 0.30]"),
        (0.50, "(0.30, 0.50]"),
        (0.5000001, "> 0.50"),
    ],
)
def test_cost_bucket_endpoints_belong_to_the_lower_bucket(
    value: float, label: str
) -> None:
    assert cost_bucket(value) == label


def test_cost_bucket_table_is_exhaustive() -> None:
    table = cost_bucket_table([0.05, 0.2, 0.4, 0.9])
    assert [row["count"] for row in table] == [1, 1, 0, 1, 1]
    assert math.isclose(sum(row["share"] for row in table), 1.0)


def test_cost_gate_boundary_is_inclusive_and_uses_the_pre_gate_population() -> None:
    records = [
        {"entry_open": 100.0, "D": 1.3},
        {"entry_open": 100.0, "D": 0.5},
    ]
    sensitivity = cost_sensitivity(records)

    assert sensitivity["26bp"]["population"] == 2
    assert sensitivity["26bp"]["M_all"] == pytest.approx(0.36)
    assert sensitivity["26bp"]["passing"] == 1
    assert sensitivity["26bp"]["M_feasible"] == pytest.approx(0.2)
    assert sensitivity["10bp"]["passing"] == 2
    assert sensitivity["39bp"]["passing"] == 0
    assert sensitivity["52bp"]["passing"] == 0


def test_stop_distance_share_below_1_30_percent_is_strict() -> None:
    table = stop_distance_table(
        [
            {"entry_open": 100.0, "D": 1.3},
            {"entry_open": 100.0, "D": 1.29},
        ]
    )
    assert table["count_below_1_30_percent"] == 1
    assert table["share_below_1_30_percent"] == 0.5


def test_non_overlap_boundary_is_inclusive() -> None:
    records = [
        {"key": "A", "entry_time_ms": 0},
        {"key": "B", "entry_time_ms": 72 * HOUR_MS},
        {"key": "C", "entry_time_ms": 144 * HOUR_MS},
    ]
    result = non_overlap(records, 72.0)

    assert result["accepted_keys"] == ["A", "B", "C"]
    assert result["rejected_count"] == 0
    assert result["spacing_hours"]["min"] == 72.0


def test_non_overlap_rejects_just_below_the_boundary() -> None:
    records = [
        {"key": "A", "entry_time_ms": 0},
        {"key": "B", "entry_time_ms": 72 * HOUR_MS - 1},
    ]
    result = non_overlap(records, 72.0)
    assert result["accepted_count"] == 1
    assert result["rejected"][0]["key"] == "B"


def test_equal_entry_times_keep_the_lexicographically_smaller_key() -> None:
    records = [
        {"key": "B", "entry_time_ms": 5},
        {"key": "A", "entry_time_ms": 5},
    ]
    result = non_overlap(records, 24.0)
    assert result["accepted_keys"] == ["A"]
    assert result["rejected"][0]["key"] == "B"


def test_deduplicate_by_entry_keeps_the_first_sorted_key() -> None:
    result = deduplicate_by_entry(
        [
            {"key": "B", "entry_time_ms": 5},
            {"key": "A", "entry_time_ms": 5},
        ]
    )
    assert [record["key"] for record in result["unique"]] == ["A"]
    assert result["duplicates"][0]["key"] == "B"


def test_calendar_counts_use_the_entry_utc_month_and_quarter() -> None:
    counts = calendar_counts(
        [
            {"entry_time_ms": 1_609_459_200_000},  # 2021-01-01T00:00:00Z
            {"entry_time_ms": 1_617_235_200_000},  # 2021-04-01T00:00:00Z
        ]
    )
    assert counts["by_year"] == {"2021": 2}
    assert counts["by_quarter"] == {"2021-Q1": 1, "2021-Q2": 1}


def test_percentile_deciles_place_100_in_the_last_bucket() -> None:
    assert pct_decile(0.0) == "0-10"
    assert pct_decile(9.999) == "0-10"
    assert pct_decile(10.0) == "10-20"
    assert pct_decile(100.0) == "90-100"
    assert pct_decile(float("nan")) == "unknown"
    assert decile_counts([{"regime_pct": 63.0}])["60-70"] == 1


def test_cluster_kish_and_largest_share() -> None:
    records = [
        {"regime_slot": 0},
        {"regime_slot": 0},
        {"regime_slot": 1},
        {"regime_slot": 2},
    ]
    result = cluster_analysis(
        records,
        run_id=[0, 1, 2],
        all_run_count=5,
        population_name="synthetic S8",
    )

    assert result["non_empty_clusters"] == 3
    assert result["largest_cluster_count"] == 2
    assert result["largest_cluster_share"] == 0.5
    assert result["n_eff_kish"] == pytest.approx(16.0 / 6.0)
    assert result["design_effect"] == pytest.approx(1.5)


def test_cluster_assignment_never_silently_drops_a_signal() -> None:
    with pytest.raises(AssertionError, match="no regime cluster"):
        cluster_analysis(
            [{"regime_slot": 0}],
            run_id=[-1],
            all_run_count=0,
            population_name="synthetic",
        )


def test_capital_geometry_units_and_numeric_impracticability() -> None:
    result = capital_geometry(
        [
            {"key": "A", "entry_time_ms": 0, "entry_open": 100.0, "D": 4.0},
            {"key": "B", "entry_time_ms": 24 * HOUR_MS, "entry_open": 100.0, "D": 0.5},
        ],
        horizon_hours=72.0,
        population_name="synthetic",
    )

    assert result["notional_usd"]["max"] == 20_000.0
    assert result["notional_pct"]["max"] == 2.0
    assert result["count_notional_pct_above_1_00"] == 1
    assert result["max_concurrent_holding_windows"] == 2
    assert result["cash_policy_skips"]["skipped"] == 1


def test_holding_windows_that_only_touch_do_not_overlap() -> None:
    result = capital_geometry(
        [
            {"key": "A", "entry_time_ms": 0, "entry_open": 100.0, "D": 4.0},
            {"key": "B", "entry_time_ms": 72 * HOUR_MS, "entry_open": 100.0, "D": 4.0},
        ],
        horizon_hours=72.0,
        population_name="synthetic",
    )
    assert result["max_concurrent_holding_windows"] == 1


def test_detectable_effect_and_ratio() -> None:
    assert detectable_effect(0) is None
    assert detectable_effect(25) == pytest.approx(0.560317)
    assert ratio(1, 4) == 0.25
    assert ratio(1, 0) is None
