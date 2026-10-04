"""Engine mechanics: fills, exits, sizing and the no-leakage guarantee."""

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import (
    CLOSE,
    HOLD,
    OPEN_LONG,
    BacktestEngine,
    Signal,
    StrategyContext,
)

ZERO_COSTS = BacktestCosts(
    fee_rate=Decimal(0), spread_rate=Decimal(0), slippage_rate=Decimal(0), latency_bars=1
)

NO_COSTS_ARGS = {
    "fee_rate": Decimal(0),
    "spread_rate": Decimal(0),
    "slippage_rate": Decimal(0),
}


def flat_candles(prices, *, high_pad="1", low_pad="1"):
    """A series of candles whose closes are ``prices`` and whose
    high/low just bracket the open so no bracket is hit unintentionally."""
    candles = []
    for index, price in enumerate(prices):
        high = str(Decimal(price) + Decimal(high_pad))
        low = str(Decimal(price) - Decimal(low_pad))
        candles.append(
            make_candle(index * 5, open_price=str(price), high=high, low=low, close=str(price))
        )
    return candles


def engine_for(candles, logic, **kwargs) -> BacktestEngine:
    defaults = {
        "candles": candles,
        "strategy_name": "test",
        "logic": logic,
        "costs": ZERO_COSTS,
        "initial_capital": Decimal("10000"),
        "timeframe": Timeframe.M5,
    }
    defaults.update(kwargs)
    return BacktestEngine(**defaults)


# -- construction ----------------------------------------------------------


def test_engine_rejects_empty_candles() -> None:
    with pytest.raises(ValueError, match="at least one candle"):
        engine_for([], lambda _: Signal())


def test_engine_rejects_non_positive_capital() -> None:
    with pytest.raises(ValueError, match="initial_capital"):
        engine_for(flat_candles([100, 100]), lambda _: Signal(), initial_capital=Decimal(0))


# -- no future leakage -----------------------------------------------------


def test_strategy_never_sees_future_candles() -> None:
    seen: list[int] = []

    def logic(context: StrategyContext) -> Signal:
        seen.append(context.index)
        assert len(context.history) == context.index + 1
        assert context.history[-1] is context.last
        return Signal(kind=HOLD)

    candles = flat_candles([100] * 10)
    engine_for(candles, logic).run()
    # The last `latency_bars` bars are skipped so no order can fill.
    assert seen == list(range(0, 9))


# -- fills -----------------------------------------------------------------


def test_entry_fills_at_the_next_bar_open_not_the_signal_close() -> None:
    candles = [
        make_candle(0, open_price="100", high="101", low="99", close="500"),
        make_candle(5, open_price="200", high="201", low="199", close="200"),
        make_candle(10, open_price="300", high="301", low="299", close="300"),
    ]
    run = engine_for(candles, lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False)).run()

    assert len(run.trades) == 1
    trade = run.trades[0]
    assert trade.entry_price == Decimal("200"), "filled at bar 1 open, not bar 0 close"
    assert trade.entry_time == candles[1].open_time


def test_latency_of_two_bars_delays_the_fill() -> None:
    candles = [
        make_candle(0, open_price="100", high="101", low="99", close="100"),
        make_candle(5, open_price="200", high="201", low="199", close="200"),
        make_candle(10, open_price="300", high="301", low="299", close="300"),
        make_candle(15, open_price="400", high="401", low="399", close="400"),
    ]
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False),
        costs=BacktestCosts(**NO_COSTS_ARGS, latency_bars=2),
    ).run()
    assert run.trades[0].entry_price == Decimal("300")
    assert run.trades[0].entry_time == candles[2].open_time


def test_no_signal_is_emitted_when_the_latency_window_exceeds_the_data() -> None:
    calls = []

    def logic(context: StrategyContext) -> Signal:
        calls.append(context.index)
        return Signal(kind=HOLD)

    engine_for(flat_candles([100] * 5), logic).run()
    assert calls == [0, 1, 2, 3], "the final bar has no room to fill and is not offered"


def test_a_close_signal_while_flat_is_recorded_and_ignored() -> None:
    run = engine_for(
        flat_candles([100] * 6), lambda _: Signal(kind=CLOSE, reason="stray exit")
    ).run()
    assert run.trades == []
    assert any("ignored while flat" in message for message in run.rejected_signals)


# -- sizing ----------------------------------------------------------------


