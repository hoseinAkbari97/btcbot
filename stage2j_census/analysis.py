"""Aggregation and pre-registered verdict synthesis for Stage 2J.

Every statistic is labelled with its population.  No outcome, return, P&L, or
performance statistic is computed.  The verdict procedure is the one declared
in ``docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md`` section 7.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from stage2i_readiness.loader import DEV_END_MS

from .series import Regime4h
from .stats import (
    calendar_counts,
    capital_geometry,
    cluster_analysis,
    cost_bucket_table,
    cost_sensitivity,
    decile_counts,
    detectable_effect,
    distribution,
    median,
    pct_decile,
    stop_distance_table,
)

PROJECT_FLOOR = 150
REFERENCE_INDEPENDENT_N = 349
MAX_MEDIAN_COST_R = 0.20
DESIGN_EFFECT_CEILING = 2.00
LARGEST_CLUSTER_SHARE_CEILING = 0.50
ASSUMED_EFFECT_R = 0.15

B_STAGES = (
    ("S1", "usable 1h bars in the development interval"),
    ("S2", "expansion-testable 1h bars (ATR[t-1] defined)"),
    ("S3", "expansion bars"),
    ("S4", "episode attempts (non-absorbed expansions, including regime failures at e)"),
    ("S5", "regime-qualified episode attempts (permission True at e)"),
    ("S6", "structurally valid episodes (touch plus resumption)"),
    ("S7", "valid confirmation regime and valid entry/stop, pre-gate"),
    ("S8", "cost-feasible signals"),
    ("S9", "deduplicated signals (one per episode)"),
    ("S10", "canonical 72h non-overlapping signals"),
)

D_STAGES = (
    ("S2", "signal-evaluable sessions (b0..b7 usable and contiguous)"),
    ("S3", "directional signals (r2 >= thr)"),
    ("S4", "volatility-budget-qualified sessions"),
    ("S5", "structurally valid sessions (P1 > session VWAP)"),
    ("S6", "valid entry and stop, pre-cost-gate"),
    ("S7", "cost-feasible sessions"),
    ("S8", "deduplicated sessions (one per session)"),
    ("S9", "canonical 24h non-overlapping signals"),
)

B_LABELS = (
    "warmup_atr",
    "warmup_regime",
    "regime_not_permitted",
    "retest_timeout",
    "retest_too_deep",
    "structure_broken",
    "resumption_timeout",
    "segment_break",
    "regime_lost",
    "no_entry_bar",
    "entry_outside_interval",
    "invalid_entry_price",
    "invalid_stop",
    "cost_gate",
    "duplicate_entry",
    "non_overlap",
)

D_LABELS = (
    "measurement_window_incomplete",
    "stop_atr_unavailable",
    "warmup_atr",
    "below_threshold",
    "warmup_budget",
    "budget_out_of_band",
    "below_vwap",
    "no_entry_bar",
    "entry_outside_interval",
    "invalid_entry_price",
    "invalid_stop",
    "cost_gate",
    "duplicate_session",
    "non_overlap",
)


def _share(numerator: int, denominator: int) -> float | None:
    return (numerator / denominator) if denominator else None


def sanitize(value: Any) -> Any:
    """Replace non-finite floats with None and normalise containers for JSON."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [sanitize(item) for item in value]
    return value


def label_table(labels: dict[str, int], frozen: Sequence[str], extras: dict[str, int]) -> dict:
    table = {label: int(labels.get(label, 0)) for label in frozen}
    for label, value in extras.items():
        table[label] = int(labels.get(label, value))
    return dict(sorted(table.items()))


def stage_ladder(
    counts: dict[str, int],
    stages: Sequence[tuple[str, str]],
    exclusion_groups: Sequence[tuple[str, str, Sequence[str], int]],
) -> dict[str, Any]:
    """Build a cumulative stage table and verify each exclusion group.

    ``exclusion_groups`` entries are ``(from_stage, to_stage, labels, excluded)``.
    """
    rows: list[dict[str, Any]] = []
    previous: int | None = None
    for name, description in stages:
        count = int(counts.get(name, 0))
        row: dict[str, Any] = {
            "stage": name,
            "description": description,
            "count": count,
        }
        if previous is not None:
            row["change_from_previous"] = count - previous
            row["share_of_previous"] = _share(count, previous)
        rows.append(row)
        previous = count

    exclusions: list[dict[str, Any]] = []
    all_reconcile = True
    for from_stage, to_stage, labels, excluded in exclusion_groups:
        rows_by_stage = {row["stage"]: row for row in rows}
        observed = rows_by_stage[from_stage]["count"] - rows_by_stage[to_stage]["count"]
        reconciles = observed == excluded
        all_reconcile = all_reconcile and reconciles
        exclusions.append(
            {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "labels": list(labels),
                "expected_excluded": excluded,
                "observed_difference": observed,
                "reconciles": reconciles,
            }
        )
    return {
        "stages": rows,
        "exclusions": exclusions,
        "all_stage_identities_reconcile": all_reconcile,
    }


