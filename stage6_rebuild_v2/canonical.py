"""Canonical trade reconstruction and provenance checks for Stage 6 v1 (v2).

One canonical trade is ``(entry_index, entry_price, stop_price, target_r=1)``.
Every ledger row sharing that identity is an observation of the same executable
trade.  Conflicts, out-of-range indices and unexplained outcomes are critical
identity/accounting failures and abort the run.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.research.aggregate import assign_episodes  # noqa: E402

from accounting import (  # noqa: E402
    BARRIER_HORIZON,
    TARGET_R,
    InvariantError,
)

TARGET_KEY = "1"
DEV_END = "2024-07-01T00:00:00+00:00"
STEP_SECONDS = 300

EXPECTED_STAGE5 = {
    "rows": 2_395_528,
    "unique_entry_candles": 103_558,
    "resolved_trades": 101_789,
    "episodes": 22_982,
    "unique_event_indices": 103_558,
}


def _norm_time(value) -> str:
    return str(value).replace(" ", "T")


def _parse_time(value) -> datetime:
    return datetime.fromisoformat(_norm_time(value))


def load_bars(path: str | Path, dev_end: str = DEV_END) -> dict:
    """Load only the development split and build a contiguous-bar gap map."""
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    end = _parse_time(dev_end)
    selected = [
        bar for bar in raw if _parse_time(bar["open_time"]) < end
    ]
    if not selected:
        raise InvariantError("development split contains no bars")
    times = [_parse_time(bar["open_time"]) for bar in selected]
    gap_after = np.zeros(len(selected) - 1, dtype=bool)
    gaps = []
    for i in range(len(selected) - 1):
        actual = (times[i + 1] - times[i]).total_seconds()
        if int(actual) != STEP_SECONDS:
            gap_after[i] = True
            gaps.append(
                {
                    "left_index": i,
                    "right_index": i + 1,
                    "left_open_time": _norm_time(selected[i]["open_time"]),
                    "right_open_time": _norm_time(selected[i + 1]["open_time"]),
                    "step_seconds": int(actual),
                    "missing_bars": int(actual // STEP_SECONDS) - 1,
                }
            )
    return {
        "opens": np.array([float(bar["open"]) for bar in selected], dtype=float),
        "closes": np.array([float(bar["close"]) for bar in selected], dtype=float),
        "highs": np.array([float(bar["high"]) for bar in selected], dtype=float),
        "lows": np.array([float(bar["low"]) for bar in selected], dtype=float),
        "open_times": [_norm_time(bar["open_time"]) for bar in selected],
        "close_times": [_norm_time(bar["close_time"]) for bar in selected],
        "gap_after": gap_after,
        "gaps": gaps,
        "dev_end": dev_end,
        "step_seconds": STEP_SECONDS,
    }


def window_has_gap(bars: dict, start: int, end: int) -> bool:
    """True if any missing bar falls between start and end (inclusive)."""
    if end <= start:
        return False
    gap_after = bars["gap_after"]
    return bool(gap_after[start:end].any())


def stream_ledger(path: str | Path, bars: dict, *, progress_every: int = 500_000) -> tuple[dict, dict]:
    """Collapse the observation ledger to canonical identities.

    All rows at one identity must agree on confirmation index, the primary
    target outcome, stop distance and truncation flag.  Any disagreement aborts.
    """
    n_bars = len(bars["open_times"])
    records: dict[tuple, dict] = {}
    rows_read = 0
    unique_events: set[int] = set()
    conflicts = Counter()
    out_of_range = 0
    alignment_checked = 0
    alignment_bad = 0

    with open(path, "r", encoding="utf-8", buffering=1 << 20) as handle:
        for line in handle:
            rows_read += 1
            row = json.loads(line)
            entry_index = int(row["entry_index"])
            entry_price = row["entry_price"]
            stop_price = row["stop_price"]
            key = (entry_index, entry_price, stop_price)
            event_index = int(row["event_index"])
            unique_events.add(event_index)
            target = row["targets"][TARGET_KEY]
            target_tuple = (
                target["target_before_stop"],
                target["bars_to_resolve"],
                target["bars_to_target"],
                target["bars_to_stop"],
                target["unresolved"],
                target["ambiguous_bar"],
                target["exit_price"],
            )
            confirmation_index = int(row["confirmation_index"])
            stop_distance = float(row["stop_distance"])
            truncated = bool(row["truncated"])

            if entry_index < 0 or entry_index >= n_bars:
                out_of_range += 1
                raise InvariantError(
                    f"ledger entry_index {entry_index} outside development bars"
                )
            alignment_checked += 1
            if _norm_time(bars["open_times"][entry_index]) != _norm_time(row["entry_time"]):
                alignment_bad += 1
                raise InvariantError(
                    f"entry_time mismatch at index {entry_index}: "
                    f"{row['entry_time']} != {bars['open_times'][entry_index]}"
                )

            rec = records.get(key)
            if rec is None:
                records[key] = {
                    "entry_index": entry_index,
                    "entry_time": row["entry_time"],
                    "confirmation_index": confirmation_index,
                    "confirmation_time": row["confirmation_time"],
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "stop_distance": stop_distance,
                    "target_r": float(TARGET_R),
                    "target_tuple": target_tuple,
                    "truncated": truncated,
                    "event_indices": {event_index},
                    "detectors": {row["detector"]},
                    "observations": 1,
                    "spill_min": int(row["spill_line"]),
                    "spill_max": int(row["spill_line"]),
                }
            else:
                rec["observations"] += 1
                rec["event_indices"].add(event_index)
                rec["detectors"].add(row["detector"])
                rec["spill_min"] = min(rec["spill_min"], int(row["spill_line"]))
                rec["spill_max"] = max(rec["spill_max"], int(row["spill_line"]))
                if rec["confirmation_index"] != confirmation_index:
                    conflicts["confirmation_index"] += 1
                if rec["target_tuple"] != target_tuple:
                    conflicts["target_outcome"] += 1
                if rec["stop_distance"] != stop_distance:
                    conflicts["stop_distance"] += 1
                if rec["truncated"] != truncated:
                    conflicts["truncated"] += 1

            if rows_read % progress_every == 0:
                print(
                    f"    ledger rows {rows_read:,}  canonical candidates {len(records):,}",
                    flush=True,
                )

    if conflicts:
        raise InvariantError(f"identity conflicts inside canonical groups: {dict(conflicts)}")
    if rows_read == 0:
        raise InvariantError("ledger is empty")
    return records, {
        "rows_read": rows_read,
        "canonical_candidates": len(records),
        "duplicate_rows_collapsed": rows_read - len(records),
        "unique_event_indices": len(unique_events),
        "alignment_checked": alignment_checked,
        "alignment_mismatches": alignment_bad,
        "entry_index_out_of_range": out_of_range,
        "conflicts": dict(conflicts),
    }


def finalize_trades(records: dict, bars: dict) -> tuple[list[dict], dict]:
    """Build canonical trades with frozen exits and gap-checked C1 time stops."""
    n_bars = len(bars["open_times"])
    last_index = n_bars - 1
    trades: list[dict] = []
    integrity = defaultdict(int)
    invalid_reasons = Counter()

    for rec in records.values():
        entry_index = int(rec["entry_index"])
        entry_raw = float(rec["entry_price"])
        stop_raw = float(rec["stop_price"])
        stop_distance = float(rec["stop_distance"])
        if not (entry_raw > 0 and stop_raw > 0 and math.isfinite(entry_raw) and math.isfinite(stop_raw)):
            raise InvariantError(f"non-finite or non-positive price at entry {entry_index}")
        if not math.isclose(
            (entry_raw - stop_raw), stop_distance, rel_tol=0.0, abs_tol=1e-6
        ):
            raise InvariantError(
                f"stop distance conflict at entry {entry_index}: "
                f"entry-stop={entry_raw - stop_raw} ledger={stop_distance}"
            )
        if stop_distance <= 0:
            raise InvariantError(f"non-positive stop distance at entry {entry_index}")

        target_before_stop, bars_to_resolve, bars_to_target, bars_to_stop, unresolved, ambiguous, exit_price = (
            rec["target_tuple"]
        )
        resolved = not bool(unresolved)
        target_raw = entry_raw + TARGET_R * stop_distance

        if resolved:
            if bars_to_resolve is None:
                raise InvariantError(f"resolved outcome without bars at entry {entry_index}")
            offset = int(bars_to_resolve)
            if offset < 0 or offset > BARRIER_HORIZON - 1:
                raise InvariantError(
                    f"resolved offset {offset} outside 12-bar horizon at entry {entry_index}"
                )
            exit_index = entry_index + offset
            if exit_index > last_index:
                raise InvariantError(
                    f"resolved exit index {exit_index} outside development data"
                )
            if window_has_gap(bars, entry_index, exit_index):
                raise InvariantError(
                    f"resolved outcome crosses a data gap at entry {entry_index}"
                )
            exit_raw = float(exit_price)
            if not math.isfinite(exit_raw) or exit_raw <= 0:
                raise InvariantError(f"non-finite resolved exit at entry {entry_index}")
            won = bool(target_before_stop)
            if won and exit_raw < target_raw - 1e-6:
                raise InvariantError(
                    f"target outcome below target at entry {entry_index}: "
                    f"{exit_raw} < {target_raw}"
                )
            if not won and exit_raw > stop_raw + 1e-6:
                raise InvariantError(
                    f"stop outcome above stop at entry {entry_index}: "
                    f"{exit_raw} > {stop_raw}"
                )
            exit_time = bars["close_times"][exit_index]
            exit_kind = "barrier"
            time_exit_valid = False
            time_exit_invalid_reason = None
            integrity["resolved_exits"] += 1
            if offset == 0:
                integrity["resolved_on_entry_bar"] += 1
            if bool(ambiguous):
                integrity["ambiguous_resolved"] += 1
            if won and exit_raw > target_raw + 1e-9:
                integrity["target_gap_fill_wins"] += 1
            if (not won) and exit_raw < stop_raw - 1e-9:
                integrity["stop_gap_fill_losses"] += 1
        else:
            won = False
            ambiguous = bool(ambiguous)
            exit_kind = "time_stop"
            time_exit_valid = False
            time_exit_invalid_reason = None
            exit_index = None
            exit_raw = None
            exit_time = None
            integrity["censored"] += 1
            if entry_index < 0 or entry_index >= n_bars:
                time_exit_invalid_reason = "entry_outside_development"
            elif entry_index + BARRIER_HORIZON - 1 > last_index:
                time_exit_invalid_reason = "insufficient_future_bars"
            elif window_has_gap(bars, entry_index, entry_index + BARRIER_HORIZON - 1):
                time_exit_invalid_reason = "gap_in_window"
            else:
                exit_index = entry_index + BARRIER_HORIZON - 1
                exit_raw = float(bars["closes"][exit_index])
                exit_time = bars["close_times"][exit_index]
                time_exit_valid = True
                integrity["censored_time_exit_valid"] += 1
            if time_exit_invalid_reason is not None:
                invalid_reasons[time_exit_invalid_reason] += 1
                integrity["censored_time_exit_invalid"] += 1

        trades.append(
            {
                "trade_id": None,
                "entry_index": entry_index,
                "exit_index": exit_index,
                "entry_time": _norm_time(rec["entry_time"]),
                "exit_time": _norm_time(exit_time) if exit_time else None,
                "confirmation_index": int(rec["confirmation_index"]),
                "confirmation_time": _norm_time(rec["confirmation_time"]),
                "entry_raw": entry_raw,
                "stop_raw": stop_raw,
                "stop_distance": stop_distance,
                "target_r": float(TARGET_R),
                "target_raw": target_raw,
                "resolved": resolved,
                "won": won,
                "ambiguous": ambiguous if resolved else False,
                "truncated": bool(rec["truncated"]),
                "exit_kind": exit_kind,
                "exit_raw": exit_raw,
                "time_exit_valid": time_exit_valid,
                "time_exit_invalid_reason": time_exit_invalid_reason,
                "observations": int(rec["observations"]),
                "event_count": len(rec["event_indices"]),
                "event_indices": sorted(rec["event_indices"]),
                "detectors": sorted(rec["detectors"]),
                "spill_min": int(rec["spill_min"]),
                "spill_max": int(rec["spill_max"]),
                "episode_id": None,
            }
        )

    trades.sort(key=lambda t: (t["entry_index"], t["entry_raw"], t["stop_raw"]))
    for i, trade in enumerate(trades):
        trade["trade_id"] = i

    order = sorted(
        range(len(trades)),
        key=lambda i: (
            trades[i]["confirmation_index"],
            trades[i]["entry_index"],
            trades[i]["trade_id"],
        ),
    )
    ids = assign_episodes(
        [trades[i]["confirmation_index"] for i in order], horizon=BARRIER_HORIZON
    )
    for position, trade_index in enumerate(order):
        trades[trade_index]["episode_id"] = int(ids[position])

    for key in (
        "resolved_exits",
        "resolved_on_entry_bar",
        "ambiguous_resolved",
        "target_gap_fill_wins",
        "stop_gap_fill_losses",
        "censored_time_exit_valid",
        "censored_time_exit_invalid",
    ):
        integrity[key] = integrity.get(key, 0)

    bar_counts = Counter(t["entry_index"] for t in trades)
    observations = [t["observations"] for t in trades]
    integrity.update(
        {
            "trades": len(trades),
            "resolved": sum(1 for t in trades if t["resolved"]),
            "censored": sum(1 for t in trades if not t["resolved"]),
            "episodes": len({t["episode_id"] for t in trades}),
            "entry_bars_with_multiple_trades": sum(
                1 for count in bar_counts.values() if count > 1
            ),
            "max_canonical_trades_per_entry_bar": max(bar_counts.values()) if bar_counts else 0,
            "max_observations_per_trade": max(observations) if observations else 0,
            "mean_observations_per_trade": (
                sum(observations) / len(observations) if observations else None
            ),
            "censored_invalid_reasons": dict(sorted(invalid_reasons.items())),
            "sample_start": min(t["entry_time"] for t in trades),
            "sample_end": max(
                (t["exit_time"] for t in trades if t["exit_time"]), default=None
            ),
        }
    )
    integrity["observations_total"] = sum(observations)
    return trades, dict(integrity)


def reconcile_provenance(stream: dict, integrity: dict, expected: dict | None = None) -> dict:
    """Hard abort unless canonical counts match the frozen Stage 5 checkpoint."""
    expected = expected or EXPECTED_STAGE5
    actual = {
        "rows": stream["rows_read"],
        "unique_entry_candles": integrity["trades"],
        "resolved_trades": integrity["resolved"],
        "episodes": integrity["episodes"],
        "unique_event_indices": stream["unique_event_indices"],
    }
    mismatches = {
        key: {"expected": expected.get(key), "actual": value}
        for key, value in actual.items()
        if expected.get(key) != value
    }
    identities = {
        "observations_equal_rows": integrity["observations_total"] == stream["rows_read"],
        "duplicates_plus_trades_equal_rows": (
            stream["duplicate_rows_collapsed"] + integrity["trades"] == stream["rows_read"]
        ),
        "resolved_plus_censored_equal_trades": (
            integrity["resolved"] + integrity["censored"] == integrity["trades"]
        ),
        "time_exit_valid_plus_invalid_equal_censored": (
            integrity.get("censored_time_exit_valid", 0)
            + integrity.get("censored_time_exit_invalid", 0)
            == integrity["censored"]
        ),
    }
    failed_identities = [key for key, ok in identities.items() if not ok]
    if mismatches or failed_identities:
        raise InvariantError(
            f"provenance reconciliation failed: mismatches={mismatches} "
            f"identities={failed_identities}"
        )
    return {
        "expected": expected,
        "actual": actual,
        "identities": identities,
        "passed": True,
    }
