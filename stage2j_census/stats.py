"""Descriptive statistics and accounting helpers for the Stage 2J census.

Every helper in this module is descriptive.  It computes no return, P&L,
expectancy, drawdown, or performance statistic.  Populations are always passed
in explicitly so that the pre-gate and post-gate views can never be mixed.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

HOUR_MS = 3_600_000
COST_BP_PRIMARY = 26
COST_FRACTION_PRIMARY = 0.0026
COST_GATE = 0.20
EQUITY_USD = 10_000.0
RISK_USD = 100.0


def median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    middle = n // 2
    if n % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def quantile(values: Sequence[float], probability: float) -> float | None:
    """Type-7 linear-interpolation quantile (the common spreadsheet form)."""
    if not values:
        return None
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    ordered = sorted(values)
    n = len(ordered)
    if n == 1:
        return ordered[0]
    position = (n - 1) * probability
    lower = int(math.floor(position))
    fraction = position - lower
    if lower + 1 >= n:
        return ordered[-1]
    return ordered[lower] + fraction * (ordered[lower + 1] - ordered[lower])


def distribution(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "median": None,
            "mean": None,
            "p25": None,
            "p75": None,
            "p90": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(values),
        "median": median(values),
        "mean": math.fsum(values) / len(values),
        "p25": quantile(values, 0.25),
        "p75": quantile(values, 0.75),
        "p90": quantile(values, 0.90),
        "min": min(values),
        "max": max(values),
    }


COST_BUCKETS = (
    ("<= 0.10", None, 0.10),
    ("(0.10, 0.20]", 0.10, 0.20),
    ("(0.20, 0.30]", 0.20, 0.30),
    ("(0.30, 0.50]", 0.30, 0.50),
    ("> 0.50", 0.50, None),
)


def cost_bucket(value: float) -> str:
    for label, lower, upper in COST_BUCKETS:
        if lower is not None and value <= lower:
            continue
        if upper is None or value <= upper:
            return label
    return "> 0.50"  # pragma: no cover - the final bucket is exhaustive


def cost_bucket_table(values: Sequence[float]) -> list[dict[str, Any]]:
    total = len(values)
    counts = Counter(cost_bucket(value) for value in values)
    return [
        {
            "bucket": label,
            "count": counts.get(label, 0),
            "share": (counts.get(label, 0) / total) if total else None,
        }
        for label, _, _ in COST_BUCKETS
    ]


def cost_sensitivity(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Recompute the unchanged gate at 10, 26, 39, and 52 bp.

    ``records`` must be the **pre-gate** valid-entry/stop population.  The
    pre-gate median is taken on the same population at every cost level, as the
    frozen protocol requires.
    """
    result: dict[str, Any] = {}
    population = len(records)
    for bp in (10, COST_BP_PRIMARY, 39, 52):
        fraction = bp / 10_000.0
        costs = [fraction * record["entry_open"] / record["D"] for record in records]
        passing = [cost for cost in costs if cost <= COST_GATE]
        m_all = median(costs)
        result[f"{bp}bp"] = {
            "bp": bp,
            "population": population,
            "passing": len(passing),
            "feasible_share": (len(passing) / population) if population else None,
            "M_all": m_all,
            "design_margin_0_15_minus_M_all": (0.15 - m_all) if m_all is not None else None,
            "M_feasible": median(passing),
            "post_gate_population": len(passing),
        }
    return result


