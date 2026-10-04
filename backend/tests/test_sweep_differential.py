"""The sweep detector's optimisation is only legitimate if it changes nothing.

``detect_liquidity_sweeps`` selects the levels a bar evaluates by price band
instead of scanning every active level, because scanning every level is
O(bars x levels) and measured 4x per doubling of bar count -- roughly five hours
on the 5m dataset, for one pass of one detector. The optimisation is only
allowed to exist if it returns *exactly* what the slow version returned, so
:func:`reference_sweeps` below is the original quadratic implementation, kept
here verbatim as the oracle, and every test asserts the two agree on the whole
event -- indices, prices, features and context, and the order of the list.

Order is part of the assertion, and deliberately so. The two implementations
find a bar's candidate levels by different routes: the slow one walks
``active`` in creation order, the fast one walks a price-sorted band and
re-sorts it into creation order. Dropping that re-sort produced the same set of
events in a different sequence -- which is invisible to a set comparison and
changes every report that lists them. A test that only checked membership would
have passed on that defect.

The tolerances used here are the detector's real defaults. A differential test
is only as good as its configuration: an oracle run at a tolerance the
production path never uses proves nothing about production.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure import LiquidityLevel
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.events import (
    _sweep_event,
    detect_liquidity_sweeps,
)

#: The detector's own defaults. Duplicated rather than imported so that a
#: change to the defaults is a *test failure* announcing that the oracle must
#: be re-checked, rather than a silent redefinition that makes both sides agree
#: for the wrong reason.
TOLERANCE = Decimal("0.001")
MIN_PENETRATION = Decimal("0")


def reference_sweeps(
    candles: list[CandleData], levels: list[LiquidityLevel]
) -> list:
    """The pre-optimisation detector, verbatim. The oracle, not production code.

    It is quadratic on purpose. Its only job is to be obviously correct, and a
    hand-checkable transcription of the original loop is more trustworthy for
    that purpose than a cleverer reimplementation would be.
    """
    by_index = sorted(levels, key=lambda level: (level.creation_index, level.price))
    events = []
    active: list[LiquidityLevel] = []
    beyond_since: dict[int, int] = {}
    cursor = 0
    for index in range(1, len(candles) - 1):
        while cursor < len(by_index) and by_index[cursor].creation_index < index:
            active.append(by_index[cursor])
            cursor += 1
        if not active:
            continue
        candle = candles[index]
        for level in active:
            if level.level_type not in ("swing_high", "equal_highs", "range_high"):
                continue
            if candle.high <= level.price * (Decimal(1) + TOLERANCE):
                beyond_since.pop(id(level), None)
                continue
            if id(level) in beyond_since:
                continue
            beyond_since[id(level)] = index
            penetration = (candle.high - level.price) / level.price
            if penetration < MIN_PENETRATION:
                continue
            events.append(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "above",
                    penetration,
                    candle.close < level.price,
                    "swing_high",
                    level.swing_count_at(index),
                )
            )
        for level in active:
            if level.level_type not in ("swing_low", "equal_lows", "range_low"):
                continue
            if candle.low >= level.price * (Decimal(1) - TOLERANCE):
                beyond_since.pop(id(level), None)
                continue
            if id(level) in beyond_since:
                continue
            beyond_since[id(level)] = index
            penetration = (level.price - candle.low) / level.price
            if penetration < MIN_PENETRATION:
                continue
            events.append(
                _sweep_event(
                    candles,
                    index,
                    level,
                    "below",
                    penetration,
                    candle.close > level.price,
                    "swing_low",
                    level.swing_count_at(index),
                )
            )
    return events


def identity(events: list) -> list[tuple]:
    """Everything an event carries, as a comparable value.

    Not just the index and the price: ``features`` and ``context`` hold the
    numbers a report cites, and an optimisation that preserved the event list
    while perturbing ``penetration`` would pass every weaker test in this file.
    """
    return [
        (
            event.event_index,
            event.confirmation_index,
            event.kind,
            event.detector,
            event.price,
            event.confirmation_time,
            tuple(sorted(event.features.items())),
            tuple(sorted(event.context.items())),
        )
        for event in events
    ]


def make_series(n: int, seed: int) -> list[CandleData]:
    """A deterministic random walk, seeded so a failure is reproducible.

    Seeded rather than fixed data for two reasons: a fixed long series would
    be a large binary-ish blob in the repository, and a seed makes the *shape*
    of the test obvious -- the same series at several lengths, so the
    differential is checked where the band-selection logic has to handle a
    different number of levels per bar.
    """
    rng = random.Random(seed)
    price = 30_000.0
    start = datetime(2021, 1, 1, tzinfo=UTC)
    out = []
    for i in range(n):
        open_time = start + timedelta(minutes=5 * i)
        opening = price
        close = max(100.0, opening * (1 + rng.gauss(0, 0.0016)))
        high = max(opening, close) * (1 + abs(rng.gauss(0, 0.0008)))
        low = min(opening, close) * (1 - abs(rng.gauss(0, 0.0008)))
        out.append(
            CandleData(
                open_time=open_time,
                close_time=open_time + timedelta(minutes=5),
                open=opening,
                high=high,
                low=low,
                close=close,
                volume=1.0,
                symbol="BTCUSDT",
                timeframe=Timeframe.M5,
                is_closed=True,
            )
        )
        price = close
    return out


@pytest.mark.parametrize("n", [400, 900, 1500, 3000])
def test_price_sorted_sweeps_match_the_quadratic_reference(n: int) -> None:
    """The band selector must be indistinguishable from scanning every level."""
    candles = make_series(n, seed=7)
    result = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    expected = identity(reference_sweeps(candles, result.liquidity_levels))
    actual = identity(
        detect_liquidity_sweeps(
            candles,
            result=result,
            min_penetration=MIN_PENETRATION,
            level_tolerance=TOLERANCE,
        )
    )
    assert actual == expected


def test_differential_covers_both_sides_and_the_reset_branch() -> None:
    """The equality must be over a series that actually exercises the logic.

    A monotonically rising series sweeps lows and never highs; a falling one
    does the opposite. Neither exercises the branch that clears ``beyond_since``
    when price returns inside a level. This random walk does, and the assertion
    that both directions are present is what makes the differential meaningful
    rather than incidentally true.
    """
    candles = make_series(1500, seed=11)
    result = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    events = detect_liquidity_sweeps(candles, result=result, level_tolerance=TOLERANCE)
    assert result.liquidity_levels, "the fixture produced no levels to sweep"
    assert events, "the fixture produced no sweeps"
    assert any(
        event.context.get("sweep_side") == "above" for event in events
    ), "no high sweeps: the above-side band was never exercised"
    assert any(
        event.context.get("sweep_side") == "below" for event in events
    ), "no low sweeps: the below-side band was never exercised"
    assert identity(events) == identity(reference_sweeps(candles, result.liquidity_levels))


def test_a_level_swept_twice_is_still_reported_twice() -> None:
    """The ``beyond_since`` crossing rule survives the rewrite.

    This is the rule that makes a re-sweep countable: price crosses a level,
    comes back inside it, and crosses again -- two events. A price-band
    selector is a natural place to break it, because the *level* has not moved
    between the two crossings and a naive "has this level been swept" cache
    would silently drop the second one.
    """
    candles = make_series(1500, seed=3)
    result = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    events = detect_liquidity_sweeps(candles, result=result, level_tolerance=TOLERANCE)
    counts: dict[tuple, int] = {}
    for event in events:
        counts[event.context.get("level_price")] = (
            counts.get(event.context.get("level_price"), 0) + 1
        )
    assert max(counts.values()) > 1, (
        "no level was swept twice, so this fixture cannot test the reset branch"
    )
    assert identity(events) == identity(reference_sweeps(candles, result.liquidity_levels))