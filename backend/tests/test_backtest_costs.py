from decimal import Decimal

import pytest
from conftest import make_candle

from app.services.backtest.costs import BacktestCosts, apply_slippage, fill_price

ZERO_COSTS = BacktestCosts(
    fee_rate=Decimal(0),
    spread_rate=Decimal(0),
    slippage_rate=Decimal(0),
    latency_bars=1,
)


def test_slippage_moves_price_against_the_trader() -> None:
    costs = BacktestCosts(
        fee_rate=Decimal(0), spread_rate=Decimal("0.001"), slippage_rate=Decimal("0.001")
    )
    price = Decimal("100")
    assert apply_slippage(price, "buy", costs) == Decimal("100.200000")
    assert apply_slippage(price, "sell", costs) == Decimal("99.800000")


def test_slippage_rejects_unknown_side() -> None:
    with pytest.raises(ValueError, match="unsupported side"):
        apply_slippage(Decimal("100"), "hold", ZERO_COSTS)


def test_scaled_multiplies_variable_costs_only() -> None:
    base = BacktestCosts(
        fee_rate=Decimal("0.001"),
        spread_rate=Decimal("0.0002"),
        slippage_rate=Decimal("0.0001"),
        latency_bars=3,
    )
    doubled = base.scaled(Decimal(2))
    assert doubled.fee_rate == Decimal("0.002")
    assert doubled.spread_rate == Decimal("0.0004")
    assert doubled.slippage_rate == Decimal("0.0002")
    assert doubled.latency_bars == 3
    assert base.fee_rate == Decimal("0.001"), "scaling must not mutate the original"


def test_round_trip_cost_covers_entry_and_exit() -> None:
    costs = BacktestCosts(
        fee_rate=Decimal("0.001"), spread_rate=Decimal("0.0002"), slippage_rate=Decimal("0.0001")
    )
    assert costs.round_trip_cost_rate() == Decimal("0.0026")


def test_fill_price_uses_the_later_candle_open() -> None:
    signal_close = Decimal("50000")
    target = make_candle(5, open_price="50100")
    filled = fill_price(signal_close, target, ZERO_COSTS, "buy")
    assert filled.filled is True
    assert filled.price == target.open


def test_fill_price_rejects_zero_latency() -> None:
    costs = BacktestCosts(latency_bars=0)
    with pytest.raises(ValueError, match="latency_bars"):
        fill_price(Decimal("1"), make_candle(), costs, "buy")
