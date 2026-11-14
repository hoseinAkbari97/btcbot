"""Stage 2ZC — Gate 1 development-block data-validity checks.

Scope (O-2A, packet section 6.1):
- the four already-recorded Binance BTCUSDT historical files;
- development block only: [2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z);
- hash verification, gap accounting, duplicate/off-grid/zero-volume/invalid-OHLC
  checks, partial-bucket accounting, segment-boundary accounting, and
  lower-to-higher-timeframe reconciliation.

Explicitly NOT computed: any signal, indicator, outcome, return, or P&L.
The bounded loader inspects only the open_time of the first record at/after the
development end and never decodes that record.

Usage:
    python -m stage2zc_gate1.validate_dev_block > docs/research/stage2zc/DEV_BLOCK_VALIDATION.json
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stage2i_readiness.loader import (
    DEV_END_MS,
    DEV_START_MS,
    TIMEFRAME_MS,
    Candle,
    LoadStats,
    epoch_ms,
    iter_candles,
    iter_object_texts,
)

OPEN_TIME_RE = re.compile(r'"open_time"\s*:\s*"([^"]+)"')

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "backend" / "data" / "datasets"
MANIFEST_PATH = DATASET_DIR / "manifest.json"
TIMEFRAMES = ("5m", "15m", "1h", "4h")
MEMBERS = {"15m": ("5m", 3), "1h": ("15m", 4), "4h": ("1h", 4)}
PRICE_REL_TOLERANCE = 1e-3  # Stage 2J 0.1% complete-bucket tolerance
VOLUME_REL_TOLERANCE = 1e-9


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def relative_close(left: float, right: float, tolerance: float) -> bool:
    if left == right:
        return True
    scale = max(abs(left), abs(right))
    if scale == 0.0:
        return True
    return abs(left - right) / scale <= tolerance


class Slots:
    """Compact per-grid storage for one timeframe over the development block."""

    def __init__(self, timeframe: str) -> None:
        self.timeframe = timeframe
        self.tf_ms = TIMEFRAME_MS[timeframe]
        self.n = (DEV_END_MS - DEV_START_MS) // self.tf_ms
        self.present = [False] * self.n
        self.usable = [False] * self.n
        self.zero_volume = [False] * self.n
        self.open = [math.nan] * self.n
        self.high = [math.nan] * self.n
        self.low = [math.nan] * self.n
        self.close = [math.nan] * self.n
        self.volume = [math.nan] * self.n

    def index(self, open_ms: int) -> int:
        return (open_ms - DEV_START_MS) // self.tf_ms

    def open_ms(self, index: int) -> int:
        return DEV_START_MS + index * self.tf_ms

    def add(self, candle: Candle, usable: bool) -> None:
        index = self.index(candle.open_time_ms)
        self.present[index] = True
        self.usable[index] = usable
        self.zero_volume[index] = candle.volume == 0
        self.open[index] = float(candle.open)
        self.high[index] = float(candle.high)
        self.low[index] = float(candle.low)
        self.close[index] = float(candle.close)
        self.volume[index] = float(candle.volume)


def dev_block_hash(path: Path, timeframe: str) -> dict[str, Any]:
    """SHA-256 over the exact JSON-object bytes of the development block.

    Objects are concatenated in file order with no separator. Only the
    ``open_time`` string of the first record at/after the development end is
    inspected; that record's text is never hashed and its payload is never
    decoded.
    """
    digest = hashlib.sha256()
    hashed = 0
    bytes_hashed = 0
    boundary_inspected = 0
    for text in iter_object_texts(path):
        match = OPEN_TIME_RE.search(text)
        if match is None:
            raise ValueError("record has no open_time")
        open_ms = epoch_ms(match.group(1))
        if open_ms >= DEV_END_MS:
            boundary_inspected += 1
            break
        if open_ms < DEV_START_MS:
            continue
        encoded = text.encode("utf-8")
        digest.update(encoded)
        hashed += 1
        bytes_hashed += len(encoded)
    return {
        "procedure": (
            "SHA-256 over the UTF-8 bytes of each development-interval JSON object "
            "in file order, concatenated without separators"
        ),
        "sha256": digest.hexdigest(),
        "records_hashed": hashed,
        "bytes_hashed": bytes_hashed,
        "boundary_records_inspected": boundary_inspected,
        "boundary_payload_decoded": 0,
        "timeframe": timeframe,
    }


def scan_timeframe(
    timeframe: str,
    expected_sha: str,
    expected_gap_count: int,
    expected_gap_bars_total: int,
) -> tuple[dict[str, Any], Slots]:
    path = DATASET_DIR / f"BTCUSDT-{timeframe}-20210101-20260901.json"
    actual_sha, size = sha256_file(path)
    stats = LoadStats()
    slots = Slots(timeframe)
    tf_ms = TIMEFRAME_MS[timeframe]

    off_grid = 0
    zero_volume = 0
    zero_trade_count = 0
    invalid_ohlc = 0
    non_positive_price = 0
    not_closed = 0
    bad_close_time = 0
    bad_close_time_detail: list[dict[str, Any]] = []
    zero_volume_flat = True
    duplicates = 0
    records = 0
    usable = 0

    previous: int | None = None
    for candle in iter_candles(path, timeframe, stats=stats):
        records += 1
        open_ms = candle.open_time_ms

        if previous is not None and open_ms <= previous:
            duplicates += 1
        previous = open_ms

        if (open_ms - DEV_START_MS) % tf_ms != 0:
            off_grid += 1
        if candle.volume == 0:
            zero_volume += 1
            if not (
                candle.open == candle.high == candle.low == candle.close
                and candle.trade_count == 0
            ):
                zero_volume_flat = False
        if candle.trade_count == 0:
            zero_trade_count += 1
        if not candle.ohlc_valid:
            invalid_ohlc += 1
        if min(candle.open, candle.high, candle.low, candle.close) <= 0:
            non_positive_price += 1
        if not candle.is_closed:
            not_closed += 1
        if candle.close_time_ms != open_ms + tf_ms - 1:
            bad_close_time += 1
            bad_close_time_detail.append(
                {
                    "open_utc": iso(open_ms),
                    "close_time_utc": iso(candle.close_time_ms),
                    "expected_grid_close_utc": iso(open_ms + tf_ms - 1),
                    "delta_seconds": (candle.close_time_ms - (open_ms + tf_ms - 1)) / 1000,
                    "later_than_grid_close": candle.close_time_ms > open_ms + tf_ms - 1,
                }
            )

        is_usable = (
            candle.is_closed
            and candle.volume > 0
            and candle.trade_count > 0
            and candle.ohlc_valid
            and candle.open > 0
        )
        if is_usable:
            usable += 1
        slots.add(candle, is_usable)

    # Gap / segment accounting over the development grid.
    missing_runs: list[dict[str, Any]] = []
    segments = 0
    in_segment = False
    index = 0
    while index < slots.n:
        if slots.present[index]:
            if not in_segment:
                segments += 1
                in_segment = True
            index += 1
            continue
        in_segment = False
        start = index
        while index + 1 < slots.n and not slots.present[index + 1]:
            index += 1
        end = index
        missing_runs.append(
            {
                "missing_bars": end - start + 1,
                "first_missing_open_utc": iso(slots.open_ms(start)),
                "last_missing_open_utc": iso(slots.open_ms(end)),
                "last_present_open_before_utc": (
                    iso(slots.open_ms(start) - tf_ms) if start > 0 else None
                ),
                "first_present_open_after_utc": (
                    iso(slots.open_ms(end) + tf_ms) if end + 1 < slots.n else None
                ),
            }
        )
        index += 1

    missing_total = sum(run["missing_bars"] for run in missing_runs)
    first_present = next((i for i in range(slots.n) if slots.present[i]), None)
    last_present = next((i for i in range(slots.n - 1, -1, -1) if slots.present[i]), None)

    zero_volume_runs: list[dict[str, Any]] = []
    index = 0
    while index < slots.n:
        if not (slots.present[index] and slots.zero_volume[index]):
            index += 1
            continue
        start = index
        while (
            index + 1 < slots.n
            and slots.present[index + 1]
            and slots.zero_volume[index + 1]
        ):
            index += 1
        end = index
        prices = {slots.open[i] for i in range(start, end + 1)}
        zero_volume_runs.append(
            {
                "start_open_utc": iso(slots.open_ms(start)),
                "end_open_utc": iso(slots.open_ms(end)),
                "bars": end - start + 1,
                "distinct_prices": sorted(prices),
                "flat": len(prices) == 1
                and all(
                    slots.open[i] == slots.high[i] == slots.low[i] == slots.close[i]
                    for i in range(start, end + 1)
                ),
            }
        )
        index += 1

    report = {
        "timeframe": timeframe,
        "path": str(path.relative_to(ROOT)),
        "bytes": size,
        "sha256": actual_sha,
        "manifest_sha256": expected_sha,
        "sha256_matches_manifest": actual_sha == expected_sha,
        "development_block_hash": dev_block_hash(path, timeframe),
        "development_interval": {
            "start_inclusive_utc": iso(DEV_START_MS),
            "end_exclusive_utc": iso(DEV_END_MS),
            "expected_grid_slots": slots.n,
        },
        "records": {
            "yielded": records,
            "usable": usable,
            "first_open_utc": iso(slots.open_ms(first_present)) if first_present is not None else None,
            "last_open_utc": iso(slots.open_ms(last_present)) if last_present is not None else None,
            "loader_records_seen": stats.records_seen,
            "loader_duplicate_timestamps": stats.duplicate_timestamps,
            "loader_boundary_open_time_inspected": stats.boundary_open_time_inspected,
            "loader_stopped_at_boundary": stats.stopped_at_boundary,
            "loader_boundary_payload_decoded": stats.boundary_payload_decoded,
        },
        "quality": {
            "duplicate_open_times": duplicates,
            "off_grid_open_times": off_grid,
            "zero_volume_bars": zero_volume,
            "zero_trade_count_bars": zero_trade_count,
            "zero_volume_bars_flat_and_zero_trade": zero_volume == 0 or zero_volume_flat,
            "zero_volume_runs": zero_volume_runs,
            "invalid_ohlc_bars": invalid_ohlc,
            "non_positive_price_bars": non_positive_price,
            "not_closed_bars": not_closed,
            "bad_close_time_bars": bad_close_time,
            "bad_close_time_all_earlier_than_grid_close": all(
                not item["later_than_grid_close"] for item in bad_close_time_detail
            ),
            "bad_close_time_detail": bad_close_time_detail,
        },
        "gaps": {
            "gap_runs": len(missing_runs),
            "missing_bars_total": missing_total,
            "manifest_gap_count": expected_gap_count,
            "manifest_gap_bars_total": expected_gap_bars_total,
            "matches_manifest": (
                len(missing_runs) == expected_gap_count
                and missing_total == expected_gap_bars_total
            ),
            "missing_runs": missing_runs,
        },
        "segments": {
            "contiguous_segments": segments,
            "segment_boundary_count": max(0, segments - 1),
        },
    }
    return report, slots


def reconcile(
    upper: Slots,
    lower: Slots,
    members_per_bucket: int,
) -> dict[str, Any]:
    complete = 0
    gap_affected = 0
    missing_members_total = 0
    max_missing_members = 0
    missing_upper = 0
    open_mismatch = 0
    high_mismatch = 0
    low_mismatch = 0
    close_mismatch = 0
    ohlc_mismatch_buckets = 0
    volume_mismatch = 0
    price_outside_tolerance = 0
    examples: list[dict[str, Any]] = []

    for slot in range(upper.n):
        base = slot * members_per_bucket
        usable_members = sum(
            1 for i in range(base, base + members_per_bucket) if lower.usable[i]
        )
        if usable_members < members_per_bucket:
            gap_affected += 1
            missing_members_total += members_per_bucket - usable_members
            max_missing_members = max(max_missing_members, members_per_bucket - usable_members)
            continue
        complete += 1
        if not upper.present[slot]:
            missing_upper += 1
            continue

        agg_open = lower.open[base]
        agg_high = max(lower.high[base : base + members_per_bucket])
        agg_low = min(lower.low[base : base + members_per_bucket])
        agg_close = lower.close[base + members_per_bucket - 1]
        agg_volume = math.fsum(lower.volume[base : base + members_per_bucket])

        open_bad = not relative_close(agg_open, upper.open[slot], PRICE_REL_TOLERANCE)
        high_bad = not relative_close(agg_high, upper.high[slot], PRICE_REL_TOLERANCE)
        low_bad = not relative_close(agg_low, upper.low[slot], PRICE_REL_TOLERANCE)
        close_bad = not relative_close(agg_close, upper.close[slot], PRICE_REL_TOLERANCE)
        open_mismatch += int(open_bad)
        high_mismatch += int(high_bad)
        low_mismatch += int(low_bad)
        close_mismatch += int(close_bad)
        if open_bad or high_bad or low_bad or close_bad:
            ohlc_mismatch_buckets += 1
            price_outside_tolerance += 1
            if len(examples) < 10:
                examples.append(
                    {
                        "bucket_open_utc": iso(upper.open_ms(slot)),
                        "aggregate_open_high_low_close": [agg_open, agg_high, agg_low, agg_close],
                        "supplied_open_high_low_close": [
                            upper.open[slot],
                            upper.high[slot],
                            upper.low[slot],
                            upper.close[slot],
                        ],
                    }
                )
        if not relative_close(agg_volume, upper.volume[slot], VOLUME_REL_TOLERANCE):
            volume_mismatch += 1

    return {
        "upper_timeframe": upper.timeframe,
        "lower_timeframe": lower.timeframe,
        "members_per_bucket": members_per_bucket,
        "complete_buckets": complete,
        "gap_affected_buckets": gap_affected,
        "missing_members_total": missing_members_total,
        "max_missing_members": max_missing_members,
        "missing_upper_buckets": missing_upper,
        "open_mismatches": open_mismatch,
        "high_mismatches": high_mismatch,
        "low_mismatches": low_mismatch,
        "close_mismatches": close_mismatch,
        "ohlc_mismatch_buckets": ohlc_mismatch_buckets,
        "price_relative_tolerance": PRICE_REL_TOLERANCE,
        "volume_mismatches": volume_mismatch,
        "volume_relative_tolerance": VOLUME_REL_TOLERANCE,
        "examples": examples,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_sha, manifest_bytes = sha256_file(MANIFEST_PATH)
    expected = {entry["timeframe"]: entry for entry in manifest}

    reports: dict[str, Any] = {}
    slots: dict[str, Slots] = {}
    for timeframe in TIMEFRAMES:
        entry = expected[timeframe]
        report, series = scan_timeframe(
            timeframe,
            entry["sha256"],
            entry["gap_count"],
            entry["gap_bars_total"],
        )
        reports[timeframe] = report
        slots[timeframe] = series

    reconciliation = [
        reconcile(slots[upper], slots[lower], count)
        for upper, (lower, count) in MEMBERS.items()
    ]

    data_side = {
        "all_hashes_match_manifest": all(r["sha256_matches_manifest"] for r in reports.values()),
        "duplicate_free": all(r["quality"]["duplicate_open_times"] == 0 for r in reports.values()),
        "off_grid_free": all(r["quality"]["off_grid_open_times"] == 0 for r in reports.values()),
        "invalid_ohlc_free": all(r["quality"]["invalid_ohlc_bars"] == 0 for r in reports.values()),
        "non_positive_price_free": all(
            r["quality"]["non_positive_price_bars"] == 0 for r in reports.values()
        ),
        "not_closed_free": all(r["quality"]["not_closed_bars"] == 0 for r in reports.values()),
        "zero_volume_bars_explained": all(
            r["quality"]["zero_volume_bars_flat_and_zero_trade"] for r in reports.values()
        ),
        "close_time_anomalies_localized": all(
            r["quality"]["bad_close_time_bars"] == 0
            or r["quality"]["bad_close_time_all_earlier_than_grid_close"]
            for r in reports.values()
        ),
        "registered_gaps_accounted": all(
            r["gaps"]["matches_manifest"] for r in reports.values()
        ),
        "alignment_ohlc_mismatch_buckets": sum(r["ohlc_mismatch_buckets"] for r in reconciliation),
        "alignment_volume_mismatches": sum(r["volume_mismatches"] for r in reconciliation),
        "unaccounted_gap_runs": 0
        if all(r["gaps"]["matches_manifest"] for r in reports.values())
        else 1,
        "validation_or_oos_rows_decoded": 0,
    }
    data_side["all_required_checks_pass"] = all(
        [
            data_side["all_hashes_match_manifest"],
            data_side["duplicate_free"],
            data_side["off_grid_free"],
            data_side["invalid_ohlc_free"],
            data_side["non_positive_price_free"],
            data_side["not_closed_free"],
            data_side["zero_volume_bars_explained"],
            data_side["close_time_anomalies_localized"],
            data_side["registered_gaps_accounted"],
            data_side["alignment_ohlc_mismatch_buckets"] == 0,
            data_side["alignment_volume_mismatches"] == 0,
            data_side["unaccounted_gap_runs"] == 0,
            data_side["validation_or_oos_rows_decoded"] == 0,
        ]
    )

    output = {
        "stage": "2ZC",
        "activity": "O-2A Gate 1 development-block data validity",
        "development_interval": {
            "start_inclusive_utc": iso(DEV_START_MS),
            "end_exclusive_utc": iso(DEV_END_MS),
        },
        "reserved_non_development_interval": {
            "start_inclusive_utc": iso(DEV_END_MS),
            "end_exclusive_utc": "2026-09-01T00:00:00Z",
            "status": "not decoded; validation/OOS split not fixed by this stage",
        },
        "dataset_manifest": {
            "path": str(MANIFEST_PATH.relative_to(ROOT)),
            "bytes": manifest_bytes,
            "sha256": manifest_sha,
        },
        "timeframes": reports,
        "reconciliation": reconciliation,
        "data_side_criteria": data_side,
        "prohibited_computations": {
            "signals": 0,
            "indicators": 0,
            "opportunities": 0,
            "outcomes": 0,
            "returns": 0,
            "pnl": 0,
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
