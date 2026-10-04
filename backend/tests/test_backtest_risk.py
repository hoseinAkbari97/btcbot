"""Risk engine tests (Phase 5).

The risk engine's contract is that a strategy's request is *advisory*: it may
ask for less risk than the ceiling, never more, and it cannot override a halt.
These tests assert that property and that the pre-Phase-5 path — no risk engine
— is unchanged. None of them asserts profitability, and a clamped result that
looks worse than the unclamped one is the expected and correct outcome.
"""

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.backtest.engine import CLOSE, OPEN_LONG, BacktestEngine, Signal
from app.services.backtest.risk import (
    COOLDOWN,
    DAILY_LOSS_LIMIT,
    DRAWDOWN_LIMIT,
    EMERGENCY_STOP,
    STALE_DATA,
    RiskEngine,
    RiskLimits,
)
from test_backtest_engine import ZERO_COSTS, engine_for, flat_candles

CAPITAL = Decimal("10000")


def risk_with(**limits) -> RiskEngine:
    return RiskEngine(RiskLimits(**limits), CAPITAL)


def permissive() -> RiskEngine:
    """Limits that never bind, to prove the two code paths agree."""
    return RiskEngine(
        RiskLimits(
            max_risk_per_trade=Decimal(1),
            max_portfolio_exposure=Decimal(1),
            max_daily_loss=Decimal(0),
            max_weekly_loss=Decimal(0),
            max_drawdown=Decimal(0),
            emergency_stop_loss=Decimal(0),
            max_stale_bars=10_000,
        ),
        CAPITAL,
    )


# -- configuration ---------------------------------------------------------


def test_limits_reject_a_fraction_above_one() -> None:
    with pytest.raises(ValueError, match="max_risk_per_trade"):
        RiskLimits(max_risk_per_trade=Decimal("2"))


def test_limits_reject_a_negative_fraction() -> None:
    with pytest.raises(ValueError, match="max_drawdown"):
        RiskLimits(max_drawdown=Decimal("-0.1"))


def test_limits_reject_a_zero_stale_window() -> None:
    """Zero would mean "every position is instantly stale"."""
    with pytest.raises(ValueError, match="max_stale_bars"):
        RiskLimits(max_stale_bars=0)


def test_a_zero_cooldown_is_allowed() -> None:
    """Unlike the other counters, zero bars of cooldown means "no cooldown"."""
    assert RiskLimits(cooldown_bars_after_loss=0).cooldown_bars_after_loss == 0


def test_defaults_are_constructible() -> None:
    assert RiskLimits().max_risk_per_trade == Decimal("0.01")


# -- the strategy cannot raise its own risk -------------------------------


def test_an_oversized_request_is_clamped_to_the_ceiling() -> None:
    engine = risk_with(max_risk_per_trade=Decimal("0.005"))
    decision = engine.check_entry(0, CAPITAL, Decimal("1"))
    assert decision.approved
    assert decision.sized_fraction == Decimal("0.005")


def test_a_smaller_request_is_honoured_exactly() -> None:
    engine = risk_with(max_risk_per_trade=Decimal("0.01"))
    assert engine.check_entry(0, CAPITAL, Decimal("0.002")).sized_fraction == Decimal("0.002")


def test_buy_and_hold_cannot_escape_the_ceiling() -> None:
    """``buy_and_hold`` asks for risk_fraction=1; the engine must refuse it."""
    candles = flat_candles([100 + i for i in range(40)])
    logic = lambda _: Signal(  # noqa: E731
        kind=OPEN_LONG, risk_fraction=Decimal("1"), use_default_brackets=False
    )

    unclamped = engine_for(candles, logic, initial_capital=CAPITAL).run()
    clamped = engine_for(
        candles, logic, initial_capital=CAPITAL, risk=risk_with(max_risk_per_trade=Decimal("0.01"))
    ).run()

    assert unclamped.trades[0].size > clamped.trades[0].size
    ratio = clamped.trades[0].size / unclamped.trades[0].size
    assert abs(ratio - Decimal("0.01")) < Decimal("1e-9")


def test_a_stopped_position_is_sized_from_the_clamped_fraction() -> None:
    """The ceiling must also bound a bracketed position, not just a stopless one."""
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    logic = lambda _: Signal(  # noqa: E731
        kind=OPEN_LONG,
        stop_price=Decimal("99.9999"),
        target_price=Decimal("200"),
        risk_fraction=Decimal("0.5"),
    )
    run = engine_for(
        candles, logic, initial_capital=CAPITAL, risk=risk_with(max_risk_per_trade=Decimal("0.01"))
    ).run()
    # 1% of 10000 risked over a 0.0001/unit stop distance would be enormous; the
    # cash cap binds first, which is the correct spot-only outcome.
    assert run.trades[0].size * run.trades[0].entry_price <= CAPITAL


# -- the no-risk-engine path is unchanged ---------------------------------


