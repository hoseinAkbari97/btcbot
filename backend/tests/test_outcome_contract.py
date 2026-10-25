"""The frozen outcome contract, one clause per test.

Setup 1 (liquidity sweep + rejection) must be measurable by the research
labeller and executable by the backtest engine with *the same* answer for the
same bars, or every experiment compares two different games. This file pins
each clause of that contract (see :mod:`app.services.outcome_contract`) on
small synthetic fixtures — a handful of candles per test, nothing loaded — so
a future change to either component fails here first:

* stop only -> loss; target only -> win;
* both barriers in one candle -> loss, flagged ``ambiguous_bar``;
* neither barrier by the horizon -> unresolved, outside the denominator;
* a gap through a level fills at the open, not the level;
* a touch earns no fill when the fill model orders the bar differently;
* the entry candle is evaluated for barriers once the fill has happened;
* labeller and backtester agree on identical scenarios;
* costs are applied once, on top of the shared raw fill reference;
* no bar after the confirmation moves the entry or the stop;
* short-side labelling (an event study) is never spot-executable performance;
* an invalid signal before entry completes no trade in either component.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import CandleData, Timeframe
from app.services.backtest.costs import BacktestCosts, apply_slippage
from app.services.backtest.engine import (
    CLOSE,
    HOLD,
    OPEN_LONG,
    OPEN_SHORT,
    BacktestEngine,
    Signal,
)
from app.services.outcome_contract import (
    STOP_LOSS,
    TAKE_PROFIT,
    is_spot_executable,
    resolve_barriers,
)
from app.services.research.aggregate import OutcomeAccumulator
from app.services.research.events import ResearchEvent
from app.services.research.outcomes import SWING_STOP, label_event

ZERO_COSTS = BacktestCosts(
    fee_rate=Decimal(0), spread_rate=Decimal(0), slippage_rate=Decimal(0), latency_bars=1
)
#: The engine's standing assumptions: Binance VIP-style fee, quoted spread and
#: slippage. Results produced with them are upper bounds on real performance.
COSTS = BacktestCosts(
    fee_rate=Decimal("0.001"),
    spread_rate=Decimal("0.0002"),
    slippage_rate=Decimal("0.0001"),
    latency_bars=1,
)

#: Bars 0..2 of every long fixture: bar 1 is the event, bar 2 the confirmation
#: whose low (90) is the structural stop, so the entry (100) gives exactly
#: 1R = 10 and the grid lands on 105 / 110 / 115 / 120.
LONG_HEAD = (
    ("100", "101", "99", "100"),
    ("100", "101", "99", "100"),
    ("100", "101", "90", "100"),
)


def bars(*rows: tuple[str, str, str, str]) -> list[CandleData]:
    """Rows of (open, high, low, close), one five-minute candle each."""
    return [
        make_candle(i * 5, open_price=o, high=h, low=l, close=c)
        for i, (o, h, l, c) in enumerate(rows)
    ]


def long_path(*tail: tuple[str, str, str, str]) -> list[CandleData]:
    """Head + entry bar (index 3, open 100) + the caller's tail."""
    return bars(*LONG_HEAD, ("100", "101", "99", "100"), *tail)


def event_at_confirmation(candles: list[CandleData]) -> ResearchEvent:
    """The event the fixtures describe: bar 1, confirmed at bar 2's close."""
    return ResearchEvent(
        kind="structure",
        detector="contract",
        event_index=1,
        event_time=candles[1].open_time,
        confirmation_index=2,
        confirmation_time=candles[2].close_time,
        price=candles[1].close,
    )


