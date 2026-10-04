"""Segmented processing must equal whole-series processing, field for field.

This is the acceptance gate for :mod:`app.services.market_structure.segmented`.
The claim being tested is not "the segmenter works" but the stronger one:

    feeding :class:`StructureState` a whole series in one call, and feeding it
    that series in segments with state carried across the boundaries, produce
    the *same* result.

A segment boundary is a memory-management boundary and nothing else. If that is
false then every statistic derived from a segmented run is a statistic about the
segmentation rather than about the market, and nothing downstream could detect
it -- which is why this compares the full output rather than a summary.

The comparisons are field-for-field and order-sensitive on purpose. Comparing
swings and events as sets would pass on a state machine that emitted the right
objects in the wrong order, and the order is observable: it decides which event
a report lists first, and it decides the episode assignment that the cluster
bootstrap later resamples.

Real ingested 5m data, not a synthetic walk. A synthetic series has too few
levels and too-clean prices for the clustering tolerance to ever admit a real
match, so it would leave the one code path that actually decides whether a swing
joins an existing level completely untested.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.market_structure.segmented import StructureState
from app.services.research.streaming import stream_candles

DATASET = Path(__file__).resolve().parents[1] / "data" / "datasets" / (
    "BTCUSDT-5m-20210101-20260901.json"
)


def real_bars(count: int) -> list:
    """The first ``count`` bars of the ingested 5m dataset.

    Read through the streaming reader: this file is a few hundred MB of JSON and
    loading it whole is the failure this project has already paid for once.
    """
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    out = []
    for candle in stream_candles(DATASET):
        out.append(candle)
        if len(out) >= count:
            break
    return out


def swing_identity(swings: list) -> list[tuple]:
    return [
        (s.index, s.timestamp, s.price, s.kind, s.confirmation_index, s.confirmation_time)
        for s in swings
    ]


def event_identity(events: list) -> list[tuple]:
    return [
        (
            e.index,
            e.timestamp,
            e.price,
            e.event_type,
            e.confirmation_index,
            e.confirmation_time,
            e.broken_level,
            e.penetration,
            e.source_swing_idx,
            e.previous_state,
            e.new_state,
            e.direction,
        )
        for e in events
    ]


def level_identity(levels: list) -> list[tuple]:
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
            lv.origin,
            lv.source_swing_indices,
            lv.swing_confirmations,
        )
        for lv in levels
    ]


def assert_same(bars: list, splits: list[int]) -> None:
    """The batch result and the segmented result are the same result."""
    batch = analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5)

    state = StructureState("BTCUSDT", Timeframe.M5)
    start = 0
    for end in [*splits, len(bars)]:
        state.observe(bars[start:end])
        start = end

    assert state.result().as_of_index == batch.as_of_index

    assert swing_identity(state.swings) == swing_identity(batch.swings), (
        f"{len(state.swings)} swings segmented vs {len(batch.swings)} in one pass"
    )
    assert event_identity(state.events) == event_identity(batch.events), (
        f"{len(state.events)} events segmented vs {len(batch.events)} in one pass"
    )
    assert level_identity(state.levels()) == level_identity(batch.liquidity_levels), (
        f"{len(state.levels())} levels segmented vs "
        f"{len(batch.liquidity_levels)} in one pass"
    )
    assert state.regime() == batch.current_regime
    assert state.result().recent_range == batch.recent_range


def test_one_pass_equals_one_uneven_split() -> None:
    """The simplest case: two segments, split somewhere awkward.

    Unequal on purpose. An equal split is the case where an off-by-one in the
    carried window is least likely to show up, because both segments have the
    same amount of trailing context.
    """
    bars = real_bars(6000)
    assert_same(bars, [3777])


def test_many_short_segments_reproduce_the_whole() -> None:
    """Segments shorter than the swing window still reproduce the whole.

    A 70-bar carried window means a segment shorter than that cannot by itself
    confirm a swing -- the confirmation has to straddle the boundary. This split
    is deliberately finer than the window, so it is the test that actually
    exercises state carrying rather than a segmentation that happens to line up.
    """
    bars = real_bars(4000)
    assert_same(bars, list(range(30, 4000, 137)))


@pytest.mark.parametrize("seed", range(5))
def test_random_split_points_all_reproduce_the_whole(seed: int) -> None:
    """Twenty random splits over the same series, all must match.

    A segmentation that works at one particular boundary can easily fail at
    another, and the failure is specific: the carried window is the right length
    at one split and one bar short at the next. One hand-picked split proves
    nothing about that, so this draws random cut points with a seeded RNG and
    requires all of them to agree.
    """
    bars = real_bars(3000)
    rng = random.Random(seed)
    cuts = sorted(rng.sample(range(1, len(bars)), 6))
    assert_same(bars, cuts)


def test_bar_by_bar_matches_one_pass() -> None:
    """The limiting case: a segment per bar.

    Nothing carries across a boundary except the minimum window, so this is the
    segmentation that would fail first if any piece of carried state were being
    reset, dropped, or reconstructed from the wrong bars.
    """
    bars = real_bars(1200)
    assert_same(bars, list(range(1, 1200)))
