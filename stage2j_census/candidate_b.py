"""Candidate B feasibility census (frozen specification version 2.0.0).

The module evaluates only the boolean rules in ``CANDIDATE_B_SPEC.md``.  It
never observes an outcome, computes no return or P&L, and writes no trade list.
Every populated stage is a count of opportunities under the frozen rules.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from stage2i_readiness.loader import DEV_END_MS

from .series import CandleSeries, Regime4h, slot_open_ms

B_HOLD_HOURS = 72.0
B_SENSITIVITY_HOURS = (24.0, 120.0)
COST_FRACTION = 0.0026
COST_GATE = 0.20


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC).isoformat()


def _permission_at(regime: Regime4h, one_hour_slot: int) -> tuple[int, int, float]:
    """Return (4h slot, permission, pct) read by a 1h bar opening at this slot."""
    slot = one_hour_slot // 4 - 1
    if slot < 0 or slot >= regime.series.n_slots:
        return slot, -1, float("nan")
    return slot, regime.permission[slot], regime.pct[slot]


def _cluster_at(regime: Regime4h, one_hour_slot: int) -> tuple[int, float]:
    slot, _, pct = _permission_at(regime, one_hour_slot)
    cluster = regime.run_id[slot] if 0 <= slot < regime.series.n_slots else -1
    return cluster, pct


def _is_expansion(series: CandleSeries, index: int) -> bool:
    if not series.usable[index]:
        return False
    if series.local_index[index] < 14:
        return False
    previous_atr = series.atr[index - 1]
    if math.isnan(previous_atr) or previous_atr <= 0.0:
        return False
    range_value = series.high[index] - series.low[index]
    if range_value <= 0.0:
        return False
    true_range = series.tr[index]
    if math.isnan(true_range) or true_range < 2.0 * previous_atr:
        return False
    body = abs(series.close[index] - series.open[index])
    if body / range_value < 0.55:
        return False
    close_location = (series.close[index] - series.low[index]) / range_value
    if close_location < 0.75:
        return False
    if series.close[index] <= series.open[index]:
        return False
    return True


@dataclass
class Episode:
    key: str
    expansion_index: int
    level: float
    atr: float
    permission_at_e: int
    qualified: bool
    setup_low: float
    phase: str = "touch"  # "touch" or "confirm"
    touch_index: int | None = None
    absorbed: int = 0
    secondary: list[str] = field(default_factory=list)


def _entry_diagnostics(series: CandleSeries, index: int) -> list[str]:
    labels: list[str] = []
    if index >= series.n_slots:
        return labels
    if not series.is_closed[index]:
        labels.append("unclosed_entry_bar")
    if series.volume[index] <= 0 or series.trade_count[index] <= 0:
        labels.append("zero_volume_entry")
    if series.partial[index]:
        labels.append("partial_entry_bar")
    if not series.ohlc_valid[index]:
        labels.append("invalid_entry_ohlc")
    return labels


def run_candidate_b(
    series: CandleSeries,
    regime: Regime4h,
    *,
    dev_end_ms: int = DEV_END_MS,
) -> dict[str, Any]:
    """Run the full B pipeline and return counts, labels, and signal metadata."""
    counts: Counter[str] = Counter({f"S{index}": 0 for index in range(1, 11)})
    primary: Counter[str] = Counter()
    secondary: Counter[str] = Counter()
    diagnostics: Counter[str] = Counter()

    counts["S1"] = sum(series.usable)
    pre_gate: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    active: Episode | None = None
    ended_this_bar = False

    def finish(episode: Episode, label: str, *, secondary_labels: list[str] | None = None) -> None:
        nonlocal active
        primary[label] += 1
        for item in (secondary_labels or []) + episode.secondary:
            secondary[item] += 1
        active = None

    def structural_end(episode: Episode, label: str) -> None:
        if episode.qualified:
            finish(episode, label)
        else:
            label = "warmup_regime" if episode.permission_at_e == -1 else "regime_not_permitted"
            finish(episode, label)

    for index in range(series.n_slots):
        if not series.usable[index]:
            if active is not None:
                structural_end(active, "segment_break")
            continue

        if series.local_index[index] >= 14:
            counts["S2"] += 1

        expansion = _is_expansion(series, index)
        if expansion:
            counts["S3"] += 1

        ended_this_bar = False
        episode_was_active = active is not None

        if active is not None:
            episode = active
            episode.setup_low = min(episode.setup_low, series.low[index])

            if episode.phase == "touch":
                if index <= episode.expansion_index + 6:
                    touch_bound = episode.level + 0.25 * episode.atr
                    if series.low[index] <= touch_bound:
                        penetration = (episode.level - series.low[index]) / episode.atr
                        if penetration > 0.50:
                            structural_end(episode, "retest_too_deep")
                            ended_this_bar = True
                        else:
                            episode.phase = "confirm"
                            episode.touch_index = index
                    elif index == episode.expansion_index + 6:
                        structural_end(episode, "retest_timeout")
                        ended_this_bar = True
                else:  # defensive: the window cannot be exceeded without ending
                    structural_end(episode, "retest_timeout")
                    ended_this_bar = True
            else:
                assert episode.touch_index is not None
                lower_bound = episode.level - 0.50 * episode.atr
                if series.close[index] < lower_bound:
                    structural_end(episode, "structure_broken")
                    ended_this_bar = True
                elif index <= episode.touch_index + 3:
                    confirmed = (
                        series.close[index] > episode.level
                        and series.close[index] > series.open[index]
                    )
                    if confirmed:
                        if not episode.qualified:
                            structural_end(episode, "structural_confirmation_without_regime")
                            ended_this_bar = True
                        else:
                            counts["S6"] += 1
                            regime_slot, permission_c, pct_c = _permission_at(regime, index)
                            if permission_c != 1:
                                finish(episode, "regime_lost")
                                ended_this_bar = True
                            else:
                                expected_ms = slot_open_ms(index + 1, "1h")
                                entry_present = (
                                    index + 1 < series.n_slots
                                    and series.present[index + 1]
                                    and series.exact[index + 1]
                                )
                                entry_diag = _entry_diagnostics(series, index + 1)
                                if expected_ms < 0 or expected_ms >= dev_end_ms:
                                    finish(
                                        episode,
                                        "entry_outside_interval",
                                        secondary_labels=[] if entry_present else ["no_entry_bar"],
                                    )
                                    ended_this_bar = True
                                elif not entry_present:
                                    finish(episode, "no_entry_bar")
                                    ended_this_bar = True
                                else:
                                    entry_open = series.open[index + 1]
                                    if entry_open <= 0.0:
                                        finish(episode, "invalid_entry_price")
                                        ended_this_bar = True
                                    else:
                                        stop = episode.setup_low
                                        distance = entry_open - stop
                                        if stop <= 0.0 or distance <= 0.0:
                                            finish(episode, "invalid_stop")
                                            ended_this_bar = True
                                        else:
                                            counts["S7"] += 1
                                            cost = COST_FRACTION * entry_open / distance
                                            signal_ms = series.open_ms(index) + series.tf_ms - 1
                                            cluster = (
                                                regime.run_id[regime_slot]
                                                if 0 <= regime_slot < regime.series.n_slots
                                                else -1
                                            )
                                            record = {
                                                "key": episode.key,
                                                "expansion_time_ms": series.open_ms(
                                                    episode.expansion_index
                                                ),
                                                "expansion_time_iso": _iso(
                                                    series.open_ms(episode.expansion_index)
                                                ),
                                                "signal_time_ms": signal_ms,
                                                "signal_time_iso": _iso(signal_ms),
                                                "entry_time_ms": series.open_ms(index + 1),
                                                "entry_time_iso": _iso(series.open_ms(index + 1)),
                                                "entry_open": entry_open,
                                                "stop": stop,
                                                "D": distance,
                                                "stop_fraction": distance / entry_open,
                                                "cost_R": cost,
                                                "permission_e": episode.permission_at_e,
                                                "permission_c": permission_c,
                                                "regime_slot": regime_slot,
                                                "regime_pct": pct_c,
                                                "cluster_id": cluster,
                                                "entry_diagnostics": entry_diag,
                                                "rejection": None,
                                            }
                                            for label in entry_diag:
                                                diagnostics[label] += 1
                                                secondary[label] += 1
                                            if cost <= COST_GATE:
                                                counts["S8"] += 1
                                                feasible.append(record)
                                                pre_gate.append(record)
                                            else:
                                                record = {**record, "rejection": "cost_gate"}
                                                pre_gate.append(record)
                                                primary["cost_gate"] += 1
                                            active = None
                                            ended_this_bar = True
                    elif index == episode.touch_index + 3:
                        structural_end(episode, "resumption_timeout")
                        ended_this_bar = True
                elif index >= episode.touch_index + 3:
                    structural_end(episode, "resumption_timeout")
                    ended_this_bar = True

            if episode_was_active and expansion:
                # The episode was active when this bar opened; the expansion is
                # absorbed even if the episode itself ends on this bar.
                diagnostics["expansions_absorbed"] += 1
                if active is not None:
                    active.absorbed += 1
            if ended_this_bar and active is not None:  # pragma: no cover - defensive
                raise AssertionError("episode state machine ended without clearing active")

        if active is None and not ended_this_bar and expansion:
            permission_e, pct_e = _permission_at(regime, index)[1:]
            counts["S4"] += 1
            if permission_e == 1:
                counts["S5"] += 1
            episode = Episode(
                key=f"B:{_iso(series.open_ms(index))}",
                expansion_index=index,
                level=series.close[index],
                atr=series.atr[index],
                permission_at_e=permission_e,
                qualified=(permission_e == 1),
                setup_low=series.low[index],
            )
            active = episode

    if active is not None:
        diagnostics["development_end_truncation"] += 1
        structural_end(active, "segment_break")

    # Deduplication and non-overlap are applied only after the cost gate.
    from .stats import deduplicate_by_entry, non_overlap

    dedup = deduplicate_by_entry(feasible)
    unique = dedup["unique"]
    counts["S9"] = len(unique)
    for _ in dedup["duplicates"]:
        primary["duplicate_entry"] += 1

    canonical = non_overlap(unique, B_HOLD_HOURS)
    counts["S10"] = canonical["accepted_count"]
    non_overlap_sets = {"72h": canonical}
    for hours in B_SENSITIVITY_HOURS:
        non_overlap_sets[f"{int(hours)}h"] = non_overlap(unique, hours)

    accepted_keys = set(canonical["accepted_keys"])
    for record in unique:
        if record["key"] not in accepted_keys:
            record["rejection"] = "non_overlap"

    # Reconcile the attempt accounting.  Every S4 attempt ends in exactly one
    # rejection label or in S7; every S7 signal is either cost_gate or S8.
    rejected_attempts = sum(
        count
        for label, count in primary.items()
        if label
        not in {
            "cost_gate",
            "duplicate_entry",
            "non_overlap",
        }
    )
    reconciliation = {
        "S3_equals_S4_plus_expansions_absorbed": (
            counts["S3"] == counts["S4"] + diagnostics["expansions_absorbed"]
        ),
        "S4_equals_rejected_attempts_plus_S7": (
            counts["S4"] == rejected_attempts + counts["S7"]
        ),
        "S7_equals_cost_gate_plus_S8": (
            counts["S7"] == primary["cost_gate"] + counts["S8"]
        ),
        "S8_equals_S9_plus_duplicate_entry": (
            counts["S8"] == counts["S9"] + primary["duplicate_entry"]
        ),
    }

    return {
        "candidate": "B",
        "counts": dict(counts),
        "primary_labels": dict(sorted(primary.items())),
        "secondary_labels": dict(sorted(secondary.items())),
        "diagnostics": dict(sorted(diagnostics.items())),
        "pre_gate": sorted(pre_gate, key=lambda record: (record["entry_time_ms"], record["key"])),
        "feasible": sorted(feasible, key=lambda record: (record["entry_time_ms"], record["key"])),
        "unique": sorted(unique, key=lambda record: (record["entry_time_ms"], record["key"])),
        "non_overlap": non_overlap_sets,
        "reconciliation": reconciliation,
        "notes": {
            "M_all_population": "S7 valid confirmation regime + valid entry/stop, pre-gate",
            "M_feasible_population": "S8 cost-feasible",
            "cluster_population": (
                "S8, assigned to the permission==True run containing the "
                "confirmation-bar 4h read"
            ),
            "no_outcome": "No P&L, return, expectancy, drawdown, or trade outcome is computed.",
        },
    }