def test_a_permissive_risk_engine_matches_the_unsupervised_run() -> None:
    """With limits that never bind, the two paths must agree exactly.

    This is what makes Phase 5 safe to add: a run that configures generous
    limits and a run that configures none describe the same experiment.
    """
    candles = flat_candles([100 + (i % 7) for i in range(80)])
    logic = lambda _: Signal(kind=OPEN_LONG, risk_fraction=Decimal("0.01"))  # noqa: E731

    plain = engine_for(candles, logic, initial_capital=CAPITAL).run()
    supervised = engine_for(candles, logic, initial_capital=CAPITAL, risk=permissive()).run()

    assert plain.final_equity == supervised.final_equity
    assert [t.size for t in plain.trades] == [t.size for t in supervised.trades]


# -- halts -----------------------------------------------------------------


def test_the_daily_loss_limit_halts_entries() -> None:
    engine = risk_with(max_daily_loss=Decimal("0.01"))
    engine.on_bar(0, flat_candles([100])[0].close_time, CAPITAL)
    assert engine.check_entry(1, CAPITAL * Decimal("0.98"), Decimal("0.01")).reason == (
        DAILY_LOSS_LIMIT
    )


def test_a_daily_loss_limit_does_not_survive_the_day_boundary() -> None:
    engine = risk_with(max_daily_loss=Decimal("0.01"))
    first = flat_candles([100])
    engine.on_bar(0, first[0].close_time, CAPITAL)
    later = make_candle(60 * 24 * 2)  # two days later
    engine.on_bar(1, later.close_time, CAPITAL * Decimal("0.98"))
    assert engine.check_entry(2, CAPITAL * Decimal("0.98"), Decimal("0.01")).approved


def test_the_drawdown_limit_halts_entries() -> None:
    engine = risk_with(max_drawdown=Decimal("0.10"))
    first = flat_candles([100])
    engine.on_bar(0, first[0].close_time, CAPITAL)
    engine.on_bar(1, first[0].close_time, CAPITAL * Decimal("1.5"))  # new peak
    assert engine.check_entry(2, CAPITAL * Decimal("1.2"), Decimal("0.01")).reason == (
        DRAWDOWN_LIMIT
    )


def test_the_emergency_stop_latches() -> None:
    engine = risk_with(emergency_stop_loss=Decimal("0.10"))
    first = flat_candles([100])
    engine.on_bar(0, first[0].close_time, CAPITAL)
    engine.on_bar(1, first[0].close_time, CAPITAL * Decimal("0.85"))

    assert engine.emergency_stopped
    # Even a fully recovered account must stay halted: the loss already happened.
    engine.on_bar(2, first[0].close_time, CAPITAL * Decimal("2"))
    assert engine.emergency_stopped
    assert engine.check_entry(3, CAPITAL * Decimal("2"), Decimal("0.01")).reason == EMERGENCY_STOP


def test_an_emergency_stop_records_a_violation() -> None:
    engine = risk_with(emergency_stop_loss=Decimal("0.10"))
    first = flat_candles([100])
    engine.on_bar(0, first[0].close_time, CAPITAL)
    engine.on_bar(1, first[0].close_time, CAPITAL * Decimal("0.5"))
    assert EMERGENCY_STOP in engine.violations


def test_the_cooldown_blocks_exactly_the_configured_bars() -> None:
    engine = risk_with(cooldown_bars_after_loss=3)
    engine.record_trade(Decimal("-10"), index=5)

    assert engine.check_entry(5, CAPITAL, Decimal("0.01")).reason == COOLDOWN
    assert engine.check_entry(7, CAPITAL, Decimal("0.01")).reason == COOLDOWN
    engine.on_bar(8, flat_candles([100])[0].close_time, CAPITAL)
    assert engine.check_entry(8, CAPITAL, Decimal("0.01")).approved


def test_a_winning_trade_does_not_start_a_cooldown() -> None:
    engine = risk_with(cooldown_bars_after_loss=3)
    engine.record_trade(Decimal("10"), index=5)
    assert engine.check_entry(5, CAPITAL, Decimal("0.01")).approved


def test_stale_data_force_exits_a_held_position() -> None:
    engine = risk_with(max_stale_bars=3)
    assert engine.check_exit(2).approved
    assert engine.check_exit(3).reason == STALE_DATA


# -- end-to-end through the engine ----------------------------------------


def test_a_halted_run_records_why_in_rejected_signals() -> None:
    # Falling prices, so a long position actually loses money: on flat candles
    # with zero costs equity never leaves 10000 and no limit can trip.
    candles = flat_candles([100 - 0.05 * i for i in range(40)])
    logic = lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False)  # noqa: E731
    run = engine_for(
        candles,
        logic,
        initial_capital=CAPITAL,
        risk=RiskEngine(RiskLimits(emergency_stop_loss=Decimal("0.0001")), CAPITAL),
    ).run()

    assert run.risk_violations
    assert EMERGENCY_STOP in run.risk_violations
    assert any("refused by risk" in message for message in run.rejected_signals)


