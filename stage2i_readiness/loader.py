"""Bounded-memory JSON-array loader for the frozen development datasets.

Design rules (Stage 2I):
- the file is never passed to ``json.load``;
- at most one raw JSON object is held at a time;
- at most one typed :class:`Candle` is yielded at a time;
- the development interval is half-open ``[dev_start_ms, dev_end_ms)``;
- once the first record at/after ``dev_end_ms`` is seen, only its
  ``open_time`` string is inspected, its payload is never decoded, and the
  stream stops;
- duplicate ``open_time`` values keep the first record in file order.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

CHUNK_SIZE = 1 << 20  # 1 MiB
DEV_START_MS = 1_609_459_200_000  # 2021-01-01T00:00:00Z, inclusive
DEV_END_MS = 1_719_792_000_000  # 2024-07-01T00:00:00Z, exclusive

TIMEFRAME_MS = {
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
}

_OPEN_TIME_RE = re.compile(r'"open_time"\s*:\s*"([^"]+)"')
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class SchemaError(ValueError):
    """A record cannot be coerced under the frozen data contract."""


class IntervalViolation(RuntimeError):
    """Records are not in the required chronological order."""


def epoch_ms(value: str) -> int:
    """Parse an ISO-8601 string to integer UTC epoch milliseconds."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SchemaError(f"invalid timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        raise SchemaError(f"timestamp has no UTC offset: {value!r}")
    delta = parsed.astimezone(UTC) - _EPOCH
    return delta.days * 86_400_000 + delta.seconds * 1_000 + delta.microseconds // 1_000


def strict_is_closed(record: dict[str, object]) -> bool:
    """Require an explicit, unambiguous completeness flag.

    The production ``CandleData`` model defaults a missing or null field to
    ``True``. The runner deliberately does not use that default: only a JSON
    boolean or the dataset's exact ``"True"``/``"False"`` strings are accepted.
    """
    if "is_closed" not in record:
        raise SchemaError("missing is_closed")
    value = record["is_closed"]
    if isinstance(value, bool):
        return value
    if value in ("True", "False"):
        return value == "True"
    raise SchemaError(f"malformed is_closed: {value!r}")


def _decimal(record: dict[str, object], key: str) -> Decimal:
    if key not in record:
        raise SchemaError(f"missing {key}")
    value = record[key]
    if isinstance(value, bool) or value is None:
        raise SchemaError(f"malformed {key}: {value!r}")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SchemaError(f"malformed {key}: {value!r}") from exc


