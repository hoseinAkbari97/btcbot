"""Causality of the liquidity model, asserted as invariance rather than intent.

Every other test in this area checks that a level or a sweep has the right
*shape*. These check the one property that, if violated, makes every shape
meaningless: that nothing downstream of bar ``n`` can change a statement dated
at or before bar ``n``.

The property is stated three ways, deliberately, because they fail differently:

* **prefix invariance** -- truncating the data leaves the surviving prefix's
  events byte-identical. This is the formulation that catches a *widening*
  window, a rolling max, a median fit on the whole sample.
* **future mutation** -- rewriting bars after the event leaves the event's own
  fields unchanged, including the ones measured at its confirmation index. This
  catches a measurement that reads one bar too far while looking fine at
  truncation time, and it is the only one of the three that can pin *which*
  field leaked.
* **confirmation timing** -- every event is confirmed at or after it occurred,
  and no event is confirmed before the information it reports exists.

Duplicates and lifecycle are included because both are ways the two leak
families hide: a level merged by price can merge one created now with one created
much later, and a level that stays active after being swept can be reported
again off a stale "already swept" set.

Nothing here is fitted to BTC. The fixtures are seeded so a failure reproduces.
"""

from __future__ import annotations

import copy
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure.analysis import analyze_market_structure
from app.services.research.events import (
    detect_liquidity_sweeps,
    measure_sweep,
)

TOLERANCE = Decimal("0.001")


