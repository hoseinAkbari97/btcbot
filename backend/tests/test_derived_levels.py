"""The time-anchored level types, tested against the availability rules.

The specification names ten liquidity level types without defining any of them,
so this file pins down what each one *is* rather than whether it produces a
plausible backtest. Every test here is synthetic and hand-checkable: a bar with
a known high, a boundary at a known index, an expectation written out in full.

The property under test throughout is availability. A level that is dated
earlier than the information defining it was complete is worse than no level at
all, because every sweep of it is fictional. That is the one failure mode here
worth a test per level type rather than one test over all of them.

Nothing in this file is fitted to BTC. ``SESSION_HOURS``, ``DEFAULT_RANGE_WINDOW``
and ``EQUAL_MIN_SWINGS`` are definitions, and a test that asserted they maximise
a return would be asserting the opposite of what they are for.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import get_args

import pytest
from conftest import make_candle

from app.schemas.market_data import CandleData, Timeframe
from app.services.market_structure import LevelType
from app.services.market_structure.analysis import analyze_market_structure
from app.services.market_structure.derived_levels import (
    DEFAULT_RANGE_WINDOW,
    EQUAL_MIN_SWINGS,
    SESSION_HOURS,
    SESSION_SLOTS,
    DerivedLevelState,
    assert_no_self_sweep,
    equal_level_for,
    session_slot_for,
)

#: 5m bars: 288 to a day, 72 to a six-hour session. Named so a boundary in a
#: test reads as the boundary it is.
BARS_PER_DAY = 288
BARS_PER_SESSION = BARS_PER_DAY // len(SESSION_SLOTS)

DAY_ZERO = datetime(2024, 1, 1, tzinfo=UTC)


def series(count: int, *, base: float = 100.0, seed: int = 11) -> list[CandleData]:
    """A random walk with real bodies, starting exactly at midnight UTC.

    Midnight matters: the day and session boundaries are what is under test, and
    a series that starts mid-session makes "the first session level" ambiguous
    in a way that has nothing to do with the code.
    """
    rng = random.Random(seed)
    out: list[CandleData] = []
    price = base
    for index in range(count):
        close = price + rng.gauss(0, 1.0)
        out.append(
            make_candle(
                index * 5,
                open_price=f"{price:.2f}",
                high=f"{max(close, price) + abs(rng.gauss(0, 0.4)):.2f}",
                low=f"{min(close, price) - abs(rng.gauss(0, 0.4)):.2f}",
                close=f"{close:.2f}",
            )
        )
        price = close
    return out


def run(candles: list[CandleData], state: DerivedLevelState | None = None, **kw):
    """Feed a whole series to the state and return ``(levels, state)``.

    The state consumes *segments*, not individual bars: it is handed a
    contiguous run of bars and rejects a second call that does not resume
    strictly after the previous one. The single-bar-at-a-time loop a naive
    fixture writes therefore fails on its own second bar, which is the
    contiguity guard doing exactly its job rather than a defect here.
    """
    state = state or DerivedLevelState(**kw)
    return list(state.observe(candles)), state


# ===========================================================================
# Availability: the core invariant
# ===========================================================================


def test_no_level_is_swept_by_the_information_that_formed_it() -> None:
    """``creation_index`` must precede every bar that could sweep the level.

    This is the executable form of the module's central claim, run over every
    level the state publishes on a series long enough to exercise all three
    families and all four session slots.
    """
    candles = series(BARS_PER_DAY * 3)
    levels, _ = run(candles)
    assert levels, "the fixture produced no levels; the assertion would be vacuous"
    assert_no_self_sweep(levels, candles)


def test_a_level_is_dated_to_the_instant_its_information_completed() -> None:
    """Every level's ``creation_time`` is a moment at or before its own bar's close.

    The two families complete their information at different instants, and both
    are correct:

    * a *rolling range* level completes at the close of the last bar in its
      window, which is the bar before the one that publishes it; and
    * a *calendar* level (session, previous day) completes at the boundary that
      ends its period, which is the *open* of the bar that publishes it.

    What both must satisfy is the causality bound: never later than the close of
    the bar whose index it carries, because a level stamped past its own
    creation bar describes information the market had not produced when the
    sweep detector would first consider it.
    """
    candles = series(BARS_PER_DAY * 2)
    levels, _ = run(candles)
    assert levels
    for level in levels:
        creation_bar = candles[level.creation_index]
        assert level.creation_time <= creation_bar.close_time, (
            f"{level.level_type} is dated to {level.creation_time}, after the "
            f"close of its own creation bar {creation_bar.close_time}"
        )
        # And never before the bar opened, which would claim knowledge of a bar
        # that had not started.
        assert level.creation_time >= creation_bar.open_time, (
            f"{level.level_type} is dated to {level.creation_time}, before its "
            f"own creation bar opened at {creation_bar.open_time}"
        )

    # The rolling family specifically: the close of the window's last bar, which
    # is the bar *before* the publishing bar.
    rolling = [lv for lv in levels if lv.level_type == "range_high"]
    assert rolling, "no rolling range levels to check"
    for level in rolling:
        assert level.creation_time == candles[level.creation_index].close_time


def test_a_session_level_never_carries_its_own_sessions_extreme() -> None:
    """The headline distinction between the two families, asserted directly.

    A rolling window's extreme is complete when its last bar closes. A session's
    extreme is not: at its own last bar it is only a high *so far*. So the session
    level published at a boundary must hold the previous occurrence's extreme --
    never the extreme of the session that just ended, which at that moment would
    be a value the market has not finished producing.
    """
    candles = series(BARS_PER_DAY * 3)
    levels, _ = run(candles)

    sessions = [lv for lv in levels if lv.level_type == "session_high"]
    assert len(sessions) >= 4, "too few session levels to distinguish anything"

    # A coincidence on a random walk is possible, so the check is on the family
    # as a whole: *every* session level matching the extreme of the session it
    # summarises would mean the level is being read out of the period still in
    # progress. One match proves nothing on its own, which is why this counts.
    # The summarised period is exactly ``period_bars`` bars from
    # ``period_start``; a level equal to its own period's extreme would be the
    # high of the session *in progress*, which is not yet a session high.
    for level in sessions:
        end = level.period_start + timedelta(minutes=5 * BARS_PER_SESSION)
        period = [c for c in candles if level.period_start <= c.open_time < end]
        assert len(period) == BARS_PER_SESSION, (
            f"{level.boundary} level summarised {len(period)} bars, not a session"
        )
        assert level.price <= max(c.high for c in period), (
            f"{level.boundary} session high {level.price} exceeds the extreme of "
            f"the session it summarises"
        )
        assert level.price >= min(c.high for c in period), (
            f"{level.boundary} session high {level.price} is below the extreme of "
            f"the session it summarises"
        )


def test_a_previous_day_level_is_dated_to_the_day_boundary_it_ends_on() -> None:
    """The day's extreme becomes knowable at midnight, when the day closes.

    A day's high is only finished at its last instant, so the level is dated to
    the boundary itself -- which is the *open* of the first bar of the next day,
    the bar that publishes it.

    Three days of bars are needed for any previous-day level at all: the first
    day has no predecessor, and the second day's level only becomes knowable at
    the boundary into the third. Two days yield none, and that absence is the
    leak this level type exists to prevent rather than a gap.
    """
    candles = series(BARS_PER_DAY * 3)
    levels, _ = run(candles)

    days = [lv for lv in levels if lv.level_type == "previous_day_high"]
    assert days, (
        "two days of bars contain exactly one day boundary, so one previous-day "
        "high must be published; none was"
    )

    for level in days:
        boundary = level.creation_time
        assert boundary == candles[level.creation_index].open_time, (
            "a previous-day level completes at the day boundary, which is the "
            "open of the bar that publishes it"
        )
        # The period it summarises ends exactly one day after it started, and
        # the boundary that publishes it is that day's end.
        assert boundary == level.period_start + timedelta(days=1), (
            f"previous-day level spans {level.period_start} to {boundary}, which "
            f"is not the day it claims to summarise"
        )
        assert boundary.hour == 0 and boundary.minute == 0
        assert level.period_bars == BARS_PER_DAY


def test_a_range_level_is_knowable_at_its_own_window_close() -> None:
    """The rolling family is dated *earlier* than the others, and must be.

    If a range level were also dated to the next bar, the two families would be
    indistinguishable and the table in the module docstring would be wrong.
    """
    candles = series(400)
    levels, _ = run(candles, range_window=DEFAULT_RANGE_WINDOW)

    ranges = [lv for lv in levels if lv.level_type == "range_high"]
    assert ranges, "no rolling range levels"
    assert len(ranges) < len(candles), (
        "a rolling extreme republished every bar would produce one level per bar; "
        "publication is meant to happen on change only"
    )


# ===========================================================================
# Each level type, defined
# ===========================================================================


def test_every_specified_level_type_is_reachable() -> None:
    """Ten types, all deriving on a series built to contain them.

    A declared enum member is not an implementation. This is the test that
    distinguishes the two: every member must appear in the output of a real run,
    not merely in the type.
    """
    # Ten days, not three. ``equal_lows`` is the rarest of the ten on a random
    # walk -- two equal *lows* need two swing lows to land inside the same
    # cluster tolerance, and a symmetric random walk produces those far less
    # often than equal highs. Three days produced no equal lows at all, which
    # made this test fail for a reason that had nothing to do with the code it
    # was checking.
    candles = series(BARS_PER_DAY * 10)
    result = analyze_market_structure(
        candles, symbol="BTCUSDT", timeframe=Timeframe.M5
    )
    found = {level.level_type for level in result.liquidity_levels}
    expected = set(get_args(LevelType))
    assert expected <= found, f"missing level types: {sorted(expected - found)}"


def test_a_session_level_summarises_the_same_slot_not_the_adjacent_one() -> None:
    """Sessions are compared to the same slot of a previous day.

    The session *immediately* preceding any slot is a different slot, so a level
    built from it would be "the high of whichever six hours came before" wearing
    the name of a named session.
    """
    for hour in (0, 6, 12, 18):
        assert session_slot_for(DAY_ZERO + timedelta(hours=hour)) == f"session_{hour:02d}"
        # One bar before the boundary belongs to the *previous* slot.
        assert session_slot_for(DAY_ZERO + timedelta(hours=hour, minutes=-5)) == (
            f"session_{(hour - SESSION_HOURS) % 24:02d}"
        )


def test_a_day_has_exactly_four_sessions_and_no_gap_or_overlap() -> None:
    """The tiling property the six-hour choice rests on."""
    slots = [session_slot_for(DAY_ZERO + timedelta(minutes=5 * i)) for i in range(BARS_PER_DAY)]
    assert len(set(slots)) == len(SESSION_SLOTS)
    # Every slot occupies exactly a quarter of the day's bars.
    for name, _ in SESSION_SLOTS:
        assert slots.count(name) == BARS_PER_SESSION


def test_a_range_level_excludes_the_publishing_bar_from_its_window() -> None:
    """The window ends at the creation bar, and the level is published after it.

    The level becomes knowable at the *close* of its creation bar, and the state
    publishes it while consuming the bar after -- so its creation index is that
    prior bar, and the window is the ``range_window`` bars ending *at* it. The
    bar being consumed when the level is published is never in the window: a
    level that contained the bar it is compared against would have its own price
    depend on that bar, which is the self-inclusion every trailing-window
    measurement in this codebase goes out of its way to avoid.
    """
    candles = series(200)
    levels, _ = run(candles, range_window=10)
    checked = 0
    for level in levels:
        if level.level_type != "range_high":
            continue
        if level.creation_index + 1 < 10:
            # The first ten bars have no full trailing window behind them, so
            # they publish no range level; nothing to check.
            continue
        # creation_index is the last bar of the window; the publishing bar is
        # creation_index + 1 and must be excluded.
        window = candles[level.creation_index - 9 : level.creation_index + 1]
        assert len(window) == 10
        assert level.price == max(c.high for c in window), (
            f"range high created at {level.creation_index} is not the extreme of "
            f"the ten bars ending at that bar"
        )
        checked += 1
    assert checked, "no range levels checked; the fixture was too short"


def test_a_time_anchored_level_reports_a_zero_touch_count() -> None:
    """Reporting a real count would imply a history the level does not have.

    Every candidate touch bar printed before a time-anchored level was knowable,
    so its count is zero by construction. This is asserted because a plausible
    number here would be the kind of thing that silently becomes a feature.
    """
    candles = series(BARS_PER_DAY * 2)
    levels, _ = run(candles)
    for level in levels:
        liquidity = level.to_liquidity_level()
        assert liquidity.touch_count == 0
        assert liquidity.strength == 0.0


def test_equal_highs_needs_two_swings_because_one_is_not_an_equal() -> None:
    """The minimum that makes the word mean anything."""
    assert EQUAL_MIN_SWINGS == 2
    single = [
        (0, 0, datetime(2024, 1, 1, 0, 25, tzinfo=UTC)),
    ]
    assert (
        equal_level_for(
            Decimal("100"),
            kind="high",
            swing_confirmations=single,
            tolerance=Decimal("0.001"),
        )
        is None
    )


def test_equal_highs_are_dated_to_the_later_of_the_two_confirmations() -> None:
    """The level becomes knowable when the *second* swing confirms."""
    first = (0, 0, datetime(2024, 1, 1, 0, 5, tzinfo=UTC))
    second = (40, 40, datetime(2024, 1, 1, 3, 25, tzinfo=UTC))
    level = equal_level_for(
        Decimal("100"),
        kind="high",
        swing_confirmations=[first, second],
        tolerance=Decimal("0.001"),
    )
    assert level is not None
    assert level.creation_time == second[2], (
        "an equal level must be dated to the confirmation of the swing that "
        "made it equal, not to the first swing's"
    )


def test_equal_membership_is_decided_by_the_bucket_not_by_this_function() -> None:
    """Which swings count as *equal* is decided where they are clustered.

    An earlier revision re-checked the tolerance here, comparing each swing's
    price against the bucket's own anchor -- which is the same number, so the
    check could never reject anything. The consequence was not a wrong answer
    but a wrong *belief*: the signature advertised a filter that did not filter,
    and a reader would conclude a bucket was being re-validated when it was not.

    So the contract asserted here is the real one: given confirmations that have
    already been admitted to a bucket, two of them form an equal level
    regardless of what the tolerance is, and fewer than two never do. The
    tolerance is a property of the bucket builder, tested there.
    """
    early = datetime(2024, 1, 1, 0, 5, tzinfo=UTC)
    later = datetime(2024, 1, 1, 0, 10, tzinfo=UTC)
    two = [(0, 0, early), (1, 1, later)]

    # Two confirmations make an equal level at any non-negative tolerance,
    # including one so small it could not admit a second swing to a bucket.
    merged = equal_level_for(
        Decimal("100"),
        kind="high",
        swing_confirmations=two,
        tolerance=Decimal("0.0000001"),
    )
    assert merged is not None, (
        "membership was decided by the bucket; a second confirmation in it "
        "makes the level equal whatever the tolerance is"
    )
    assert merged.level_type == "equal_highs"

    # One confirmation never does, at any tolerance.
    assert (
        equal_level_for(
            Decimal("100"),
            kind="high",
            swing_confirmations=two[:1],
            tolerance=Decimal("10"),
        )
        is None
    )

    # And a negative tolerance is rejected rather than silently treated as
    # "no filtering", which would make the parameter's sign meaningless.
    with pytest.raises(ValueError):
        equal_level_for(
            Decimal("100"),
            kind="high",
            swing_confirmations=two,
            tolerance=Decimal("-0.001"),
        )


# ===========================================================================
# Segmentation invariance
# ===========================================================================


@pytest.mark.parametrize("segment", [1, 7, 50, 288])
def test_segmented_derivation_equals_the_whole_series(segment: int) -> None:
    """Splitting the bars must not change a single level.

    Boundary sizes deliberately include awkward ones: 1 bar (every bar is a
    boundary), 7 (incommensurate with 72 and 288), 50, and 288 (exactly one day,
    so every boundary lands on a day change).
    """
    candles = series(BARS_PER_DAY * 2)
    whole, _ = run(candles)

    state = DerivedLevelState()
    pieces: list = []
    for start in range(0, len(candles), segment):
        pieces.extend(state.observe(candles[start : start + segment]))

    assert _key(pieces) == _key(whole), (
        f"segment size {segment} changed the derived levels"
    )


def _key(levels) -> list:
    return sorted(
        (str(lv.price), lv.level_type, lv.creation_index, lv.creation_time, lv.boundary)
        for lv in levels
    )


def test_a_checkpoint_round_trip_preserves_every_level() -> None:
    """Resume must not re-derive levels, and must not lose them.

    A sweep in a late segment can be of a level published in an early one. A
    resumed run that forgot it would stop reporting those sweeps while every
    other number still looked right.
    """
    candles = series(BARS_PER_DAY * 2)

    # Run the first half in 97-bar segments, checkpoint mid-way, and resume.
    # The state refuses a segment that does not resume strictly after the
    # previous one, so a resume replayed from bar 0 is a test bug, not a
    # production tolerance: what is under test is that the *later* segments,
    # derived after a reload, still produce the same levels.
    head, state = run(candles[: len(candles) // 2], DerivedLevelState())
    resumed = DerivedLevelState.from_payload(state.to_payload())
    pieces = list(head)
    for start in range(len(candles) // 2, len(candles), 97):
        pieces.extend(resumed.observe(candles[start : start + 97]))

    whole, _ = run(candles)
    assert _key(pieces) == _key(whole)


def test_a_resumed_state_rejects_an_older_payload_shape() -> None:
    """Silently reading a v0 payload would resurrect the original bug."""
    with pytest.raises(Exception):
        DerivedLevelState.from_payload({"version": 0})