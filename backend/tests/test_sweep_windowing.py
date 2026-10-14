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

from datetime import UTC, datetime, timedelta
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

DATASET = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "datasets"
    / ("BTCUSDT-5m-20210101-20260901.json")
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
        boundary_events.extend(e for e in found if e.event_index in (size, 2 * size, 3 * size))
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
    expected = compression_identity(detect_compression(bars, vol_window=COMPRESSION_VOL_WINDOW))
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


# ===========================================================================
# The confirmation-bar measurement, independent of window length
# ===========================================================================


def test_the_recovery_measurement_does_not_depend_on_where_the_window_ends() -> None:
    """``recovery_ratio`` must be a property of the bar, not of the segment grid.

    The measurements that need the confirmation bar used to find it as
    ``min(index + 1, len(candles) - 1)`` -- the *window's* length standing in for
    the series' length. On a window that ends at the pierce bar that clamp lands
    the confirmation back on the pierce bar itself, so the ratio came out against
    the pierce bar's own close.

    The fixture below is small enough to compute by hand:

        bar 5   high 110, low 90, close 91 -- pierces a level at 100 and closes
                back below it, which is a sweep of a high from underneath
        bar 6   close 95

    The level is at 100. ``recovery_ratio`` is
    ``|confirmation_close - 100| / |pierce_high - 100| = |95 - 100| / |110 - 100| = 0.5``.

    The same bar measured with the window ending at the pierce bar used to
    report ``|91 - 100| / |110 - 100| = 0.9`` -- a different number for an
    identical bar, differing only in where the caller chose to stop.
    """
    from decimal import Decimal

    from conftest import make_candle

    from app.services.market_structure import LiquidityLevel
    from app.services.research.events import _bare_structure, measure_sweep

    bars = [
        make_candle(i * 5, open_price="100", high="100", low="100", close="100") for i in range(8)
    ]
    bars[5] = make_candle(25, open_price="100", high="110", low="90", close="91")
    bars[6] = make_candle(30, open_price="91", high="96", low="90", close="95")

    level = LiquidityLevel(
        price=Decimal("100"),
        level_type="swing_high",
        origin="swing",
        first_seen=bars[0].close_time,
        last_seen=bars[0].close_time,
        creation_index=0,
        creation_time=bars[0].close_time,
        touch_count=1,
        strength=0.5,
    )

    measured = [
        measure_sweep(
            bars[:end],
            5,
            level,
            "above",
            6,
            bars[:5],
            _bare_structure(),
            confirmation=bars[6],
        )
        for end in (6, 7, 8)
    ]
    for measures in measured:
        assert measures.recovery_ratio == Decimal("0.5"), (
            f"got {measures.recovery_ratio}; |95-100| / |110-100| is 0.5"
        )
        assert measures.time_above == 0 and measures.time_below == 1, (
            "bar 6 closes at 95, below the level at 100, so exactly one bar "
            "closed below and none above"
        )
    assert len({str(m.recovery_ratio) for m in measured}) == 1


def test_a_deferred_sweep_is_re_measured_not_merely_re_dated() -> None:
    """The parked last-bar sweep gets its measurements from the right bar.

    A sweep on a non-final window's last bar is parked in
    :attr:`SweepCarried.pending` and re-emitted by the next window, which is the
    first place its confirmation bar exists. The replay used to patch the
    confirmation index, time and price and carry the previous window's
    measurements across unchanged -- so those fields described a bar the reader
    never saw them describe.

    Measured on BTCUSDT 5m Q1 2021 this was 38 of 268,358 sweep events, one per
    segment boundary, differing from a continuous run in ``time_above``,
    ``time_below`` and ``recovery_ratio`` while every aggregate still matched --
    38 rows out of 268,358 do not move a mean enough to notice.

    The check here is the property, not the count: the deferred event's three
    measurements must equal what the same bar produces when measured in one
    uninterrupted window.
    """
    bars = real_bars(BARS)
    levels = analyze_market_structure(
        bars, symbol="BTCUSDT", timeframe=Timeframe.M5
    ).liquidity_levels

    whole = {
        (e.detector, e.event_index): e
        for e in detect_liquidity_sweeps(bars, levels=levels, excursion_bars=6)
    }

    boundary = 2500
    resumed = []
    carried = SweepCarried()
    for start in range(0, len(bars), boundary):
        resumed.extend(
            detect_liquidity_sweeps(
                bars[start : start + boundary],
                levels=levels,
                offset=start,
                carried=carried,
                final=start + boundary >= len(bars),
                excursion_bars=6,
            )
        )

    deferred = [event for event in resumed if event.event_index in (boundary - 1,)]
    assert deferred, (
        f"the fixture must produce a sweep on bar {boundary - 1} or this test "
        "measures nothing; pick a boundary that carries one"
    )
    for event in deferred:
        reference = whole[(event.detector, event.event_index)]
        for field in ("time_above", "time_below", "recovery_ratio", "wick_ratio"):
            assert event.features.get(field) == reference.features.get(field), (
                f"{event.detector} at bar {event.event_index}: {field} is "
                f"{event.features.get(field)} from the windowed run and "
                f"{reference.features.get(field)} from the whole-series run; a "
                "deferred sweep must be re-measured, not replayed"
            )


