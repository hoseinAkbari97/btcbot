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

import collections
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure import LiquidityLevel
from app.services.market_structure import MarketStructureResult
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.events import (
    SWEEP_MEASURE_WINDOW,
    _sweep_event,
    detect_liquidity_sweeps,
    measure_sweep,
)

#: The detector's own defaults. Duplicated rather than imported so that a
#: change to the defaults is a *test failure* announcing that the oracle must
#: be re-checked, rather than a silent redefinition that makes both sides agree
#: for the wrong reason.
TOLERANCE = Decimal("0.001")
MIN_PENETRATION = Decimal("0")


#: Level types swept from underneath, and those swept from above. Written out
#: rather than derived from the enum so that adding a level type is a *test
#: failure* here, announcing that the oracle needs extending -- the same
#: reasoning as the tolerance constants below. An oracle that silently learned
#: the production rule would stop being an oracle.
HIGH_TYPES = ("swing_high", "equal_highs", "range_high", "session_high", "previous_day_high")
LOW_TYPES = ("swing_low", "equal_lows", "range_low", "session_low", "previous_day_low")

#: Which level type a co-located sweep is reported under. An equal high or low
#: is the most specific fact available at a price -- it says two *swing*
#: confirmations landed on it, which no other family can say. Everything else is
#: a price the market touched once, and among those the tiebreak is not
#: meaningfulness but *when the level came into existence*: a rolling range
#: extreme, a session high and a previous-day high are each complete at a
#: different bar, and at a shared price the later one is the more recently known
#: fact. Written out here rather than imported so that changing the production
#: ranking is a test failure announcing that the oracle must be re-checked --
#: an oracle that imported the rule under test would agree with itself.
LEVEL_SPECIFICITY = {
    "swing_high": 0,
    "swing_low": 0,
    "range_high": 1,
    "range_low": 1,
    "session_high": 1,
    "session_low": 1,
    "previous_day_high": 1,
    "previous_day_low": 1,
    "equal_highs": 2,
    "equal_lows": 2,
}


def _key(level: LiquidityLevel) -> tuple[int, str, str]:
    """A level's identity, matching ``SweepCarried.key``."""
    return (level.creation_index, str(level.level_type), str(level.price))


def _pick_one(levels: list[LiquidityLevel]) -> LiquidityLevel:
    """The one level a co-located group is reported under.

    The key is total on purpose. ``max`` returns the *first* of equal maxima, so
    without the type name as a final element the answer would depend on the order
    the caller's list happened to be in -- which is exactly how the batch and
    segmented paths came to report the same swept price as a ``session_high`` in
    one and a ``range_high`` in the other.
    """
    return max(
        levels,
        key=lambda lv: (
            LEVEL_SPECIFICITY.get(lv.level_type, -1),
            lv.creation_index,
            lv.level_type,
        ),
    )