def test_fixed_fractional_sizing_risks_one_percent_of_equity() -> None:
    candles = flat_candles([100] * 6, high_pad="0", low_pad="5")
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("200")),
        initial_capital=Decimal("10000"),
    ).run()
    # 1% of 10000 = 100 at risk, 5 per unit risk => 20 units.
    assert run.trades[0].size == Decimal("20")
    # Filled at 100, stopped at 95: a full -1R.
    assert run.trades[0].r_multiple == Decimal(-1)


def test_sizing_never_exceeds_available_cash() -> None:
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    run = engine_for(
        candles,
        lambda _: Signal(
            kind=OPEN_LONG, stop_price=Decimal("99.9999"), target_price=Decimal("200")
        ),
        initial_capital=Decimal("1000"),
    ).run()
    assert run.trades[0].size * run.trades[0].entry_price <= Decimal("1000")


def test_a_full_cash_position_leaves_room_for_its_entry_fee() -> None:
    """Sizing to the whole balance would leave nothing to pay the fee with."""
    fees = BacktestCosts(
        fee_rate=Decimal("0.001"), spread_rate=Decimal(0), slippage_rate=Decimal(0), latency_bars=1
    )
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False),
        costs=fees,
        initial_capital=Decimal("1000"),
    ).run()
    assert run.trades, "the entry must not be rejected for want of cash"
    notional = run.trades[0].size * run.trades[0].entry_price
    assert notional + fees.fee(notional) <= Decimal("1000")
    assert notional > Decimal("0")


# -- exits -----------------------------------------------------------------


def test_stop_loss_is_honoured_intrabar() -> None:
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    candles.append(make_candle(30, open_price="100", high="100", low="80", close="100"))
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("200")),
    ).run()
    assert run.trades[0].exit_reason == "stop_loss"
    assert run.trades[0].exit_price == Decimal("95")


def test_take_profit_is_honoured_intrabar() -> None:
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    candles.append(make_candle(30, open_price="100", high="130", low="100", close="100"))
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("110")),
    ).run()
    assert run.trades[0].exit_reason == "take_profit"
    assert run.trades[0].exit_price == Decimal("110")


def test_stop_wins_when_a_single_bar_touches_both_levels() -> None:
    """We cannot know the intrabar order, so the pessimistic one is assumed."""
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    candles.append(make_candle(30, open_price="100", high="120", low="90", close="100"))
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("110")),
    ).run()
    assert run.trades[0].exit_reason == "stop_loss"


def test_brackets_are_validated_against_the_actual_fill_price() -> None:
    """A gap up past the target must not be reported as a profitable fill."""
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    # The fill bar gaps up to 120, well past the 110 target.
    candles[1] = make_candle(5, open_price="120", high="121", low="119", close="120")
    with pytest.raises(ValueError, match="already reached"):
        engine_for(
            candles,
            lambda _: Signal(
                kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("110")
            ),
        ).run()


def test_close_signal_exits_at_the_next_open() -> None:
    candles = flat_candles([100] * 8)
    # The close signal is raised on bar 3; bar 4's open is the fill.
    candles[4] = make_candle(20, open_price="200", high="201", low="199", close="200")

    def logic(context: StrategyContext) -> Signal:
        if context.index == 0:
            return Signal(kind=OPEN_LONG, use_default_brackets=False)
        if context.index == 3:
            return Signal(kind=CLOSE, reason="test exit")
        return Signal(kind=HOLD)

    run = engine_for(candles, logic).run()
    exits = [t for t in run.trades if t.exit_reason == "test exit"]
    assert exits and exits[0].exit_price == Decimal("200")


def test_open_position_is_liquidated_at_the_final_close() -> None:
    candles = flat_candles([100] * 8)
    candles[-1] = make_candle(35, open_price="100", high="101", low="99", close="150")
    run = engine_for(candles, lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False)).run()

    assert len(run.trades) == 1
    assert run.trades[0].exit_reason == "end_of_data"
    assert run.trades[0].exit_price == Decimal("150")
    # Final equity is realized: cash, not cash plus an open position.
    assert run.final_equity == run.equity_curve[-1].equity
    assert run.equity_curve[-1].unrealized == Decimal(0)
    assert run.equity_curve[-1].position_side is None


def test_unbracketed_position_is_not_churned_by_the_time_limit() -> None:
    """Buy-and-hold semantics: one entry, one liquidation."""
    candles = flat_candles([100] * 400)
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False),
        default_max_hold_bars=10,
    ).run()
    assert len(run.trades) == 1
    assert run.trades[0].exit_reason == "end_of_data"


def test_bracketed_position_is_closed_by_the_time_limit() -> None:
    candles = flat_candles([100] * 400, high_pad="0", low_pad="0.0001")
    run = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("90"), target_price=Decimal("300")),
        default_max_hold_bars=5,
    ).run()
    assert run.trades[0].exit_reason == "time_exit"


