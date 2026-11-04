"""Stage 2I bounded-loader contract tests on small synthetic arrays."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from stage2i_readiness.loader import (
    DEV_END_MS,
    DEV_START_MS,
    IntervalViolation,
    LoadStats,
    SchemaError,
    hash_file,
    iter_candles,
)


def row(open_time: str, close_time: str, *, closed: object = "True") -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "open_time": open_time,
        "close_time": close_time,
        "open": "100",
        "high": "101",
        "low": "99",
        "close": "100.5",
        "volume": "1",
        "trade_count": "1",
        "is_closed": closed,
    }


def write_array(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def test_loader_is_bounded_and_stops_before_oos_payload(tmp_path: Path) -> None:
    rows = [
        row("2021-01-01 00:00:00+00:00", "2021-01-01 00:14:59.999+00:00"),
        row("2021-01-01 00:15:00+00:00", "2021-01-01 00:29:59.999+00:00"),
        row("2024-07-01 00:00:00+00:00", "2024-07-01 00:14:59.999+00:00"),
        row("2024-07-01 00:15:00+00:00", "2024-07-01 00:29:59.999+00:00"),
    ]
    path = write_array(tmp_path / "set.json", rows)
    stats = LoadStats()
    candles = list(iter_candles(path, "15m", chunk_size=64, stats=stats))
    assert [c.open_time_ms for c in candles] == [DEV_START_MS, DEV_START_MS + 900_000]
    assert stats.stopped_at_boundary is True
    assert stats.boundary_open_time_inspected == 1
    assert stats.boundary_payload_decoded == 0
    assert all(c.open_time_ms < DEV_END_MS for c in candles)


def test_loader_keeps_first_duplicate(tmp_path: Path) -> None:
    rows = [
        row("2021-01-01 00:00:00+00:00", "2021-01-01 00:14:59.999+00:00"),
        row("2021-01-01 00:00:00+00:00", "2021-01-01 00:14:59.999+00:00", closed="False"),
    ]
    path = write_array(tmp_path / "set.json", rows)
    stats = LoadStats()
    candles = list(iter_candles(path, "15m", stats=stats))
    assert len(candles) == 1
    assert candles[0].is_closed is True
    assert stats.duplicate_timestamps == 1


def test_loader_rejects_unordered_records(tmp_path: Path) -> None:
    rows = [
        row("2021-01-01 00:15:00+00:00", "2021-01-01 00:29:59.999+00:00"),
        row("2021-01-01 00:00:00+00:00", "2021-01-01 00:14:59.999+00:00"),
    ]
    path = write_array(tmp_path / "set.json", rows)
    with pytest.raises(IntervalViolation):
        list(iter_candles(path, "15m"))


def test_loader_rejects_missing_is_closed(tmp_path: Path) -> None:
    record = row("2021-01-01 00:00:00+00:00", "2021-01-01 00:14:59.999+00:00")
    del record["is_closed"]
    path = write_array(tmp_path / "set.json", [record])
    with pytest.raises(SchemaError, match="is_closed"):
        list(iter_candles(path, "15m"))


def test_hash_is_streamed_and_reproducible(tmp_path: Path) -> None:
    path = write_array(tmp_path / "set.json", [])
    first = hash_file(path, chunk_size=7)
    second = hash_file(path, chunk_size=3)
    assert first == second
    assert len(first) == 64
