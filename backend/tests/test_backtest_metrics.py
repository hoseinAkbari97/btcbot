from decimal import Decimal

from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import HOLD, OPEN_LONG, BacktestEngine, Signal
from app.services.backtest.metrics import (
    BARS_PER_YEAR,
    MIN_CAGR_SPAN_SECONDS,
    compute_metrics,
    group_monthly_pnl,
    summarize_trade_exits,
)
from test_backtest_engine import flat_candles
from conftest import make_candle

ZERO_COSTS = BacktestCosts(
    fee_rate=Decimal(0), spread_rate=Decimal(0), slippage_rate=Decimal(0), latency_bars=1
)


def run_over(candles, **kwargs):
    engine = BacktestEngine(
        candles=candles,
        strategy_name="metrics_fixture",
        logic=kwargs.pop("logic", lambda _: Signal(kind=OPEN_LONG, use_default_brackets=False)),
        costs=kwargs.pop("costs", ZERO_COSTS),
        initial_capital=kwargs.pop("initial_capital", Decimal("10000")),
        timeframe=kwargs.pop("timeframe", Timeframe.M5),
        **kwargs,
    )
    return engine.run()


def test_bars_per_year_covers_every_timeframe() -> None:
    assert set(BARS_PER_YEAR) == set(Timeframe)


def test_a_short_sample_is_not_annualised() -> None:
    """Annualising a window of days yields ratios no real strategy produces.

    Over a few dozen bars the sqrt(bars-per-year) scaling factor turns an
    ordinary per-bar mean-to-dispersion ratio into a headline number in the
    hundreds. CAGR and Calmar are reported as zero for the same reason, and
    Sharpe/Sortino fall back to their unannualised form.
    """
    run = run_over(flat_candles([100 + (i % 9) for i in range(60)]))
    metrics = compute_metrics(run)

    assert (run.end - run.start).days < 30
    assert metrics.cagr == 0.0
    assert metrics.calmar == 0.0
    assert abs(metrics.sharpe) < 100, "an annualised figure would be in the hundreds"


def test_a_short_run_flags_itself_as_an_insufficient_sample() -> None:
    """Zero is not the same answer as "not computable".

    The annual fields are suppressed on a short span by writing 0.0. A reader —
    or a dashboard — that cannot tell suppression from a measured zero will read
    a 60-bar run as "0% annualised return, Sharpe 0" and draw a confident
    conclusion from it. The flag makes the suppression explicit, and carries
    the span so the reader can see how far short it fell.
    """
    run = run_over(flat_candles([100 + (i % 9) for i in range(60)]))
    metrics = compute_metrics(run)

    assert metrics.insufficient_sample is True
    assert metrics.sample_span_seconds == (run.end - run.start).total_seconds()
    assert metrics.sample_span_seconds < MIN_CAGR_SPAN_SECONDS
    # The flag must survive serialisation — an unflagged dict is what the API
    # and the research reports actually consume.
    assert metrics.as_dict()["insufficient_sample"] is True


def test_a_year_long_run_is_not_flagged_as_insufficient() -> None:
    """The guard is not a permanent 'insufficient' sticker on every result."""
    # 800 hourly candles == 33 days, just past the 30-day annualisation floor.
    candles = [
        make_candle(
            index * 60,
            open_price=str(100 + (i % 5)),
            high=str(101 + (i % 5)),
            low=str(99 + (i % 5)),
            close=str(100 + (i % 5)),
        )
        for index, i in enumerate(range(800))
    ]
    run = run_over(candles, timeframe=Timeframe.H1)
    metrics = compute_metrics(run)

    assert (run.end - run.start).days >= 30
    assert metrics.insufficient_sample is False
    assert metrics.as_dict()["insufficient_sample"] is False


def test_flat_market_produces_zero_return_and_no_trades() -> None:
    run = run_over(flat_candles([100] * 50))
    metrics = compute_metrics(run)

    assert metrics.total_return == 0.0
    # One round trip at an unchanged price: two fills, zero net PnL.
    assert metrics.trade_count == 1
    assert run.trades[0].net_pnl == 0
    assert metrics.max_drawdown == 0.0
    assert metrics.profit_factor == 0.0
    assert metrics.win_rate == 0.0


