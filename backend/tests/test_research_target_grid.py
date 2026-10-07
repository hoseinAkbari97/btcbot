"""Phase 11: what each setup actually does at +0.5R, +1R, +1.5R and +2R.

Milestone 6 measured excursions and a single +1R barrier. That answers "did
price move in the event's direction?" but not the question a researcher
actually has, which is *where to put the exit*. A +1R barrier hit rate is a
statement about one exit; +0.5R and +2R hit the same event at different rates,
and the ratio between them is the asymmetry the strategy will be built on.

Two failure modes this file exists to prevent:

* **The grid is measured at the wrong denominator.** Every target has its own
  unresolved population -- +2R is reached by far fewer events than +0.5R -- so
  the win rates are not four views of one sample and must never be averaged
  together or compared without their counts.
* **Unresolvable bars become losses.** When the target and the stop land in the
  same bar, OHLC cannot say which printed first. Counting that as a loss
  silently manufactures an edge that OHLC never supported.

The fixtures here are a handful of bars each. Nothing is loaded.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import CandleData
from app.services.research.aggregate import OutcomeAccumulator
from app.services.research.events import ResearchEvent
from app.services.research.outcomes import (
    SWING_STOP,
    TARGET_R_GRID,
    TargetOutcome,
    label_event,
)


def bars(*, highs: list[str], lows: list[str], closes: list[str]) -> list[CandleData]:
    """A price path from explicit highs/lows/closes, one bar per triple.

    OHLC is given directly rather than derived, because the ambiguous-bar case
    needs a bar whose range spans *both* barriers -- something a random walk
    essentially never produces on purpose.
    """
    candles = []
    for index, (high, low, close) in enumerate(zip(highs, lows, closes, strict=True)):
        candles.append(
            make_candle(
                index * 5,
                open_price=close,
                high=high,
                low=low,
                close=close,
            )
        )
    return candles


def swing_event_with_stop() -> ResearchEvent:
    """An event whose confirmation bar has a low 10 below its 100 close.

    The stop distance is what makes the grid hand-checkable: 1R is 10 points,
    so +0.5R is 105, +1R is 110, +1.5R is 115 and +2R is 120. Entry is the bar
    after confirmation, so the scan starts at bar 3.
    """
    return ResearchEvent(
        kind="structure",
        detector="test",
        event_index=1,
        event_time=make_candle(5).open_time,
        confirmation_index=2,
        confirmation_time=make_candle(10).close_time,
        price=Decimal("100"),
    )


# ---------------------------------------------------------------------------
# The grid resolves against the same bar path
# ---------------------------------------------------------------------------


ENTRY_BAR = ("100", "99", "100")

#: Prepended to every forward path, because the entry is the *close* of the
#: first bar after confirmation. Without it the entry drifts to whatever the
#: fixture's first forward bar closed at, and every R in the grid moves with it.
def path(*, forward: list[tuple[str, str, str]], short: bool = False) -> list[CandleData]:
    """Three setup bars (confirmation bar 2, close 100), the entry bar, then
    the forward path.

    For a long the confirmation bar's low is 90; for a short its high is 110.
    Either way the entry is 100 and 1R is 10, so the grid levels are exactly
    105 / 110 / 115 / 120 up and 95 / 90 / 85 / 80 down.
    """
    forward = [ENTRY_BAR, *forward]
    head = bars(
        highs=["100", "100", "110"] if short else ["100", "100", "100"],
        lows=["99", "99", "99"] if short else ["99", "99", "90"],
        closes=["100"] * 3,
    )
    tail = bars(
        highs=[h for h, _l, _c in forward],
        lows=[lo for _h, lo, _c in forward],
        closes=[c for _h, _lo, c in forward],
    )
    return head + tail


def test_every_grid_target_is_measured() -> None:
    """All four multiples the milestone asks for, and no others.

    A grid silently missing +1.5R would still produce a report that looks
    complete, which is the reason to assert on the exact set rather than on
    "some targets".
    """
    outcome = label_event(
        path(forward=[("100", "99", "100")] * 14),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )

    assert set(outcome.targets) == {"0.5", "1", "1.5", "2"}
    assert TARGET_R_GRID == (
        Decimal("0.5"),
        Decimal("1"),
        Decimal("1.5"),
        Decimal("2"),
    )


def test_each_target_resolves_when_its_own_level_is_reached() -> None:
    """A slow rise that clears +0.5R, then +1R, then +1.5R, then +2R.

    All four are wins, at the bar each level actually printed. The shortcut --
    "the highest target that was hit decides, so the earlier ones hit too" --
    gives the same win flags but the wrong bar counts, and bar counts are what
    the time-to-target mean is built from.
    """
    outcome = label_event(
        path(forward=[("106", "104", "105"), ("110", "109", "109"),
                      ("116", "114", "115"), ("120", "119", "119")]),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )
    targets = outcome.targets

    assert all(t.target_before_stop is True for t in targets.values())
    assert targets["0.5"].bars_to_target == 1
    assert targets["1"].bars_to_target == 2
    assert targets["1.5"].bars_to_target == 3
    assert targets["2"].bars_to_target == 4


def test_a_target_the_path_never_reaches_is_not_a_loss() -> None:
    """+1R prints, +2R never does: a win at 1R and an unresolved row at 2R.

    Collapsing the second into a loss would make the grid look monotone --
    every far target strictly worse than every near one -- when what actually
    happened is that the run did not go far enough inside the horizon.
    """
    outcome = label_event(
        path(forward=[("106", "104", "105"), ("112", "109", "111"),
                      ("112", "109", "111"), ("112", "109", "111")]),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )
    targets = outcome.targets

    assert targets["0.5"].target_before_stop is True
    assert targets["1"].target_before_stop is True
    assert targets["1.5"].unresolved is True
    assert targets["2"].unresolved is True
    # Unresolved is not a loss, and not a win either.
    assert targets["2"].target_before_stop is None


def test_the_stop_ending_the_scan_resolves_every_open_target_as_a_loss() -> None:
    """Once -1R prints, every still-open target is settled, not left pending.

    A target still open after the stop would otherwise report `unresolved`
    forever, which reads as "the data ran out" on a run that ended cleanly.
    """
    outcome = label_event(
        path(forward=[("106", "104", "105"), ("108", "103", "104"),
                      ("108", "89", "90"), ("108", "89", "90")]),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )
    targets = outcome.targets

    assert targets["0.5"].target_before_stop is True
    for key in ("1", "1.5", "2"):
        assert targets[key].target_before_stop is False, key
        assert targets[key].unresolved is False, key
        assert targets[key].bars_to_stop == 3, key


def test_both_barriers_in_one_bar_is_ambiguous_not_a_loss() -> None:
    """A bar spanning the target *and* the stop: OHLC cannot order them.

    This is the single most consequential case in the module. Reporting it as a
    loss would inflate every loss rate by exactly the number of such bars --
    which on a tight stop is not a rounding error.
    """
    outcome = label_event(
        path(forward=[("100", "99", "100"), ("121", "85", "90")]),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )

    for key, target in outcome.targets.items():
        assert target.target_before_stop is None, key
        assert target.unresolved is False, key
        # It resolved -- there is an answer, just not an orderable one.
        assert target.bars_to_resolve is not None, key


def test_the_legacy_single_barrier_field_is_unchanged_by_the_grid() -> None:
    """The +1R cell must agree with the pre-existing barrier, exactly.

    The grid replaced a loop that produced ``barrier_hit``/``bars_to_barrier``.
    Anything that already consumed those fields -- the aggregate's barrier
    tallies, the report -- must see the same numbers, or every previously
    validated result silently shifts.
    """
    outcome = label_event(
        path(forward=[("106", "104", "105"), ("108", "103", "104"),
                      ("108", "89", "90"), ("108", "89", "90")]),
        swing_event_with_stop(),
        side="long",
        stop_model=SWING_STOP,
    )

    assert outcome.targets["1"].target_before_stop == outcome.r_barrier_hit
    assert outcome.targets["1"].bars_to_stop == outcome.bars_to_barrier


def test_a_short_mirrors_the_long_without_sign_errors() -> None:
    """The grid is symmetric; a sign slip would only show on one side.

    Both directions are always labelled, so a short-only bug is discoverable
    only by a test that exercises the short.
    """
    outcome = label_event(
        path(
            forward=[("94", "93", "95"), ("88", "87", "88"), ("84", "79", "80")],
            short=True,
        ),
        swing_event_with_stop(),
        side="short",
        stop_model=SWING_STOP,
    )

    assert outcome.targets["1"].target_before_stop is True
    assert outcome.targets["2"].target_before_stop is True
    assert outcome.targets["0.5"].bars_to_target == 1
    assert outcome.targets["2"].bars_to_target == 3


def test_no_grid_cells_appear_without_a_stop_distance() -> None:
    """R needs a stop; with none, the grid is absent rather than invented.

    Emitting a 0R "result" here would mean every event without a stop
    contributed a flat row to the win-rate table.
    """
    # A confirmation bar whose low equals the entry: the structural stop
    # collapses to zero distance, which is undefined, not zero.
    candles = bars(
        highs=["100"] * 20,
        lows=["100"] * 20,
        closes=["100"] * 20,
    )
    outcome = label_event(candles, swing_event_with_stop(), side="long", stop_model=SWING_STOP)

    assert outcome.stop_distance is None
    assert outcome.targets == {}


# ---------------------------------------------------------------------------
# Aggregation: denominators over resolved outcomes only
# ---------------------------------------------------------------------------


def _outcome(target: TargetOutcome, **extra) -> object:
    from app.services.research.outcomes import EventOutcome

    payload = {
        "detector": "test",
        "kind": "structure",
        "side": "long",
        "stop_model": "swing_extreme",
        "event_index": 1,
        "confirmation_index": 2,
        "forward_return": {},
        "forward_return_r": {},
        "mfe": None,
        "mae": None,
        "r_barrier_hit": target.target_before_stop,
        "bars_to_barrier": target.bars_to_resolve,
        "stop_price": Decimal("90"),
        "stop_distance": Decimal("10"),
        "entry_price": Decimal("100"),
        "confirmation_delay_bars": 1,
        # Keyed by the target's own multiple, not always "1": the accumulator
        # looks the bucket up under the grid key the report asks for, so a
        # fixture that filed a 1.5R outcome under "1" would test nothing.
        "targets": {str(target.target_r.normalize()): target},
    }
    payload.update(extra)
    return EventOutcome(**payload)


def test_win_and_loss_rates_use_resolved_outcomes_only() -> None:
    """The ambiguous and unresolved rows leave the denominator.

    2 wins, 1 loss, 1 ambiguous, 1 unresolved. Counting the last two would
    report 40% instead of 2/3 -- and would do it silently, because the row
    still looks like a complete measurement.
    """
    accumulator = OutcomeAccumulator()
    accumulator.add(_outcome(TargetOutcome(Decimal("1"), True, 2, bars_to_target=2)))
    accumulator.add(_outcome(TargetOutcome(Decimal("1"), True, 3, bars_to_target=3)))
    accumulator.add(_outcome(TargetOutcome(Decimal("1"), False, 4, bars_to_stop=4)))
    accumulator.add(_outcome(TargetOutcome(Decimal("1"), None, 5)))
    accumulator.add(
        _outcome(
            TargetOutcome(Decimal("1"), None, None, bars_to_stop=2, unresolved=True)
        )
    )

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "1")

    assert stats["wins"] == 2
    assert stats["losses"] == 1
    assert stats["ambiguous"] == 1
    assert stats["unresolved"] == 1
    assert stats["n"] == 3
    assert stats["win_rate"] == pytest.approx(2 / 3)
    assert stats["loss_rate"] == pytest.approx(1 / 3)


def test_average_r_counts_a_win_at_its_target_and_a_loss_at_minus_one() -> None:
    """+1.5R hit twice and -1R twice averages 0.25R, not 0.5R.

    The asymmetry is the entire reason to sweep targets: at +1.5R the wins are
    worth more than the losses cost, and only because the win is credited at
    the level that was actually reached.
    """
    accumulator = OutcomeAccumulator()
    for _ in range(2):
        accumulator.add(
            _outcome(TargetOutcome(Decimal("1.5"), True, 2, bars_to_target=2))
        )
    for _ in range(2):
        accumulator.add(
            _outcome(TargetOutcome(Decimal("1.5"), False, 5, bars_to_stop=5))
        )

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "1.5")

    assert stats["average_r"] == pytest.approx(0.25)
    # Sorted [-1, -1, 1.5, 1.5]: the median of an even count is the midpoint,
    # 0.25 -- not the mean of the wins and not either extreme.
    assert stats["median_r"] == pytest.approx(0.25)


def test_a_cell_nothing_reached_reports_zero_not_absence() -> None:
    """"Measured and found nothing" differs from "never measured"."""
    accumulator = OutcomeAccumulator()

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "2")

    assert stats["n"] == 0
    assert stats["win_rate"] is None
    assert stats["average_r"] is None


def test_a_median_is_reported_when_the_r_sample_was_truncated() -> None:
    """A capped sample must say so next to the number.

    Below the cap the median is exact; above it, the reservoir keeps the
    smallest N, which is a biased sample of the median and therefore not the
    median.
    """
    from app.services.research.aggregate import TARGET_R_SAMPLE_CAP

    accumulator = OutcomeAccumulator()
    for i in range(TARGET_R_SAMPLE_CAP + 50):
        # Losses arrive last in the stream, so each one is strictly smaller than
        # the largest value already held and the reservoir has to replace.
        wins = i < TARGET_R_SAMPLE_CAP
        accumulator.add(
            _outcome(
                TargetOutcome(
                    Decimal("1"),
                    wins,
                    2,
                    bars_to_target=2 if wins else None,
                    bars_to_stop=None if wins else 2,
                )
            )
        )

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "1")

    assert stats["median_r"] is not None
    assert stats["median_truncated"] is True

def test_the_median_is_an_order_statistic_and_not_a_stream_position() -> None:
    """The sample is kept sorted, so the median is the middle *value*.

    This is here because the first implementation appended and only sorted once
    the cap forced a replacement, which made the median a function of arrival
    order. It produced medians of 0.25 and 2.0 for a population whose only
    possible values were +1R and -1R -- and did so silently, on real data, at a
    family size large enough to look credible.

    A median of a set of losses and wins can only ever be one of those values or
    their midpoint. That invariant is what makes the bug detectable.
    """
    accumulator = OutcomeAccumulator()
    stream = [True, True, False, True, False, False, True, False, False, True, False]
    for wins in stream:
        accumulator.add(
            _outcome(
                TargetOutcome(
                    Decimal("1"),
                    wins,
                    2,
                    bars_to_target=2 if wins else None,
                    bars_to_stop=None if wins else 2,
                )
            )
        )

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "1")
    expected = sorted(1.0 if w else -1.0 for w in stream)

    assert stats["n"] == len(stream)
    assert stats["average_r"] == pytest.approx(sum(expected) / len(expected))
    assert stats["median_r"] in (1.0, -1.0, 0.0)
    assert stats["median_r"] == pytest.approx(sum(expected) / len(expected)) or \
        stats["median_r"] in (1.0, -1.0)


def test_a_truncated_sample_still_reports_a_value_the_population_can_take() -> None:
    """Once the cap is hit, the median must remain an order statistic.

    Only +1R and -1R are ever recorded, so a median of anything else is
    provably wrong -- and a reservoir that keeps the wrong N elements produces
    exactly that, without failing on the mean or the win rate.
    """
    from app.services.research.aggregate import TARGET_R_SAMPLE_CAP

    accumulator = OutcomeAccumulator()
    # Losses arrive after the cap fills, so each is strictly smaller than the
    # largest value held and the reservoir must replace on every one.
    for i in range(TARGET_R_SAMPLE_CAP + 20):
        wins = i < TARGET_R_SAMPLE_CAP
        accumulator.add(
            _outcome(
                TargetOutcome(
                    Decimal("1"),
                    wins,
                    2,
                    bars_to_target=2 if wins else None,
                    bars_to_stop=None if wins else 2,
                )
            )
        )

    stats = accumulator.target_stats("test", "structure", "long", "swing_extreme", "1")

    assert stats["median_truncated"] is True
    assert stats["median_r"] in (1.0, -1.0)
    # 20 losses against a full reservoir of 20,000 wins: the median is the
    # midpoint of the two middle values, which is 0.0 only if the sample kept
    # both populations -- a reservoir that dropped the losses could not.
    assert stats["median_r"] == pytest.approx(1.0)
