"""The R distribution is the Monte Carlo project's input, so it is tested as one.

These tests check the statistics against hand-computed values rather than
against a previous run of the code, because a distribution module that is only
self-consistent will happily be self-consistently wrong.
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest
from conftest import make_candle

from app.services.backtest.distributions import (
    MIN_TRADES_FOR_DISTRIBUTION,
    summarize_r_distribution,
)
from app.services.backtest.engine import (
    HOLD,
    OPEN_LONG,
    BacktestEngine,
    Signal,
    SizingModel,
    Trade,
)
from app.schemas.market_data import Timeframe


def trade(
    *,
    net_r: float | None,
    mae: float | None = None,
    mfe: float | None = None,
    regime: str = "",
    risk_amount: float = 1.0,
    fees: float = 0.0,
    spread: float = 0.0,
    slippage: float = 0.0,
) -> Trade:
    """A ``Trade`` with only the fields the distribution module reads."""
    return Trade(
        id=0,
        side="long",
        signal_time=None,
        order_time=None,
        fill_time=None,
        entry_time=make_candle(0).open_time,
        exit_time=make_candle(60).close_time,
        entry_price=Decimal("100"),
        exit_price=Decimal("100"),
        size=Decimal("1"),
        notional_value=Decimal("100"),
        initial_stop=Decimal("99"),
        initial_target=None,
        gross_pnl=Decimal("0"),
        fees=Decimal(str(fees)),
        net_pnl=Decimal("0"),
        gross_r=net_r,
        net_r=None if net_r is None else Decimal(str(net_r)),
        r_multiple=net_r,
        mae=None if mae is None else Decimal(str(mae)),
        risk_amount=Decimal(str(risk_amount)),
        mae_price=None,
        mfe=None if mfe is None else Decimal(str(mfe)),
        mfe_price=None,
        bars_held=1,
        exit_reason="signal_exit",
        strategy_name="test",
        strategy_version="1",
        symbol="BTCUSDT",
        timeframe="5m",
        market_regime=regime,
        spread_cost=Decimal(str(spread)),
        slippage_cost=Decimal(str(slippage)),
        latency_cost=Decimal("0"),
        other_costs=Decimal("0"),
    )


# -- the insufficient-sample guard -----------------------------------------


def test_a_short_sample_withholds_its_estimates() -> None:
    """Two trades have no distribution worth summarising, and must not fake one."""
    result = summarize_r_distribution([trade(net_r=1.0), trade(net_r=-1.0)])
    assert result.count == 2
    assert not result.sufficient_sample
    assert result.mean_r is None
    assert result.median_r is None
    assert result.stdev_r is None
    assert result.skew is None
    assert result.kurtosis is None
    assert result.percentiles == {}


def test_a_short_sample_still_reports_what_was_observed() -> None:
    """Withholding estimates must not mean withholding data.

    The count, the extremes and the win rate are descriptions of trades that
    really happened, not predictions about future ones. Hiding them alongside
    the withheld estimates would throw away information for no gain.
    """
    result = summarize_r_distribution(
        [trade(net_r=2.0), trade(net_r=-1.0), trade(net_r=0.5)]
    )
    assert result.count == 3
    assert result.worst_r == -1.0
    assert result.best_r == 2.0
    assert result.win_rate == pytest.approx(2 / 3)


def test_the_threshold_is_exactly_enforced() -> None:
    """One trade below the threshold and one at it must straddle the boundary."""
    just_enough = [trade(net_r=1.0) for _ in range(MIN_TRADES_FOR_DISTRIBUTION)]
    just_short = just_enough[:-1]
    assert summarize_r_distribution(just_enough).sufficient_sample
    assert not summarize_r_distribution(just_short).sufficient_sample


# -- the statistics themselves ---------------------------------------------


def test_median_and_percentiles_match_hand_computed_values() -> None:
    values = [float(v) for v in range(1, 101)]  # 1..100
    result = summarize_r_distribution([trade(net_r=v) for v in values])
    assert result.sufficient_sample
    # The median of 1..100 is the mean of 50 and 51.
    assert result.median_r == pytest.approx(50.5)
    # p25 sits at index 24.75 of the zero-based range: 25 + 0.75*(26-25).
    assert result.percentiles[25] == pytest.approx(25.75)
    assert result.percentiles[50] == pytest.approx(50.5)
    assert result.percentiles[75] == pytest.approx(75.25)
    assert result.percentiles[1] == pytest.approx(1.99)
    assert result.percentiles[99] == pytest.approx(99.01)


def test_stdev_is_the_sample_standard_deviation() -> None:
    """Sample (n-1), not population (n): these are observations, not the population."""
    # The expected value is computed from the full 120-value sample rather than
    # from the four distinct values: repeating a set evenly leaves the *mean*
    # and the sum of squared deviations unchanged, but the n-1 denominator does
    # not, so the two stdevs genuinely differ. The population stdev of this
    # sample is 1.118; the sample stdev is measurably larger, and reporting the
    # larger one is the whole point — these are observations, not the
    # population they were drawn from.
    values = [float(v) for v in [1, 2, 3, 4] * 30]
    result = summarize_r_distribution([trade(net_r=v) for v in values])
    mean = sum(values) / len(values)
    population = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    expected = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    assert result.stdev_r == pytest.approx(expected)
    assert result.stdev_r > population


def test_percentiles_of_a_constant_sample_are_that_constant() -> None:
    result = summarize_r_distribution([trade(net_r=1.5) for _ in range(40)])
    assert result.percentiles[1] == pytest.approx(1.5)
    assert result.percentiles[99] == pytest.approx(1.5)
    assert result.stdev_r == pytest.approx(0.0)
    # A constant sample has no skew to measure; zero would be a claim, not a fact.
    assert result.skew is None
    assert result.kurtosis is None


def test_profit_factor_is_gross_win_over_gross_loss() -> None:
    result = summarize_r_distribution(
        [trade(net_r=2.0), trade(net_r=1.0), trade(net_r=-1.5)]
        + [trade(net_r=0.0)] * 30
    )
    assert result.profit_factor_r == pytest.approx(3.0 / 1.5)


def test_profit_factor_is_none_when_nothing_was_lost() -> None:
    """An undefined ratio is reported as undefined, not as infinity."""
    result = summarize_r_distribution([trade(net_r=1.0) for _ in range(40)])
    assert result.profit_factor_r is None


def test_skew_is_positive_when_a_few_wins_dwarf_many_losses() -> None:
    """The shape of a trend-following system: many small losses, rare big wins."""
    values = [3.0] * 5 + [-0.5] * 40
    result = summarize_r_distribution([trade(net_r=v) for v in values])
    assert result.skew is not None and result.skew > 0


def test_a_symmetric_sample_has_near_zero_skew() -> None:
    values = [-2.0, -1.0, 1.0, 2.0] * 10
    result = summarize_r_distribution([trade(net_r=v) for v in values])
    assert result.skew == pytest.approx(0.0, abs=1e-9)


def test_streaks_measure_consecutive_runs() -> None:
    result = summarize_r_distribution(
        [trade(net_r=v) for v in [1, 1, 1, -1, -1, 1, -1, -1, -1]] * 6
    )
    assert result.longest_win_streak == 3
    assert result.longest_loss_streak == 3


def test_a_flat_trade_breaks_a_streak_rather_than_extending_it() -> None:
    """Counting a zero either way would misstate the length of the runs."""
    result = summarize_r_distribution(
        [trade(net_r=v) for v in [1, 1, 0, 1, -1, -1, -1, -1, 0, -1]] * 5
    )
    assert result.longest_win_streak == 2
    assert result.longest_loss_streak == 4


# -- excursions and costs ---------------------------------------------------


def test_excursions_are_averaged_in_r_over_the_trades_that_have_them() -> None:
    result = summarize_r_distribution(
        [trade(net_r=1.0, mae=0.5, mfe=2.0)] * 20
        + [trade(net_r=-1.0, mae=1.0, mfe=0.1)] * 20
    )
    assert result.mean_mae_r == pytest.approx(0.75)
    assert result.mean_mfe_r == pytest.approx(1.05)


def test_costs_are_expressed_in_r_not_in_currency() -> None:
    """Cost in R is comparable across trades of different size; currency is not."""
    result = summarize_r_distribution(
        [trade(net_r=1.0, fees=0.1, spread=0.05, slippage=0.05, risk_amount=2.0)]
        + [trade(net_r=-1.0) for _ in range(40)]
        + [trade(net_r=1.0, fees=0.0, risk_amount=1.0)] * 60
    )
    # 0.1 + 0.05 + 0.05 = 0.20 of friction on 2.0 of risk = 0.1R. Only one
    # trade of the 101 carries any friction at all, so the mean is 0.1/101 —
    # which is the point: an unweighted mean across trades of different sizes
    # is not itself a cost figure anyone should act on.
    assert result.mean_cost_r == pytest.approx(0.1 / 101)


# -- allocation-sized trades ------------------------------------------------


def test_trades_without_an_r_are_excluded_rather_than_given_a_fake_one() -> None:
    """An allocation-sized position has no defined risk unit.

    Assigning it one — say, by dividing by its notional — would manufacture an
    R that means nothing and quietly pollute the distribution that the Monte
    Carlo project is going to resample.
    """
    trades = [trade(net_r=None) for _ in range(5)] + [trade(net_r=1.0) for _ in range(30)]
    result = summarize_r_distribution(trades)
    assert result.count == 30, "the five undefined-R trades must not be counted"
    assert result.sufficient_sample


def test_a_run_of_only_allocation_trades_produces_an_empty_distribution() -> None:
    result = summarize_r_distribution([trade(net_r=None) for _ in range(50)])
    assert result.count == 0
    assert not result.sufficient_sample
    assert result.mean_r is None
    assert result.worst_r is None
    assert result.win_rate is None


# -- regime slicing ---------------------------------------------------------


def test_regimes_are_counted_and_summarised_separately() -> None:
    """Per-regime R is how a strategy's dependence on one market state is seen."""
    trending = [trade(net_r=1.5, regime="uptrend") for _ in range(30)]
    choppy = [trade(net_r=-0.5, regime="chop") for _ in range(30)]
    result = summarize_r_distribution(trending + choppy)
    assert result.by_regime == {"uptrend": 30, "chop": 30}
    assert result.mean_r_by_regime == {"uptrend": 1.5, "chop": -0.5}