def make_series(n: int, seed: int = 17) -> list[CandleData]:
    """A deterministic walk with fat wicks, so sweeps actually happen.

    Fat relative to the body on purpose: the sweep detector needs a bar whose
    wick crosses a level and whose body closes back inside it, and a walk with
    small wicks produces so few of those that an invariance test over them
    passes on an empty set.
    """
    rng = random.Random(seed)
    price = 30_000.0
    start = datetime(2021, 1, 1, tzinfo=UTC)
    out: list[CandleData] = []
    for i in range(n):
        open_time = start + timedelta(minutes=5 * i)
        close = max(100.0, price * (1 + rng.gauss(0, 0.0018)))
        high = max(price, close) * (1 + abs(rng.gauss(0, 0.0012)))
        low = min(price, close) * (1 - abs(rng.gauss(0, 0.0012)))
        out.append(
            CandleData(
                open_time=open_time,
                close_time=open_time + timedelta(minutes=5, milliseconds=-1),
                open=price,
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


def sweeps(candles: list[CandleData]):
    result = analyze_market_structure(candles, symbol="BTCUSDT", timeframe=Timeframe.M5)
    return detect_liquidity_sweeps(
        candles, result=result, level_tolerance=TOLERANCE
    )


def fingerprint(events) -> list[tuple]:
    """Everything an event carries, order-insensitive but value-exact.

    A ``Decimal`` that drifted from 0.5 to 0.5000000001 must fail here, so the
    features are not rounded on the way through.
    """
    return sorted(
        (
            event.event_index,
            event.confirmation_index,
            event.event_time,
            event.confirmation_time,
            event.kind,
            event.detector,
            str(event.price),
            tuple(sorted((k, str(v)) for k, v in event.features.items())),
            tuple(sorted((k, str(v)) for k, v in event.context.items())),
        )
        for event in events
    )


N = 2500


# ===========================================================================
# Prefix invariance
# ===========================================================================


@pytest.mark.parametrize("cut", [900, 1400, 2000, 2400])
def test_truncating_the_future_leaves_the_past_unchanged(cut: int) -> None:
    """Cutting the series cannot change an event dated inside it.

    The strongest of the three formulations, because it does not care *how* a
    leak happened: a wider window, a global max, a fitted scaler, a state
    variable left at a final value -- all of them show up here as a changed
    field on an event whose index did not move.

    The comparison stops one bar before the cut, since a sweep on the final bar
    of a prefix is legitimately incomplete: its confirmation bar is the one the
    truncation removed, and the code is explicit that it falls back rather than
    claiming a bar nobody has seen. That is checked on its own below.
    """
    full = make_series(N)
    partial = make_series(N)[:cut]

    full_early = [e for e in sweeps(full) if e.event_index <= cut - 3]
    part_all = sweeps(partial)

    assert full_early, "the fixture produced no early sweeps; the test is vacuous"
    assert fingerprint(full_early) == fingerprint(
        [e for e in part_all if e.event_index <= cut - 3]
    ), "truncating the series changed an event dated before the cut"


def test_a_sweep_on_the_last_bar_is_reported_rather_than_dropped() -> None:
    """Truncation may *incomplete* a boundary event; it may not erase it.

    The complement of the test above. A detector that simply skipped the last
    bar would pass prefix invariance cleanly while silently dropping one sweep
    per segment in the segmented runner -- a systematic loss exactly at every
    boundary, which is where the previous defects were found.

    Checked on the event builder rather than by fishing for a sweep on the
    second-to-last bar of a random walk, because whether one happens to land
    there is a property of the fixture, not of the code. What has to hold is
    the rule: a sweep on the final bar present is emitted with its
    confirmation falling back to that same bar, never clamped to a bar past the
    end of the data.
    """
    from app.services.market_structure import LiquidityLevel
    from app.services.research.events import _sweep_event

    candles = make_series(50)
    level = LiquidityLevel(
        price=candles[-1].high / 2,
        level_type="swing_high",
        origin="swing",
        first_seen=candles[0].open_time,
        last_seen=candles[0].open_time,
        creation_index=0,
        creation_time=candles[0].close_time,
        touch_count=1,
        strength=1.0,
    )
    last = len(candles) - 1
    event = _sweep_event(candles, last, level, "above", Decimal("0.001"), True, "swing_high")
    assert event.event_index == last
    assert event.confirmation_index == last, (
        "with no bar after the pierce, the confirmation must fall back to the "
        "pierce bar rather than name a bar that does not exist"
    )
    assert event.confirmation_time == candles[last].close_time

    # And the same rule one bar earlier: there the next bar *does* exist, so it
    # is the confirmation.
    event = _sweep_event(candles, last - 1, level, "above", Decimal("0.001"), True, "swing_high")
    assert event.confirmation_index == last


# ===========================================================================
# Future mutation
# ===========================================================================


def test_rewriting_bars_after_an_event_leaves_that_event_untouched() -> None:
    """Replace the tail with something violent; the prefix's events must not move.

    Complements prefix invariance by being *local*: it does not shorten the
    data, so it cannot pass by accident on an event that merely fell out. And
    because the tail is made to cross every level in sight, a measurement that
    reads even one bar past its confirmation would be reading the injected
    spike rather than the market.
    """
    base = make_series(N, seed=23)
    mutated = list(base)
    # From bar 1500 on, drive the price to a fixed extreme far outside the whole
    # earlier range. Anything reading past its confirmation lands in this.
    tail_start = 1500
    extreme = Decimal("1")
    for i in range(tail_start, len(mutated)):
        mutated[i] = base[i].model_copy(
            update={
                "open": extreme,
                "high": extreme * 2,
                "low": extreme / 2,
                "close": extreme,
            }
        )

    before_events = [e for e in sweeps(base) if e.event_index < tail_start - 3]
    after_events = [
        e for e in sweeps(mutated) if e.event_index < tail_start - 3
    ]
    assert before_events, "the fixture produced no pre-tail sweeps"
    assert fingerprint(before_events) == fingerprint(after_events), (
        "an event dated before the tail changed when the tail was rewritten"
    )


def test_each_measured_field_is_individually_covered() -> None:
    """The mutation test above is only as good as the set of fields it compares.

    If a future field were added to ``features`` and this fingerprint did not
    include it, the invariance would be asserted over the wrong surface. So the
    names are pinned here, and a field added without a decision about its
    window fails the test rather than passing unnoticed.
    """
    events = sweeps(make_series(1500, seed=29))
    assert events, "no sweeps on the fixture"
    keys = set(events[0].features) | {
        k for e in events for k in e.features
    }
    expected = {
        "level_price",
        "penetration",
        "penetration_percent",
        "swept_side",
        "level_age_bars",
        "level_touch_count",
        "level_strength",
        "level_swing_count",
        "time_above",
        "time_below",
        "recovery_ratio",
        "wick_ratio",
        "volume",
        "volatility",
    }
    assert expected <= keys, f"features missing from sweeps: {sorted(expected - keys)}"
    assert keys == expected, (
        f"unexpected features on a sweep: {sorted(keys - expected)} -- every one "
        f"of them needs a stated window before it can be checked for leakage"
    )


# ===========================================================================
# Confirmation timing
# ===========================================================================


def test_no_sweep_is_confirmed_before_it_occurred() -> None:
    candles = make_series(N)
    for event in sweeps(candles):
        assert event.confirmation_index > event.event_index, (
            f"sweep at bar {event.event_index} claims to be confirmed at "
            f"{event.confirmation_index}, at or before it happened"
        )
        assert event.confirmation_time > event.event_time


def test_a_sweep_is_confirmed_exactly_one_bar_after_the_pierce() -> None:
    """The two-bar definition, asserted rather than described.

    A sweep is a pierce plus the knowledge that the bar closed back. The first
    is knowable intrabar and the second only at the close, so the two indices
    differ by one -- never zero (which would let a trader act on the same bar
    that produced the wick) and never more (which would silently delay every
    event and flatter the forward returns).
    """
    for event in sweeps(make_series(N)):
        assert event.confirmation_index == event.event_index + 1


def test_no_measurement_reads_past_the_confirmation_bar() -> None:
    """The window of every measured field ends at or before confirmation.

    ``time_above`` / ``time_below`` are the trap: they invite an excursion
    window, and an excursion window is a reading of the future. What is checked
    is the observable consequence -- over a series whose bars after confirmation
    are rewritten to sit entirely on one side of the level, the counts must not
    move.
    """
    base = make_series(N, seed=31)
    levels_result = analyze_market_structure(base, symbol="BTCUSDT", timeframe=Timeframe.M5)
    level = levels_result.liquidity_levels[len(levels_result.liquidity_levels) // 2]

    # Bar 200 is the pierce; 201 is its confirmation, and both fields are
    # legitimately read there -- recovery is the confirmation close's distance
    # from the level, so rewriting it would test nothing. The rewrite therefore
    # starts at 202, the first bar past the confirmation.
    ahead = list(base)
    for i in range(202, len(ahead)):
        c = ahead[i]
        ahead[i] = c.model_copy(update={"close": c.low * Decimal("0.5")})
    behind = list(base)
    for i in range(202, len(behind)):
        c = behind[i]
        behind[i] = c.model_copy(update={"close": c.high * Decimal("1.5")})

    args = dict(side="above", excursion_bars=None, structure=levels_result)
    a = measure_sweep(ahead, 200, level, before=ahead[:200], **args)
    b = measure_sweep(behind, 200, level, before=behind[:200], **args)
    # The window is the single bar 201 -- the confirmation, which both variants
    # leave alone -- and both rewrites are large enough to reverse whichever
    # side it happens to sit on. So the counts must be identical in all three
    # series, and identical to the unmutated baseline rather than merely to each
    # other: two runs that agreed because they both read the same wrong bar
    # would satisfy the weaker comparison.
    plain = measure_sweep(
        base, 200, level, before=base[:200], **args
    )
    assert a.time_above == b.time_above == plain.time_above
    assert a.time_below == b.time_below == plain.time_below
    assert a.recovery_ratio == b.recovery_ratio, (
        "recovery is measured at the confirmation bar's close, so it must not "
        "depend on what later bars do"
    )


# ===========================================================================
# Duplicates
# ===========================================================================


def test_levels_at_one_price_are_merged_not_republished() -> None:
    """A price is a level; a fact about it is published once.

    Two identical levels would make every sweep of that price ambiguous --
    which one was swept -- and would double-count one market event. So the
    duplicate count is asserted, not the merge policy: the code may merge by
    identity or by price, but it must not leave two identical levels active on
    the same bar.
    """
    candles = make_series(N, seed=37)
    levels = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5
    ).liquidity_levels

    seen: dict[tuple[int, str, str], int] = {}
    for level in levels:
        key = (level.creation_index, str(level.level_type), str(level.price))
        seen[key] = seen.get(key, 0) + 1
    duplicated = {k: v for k, v in seen.items() if v > 1}
    assert not duplicated, (
        f"{len(duplicated)} levels were published more than once under the same "
        f"identity, e.g. {duplicated and next(iter(duplicated))}"
    )


def test_a_co_located_sweep_is_reported_once_not_once_per_level() -> None:
    """One wick through one price is one market event.

    With ten level types deriving from the same bars, a price can carry a
    session high, a previous-day high and a range high simultaneously. Three
    levels, one pierce. The detector reports one event under the most specific
    of them; what this asserts is that it reports exactly one.
    """
    events = sweeps(make_series(N, seed=41))
    assert events
    by_bar_and_price: dict[tuple, int] = {}
    for event in events:
        key = (event.event_index, event.features.get("level_price"), event.context.get("sweep_side"))
        by_bar_and_price[key] = by_bar_and_price.get(key, 0) + 1
    assert max(by_bar_and_price.values()) == 1, (
        "a single bar and price reported two sweeps; that is one market event "
        "counted twice"
    )


def test_one_sweep_event_names_exactly_one_level_type() -> None:
    """The winner is chosen, not left ambiguous.

    A co-located sweep is reported under a single type, and the choice is by a
    stated rule (specificity, then recency) rather than by whatever order the
    candidates happened to arrive in.
    """
    events = sweeps(make_series(N, seed=41))
    for event in events:
        assert isinstance(event.context.get("level_type"), str)
        assert event.detector == f"sweep:{event.context['level_type']}"


# ===========================================================================
# Lifecycle
# ===========================================================================


def test_a_swept_level_stays_swept_while_price_remains_beyond_it() -> None:
    """Persistence is not a crossing.

    A level already beyond price is not swept again on the next bar. Without
    this the same excursion would be counted once per bar it lasts, and an
    excursion's *duration* -- one of the things a reader would draw a conclusion
    from -- would be an artefact of the detector.
    """
    candles = make_series(N, seed=43)
    events = sweeps(candles)
    by_level: dict[tuple, list[int]] = {}
    for event in events:
        key = (
            event.context["level_creation_index"],
            event.features["level_price"],
        )
        by_level.setdefault(key, []).append(event.event_index)
    repeats = {k: v for k, v in by_level.items() if len(v) > 1}
    assert repeats, "no level was swept twice; the reset branch is untested here"
    for key, indices in repeats.items():
        # Consecutive indices would mean a persistent condition, not a crossing.
        for a, b in zip(indices, indices[1:]):
            assert b - a > 1, (
                f"level {key} was reported on consecutive bars {a} and {b}; a "
                f"single excursion lasting two bars is one event"
            )


def test_a_level_can_be_swept_again_after_price_returns_inside_it() -> None:
    """The other half: crossing, coming back, crossing again is two events.

    The pair of tests above is the whole lifecycle. Asserting only the first
    would pass on a detector that marks a level swept *forever*, which is
    exactly as wrong in the opposite direction -- it silently drops every
    re-sweep for the rest of the dataset.
    """
    events = sweeps(make_series(N, seed=43))
    by_level: dict[tuple, list[int]] = {}
    for event in events:
        key = (
            event.context["level_creation_index"],
            event.features["level_price"],
        )
        by_level.setdefault(key, []).append(event.event_index)
    assert any(len(v) > 1 for v in by_level.values()), (
        "no level was re-swept, so a permanent-swept detector would pass here"
    )


def test_a_level_is_never_swept_on_or_before_the_bar_that_formed_it() -> None:
    """The creation bound, asserted through the event log.

    ``creation_index < event_index`` is the filter the detector applies, and it
    is what makes the level's own defining bar incapable of sweeping it. Read
    off the events rather than the levels, because that is where a defect
    would actually surface.
    """
    candles = make_series(N, seed=47)
    events = sweeps(candles)
    assert events
    for event in events:
        assert event.event_index > event.context["level_creation_index"], (
            f"a level created at bar {event.context['level_creation_index']} was "
            f"swept on bar {event.event_index}"
        )


def test_level_age_is_never_negative_and_counts_from_creation() -> None:
    for event in sweeps(make_series(1200, seed=53)):
        age = event.features["level_age_bars"]
        assert age is not None and age >= 0
        assert age == Decimal(event.event_index - event.context["level_creation_index"])


def test_reflecting_prices_reflects_the_ratio_measurements() -> None:
    """A ratio of differences is invariant under negation; an absolute one is not.

    ``penetration`` is ``(high - level) / level`` for a high swept from
    underneath. Negating every price turns a high sweep into a low sweep and
    leaves the *ratio* unchanged, while any measurement taken as a raw price
    distance -- or any side decided against a constant rather than against the
    level -- comes out sign-flipped or different.

    Run per level on a hand-built pair of bars rather than over two independent
    analyses. Reflecting a whole random walk produces a different set of levels
    (a swing high above zero is a swing low below it, but the *tolerance band*
    around every level moves with the negation), so the two runs do not share
    event bars and comparing them bar-for-bar would be comparing two different
    markets. The question being asked is narrower -- does one sweep's
    measurement depend on the sign of the prices -- and that needs only one
    sweep.
    """
    from app.services.market_structure import LiquidityLevel
    from app.services.research.events import measure_sweep

    candles = make_series(60)
    level_price = Decimal("31000")

    def bar(open_time, o, h, low, c):
        return make_candle(
            open_time,
            open_price=str(o),
            high=str(h),
            low=str(low),
            close=str(c),
        )

    def level(price):
        return LiquidityLevel(
            price=price,
            level_type="swing_high",
            origin="swing",
            first_seen=candles[0].open_time,
            last_seen=candles[0].open_time,
            creation_index=0,
            creation_time=candles[0].close_time,
            touch_count=1,
            strength=1.0,
        )

    bars = [bar(0, 30_500, 30_900, 30_200, 30_400), bar(300, 30_400, 31_620, 30_300, 30_600)]

    up = measure_sweep(bars, 1, level(level_price), "above", None, bars[:1], analyze_market_structure(bars, symbol="BTCUSDT", timeframe=Timeframe.M5))

    reflected = [bar(0, -30_500, -30_200, -30_900, -30_400), bar(300, -30_400, -30_300, -31_620, -30_600)]
    down = measure_sweep(reflected, 1, level(-level_price), "below", None, reflected[:1], analyze_market_structure(reflected, symbol="BTCUSDT", timeframe=Timeframe.M5))

    # Penetration is normalised by a *signed* level price, so negation flips
    # its sign along with the direction of travel. That is the intended
    # behaviour -- a sweep reported as a fraction of the level it pierced, and
    # the level here is negative -- and it is asserted, because a measurement
    # that instead reported a positive depth on a downward sweep would be
    # claiming a penetration that went the other way.
    assert up.penetration == -down.penetration
    assert up.penetration == Decimal("0.02")
    assert up.penetration_percent == -down.penetration_percent
    assert up.wick_ratio == down.wick_ratio
    assert up.range == down.range