def grouped_concentration(
    records: Sequence[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
    *,
    population_name: str,
    label: str,
) -> dict[str, Any]:
    """Descriptive concentration over arbitrary non-empty groups."""
    counts = Counter(key(record) for record in records)
    sizes = list(counts.values())
    population = sum(sizes)
    sum_squares = sum(size * size for size in sizes)
    n_eff = (population * population / sum_squares) if sum_squares else None
    largest = max(sizes) if sizes else 0
    return {
        "view": label,
        "population": population_name,
        "population_count": population,
        "group_count": len(sizes),
        "median_group_size": median([float(size) for size in sizes]),
        "max_group_size": largest,
        "largest_group_share": _share(largest, population),
        "n_eff_grouped": n_eff,
        "design_effect_grouped": (population / n_eff) if n_eff else None,
        "group_counts": dict(sorted(counts.items())),
    }


def _regime_state_counts(records: Sequence[dict[str, Any]], field: str) -> dict[str, int]:
    labels = {-1: "unknown", 0: "false", 1: "true"}
    counts = Counter(labels.get(int(record[field]), "unknown") for record in records)
    return {key: counts.get(key, 0) for key in ("true", "false", "unknown")}


def _budget_state_counts(
    records: Sequence[dict[str, Any]], regime: Regime4h
) -> dict[str, int]:
    labels = {-1: "unknown", 0: "false", 1: "true"}
    counts = Counter(
        labels.get(int(regime.budget_ok[record["budget_slot"]]), "unknown")
        for record in records
    )
    return {key: counts.get(key, 0) for key in ("true", "false", "unknown")}


def causality_b(records: Sequence[dict[str, Any]], regime: Regime4h) -> dict[str, Any]:
    violations: list[str] = []
    for record in records:
        slot = int(record["regime_slot"])
        decision = int(record["signal_time_ms"])
        if slot < 0 or slot >= regime.series.n_slots:
            violations.append(f"{record['key']}: regime slot outside the series")
            continue
        if regime.series.close_ms(slot) >= decision:
            violations.append(f"{record['key']}: 4h bar not closed before signal instant")
        if int(record["entry_time_ms"]) <= decision:
            violations.append(f"{record['key']}: entry is not after the signal instant")
        if int(record["entry_time_ms"]) >= DEV_END_MS:
            violations.append(f"{record['key']}: entry outside the development interval")
        if int(record["expansion_time_ms"]) > decision:
            violations.append(f"{record['key']}: expansion is after the signal instant")
    return {
        "candidate": "B",
        "checked": len(records),
        "violations": violations,
        "pass": not violations,
        "checks": [
            "4h decision bar closes strictly before the signal instant",
            "entry time is strictly after the signal instant",
            "entry time is inside the development interval",
            "expansion time is not after the signal instant",
        ],
    }


def causality_d(records: Sequence[dict[str, Any]], regime: Regime4h) -> dict[str, Any]:
    violations: list[str] = []
    for record in records:
        slot = int(record["budget_slot"])
        decision = int(record["signal_time_ms"])
        if slot < 0 or slot >= regime.series.n_slots:
            violations.append(f"{record['key']}: budget slot outside the series")
            continue
        if regime.series.close_ms(slot) >= decision:
            violations.append(f"{record['key']}: 4h budget bar not closed before signal instant")
        if int(record["entry_time_ms"]) <= decision:
            violations.append(f"{record['key']}: entry is not after the signal instant")
        if int(record["entry_time_ms"]) >= DEV_END_MS:
            violations.append(f"{record['key']}: entry outside the development interval")
        if int(record["signal_time_ms"]) >= DEV_END_MS:
            violations.append(f"{record['key']}: signal outside the development interval")
    return {
        "candidate": "D",
        "checked": len(records),
        "violations": violations,
        "pass": not violations,
        "checks": [
            "4h budget bar closes strictly before the signal instant",
            "entry time is strictly after the signal instant",
            "entry and signal times are inside the development interval",
        ],
    }


def _signal_metadata(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "key",
        "entry_time_ms",
        "entry_time_iso",
        "signal_time_ms",
        "signal_time_iso",
        "entry_open",
        "stop",
        "D",
        "stop_fraction",
        "cost_R",
        "regime_slot",
        "budget_slot",
        "regime_pct",
        "cluster_id",
        "session_id",
        "rejection",
    )
    return [
        {field: record.get(field) for field in fields if field in record}
        for record in records
    ]


def _non_overlap_block(result: dict[str, Any], canonical_key: str) -> dict[str, Any]:
    block: dict[str, Any] = {}
    for key, value in sorted(result["non_overlap"].items()):
        block[key] = {
            "role": "canonical" if key == canonical_key else "sensitivity",
            "population": "unique cost-feasible signals",
            "threshold_hours": value["threshold_hours"],
            "population_count": value["population"],
            "accepted_count": value["accepted_count"],
            "rejected_count": value["rejected_count"],
            "spacing_hours": value["spacing_hours"],
            "accepted_keys": value["accepted_keys"],
        }
    return block


def _canonical_records(
    unique: Sequence[dict[str, Any]], canonical: dict[str, Any]
) -> list[dict[str, Any]]:
    accepted = set(canonical["accepted_keys"])
    return [record for record in unique if record["key"] in accepted]


def _sensitivity_4h_block(
    result: dict[str, Any],
    regime: Regime4h,
    *,
    canonical_key: str,
    canonical_hours: int,
    cluster_field: str,
    population_name: str,
    exempt_slot_count: int,
    exempt_slot_open_times_utc: Sequence[str],
) -> dict[str, Any]:
    """Compact non-decision M3 supplied-bar exemption sensitivity."""
    pre_gate = result["pre_gate"]
    feasible = result["feasible"]
    canonical = result["non_overlap"][canonical_key]
    cluster = cluster_analysis(
        feasible,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field=cluster_field,
        population_name=population_name,
    )
    return {
        "role": "non-decision diagnostic",
        "canonical_hours": canonical_hours,
        "exempt_slot_count": exempt_slot_count,
        "exempt_slot_open_times_utc": list(exempt_slot_open_times_utc),
        "counts": {key: int(value) for key, value in sorted(result["counts"].items())},
        "primary_labels": dict(sorted(result["primary_labels"].items())),
        "secondary_labels": dict(sorted(result["secondary_labels"].items())),
        "diagnostics": dict(sorted(result["diagnostics"].items())),
        "M_all": median([record["cost_R"] for record in pre_gate]),
        "M_feasible": median([record["cost_R"] for record in feasible]),
        "canonical_non_overlap_count": canonical["accepted_count"],
        "non_overlap_counts": {
            key: value["accepted_count"]
            for key, value in sorted(result["non_overlap"].items())
        },
        "largest_cluster_share": cluster["largest_cluster_share"],
        "design_effect": cluster["design_effect"],
        "n_eff_kish": cluster["n_eff_kish"],
        "non_empty_clusters": cluster["non_empty_clusters"],
        "all_regime_runs": cluster["all_regime_runs"],
        "reconciliation": dict(sorted(result["reconciliation"].items())),
        "note": (
            "Reruns the candidate with the twelve registered gap-adjacent 4h buckets "
            "marked unusable and the 4h ATR segment-broken at them. It is reported for "
            "transparency only and never changes the primary signal set, denominator, "
            "or verdict."
        ),
    }


def analyse_candidate_b(
    result: dict[str, Any],
    regime: Regime4h,
    *,
    compliance: dict[str, Any],
    sensitivity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts = result["counts"]
    primary = result["primary_labels"]
    feasible = result["feasible"]
    pre_gate = result["pre_gate"]
    unique = result["unique"]

    costs_all = [record["cost_R"] for record in pre_gate]
    costs_feasible = [record["cost_R"] for record in feasible]
    m_all = median(costs_all)
    m_feasible = median(costs_feasible)

    canonical = result["non_overlap"]["72h"]
    canonical_records = _canonical_records(unique, canonical)

    cluster_primary = cluster_analysis(
        feasible,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field="regime_slot",
        population_name="S8 cost-feasible",
    )
    cluster_canonical = cluster_analysis(
        canonical_records,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field="regime_slot",
        population_name="S10 canonical 72h non-overlapping",
    )

    labels = label_table(
        primary,
        B_LABELS,
        {
            "warmup_atr": counts["S1"] - counts["S2"],
            "non_overlap": canonical["rejected_count"],
        },
    )
    ladder = stage_ladder(
        counts,
        B_STAGES,
        (
            ("S1", "S2", ("warmup_atr",), counts["S1"] - counts["S2"]),
            (
                "S4",
                "S5",
                ("warmup_regime", "regime_not_permitted"),
                primary.get("warmup_regime", 0) + primary.get("regime_not_permitted", 0),
            ),
            (
                "S5",
                "S6",
                (
                    "retest_timeout",
                    "retest_too_deep",
                    "structure_broken",
                    "resumption_timeout",
                    "segment_break",
                ),
                sum(
                    primary.get(label, 0)
                    for label in (
                        "retest_timeout",
                        "retest_too_deep",
                        "structure_broken",
                        "resumption_timeout",
                        "segment_break",
                    )
                ),
            ),
            (
                "S6",
                "S7",
                (
                    "regime_lost",
                    "no_entry_bar",
                    "entry_outside_interval",
                    "invalid_entry_price",
                    "invalid_stop",
                ),
                sum(
                    primary.get(label, 0)
                    for label in (
                        "regime_lost",
                        "no_entry_bar",
                        "entry_outside_interval",
                        "invalid_entry_price",
                        "invalid_stop",
                    )
                ),
            ),
            ("S7", "S8", ("cost_gate",), primary.get("cost_gate", 0)),
            ("S8", "S9", ("duplicate_entry",), primary.get("duplicate_entry", 0)),
            (
                "S9",
                "S10",
                ("non_overlap",),
                canonical["rejected_count"],
            ),
        ),
    )

    stage_identities = {
        **result["reconciliation"],
        "stage_ladder_reconciles": ladder["all_stage_identities_reconcile"],
        "S5_equals_S4_minus_regime_labels": (
            counts["S5"]
            == counts["S4"]
            - primary.get("warmup_regime", 0)
            - primary.get("regime_not_permitted", 0)
        ),
        "S6_equals_S5_minus_structural_labels": (
            counts["S6"]
            == counts["S5"]
            - sum(
                primary.get(label, 0)
                for label in (
                    "retest_timeout",
                    "retest_too_deep",
                    "structure_broken",
                    "resumption_timeout",
                    "segment_break",
                )
            )
        ),
        "S7_equals_S6_minus_entry_and_regime_labels": (
            counts["S7"]
            == counts["S6"]
            - sum(
                primary.get(label, 0)
                for label in (
                    "regime_lost",
                    "no_entry_bar",
                    "entry_outside_interval",
                    "invalid_entry_price",
                    "invalid_stop",
                )
            )
        ),
        "S8_equals_S7_minus_cost_gate": (
            counts["S8"] == counts["S7"] - primary.get("cost_gate", 0)
        ),
        "S10_equals_S9_minus_non_overlap": (
            counts["S10"] == counts["S9"] - canonical["rejected_count"]
        ),
    }

    feasible_share = _share(counts["S8"], counts["S7"])
    causality = causality_b(pre_gate, regime)
    local_compliance = {
        **compliance,
        "causality_pass": causality["pass"],
        "stage_identities_reconcile": all(stage_identities.values()),
    }
    verdict = decide_verdict(
        candidate="B",
        compliance=local_compliance,
        pre_gate_count=counts["S7"],
        m_all=m_all,
        non_overlap_count=counts["S10"],
        capital_violation=any(
            record["D"] / record["entry_open"] < 0.01 for record in feasible
        ),
        cluster=cluster_primary,
        canonical_hours=72,
    )

    return {
        "candidate": "B",
        "frozen_spec_version": "2.0.0",
        "population_labels": {
            "S4": "episode attempts, raw-candidate denominator",
            "S7": "valid confirmation regime and valid entry/stop, pre-gate; M_all population",
            "S8": "cost-feasible; M_feasible population and primary cluster population",
            "S10": "canonical 72h non-overlapping; opportunity count",
        },
        "counts": {f"S{index}": counts.get(f"S{index}", 0) for index in range(1, 11)},
        "labels": labels,
        "secondary_labels": dict(sorted(result["secondary_labels"].items())),
        "diagnostics": dict(sorted(result["diagnostics"].items())),
        "denominators": {
            "expansion_test_share": _share(counts["S3"], counts["S2"]),
            "permission_share": _share(counts["S5"], counts["S4"]),
            "retest_conversion": _share(counts["S6"], counts["S5"]),
            "signal_validity_share": _share(counts["S7"], counts["S6"]),
            "feasible_share": feasible_share,
            "unique_share": _share(counts["S9"], counts["S8"]),
            "nonoverlap_share": _share(counts["S10"], counts["S9"]),
        },
        "stage_ladder": ladder,
        "identities": stage_identities,
        "cost": {
            "primary_bp": 26,
            "gate": 0.20,
            "M_all": m_all,
            "M_all_population": "S7 pre-gate valid entry/stop",
            "M_feasible": m_feasible,
            "M_feasible_population": "S8 cost-feasible",
            "design_margin_0_15_minus_M_all": (ASSUMED_EFFECT_R - m_all)
            if m_all is not None
            else None,
            "distribution_S7": distribution(costs_all),
            "distribution_S8": distribution(costs_feasible),
            "buckets_S7": cost_bucket_table(costs_all),
            "buckets_S8": cost_bucket_table(costs_feasible),
            "sensitivity_pre_gate_S7": cost_sensitivity(pre_gate),
        },
        "stop_distance": {
            "S7": stop_distance_table(pre_gate),
            "S8": stop_distance_table(feasible),
        },
        "non_overlap": _non_overlap_block(result, "72h"),
        "cluster_primary_S8": cluster_primary,
        "cluster_canonical_S10": cluster_canonical,
        "cluster_extra_views_S8": [
            grouped_concentration(
                feasible,
                lambda record: pct_decile(record["regime_pct"]),
                population_name="S8 cost-feasible",
                label="permission percentile decile",
            ),
            grouped_concentration(
                feasible,
                lambda record: str(record["entry_time_iso"])[:7],
                population_name="S8 cost-feasible",
                label="calendar month of entry time",
            ),
            grouped_concentration(
                feasible,
                lambda record: _quarter(record["entry_time_iso"]),
                population_name="S8 cost-feasible",
                label="calendar quarter of entry time",
            ),
        ],
        "regime_counts": {
            "S7": {
                "permission_e": _regime_state_counts(pre_gate, "permission_e"),
                "permission_c": _regime_state_counts(pre_gate, "permission_c"),
                "pct_decile": decile_counts(pre_gate),
            },
            "S8": {
                "permission_e": _regime_state_counts(feasible, "permission_e"),
                "permission_c": _regime_state_counts(feasible, "permission_c"),
                "pct_decile": decile_counts(feasible),
            },
        },
        "calendar": {
            "S8": _calendar(feasible),
            "S10": _calendar(canonical_records),
        },
        "capital_geometry": {
            "verdict_population": capital_geometry(
                feasible,
                horizon_hours=72.0,
                population_name="S8 cost-feasible",
            ),
            "pre_gate_diagnostic": capital_geometry(
                pre_gate,
                horizon_hours=72.0,
                population_name="S7 pre-gate",
            ),
        },
        "detectable_effect_R": detectable_effect(counts["S10"]),
        "causality": causality,
        "verdict": verdict,
        "sensitivity_4h_exemption": (
            _sensitivity_4h_block(
                sensitivity["result"],
                sensitivity["regime"],
                canonical_key="72h",
                canonical_hours=72,
                cluster_field="regime_slot",
                population_name="S8 cost-feasible (4h exemption sensitivity)",
                exempt_slot_count=sensitivity["exempt_slot_count"],
                exempt_slot_open_times_utc=sensitivity["exempt_slot_open_times_utc"],
            )
            if sensitivity is not None
            else None
        ),
        "signal_metadata": {
            "S7_pre_gate": _signal_metadata(pre_gate),
            "S8_feasible": _signal_metadata(feasible),
            "S10_canonical": _signal_metadata(canonical_records),
        },
    }


def analyse_candidate_d(
    result: dict[str, Any],
    regime: Regime4h,
    *,
    compliance: dict[str, Any],
    sensitivity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts = result["counts"]
    primary = result["primary_labels"]
    feasible = result["feasible"]
    pre_gate = result["pre_gate"]
    unique = result["unique"]

    costs_all = [record["cost_R"] for record in pre_gate]
    costs_feasible = [record["cost_R"] for record in feasible]
    m_all = median(costs_all)
    m_feasible = median(costs_feasible)

    canonical = result["non_overlap"]["24h"]
    canonical_records = _canonical_records(unique, canonical)

    cluster_primary = cluster_analysis(
        feasible,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field="budget_slot",
        population_name="S7 cost-feasible",
    )
    cluster_s6 = cluster_analysis(
        pre_gate,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field="budget_slot",
        population_name="S6 pre-gate valid entry/stop",
    )
    cluster_s9 = cluster_analysis(
        canonical_records,
        run_id=regime.run_id,
        all_run_count=len(regime.runs),
        field="budget_slot",
        population_name="S9 canonical 24h non-overlapping",
    )

    labels = label_table(
        primary,
        D_LABELS,
        {"non_overlap": canonical["rejected_count"]},
    )
    ladder = stage_ladder(
        counts,
        D_STAGES,
        (
            (
                "S2",
                "S3",
                ("stop_atr_unavailable", "warmup_atr", "below_threshold"),
                primary.get("stop_atr_unavailable", 0)
                + primary.get("warmup_atr", 0)
                + primary.get("below_threshold", 0),
            ),
            (
                "S3",
                "S4",
                ("warmup_budget", "budget_out_of_band"),
                primary.get("warmup_budget", 0) + primary.get("budget_out_of_band", 0),
            ),
            ("S4", "S5", ("below_vwap",), primary.get("below_vwap", 0)),
            (
                "S5",
                "S6",
                (
                    "no_entry_bar",
                    "entry_outside_interval",
                    "invalid_entry_price",
                    "invalid_stop",
                ),
                sum(
                    primary.get(label, 0)
                    for label in (
                        "no_entry_bar",
                        "entry_outside_interval",
                        "invalid_entry_price",
                        "invalid_stop",
                    )
                ),
            ),
            ("S6", "S7", ("cost_gate",), primary.get("cost_gate", 0)),
            ("S7", "S8", ("duplicate_session",), primary.get("duplicate_session", 0)),
            ("S8", "S9", ("non_overlap",), canonical["rejected_count"]),
        ),
    )

    identities = {
        **result["reconciliation"],
        "stage_ladder_reconciles": ladder["all_stage_identities_reconcile"],
        "S0_equals_S2_plus_measurement_incomplete": (
            counts["S0"]
            == counts["S2"] + primary.get("measurement_window_incomplete", 0)
        ),
        "S2_equals_S3_plus_threshold_and_atr_labels": (
            counts["S2"]
            == counts["S3"]
            + primary.get("stop_atr_unavailable", 0)
            + primary.get("warmup_atr", 0)
            + primary.get("below_threshold", 0)
        ),
        "S3_equals_S4_plus_budget_labels": (
            counts["S3"]
            == counts["S4"]
            + primary.get("warmup_budget", 0)
            + primary.get("budget_out_of_band", 0)
        ),
        "S4_equals_S5_plus_vwap": (
            counts["S4"] == counts["S5"] + primary.get("below_vwap", 0)
        ),
        "S5_equals_S6_plus_entry_labels": (
            counts["S5"]
            == counts["S6"]
            + sum(
                primary.get(label, 0)
                for label in (
                    "no_entry_bar",
                    "entry_outside_interval",
                    "invalid_entry_price",
                    "invalid_stop",
                )
            )
        ),
        "S6_equals_S7_plus_cost_gate": (
            counts["S6"] == counts["S7"] + primary.get("cost_gate", 0)
        ),
        "S7_equals_S8_plus_duplicate_session": (
            counts["S7"] == counts["S8"] + primary.get("duplicate_session", 0)
        ),
        "S9_equals_S8_minus_non_overlap": (
            counts["S9"] == counts["S8"] - canonical["rejected_count"]
        ),
    }

    causality = causality_d(pre_gate, regime)
    local_compliance = {
        **compliance,
        "causality_pass": causality["pass"],
        "stage_identities_reconcile": all(identities.values()),
    }
    verdict = decide_verdict(
        candidate="D",
        compliance=local_compliance,
        pre_gate_count=counts["S6"],
        m_all=m_all,
        non_overlap_count=counts["S9"],
        capital_violation=any(
            record["D"] / record["entry_open"] < 0.01 for record in feasible
        ),
        cluster=cluster_primary,
        canonical_hours=24,
    )

    return {
        "candidate": "D",
        "frozen_spec_version": "2.0.0",
        "population_labels": {
            "S0": "session buckets whose signal instant is in the development interval",
            "S6": "valid entry/stop, pre-gate; M_all population and required cluster view",
            "S7": "cost-feasible; M_feasible population and K3 primary cluster population",
            "S9": "canonical 24h non-overlapping; opportunity count and required cluster view",
        },
        "counts": {f"S{index}": counts.get(f"S{index}", 0) for index in range(10)},
        "labels": labels,
        "secondary_labels": dict(sorted(result["secondary_labels"].items())),
        "diagnostics": dict(sorted(result["diagnostics"].items())),
        "denominators": {
            "session_completeness": _share(counts["S2"], counts["S0"]),
            "threshold_pass_share": _share(counts["S3"], counts["S2"]),
            "budget_pass_share": _share(counts["S4"], counts["S3"]),
            "vwap_pass_share": _share(counts["S5"], counts["S4"]),
            "entry_validity_share": _share(counts["S6"], counts["S5"]),
            "feasible_share": _share(counts["S7"], counts["S6"]),
            "unique_share": _share(counts["S8"], counts["S7"]),
            "nonoverlap_share": _share(counts["S9"], counts["S8"]),
        },
        "stage_ladder": ladder,
        "identities": identities,
        "session_accounting": {
            "S0": counts["S0"],
            "per_session": result["per_session"],
            "session_full_data": result["session_full_data"],
            "us_only": result["us_only"],
        },
        "cost": {
            "primary_bp": 26,
            "gate": 0.20,
            "M_all": m_all,
            "M_all_population": "S6 pre-gate valid entry/stop",
            "M_feasible": m_feasible,
            "M_feasible_population": "S7 cost-feasible",
            "design_margin_0_15_minus_M_all": (ASSUMED_EFFECT_R - m_all)
            if m_all is not None
            else None,
            "distribution_S6": distribution(costs_all),
            "distribution_S7": distribution(costs_feasible),
            "buckets_S6": cost_bucket_table(costs_all),
            "buckets_S7": cost_bucket_table(costs_feasible),
            "sensitivity_pre_gate_S6": cost_sensitivity(pre_gate),
        },
        "stop_distance": {
            "S6": stop_distance_table(pre_gate),
            "S7": stop_distance_table(feasible),
        },
        "non_overlap": _non_overlap_block(result, "24h"),
        "cluster_primary_S7": cluster_primary,
        "cluster_required_view_S6": cluster_s6,
        "cluster_required_view_S9": cluster_s9,
        "cluster_extra_views_S7": [
            grouped_concentration(
                feasible,
                lambda record: str(record["session_id"]),
                population_name="S7 cost-feasible",
                label="session id",
            ),
            grouped_concentration(
                feasible,
                lambda record: str(record["entry_time_iso"])[:7],
                population_name="S7 cost-feasible",
                label="calendar month of entry time",
            ),
            grouped_concentration(
                feasible,
                lambda record: _quarter(record["entry_time_iso"]),
                population_name="S7 cost-feasible",
                label="calendar quarter of entry time",
            ),
        ],
        "regime_counts": {
            "S6": {
                "budget_state": _budget_state_counts(pre_gate, regime),
                "budget_pct_decile": decile_counts(pre_gate),
                "session_id": dict(
                    sorted(Counter(str(record["session_id"]) for record in pre_gate).items())
                ),
            },
            "S7": {
                "budget_state": _budget_state_counts(feasible, regime),
                "budget_pct_decile": decile_counts(feasible),
                "session_id": dict(
                    sorted(Counter(str(record["session_id"]) for record in feasible).items())
                ),
            },
        },
        "calendar": {
            "S7": _calendar(feasible),
            "S9": _calendar(canonical_records),
        },
        "capital_geometry": {
            "verdict_population": capital_geometry(
                feasible,
                horizon_hours=6.0,
                population_name="S7 cost-feasible",
                alternative_horizon_hours=8.0,
                alternative_label="session bound",
            ),
            "pre_gate_diagnostic": capital_geometry(
                pre_gate,
                horizon_hours=6.0,
                population_name="S6 pre-gate",
                alternative_horizon_hours=8.0,
                alternative_label="session bound",
            ),
        },
        "detectable_effect_R": detectable_effect(counts["S9"]),
        "causality": causality,
        "verdict": verdict,
        "sensitivity_4h_exemption": (
            _sensitivity_4h_block(
                sensitivity["result"],
                sensitivity["regime"],
                canonical_key="24h",
                canonical_hours=24,
                cluster_field="budget_slot",
                population_name="S7 cost-feasible (4h exemption sensitivity)",
                exempt_slot_count=sensitivity["exempt_slot_count"],
                exempt_slot_open_times_utc=sensitivity["exempt_slot_open_times_utc"],
            )
            if sensitivity is not None
            else None
        ),
        "signal_metadata": {
            "S6_pre_gate": _signal_metadata(pre_gate),
            "S7_feasible": _signal_metadata(feasible),
            "S9_canonical": _signal_metadata(canonical_records),
        },
    }


def _calendar(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return calendar_counts(records)


def _quarter(iso: str) -> str:
    year, month = iso[:7].split("-")
    return f"{year}-Q{((int(month) - 1) // 3) + 1}"


def decide_verdict(
    *,
    candidate: str,
    compliance: dict[str, Any],
    pre_gate_count: int,
    m_all: float | None,
    non_overlap_count: int,
    capital_violation: bool,
    cluster: dict[str, Any],
    canonical_hours: int,
) -> dict[str, Any]:
    """Apply the pre-registered section 7 procedure in order."""
    compliance_checks = dict(compliance)
    compliance_checks["non_empty_pre_gate_population"] = pre_gate_count > 0
    compliance_checks["M_all_defined"] = m_all is not None
    compliance_passed = all(bool(value) for value in compliance_checks.values())

    insufficient: list[str] = []
    if non_overlap_count < PROJECT_FLOOR:
        insufficient.append(
            f"N_nonoverlap {non_overlap_count} < project floor {PROJECT_FLOOR}"
        )
    if m_all is not None and m_all > MAX_MEDIAN_COST_R:
        insufficient.append(f"M_all {m_all} > {MAX_MEDIAN_COST_R}")
    if capital_violation:
        insufficient.append("a cost-feasible signal has notional_pct > 1.00")

    largest_share = cluster.get("largest_cluster_share")
    design_effect = cluster.get("design_effect")
    concentration_failed = bool(
        (largest_share is not None and largest_share > LARGEST_CLUSTER_SHARE_CEILING)
        or (design_effect is not None and design_effect >= DESIGN_EFFECT_CEILING)
    )

    if not compliance_passed:
        verdict = "INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION"
    elif insufficient:
        verdict = "FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES"
    elif concentration_failed:
        verdict = "FEASIBILITY FAIL — EXCESSIVE CONCENTRATION"
    else:
        verdict = "FEASIBILITY PASS"

    if non_overlap_count >= REFERENCE_INDEPENDENT_N and (
        m_all is not None and m_all <= MAX_MEDIAN_COST_R
    ):
        tier = "PASS"
    elif PROJECT_FLOOR <= non_overlap_count < REFERENCE_INDEPENDENT_N and (
        m_all is not None and m_all <= MAX_MEDIAN_COST_R
    ):
        tier = "PASS WITH LIMITATIONS"
    else:
        tier = "FAIL"

    return {
        "candidate": candidate,
        "verdict": verdict,
        "compliance_passed": compliance_passed,
        "compliance_checks": compliance_checks,
        "insufficient_opportunities": {
            "failed": bool(insufficient),
            "subconditions": insufficient,
        },
        "concentration": {
            "criterion_met": concentration_failed,
            "population": cluster.get("population"),
            "largest_cluster_share": largest_share,
            "largest_cluster_share_ceiling": LARGEST_CLUSTER_SHARE_CEILING,
            "design_effect": design_effect,
            "design_effect_ceiling": DESIGN_EFFECT_CEILING,
            "note": (
                "Pre-declared descriptive screening criterion, not a statistical test "
                "and not a dependence estimate."
            ),
        },
        "inputs": {
            "canonical_non_overlap_hours": canonical_hours,
            "N_nonoverlap": non_overlap_count,
            "project_floor": PROJECT_FLOOR,
            "reference_independent_n": REFERENCE_INDEPENDENT_N,
            "M_all": m_all,
            "M_all_population": (
                "B S7 pre-gate" if candidate == "B" else "D S6 pre-gate"
            ),
            "max_median_cost_R": MAX_MEDIAN_COST_R,
            "capital_violation": capital_violation,
        },
        "frozen_tier_label": tier,
        "frozen_tier_meaning": (
            "Tier label from the frozen candidate specification, reported separately. "
            "Neither tier nor PASS is evidence of profitability."
        ),
        "precedence": (
            "INCONCLUSIVE, then INSUFFICIENT OPPORTUNITIES, then EXCESSIVE "
            "CONCENTRATION, then FEASIBILITY PASS"
        ),
    }


def summarise_verdict_inputs(
    candidate_report: dict[str, Any],
) -> dict[str, Any]:
    verdict = candidate_report["verdict"]
    return {
        "candidate": candidate_report["candidate"],
        "verdict": verdict["verdict"],
        "tier_label": verdict["frozen_tier_label"],
        "N_nonoverlap": verdict["inputs"]["N_nonoverlap"],
        "M_all": verdict["inputs"]["M_all"],
        "M_feasible": candidate_report["cost"]["M_feasible"],
        "feasible_share": candidate_report["denominators"]["feasible_share"],
        "largest_cluster_share": verdict["concentration"]["largest_cluster_share"],
        "design_effect": verdict["concentration"]["design_effect"],
        "capital_violation": verdict["inputs"]["capital_violation"],
        "insufficient_subconditions": verdict["insufficient_opportunities"][
            "subconditions"
        ],
        "compliance_passed": verdict["compliance_passed"],
    }


def alignment_compliance(alignment: dict[str, Any]) -> dict[str, Any]:
    summary = alignment["summary"]
    return {
        "alignment_price_tolerance": bool(summary["price_tolerance_checks_pass"]),
        "alignment_no_price_mismatch": not bool(summary["any_price_mismatch"]),
        "alignment_registered_gaps_match": bool(
            summary["registered_gap_locations_match"]
        ),
        "alignment_missing_totals_match": bool(
            summary["missing_bar_totals_match_freeze"]
        ),
        "alignment_grid_checks": bool(summary["grid_checks_pass"]),
        "alignment_4h_boundary_hours": bool(summary["four_hour_boundary_hours_ok"]),
        "alignment_fail_flag_clear": not bool(summary["alignment_fail"]),
    }


def iter_identity_flags(identities: dict[str, Any]) -> Iterable[tuple[str, bool]]:
    for key, value in identities.items():
        if isinstance(value, bool):
            yield key, value