# -- bracket validation ----------------------------------------------------


def test_default_brackets_are_protective_for_a_long() -> None:
    stop, target = engine_for(flat_candles([100, 100]), lambda _: Signal())._default_brackets(
        "buy", Decimal("100")
    )
    assert stop < Decimal("100") < target


def test_default_brackets_are_protective_for_a_short() -> None:
    stop, target = engine_for(flat_candles([100, 100]), lambda _: Signal())._default_brackets(
        "sell", Decimal("100")
    )
    assert stop > Decimal("100") > target


def test_default_brackets_reject_an_unknown_side() -> None:
    with pytest.raises(ValueError, match="unsupported side"):
        engine_for(flat_candles([100, 100]), lambda _: Signal())._default_brackets(
            "open_long", Decimal("100")
        )


def test_inverted_stop_is_rejected() -> None:
    """A stop above the fill for a long is a bug, not a trade — it must fail loudly."""
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    with pytest.raises(ValueError, match="not protective"):
        engine_for(candles, lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("110"))).run()


def test_already_reached_target_is_rejected() -> None:
    candles = flat_candles([100] * 6, high_pad="0", low_pad="0.0001")
    with pytest.raises(ValueError, match="already reached"):
        engine_for(
            candles,
            lambda _: Signal(
                kind=OPEN_LONG, stop_price=Decimal("95"), target_price=Decimal("99")
            ),
        ).run()


def test_a_close_signal_can_be_emitted_while_a_position_is_open() -> None:
    """The strategy is consulted while in a position — otherwise nothing can exit."""
    candles = flat_candles([100] * 8)

    def logic(context: StrategyContext) -> Signal:
        if context.position is not None:
            return Signal(kind=CLOSE, reason="always exit")
        return Signal(kind=OPEN_LONG, use_default_brackets=False)

    run = engine_for(candles, logic).run()
    assert any(trade.exit_reason == "always exit" for trade in run.trades)


def test_short_signal_is_rejected_when_shorts_are_disabled() -> None:
    run = engine_for(
        flat_candles([100] * 6), lambda _: Signal(kind="open_short"), allow_short=False
    ).run()
    assert run.trades == []
    assert any("long-only" in message for message in run.rejected_signals)


# -- accounting ------------------------------------------------------------


def test_fees_are_charged_on_both_sides_and_reduce_equity() -> None:
    candles = flat_candles([100] * 6)
    free = engine_for(
        candles, lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False)
    ).run()
    costly = engine_for(
        candles,
        lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False),
        costs=BacktestCosts(fee_rate=Decimal("0.01"), spread_rate=Decimal(0), slippage_rate=Decimal(0)),
    ).run()
    assert free.final_equity == Decimal("10000")
    assert costly.final_equity < Decimal("10000")
    assert costly.trades[0].fees > free.trades[0].fees


def test_equity_curve_has_one_point_per_bar_and_is_non_decreasing_in_peak() -> None:
    candles = flat_candles([100 + i for i in range(20)])
    run = engine_for(candles, lambda _: Signal(kind=HOLD)).run()
    assert len(run.equity_curve) == len(candles)
    drawdowns = [point.drawdown for point in run.equity_curve]
    assert all(drawdown <= 0 for drawdown in drawdowns)


def test_runs_are_independent_and_repeatable() -> None:
    candles = flat_candles([100 + (i % 7) for i in range(50)])
    engine = engine_for(candles, lambda _: Signal(kind=OPEN_LONG, stop_price=Decimal("90")))
    first = engine.run()
    second = engine.run()
    assert first.final_equity == second.final_equity
    assert len(first.trades) == len(second.trades)


# -- ledger integrity -----------------------------------------------------


#: Every cost configuration the reconciliation test sweeps. The identity must
#: hold for all of them, not just one hand-picked rate.
RECONCILING_COSTS = [
    BacktestCosts(fee_rate=Decimal("0.001"), spread_rate=Decimal("0.0002"), slippage_rate=Decimal("0.0001"), latency_bars=1),
    BacktestCosts(fee_rate=Decimal("0"), spread_rate=Decimal("0.0005"), slippage_rate=Decimal(0), latency_bars=1),
    BacktestCosts(fee_rate=Decimal(0), spread_rate=Decimal(0), slippage_rate=Decimal("0.0003"), latency_bars=1),
    BacktestCosts(fee_rate=Decimal("0.0006"), spread_rate=Decimal("0"), slippage_rate=Decimal(0), latency_bars=1),
    BacktestCosts(fee_rate=Decimal("0.00075"), spread_rate=Decimal("0.0001"), slippage_rate=Decimal("0.00005"), latency_bars=2),
]