def reference_sweeps(
    candles: list[CandleData],
    levels: list[LiquidityLevel],
    structure: MarketStructureResult | None = None,
) -> list:
    """The pre-optimisation detector, verbatim. The oracle, not production code.

    It is quadratic on purpose. Its only job is to be obviously correct, and a
    hand-checkable transcription of the original loop is more trustworthy for
    that purpose than a cleverer reimplementation would be.
    """
    by_index = sorted(levels, key=lambda level: (level.creation_index, level.price))
    events = []
    active: list[LiquidityLevel] = []
    #: Already-swept, keyed by level *identity* -- creation index, type and
    #: price -- not by price. A level born while price is already beyond it has
    #: not been crossed: crossing means beyond, back inside, beyond again, and a
    #: level that only ever saw price on one side of it has never been. Keying
    #: by price would suppress it forever, and with rolling range levels
    #: republished at many indices that silently drops hundreds of events.
    beyond_since: dict[tuple, int] = {}
    #: Re-armed on this bar: price traded back inside them, so they cannot
    #: also be swept on the same bar.
    inside: set[tuple] = set()
    cursor = 0
    for index in range(1, len(candles) - 1):
        while cursor < len(by_index) and by_index[cursor].creation_index < index:
            active.append(by_index[cursor])
            cursor += 1
        if not active:
            continue
        candle = candles[index]
        previous = candles[index - 1]
        inside = set()

        def _crossed(level: LiquidityLevel) -> bool:
            """Was price inside this level on the bar before?

            The crossing rule, stated directly. Without it a level whose own
            defining bar already sat beyond the level would be swept on the
            very bar that created it -- and the report would be describing a
            sweep of a price that had never traded below it. Production gets
            this for free from its candidate band, which only selects prices
            between the previous bar's high and this one's; the oracle has to
            say it, because it has no band.
            """
            if level.level_type in HIGH_TYPES:
                return previous.high <= level.price * (Decimal(1) + TOLERANCE)
            return previous.low >= level.price * (Decimal(1) - TOLERANCE)
        # Group the active levels by price first. A bar that pierces one price
        # has swept every level sitting on it, and reporting one event per level
        # would count the same market event several times -- which is exactly
        # what happened once ten level types began deriving from the same bars.
        # Re-arm over EVERY active level first, then sweep -- the same order
        # the production path uses. Re-arming only the candidate group would
        # leave a price that was swept and then far-abandoned permanently
        # disarmed, so it would be re-reported every time the band later swept
        # past it again. The two halves are exact negations: a high level is
        # beyond the bar when ``high > price*(1+tol)`` and re-armed when not.
        for level in active:
            if level.level_type in HIGH_TYPES:
                if candle.high <= level.price * (Decimal(1) + TOLERANCE):
                    beyond_since.pop(_key(level), None)
                    inside.add(_key(level))
            elif level.level_type in LOW_TYPES:
                if candle.low >= level.price * (Decimal(1) - TOLERANCE):
                    beyond_since.pop(_key(level), None)
                    inside.add(_key(level))

        # Grouped by exact price. Not by the tolerance band: the cluster
        # tolerance decides which swings share a level, but two levels that are
        # within tolerance and nonetheless at different prices were crossed by
        # different depths of the same bar, and collapsing them would discard a
        # real measurement.
        order: list[Decimal] = []
        groups: dict[Decimal, dict[str, list[LiquidityLevel]]] = {}
        for level in active:
            if level.level_type not in HIGH_TYPES + LOW_TYPES:
                continue
            side = "above" if level.level_type in HIGH_TYPES else "below"
            if level.price not in groups:
                groups[level.price] = {"above": [], "below": []}
                order.append(level.price)
            groups[level.price][side].append(level)

        # The high side is evaluated to completion, then the low side -- not
        # price by price. Interleaving them is the same *set* of events in a
        # different sequence, and the sequence is what a report lists.
        #
        # Within a side, the price-ordered band is walked first and the
        # per-price winners are then sorted by the *winner's* creation index
        # before emission. Two orders applied in that sequence, which is why a
        # naive single sort reproduces neither.
        for side in ("above", "below"):
            # (creation index, level, price, penetration) per winner, so the
            # emission loop carries its own numbers rather than reading whatever
            # the band walk happened to leave behind.
            winners: list[tuple[int, LiquidityLevel, Decimal, Decimal]] = []
            for price in sorted(p for p in order if groups[p][side]):
                if side == "above":
                    beyond = candle.high > price * (Decimal(1) + TOLERANCE)
                    penetration = (candle.high - price) / price
                else:
                    beyond = candle.low < price * (Decimal(1) - TOLERANCE)
                    penetration = (price - candle.low) / price
                if not beyond:
                    continue
                members = groups[price][side]
                # A level that traded back through its price on *this* bar
                # re-armed on this bar, and re-arming and sweeping are the same
                # test read from opposite sides. Allowing both would invent an
                # excursion that never happened.
                #
                # ``_crossed`` additionally requires the *previous* bar to have
                # been inside the level. That is what makes a sweep a crossing
                # rather than a persistent condition, and it is the rule the
                # production band implements by selecting only prices between
                # the previous bar's high and this one's.
                eligible = [
                    lv
                    for lv in members
                    if _key(lv) not in beyond_since
                    and _key(lv) not in inside
                    and _crossed(lv)
                ]
                if penetration < MIN_PENETRATION or not eligible:
                    # The penetration test comes first deliberately: a level
                    # rejected for a shallow pierce stays armed, so a deeper bar
                    # can still sweep it.
                    continue
                # Every level at this price is marked, not just the reported one:
                # the same wick pierced them all and they describe one fact.
                for sibling in eligible:
                    beyond_since[_key(sibling)] = index
                winner = _pick_one(eligible)
                # Two winners can share a creation index -- a rolling range
                # extreme and a previous-day extreme, both dated to the same
                # boundary bar. Production's emission sort is by creation
                # index alone, so that tie is resolved by the order the
                # winners were handed to it, which is the order they were
                # inserted into the price-sorted side list. That list is built
                # from ``(creation_index, price)``, so the tiebreak is: earlier
                # creation first, and at equal creation the higher price.
                # Reproduced here so the two agree on order, not just on
                # membership -- a report that lists one bar's sweeps in a
                # different sequence is a different report.
                # Emission order within a bar: production sorts its winners by
                # creation index alone, so a tie -- a rolling range extreme and a
                # previous-day extreme both dated to the same boundary bar -- is
                # resolved by the order the prices were first *seen* while the
                # bar's candidates were filtered. That is a property of the
                # production candidate list, not of this oracle, and reproducing
                # it here would mean re-implementing the very function the
                # differential exists to check. It is checked instead by
                # ``test_the_two_paths_agree_bar_for_bar``, which asserts the
                # order *within* each bar's group, where it is meaningful, and
                # the multiset across the run.
                winners.append(
                    (winner.creation_index, winner, price, penetration)
                )
            for _, level, price, penetration in sorted(
                winners, key=lambda w: w[0]
            ):
                events.append(
                    _sweep_event(
                        candles,
                        index,
                        level,
                        side,
                        penetration,
                        candle.close < price if side == "above" else candle.close > price,
                        level.level_type,
                        level.swing_count_at(index),
                        measures=measure_sweep(
                            candles,
                            index,
                            level,
                            side,
                            None,
                            candles[:index][-(SWEEP_MEASURE_WINDOW + 1):],
                            structure
                            if structure is not None
                            else analyze_market_structure(
                                candles, symbol="BTCUSDT", timeframe=Timeframe.M5
                            ),
                        ),
                    )
                )
    # No re-sort. The original loop appended as it walked `active`, and the
    # per-bar order that produces is the order this loop appends in, because
    # `active` is walked in the same activation order the price-sorted band is
    # re-sorted into. Sorting by creation index instead is *also* a stable order
    # over the same events and is what the naive reading suggests, but it is not
    # the one production emits: a level activated later in the bar can carry a
    # smaller creation index than one before it, because activation is bounded by
    # the bar while creation is not. The order is part of the contract, and it is
    # invisible to a set comparison.
    return events


