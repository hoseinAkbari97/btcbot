"""The streaming reader must produce what a full parse produces.

A streaming reader is only worth having if it is *equivalent*. If it drops the
last bar, mis-frames a record spanning a buffer boundary, or drops one every
time a value happens to contain a bracket, it produces a quietly different
dataset — and the difference shows up as a slightly different research result
rather than as an error, which is the worst possible place for it to show up.

So most of these tests are equivalence assertions against ``json.load``, run at a
buffer size small enough to force records across every boundary they can hit.
The memory tests are structural: the shape of the call, not a measurement of the
process, because measuring real memory here would mean the crash §29 forbids.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.market_data import CandleData
from app.services.research.streaming import (
    DatasetFormatError,
    plan_segments,
    read_chunks,
    segment_candles,
    stream_candles,
    stream_chunks,
    stream_json_records,
)

#: Deliberately tiny. Every record is ~200 bytes, so a 128-byte window forces
#: the reader to refill mid-record on essentially every element -- which is the
#: condition under which a streaming reader breaks.
TINY_BUFFER = 128
BASE = datetime(2021, 1, 1, tzinfo=UTC)


def record(index: int) -> dict:
    """One candle in the shape the ingested datasets carry: strings, not numbers."""
    when = BASE + timedelta(minutes=5 * index)
    return {
        "symbol": "BTCUSDT",
        "timeframe": "5m",
        "open_time": when.isoformat(),
        "close_time": (when + timedelta(minutes=5)).isoformat(),
        "open": str(40000 + index),
        "high": str(41000 + index),
        "low": str(39000 + index),
        "close": str(40500 + index),
        "volume": "12.5",
        "quote_volume": "500000.0",
        "trade_count": 1000,
        "is_closed": True,
    }


def write_dataset(tmp_path, n: int) -> str:
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([record(i) for i in range(n)]), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Equivalence with a full parse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("buffer_bytes", [TINY_BUFFER, 4096, 1 << 20])
def test_the_stream_matches_a_full_parse_exactly(tmp_path, buffer_bytes) -> None:
    """The whole contract: same candles, same order, same Decimals.

    Checked at three buffer sizes, the smallest of which is smaller than a
    single record. Equality is on the models themselves rather than on a
    digest, so a mismatch reports which field differs.
    """
    path = write_dataset(tmp_path, 40)
    expected = [CandleData.model_validate(r) for r in json.loads(open(path).read())]

    assert list(stream_candles(path, buffer_bytes=buffer_bytes)) == expected


def test_the_buffer_size_does_not_change_the_result(tmp_path) -> None:
    """A memory knob must never be a parameter of the analysis.

    If a different buffer size produced different candles, then lowering it to
    fit the machine's RAM would silently change the dataset — the exact failure
    every other batching knob in this project was written to avoid.
    """
    path = write_dataset(tmp_path, 60)

    assert list(stream_candles(path, buffer_bytes=TINY_BUFFER)) == list(
        stream_candles(path, buffer_bytes=1 << 22)
    )


def test_a_record_containing_brackets_does_not_end_the_element_early(tmp_path) -> None:
    """The reason the reader uses ``raw_decode`` rather than bracket matching.

    Hand-rolled scanning for ``{`` and ``}`` breaks the moment a string value
    contains one. A symbol like ``BTC/USDT`` is not exotic, and a note field
    holding a JSON fragment would be worse.
    """
    path = tmp_path / "bracketish.json"
    records = [record(0), record(1)]
    records[0]["note"] = "close {not a brace}, [nor this]"
    records[1]["note"] = "}}"
    path.write_text(json.dumps(records), encoding="utf-8")

    streamed = list(stream_json_records(str(path), buffer_bytes=TINY_BUFFER))

    assert len(streamed) == 2
    assert streamed[0]["note"] == "close {not a brace}, [nor this]"


def test_pretty_printed_json_still_streams(tmp_path) -> None:
    """Whitespace between elements is not an element.

    The ingested files are compact, but a dataset written by anything else is
    not, and a reader that only handles one formatting is a reader that fails on
    data it was given.
    """
    path = tmp_path / "pretty.json"
    path.write_text(json.dumps([record(i) for i in range(5)], indent=2), encoding="utf-8")

    assert len(list(stream_json_records(str(path), buffer_bytes=TINY_BUFFER))) == 5


def test_an_empty_array_yields_nothing(tmp_path) -> None:
    """A quiet period is a normal outcome, not a failure."""
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")

    assert list(stream_candles(str(path))) == []


def test_string_valued_numbers_are_coerced_exactly_once(tmp_path) -> None:
    """Decimal, not float.

    The datasets carry every price as a string precisely so no binary rounding
    is introduced on ingest. Re-reading them through the streaming path must not
    lose that.
    """
    path = write_dataset(tmp_path, 1)
    candle = next(stream_candles(path))

    assert isinstance(candle.open, Decimal)
    assert candle.open == Decimal("40000")


# ---------------------------------------------------------------------------
# Refusing malformed input
# ---------------------------------------------------------------------------


def test_a_file_with_no_array_is_rejected(tmp_path) -> None:
    """Not an array means not a dataset, and guessing is worse than refusing."""
    path = tmp_path / "object.json"
    path.write_text('{"open_time": "2021-01-01T00:00:00Z"}', encoding="utf-8")

    with pytest.raises(DatasetFormatError, match="no JSON array"):
        list(stream_json_records(str(path)))


def test_a_truncated_file_is_rejected_rather_than_silently_short(tmp_path) -> None:
    """A dataset cut off mid-file must not read as a shorter dataset.

    Silently returning the prefix is the dangerous outcome: every statistic
    computed from it is a valid number describing the wrong period, and nothing
    in the output says the file was incomplete.
    """
    path = tmp_path / "cut.json"
    full = json.dumps([record(i) for i in range(20)])
    path.write_text(full[: len(full) // 2], encoding="utf-8")

    with pytest.raises(DatasetFormatError):
        list(stream_json_records(str(path), buffer_bytes=TINY_BUFFER))


def test_a_malformed_record_is_rejected_with_its_position(tmp_path) -> None:
    """The offset is in the message because that is where the fix starts."""
    path = tmp_path / "bad.json"
    # Written as raw text rather than through ``json.dumps``: a dumped list
    # would quote the broken element, making it a *valid* string record that the
    # reader would correctly hand back. The file has to be malformed to match.
    path.write_text(
        "[" + json.dumps(record(0)) + ", {not json}, " + json.dumps(record(2)) + "]",
        encoding="utf-8",
    )

    with pytest.raises(DatasetFormatError, match="offset"):
        list(stream_json_records(str(path), buffer_bytes=4096))


# ---------------------------------------------------------------------------
# Laziness: the reader must not read the file to find its first record
# ---------------------------------------------------------------------------


def test_the_reader_produces_records_before_the_file_is_exhausted(tmp_path) -> None:
    """Asserted by consumption, not by a spy on ``read``.

    ``list(...)`` would pass on a reader that streams and on one that
    materialises, so the check is whether the *source* still has items left
    after the first one has been handed over.
    """
    path = write_dataset(tmp_path, 50)
    source = stream_json_records(path, buffer_bytes=TINY_BUFFER)

    first = next(source)
    assert first["open"] == "40000"
    # The reader is a generator, not a list; the rest of the file is still unread.
    assert next(source)["open"] == "40001"


def test_chunking_never_holds_more_than_chunk_rows(tmp_path) -> None:
    """The bound is what keeps a 198k-bar dataset off the heap."""
    path = write_dataset(tmp_path, 500)
    chunks = stream_chunks(path, chunk_rows=64, buffer_bytes=TINY_BUFFER)

    sizes = [len(chunk) for chunk in chunks]
    assert max(sizes) == 64
    assert sum(sizes) == 500


def test_chunking_reassembles_the_whole_dataset_in_order(tmp_path) -> None:
    """Batching is a memory technique; it must not reorder or drop."""
    path = write_dataset(tmp_path, 50)
    whole = list(stream_candles(path, buffer_bytes=TINY_BUFFER))
    chunked = [c for batch in stream_chunks(path, chunk_rows=7) for c in batch]

    assert chunked == whole


def test_read_chunks_works_on_a_sequence_too(tmp_path) -> None:
    """A caller holding candles already should get the same batching.

    Otherwise the batch bound would only apply to the streaming path, and the
    in-memory path -- which is what a small test or a caller with a cached
    dataset uses -- would be unbounded by construction.
    """
    candles = [CandleData.model_validate(record(i)) for i in range(20)]

    assert [len(c) for c in read_chunks(candles, chunk_rows=6)] == [6, 6, 6, 2]


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


def test_segments_tile_the_range_with_no_gap_and_no_overlap() -> None:
    """Half-open at both ends, so no bar is counted twice and none is skipped.

    This is the property that makes a segmented run equal to a continuous one;
    if it fails here, no equivalence test downstream can mean anything.
    """
    segments = plan_segments(BASE, BASE + timedelta(days=10), segment_days=3)

    assert segments[0].start == BASE
    assert segments[-1].end == BASE + timedelta(days=10)
    for earlier, later in zip(segments, segments[1:], strict=False):
        assert earlier.end == later.start
        assert earlier.index + 1 == later.index


def test_the_final_segment_is_short_rather_than_overlong() -> None:
    """A fixed-width plan would run past ``end`` and process bars not asked for."""
    segments = plan_segments(BASE, BASE + timedelta(days=7), segment_days=3)

    assert (segments[-1].end - segments[-1].start).days == 1


def test_an_empty_range_plans_no_segments() -> None:
    """Defined rather than an exception, for the same reason the reader is."""
    assert plan_segments(BASE, BASE, segment_days=3) == []
    assert plan_segments(BASE, BASE - timedelta(days=1), segment_days=3) == []


def test_every_candle_lands_in_exactly_one_segment(tmp_path) -> None:
    """The partition must be a partition -- the union is the dataset, disjointly."""
    candles = [
        CandleData.model_validate(record(i)) for i in range(0, 24 * 12, 5)
    ]
    segments = plan_segments(BASE, BASE + timedelta(days=1), segment_days=1)

    assigned = [s.index for c in candles for s in segments if s.contains(c.open_time)]

    assert len(assigned) == len(candles)
    assert sorted(assigned) == assigned


def test_segmenting_a_stream_reassembles_the_whole_dataset(tmp_path) -> None:
    """The grouping must not lose or duplicate a bar.

    A dropped bar here is a dropped bar in the analysis, and it would appear as
    a slightly smaller dataset rather than as an error.
    """
    candles = [CandleData.model_validate(record(i)) for i in range(0, 24 * 12, 5)]
    segments = list(segment_candles(candles, segment_days=1))

    rebuilt = [candle for bars in segments for candle in bars.candles]

    assert rebuilt == candles


def test_unsorted_candles_are_refused_rather_than_misassigned(tmp_path) -> None:
    """The grouping needs order and says so.

    An out-of-order bar attached to the wrong segment would not be an obvious
    failure -- it would be a dataset with a bar moved, which changes the
    structure analysis without changing any count.
    """
    candles = [CandleData.model_validate(record(i)) for i in range(0, 60, 5)]
    swapped = [candles[1], candles[0], *candles[2:]]

    with pytest.raises(ValueError, match="not sorted"):
        list(segment_candles(swapped, segment_days=1))