def test_a_deferred_sweep_reproduces_the_whole_series_ratio_exactly() -> None:
    """The re-measured ratio must be bit-identical, not merely close.

    The obvious way to recover the excursion denominator on a sweep deferred to
    the next window is algebraically: ``level * (1 + penetration)`` is equal to
    ``|pierce_extreme - level|``. It is not equal *numerically* -- it round-trips
    through a division and a multiplication, and the noise survives into the
    quotient.

    On BTCUSDT 5m Q1 2021 that left the 28th decimal place of ``recovery_ratio``
    differing on the deferred events:

        whole series   0.5727951023531662521522862062
        segmented      0.5727951023531662521522860967

    A relative error of 2e-25. It cannot matter to any statistic, and it breaks
    every equality check this project makes -- which is the point. A segmented run
    that is "equal to within rounding" is not equal, and the day it is compared
    with a tolerance is the day a real difference hides inside it. So the
    denominator is carried on the event rather than re-derived.

    The fixture below is a hand-built deferred sweep, so the failure is
    deterministic rather than dependent on which boundary happens to carry one.
    """
    from decimal import Decimal

    from app.schemas.market_data import CandleData, Timeframe
    from app.services.market_structure import LiquidityLevel
    from app.services.research.events import SweepCarried

    level_price = Decimal("32194.40")
    pierce_high = Decimal("32246.67")

    def bar(minutes: int, *, high: str, low: str, close: str) -> CandleData:
        return CandleData(
            symbol="BTCUSDT",
            timeframe=Timeframe.M5,
            open_time=datetime(2021, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes),
            close_time=datetime(2021, 1, 1, tzinfo=UTC)
            + timedelta(minutes=minutes + 5, microseconds=-1),
            open=Decimal("32190.00"),
            high=Decimal(high),
            low=Decimal(low),
            close=Decimal(close),
            volume=Decimal("10"),
        )

    # Bar 0 pierces the level (high 32246.67 is above it) and closes back below
    # at 32100. Bar 1 closes at 32164.46 -- the confirmation.
    # The detector starts at bar 1 because it needs the previous bar's range to
    # build its candidate band, so the pierce is on the second bar.
    lead = bar(0, high="32180.00", low="32110.00", close="32150.00")
    first = bar(5, high="32246.67", low="32090.00", close="32100.00")
    second = bar(10, high="32200.00", low="32160.00", close="32164.46")

    level = LiquidityLevel(
        price=level_price,
        level_type="range_high",
        origin="range",
        first_seen=first.close_time,
        last_seen=first.close_time,
        creation_index=0,
        creation_time=lead.close_time,
        touch_count=0,
        strength=0.0,
    )

    whole = detect_liquidity_sweeps(
        [lead, first, second], levels=[level], final=True, excursion_bars=6
    )
    assert len(whole) == 1, "the fixture must produce exactly one sweep"
    reference = whole[0]

    # The same bar, but as a *deferred* last-bar sweep: the detector sees only
    # ``second``, with the first window's state parked.
    carried = SweepCarried()
    carried.pending.append(reference.to_payload())
    # The replay also needs the previous window's last bar, which the real runner
    # carries and uses to open the window at its first bar. Without it the window
    # starts at bar 1 and finds nothing, so the fixture would pass vacuously.
    carried.previous_bar = (str(first.high), str(first.low))
    deferred = detect_liquidity_sweeps(
        [second], levels=[level], offset=10, carried=carried, final=True, excursion_bars=6
    )
    assert len(deferred) == 1

    expected = abs(second.close - level_price) / abs(pierce_high - level_price)
    assert reference.features["recovery_ratio"] == expected
    assert deferred[0].features["recovery_ratio"] == expected, (
        f"deferred {deferred[0].features['recovery_ratio']} against the whole "
        f"series' {reference.features['recovery_ratio']}; the denominator is "
        "being reconstructed instead of carried"
    )
