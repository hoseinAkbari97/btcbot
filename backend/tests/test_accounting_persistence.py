"""Persistence contract for the exact engine curve and per-leg ledger costs."""

from decimal import Decimal

import pytest
from conftest import make_candle

from app.repositories.backtest import BacktestRepository
from app.schemas.market_data import Timeframe
from app.services.accounting.model import ACCOUNTING_MODEL_VERSION
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.runner import run_backtest

STORED_MONEY = Decimal("0.0000000001")


def stored_money(value: Decimal) -> Decimal:
    """The run schema stores monetary values at ten decimal places."""
    return value.quantize(STORED_MONEY)


def test_candles() -> list:
    return [
        make_candle(
            index * 5,
            open_price="100",
            high="101",
            low="99",
            close=str(100 + index),
        )
        for index in range(12)
    ]


@pytest.mark.asyncio
async def test_save_persists_the_exact_engine_curve_and_per_leg_costs(db_session) -> None:
    result = run_backtest(
        test_candles(),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=BacktestCosts(
            fee_rate=Decimal("0.001"),
            spread_rate=Decimal("0.0002"),
            slippage_rate=Decimal("0.0001"),
            latency_bars=1,
        ),
        initial_capital=Decimal("10000"),
    )
    repository = BacktestRepository(db_session)
    record = await repository.save(result)
    run_id = record.id
    await db_session.commit()
    db_session.expire_all()

    stored_run = await repository.get_run_without_trades(run_id)
    assert stored_run is not None
    assert stored_run.accounting_model_version == ACCOUNTING_MODEL_VERSION

    # SQLite stores timezone-aware datetimes as naive UTC, as it already does
    # for trade timestamps; compare the stored representation, not object identity.
    expected = [
        (
            point.bar_index,
            point.time.replace(tzinfo=None),
            stored_money(point.equity),
            stored_money(point.cash),
            stored_money(point.unrealized),
            point.position_side,
            stored_money(point.drawdown),
        )
        for point in result.run.equity_curve
    ]
    rows = await repository.list_equity_point_rows(
        run_id, len(result.run.equity_curve)
    )
    assert rows == expected
    assert await repository.count_equity_points(run_id) == len(expected)

    batches = [
        batch async for batch in repository.iter_equity_point_batches(run_id, batch_size=5)
    ]
    assert [len(batch) for batch in batches] == [5, 5, 2]
    assert [row for batch in batches for row in batch] == expected

    # After end-of-data liquidation the terminal point is fully realized.
    assert rows[-1][2] == stored_run.final_equity
    assert rows[-1][4] == Decimal(0)
    assert rows[-1][5] is None

    trades = await repository.list_trades(run_id)
    assert trades
    source = result.run.trades[0]
    stored = trades[0]
    assert stored.entry_fee == stored_money(source.entry_fee)
    assert stored.exit_fee == stored_money(source.exit_fee)
    assert stored.raw_exit_price == stored_money(source.raw_exit_price)
    assert stored.entry_concession == stored_money(source.entry_concession)
    assert stored.exit_concession == stored_money(source.exit_concession)


@pytest.mark.asyncio
async def test_equity_curve_reads_are_bounded_and_missing_runs_are_unavailable(
    db_session,
) -> None:
    result = run_backtest(
        test_candles(),
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
    )
    repository = BacktestRepository(db_session)
    record = await repository.save(result)
    await db_session.commit()

    page = await repository.list_equity_point_rows(record.id, 3)
    assert len(page) == 4  # limit + 1 truncation sentinel
    assert [row[0] for row in page] == [0, 1, 2, 3]

    assert await repository.count_equity_points("missing-run") == 0
    assert await repository.list_equity_point_rows("missing-run", 10) == []
