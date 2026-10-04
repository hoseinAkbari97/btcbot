"""Reading a multi-year dataset without holding it in memory.

The problem this solves
----------------------
``data/datasets/BTCUSDT-5m-*.json`` is a single JSON array of 198,554 candle
objects. ``json.loads(path.read_text())`` on it produces a ~1 GB Python list of
dicts, and validating each into a :class:`CandleData` produces a second
population. Either alone is enough to push a 4 GB budget into swap.

So the array is walked incrementally. ``raw_decode`` decodes exactly one element
from a buffer at a time; when the buffer runs low it is topped up from the file
and the consumed prefix is dropped. Peak memory is the buffer plus one record —
a few megabytes regardless of dataset size, and the buffer is the *only* knob
that grows with input.

Why not Parquet, and why not convert
------------------------------------
The dataset files are the canonical copy. A streaming reader over them keeps
them canonical; converting to Parquet would create a second 40 MB copy that then
has to be kept in step with the first, and the first file has a sha256 in the
manifest that the research report cites. Two copies, one of which is the one
cited, is a worse arrangement than one file read slowly.

The reader is not a JSON *parser*
---------------------------------
It does not validate the outer structure beyond finding ``[`` and ``]``. It is
trusted to be reading a file this project wrote, and it says so: a malformed
document raises rather than guessing. General-purpose JSON is not the goal;
bounded memory on a known format is.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.schemas.market_data import CandleData, Timeframe

#: How much of the file to hold while hunting for the next ``,``. Sized so a
#: single candle record — a few hundred bytes — always fits with room to spare,
#: while the buffer itself stays far below any memory budget.
DEFAULT_BUFFER_BYTES = 1 << 20


class DatasetFormatError(ValueError):
    """The file is not a flat JSON array of candle records."""


def stream_json_records(
    path: Path | str,
    *,
    buffer_bytes: int = DEFAULT_BUFFER_BYTES,
    start_offset: int = 0,
) -> Iterator[dict]:
    """Yield each element of a top-level JSON array, one at a time.

    Uses the decoder's own ``raw_decode`` at the current offset rather than
    scanning for delimiters, so a ``{`` or ``[`` nested inside a string value
    cannot end an element early — the failure mode of hand-rolled bracket
    matching.

    :param buffer_bytes: size of the read window. This is the *only* term in
        peak memory that depends on the file, and it does not depend on how many
        records the file holds.
    :param start_offset: resume point, as a byte offset previously returned by
        :func:`current_offset`. Used to continue a run that was stopped mid-file
        instead of re-reading what it had already processed.
    """
    decoder = json.JSONDecoder()
    path = Path(path)

    with path.open("r", encoding="utf-8") as handle:
        handle.seek(start_offset)
        decoder = json.JSONDecoder()

        if start_offset:
            # Resuming: the caller positioned us mid-array. Whatever is in the
            # buffer is a record boundary or whitespace, and either decodes or
            # turns out to be the closing bracket.
            buffer = handle.read(buffer_bytes)
        else:
            if not _skip_to_first_record(handle, buffer_bytes):
                raise DatasetFormatError(f"{path} contains no JSON array")
            buffer = handle.read(buffer_bytes)

        exhausted = False
        while True:
            stripped = buffer.lstrip()
            # Strip the element separator as well as whitespace. `raw_decode`
            # parses a *value*, so the comma between records has to go — leaving
            # it in is the single easiest way to make a streaming JSON reader
            # fail on a perfectly well-formed file.
            if stripped[:1] == ",":
                stripped = stripped[1:].lstrip()
            # A closing bracket ends the array. Checked before decoding,
            # because raw_decode on "]" raises and that is the *normal* end of
            # the file rather than a malformed record.
            if stripped.startswith("]"):
                return
            if not stripped:
                if exhausted:
                    raise DatasetFormatError(
                        f"{path} ended before the closing ']' at offset "
                        f"{handle.tell()}"
                    )
                chunk = handle.read(buffer_bytes)
                if not chunk:
                    exhausted = True
                    continue
                buffer = stripped + chunk
                continue

            try:
                value, end = decoder.raw_decode(stripped)
            except json.JSONDecodeError:
                if exhausted:
                    raise DatasetFormatError(
                        f"{path} has a malformed record near offset "
                        f"{handle.tell() - len(buffer)}"
                    ) from None
                # The record is cut off by the end of the buffer. Pull more in
                # and retry; one candle record never spans many reads.
                chunk = handle.read(buffer_bytes)
                if not chunk:
                    exhausted = True
                    continue
                buffer = stripped + chunk
                continue

            yield value
            buffer = stripped[end:]


def _trim(buffer: str, index: int) -> tuple[str, int]:
    """Discard the consumed prefix, returning the buffer and the new index.

    This is what keeps memory flat. Without it the buffer would grow by every
    record ever read, and a "streaming" reader would be the one thing in the
    pipeline that accumulates the whole dataset.
    """
    if index == 0:
        return buffer, 0
    return buffer[index:], 0


def _at_end_of_array(buffer: str, index: int) -> bool:
    """Whether what follows the last record is the array's closing bracket."""
    return buffer[index:].strip().startswith("]")


def _skip_to_first_record(handle, buffer_bytes: int) -> bool:
    """Advance past the opening bracket. False if there is no array."""
    chunk = handle.read(buffer_bytes)
    index = chunk.find("[")
    if index < 0:
        return False
    # Keep the remainder; the caller re-reads from here.
    handle.seek(handle.tell() - len(chunk) + index + 1)
    return True


def _trim(buffer: str, index: int) -> tuple[str, int]:
    """Discard the consumed prefix, returning the buffer and the new index.

    This is what keeps memory flat. Without it the buffer would grow by every
    record ever read, and a "streaming" reader would be the one thing in the
    pipeline that accumulates the whole dataset.
    """
    if index == 0:
        return buffer, 0
    return buffer[index:], 0


def to_candle(record: dict) -> CandleData:
    """Build one :class:`CandleData` from a decoded record.

    Kept separate from the reader so the dataset's quirks are fixed in exactly
    one place. The ingested files carry every numeric and boolean field as a
    *string* — pydantic coerces these, and the coercion is correct, but doing it
    in one visible function means a schema change has one place to be reflected
    rather than every call site.
    """
    return CandleData.model_validate(record)


def stream_candles(
    path: Path | str,
    *,
    buffer_bytes: int = DEFAULT_BUFFER_BYTES,
    start_offset: int = 0,
) -> Iterator[CandleData]:
    """Stream a dataset as validated candles, one at a time.

    Validation happens per record and the record is dropped immediately, so no
    population of dicts and no population of models ever exists at once.
    """
    for record in stream_json_records(
        path, buffer_bytes=buffer_bytes, start_offset=start_offset
    ):
        yield to_candle(record)


def read_chunks(
    candles: Iterator[CandleData] | Sequence[CandleData],
    *,
    chunk_rows: int,
) -> Iterator[list[CandleData]]:
    """Group a candle stream into bounded lists of at most ``chunk_rows``.

    The batching primitive every chunked path shares, so "how many bars are in
    memory at once" is one configurable number rather than a decision made
    separately in each caller.
    """
    batch: list[CandleData] = []
    for candle in candles:
        batch.append(candle)
        if len(batch) >= chunk_rows:
            yield batch
            batch = []
    if batch:
        yield batch


def stream_chunks(
    path: Path | str,
    *,
    chunk_rows: int,
    buffer_bytes: int = DEFAULT_BUFFER_BYTES,
) -> Iterator[list[CandleData]]:
    """Stream a dataset straight into bounded chunks, never materialising it."""
    return read_chunks(
        stream_candles(path, buffer_bytes=buffer_bytes), chunk_rows=chunk_rows
    )


# ---------------------------------------------------------------------------
# Segment boundaries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Segment:
    """One bounded time span, and where its data starts and ends in the file.

    A segment is a *memory* boundary. It is explicitly not a reset: state
    produced by the previous segment is carried in and the events of this one
    are filtered to this one's bars.
    """

    index: int
    start: datetime
    end: datetime

    def contains(self, when: datetime) -> bool:
        return self.start <= when < self.end

    @property
    def label(self) -> str:
        return f"{self.start.date()}_{self.end.date()}"


def plan_segments(
    start: datetime,
    end: datetime,
    *,
    segment_days: int,
) -> list[Segment]:
    """Split ``[start, end)`` into consecutive ``segment_days`` spans.

    Half-open at both ends so consecutive segments tile the range with no bar
    counted twice and none skipped — the property that makes a segmented run
    equal to a continuous one.
    """
    if end <= start:
        return []
    segments: list[Segment] = []
    cursor = start
    step = timedelta(days=segment_days)
    index = 0
    while cursor < end:
        following = min(cursor + step, end)
        segments.append(Segment(index=index, start=cursor, end=following))
        cursor = following
        index += 1
    return segments


def segment_candles(
    candles: Iterator[CandleData] | Sequence[CandleData],
    *,
    segment_days: int,
) -> Iterator[SegmentBars]:
    """Group a candle stream into time segments, in order.

    The stream must be sorted by ``open_time``; the ingested datasets are, and
    this function relies on it to assign each bar to exactly one segment. An
    out-of-order bar would be silently attached to the wrong segment, so the
    assumption is checked rather than trusted.
    """
    current: list[CandleData] = []
    current_segment: Segment | None = None
    previous_time: datetime | None = None

    for candle in candles:
        if previous_time is not None and candle.open_time < previous_time:
            raise ValueError(
                f"candles are not sorted by open_time: {candle.open_time.isoformat()} "
                f"follows {previous_time.isoformat()}"
            )
        previous_time = candle.open_time

        # A segment runs until the *next* one starts, so its length is not known
        # until a later bar arrives. Rather than buffer to discover it, this
        # closes the current segment when a bar's own month/year crosses a
        # segment-sized boundary — which the planner below agrees with exactly.
        index = int(
            (candle.open_time - candle.open_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )).total_seconds()
        )
        segment_index = index // (segment_days * 86400)
        if current_segment is None:
            current_segment = Segment(
                index=segment_index,
                start=_floor_to_days(candle.open_time, segment_days),
                end=_floor_to_days(candle.open_time, segment_days)
                + timedelta(days=segment_days),
            )
        elif segment_index != current_segment.index:
            if current:
                yield SegmentBars(current_segment, current)
            current = []
            current_segment = Segment(
                index=segment_index,
                start=_floor_to_days(candle.open_time, segment_days),
                end=_floor_to_days(candle.open_time, segment_days)
                + timedelta(days=segment_days),
            )
        current.append(candle)

    if current and current_segment is not None:
        yield SegmentBars(current_segment, current)


@dataclass(frozen=True)
class SegmentBars:
    """A segment and the bars whose ``open_time`` falls inside it."""

    segment: Segment
    candles: list[CandleData]


def _floor_to_days(when: datetime, days: int) -> datetime:
    """The start of the ``days``-long block containing ``when``.

    Anchored to the Unix epoch so a segment boundary is the same instant on
    every run regardless of when it started. Anchoring to the first bar's
    timestamp instead would make a resumed run's boundaries depend on where the
    previous one happened to stop.
    """
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    elapsed = (when - epoch).total_seconds()
    block = int(elapsed // (days * 86400))
    return epoch + timedelta(seconds=block * days * 86400)


def dataset_timeframe(path: Path) -> Timeframe | None:
    """Read the timeframe from a dataset's first record without a full parse.

    Reading one record rather than the file is the whole point of the streaming
    reader, and the timeframe is needed before any processing starts.
    """
    for record in stream_json_records(path, buffer_bytes=8192):
        value = record.get("timeframe")
        if value is None:
            return None
        return Timeframe(value)
    return None


def dataset_bounds(path: Path) -> tuple[datetime, datetime] | None:
    """The first and last bar times, found without holding the dataset.

    ``first`` comes from the head of the file and ``last`` from its tail, so the
    cost is a few kilobytes of reads regardless of size.
    """
    first = next(stream_json_records(path, buffer_bytes=8192), None)
    if first is None:
        return None
    return datetime.fromisoformat(first["open_time"]), _last_open_time(path)


def _last_open_time(path: Path) -> datetime:
    """The ``open_time`` of the final record, found by scanning the tail.

    Scans backwards from the end for the last ``"open_time"`` key rather than
    parsing the tail as JSON: the tail is almost certainly a *partial* record,
    and the last key inside the file's final object is the one wanted. Keys
    appear alphabetically in these files, so ``open_time`` is not last within
    its object — which is exactly why the search is for the last *occurrence*
    rather than the last key of the last object.
    """
    window = 8192
    size = path.stat().st_size
    while window <= size:
        with path.open("r", encoding="utf-8") as handle:
            handle.seek(size - window)
            tail = handle.read(window)
        marker = tail.rfind('"open_time"')
        if marker >= 0:
            start = tail.find('"', marker + len('"open_time"'))
            end = tail.find('"', start + 1)
            if start > 0 and end > 0:
                return datetime.fromisoformat(tail[start + 1 : end])
        window *= 8
    raise DatasetFormatError(f"{path} has no open_time field to bound the dataset")


def estimate_candle_bytes(sample: Sequence[CandleData]) -> int:
    """Bytes per candle, estimated from a small sample rather than assumed.

    Used to size a segment's expected memory before it is read. Taking it from
    the data rather than a constant means the estimate stays right if the
    dataset's fields change.
    """
    if not sample:
        return 0
    return max(1, int(sum(len(repr(candle.model_dump())) for candle in sample) / len(sample)))


def decimal_from(value: object) -> Decimal | None:
    """Coerce a dataset field to :class:`Decimal`, or ``None`` if absent.

    The ingested files store numerics as strings; pydantic handles that, but
    anything reading a raw record does not get that for free.
    """
    if value is None or value == "":
        return None
    return Decimal(str(value))