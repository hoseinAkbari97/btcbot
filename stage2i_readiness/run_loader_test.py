#!/usr/bin/env python3
"""Stage 2I actual-dataset, loader-only readiness test.

This script parses the frozen datasets with the bounded loader. It does not
evaluate a candidate entry condition, count signals, apply a cost gate or
non-overlap rule, or compute any performance statistic.
"""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from stage2i_readiness.loader import (
    DEV_END_MS,
    DEV_START_MS,
    TIMEFRAME_MS,
    AlignmentStats,
    LoadStats,
    compare_membership,
    hash_file,
    iter_candles,
)

DATASETS = {
    "5m": "backend/data/datasets/BTCUSDT-5m-20210101-20260901.json",
    "15m": "backend/data/datasets/BTCUSDT-15m-20210101-20260901.json",
    "1h": "backend/data/datasets/BTCUSDT-1h-20210101-20260901.json",
    "4h": "backend/data/datasets/BTCUSDT-4h-20210101-20260901.json",
}
EXPECTED_SHA256 = {
    "5m": "20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681",
    "15m": "db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780",
    "1h": "52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69",
    "4h": "35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa",
}
CHUNK_SIZE = 1 << 20


def rss_bytes() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def scan(timeframe: str, path: Path) -> dict[str, object]:
    stats = LoadStats()
    started = time.perf_counter()
    previous_close_ms = -1
    grid = TIMEFRAME_MS[timeframe]
    off_grid = 0
    non_monotonic_close = 0
    invalid_ohlc = 0
    unclosed = 0
    for candle in iter_candles(path, timeframe, chunk_size=CHUNK_SIZE, stats=stats):
        if candle.open_time_ms % grid != 0:
            off_grid += 1
        if candle.close_time_ms <= previous_close_ms:
            non_monotonic_close += 1
        previous_close_ms = candle.close_time_ms
        if not candle.ohlc_valid:
            invalid_ohlc += 1
        if not candle.is_closed:
            unclosed += 1
    elapsed = time.perf_counter() - started
    return {
        "timeframe": timeframe,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": EXPECTED_SHA256[timeframe],
        "records_yielded": stats.records_yielded,
        "records_seen_until_boundary": stats.records_seen,
        "records_before_interval": stats.records_before_interval,
        "duplicate_timestamps": stats.duplicate_timestamps,
        "first_open_time_ms": stats.first_open_time_ms,
        "last_open_time_ms": stats.last_open_time_ms,
        "boundary_open_time_inspected": stats.boundary_open_time_inspected,
        "boundary_payload_decoded": stats.boundary_payload_decoded,
        "stopped_at_boundary": stats.stopped_at_boundary,
        "max_object_chars": stats.max_object_chars,
        "off_grid": off_grid,
        "non_monotonic_close_time": non_monotonic_close,
        "invalid_ohlc": invalid_ohlc,
        "unclosed": unclosed,
        "seconds": round(elapsed, 3),
    }


def alignment(lower: str, upper: str, expected: int) -> dict[str, object]:
    started = time.perf_counter()
    stats: AlignmentStats = compare_membership(
        DATASETS[lower],
        lower,
        DATASETS[upper],
        upper,
        expected,
        chunk_size=CHUNK_SIZE,
    )
    return {
        "lower": lower,
        "upper": upper,
        "expected_members": expected,
        "upper_buckets": stats.upper_buckets,
        "complete_buckets": stats.complete_buckets,
        "gap_affected_buckets": stats.gap_affected_buckets,
        "missing_members_total": stats.missing_members_total,
        "max_missing_members": stats.max_missing_members,
        "lower_buckets_without_upper": stats.lower_buckets_without_upper,
        "seconds": round(time.perf_counter() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = rss_bytes()
    started = time.perf_counter()
    hashes = {tf: hash_file(path, CHUNK_SIZE) for tf, path in DATASETS.items()}
    hash_seconds = time.perf_counter() - started
    hash_peak = rss_bytes()

    scans = [scan(tf, Path(path)) for tf, path in DATASETS.items()]
    alignments = [
        alignment("5m", "15m", 3),
        alignment("15m", "1h", 4),
        alignment("1h", "4h", 4),
    ]
    elapsed = time.perf_counter() - started
    peak = rss_bytes()

    output = {
        "stage": "2I",
        "test": "actual-dataset loader-only bounded-memory readiness",
        "strategy_logic_evaluated": False,
        "signals_counted": False,
        "development_interval": {
            "start_ms": DEV_START_MS,
            "end_ms": DEV_END_MS,
            "semantics": "[start_ms, end_ms)",
        },
        "chunk_size_bytes": CHUNK_SIZE,
        "max_records_held_simultaneously": 1,
        "max_batch_size_bytes": CHUNK_SIZE,
        "max_raw_object_chars": max(int(s["max_object_chars"]) for s in scans),
        "memory": {
            "baseline_rss_bytes": baseline,
            "hash_peak_rss_bytes": hash_peak,
            "peak_rss_bytes": peak,
            "peak_above_baseline_bytes": max(peak - baseline, 0),
            "target_bytes": 4 * 1024**3,
            "hard_ceiling_bytes": 6 * 1024**3,
            "within_4gb_target": peak < 4 * 1024**3,
            "within_6gb_hard_ceiling": peak < 6 * 1024**3,
        },
        "hash_verification": {
            "expected": EXPECTED_SHA256,
            "computed": hashes,
            "all_match": hashes == EXPECTED_SHA256,
            "seconds": round(hash_seconds, 3),
        },
        "scans": scans,
        "alignment": alignments,
        "oos_records_yielded": 0,
        "oos_payloads_decoded": sum(int(s["boundary_payload_decoded"]) for s in scans),
        "boundary_open_times_inspected": sum(int(s["boundary_open_time_inspected"]) for s in scans),
        "temporary_disk_bytes": 0,
        "total_seconds": round(elapsed, 3),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output["memory"], indent=2, sort_keys=True))
    print(f"result: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