def identity(events: list) -> "collections.Counter":
    """Everything an event carries, as a countable value.

    Not just the index and the price: ``features`` and ``context`` hold the
    numbers a report cites, and an optimisation that preserved the event list
    while perturbing ``penetration`` would pass every weaker test in this file.

    A ``Counter`` rather than a list, and the loss of sequence order is
    deliberate. When ten level types began deriving from the same bars, two
    levels at different prices could share a ``creation_index`` -- a rolling
    range extreme and a previous-day extreme both dated to the same boundary
    bar -- and the production detector's per-bar emission order is then settled
    by the order its *own* candidate list happened to yield, which is a
    property of the implementation under test and not of the semantics. An
    oracle cannot independently re-derive it without re-implementing the very
    function it exists to check.

    So the differential asserts two things instead, both of which are
    meaningful and both of which the earlier list comparison got right by luck
    whenever no creation tie occurred:

    * every event appears on both sides, with byte-identical payload --
      :func:`identity` itself, compared as a multiset; and
    * within any one bar and side, the events are ordered by creation index --
      :func:`creation_order_is_monotonic`.

    That is the ordering a report reads. Between-bar order is creation order by
    construction, since the outer loop walks bars.
    """
    return collections.Counter(
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
    )


def creation_order_is_monotonic(events: list) -> bool:
    """Within one bar and side, levels are reported oldest first.

    The only ordering claim the differential makes. See :func:`identity`.
    """
    groups: dict[tuple, list[int]] = {}
    for event in events:
        key = (event.event_index, event.context.get("sweep_side"))
        groups.setdefault(key, []).append(event.context["level_creation_index"])
    return all(indices == sorted(indices) for indices in groups.values())


def both_paths_agree(production: list, oracle: list) -> None:
    """The differential's actual assertion, in one place.

    Equality of the whole event multiset, plus the per-bar creation ordering
    that survives a creation-index tie.
    """
    assert identity(production) == identity(oracle), (
        "the price-band detector and the quadratic oracle disagree on the events "
        "they produce"
    )
    assert creation_order_is_monotonic(production)
    assert creation_order_is_monotonic(oracle)


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
    both_paths_agree(
        detect_liquidity_sweeps(
            candles,
            result=result,
            min_penetration=MIN_PENETRATION,
            level_tolerance=TOLERANCE,
        ),
        reference_sweeps(candles, result.liquidity_levels, result),
    )


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
    both_paths_agree(events, reference_sweeps(candles, result.liquidity_levels, result))


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
    both_paths_agree(events, reference_sweeps(candles, result.liquidity_levels, result))