def run_engine(
    candles: list[CandleData],
    signal: Signal,
    *,
    costs: BacktestCosts = ZERO_COSTS,
    allow_short: bool = False,
    signal_index: int = 2,
):
    """Emit ``signal`` at ``signal_index``'s close, hold otherwise."""

    def logic(context) -> Signal:
        return signal if context.index == signal_index else Signal(kind=HOLD)

    return BacktestEngine(
        candles=candles,
        strategy_name="outcome_contract",
        logic=logic,
        costs=costs,
        initial_capital=Decimal("10000"),
        timeframe=Timeframe.M5,
        allow_short=allow_short,
    ).run()


LONG_BRACKET = dict(side="long", stop_price=Decimal("90"), target_price=Decimal("110"))


# ---------------------------------------------------------------------------
# The canonical resolver: one decision per clause
# ---------------------------------------------------------------------------


def test_stop_only_resolves_to_a_loss_at_the_stop_level() -> None:
    fill = resolve_barriers(
        make_candle(0, open_price="100", high="109", low="89", close="95"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == STOP_LOSS
    assert fill.fill_price == Decimal("90"), "a fill on the level fills at the level"
    assert fill.ambiguous_bar is False
    assert fill.gapped is False

    # Asking with no target ("did the stop print?") gives the same answer.
    only_stop = resolve_barriers(
        make_candle(0, open_price="100", high="109", low="89", close="95"),
        side="long",
        stop_price=Decimal("90"),
        target_price=None,
    )
    assert only_stop == fill

    # Short mirrors: high touches 110, no gap, no ambiguity.
    short = resolve_barriers(
        make_candle(0, open_price="100", high="111", low="99", close="101"),
        side="short",
        stop_price=Decimal("110"),
        target_price=Decimal("90"),
    )
    assert short is not None
    assert (short.reason, short.fill_price) == (STOP_LOSS, Decimal("110"))
    assert short.ambiguous_bar is False


def test_target_only_resolves_to_a_win_at_the_target_level() -> None:
    fill = resolve_barriers(
        make_candle(0, open_price="100", high="111", low="99", close="105"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == TAKE_PROFIT
    assert fill.fill_price == Decimal("110")
    assert fill.ambiguous_bar is False and fill.gapped is False

    short = resolve_barriers(
        make_candle(0, open_price="100", high="101", low="89", close="95"),
        side="short",
        stop_price=Decimal("110"),
        target_price=Decimal("90"),
    )
    assert short is not None
    assert (short.reason, short.fill_price) == (TAKE_PROFIT, Decimal("90"))


def test_both_barriers_in_one_candle_counts_as_a_stop_loss() -> None:
    """The frozen primary convention: a tie is a loss, and it stays visible.

    The candle opens strictly between the two levels, so nothing observable
    orders them — only the pre-registered convention can, and it says loss.
    """
    fill = resolve_barriers(
        make_candle(0, open_price="95", high="121", low="85", close="96"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == STOP_LOSS
    assert fill.fill_price == Decimal("90")
    assert fill.ambiguous_bar is True, "the tie must remain countable as a diagnostic"
    assert fill.gapped is False

    short = resolve_barriers(
        make_candle(0, open_price="105", high="115", low="89", close="104"),
        side="short",
        stop_price=Decimal("110"),
        target_price=Decimal("90"),
    )
    assert short is not None
    assert short.reason == STOP_LOSS and short.ambiguous_bar is True


def test_gap_through_the_stop_fills_at_the_open_not_the_trigger() -> None:
    """A resting stop-market order cannot fill better than the next quote.

    The candle *opens* below the stop, so the fill is the open — worse than
    the trigger — and the gap itself orders the candle: whatever the high did
    later cannot have happened first, so this is not an ambiguous bar.
    """
    fill = resolve_barriers(
        make_candle(0, open_price="85", high="121", low="84", close="87"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == STOP_LOSS
    assert fill.fill_price == Decimal("85"), "gapped fills are at the open, not the stop"
    assert fill.fill_price < Decimal("90"), "and they are worse than the level"
    assert fill.gapped is True
    assert fill.ambiguous_bar is False, "the gap orders the candle: no tie to break"

    short = resolve_barriers(
        make_candle(0, open_price="115", high="116", low="99", close="112"),
        side="short",
        stop_price=Decimal("110"),
        target_price=Decimal("90"),
    )
    assert short is not None
    assert short.fill_price == Decimal("115") and short.gapped is True


def test_gap_through_the_target_fills_at_the_open_and_beats_the_level() -> None:
    """A resting limit fills at the market's open when that open is better.

    The candle also opened through the stop's territory later, but the fill
    happened at the open — before any intrabar move — so the target wins.
    """
    fill = resolve_barriers(
        make_candle(0, open_price="115", high="116", low="88", close="112"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == TAKE_PROFIT
    assert fill.fill_price == Decimal("115")
    assert fill.fill_price > Decimal("110")
    assert fill.gapped is True and fill.ambiguous_bar is False


def test_target_touched_but_fill_order_says_stop_gets_no_target_fill() -> None:
    """A touch is not a fill when the candle *opened* through the stop.

    The high reaches 110 exactly, but the resting stop-market order executed
    at the open below the stop: the position was already flat when the target
    printed. Touch-based fill models would have invented a win here.
    """
    fill = resolve_barriers(
        make_candle(0, open_price="88", high="110", low="86", close="90"),
        **LONG_BRACKET,
    )
    assert fill is not None
    assert fill.reason == STOP_LOSS, "the touched target earns nothing"
    assert fill.fill_price == Decimal("88")
    assert fill.gapped is True and fill.ambiguous_bar is False


def test_a_candle_printing_neither_barrier_resolves_nothing() -> None:
    assert (
        resolve_barriers(
            make_candle(0, open_price="100", high="105", low="95", close="101"),
            **LONG_BRACKET,
        )
        is None
    )
    with pytest.raises(ValueError, match="long.*short"):
        resolve_barriers(
            make_candle(0, open_price="100", high="105", low="95", close="101"),
            side="up",
            stop_price=Decimal("90"),
            target_price=Decimal("110"),
        )


# ---------------------------------------------------------------------------
# Labeller: entry timing, horizons, and the denominator
# ---------------------------------------------------------------------------


def test_entry_is_the_open_of_the_bar_after_confirmation() -> None:
    """Signal at bar 2's close -> fill at bar 3's *open*, never its close.

    This is also the "confirmed swing used only after confirmation" rule: the
    entry can never precede the close that confirmed it, and a bar whose open
    (103) differs from its close (104) proves which one is used.
    """
    candles = bars(
        *LONG_HEAD,
        ("103", "104", "102", "104"),
        ("104", "105", "103", "104"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )

    assert outcome.entry_price == Decimal("103"), "T+1 open, not T+1 close"
    assert outcome.entry_price != candles[3].close
    assert outcome.stop_price == Decimal("90")
    assert outcome.stop_distance == Decimal("13")


def test_the_entry_candle_is_evaluated_after_the_fill() -> None:
    """A barrier printed in the fill candle exits the trade on that candle.

    The position is exposed from the fill price onward, so the entry candle's
    remaining range counts. This fixture's entry bar (index 3) opens at 100 and
    dips to 85, through the 90 stop: at zero costs that is a loss at the stop,
    and the labeller reports it with ``bars_to_stop`` of 0. The old behaviour
    (scanning from ``entry_index + 1``) deferred the exit to the next bar and
    reported the trade open through a stop that had already been hit.
    """
    candles = bars(
        *LONG_HEAD,
        ("100", "101", "85", "100"),   # entry bar: stop touched after the fill
        ("100", "110", "99", "105"),   # next bar: target prints (too late)
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    target = outcome.targets["1"]
    assert target.target_before_stop is False, "the entry candle's stop hit wins"
    assert target.exit_price == Decimal("90")
    assert target.bars_to_stop == 0, "resolved in the entry candle, not the next bar"

    run = run_engine(
        candles,
        Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")),
    )
    assert len(run.trades) == 1
    assert run.trades[0].exit_reason == STOP_LOSS
    assert run.trades[0].exit_price == Decimal("90")
    assert run.trades[0].bars_held == 0, "the engine closes it on the fill candle"


def test_an_entry_candle_deep_into_the_target_resolves_as_a_win() -> None:
    """The entry candle is evaluated for the target too, not only the stop."""
    candles = bars(
        *LONG_HEAD,
        ("100", "112", "99", "110"),   # entry bar: target prints after the fill
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    target = outcome.targets["1"]
    assert target.target_before_stop is True
    assert target.exit_price == Decimal("110")
    assert target.bars_to_target == 0

    run = run_engine(
        candles,
        Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")),
    )
    assert run.trades[0].exit_reason == TAKE_PROFIT
    assert run.trades[0].exit_price == Decimal("110")


def test_a_tie_in_the_entry_candle_is_a_flagged_loss() -> None:
    """Both barriers inside the entry candle: same convention as any other bar."""
    candles = bars(
        *LONG_HEAD,
        ("95", "121", "85", "96"),     # entry bar touches both level and target
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    for key, target in outcome.targets.items():
        assert target.target_before_stop is False, key
        assert target.ambiguous_bar is True, key
        assert target.bars_to_stop == 0, key

    run = run_engine(
        candles,
        Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")),
    )
    assert run.trades[0].exit_reason == STOP_LOSS
    assert run.trades[0].exit_price == Decimal("90")


def test_the_entry_price_itself_is_never_a_barrier_hit() -> None:
    """A dead-flat entry candle opens *at* the entry: neither barrier prints.

    The brackets sit strictly beyond the entry (stop 90 below, target 110
    above), and the candle's open, high, low and close are all the entry price
    of 100. Nothing has moved against or for the position, so it stays open —
    the entry price is the fill, not a level that can be "touched".
    """
    candles = bars(
        *LONG_HEAD,
        ("100", "100", "100", "100"),  # entry bar: open == high == low == close
        ("100", "101", "99", "100"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    assert outcome.targets["1"].target_before_stop is None, "neither barrier printed"
    assert outcome.targets["1"].unresolved is True

    run = run_engine(
        candles,
        Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")),
    )
    assert len(run.trades) == 1
    assert run.trades[0].exit_reason == "end_of_data"


def test_neither_barrier_by_the_horizon_is_unresolved_not_a_loss() -> None:
    """A full 12-bar horizon of flat bars: no trade result exists at all."""
    flat = [("100", "101", "99", "100")] * 13
    candles = long_path(*flat)
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )

    for key, target in outcome.targets.items():
        assert target.unresolved is True, key
        assert target.target_before_stop is None, key
        assert target.exit_price is None, key

    accumulator = OutcomeAccumulator()
    accumulator.add(outcome)
    stats = accumulator.target_stats("contract", "structure", "long", "swing_extreme", "1")
    assert stats["n"] == 0, "unresolved events are outside the denominator"
    assert stats["unresolved"] == 1
    assert stats["win_rate"] is None and stats["loss_rate"] is None


def test_a_gap_stop_resolves_worse_than_minus_one_r_in_the_labeller() -> None:
    """The labeller's R comes from the resolver's fill, not from the level.

    Entry 100, stop 90, but the candle opens at 85: the loss is -1.5R, not
    the -1R a trigger-price assumption would have reported.
    """
    candles = long_path(("85", "90", "84", "86"), ("100", "101", "99", "100"))
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    target = outcome.targets["1"]
    assert target.target_before_stop is False
    assert target.exit_price == Decimal("85")

    accumulator = OutcomeAccumulator()
    accumulator.add(outcome)
    stats = accumulator.target_stats("contract", "structure", "long", "swing_extreme", "1")
    assert stats["losses"] == 1 and stats["n"] == 1
    assert stats["average_r"] == pytest.approx(-1.5)


def test_a_same_bar_tie_is_inside_the_labellers_resolved_denominator() -> None:
    """End-to-end: the labeller's tie rows land in losses, flagged, counted.

    This is the clause the old labeller violated — it dropped ties from the
    denominator while the engine called them stop losses.
    """
    candles = long_path(("95", "121", "85", "96"))
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    for key, target in outcome.targets.items():
        assert target.target_before_stop is False, key
        assert target.ambiguous_bar is True, key
    assert outcome.r_barrier_hit is False, "the legacy +1R barrier is a loss too"

    accumulator = OutcomeAccumulator()
    accumulator.add(outcome)
    stats = accumulator.target_stats("contract", "structure", "long", "swing_extreme", "1")
    assert stats["n"] == 1 and stats["losses"] == 1 and stats["wins"] == 0
    assert stats["ambiguous"] == 1, "diagnostic on top of the loss, not an alternative"


# ---------------------------------------------------------------------------
# Labeller and backtester agree on identical scenarios
# ---------------------------------------------------------------------------

BRACKET_SIGNAL = Signal(
    kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")
)


@pytest.mark.parametrize(
    ("tail", "expected_reason", "expected_fill"),
    [
        # Both barriers in one candle -> loss at the stop, tie flagged.
        (("95", "121", "85", "96"), STOP_LOSS, Decimal("90")),
        # Gap through the stop -> loss at the open, worse than the level.
        (("85", "90", "84", "86"), STOP_LOSS, Decimal("85")),
        # Target only -> win at the level.
        (("100", "110", "99", "105"), TAKE_PROFIT, Decimal("110")),
        # Touch without fill order -> still the stop's answer.
        (("88", "110", "86", "90"), STOP_LOSS, Decimal("88")),
    ],
)
def test_labeller_and_backtester_agree_on_identical_scenarios(
    tail: tuple[str, str, str, str], expected_reason: str, expected_fill: Decimal
) -> None:
    """Same candles, same bracket, same answer — zero costs isolate the rules.

    The labeller's raw fill reference and the engine's (zero-cost) exit price
    must be the *same number*: agreement on the fill model, not just on the
    win/loss label.
    """
    candles = long_path(tail, ("100", "101", "99", "100"))
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    target = outcome.targets["1"]
    assert target.exit_price == expected_fill
    assert target.target_before_stop is (expected_reason == TAKE_PROFIT)

    run = run_engine(candles, BRACKET_SIGNAL)
    assert len(run.trades) == 1
    trade = run.trades[0]
    assert trade.exit_reason == expected_reason
    assert trade.exit_price == expected_fill, "engine exit == labeller raw fill"
    assert trade.entry_price == outcome.entry_price, "both fill at bar 3's open"


# ---------------------------------------------------------------------------
# Costs: applied once, on top of the shared reference
# ---------------------------------------------------------------------------


def test_costs_are_applied_once_on_top_of_the_shared_fill_reference() -> None:
    """The cost model may change the price, never the fill decision.

    Entry and exit must equal exactly the shared raw references moved by the
    declared spread+slippage concession — no second application, no different
    reference — and the net result must be strictly below the gross one.
    """
    candles = long_path(("100", "110", "99", "105"), ("100", "101", "99", "100"))
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    raw_entry = outcome.entry_price                      # 100, the bar open
    raw_exit = outcome.targets["1"].exit_price           # 110, the target level

    run = run_engine(candles, BRACKET_SIGNAL, costs=COSTS)
    trade = run.trades[0]

    assert trade.entry_price == apply_slippage(raw_entry, "buy", COSTS)
    assert trade.exit_price == apply_slippage(raw_exit, "sell", COSTS)
    assert trade.entry_price > raw_entry, "the buy-side concession is against us"
    assert trade.exit_price < raw_exit, "the sell-side concession is against us"
    assert trade.gross_r is not None and trade.net_r is not None
    assert trade.net_r < trade.gross_r, "fees and spread strictly reduce the result"


# ---------------------------------------------------------------------------
# No future information; spot eligibility; invalid signals
# ---------------------------------------------------------------------------


def test_no_bar_after_the_confirmation_moves_the_entry_or_the_stop() -> None:
    """Entry and stop are functions of the signal, not of what followed.

    Two paths identical through the entry bar (index 3) but wild afterwards:
    entry price, stop price, stop distance and delay must be identical. The
    forward returns *do* differ — they are the measurement, not the signal.
    """
    head = bars(*LONG_HEAD, ("100", "101", "99", "100"))
    calm = head + bars(("100", "101", "99", "100"), ("100", "101", "99", "100"))
    wild = head + bars(("150", "160", "140", "155"), ("50", "55", "45", "52"))

    calm_outcome = label_event(
        calm, event_at_confirmation(calm), side="long", stop_model=SWING_STOP
    )
    wild_outcome = label_event(
        wild, event_at_confirmation(wild), side="long", stop_model=SWING_STOP
    )

    assert calm_outcome.entry_price == wild_outcome.entry_price
    assert calm_outcome.stop_price == wild_outcome.stop_price
    assert calm_outcome.stop_distance == wild_outcome.stop_distance
    assert (
        calm_outcome.confirmation_delay_bars == wild_outcome.confirmation_delay_bars
    )
    # ...while the measured future differs, which is the whole point of it.
    assert calm_outcome.forward_return[1] != wild_outcome.forward_return[1]


def test_short_labelling_is_not_spot_execution_eligibility() -> None:
    """Shorts stay an event study; the spot engine refuses them by default.

    The labeller must keep producing short outcomes (research input), while
    ``is_spot_executable`` and the long-only engine keep those outcomes from
    ever being presented as spot-backtest performance.
    """
    assert is_spot_executable("long") is True
    assert is_spot_executable("short") is False

    short_candles = bars(
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
        ("100", "110", "99", "100"),   # confirmation high 110 -> stop 110
        ("100", "101", "99", "100"),
        ("100", "101", "89", "95"),
    )
    outcome = label_event(
        short_candles,
        event_at_confirmation(short_candles),
        side="short",
        stop_model=SWING_STOP,
    )
    assert outcome.side == "short"
    assert outcome.targets["1"].target_before_stop is True, "the study still labels"

    short_signal = Signal(
        kind=OPEN_SHORT, stop_price=Decimal("110"), target_price=Decimal("90")
    )
    refused = run_engine(short_candles, short_signal)          # spot default
    assert refused.trades == []
    assert any("long-only" in reason for reason in refused.rejected_signals)

    # The gate is explicit, not accidental: with shorts opted in the engine
    # runs the identical scenario — and that result is still not spot
    # performance, which is what is_spot_executable("short") refuses.
    opted_in = run_engine(short_candles, short_signal, allow_short=True)
    assert len(opted_in.trades) == 1
    assert is_spot_executable("short") is False


def test_twelve_evaluated_candles_including_the_entry_candle() -> None:
    """Horizon = 12 evaluated candles total, counting the entry candle.

    The 12th evaluated candle is entry_index + 11 relative to entry; a barrier
    that prints there resolves the trade. A barrier on the 13th candle
    (entry_index + 12) must not be evaluated.
    """
    # Flat candles through the horizon tail
    candles = bars(
        *LONG_HEAD,
        ("100", "101", "99", "100"),   # eval candle 1 (entry)
        ("100", "101", "99", "100"),   # 2
        ("100", "101", "99", "100"),   # 3
        ("100", "101", "99", "100"),   # 4
        ("100", "101", "99", "100"),   # 5
        ("100", "101", "99", "100"),   # 6
        ("100", "101", "99", "100"),   # 7
        ("100", "101", "99", "100"),   # 8
        ("100", "101", "99", "100"),   # 9
        ("100", "101", "99", "100"),   # 10
        ("100", "101", "99", "100"),   # 11
        ("100", "110", "99", "105"),   # 12th evaluated candle: hits target
        ("100", "101", "99", "100"),   # 13th: would hit but must not be evaluated
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    target = outcome.targets["1"]
    assert target.target_before_stop is True
    assert target.bars_to_target == 11, "resolved on the 12th evaluated candle"
    assert target.exit_price == Decimal("110")

    run = run_engine(
        candles,
        Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("110")),
    )
    assert len(run.trades) == 1
    assert run.trades[0].exit_reason == TAKE_PROFIT
    assert run.trades[0].exit_price == Decimal("110")


def test_horizon_expiry_after_the_twelfth_evaluated_candle_is_unresolved() -> None:
    """No barrier by close of the 12th evaluated candle => unresolved/censored."""
    tail = [("100", "101", "99", "100")] * 15
    candles = long_path(*tail)
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    for key, target in outcome.targets.items():
        assert target.unresolved is True, key
        assert target.target_before_stop is None, key

    # Also prove the 13th candle is not evaluated by putting a target hit there
    # but not earlier; with correct counting it must be unresolved.
    candles2 = bars(
        *LONG_HEAD,
        ("100", "101", "99", "100"),   # 1
        ("100", "101", "99", "100"),   # 2
        ("100", "101", "99", "100"),   # 3
        ("100", "101", "99", "100"),   # 4
        ("100", "101", "99", "100"),   # 5
        ("100", "101", "99", "100"),   # 6
        ("100", "101", "99", "100"),   # 7
        ("100", "101", "99", "100"),   # 8
        ("100", "101", "99", "100"),   # 9
        ("100", "101", "99", "100"),   # 10
        ("100", "101", "99", "100"),   # 11
        ("100", "101", "99", "100"),   # 12th: flat, no barrier
        ("100", "110", "99", "105"),   # 13th: would hit but beyond horizon
    )
    outcome2 = label_event(
        candles2, event_at_confirmation(candles2), side="long", stop_model=SWING_STOP
    )
    assert outcome2.targets["1"].unresolved is True
    assert outcome2.targets["1"].target_before_stop is None
    """Signal invalid before entry: neither component reports a result.

    The confirmation low is 90, but the entry candle gapped to 85 — a stop
    above the fill. The labeller returns no stop distance (so no grid, no R)
    and the engine refuses the bracket outright. The old labeller's ``abs()``
    would have turned this into a guaranteed instant loss instead.
    """
    candles = bars(
        *LONG_HEAD,
        ("85", "88", "84", "86"),       # entry bar gapped below the stop
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
    )
    outcome = label_event(
        candles, event_at_confirmation(candles), side="long", stop_model=SWING_STOP
    )
    assert outcome.entry_price == Decimal("85")
    # No completed trade: neither a stop distance nor a trade stop is recorded
    # (the structural level itself is not promoted into a fake trade stop).
    assert outcome.stop_price is None
    assert outcome.stop_distance is None, "an inverted stop is unmeasurable, not a loss"
    assert outcome.targets == {}
    assert outcome.r_barrier_hit is None

    with pytest.raises(ValueError, match="not protective"):
        run_engine(candles, BRACKET_SIGNAL)


def test_signal_exit_orders_still_close_flat_positions() -> None:
    """A CLOSE signal while flat is recorded and ignored, never a phantom trade.

    Guards the exit path that sits next to the resolver: contract work in
    ``_intrabar_exit`` must not disturb ordinary order handling.
    """
    run = run_engine(
        long_path(("100", "101", "99", "100")),
        Signal(kind=CLOSE, reason="stray exit"),
    )
    assert run.trades == []
    assert any("flat" in reason for reason in run.rejected_signals)