def _integer(record: dict[str, object], key: str) -> int:
    if key not in record:
        raise SchemaError(f"missing {key}")
    value = record[key]
    if isinstance(value, bool) or value is None:
        raise SchemaError(f"malformed {key}: {value!r}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SchemaError(f"malformed {key}: {value!r}") from exc
    if number != number.to_integral_value():
        raise SchemaError(f"non-integer {key}: {value!r}")
    return int(number)


@dataclass(frozen=True, slots=True)
class Candle:
    """One validated record. Only the current candle is retained."""

    timeframe: str
    open_time: datetime
    close_time: datetime
    open_time_ms: int
    close_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int
    is_closed: bool
    ohlc_valid: bool


def candle_from_record(record: dict[str, object], timeframe: str) -> Candle:
    """Coerce one record, rejecting missing or ambiguous contract fields."""
    if record.get("timeframe") != timeframe:
        raise SchemaError(f"timeframe mismatch: {record.get('timeframe')!r}")
    if record.get("symbol") != "BTCUSDT":
        raise SchemaError(f"symbol mismatch: {record.get('symbol')!r}")
    open_time_raw = record.get("open_time")
    close_time_raw = record.get("close_time")
    if not isinstance(open_time_raw, str) or not isinstance(close_time_raw, str):
        raise SchemaError("open_time and close_time must be strings")
    open_time = datetime.fromisoformat(open_time_raw)
    close_time = datetime.fromisoformat(close_time_raw)
    if open_time.tzinfo is None or close_time.tzinfo is None:
        raise SchemaError("timestamps must carry a UTC offset")
    open_ms = epoch_ms(open_time_raw)
    close_ms = epoch_ms(close_time_raw)
    if close_ms <= open_ms:
        raise SchemaError("close_time must be after open_time")
    open_price = _decimal(record, "open")
    high = _decimal(record, "high")
    low = _decimal(record, "low")
    close = _decimal(record, "close")
    volume = _decimal(record, "volume")
    trade_count = _integer(record, "trade_count")
    ohlc_valid = high >= low and high >= max(open_price, close) and low <= min(open_price, close)
    return Candle(
        timeframe=timeframe,
        open_time=open_time.astimezone(UTC),
        close_time=close_time.astimezone(UTC),
        open_time_ms=open_ms,
        close_time_ms=close_ms,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
        trade_count=trade_count,
        is_closed=strict_is_closed(record),
        ohlc_valid=ohlc_valid,
    )


@dataclass
class LoadStats:
    """Mutable accounting for one bounded-memory pass."""

    records_seen: int = 0
    records_yielded: int = 0
    records_before_interval: int = 0
    duplicate_timestamps: int = 0
    boundary_open_time_inspected: int = 0
    stopped_at_boundary: bool = False
    boundary_payload_decoded: int = 0
    max_object_chars: int = 0
    max_buffer_chars: int = 0
    first_open_time_ms: int | None = None
    last_open_time_ms: int | None = None
    extra: dict[str, int] = field(default_factory=dict)


def _find_object_end(text: str, start: int) -> int | None:
    """Return the index of the brace closing the object at ``start``."""
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def iter_object_texts(path: str | Path, chunk_size: int = CHUNK_SIZE) -> Iterator[str]:
    """Yield one raw JSON object at a time from a top-level JSON array."""
    with Path(path).open("r", encoding="utf-8") as handle:
        buffer = ""
        position = 0
        eof = False

        def refill(keep_from: int = 0) -> bool:
            nonlocal buffer, position, eof
            more = handle.read(chunk_size)
            if not more:
                eof = True
                return False
            buffer = buffer[keep_from:] + more
            position = 0
            return True

        # Find the opening bracket.
        while True:
            if position >= len(buffer):
                if not refill(keep_from=position):
                    raise SchemaError("no JSON array found")
                continue
            char = buffer[position]
            if char.isspace():
                position += 1
                continue
            if char != "[":
                raise SchemaError("dataset is not a JSON array")
            position += 1
            break

        while True:
            # Skip whitespace and the separator comma.
            while True:
                if position >= len(buffer):
                    if not refill(keep_from=position):
                        return
                    continue
                char = buffer[position]
                if char.isspace() or char == ",":
                    position += 1
                    continue
                break  # type: ignore[possibly-undefined]
            if char == "]":
                return
            if char != "{":
                raise SchemaError("expected a JSON object in the array")

            start = position
            end = _find_object_end(buffer, start)
            while end is None:
                if not refill(keep_from=start):
                    raise SchemaError("unterminated JSON object")
                start = 0
                end = _find_object_end(buffer, start)
            yield buffer[start : end + 1]
            position = end + 1
            if position > chunk_size:
                buffer = buffer[position:]
                position = 0


def iter_candles(
    path: str | Path,
    timeframe: str,
    *,
    dev_start_ms: int = DEV_START_MS,
    dev_end_ms: int = DEV_END_MS,
    chunk_size: int = CHUNK_SIZE,
    stats: LoadStats | None = None,
) -> Iterator[Candle]:
    """Yield development-interval candles, one at a time.

    The first record at or after ``dev_end_ms`` terminates the pass. Only its
    ``open_time`` string is read; its payload is never decoded or exposed.
    """
    if timeframe not in TIMEFRAME_MS:
        raise ValueError(f"unknown timeframe {timeframe!r}")
    stats = stats if stats is not None else LoadStats()
    last_ms: int | None = None

    for text in iter_object_texts(path, chunk_size=chunk_size):
        stats.records_seen += 1
        stats.max_object_chars = max(stats.max_object_chars, len(text))
        stats.max_buffer_chars = max(stats.max_buffer_chars, len(text))
        match = _OPEN_TIME_RE.search(text)
        if match is None:
            # Decode only to produce a precise schema error.
            stats.boundary_payload_decoded += 1
            raise SchemaError("record has no open_time")
        open_ms = epoch_ms(match.group(1))
        if open_ms < dev_start_ms:
            stats.records_before_interval += 1
            continue
        if open_ms >= dev_end_ms:
            stats.boundary_open_time_inspected += 1
            stats.stopped_at_boundary = True
            return

        record = json.loads(text)
        candle = candle_from_record(record, timeframe)
        if candle.open_time_ms != open_ms:
            raise SchemaError("open_time changed after decoding")
        if last_ms is not None:
            if candle.open_time_ms < last_ms:
                raise IntervalViolation("records are not chronologically ordered")
            if candle.open_time_ms == last_ms:
                stats.duplicate_timestamps += 1
                continue
        if stats.first_open_time_ms is None:
            stats.first_open_time_ms = candle.open_time_ms
        stats.last_open_time_ms = candle.open_time_ms
        stats.records_yielded += 1
        last_ms = candle.open_time_ms
        yield candle


def hash_file(path: str | Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Stream a file through SHA256 without parsing it."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def bucket_counts(
    path: str | Path,
    timeframe: str,
    bucket_ms: int,
    *,
    dev_start_ms: int = DEV_START_MS,
    dev_end_ms: int = DEV_END_MS,
    chunk_size: int = CHUNK_SIZE,
    stats: LoadStats | None = None,
) -> Iterator[tuple[int, int]]:
    """Count lower-timeframe records per bucket, retaining one bucket only."""
    current: int | None = None
    count = 0
    for candle in iter_candles(
        path,
        timeframe,
        dev_start_ms=dev_start_ms,
        dev_end_ms=dev_end_ms,
        chunk_size=chunk_size,
        stats=stats,
    ):
        bucket = candle.open_time_ms - (candle.open_time_ms % bucket_ms)
        if bucket != current:
            if current is not None:
                yield current, count
            current = bucket
            count = 0
        count += 1
    if current is not None:
        yield current, count


@dataclass
class AlignmentStats:
    upper_buckets: int = 0
    complete_buckets: int = 0
    gap_affected_buckets: int = 0
    missing_members_total: int = 0
    lower_buckets_without_upper: int = 0
    max_missing_members: int = 0


def compare_membership(
    lower_path: str | Path,
    lower_timeframe: str,
    upper_path: str | Path,
    upper_timeframe: str,
    expected_members: int,
    *,
    dev_start_ms: int = DEV_START_MS,
    dev_end_ms: int = DEV_END_MS,
    chunk_size: int = CHUNK_SIZE,
) -> AlignmentStats:
    """Stream both files and compare bucket membership without materialising either."""
    result = AlignmentStats()
    upper_ms = TIMEFRAME_MS[upper_timeframe]
    lower_counts = bucket_counts(
        lower_path,
        lower_timeframe,
        upper_ms,
        dev_start_ms=dev_start_ms,
        dev_end_ms=dev_end_ms,
        chunk_size=chunk_size,
    )
    uppers = iter_candles(
        upper_path,
        upper_timeframe,
        dev_start_ms=dev_start_ms,
        dev_end_ms=dev_end_ms,
        chunk_size=chunk_size,
    )
    next_lower = next(lower_counts, None)
    for upper in uppers:
        upper_bucket = upper.open_time_ms - (upper.open_time_ms % upper_ms)
        count = 0
        while next_lower is not None and next_lower[0] <= upper_bucket:
            if next_lower[0] == upper_bucket:
                count = next_lower[1]
            else:
                result.lower_buckets_without_upper += 1
            next_lower = next(lower_counts, None)
        result.upper_buckets += 1
        missing = max(expected_members - count, 0)
        if missing == 0:
            result.complete_buckets += 1
        else:
            result.gap_affected_buckets += 1
            result.missing_members_total += missing
            result.max_missing_members = max(result.max_missing_members, missing)
    while next_lower is not None:
        result.lower_buckets_without_upper += 1
        next_lower = next(lower_counts, None)
    return result