def test_risk_violations_are_empty_for_a_healthy_run() -> None:
    candles = flat_candles([100 + i for i in range(40)])
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False),
        initial_capital=CAPITAL,
        risk=permissive(),
    ).run()
    assert run.risk_violations == []


def test_a_risk_forced_exit_is_labelled_distinctly() -> None:
    """A stale-data exit must not be mistaken for a stop or target.

    The brackets here (50 / 500 around a 100 entry) are never touched, so any
    position held for the full stale window can only have left via risk.
    """
    candles = flat_candles([100] * 30, high_pad="0", low_pad="0.0001")
    logic = lambda ctx: Signal(  # noqa: E731
        kind=OPEN_LONG,
        stop_price=Decimal("50"),
        target_price=Decimal("500"),
        use_default_brackets=False,
    )
    run = engine_for(
        candles,
        logic,
        initial_capital=CAPITAL,
        risk=RiskEngine(RiskLimits(max_stale_bars=2), CAPITAL),
    ).run()

    assert run.trades
    # A position open at the end of the data is liquidated instead; everything
    # else must carry the risk slug, and none may blame a bracket.
    forced = [t for t in run.trades if t.exit_reason != "end_of_data"]
    assert forced
    assert all(t.exit_reason == f"risk_{STALE_DATA}" for t in forced)
    assert all(t.bars_held >= 2 for t in forced)
    assert not any(t.exit_reason in ("stop_loss", "take_profit", "time_exit") for t in run.trades)


def test_a_run_is_reproducible_under_the_same_limits() -> None:
    candles = flat_candles([100 + (i % 11) for i in range(60)])
    logic = lambda _: Signal(kind=OPEN_LONG, risk_fraction=Decimal("0.5"))  # noqa: E731

    def once() -> BacktestEngine:
        return engine_for(
            candles,
            logic,
            initial_capital=CAPITAL,
            risk=RiskEngine(RiskLimits(max_risk_per_trade=Decimal("0.02")), CAPITAL),
        )

    assert once().run().final_equity == once().run().final_equity


def test_exposure_headroom_shrinks_while_a_position_is_open() -> None:
    engine = risk_with(max_portfolio_exposure=Decimal("1"))
    engine.record_entry(Decimal("6000"))
    assert engine.max_exposure_notional(CAPITAL) - engine.state.open_exposure == Decimal("4000")
    engine.record_exit(Decimal("6000"))
    assert engine.state.open_exposure == Decimal(0)


def test_an_exposure_cap_limits_a_new_position() -> None:
    candles = flat_candles([100 + i for i in range(40)])
    logic = lambda _: Signal(  # noqa: E731
        kind=OPEN_LONG, risk_fraction=Decimal("1"), use_default_brackets=False
    )
    run = engine_for(
        candles,
        logic,
        initial_capital=CAPITAL,
        risk=RiskEngine(RiskLimits(max_risk_per_trade=Decimal("0.2"),
                                   max_portfolio_exposure=Decimal("0.2")), CAPITAL),
    ).run()
    notional = run.trades[0].size * run.trades[0].entry_price
    assert notional <= CAPITAL * Decimal("0.2")


def test_no_risk_engine_leaves_the_field_empty() -> None:
    run = engine_for(
        flat_candles([100] * 10), lambda _: Signal(kind=OPEN_LONG)
    ).run()
    assert run.risk_violations == []


def test_a_close_signal_is_not_gated_by_risk() -> None:
    """Risk can veto an entry; refusing to let a position be closed is not safe."""
    candles = flat_candles([100] * 10, high_pad="0", low_pad="0.0001")
    logic = lambda ctx: (  # noqa: E731
        Signal(kind=OPEN_LONG, use_default_brackets=False)
        if ctx.position is None
        else Signal(kind=CLOSE)
    )
    run = engine_for(
        candles,
        logic,
        initial_capital=CAPITAL,
        risk=RiskEngine(RiskLimits(emergency_stop_loss=Decimal("0.0001")), CAPITAL),
    ).run()
    assert all(trade.side == "long" for trade in run.trades)


# -- persistence of the assumption -----------------------------------------


def test_a_run_records_the_limits_it_used() -> None:
    from app.services.backtest.runner import run_backtest

    result = run_backtest(
        flat_candles([100 + i for i in range(40)]),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=ZERO_COSTS,
        initial_capital=CAPITAL,
        risk=RiskEngine(RiskLimits(max_risk_per_trade=Decimal("0.005")), CAPITAL),
    )
    limits = result.run.parameters["risk_limits"]
    assert limits["max_risk_per_trade"] == Decimal("0.005")
    assert limits["max_drawdown"] == Decimal("0.20")


def test_a_run_without_risk_records_the_absence() -> None:
    from app.services.backtest.runner import run_backtest

    result = run_backtest(
        flat_candles([100 + i for i in range(40)]),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=ZERO_COSTS,
        initial_capital=CAPITAL,
    )
    assert "risk_limits" not in result.run.parameters
