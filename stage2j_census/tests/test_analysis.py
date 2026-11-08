"""Focused tests for Stage 2J aggregation helpers."""

from __future__ import annotations

from types import SimpleNamespace

from stage2j_census.analysis import _budget_state_counts, _sensitivity_4h_block


def test_budget_state_counts_map_the_three_valued_states() -> None:
    regime = SimpleNamespace(budget_ok=[1, 0, -1])
    records = [
        {"budget_slot": 0},
        {"budget_slot": 0},
        {"budget_slot": 1},
        {"budget_slot": 2},
    ]

    assert _budget_state_counts(records, regime) == {
        "true": 2,
        "false": 1,
        "unknown": 1,
    }


def test_sensitivity_block_is_labelled_and_keeps_the_primary_denominator() -> None:
    result = {
        "pre_gate": [{"cost_R": 0.10}],
        "feasible": [{"cost_R": 0.10, "regime_slot": 0}],
        "non_overlap": {"72h": {"accepted_count": 1}},
        "counts": {"S8": 1},
        "primary_labels": {"cost_gate": 0},
        "secondary_labels": {},
        "diagnostics": {},
        "reconciliation": {"S8_equals_S9_plus_duplicate_entry": True},
    }
    regime = SimpleNamespace(run_id=[0], runs=[{"start": 0, "end": 0}])

    block = _sensitivity_4h_block(
        result,
        regime,
        canonical_key="72h",
        canonical_hours=72,
        cluster_field="regime_slot",
        population_name="S8 cost-feasible (4h exemption sensitivity)",
        exempt_slot_count=1,
        exempt_slot_open_times_utc=["2021-02-11T00:00:00Z"],
    )

    assert block["role"] == "non-decision diagnostic"
    assert block["exempt_slot_count"] == 1
    assert block["canonical_hours"] == 72
    assert block["canonical_non_overlap_count"] == 1
    assert block["M_all"] == 0.10
    assert block["M_feasible"] == 0.10
    assert block["largest_cluster_share"] == 1.0
    assert block["design_effect"] == 1.0
    assert "never changes the primary" in block["note"]
