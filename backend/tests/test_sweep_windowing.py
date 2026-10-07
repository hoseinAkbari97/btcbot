"""A windowed sweep run must equal the whole-series run, event for event.

The segmented runner's whole premise is that a boundary is a *memory* boundary
and nothing else. That claim is not testable by counting events: a run that
loses a sweep at every boundary still reports the right order of magnitude, and
one that confirms each boundary sweep against the wrong bar differs from the
continuous result by a single price on a handful of events. Both look fine in a
report.

So these compare full records -- event bar, confirmation bar and time, price,
level price, penetration, swing count -- against the batch path over the same
data. Equality, not similarity.

Real ingested 5m data, for the reason the other differentials use it: the
synthetic fixtures produce too few levels for a price-band selection to be
exercised at all, so a boundary bug hides in them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.schemas.market_data import Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.events import (
    SweepCarried,
    detect_compression,
    detect_liquidity_sweeps,
)
from app.services.research.segmented_runner import COMPRESSION_VOL_WINDOW
from app.services.research.streaming import stream_candles

DATASET = Path(__file__).resolve().parents[1] / "data" / "datasets" / (
    "BTCUSDT-5m-20210101-20260901.json"
)

BARS = 6000


def real_bars(count: int) -> list:
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    out = []
    for candle in stream_candles(DATASET):
        out.append(candle)
        if len(out) >= count:
            break
    return out


def identity(events) -> list[tuple]:
    """Every field that a segmented run could plausibly get wrong.

    Deliberately not the row projection: ``as_row`` stringifies and flattens,
    which would hide a ``Decimal`` that survived a checkpoint as a float.
    """
    return sorted(
        (
            e.kind,
            e.detector,
            e.event_index,
            e.event_time,
            e.confirmation_index,
            e.confirmation_time,
            e.price,
            e.features.get("level_price"),
            e.features.get("penetration"),
            e.features.get("level_swing_count"),
            e.features.get("level_touch_count"),
        )
        for e in events
    )


def windowed(bars: list, levels, size: int) -> list:
    carried = SweepCarried()
    out = []
    for start in range(0, len(bars), size):
        out.extend(
            detect_liquidity_sweeps(
                bars[start : start + size],
                levels=levels,
                offset=start,
                carried=carried,
                final=start + size >= len(bars),
            )
        )
    return out


def test_the_fixture_is_strong_enough_to_detect_a_boundary_bug() -> None:
    """A fixture that passes for the wrong reason is worse than no fixture.

    Every boundary defect this file guards against shows up as a small absolute
    difference -- a handful of events out of thousands. Asserting the scale
    first means a later failure is a real regression rather than a dataset that
    shrank.
    """
    bars = real_bars(BARS)
    result = analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5)
    events = detect_liquidity_sweeps(bars, result=result)
    assert len(events) > 1000, "too few sweeps for a boundary loss to show"
    assert len(result.liquidity_levels) > 100, "too few levels to exercise price banding"


@pytest.mark.parametrize("size", [500, 1000, 2500, 3333, BARS - 1])
def test_windowed_sweeps_equal_the_whole_series(size: int) -> None:
    """The core guarantee, at sizes chosen to straddle bar indices.

    ``size=2500`` puts boundaries at bars whose level prices sit inside the
    dataset's actual price range; ``3333`` is coprime with the bar count so no
    two boundaries share an alignment. ``BARS - 1`` isolates a single boundary.
    """
    bars = real_bars(BARS)
    result = analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5)
    levels = result.liquidity_levels

    whole = detect_liquidity_sweeps(bars, levels=levels)
    segmented = windowed(bars, levels, size)

    assert identity(segmented) == identity(whole)
    assert len(segmented) == len(whole)


def test_a_sweep_on_a_boundary_bar_is_confirmed_by_the_next_window() -> None:
    """The specific case the deferral exists for.

    Checked directly rather than only through equality, because a fixture that
    happens not to sweep anything on a boundary bar would let the deferral be
    deleted and every equality test above would still pass.
    """
    bars = real_bars(BARS)
    result = analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5)
    levels = result.liquidity_levels

    size = 1000
    carried = SweepCarried()
    boundary_events = []
    for start in range(0, len(bars), size):
        found = detect_liquidity_sweeps(
            bars[start : start + size],
            levels=levels,
            offset=start,
            carried=carried,
            final=start + size >= len(bars),
        )
        boundary_events.extend(
            e for e in found if e.event_index in (size, 2 * size, 3 * size)
        )
    assert boundary_events, "the fixture sweeps nothing on a boundary bar"

    whole = detect_liquidity_sweeps(bars, levels=levels)
    for event in boundary_events:
        match = [e for e in whole if e.event_index == event.event_index]
        assert match, f"boundary sweep {event.event_index} absent from the whole series"
        assert event.confirmation_index == event.event_index + 1
        assert event.confirmation_index == match[0].confirmation_index
        assert event.price == match[0].price


def test_carried_state_survives_a_json_checkpoint() -> None:
    """A resumed run must see exactly what an uninterrupted one would.

    Through JSON, because that is how a checkpoint actually crosses a process
    boundary -- and a state that only round-trips in memory is not resumable.
    Swept set, pending events and the trailing bar all have to survive; the
    third is the easiest to omit and silently re-reads ``candles[-1]``.
    """
    import json

    bars = real_bars(BARS)
    result = analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5)
    levels = result.liquidity_levels
    size = 1000

    carried = SweepCarried()
    for start in range(0, size, size):
        detect_liquidity_sweeps(
            bars[start : start + size],
            levels=levels,
            offset=start,
            carried=carried,
            final=False,
        )
    assert carried.swept, "the swept set is empty; the fixture proves nothing"
    assert carried.previous_bar is not None

    restored = SweepCarried.from_payload(json.loads(json.dumps(carried.to_payload())))
    assert restored.swept == carried.swept
    assert restored.pending == carried.pending
    assert restored.previous_bar == carried.previous_bar

    resumed = []
    for start in range(size, len(bars), size):
        resumed.extend(
            detect_liquidity_sweeps(
                bars[start : start + size],
                levels=levels,
                offset=start,
                carried=restored,
                final=start + size >= len(bars),
            )
        )
    # Compare against the whole-series events *from the resume point on*. Taking
    # a slice of the sorted list instead would be slicing by identity tuple, not
    # by time, and would fail for reasons that have nothing to do with the
    # checkpoint.
    whole = detect_liquidity_sweeps(bars, levels=levels)
    expected = [e for e in whole if e.event_index >= size - 1]
    assert identity(resumed) == identity(expected)


# ---------------------------------------------------------------------------
# Compression windowing
# ---------------------------------------------------------------------------
#
# Compression carries no state of its own, so its windowed guarantee is a
# different one from the sweep's. The sweep's risk is a *lost* event at a
# boundary (its carried `swept` set forgets a level). Compression's risk is the
# opposite: it re-derives from scratch on every window, so the boundary can
# produce a *duplicate* -- the same release found once in the window that ends
# on it and again in the window that starts there.


def compression_identity(events) -> list[tuple]:
    """Every compression field, unflattened, so a type change cannot hide."""
    return sorted(
        (
            e.kind,
            e.detector,
            e.event_index,
            e.event_time,
            e.confirmation_index,
            e.price,
            e.features.get("compression_ratio"),
            e.features.get("volatility_5"),
            e.features.get("volatility_20"),
            e.features.get("range_20"),
            e.features.get("release_range"),
            e.context.get("direction"),
            # ``start_index`` is absolute and travels in the payload, so it is
            # exactly the field a windowing offset bug would corrupt.
            e.context.get("start_index"),
        )
        for e in events
    )


def compression_windowed(bars: list, size: int, overlap: int = 64) -> list:
    """Run compression window by window with a trailing prefix, as the runner does.

    ``overlap`` mirrors ``OUTCOME_LOOKBACK_BARS``. The prefix exists only to
    give the trailing volatility windows their history; its own events are
    dropped, and that filter is what this test is really about.
    """
    out = []
    for start in range(0, len(bars), size):
        window_start = max(0, start - overlap)
        events = detect_compression(
            bars[window_start : start + size],
            vol_window=COMPRESSION_VOL_WINDOW,
            offset=window_start,
        )
        out.extend(e for e in events if e.event_index >= start)
    return out


def test_the_fixture_contains_compressions_to_compare() -> None:
    """Same guard as above: a detector that stopped firing passes vacuously."""
    bars = real_bars(BARS)
    assert len(detect_compression(bars, vol_window=COMPRESSION_VOL_WINDOW)) > 3


@pytest.mark.parametrize("size", [500, 1000, 2500, 3333])
def test_windowed_compressions_equal_the_whole_series(size: int) -> None:
    """Windowing must neither duplicate nor lose a release.

    With no carried state the only thing that can go wrong is an off-by-one on
    the ``offset``, which shows up as a release reported on the wrong bar -- and
    the bar is what ties the event to its outcome, so a shifted event is not a
    cosmetic difference but a mislabelled result.
    """
    bars = real_bars(BARS)
    expected = compression_identity(
        detect_compression(bars, vol_window=COMPRESSION_VOL_WINDOW)
    )
    actual = compression_identity(compression_windowed(bars, size))

    assert actual == expected, "windowed compression diverged from the whole series"


def test_a_release_never_appears_in_two_windows() -> None:
    """The duplicate case, asserted directly rather than only via equality.

    Equality catches it, but only because the two copies differ in some field.
    A duplicate that happened to match exactly -- same bar, same numbers -- would
    slide through, and it is the more dangerous half: it inflates the sample
    size the statistics are computed over while leaving every mean intact.
    """
    bars = real_bars(BARS)
    seen: list[int] = []
    for start in range(0, len(bars), 500):
        window_start = max(0, start - 64)
        for event in detect_compression(
            bars[window_start : start + 500],
            vol_window=COMPRESSION_VOL_WINDOW,
            offset=window_start,
        ):
            if event.event_index >= start:
                seen.append(event.event_index)
    assert len(seen) == len(set(seen)), "a bar produced two compression events"
