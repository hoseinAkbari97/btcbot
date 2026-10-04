"""A resumed run must equal an uninterrupted one, exactly.

Checkpoints exist so a run that is killed for memory can continue where it
stopped. That is only worth anything if the resumed run produces the *same*
answer as a run that was never interrupted -- otherwise an aborted run and a
clean run are two different datasets wearing the same name, and nothing
downstream can tell them apart.

So this is an equality test, not a smoke test. It compares swings, events,
levels, the carried trailing window, the trailing closes, the running range and
the regime label, field for field, against a state that consumed the same bars
without interruption.

The specific failure this guards against is the carried window. A swing is
confirmed ``2 * lookback`` bars after its pivot, so a checkpoint that did not
carry those trailing bars would resume with a half-built window and shift every
swing near the boundary. The shift is small, the levels still look plausible,
and the run still reports a number -- it is just the number for a slightly
different series.

Real ingested 5m data, for the reason the other differentials use it: the
dataset is the only fixture that produces enough levels for the clustering
tolerance to matter.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.market_data import Timeframe
from app.services.market_structure.segmented import StructureState
from app.services.research.streaming import stream_candles

DATASET = Path(__file__).resolve().parents[1] / "data" / "datasets" / (
    "BTCUSDT-5m-20210101-20260901.json"
)

SPLIT = 2000
TOTAL = 4000


def real_bars(count: int) -> list:
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    out = []
    for candle in stream_candles(DATASET):
        out.append(candle)
        if len(out) >= count:
            break
    return out


def feeds(bars: list, stop: int, size: int) -> StructureState:
    """A state fed ``bars[:stop]`` in ``size``-bar segments."""
    state = StructureState("BTCUSDT", Timeframe.M5)
    start = 0
    while start < stop:
        end = min(start + size, stop)
        state.observe(bars[start:end])
        start = end
    return state


def swings_of(state: StructureState) -> list[tuple]:
    return [
        (s.index, s.timestamp, s.price, s.kind, s.confirmation_index, s.confirmation_time)
        for s in state.swings
    ]


def events_of(state: StructureState) -> list[tuple]:
    return [
        (
            e.index,
            e.timestamp,
            e.price,
            e.event_type,
            e.confirmation_index,
            e.broken_level,
            e.penetration,
            e.source_swing_idx,
            e.previous_state,
            e.new_state,
            e.direction,
        )
        for e in state.events
    ]


def levels_of(state: StructureState) -> list[tuple]:
    return [
        (
            lv.price,
            lv.level_type,
            lv.creation_index,
            lv.creation_time,
            lv.first_seen,
            lv.last_seen,
            lv.touch_count,
            lv.strength,
            lv.source_swing_indices,
            lv.swing_confirmations,
        )
        for lv in state.levels()
    ]


def assert_equal(resumed: StructureState, whole: StructureState) -> None:
    assert swings_of(resumed) == swings_of(whole)
    assert events_of(resumed) == events_of(whole)
    assert levels_of(resumed) == levels_of(whole)
    assert resumed.regime() == whole.regime()
    assert resumed.result().recent_range == whole.result().recent_range
    assert resumed.result().as_of_index == whole.result().as_of_index
    # The carried rolling state itself, not just what it produced.
    assert resumed._closes == whole._closes
    assert [
        (c.open_time, c.high, c.low, c.close) for c in resumed._window
    ] == [(c.open_time, c.high, c.low, c.close) for c in whole._window]
    assert resumed._next_index == whole._next_index


def test_resume_from_a_checkpoint_equals_an_uninterrupted_run() -> None:
    """The core guarantee: abort and continue, get the same answer."""
    bars = real_bars(TOTAL)
    before = feeds(bars, SPLIT, 311)
    # Through JSON, because that is how a checkpoint actually crosses a process
    # boundary -- and because a payload that only survives in memory is not one.
    payload = json.loads(json.dumps(before.to_payload()))
    resumed = StructureState.from_payload(payload)
    resumed.observe(bars[SPLIT:])

    whole = StructureState("BTCUSDT", Timeframe.M5)
    whole.observe(bars)
    assert_equal(resumed, whole)


@pytest.mark.parametrize("size", [1, 37, 311, SPLIT])
def test_resume_is_independent_of_the_segment_size_that_preceded_it(size: int) -> None:
    """The checkpoint is the only thing that crosses the boundary.

    Segment size before the checkpoint must not matter: whatever segmentation the
    first half used, the carried state at the checkpoint is the same, and the
    second half must produce the same result. A checkpoint that encoded any of
    the segmentation's incidental state -- a chunk length, a partial window --
    would pass the test above and fail this one.
    """
    bars = real_bars(TOTAL)
    before = feeds(bars, SPLIT, size)
    resumed = StructureState.from_payload(json.loads(json.dumps(before.to_payload())))
    resumed.observe(bars[SPLIT:])
    whole = StructureState("BTCUSDT", Timeframe.M5)
    whole.observe(bars)
    assert_equal(resumed, whole)


def test_a_checkpoint_carries_the_window_a_swing_needs() -> None:
    """The trailing bars are in the payload, not just in memory.

    Checked directly because the failure it prevents is subtle: drop the window
    and the resumed run still completes, still produces levels, and differs from
    the uninterrupted run only in the swings near the boundary.
    """
    bars = real_bars(TOTAL)
    state = feeds(bars, SPLIT, 311)
    payload = state.to_payload()
    assert len(payload["window"]) == 2 * state.lookback + 1, (
        "the carried window must hold exactly the bars needed to confirm the next "
        "swing, or resume shifts every swing near the boundary"
    )


def test_resuming_a_stale_schema_fails_loudly() -> None:
    """A checkpoint from another build is rejected, not guessed at.

    Resuming across a schema change by interpreting the old fields anyway is the
    failure that produces a clean-looking report of the wrong run, so the version
    is checked rather than assumed.
    """
    bars = real_bars(1200)
    payload = feeds(bars, 900, 100).to_payload()
    payload["schema_version"] = payload["schema_version"] + 1
    with pytest.raises(ValueError, match="schema version"):
        StructureState.from_payload(payload)


def test_a_checkpoint_with_a_hole_in_it_is_rejected() -> None:
    """A bucket referring to an absent swing is a corrupt checkpoint.

    Not hypothetical: the bucket list and the swing list are written as
    separate arrays, so a partial write or a hand-edited file can produce one
    without the other. Reading it anyway would attach a level to the wrong swing
    silently.
    """
    bars = real_bars(1200)
    payload = feeds(bars, 900, 100).to_payload()
    payload["swings"] = payload["swings"][:-1]
    with pytest.raises(ValueError, match="not in the swing list"):
        StructureState.from_payload(payload)
