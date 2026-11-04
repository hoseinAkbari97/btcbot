"""Candidate D feasibility census (frozen specification version 2.0.0).

Only the boolean rules in ``CANDIDATE_D_SPEC.md`` are evaluated.  No outcome,
return, P&L, or trade result is computed.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from stage2i_readiness.loader import DEV_END_MS, DEV_START_MS

from .series import CandleSeries, Regime4h, slot_index, slot_open_ms

D_HOLD_HOURS = 6.0  # entry at s+2h, session end at s+8h
D_SESSION_BOUND_HOURS = 8.0
D_SENSITIVITY_HOURS = (12.0, 48.0)
COST_FRACTION = 0.0026
COST_GATE = 0.20
DAY_MS = 86_400_000
SESSION_OFFSETS = (("ASIA", 0), ("EUROPE", 8 * 3_600_000), ("US", 16 * 3_600_000))


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC).isoformat()


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


def _full_session_data(series: CandleSeries, b0: int) -> bool:
    for offset in range(32):
        index = b0 + offset
        if index >= series.n_slots or not series.usable[index]:
            return False
    return True


def run_candidate_d(
    series_15m: CandleSeries,
    series_1h: CandleSeries,
    regime: Regime4h,
    *,
    dev_start_ms: int = DEV_START_MS,
    dev_end_ms: int = DEV_END_MS,
) -> dict[str, Any]:
    """Run the full D pipeline and return counts, labels, and signal metadata."""
    counts: Counter[str] = Counter()
    primary: Counter[str] = Counter()
    secondary: Counter[str] = Counter()
    diagnostics: Counter[str] = Counter()
    per_session: dict[str, Counter[str]] = {
        session_id: Counter() for session_id, _ in SESSION_OFFSETS
    }
    full_data_true = 0
    full_data_false = 0

    counts["S1"] = sum(series_15m.usable)
    pre_gate: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    us_feasible: list[dict[str, Any]] = []

    day_ms = dev_start_ms
    while day_ms < dev_end_ms:
        for session_id, offset in SESSION_OFFSETS:
            start_ms = day_ms + offset
            signal_ms = start_ms + 2 * 3_600_000 - 1
            if signal_ms < dev_start_ms or signal_ms >= dev_end_ms:
                continue

            counts["S0"] += 1
            per_session[session_id]["S0"] += 1
            b0 = slot_index(start_ms, "15m")
            full_data = _full_session_data(series_15m, b0)
            if full_data:
                full_data_true += 1
            else:
                full_data_false += 1

            measurement = all(
                0 <= b0 + offset15 < series_15m.n_slots and series_15m.usable[b0 + offset15]
                for offset15 in range(8)
            )
            if not measurement:
                primary["measurement_window_incomplete"] += 1
                continue
            counts["S2"] += 1
            per_session[session_id]["S2"] += 1

            q = slot_index(start_ms + 3_600_000, "1h")
            if q < 0 or q >= series_1h.n_slots or not series_1h.usable[q]:
                primary["stop_atr_unavailable"] += 1
                continue
            if series_1h.local_index[q] < 13 or math.isnan(series_1h.atr[q]):
                primary["warmup_atr"] += 1
                continue
            atr_q = series_1h.atr[q]

            p0 = series_15m.open[b0]
            p1 = series_15m.close[b0 + 7]
            r2 = p1 / p0 - 1.0
            threshold = 0.5 * atr_q / p0
            if r2 < threshold:
                primary["below_threshold"] += 1
                continue
            counts["S3"] += 1
            per_session[session_id]["S3"] += 1

            budget_slot = slot_index(signal_ms, "4h") - 1
            if (
                budget_slot < 0
                or budget_slot >= regime.series.n_slots
                or not regime.usable[budget_slot]
                or math.isnan(regime.pct[budget_slot])
            ):
                primary["warmup_budget"] += 1
                continue
            pct = regime.pct[budget_slot]
            if pct < 25.0 or pct > 80.0:
                primary["budget_out_of_band"] += 1
                continue
            counts["S4"] += 1
            per_session[session_id]["S4"] += 1

            numerator = 0.0
            denominator = 0.0
            for offset15 in range(8):
                index = b0 + offset15
                typical = (
                    series_15m.high[index]
                    + series_15m.low[index]
                    + series_15m.close[index]
                ) / 3.0
                volume = series_15m.volume[index]
                numerator += typical * volume
                denominator += volume
            if denominator <= 0.0:
                raise AssertionError("signal-evaluable session has zero measurement volume")
            vwap = numerator / denominator
            if p1 <= vwap:
                primary["below_vwap"] += 1
                continue
            counts["S5"] += 1
            per_session[session_id]["S5"] += 1

            b8 = b0 + 8
            expected_ms = slot_open_ms(b8, "15m")
            entry_present = (
                b8 < series_15m.n_slots
                and series_15m.present[b8]
                and series_15m.exact[b8]
            )
            entry_diag = _entry_diagnostics(series_15m, b8)
            if expected_ms < 0 or expected_ms >= dev_end_ms:
                primary["entry_outside_interval"] += 1
                if not entry_present:
                    secondary["no_entry_bar"] += 1
                continue
            if not entry_present:
                primary["no_entry_bar"] += 1
                continue
            entry_open = series_15m.open[b8]
            if entry_open <= 0.0:
                primary["invalid_entry_price"] += 1
                continue
            stop = entry_open - atr_q
            distance = atr_q
            if atr_q <= 0.0 or stop <= 0.0 or distance <= 0.0:
                primary["invalid_stop"] += 1
                continue

            counts["S6"] += 1
            per_session[session_id]["S6"] += 1
            cost = COST_FRACTION * entry_open / distance
            cluster = regime.run_id[budget_slot]
            record = {
                "key": f"D:{_iso(start_ms)}|{session_id}",
                "session_id": session_id,
                "session_start_ms": start_ms,
                "session_start_iso": _iso(start_ms),
                "signal_time_ms": signal_ms,
                "signal_time_iso": _iso(signal_ms),
                "entry_time_ms": series_15m.open_ms(b8),
                "entry_time_iso": _iso(series_15m.open_ms(b8)),
                "entry_open": entry_open,
                "stop": stop,
                "D": distance,
                "stop_fraction": distance / entry_open,
                "cost_R": cost,
                "budget_slot": budget_slot,
                "regime_pct": pct,
                "cluster_id": cluster,
                "atr_1h_q": atr_q,
                "p0": p0,
                "p1": p1,
                "r2": r2,
                "threshold": threshold,
                "vwap": vwap,
                "session_full_data": full_data,
                "entry_diagnostics": entry_diag,
                "rejection": None,
            }
            for label in entry_diag:
                diagnostics[label] += 1
            if cost <= COST_GATE:
                counts["S7"] += 1
                per_session[session_id]["S7"] += 1
                feasible.append(record)
                pre_gate.append(record)
                if session_id == "US":
                    us_feasible.append(record)
            else:
                record = {**record, "rejection": "cost_gate"}
                pre_gate.append(record)
                primary["cost_gate"] += 1
        day_ms += DAY_MS

    from .stats import deduplicate_by_key, non_overlap

    dedup = deduplicate_by_key(feasible)
    unique = dedup["unique"]
    counts["S8"] = len(unique)
    for _ in dedup["duplicates"]:
        primary["duplicate_session"] += 1

    canonical = non_overlap(unique, 24.0)
    counts["S9"] = canonical["accepted_count"]
    non_overlap_sets = {"24h": canonical}
    for hours in D_SENSITIVITY_HOURS:
        non_overlap_sets[f"{int(hours)}h"] = non_overlap(unique, hours)
    accepted_keys = set(canonical["accepted_keys"])
    for record in unique:
        if record["key"] not in accepted_keys:
            record["rejection"] = "non_overlap"
        else:
            per_session[record["session_id"]]["S9"] += 1
    for record in unique:
        per_session[record["session_id"]]["S8"] += 1

    us_only = non_overlap(us_feasible, 24.0)

    signals_incomplete_session = sum(
        1
        for record in pre_gate
        if not record["session_full_data"] and record["rejection"] != "cost_gate"
    )
    signals_incomplete_session_feasible = sum(
        1 for record in feasible if not record["session_full_data"]
    )

    reconciliation = {
        "S7_equals_S8_plus_duplicate_session": (
            counts["S7"] == counts["S8"] + primary["duplicate_session"]
        ),
        "S8_equals_S9_plus_non_overlap": (
            counts["S8"] == counts["S9"] + canonical["rejected_count"]
        ),
    }

    return {
        "candidate": "D",
        "counts": dict(counts),
        "primary_labels": dict(sorted(primary.items())),
        "secondary_labels": dict(sorted(secondary.items())),
        "diagnostics": dict(sorted(diagnostics.items())),
        "per_session": {
            key: dict(sorted(value.items())) for key, value in sorted(per_session.items())
        },
        "session_full_data": {
            "sessions_true": full_data_true,
            "sessions_false": full_data_false,
            "pre_gate_signals_from_incomplete_sessions": signals_incomplete_session,
            "feasible_signals_from_incomplete_sessions": signals_incomplete_session_feasible,
            "note": (
                "session_full_data is a post-count diagnostic over all 32 session bars. "
                "It never removes, defers, or relabels a signal."
            ),
        },
        "us_only": {
            "population": len(us_feasible),
            **us_only,
            "note": (
                "Diagnostic variant restricted to US sessions; "
                "the all-session canonical count governs."
            ),
        },
        "pre_gate": sorted(
            pre_gate, key=lambda record: (record["entry_time_ms"], record["key"])
        ),
        "feasible": sorted(
            feasible, key=lambda record: (record["entry_time_ms"], record["key"])
        ),
        "unique": sorted(
            unique, key=lambda record: (record["entry_time_ms"], record["key"])
        ),
        "non_overlap": non_overlap_sets,
        "reconciliation": reconciliation,
        "notes": {
            "M_all_population": "S6 valid entry/stop, pre-gate",
            "M_feasible_population": "S7 cost-feasible",
            "cluster_primary_population": "S7 (K3); S6 and S9 also reported",
            "no_outcome": "No P&L, return, expectancy, drawdown, or trade outcome is computed.",
        },
    }