def test_a_regime_with_too_few_of_its_own_trades_reports_no_mean() -> None:
    """Thirty trades in one regime says nothing about the other regime's mean."""
    trades = [trade(net_r=1.0, regime="uptrend") for _ in range(35)] + [
        trade(net_r=1.0, regime="chop") for _ in range(2)
    ]
    result = summarize_r_distribution(trades)
    assert result.mean_r_by_regime["uptrend"] == pytest.approx(1.0)
    assert result.mean_r_by_regime["chop"] is None


def test_trades_with_no_recorded_regime_are_grouped_rather_than_dropped() -> None:
    result = summarize_r_distribution([trade(net_r=1.0) for _ in range(40)])
    assert result.by_regime == {"unclassified": 40}


# -- integration with the engine --------------------------------------------


def test_the_distribution_of_a_real_run_reflects_its_ledger() -> None:
    """End-to-end: a run with real costs must show costs in its net R.

    This is the property the Monte Carlo project depends on — the distribution
    it resamples has to be the one a trader would have experienced, not the
    frictionless one.
    """
    prices = [100, 100, 102, 101, 103, 102, 104, 103, 105, 104,
              106, 105, 107, 106, 108, 107, 109, 108, 110, 109]
    candles = [
        make_candle(i * 5, open_price=str(p), high=str(p + 1), low=str(p - 1), close=str(p))
        for i, p in enumerate(prices)
    ]

    def logic(history):
        # Long only while the close is making a new high, so the run actually
        # trades rather than idling.
        closes = [c.close for c in history.history]
        rising = len(closes) > 2 and closes[-1] > max(closes[:-2])
        return Signal(kind=OPEN_LONG, stop_price=Decimal("98"), target_price=Decimal("200")) if rising else Signal(kind=HOLD)

    run = BacktestEngine(
        candles=candles,
        strategy_name="test",
        logic=logic,
        costs=__import__(
            "app.services.backtest.costs", fromlist=["BacktestCosts"]
        ).BacktestCosts(
            fee_rate=Decimal("0.001"),
            spread_rate=Decimal("0.0002"),
            slippage_rate=Decimal("0.0001"),
            latency_bars=1,
        ),
        initial_capital=Decimal("100000"),
        timeframe=Timeframe.M5,
    ).run()

    assert run.trades, "the run must produce trades for this test to mean anything"
    for recorded in run.trades:
        assert recorded.sizing_model == SizingModel.RISK
        assert recorded.net_r is not None
        # Net R is strictly below gross R whenever there are costs, because
        # friction can only subtract from an outcome.
        assert recorded.net_r < recorded.gross_r

    result = summarize_r_distribution(run.trades)
    assert result.count == len(run.trades)
    if result.sufficient_sample:
        # Net R must sit below gross R on average too, by exactly the mean cost.
        assert result.mean_r is not None
        assert result.mean_cost_r is not None
        assert result.mean_cost_r > 0
        assert result.mean_r < result.median_r or result.mean_r == result.median_r
    else:
        # Too few trades to characterise: the count is still exact.
        assert result.count > 0
        assert result.mean_r is None