def stop_distance_table(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    distances = [record["D"] for record in records]
    fractions = [record["D"] / record["entry_open"] for record in records]
    below = sum(1 for fraction in fractions if fraction < 0.013)
    return {
        "population": len(records),
        "D_usdt": distribution(distances),
        "stop_fraction": distribution(fractions),
        "stop_percent": distribution([100.0 * value for value in fractions]),
        "share_below_1_30_percent": (below / len(records)) if records else None,
        "count_below_1_30_percent": below,
    }


def non_overlap(
    records: Sequence[dict[str, Any]],
    hours: float,
    *,
    key_name: str = "key",
    entry_name: str = "entry_time_ms",
) -> dict[str, Any]:
    """Greedy interval selection on entry time, inclusive boundary."""
    threshold_ms = int(round(hours * HOUR_MS))
    ordered = sorted(records, key=lambda record: (record[entry_name], record[key_name]))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    last_entry: int | None = None
    for record in ordered:
        if last_entry is None or record[entry_name] - last_entry >= threshold_ms:
            accepted.append(record)
            last_entry = record[entry_name]
        else:
            rejected.append(
                {
                    "key": record[key_name],
                    "entry_time_ms": record[entry_name],
                    "hours_since_last_accepted": (record[entry_name] - last_entry) / HOUR_MS,
                }
            )
    spacings = [
        (accepted[index][entry_name] - accepted[index - 1][entry_name]) / HOUR_MS
        for index in range(1, len(accepted))
    ]
    return {
        "threshold_hours": hours,
        "population": len(records),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted_keys": [record[key_name] for record in accepted],
        "rejected": rejected,
        "spacing_hours": distribution(spacings),
    }


def deduplicate_by_entry(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(records, key=lambda record: (record["entry_time_ms"], record["key"]))
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for record in ordered:
        if record["entry_time_ms"] in seen:
            duplicates.append({"key": record["key"], "entry_time_ms": record["entry_time_ms"]})
            continue
        seen.add(record["entry_time_ms"])
        unique.append(record)
    return {"unique": unique, "duplicates": duplicates}


def deduplicate_by_key(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(records, key=lambda record: (record["entry_time_ms"], record["key"]))
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for record in ordered:
        if record["key"] in seen:
            duplicates.append({"key": record["key"], "entry_time_ms": record["entry_time_ms"]})
            continue
        seen.add(record["key"])
        unique.append(record)
    return {"unique": unique, "duplicates": duplicates}


def _utc(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC)


def calendar_counts(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    years: Counter[str] = Counter()
    months: Counter[str] = Counter()
    quarters: Counter[str] = Counter()
    for record in records:
        moment = _utc(record["entry_time_ms"])
        years[f"{moment.year:04d}"] += 1
        months[f"{moment.year:04d}-{moment.month:02d}"] += 1
        quarters[f"{moment.year:04d}-Q{((moment.month - 1) // 3) + 1}"] += 1
    return {
        "population": len(records),
        "by_year": dict(sorted(years.items())),
        "by_month": dict(sorted(months.items())),
        "by_quarter": dict(sorted(quarters.items())),
    }


def pct_decile(pct: float) -> str:
    if math.isnan(pct):
        return "unknown"
    if pct >= 100.0:
        return "90-100"
    index = int(math.floor(pct / 10.0))
    if index < 0:
        return "unknown"
    return f"{index * 10}-{(index + 1) * 10}"


def decile_counts(records: Sequence[dict[str, Any]], field: str = "regime_pct") -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        counts[pct_decile(record[field])] += 1
    order = [
        "0-10",
        "10-20",
        "20-30",
        "30-40",
        "40-50",
        "50-60",
        "60-70",
        "70-80",
        "80-90",
        "90-100",
        "unknown",
    ]
    return {
        label: counts.get(label, 0)
        for label in order
        if counts.get(label, 0) or label != "unknown"
    }


def cluster_analysis(
    records: Sequence[dict[str, Any]],
    *,
    run_id: Sequence[int],
    all_run_count: int,
    field: str = "regime_slot",
    population_name: str,
) -> dict[str, Any]:
    """Kish concentration over non-empty maximal regime runs.

    The cluster unit is the candidate's regime series, not the signal set.
    Every signal must map to a ``True`` run; that is asserted by the caller.
    """
    counts: Counter[int] = Counter()
    unassigned = 0
    for record in records:
        slot = record[field]
        cluster = run_id[slot] if 0 <= slot < len(run_id) else -1
        if cluster < 0:
            unassigned += 1
            continue
        counts[cluster] += 1
    if unassigned:
        raise AssertionError(f"{population_name}: {unassigned} signals have no regime cluster")
    sizes = list(counts.values())
    population = sum(sizes)
    largest = max(sizes) if sizes else 0
    sum_squares = sum(size * size for size in sizes)
    n_eff = (population * population / sum_squares) if sum_squares else None
    design_effect = (population / n_eff) if n_eff else None
    k_nonempty = len(sizes)
    mean_size = (population / k_nonempty) if k_nonempty else None
    rho_sensitivity: dict[str, float | None] = {}
    if mean_size is not None:
        for rho in (0.25, 0.50, 0.75, 1.00):
            rho_sensitivity[f"{rho:.2f}"] = population / (1.0 + (mean_size - 1.0) * rho)
    return {
        "population": population_name,
        "population_count": population,
        "all_regime_runs": all_run_count,
        "non_empty_clusters": k_nonempty,
        "cluster_size_distribution": distribution([float(size) for size in sizes]),
        "largest_cluster_count": largest,
        "largest_cluster_share": (largest / population) if population else None,
        "sum_cluster_size_squares": sum_squares,
        "n_eff_kish": n_eff,
        "design_effect": design_effect,
        "mean_non_empty_cluster_size": mean_size,
        "n_eff_rho_sensitivity": rho_sensitivity,
        "note": (
            "Kish is a concentration diagnostic, not an estimate of serial dependence "
            "and not the definitive effective sample size of returns. The rho series is "
            "the frozen formula using the arithmetic mean non-empty cluster size; the "
            "exact Kish value uses the size-weighted mean and is reported separately."
        ),
    }


def _overlap_peak(
    records: Sequence[dict[str, Any]], horizon_ms: int
) -> dict[str, Any]:
    """Largest number (and notionals) of half-open holding windows at one instant."""
    events: list[tuple[int, int, float]] = []
    for record in records:
        start = record["entry_time_ms"]
        events.append((start, 1, record["notional_usd"]))
        events.append((start + horizon_ms, -1, record["notional_usd"]))
    events.sort(key=lambda item: (item[0], item[1]))
    active: list[float] = []
    peak_count = 0
    peak_sum = 0.0
    index = 0
    while index < len(events):
        moment = events[index][0]
        # End events first: a window ending exactly when another starts does not overlap.
        while index < len(events) and events[index][0] == moment and events[index][1] == -1:
            active.remove(events[index][2])
            index += 1
        while index < len(events) and events[index][0] == moment and events[index][1] == 1:
            active.append(events[index][2])
            index += 1
        current_sum = math.fsum(active)
        if len(active) > peak_count:
            peak_count = len(active)
            peak_sum = current_sum
        elif len(active) == peak_count and current_sum > peak_sum:
            peak_sum = current_sum
    return {"max_concurrent": peak_count, "implied_capital_usd": peak_sum}


def cash_policy_skips(
    records: Sequence[dict[str, Any]], horizon_ms: int
) -> dict[str, Any]:
    ordered = sorted(records, key=lambda record: (record["entry_time_ms"], record["key"]))
    accepted = 0
    skipped = 0
    last_entry: int | None = None
    for record in ordered:
        if last_entry is None or record["entry_time_ms"] - last_entry >= horizon_ms:
            accepted += 1
            last_entry = record["entry_time_ms"]
        else:
            skipped += 1
    return {"population": len(records), "accepted": accepted, "skipped": skipped}


def capital_geometry(
    records: Sequence[dict[str, Any]],
    *,
    horizon_hours: float,
    population_name: str,
    equity_usd: float = EQUITY_USD,
    risk_usd: float = RISK_USD,
    alternative_horizon_hours: float | None = None,
    alternative_label: str | None = None,
) -> dict[str, Any]:
    enriched: list[dict[str, Any]] = []
    for record in records:
        stop_fraction = record["D"] / record["entry_open"]
        notional_usd = risk_usd / stop_fraction
        enriched.append(
            {
                **record,
                "stop_fraction": stop_fraction,
                "notional_usd": notional_usd,
                "notional_pct": notional_usd / equity_usd,
                "quantity_btc": notional_usd / record["entry_open"],
            }
        )
    notional = [record["notional_usd"] for record in enriched]
    notional_pct = [record["notional_pct"] for record in enriched]
    above = sum(1 for value in notional_pct if value > 1.0)
    horizon_ms = int(round(horizon_hours * HOUR_MS))
    peak = _overlap_peak(enriched, horizon_ms)
    skips = cash_policy_skips(enriched, horizon_ms)
    quantities = [record["quantity_btc"] for record in enriched]
    minimum_notional_binding = sum(1 for value in notional if value < 5.0)
    lot_step_binding = sum(1 for value in quantities if value < 1e-5)
    result: dict[str, Any] = {
        "population": population_name,
        "population_count": len(records),
        "equity_usd": equity_usd,
        "risk_usd": risk_usd,
        "holding_horizon_hours": horizon_hours,
        "notional_usd": distribution(notional),
        "notional_pct": distribution(notional_pct),
        "count_notional_pct_above_1_00": above,
        "share_notional_pct_above_1_00": (above / len(records)) if records else None,
        "max_concurrent_holding_windows": peak["max_concurrent"],
        "implied_capital_at_peak_usd": peak["implied_capital_usd"],
        "implied_capital_at_peak_pct_equity": peak["implied_capital_usd"] / equity_usd,
        "cash_policy_skips": skips,
        "minimum_5_usd_notional_binding_count": minimum_notional_binding,
        "lot_step_1e_5_btc_binding_count": lot_step_binding,
        "lot_step_note": (
            "A quantity below 1e-5 BTC would be unfundable at the stated lot step. "
            "No order rounding, venue rule, or fill is simulated."
        ),
    }
    if alternative_horizon_hours is not None:
        alternative_ms = int(round(alternative_horizon_hours * HOUR_MS))
        alternative_peak = _overlap_peak(enriched, alternative_ms)
        result["alternative_horizon"] = {
            "label": alternative_label or f"{alternative_horizon_hours}h",
            "holding_horizon_hours": alternative_horizon_hours,
            "max_concurrent_holding_windows": alternative_peak["max_concurrent"],
            "implied_capital_at_peak_usd": alternative_peak["implied_capital_usd"],
            "cash_policy_skips": cash_policy_skips(enriched, alternative_ms),
        }
    return result


def detectable_effect(non_overlap_count: int) -> float | None:
    if non_overlap_count <= 0:
        return None
    return 2.801585 / math.sqrt(non_overlap_count)


def session_full_data_flags(
    series: Any, session_start_index: int, session_bars: int = 32
) -> bool:
    """All 32 session bars usable and exactly one 15m slot apart."""
    for offset in range(session_bars):
        index = session_start_index + offset
        if index >= series.n_slots or not series.usable[index]:
            return False
    return True


def ratio(numerator: int, denominator: int) -> float | None:
    return (numerator / denominator) if denominator else None


def summarise_records(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact, deterministic signal metadata (no outcome field)."""
    fields = (
        "key",
        "entry_time_ms",
        "entry_time_iso",
        "signal_time_ms",
        "entry_open",
        "stop",
        "D",
        "stop_fraction",
        "cost_R",
        "regime_slot",
        "regime_pct",
        "cluster_id",
    )
    return [{field: record.get(field) for field in fields} for record in records]
