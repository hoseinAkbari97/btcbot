"""Baseline strategies are controls, not products.

These tests only assert the properties that make a baseline a fair
comparison point — reproducibility, causality, and consistent cost and
sizing assumptions.  None of them asserts that a strategy is profitable,
and no result here should be read as evidence that it is.
"""

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.backtest.baselines import (
    STRATEGY_NAMES,
    BuyAndHoldStrategy,
    DonchianBreakoutStrategy,
    RandomStrategy,
    SmaTrendStrategy,
    build_strategy,
    default_parameters,
)
from app.services.backtest.engine import (
    CLOSE,
    OPEN_LONG,
    OPEN_SHORT,
    OpenPosition,
    Signal,
    StrategyContext,
)
from test_backtest_engine import flat_candles


def a_long_position() -> OpenPosition:
    """A stand-in open long, for exercising a strategy's in-position branch."""
    return OpenPosition(
        side="long",
        size=Decimal("1"),
        entry_price=Decimal("100"),
        entry_time=flat_candles([100])[0].open_time,
        entry_index=0,
        entry_fee=Decimal(0),
        max_hold_bars=100,
    )


def context_for(candles, index: int, position=None) -> StrategyContext:
    history = candles[: index + 1]
    return StrategyContext(
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        index=index,
        history=history,
        equity=Decimal("10000"),
        position=position,
    )


# -- registry --------------------------------------------------------------


def test_registry_exposes_the_four_specified_baselines() -> None:
    assert set(STRATEGY_NAMES) == {
        "buy_and_hold",
        "random",
        "sma_trend",
        "donchian_breakout",
    }


def test_build_strategy_rejects_an_unknown_name() -> None:
    with pytest.raises(ValueError, match="unknown strategy"):
        build_strategy("does_not_exist")


def test_default_parameters_exclude_private_state() -> None:
    parameters = default_parameters("random")
    assert parameters["seed"] == 42
    assert not any(key.startswith("_") for key in parameters)


# -- buy and hold ----------------------------------------------------------


def test_buy_and_hold_is_unbracketed() -> None:
    """An artificial stop would turn this baseline into a different strategy."""
    signal = BuyAndHoldStrategy()(context_for(flat_candles([100] * 5), 4))
    assert signal.kind == OPEN_LONG
    assert signal.use_default_brackets is False


def test_buy_and_hold_holds_when_already_long() -> None:
    strategy = BuyAndHoldStrategy()
    assert strategy(context_for(flat_candles([100] * 5), 4, position=a_long_position())).kind == Signal().kind


# -- random ----------------------------------------------------------------


def test_random_is_reproducible_for_a_given_seed() -> None:
    candles = flat_candles([100] * 200)

    def sequence(seed: int):
        strategy = RandomStrategy(seed=seed)
        return [
            strategy(context_for(candles, index)).kind
            for index in range(len(candles))
        ]

    assert sequence(7) == sequence(7)
    assert sequence(7) != sequence(8)


def test_random_never_enters_while_in_a_position() -> None:
    strategy = RandomStrategy(entry_probability=1.0)
    signal = strategy(context_for(flat_candles([100] * 5), 4, position=a_long_position()))
    assert signal.kind == Signal().kind


def test_random_falls_back_to_long_when_shorts_are_disabled() -> None:
    strategy = RandomStrategy(seed=1, entry_probability=1.0, allow_short=False)
    signals = [
        strategy(context_for(flat_candles([100] * 200), index)).kind for index in range(200)
    ]
    assert OPEN_SHORT not in signals


# -- SMA trend -------------------------------------------------------------


def test_sma_trend_waits_for_enough_history() -> None:
    strategy = SmaTrendStrategy(fast_period=20, slow_period=50)
    assert strategy(context_for(flat_candles([100] * 10), 9)).kind == Signal().kind


def test_sma_trend_enters_when_the_fast_average_leads() -> None:
    strategy = SmaTrendStrategy(fast_period=5, slow_period=20)
    candles = flat_candles([100] * 20 + [120] * 5)
    signal = strategy(context_for(candles, 24))
    assert signal.kind == OPEN_LONG


def test_sma_trend_exits_when_the_fast_average_falls_behind() -> None:
    strategy = SmaTrendStrategy(fast_period=5, slow_period=20)
    candles = flat_candles([100] * 20 + [80] * 10)
    signal = strategy(context_for(candles, 29, position=a_long_position()))
    assert signal.kind == CLOSE


def test_sma_trend_stays_flat_when_the_averages_agree() -> None:
    strategy = SmaTrendStrategy(fast_period=5, slow_period=20)
    assert strategy(context_for(flat_candles([100] * 30), 29)).kind == Signal().kind


# -- Donchian breakout -----------------------------------------------------


def test_donchian_waits_for_enough_history() -> None:
    strategy = DonchianBreakoutStrategy(lookback=20)
    assert strategy(context_for(flat_candles([100] * 10), 9)).kind == Signal().kind


def test_donchian_enters_on_a_new_high() -> None:
    strategy = DonchianBreakoutStrategy(lookback=10)
    candles = flat_candles([100] * 15 + [130])
    signal = strategy(context_for(candles, 15))
    assert signal.kind == OPEN_LONG
    assert signal.stop_price is not None and signal.stop_price < signal.target_price


def test_donchian_channel_excludes_the_current_bar() -> None:
    """Otherwise every bar is trivially its own high and it never triggers."""
    strategy = DonchianBreakoutStrategy(lookback=10)
    candles = flat_candles([100] * 40)
    for index in range(11, 40):
        assert strategy(context_for(candles, index)).kind == Signal().kind


def test_donchian_exits_on_a_new_low() -> None:
    strategy = DonchianBreakoutStrategy(lookback=10, exit_lookback=5)
    candles = flat_candles([120] * 24 + [80])
    signal = strategy(context_for(candles, 24, position=a_long_position()))
    assert signal.kind == CLOSE


def test_donchian_stays_flat_inside_the_channel() -> None:
    strategy = DonchianBreakoutStrategy(lookback=10)
    candles = flat_candles([100 + (i % 3) for i in range(40)])
    assert strategy(context_for(candles, 39)).kind == Signal().kind


# -- causality -------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(STRATEGY_NAMES))
def test_no_strategy_reacts_to_a_bar_it_has_not_seen(name: str) -> None:
    """Signals must be a pure function of the truncated history."""
    candles = flat_candles([100 + (i % 7) for i in range(120)])
    strategy = build_strategy(name)
    for index in (30, 60, 90):
        first = strategy(context_for(candles, index))
        second = strategy(context_for(candles, index))
        assert first == second


@pytest.mark.parametrize("name", sorted(STRATEGY_NAMES))
def test_signals_only_use_kinds_the_engine_understands(name: str) -> None:
    candles = flat_candles([100 + (i % 5) for i in range(120)])
    strategy = build_strategy(name)
    for index in range(len(candles)):
        assert strategy(context_for(candles, index)).kind in {
            Signal().kind,
            OPEN_LONG,
            OPEN_SHORT,
            CLOSE,
        }


def test_a_future_bar_cannot_change_an_earlier_signal() -> None:
    """Truncating the data must not alter what a strategy already decided."""
    candles = flat_candles([100 + (i % 7) for i in range(120)])
    truncated = [candle.model_copy() for candle in candles[:60]]
    for name in sorted(STRATEGY_NAMES):
        strategy = build_strategy(name)
        for index in (30, 59):
            assert strategy(context_for(candles, index)) == strategy(
                context_for(truncated, index)
            )
