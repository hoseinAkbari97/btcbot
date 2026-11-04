"""Gap-aware data-alignment audit for the Stage 2J census.

The audit compares only complete buckets.  Gap-affected buckets are reported
separately and never enter the tolerance denominator.  The twelve registered
4h supplied buckets are exempt from the 4h-from-1h denominator under the
ratified M3 rule.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS

from .series import CandleSeries, FiveMinuteSupport, slot_open_ms


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC).isoformat()


def _missing_runs(present: Sequence[bool], timeframe: str) -> list[dict[str, Any]]:
    tf_ms = TIMEFRAME_MS[timeframe]
    n = len(present)
    runs: list[dict[str, Any]] = []
    index = 0
    while index < n:
        if present[index]:
            index += 1
            continue
        start = index
        while index + 1 < n and not present[index + 1]:
            index += 1
        end = index
        runs.append(
            {
                "missing_bars": end - start + 1,
                "first_missing_open_utc": _iso(slot_open_ms(start, timeframe)),
                "last_missing_open_utc": _iso(slot_open_ms(end, timeframe)),
                "last_bar_before_utc": _iso(slot_open_ms(start, timeframe) - tf_ms),
                "resumes_at_utc": _iso(slot_open_ms(end, timeframe) + tf_ms),
            }
        )
        index += 1
    return runs


def _expected_resume_open_ms(resume_ms: int, timeframe: str) -> int:
    """Floor a 5m-grid resume time to the containing slot of another grid."""
    tf_ms = TIMEFRAME_MS[timeframe]
    return resume_ms - ((resume_ms - DEV_START_MS) % tf_ms)


def _within_volume_tolerance(left: float, right: float, tolerance: float = 1e-9) -> bool:
    if left == right:
        return True
    scale = max(abs(left), abs(right))
    if scale == 0.0:
        return True
    return abs(left - right) / scale <= tolerance


def _compare_upper_from_members(
    *,
    upper: CandleSeries,
    member_timeframe: str,
    member_series: CandleSeries,
    members_per_bucket: int,
    exempt_slots: frozenset[int] = frozenset(),
) -> dict[str, Any]:
    complete = 0
    gap_affected = 0
    exempt = 0
    exempt_gap_affected = 0
    missing_upper = 0
    missing_members_total = 0
    max_missing_members = 0
    open_mismatch = 0
    high_mismatch = 0
    low_mismatch = 0
    close_mismatch = 0
    ohlc_mismatch_buckets = 0
    volume_mismatch = 0
    examples: list[dict[str, Any]] = []

    for slot in range(upper.n_slots):
        base = slot * members_per_bucket
        member_indices = list(range(base, base + members_per_bucket))
        usable_members = sum(
            1
            for index in member_indices
            if index < member_series.n_slots and member_series.usable[index]
        )
        if slot in exempt_slots:
            exempt += 1
            if usable_members < members_per_bucket:
                exempt_gap_affected += 1
            continue
        if usable_members < members_per_bucket:
            gap_affected += 1
            missing_members_total += members_per_bucket - usable_members
            max_missing_members = max(max_missing_members, members_per_bucket - usable_members)
            continue
        complete += 1
        if not upper.present[slot] or not upper.exact[slot]:
            missing_upper += 1
            continue
        aggregate_open = member_series.open[base]
        aggregate_high = max(member_series.high[base : base + members_per_bucket])
        aggregate_low = min(member_series.low[base : base + members_per_bucket])
        aggregate_close = member_series.close[base + members_per_bucket - 1]
        aggregate_volume = math.fsum(
            member_series.volume[base : base + members_per_bucket]
        )
        open_bad = aggregate_open != upper.open[slot]
        high_bad = aggregate_high != upper.high[slot]
        low_bad = aggregate_low != upper.low[slot]
        close_bad = aggregate_close != upper.close[slot]
        open_mismatch += int(open_bad)
        high_mismatch += int(high_bad)
        low_mismatch += int(low_bad)
        close_mismatch += int(close_bad)
        if open_bad or high_bad or low_bad or close_bad:
            ohlc_mismatch_buckets += 1
            if len(examples) < 10:
                examples.append(
                    {
                        "slot": slot,
                        "open_utc": _iso(upper.open_ms(slot)),
                        "aggregate": [
                            aggregate_open,
                            aggregate_high,
                            aggregate_low,
                            aggregate_close,
                        ],
                        "supplied": [
                            upper.open[slot],
                            upper.high[slot],
                            upper.low[slot],
                            upper.close[slot],
                        ],
                    }
                )
        if not _within_volume_tolerance(aggregate_volume, upper.volume[slot]):
            volume_mismatch += 1

    mismatch_share = (ohlc_mismatch_buckets / complete) if complete else None
    return {
        "upper_timeframe": upper.timeframe,
        "member_timeframe": member_timeframe,
        "members_per_bucket": members_per_bucket,
        "complete_buckets": complete,
        "gap_affected_buckets": gap_affected,
        "missing_members_total": missing_members_total,
        "max_missing_members": max_missing_members,
        "exempt_buckets": exempt,
        "exempt_gap_affected_buckets": exempt_gap_affected,
        "missing_upper_buckets": missing_upper,
        "open_mismatches": open_mismatch,
        "high_mismatches": high_mismatch,
        "low_mismatches": low_mismatch,
        "close_mismatches": close_mismatch,
        "ohlc_mismatch_buckets": ohlc_mismatch_buckets,
        "ohlc_mismatch_share_of_complete": mismatch_share,
        "volume_mismatches": volume_mismatch,
        "volume_relative_tolerance": 1e-9,
        "examples": examples,
        "passes_0_1_percent_price_tolerance": (
            mismatch_share is not None and mismatch_share <= 0.001
        ),
    }


def _compare_15m_from_5m(support: FiveMinuteSupport, series_15m: CandleSeries) -> dict[str, Any]:
    complete = 0
    gap_affected = 0
    missing_upper = 0
    missing_members_total = 0
    max_missing_members = 0
    open_mismatch = 0
    hlc_mismatch_buckets = 0
    high_mismatch = 0
    low_mismatch = 0
    close_mismatch = 0
    volume_mismatch = 0
    examples: list[dict[str, Any]] = []

    for slot in range(series_15m.n_slots):
        members = support.member_15m[slot]
        if members != 3:
            gap_affected += 1
            missing_members_total += 3 - members
            max_missing_members = max(max_missing_members, 3 - members)
            continue
        complete += 1
        if not series_15m.present[slot] or not series_15m.exact[slot]:
            missing_upper += 1
            continue
        aggregate_open = support.aggregate_open_15m[slot]
        aggregate_high = support.aggregate_high_15m[slot]
        aggregate_low = support.aggregate_low_15m[slot]
        aggregate_close = support.aggregate_close_15m[slot]
        aggregate_volume = support.aggregate_volume_15m[slot]
        high_bad = aggregate_high != series_15m.high[slot]
        low_bad = aggregate_low != series_15m.low[slot]
        close_bad = aggregate_close != series_15m.close[slot]
        open_bad = aggregate_open != series_15m.open[slot]
        open_mismatch += int(open_bad)
        high_mismatch += int(high_bad)
        low_mismatch += int(low_bad)
        close_mismatch += int(close_bad)
        if high_bad or low_bad or close_bad:
            hlc_mismatch_buckets += 1
            if len(examples) < 10:
                examples.append(
                    {
                        "slot": slot,
                        "open_utc": _iso(series_15m.open_ms(slot)),
                        "aggregate_hlc": [aggregate_high, aggregate_low, aggregate_close],
                        "supplied_hlc": [
                            series_15m.high[slot],
                            series_15m.low[slot],
                            series_15m.close[slot],
                        ],
                    }
                )
        if not _within_volume_tolerance(aggregate_volume, series_15m.volume[slot]):
            volume_mismatch += 1

    mismatch_share = (hlc_mismatch_buckets / complete) if complete else None
    return {
        "upper_timeframe": "15m",
        "member_timeframe": "5m",
        "members_per_bucket": 3,
        "complete_buckets": complete,
        "gap_affected_buckets": gap_affected,
        "missing_members_total": missing_members_total,
        "max_missing_members": max_missing_members,
        "missing_upper_buckets": missing_upper,
        "open_mismatches_diagnostic": open_mismatch,
        "high_mismatches": high_mismatch,
        "low_mismatches": low_mismatch,
        "close_mismatches": close_mismatch,
        "hlc_mismatch_buckets": hlc_mismatch_buckets,
        "hlc_mismatch_share_of_complete": mismatch_share,
        "volume_mismatches": volume_mismatch,
        "volume_relative_tolerance": 1e-9,
        "examples": examples,
        "passes_0_1_percent_price_tolerance": (
            mismatch_share is not None and mismatch_share <= 0.001
        ),
    }


def _grid_check(series: CandleSeries) -> dict[str, Any]:
    present = sum(series.present)
    off_grid_present = sum(
        1 for slot in range(series.n_slots) if series.present[slot] and not series.exact[slot]
    )
    boundary_hours_ok = True
    if series.timeframe == "4h":
        for slot in range(series.n_slots):
            if not series.present[slot]:
                continue
            moment = datetime.fromtimestamp(series.open_ms(slot) / 1000.0, tz=UTC)
            if moment.hour not in {0, 4, 8, 12, 16, 20} or moment.minute or moment.second:
                boundary_hours_ok = False
                break
    return {
        "timeframe": series.timeframe,
        "present_bars": present,
        "off_grid_present": off_grid_present,
        "four_hour_boundary_hours_ok": boundary_hours_ok if series.timeframe == "4h" else None,
    }


def build_alignment_report(
    *,
    support: FiveMinuteSupport,
    series_15m: CandleSeries,
    series_1h: CandleSeries,
    series_4h: CandleSeries,
    exempt_4h_open_times: Sequence[str],
    manifest_gaps: dict[str, Any],
) -> dict[str, Any]:
    exempt_slots = frozenset(
        (
            int(datetime.fromisoformat(value).timestamp() * 1000)
            - series_4h.open_ms(0)
        )
        // TIMEFRAME_MS["4h"]
        for value in exempt_4h_open_times
    )
    four_from_one = _compare_upper_from_members(
        upper=series_4h,
        member_timeframe="1h",
        member_series=series_1h,
        members_per_bucket=4,
        exempt_slots=exempt_slots,
    )
    one_from_15 = _compare_upper_from_members(
        upper=series_1h,
        member_timeframe="15m",
        member_series=series_15m,
        members_per_bucket=4,
    )
    fifteen_from_five = _compare_15m_from_5m(support, series_15m)

    missing_5m = _missing_runs(support.present_5m, "5m")
    missing_15m = _missing_runs(series_15m.present, "15m")
    missing_1h = _missing_runs(series_1h.present, "1h")
    missing_4h = _missing_runs(series_4h.present, "4h")
    detected = {
        "5m": missing_5m,
        "15m": missing_15m,
        "1h": missing_1h,
        "4h": missing_4h,
    }
    expected_totals = {
        "5m": manifest_gaps["totals"]["missing_5m_bars"],
        "15m": manifest_gaps["totals"]["missing_15m_bars"],
        "1h": manifest_gaps["totals"]["missing_1h_bars"],
        "4h": 0,
    }
    totals = {
        timeframe: sum(run["missing_bars"] for run in runs)
        for timeframe, runs in detected.items()
    }
    counts = {timeframe: len(runs) for timeframe, runs in detected.items()}

    per_gap: list[dict[str, Any]] = []
    for gap in manifest_gaps["gaps"]:
        gap_resume_ms = int(datetime.fromisoformat(gap["resumes_at_utc"]).timestamp() * 1000)
        entry: dict[str, Any] = {
            "id": gap["id"],
            "last_bar_before_utc": gap["last_bar_before_gap_utc"],
            "manifest_resumes_at_utc": gap["resumes_at_utc"],
            "manifest_resume_grid": "5m",
        }
        for timeframe, expected_key in (
            ("5m", "missing_5m_bars"),
            ("15m", "missing_15m_bars"),
            ("1h", "missing_1h_bars"),
        ):
            # The frozen manifest records one resume timestamp on the 5m grid.
            # A coarser grid resumes at the containing slot, so the expected
            # per-timeframe resume is the floor of that timestamp to the grid.
            expected_resume_ms = _expected_resume_open_ms(gap_resume_ms, timeframe)
            match = next(
                (
                    run
                    for run in detected[timeframe]
                    if run["resumes_at_utc"] == _iso(expected_resume_ms)
                ),
                None,
            )
            entry[f"{timeframe}_expected_resume_utc"] = _iso(expected_resume_ms)
            entry[f"{timeframe}_detected"] = match
            entry[f"{timeframe}_expected_missing"] = gap[expected_key]
            entry[f"{timeframe}_match"] = (
                match is not None and match["missing_bars"] == gap[expected_key]
            )
        entry["matches"] = all(
            entry[f"{timeframe}_match"] for timeframe in ("5m", "15m", "1h")
        )
        per_gap.append(entry)

    exempt_used = sum(
        1
        for slot in exempt_slots
        if 0 <= slot < series_4h.n_slots and series_4h.present[slot] and series_4h.usable[slot]
    )
    report = {
        "four_hour_from_one_hour": four_from_one,
        "one_hour_from_15m": one_from_15,
        "15m_from_5m": fifteen_from_five,
        "grid_checks": [
            _grid_check(series_15m),
            _grid_check(series_1h),
            _grid_check(series_4h),
        ],
        "registered_gaps": {
            "expected_gap_count": 7,
            "expected_totals": expected_totals,
            "detected_gap_count": counts,
            "detected_totals": totals,
            "totals_match": totals == expected_totals,
            "counts_match": {
                timeframe: counts[timeframe] == (7 if timeframe != "4h" else 0)
                for timeframe in ("5m", "15m", "1h", "4h")
            },
            "per_gap": per_gap,
            "all_per_gap_match": all(entry["matches"] for entry in per_gap),
            "detected_runs": detected,
        },
        "four_hour_exemption": {
            "registered_buckets": len(exempt_slots),
            "supplied_buckets_present_and_usable": exempt_used,
            "excluded_from_4h_from_1h_denominator": four_from_one["exempt_buckets"],
            "note": (
                "The twelve registered supplied 4h buckets are retained in the primary "
                "series and excluded from the 4h-from-1h tolerance denominator, as M3 requires."
            ),
        },
        "partial_bucket_counts": {
            "15m_below_3_members": sum(1 for value in support.member_15m if value != 3),
            "1h_below_12_members": sum(1 for value in support.member_1h if value != 12),
            "4h_exempt_buckets": len(exempt_slots),
        },
    }
    price_checks = [four_from_one, one_from_15, fifteen_from_five]
    report["summary"] = {
        "price_tolerance_checks_pass": all(
            item["passes_0_1_percent_price_tolerance"] for item in price_checks
        ),
        "any_price_mismatch": any(
            item.get("ohlc_mismatch_buckets", item.get("hlc_mismatch_buckets", 0)) > 0
            for item in price_checks
        ),
        "any_volume_mismatch": any(item["volume_mismatches"] > 0 for item in price_checks),
        "missing_bar_totals_match_freeze": totals == expected_totals,
        "registered_gap_locations_match": all(entry["matches"] for entry in per_gap),
        "grid_checks_pass": all(
            check["off_grid_present"] == 0 for check in report["grid_checks"]
        ),
        "four_hour_boundary_hours_ok": report["grid_checks"][-1][
            "four_hour_boundary_hours_ok"
        ],
    }
    report["summary"]["alignment_fail"] = not (
        report["summary"]["price_tolerance_checks_pass"]
        and report["summary"]["missing_bar_totals_match_freeze"]
        and report["summary"]["registered_gap_locations_match"]
        and report["summary"]["grid_checks_pass"]
    )
    return report
