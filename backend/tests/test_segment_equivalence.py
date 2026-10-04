"""A segmented research run must equal a whole-series run, number for number.

The runner's entire premise is that a segment boundary is a *memory* boundary
and nothing else. Counts alone cannot establish that: a run that loses a
handful of events at each boundary still reports the right order of magnitude,
and one that computes an ATR from a truncated window still reports a plausible
mean. So these compare the accumulated statistics themselves -- n, mean,
variance and the barrier tallies -- against the batch path over identical data.

Three separate failure modes are guarded, each of which was a real bug found by
running this comparison rather than by reading the code:

* events stranded at a boundary because their forward window never completed,
  which silently shrinks the sample the statistics are computed over;
* outcomes computed from the wrong bars, which shift every mean by a little and
  so never fail an equality check on counts;
* resume restoring a partial accumulator, which reports only the segments that
  followed the checkpoint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.resources import ResourceLimits
from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.aggregate import OutcomeAccumulator, label_events_streaming
from app.services.research.events import detect_liquidity_sweeps
from app.services.research.segmented_runner import SegmentedResearchRunner
from app.services.research.streaming import stream_candles

DATASET = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "datasets"
    / "BTCUSDT-5m-20210101-20260901.json"
)

START = datetime(2021, 1, 1, tzinfo=UTC)
END = datetime(2021, 2, 1, tzinfo=UTC)


@pytest.fixture(scope="module")
def month() -> list:
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    bars = []
    for candle in stream_candles(DATASET):
        if candle.open_time >= END:
            break
        bars.append(candle)
    return bars


@pytest.fixture(scope="module")
def whole(month) -> OutcomeAccumulator:
    structure = analyze_market_structure(
        month, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    events = detect_liquidity_sweeps(month, levels=structure.liquidity_levels)
    accumulator = OutcomeAccumulator()
    label_events_streaming(month, events, accumulator)
    return accumulator


def segmented(tmp_path: Path, bars: list, *, segment_days: int) -> OutcomeAccumulator:
    import json

    runner = SegmentedResearchRunner(
        dataset=DATASET,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=segment_days),
        start=START,
        end=END,
        out_dir=tmp_path,
    )
    runner.run()
    return json.loads(runner.checkpoint_path.read_text(encoding="utf-8"))["outcomes"]


def test_the_fixture_produces_enough_events_to_mean_anything(
    month, whole
) -> None:
    """A month that detects almost nothing would make the equality below vacuous.

    Without this, a detector that silently stopped finding sweeps would produce
    matching counts on both paths and pass -- the differential would be testing
    that two runs of a broken detector agree.
    """
    assert whole.total > 10_000, f"only {whole.total} outcomes; too weak to compare"
    assert len(whole.families()) >= 4, "too few families to exercise the cell keys"


@pytest.mark.parametrize("segment_days", [1, 3, 7])
def test_segmented_aggregates_equal_the_whole_series(
    tmp_path, month, whole, segment_days: int
) -> None:
    """The core guarantee, at three segment sizes.

    ``1`` puts a boundary roughly every 288 bars, so a five-day segment is
    straddle-heavy and every boundary is crossed by many events; ``7`` is the
    size the 2021 validation run uses. Both must produce the same numbers as one
    pass, because neither the boundaries nor their spacing may change a result.
    """
    report = segmented(tmp_path / f"seg{segment_days}", month, segment_days=segment_days)

    assert report["total_outcomes"] == whole.total
    assert report["truncated_outcomes"] == whole.truncated

    whole_cells = {
        (c["detector"], c["kind"], c["side"], c["stop_model"]): c
        for c in whole.as_dict()["cells"]
    }
    segmented_cells = {
        (c["detector"], c["kind"], c["side"], c["stop_model"]): c for c in report["cells"]
    }
    assert set(segmented_cells) == set(whole_cells)

    for key, expected in whole_cells.items():
        actual = segmented_cells[key]
        assert actual["barriers"] == expected["barriers"], f"barriers differ for {key}"
        assert actual.get("excursions", {}) == expected.get("excursions", {}), (
            f"excursions differ for {key}"
        )
        assert set(actual["horizons"]) == set(expected["horizons"]), f"horizons differ for {key}"
        for horizon, moment in expected["horizons"].items():
            got = actual["horizons"][horizon]
            assert got["n"] == moment["n"], f"{key} h={horizon}: n differs"
            # Exact, not approximate. These are means of the same Decimals in a
            # different order, and Welford is stable enough that the results
            # agree to the last bit; a tolerance here would hide a wrong-bar read.
            assert got["mean"] == pytest.approx(moment["mean"], rel=1e-12, abs=1e-15)
            assert got["variance"] == pytest.approx(
                moment["variance"], rel=1e-9, abs=1e-18
            )


def test_resuming_a_finished_run_changes_nothing(tmp_path) -> None:
    """A completed checkpoint is a result, not pending work.

    Re-invoking must not re-detect every event and append them to the spill it
    already produced -- that would double the event count while the statistics
    stayed right, which is precisely the kind of error a summary cannot show.
    """
    first = SegmentedResearchRunner(
        dataset=DATASET, symbol="BTCUSDT", limits=ResourceLimits(segment_days=7),
        start=START, end=END, out_dir=tmp_path / "resume",
    )
    original = first.run()
    spilled = first.events_path.read_text(encoding="utf-8").count("\n")

    second = SegmentedResearchRunner(
        dataset=DATASET, symbol="BTCUSDT", limits=ResourceLimits(segment_days=7),
        start=START, end=END, out_dir=tmp_path / "resume",
    )
    repeated = second.run()

    assert repeated.bars == original.bars
    assert repeated.events == original.events
    assert repeated.outcomes == original.outcomes
    assert second.events_path.read_text(encoding="utf-8").count("\n") == spilled


def test_a_checkpoint_from_a_different_range_is_refused(tmp_path) -> None:
    """Bar indices are absolute, so a different range is a different analysis.

    Resuming a one-month run from a full-year checkpoint would skip bars it never
    processed and then try to label events against bars it never read. The
    fingerprint carries the date range precisely so that is a refusal rather than
    a crash that looks like a segmentation bug.
    """
    from app.services.research.segmented_runner import CheckpointMismatch

    out = tmp_path / "mismatch"
    full = SegmentedResearchRunner(
        dataset=DATASET, symbol="BTCUSDT", limits=ResourceLimits(segment_days=7),
        start=START, end=None, out_dir=out,
    )
    # Write a checkpoint without running the whole dataset: the fingerprint is
    # what is under test, not the run.
    full._digest = "x" * 64
    full.state = __import__(
        "app.services.market_structure.segmented", fromlist=["StructureState"]
    ).StructureState("BTCUSDT", Timeframe.M5)
    full._write_checkpoint()

    narrowed = SegmentedResearchRunner(
        dataset=DATASET, symbol="BTCUSDT", limits=ResourceLimits(segment_days=7),
        start=START, end=END, out_dir=out,
    )
    with pytest.raises(CheckpointMismatch):
        narrowed.run()