def _ledger_run(costs: BacktestCosts) -> "Trade":
    """A run exercising a stop exit, where every ledger field is populated."""
    candles = [
        make_candle(0, open_price="100", high="101", low="99", close="100"),
        make_candle(5, open_price="100", high="103", low="99.5", close="102"),
        make_candle(10, open_price="102", high="103", low="95", close="96"),
        # A trailing bar so the stop exit is an intrabar fill rather than the
        # end-of-data liquidation, which prices from the close instead.
        make_candle(15, open_price="96", high="97", low="95", close="96"),
        make_candle(20, open_price="96", high="97", low="95", close="96"),
    ]
    run = engine_for(
        candles,
        lambda h: Signal(kind=OPEN_LONG, stop_price=Decimal("99"), target_price=Decimal("120"))
        if len(h.history) == 1
        else Signal(kind=HOLD),
        costs=costs,
    ).run()
    assert run.trades and run.trades[0].exit_reason == "stop_loss"
    return run.trades[0]


@pytest.mark.parametrize("costs", RECONCILING_COSTS)
def test_costs_reconcile_to_the_gross_to_net_gap(costs: BacktestCosts) -> None:
    """``fees + spread + slippage`` must equal ``gross_pnl - net_pnl`` exactly.

    The itemised columns are only useful if they add up. An earlier version
    measured gross between the *concessioned* fill prices while also booking
    spread and slippage separately, so friction was hidden inside gross and the
    itemisation explained a different number entirely.
    """
    trade = _ledger_run(costs)
    booked = trade.fees + trade.spread_cost + trade.slippage_cost + trade.other_costs
    # Tolerance is the default 28-digit Decimal context: the identity is exact
    # to the last representable bit, not merely close.
    assert abs((trade.gross_pnl - trade.net_pnl) - booked) < Decimal("1e-20")


def test_gross_pnl_excludes_friction_and_net_pnl_includes_it() -> None:
    """Friction must move ``net_pnl`` but leave ``gross_pnl`` unchanged."""
    free = _ledger_run(ZERO_COSTS)
    costly = _ledger_run(RECONCILING_COSTS[0])
    # Gross measures the price move between the two frictionless references, so
    # it is invariant to the cost model even though the fills are not. Dividing
    # by size isolates that move from the slightly different stop distances the
    # two fills produce.
    free_move = free.gross_pnl / free.size
    costly_move = costly.gross_pnl / costly.size
    assert free_move == costly_move == Decimal("99") - Decimal("100")
    assert costly.net_pnl < free.net_pnl
    identity = costly.gross_pnl - costly.fees - costly.spread_cost - costly.slippage_cost
    assert abs(costly.net_pnl - identity) < Decimal("1e-20")


def test_every_cost_component_is_non_negative() -> None:
    """A negative cost would mean a favourable concession, i.e. a modelling bug."""
    for costs in RECONCILING_COSTS:
        trade = _ledger_run(costs)
        assert trade.fees >= 0
        assert trade.spread_cost >= 0
        assert trade.slippage_cost >= 0
        assert trade.latency_cost >= 0
        assert trade.other_costs >= 0


def test_gross_and_net_r_bracket_the_true_edge() -> None:
    """Net R can never exceed gross R: costs only ever subtract."""
    trade = _ledger_run(RECONCILING_COSTS[0])
    assert trade.gross_r is not None and trade.net_r is not None
    assert trade.net_r < trade.gross_r
    assert trade.r_multiple == trade.gross_r


def test_r_multiples_are_measured_against_the_actual_stop_distance() -> None:
    """1R is the money lost if the initial stop is hit — no more, no less."""
    candles = [
        make_candle(0, open_price="100", high="101", low="99", close="100"),
        make_candle(5, open_price="100", high="110", low="99.5", close="109"),
        make_candle(10, open_price="109", high="110", low="99", close="100"),
    ]
    run = engine_for(
        candles,
        lambda h: Signal(kind=OPEN_LONG, stop_price=Decimal("99"), target_price=Decimal("200"))
        if len(h.history) == 1
        else Signal(kind=HOLD),
        costs=ZERO_COSTS,
    ).run()
    trade = run.trades[0]
    # The entry fills at bar 1's open (100) because latency is 1 bar, and the
    # stop is 1 unit away, so one unit of size risks exactly 1 unit of cash.
    assert trade.risk_amount == trade.size
    assert abs(trade.gross_r - trade.gross_pnl / trade.risk_amount) < Decimal("1e-20")