def test_rising_market_shows_a_positive_return() -> None:
    run = run_over(flat_candles([100 + i for i in range(60)]))
    metrics = compute_metrics(run)

    assert metrics.total_return > 0
    assert metrics.final_equity > metrics.initial_capital
    # Flat on the signal bar and on the bar that is liquidated.
    assert metrics.exposure > 0.9
    assert metrics.max_drawdown == 0.0, "a monotonic rise has no drawdown"


def test_exposure_is_the_fraction_of_bars_holding_a_position() -> None:
    run = run_over(flat_candles([100] * 50), logic=lambda _: Signal(kind=HOLD))
    assert compute_metrics(run).exposure == 0.0

    held = run_over(flat_candles([100] * 50))
    assert compute_metrics(held).exposure > 0.9


def test_drawdown_is_measured_from_the_running_peak() -> None:
    prices = [100] * 5 + [120] * 5 + [60] * 5 + [100] * 5
    run = run_over(flat_candles(prices))
    metrics = compute_metrics(run)
    # Equity peaks near 120 and troughs near 60: a 50% peak-to-trough fall.
    assert -0.51 < metrics.max_drawdown < -0.49


def test_total_return_matches_the_final_equity() -> None:
    run = run_over(flat_candles([100 + 2 * i for i in range(40)]))
    metrics = compute_metrics(run)
    expected = float(run.final_equity) / float(run.initial_capital) - 1.0
    assert abs(metrics.total_return - expected) < 1e-12


def test_win_rate_and_profit_factor_reflect_trade_outcomes() -> None:
    """One trade takes profit; the second is still open at the end of the data."""
    prices = [100] * 6 + [115] + [100] * 20
    run = run_over(
        flat_candles(prices),
        logic=lambda _: Signal(
            kind=OPEN_LONG, stop_price=Decimal("50"), target_price=Decimal("110")
        ),
    )
    metrics = compute_metrics(run)
    # The second position is still open when the data ends, so it exits flat.
    assert metrics.trade_count == 2
    assert metrics.win_rate == 0.5
    assert metrics.average_win > 0
    assert metrics.average_loss == 0.0
    assert metrics.best_trade > metrics.worst_trade
    assert metrics.profit_factor == 0.0, "no losses means no defined profit factor"


def test_fees_reduce_reported_performance() -> None:
    candles = flat_candles([100 + i for i in range(40)])
    free = compute_metrics(run_over(candles))
    charged = compute_metrics(
        run_over(candles, costs=BacktestCosts(fee_rate=Decimal("0.01"), spread_rate=Decimal(0), slippage_rate=Decimal(0)))
    )
    assert charged.total_fees > 0
    assert free.total_fees == 0
    assert charged.total_return < free.total_return
    assert charged.final_equity < free.final_equity


def test_metrics_are_serialisable() -> None:
    payload = compute_metrics(run_over(flat_candles([100 + i for i in range(30)]))).as_dict()
    assert set(payload) >= {"total_return", "sharpe", "max_drawdown", "trade_count"}
    assert isinstance(payload["monthly_returns"], dict)


def test_period_returns_are_keyed_by_calendar_bucket() -> None:
    metrics = compute_metrics(run_over(flat_candles([100 + i for i in range(60)])))
    assert all(len(key) == 7 and key[4] == "-" for key in metrics.monthly_returns)
    assert all(len(key) == 4 for key in metrics.yearly_returns)


def test_exit_reasons_are_counted_by_type() -> None:
    prices = [100] * 6 + [120] + [100] * 20
    run = run_over(
        flat_candles(prices),
        logic=lambda _: Signal(
            kind=OPEN_LONG, stop_price=Decimal("50"), target_price=Decimal("110")
        ),
    )
    assert set(summarize_trade_exits(run)) <= {
        "take_profit",
        "stop_loss",
        "time_exit",
        "end_of_data",
        "signal_exit",
    }


def test_monthly_pnl_groups_realized_trades() -> None:
    prices = [100] * 6 + [115] + [100] * 20
    run = run_over(
        flat_candles(prices),
        logic=lambda _: Signal(
            kind=OPEN_LONG, stop_price=Decimal("50"), target_price=Decimal("110")
        ),
    )
    buckets = group_monthly_pnl(run)
    assert sum(buckets.values()) == sum(float(t.net_pnl) for t in run.trades)
